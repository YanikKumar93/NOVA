import os
from dotenv import load_dotenv

load_dotenv()

from agent.nova import createNova
from agent.router import routeRequest


def main():
    print("NOVA (terminal mode). Type 'quit' to exit.\n")
    chat = createNova()
    while True:
        userText = input("You: ").strip()
        if userText.lower() == "quit":
            break
        if not userText:
            continue

        print("NOVA:", routeRequest(userText, chat))


if __name__ == "__main__":
    main()