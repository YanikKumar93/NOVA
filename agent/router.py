#router for main and app.py

import os
import re

from agent.nova import askNova, toolMap
from agent.routing_log import logRouteDecision
from tools.classifier import IntentClassifier


classifier = IntentClassifier()


def hasApiKeyFor(intent: str) -> bool:
    if intent == "get_weather":
        return bool(os.getenv("OPENWEATHER_API_KEY"))
    if intent == "get_news":
        return bool(os.getenv("GNEWS_API_KEY"))
    return True

#weather nd news requests would randomly get called on any question asked if an initial weather question couldnt be answered due to absent API key
#i really dont get why it did that, but it did and now its fixed


def directArguments(intent: str, text: str) -> tuple:
    if intent == "get_weather":
        match = re.search(r"(?:weather|temperature)\s+(?:in|for)\s+(.+)", text, re.I)
        return (match.group(1).strip() if match else text,)

    if intent == "get_news":
        match = re.search(r"(?:news|headlines)\s+(?:about|on|for)\s+(.+)", text, re.I)
        return (match.group(1).strip() if match else "",)

    if intent == "convert_currency":
        match = re.search(
            r"([0-9]+(?:\.[0-9]+)?)\s*([A-Za-z]{3})\s+(?:to|in)\s+([A-Za-z]{3})",
            text,
        )
        if not match:
            raise ValueError("Use a format such as: convert 100 USD to EUR")
        return (float(match.group(1)), match.group(2), match.group(3))

    if intent in {"create_file", "create_folder", "read_file"}:
        match = re.search(r"(?:named|called)\s+([\w.\\/-]+)", text, re.I)
        if not match:
            match = re.search(r"(?:file|folder)\s+([\w.\\/-]+)", text, re.I)
        if not match:
            raise ValueError("I could not find a file or folder name")
        return (match.group(1),)

    return (text,)


def routeRequest(message: str, chat: list) -> str:
    #self explanatory
    intent, confidence = classifier.predict(message)

    if intent in {"get_weather", "get_news"} and not hasApiKeyFor(intent):
        logRouteDecision(intent, confidence, "agent", reason="api_key_missing")
        fallbackMessage = (
            f"{message}\n\n"
            f"The {intent} API key is unavailable. Do not call {intent}; "
            "use the searchWeb tool to answer this request instead."
        )
        return askNova(chat, fallbackMessage)

    if intent in toolMap and intent != "LLM":
        try:
            arguments = directArguments(intent, message)
            result = str(toolMap[intent](*arguments))
            logRouteDecision(intent, confidence, "system_tool", tool=intent)
            chat.append({"role": "user", "content": message})
            chat.append({"role": "assistant", "content": result})
            return result
        except Exception:
            logRouteDecision(intent, confidence, "agent", tool=intent, reason="system_tool_failed")

    logRouteDecision(intent, confidence, "agent", reason="no_matching_system_tool")
    return askNova(chat, message)
