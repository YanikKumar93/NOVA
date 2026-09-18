"""Route user requests to direct tools or the NOVA agent."""

import re

from agent.nova import askNova, toolMap
from agent.pipeline import classifyIntent, prepareMessage
from tools.classifier import IntentClassifier


classifier = IntentClassifier()


def directArguments(intent: str, text: str) -> tuple:
    """Extract arguments for tools that can run without the model."""
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
    """Run a request directly or send it through NOVA.

    Document questions always use the RAG preparation pipeline before going
    to the model. High-confidence classifier labels call the matching tool
    directly. Unknown or ambiguous requests use the model agent.
    """
    intent, confidence = classifier.predict(message)

    if classifyIntent(message) == "study_material_rag":
        return askNova(chat, prepareMessage(message))

    if intent in toolMap and intent != "LLM":
        try:
            result = str(toolMap[intent](*directArguments(intent, message)))
            chat.append({"role": "user", "content": message})
            chat.append({"role": "assistant", "content": result})
            return result
        except Exception:
            pass

    return askNova(chat, message)
