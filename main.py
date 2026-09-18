import os
import re
from dotenv import load_dotenv

load_dotenv()

from agent.nova import createNova, askNova, toolMap
from tools.classifier import IntentClassifier

classifier = IntentClassifier()


def directArguments(intent: str, text: str) -> tuple:
    """Extract simple arguments for tools that can run without the model."""
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


def main():
    print("NOVA (terminal mode). Type 'quit' to exit.\n")
    chat = createNova()
    while True:
        userText = input("You: ").strip()
        if userText.lower() == "quit":
            break
        if not userText:
            continue

        intent, confidence = classifier.predict(userText)

        if intent is None or intent == "LLM":
            print("NOVA:", askNova(chat, userText))

        elif intent in toolMap:
            handler = toolMap[intent]

            try:
                print("NOVA:", handler(*directArguments(intent, userText)))
            except Exception:
                print("NOVA:", askNova(chat, userText))
        else: # shouldnt happen but hey safety
            print("NOVA:", askNova(chat, userText))


if __name__ == "__main__":
    main()