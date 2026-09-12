
import os
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv
from tools.websearch import searchWeb, searchYoutube
from tools.filehandling import createFolder, createFile, readFile
from tools.weather import getWeather


#TOOLBOX FOR NOWWWWW, WILL BE KEPT UPDATED AS MORE TOOLS ARE ADDED. I CREATED THESE TOOLS WITH CLAUDE FOR A QUICK TEST. THEY ARE RUDIMENTARY, PLS ADD KHUDSE BANAKE
TOOLBOX = [
    searchWeb,
    getWeather,
    createFolder,
    createFile,
    readFile,
    searchYoutube
]

#PERSONALITY, PPL CAN CHANGE THIS
systemInstruction = (
    "You are NOVA, a friendly voice-controlled desktop assistant. "
    "When the user asks you to DO something (search the web, search on youtube check the "
    "weather, create a file or folder, or read a file), use one of your "
    "tools instead of only describing it. After a tool runs, tell the user "
    "in one short, warm sentence what you did. Keep replies brief." #ill expand this as more tools are added
)

load_dotenv()
def createNova():
    
    apiKey = os.environ.get("GEMINI_API_KEY")
    if not apiKey:
        raise RuntimeError(
            "No Gemini API key found. Set GEMINI_API_KEY in your .env file "
            "first (see the README). Never paste your key directly into code."
        )

    client = genai.Client(api_key=apiKey)


    chat = client.chats.create(
        model="gemini-3.6-flash",
        config=types.GenerateContentConfig(
            tools=TOOLBOX,
            system_instruction=systemInstruction,
        ),
    )
    chat._novaClient = client
    return chat

#ERROR HANDLING MJJE KHUD SMJH NI AAYI, I ASKED COPILOT WHY CODE ISNT WORKING AND IT ADDDED THIS AND SOMEHOW IT WORKS NOW
def askNova(chat, message: str, tries: int = 3) -> str:
    lastError = None
    for attempt in range(tries):
        try:
            return chat.send_message(message).text
        except Exception as error:
            lastError = error
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

    return f"The AI service was busy and didn't answer. ({lastError})"