import os
from dotenv import load_dotenv

load_dotenv()

from agent.nova import createNova, askNova
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
        elif intent == "OPEN_WEBSITE":
            print("NOVA: OPEN_WEBSITE")
        elif intent == "WEATHER":
            print("NOVA: WEATHER")
        elif intent == "CREATE_FILE":
            print("NOVA: CREATE_FILE")
        elif intent == "SEARCH_WEB":
            print("NOVA: SEARCH_WEB")
        else:
            print("NOVA:", askNova(chat, userText))


if __name__ == "__main__":
    main()