
import os
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv
from tools.websearch import search_web, search_youtube
from tools.filehandling import create_folder, create_file, read_file
from tools.weather import get_weather


#TOOLBOX FOR NOWWWWW, WILL BE KEPT UPDATED AS MORE TOOLS ARE ADDED. I CREATED THESE TOOLS WITH CLAUDE FOR A QUICK TEST. THEY ARE RUDIMENTARY, PLS ADD KHUDSE BANAKE
TOOLBOX = [
    search_web,
    get_weather,
    create_folder,
    create_file,
    read_file,
    search_youtube
]

#PERSONALITY, PPL CAN CHANGE THIS
SYSTEM_INSTRUCTION = (
    "You are NOVA, a friendly voice-controlled desktop assistant. "
    "When the user asks you to DO something (search the web, search on youtube check the "
    "weather, create a file or folder, or read a file), use one of your "
    "tools instead of only describing it. After a tool runs, tell the user "
    "in one short, warm sentence what you did. Keep replies brief." #ill expand this as more tools are added
)

load_dotenv()
def create_nova():
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "No Gemini API key found. Set GEMINI_API_KEY in your .env file "
            "first (see the README). Never paste your key directly into code."
        )

    client = genai.Client(api_key=api_key)


    chat = client.chats.create(
        model="gemini-3.6-flash",
        config=types.GenerateContentConfig(
            tools=TOOLBOX,
            system_instruction=SYSTEM_INSTRUCTION,
        ),
    )
    chat._nova_client = client
    return chat

#ERROR HANDLING MJJE KHUD SMJH NI AAYI, I ASKED COPILOT WHY CODE ISNT WORKING AND IT ADDDED THIS AND SOMEHOW IT WORKS NOW
def ask_nova(chat, message: str, tries: int = 3) -> str:
    last_error = None
    for attempt in range(tries):
        try:
            return chat.send_message(message).text
        except Exception as error:
            last_error = error
            text = str(error)

           
            if "RESOURCE_EXHAUSTED" in text or "429" in text:
                return (
                    "I've hit today's free usage limit for the Gemini API. "
                    "Please try again later, or use an API key with billing "
                    "enabled."
                )

            
            if "API_KEY" in text or "PERMISSION_DENIED" in text or "401" in text:
                return (
                    "My API key doesn't seem to be working. Double-check "
                    "GEMINI_API_KEY in your .env file and try again."
                )

            
            if "NOT_FOUND" in text and "model" in text.lower():
                return (
                    "The Gemini model name set in agent/nova.py is no longer "
                    "available. Update the `model=` value — see the README "
                    "for how to check which models are currently live."
                )

            time.sleep(1.5 * (attempt + 1))

    return f"The AI service was busy and didn't answer. ({last_error})"