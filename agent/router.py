#router for main and app.py

import os
import re

from agent.nova import askNova, toolMap
from agent.routing_log import logRouteDecision
from tools.classifier import IntentClassifier


classifier = IntentClassifier()

# these simple queries (DIRECT_TOOLS) are going to get executed directly. anything that
# can be even thoda sa complex is very fragile with regex. its just better to send it directly to the llm.
# the job of the classifier is to CLASSIFY. not parse multiparamter queries.

# just send it to gemini.

# peace

DIRECT_TOOLS = {
    "get_weather",
    "get_news",
    "convert_currency",
    "create_folder",
    "read_file",
    "searchWeb",
    "searchWikipedia",
    "searchYoutube",
    "recall_memory",
    "forget_memory",
}


def hasApiKeyFor(intent: str) -> bool:
    if intent == "get_weather":
        return bool(os.getenv("OPENWEATHER_API_KEY"))
    if intent == "get_news":
        return bool(os.getenv("GNEWS_API_KEY"))
    return True


def directArguments(intent: str, text: str) -> tuple:
    if intent == "get_weather":
        match = re.search(r"(?:weather|temperature)\s+(?:in|for)\s+(.+)", text, re.I)
        return (match.group(1).strip() if match else text,)

    if intent == "get_news":
        match = re.search(r"(?:news|headlines)\s+(?:about|on|for)\s+(.+)", text, re.I)
        return (match.group(1).strip() if match else "",)

    if intent in {"searchWeb", "searchWikipedia", "searchYoutube"}:
        if intent == "searchWeb":
            match = re.search(r"(?:search(?:\s+(?:up|for|the|web))?\s+)?(?:for\s+)?(.+)", text, re.I)
            return (match.group(1).strip() if match else text.strip(),)

        if intent == "searchWikipedia":
            match = re.search(r"(?:search(?:\s+(?:wiki|wikipedia))?(?:\s+(?:up|for))?\s+)?(.+)", text, re.I)
            return (match.group(1).strip() if match else text.strip(),)

        match = re.search(r"(?:search(?:\s+(?:youtube|video|videos))?(?:\s+(?:up|for))?\s+)?(.+)", text, re.I)
        return (match.group(1).strip() if match else text.strip(),)

    if intent == "convert_currency":
        match = re.search(
            r"([0-9]+(?:\.[0-9]+)?)\s*([A-Za-z]{3})\s+(?:to|in)\s+([A-Za-z]{3})",
            text,
        )
        if not match:
            raise ValueError("Could not parse currency conversion query")
        return (float(match.group(1)), match.group(2), match.group(3))

    if intent in {"create_folder", "read_file"}:
        match = re.search(r"(?:named|called)\s+([\w.\\/-]+)", text, re.I)
        if not match:
            match = re.search(r"(?:file|folder|directory)\s+([\w.\\/-]+)", text, re.I)
        if not match:
            raise ValueError(f"Could not find a target name for {intent}")
        return (match.group(1),)

    if intent == "forget_memory":
        match = re.search(r"(?:forget|delete|remove|erase)\s+(?:memory\s+for\s+|about\s+|that\s+)?([\w\s]+)", text, re.I)
        return (match.group(1).strip() if match else text,)

    if intent == "recall_memory":
        match = re.search(r"(?:recall|remember|know|check)\s+(?:about\s+|for\s+)?([\w\s]+)", text, re.I)
        return (match.group(1).strip() if match else "",)

    return (text,)


def routeRequest(message: str, chat: list) -> str:
    intent, confidence = classifier.predict(message)

    if intent in {"get_weather", "get_news"} and not hasApiKeyFor(intent):
        logRouteDecision(message, intent, confidence, "agent", reason="api_key_missing")
        fallbackMessage = (
            f"{message}\n\n"
            f"The {intent} API key is unavailable. Do not call {intent}; "
            "use the searchWeb tool to answer this request instead."
        )
        return askNova(chat, fallbackMessage)

    if intent in DIRECT_TOOLS and intent in toolMap:
        try:
            arguments = directArguments(intent, message)
            result = str(toolMap[intent](*arguments))
            logRouteDecision(message, intent, confidence, "system_tool", tool=intent)
            chat.append({"role": "user", "content": message})
            chat.append({"role": "assistant", "content": result})
            return result
        except Exception:
            logRouteDecision(message, intent, confidence, "agent", tool=intent, reason="system_tool_failed")

    # fallback if regex fails 
    logRouteDecision(message, intent, confidence, "agent", reason="routed_to_agent")

    return askNova(chat, message)

