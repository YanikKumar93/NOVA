#current placeholder written by claude, since i wasnt too sure how to properly convert json to dict. my code kept having errors.
#this will be updated properly later. Or not if it works perfectly, but i will study it.

"""
agent/tool_schema.py — turns a plain Python function into the JSON
schema OpenAI-compatible APIs expect in `tools=[...]`.

Unlike google-genai, Chat Completions does NOT read a function's type
hints/docstring for you automatically — we have to hand it an explicit
schema ourselves. This helper does that inspection ONCE, here, so every
tool file (tools/*.py) gets to stay exactly as it already is: plain
functions, typed parameters, real docstrings. Nothing about the tool
interface P2/P3/P4 were given changes because of this provider switch.
"""

import inspect
import re

typeMap = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
}


def functionToToolSchema(func) -> dict:
    """Build one OpenAI-style tool schema entry from a function's
    signature and docstring.
    """
    sig = inspect.signature(func)
    doc = inspect.getdoc(func) or ""

    # First line of the docstring becomes the tool's description — this
    # is what the model reads to decide WHEN to call this tool, so a
    # vague first line means it gets picked at the wrong time.
    description = doc.strip().split("\n")[0] if doc else func.__name__

    # Pull per-argument descriptions out of a Google-style "Args:" block,
    # if the docstring has one — matches the style already used across
    # tools/files.py, tools/weather.py, tools/web_search.py.
    argDescriptions = {}
    match = re.search(r"Args:\s*\n(.*)", doc, re.DOTALL)
    if match:
        for line in match.group(1).strip().split("\n"):
            line = line.strip()
            if ":" in line:
                name, desc = line.split(":", 1)
                argDescriptions[name.strip()] = desc.strip()

    properties = {}
    required = []
    for name, param in sig.parameters.items():
        jsonType = typeMap.get(param.annotation, "string")
        properties[name] = {
            "type": jsonType,
            "description": argDescriptions.get(name, ""),
        }
        if param.default is inspect.Parameter.empty:
            required.append(name)

    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }