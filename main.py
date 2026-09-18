import os
from dotenv import load_dotenv

load_dotenv()

from agent.nova import createNova, askNova, toolMap
from tools.classifier import IntentClassifier

classifier = IntentClassifier()

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
                print("NOVA:", handler(userText))
            except Exception:
                print("NOVA:", askNova(chat, userText))
        else: # shouldnt happen but hey safety
            print("NOVA:", askNova(chat, userText))


if __name__ == "__main__":
    main()