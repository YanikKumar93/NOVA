
import os
from dotenv import load_dotenv

load_dotenv()

from agent.nova import create_nova, ask_nova 


def main():
    print("NOVA (terminal mode). Type 'quit' to exit.\n")
    chat = create_nova()
    while True:
        user_text = input("You: ").strip()
        if user_text.lower() == "quit":
            break
        if not user_text:
            continue
        print("NOVA:", ask_nova(chat, user_text))


if __name__ == "__main__":
    main()