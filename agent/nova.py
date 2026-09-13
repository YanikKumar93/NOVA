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
 
from tools.toolSchema import function_to_tool_schema
from tools.webSearch import searchWeb, searchYoutube
#from tools.files import create_folder, create_file, read_file #PLACEHOLDER
#from tools.weather import get_weather #PLACEHOLDER
from agent.systemprompt import PROMPT
 

TOOLBOX = [
    searchWeb,
    searchYoutube,
    #get_weather,
    #create_folder,
    #create_file,
    #read_file,
]
#different from gemini, pls see this in detail once. it uses toolschema now to get a general gist of syntax
TOOL_SCHEMAS = [function_to_tool_schema(fn) for fn in TOOLBOX]
TOOL_MAP = {fn.__name__: fn for fn in TOOLBOX}
 

 
# Model names change often,see README for how to list what's currently
# available on whichever provider OPENAI_BASE_URL points at.
MODEL = os.environ.get("NOVA_MODEL", "gpt-5")
 
 
def _get_client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "No API key found. Set OPENAI_API_KEY in your .env file first "
            "(see the README). Never paste a key directly into code."
        )
    # leave OPENAI_BASE_URL unset for real OpenAI, or point it at other supported ones (test krlena tb bhi ek baar)
    base_url = os.environ.get("OPENAI_BASE_URL") or None
    return OpenAI(api_key=api_key, base_url=base_url)
 

def create_nova() -> list:
    """Return a fresh conversation: a plain list of message dicts,
    starting with the system instruction. This list IS "the chat" from
    here on, ask_nova() appends to it in place and returns it.
    """
    _get_client()  
    return [{"role": "system", "content":PROMPT}]
 
  #Frankly, ive no idea what exception handling is happening inside here
def ask_nova(chat: list, message: str, tries: int = 3) -> str:
    """Send one message to NOVA and get its text reply back.
 
    Runs the manual tool-calling loop: send messages -> check for
    tool_calls -> execute the matching Python function -> send the
    result back -> get the final reply.

    """
    client = _get_client()
    chat.append({"role": "user", "content": message})
 
    last_error = None
    for attempt in range(tries):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=chat,
                tools=TOOL_SCHEMAS,
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
 
                for tool_call in msg.tool_calls:
                    fn = TOOL_MAP[tool_call.function.name]
                   
                    #we are acccepting argument as json and converting it to dict. the SDK did this by itself previously
                    #(in all honesty i used claude for this, idk which key value pairs to take)
                    args = json.loads(tool_call.function.arguments)
                    result = fn(**args)
                    chat.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(result),
                    })
 
                # One more call so the model can phrase a final reply
                # using the tool result(s) we just appended.
                followup = client.chat.completions.create(model=MODEL, messages=chat)
                final_text = followup.choices[0].message.content
                chat.append({"role": "assistant", "content": final_text})
                return final_text
 
            
            chat.append({"role": "assistant", "content": msg.content})
            return msg.content
 
        except openai.RateLimitError:
            return (
                "I've hit the usage limit for this API key. Please try "
                "again later, or use a key with more quota."
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
            last_error = error
            time.sleep(1.5 * (attempt + 1))
 
    return f"The AI service was busy and didn't answer. ({last_error})"
