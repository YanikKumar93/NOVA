"""OpenAI-compatible NOVA agent with tool calling and provider fallback."""

import json
import os
import time

import openai
from openai import OpenAI

from agent.fallback import friendly_provider_error, safe_call, secondary_model
from agent.systemprompt import PROMPT
from tools.currency import convert_currency
from tools.files import create_file, create_folder, edit_file, read_file
from tools.memory import (
    forget_memory,
    formatMemoriesForPrompt,
    recall_memory,
    save_memory,
)
from tools.news import get_news
from tools.rag import ask_document, ingest_document
from tools.toolSchema import functionToToolSchema
from tools.weather import get_weather
from tools.webSearch import searchWeb, searchWikipedia, searchYoutube


toolBox = [
    searchWeb,
    searchYoutube,
    searchWikipedia,
    create_folder,
    create_file,
    read_file,
    edit_file,
    get_weather,
    get_news,
    convert_currency,
    save_memory,
    recall_memory,
    forget_memory,
    ingest_document,
    ask_document,
]
toolSchemas = [functionToToolSchema(fn) for fn in toolBox]
toolMap = {fn.__name__: fn for fn in toolBox}

MODEL = os.environ.get("NOVA_MODEL", "gpt-4o-mini")


def getClient() -> OpenAI:
    apiKey = os.environ.get("OPENAI_API_KEY")
    if not apiKey:
        raise RuntimeError("No API key found. Set OPENAI_API_KEY in your .env file first.")

    baseUrl = os.environ.get("OPENAI_BASE_URL") or None
    if baseUrl:
        return OpenAI(api_key=apiKey, base_url=baseUrl, max_retries=0)

    os.environ.pop("OPENAI_BASE_URL", None)
    return OpenAI(api_key=apiKey, max_retries=0)




def askNova(
    chat: list,
    message: str,
    tries: int = 2,
    agentLog: dict | None = None,
) -> str:
    """Send one message to NOVA with tool calling and model fallback."""
    agentLog = agentLog if agentLog is not None else {}
    agentLog.setdefault("agentToolCalls", [])
    agentLog.setdefault("fallbackTriggered", False)
    client = getClient()
    chat.append({"role": "user", "content": message})

    modelsToTry = [MODEL]
    backup = secondary_model()
    if backup and backup not in modelsToTry:
        modelsToTry.append(backup)

    lastError = None
    for currentModel in modelsToTry:
        if currentModel != MODEL:
            agentLog["fallbackTriggered"] = True
        for attempt in range(max(1, tries)):
            try:
                response = client.chat.completions.create(
                    model=currentModel,
                    messages=chat,
                    tools=toolSchemas,
                )
                for _ in range(5):
                    msg = response.choices[0].message

                    if not msg.tool_calls:
                        text = msg.content or "The action completed, but NOVA did not provide a written response."
                        chat.append({"role": "assistant", "content": text})
                        return text

                    chat.append(
                        {
                            "role": "assistant",
                            "content": msg.content,
                            "tool_calls": [
                                {
                                    "id": toolCall.id,
                                    "type": "function",
                                    "function": {
                                        "name": toolCall.function.name,
                                        "arguments": toolCall.function.arguments,
                                    },
                                }
                                for toolCall in msg.tool_calls
                            ],
                        }
                    )

                    for toolCall in msg.tool_calls:
                        functionName = toolCall.function.name
                        function = toolMap.get(functionName)
                        try:
                            arguments = json.loads(toolCall.function.arguments or "{}")
                            if not isinstance(arguments, dict):
                                arguments = {}
                            agentLog["agentToolCalls"].append(
                                {"tool": functionName, "arguments": arguments}
                            )
                            if function is None:
                                result = f"Unknown tool '{functionName}'."
                            else:
                                result = safe_call(
                                    function,
                                    **arguments,
                                    error_prefix=f"Tool '{functionName}' failed",
                                )
                        except (TypeError, ValueError):
                            agentLog["agentToolCalls"].append(
                                {"tool": functionName, "arguments": toolCall.function.arguments}
                            )
                            result = f"Tool '{functionName}' got invalid JSON arguments." #idk how this works 

                        chat.append(
                            {
                                "role": "tool",
                                "tool_call_id": toolCall.id,
                                "content": str(result),
                            }
                        )

                    response = client.chat.completions.create(
                        model=currentModel,
                        messages=chat,
                        tools=toolSchemas,
                    )

                return "tool call limit reach hogyi gng :( firse try karo ya model change krlo"

            except openai.AuthenticationError as error:
                return friendly_provider_error(error, currentModel, getattr(client, "base_url", None))
            except openai.NotFoundError as error:
                lastError = error
                break
            except openai.RateLimitError as error:
                lastError = error
                time.sleep(1.2 * (attempt + 1))
            except Exception as error:
                lastError = error
                time.sleep(1.0 * (attempt + 1))

    return friendly_provider_error(lastError, MODEL, getattr(client, "base_url", None))