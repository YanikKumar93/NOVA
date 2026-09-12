import os
from dotenv import load_dotenv

load_dotenv()

from agent.nova import createNova, askNova


def main():
    print("NOVA (terminal mode). Type 'quit' to exit.\n")
    chat = createNova()
    while True:
        userText = input("You: ").strip()
        if userText.lower() == "quit":
            break
        if not userText:
            continue
        print("NOVA:", askNova(chat, userText))


if __name__ == "__main__":
    main()