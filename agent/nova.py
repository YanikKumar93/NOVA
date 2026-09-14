"""
project is built entirely different now, it relises on openai instead of google SDK, it can accept many diff
agents through openRouter(or others if needed). but each agent should be checked for tool schema compatibility

this version of nova does NOT store chat history in `chat` like gemini-sdk did. its stateless
"""

import os
import json
import time
 
from openai import OpenAI
import openai
 
from tools.toolSchema import functionToToolSchema
from tools.webSearch import searchWeb, searchYoutube, searchWikipedia
#from tools.files import create_folder, create_file, read_file #PLACEHOLDER
#from tools.weather import get_weather #PLACEHOLDER
from agent.systemprompt import PROMPT
 

toolBox = [
    searchWeb,
    searchYoutube,
    searchWikipedia
    #get_weather,
    #create_folder,
    #create_file,
    #read_file,
]
#different from gemini, pls see this in detail once. it uses toolschema now to get a general gist of syntax
toolSchemas = [functionToToolSchema(fn) for fn in toolBox]
toolMap = {fn.__name__: fn for fn in toolBox}
 

 
# Model names change often,see README for how to list what's currently
# available on whichever provider OPENAI_BASE_URL points at.
MODEL = os.environ.get("NOVA_MODEL", "gpt-5")
 
 
def getClient() -> OpenAI:
    apiKey = os.environ.get("OPENAI_API_KEY")
    if not apiKey:
        raise RuntimeError(
            "No API key found. Set OPENAI_API_KEY in your .env file first "
            "(see the README). Never paste a key directly into code."
        )
    # leave OPENAI_BASE_URL unset for real OpenAI, or point it at other supported ones (test krlena tb bhi ek baar)
    baseUrl = os.environ.get("OPENAI_BASE_URL") or None
    if baseUrl:
        return OpenAI(api_key=apiKey, base_url=baseUrl, max_retries=0)

    # An empty OPENAI_BASE_URL overrides the SDK's default endpoint.
    os.environ.pop("OPENAI_BASE_URL", None)
    return OpenAI(api_key=apiKey, max_retries=0)
 

def createNova() -> list:
    """Return a fresh conversation: a plain list of message dicts,
    starting with the system instruction. This list IS "the chat" from
    here on, ask_nova() appends to it in place and returns it.
    """
    getClient()
    return [{"role": "system", "content":PROMPT}]
 
  #Frankly, ive no idea what exception handling is happening inside here
def askNova(chat: list, message: str, tries: int = 1) -> str:
    """Send one message to NOVA and get its text reply back.
 
    Runs the manual tool-calling loop: send messages -> check for
    tool_calls -> execute the matching Python function -> send the
    result back -> get the final reply.

    """
    client = getClient()
    chat.append({"role": "user", "content": message})
 
    lastError = None
    for attempt in range(tries):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=chat,
                tools=toolSchemas,
            )
            msg = response.choices[0].message
 
            if msg.tool_calls:
                # we are turning the chat history as a saveable dict, so if we switch models the history wont be lost
                chat.append({
                    "role": "assistant",
                    "content": msg.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in msg.tool_calls
                    ],
                })
 
                for toolCall in msg.tool_calls:
                    fn = toolMap[toolCall.function.name]
                   
                    #we are acccepting argument as json and converting it to dict. the SDK did this by itself previously
                    #(in all honesty i used claude for this, idk which key value pairs to take)
                    args = json.loads(toolCall.function.arguments)
                    result = fn(**args)
                    chat.append({
                        "role": "tool",
                        "tool_call_id": toolCall.id,
                        "content": str(result),
                    })
 
                # One more call so the model can phrase a final reply
                # using the tool result(s) we just appended.
                # followup = client.chat.completions.create(model=MODEL, messages=chat)
                followup = client.chat.completions.create(
                    model=MODEL,
                    messages=chat,
                    tools=toolSchemas,
                )
                finalText = followup.choices[0].message.content
                chat.append({"role": "assistant", "content": finalText})
                return finalText
 
            
            chat.append({"role": "assistant", "content": msg.content})
            return msg.content
 
        except openai.RateLimitError:
            return (
                f"The provider at {client.base_url} rate-limited this request "
                "(HTTP 429). Wait a moment and try again; repeated retries "
                "will not bypass the provider's limit."
            )
        except openai.AuthenticationError:
            return (
                "My API key doesn't seem to be working. Double-check "
                "OPENAI_API_KEY in your .env file and try again."
            )
        except openai.NotFoundError as error:
            return (
                f"The model '{MODEL}' isn't available on this API. "
                "Update NOVA_MODEL (or the MODEL default in agent/nova.py) "
                f"— see the README for how to check current model names. ({error})"
            )
        except Exception as error:
            lastError = error
            time.sleep(1.5 * (attempt + 1))
 
    return f"The AI service was busy and didn't answer. ({type(lastError).__name__}: {lastError})"
