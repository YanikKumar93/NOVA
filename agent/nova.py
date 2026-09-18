"""
agent/nova.py — OpenAI-compatible client, tool-calling loop, fallbacks.
"""

import os
import json
import time

from openai import OpenAI
import openai

from tools.toolSchema import functionToToolSchema
from tools.webSearch import searchWeb, searchYoutube, searchWikipedia
from tools.files import create_folder, create_file, read_file, edit_file
from tools.memory import (
    save_memory,
    recall_memory,
    forget_memory,
    formatMemoriesForPrompt,
)
from tools.rag import ingest_document, ask_document
from agent.systemprompt import PROMPT
from agent.fallback import safe_call, friendly_provider_error, secondary_model


toolBox = [
    searchWeb,
    searchYoutube,
    searchWikipedia,
    create_folder,
    create_file,
    read_file,
    edit_file,
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
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "No API key found. Set OPENAI_API_KEY in your .env file first."
        )

    base_url = os.environ.get("OPENAI_BASE_URL") or None
    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url, max_retries=0)

    os.environ.pop("OPENAI_BASE_URL", None)
    return OpenAI(api_key=api_key, max_retries=0)


def createNova() -> list:
    """Return a fresh conversation with system prompt + saved user facts."""
    getClient()
    chat = [{"role": "system", "content": PROMPT}]

    memory_text = formatMemoriesForPrompt()
    if memory_text:
        chat.append({"role": "system", "content": memory_text})

    return chat


def askNova(chat: list, message: str, tries: int = 2) -> str:
    """Send one message to NOVA with tool-calling + provider/model fallback."""
    client = getClient()
    chat.append({"role": "user", "content": message})

    models_to_try = [MODEL]
    backup = secondary_model()
    if backup and backup not in models_to_try:
        models_to_try.append(backup)

    last_error = None

    for current_model in models_to_try:
        for attempt in range(max(1, tries)):
            try:
                response = client.chat.completions.create(
                    model=current_model,
                    messages=chat,
                    tools=toolSchemas,
                )
                msg = response.choices[0].message

                if msg.tool_calls:
                    chat.append(
                        {
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
                        }
                    )

                    for tool_call in msg.tool_calls:
                        fn_name = tool_call.function.name
                        fn = toolMap.get(fn_name)

                        if fn is None:
                            result = (
                                f"Unknown tool '{fn_name}'. "
                                f"Available: {', '.join(toolMap)}"
                            )
                        else:
                            try:
                                args = json.loads(tool_call.function.arguments or "{}")
                                if not isinstance(args, dict):
                                    args = {}
                            except Exception:
                                args = {}
                                result = (
                                    f"Tool '{fn_name}' got invalid JSON arguments."
                                )
                            else:
                                result = safe_call(
                                    fn,
                                    **args,
                                    error_prefix=f"Tool '{fn_name}' failed",
                                )

                        chat.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": str(result),
                            }
                        )

                    followup = client.chat.completions.create(
                        model=current_model,
                        messages=chat,
                        tools=toolSchemas,
                    )
                    final_text = followup.choices[0].message.content or "Done."
                    chat.append({"role": "assistant", "content": final_text})
                    return final_text

                text = msg.content or ""
                chat.append({"role": "assistant", "content": text})
                return text

            except openai.RateLimitError as error:
                last_error = error
                time.sleep(1.2 * (attempt + 1))
            except openai.AuthenticationError as error:
                return friendly_provider_error(
                    error, current_model, getattr(client, "base_url", None)
                )
            except openai.NotFoundError as error:
                last_error = error
                break  # try fallback model if available
            except Exception as error:
                last_error = error
                time.sleep(1.0 * (attempt + 1))

    return friendly_provider_error(
        last_error, MODEL, getattr(client, "base_url", None)
    )