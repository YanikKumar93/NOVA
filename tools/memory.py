"""
tools/memory.py — persistent key facts about the user.

Survives restarts. Injected into the chat on createNova().
NO TOOL EVER RAISES — always returns a plain string.
"""

import json
import os
import threading

MEMORY_FILE = os.environ.get("NOVA_MEMORY_FILE", "nova_memory.json")
_lock = threading.Lock()


def _load() -> dict:
    if not os.path.exists(MEMORY_FILE):
        return {}
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save(data: dict) -> None:
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def formatMemoriesForPrompt() -> str:
    """Used by createNova — not a tool."""
    data = _load()
    if not data:
        return ""
    lines = [f"- {k}: {v}" for k, v in data.items()]
    return "Known facts about the user:\n" + "\n".join(lines)


def save_memory(key: str, value: str) -> str:
    """Save a lasting fact about the user so it is remembered in future chats.

    Args:
        key: Short label for the fact (e.g. name, city, favorite_language).
        value: The fact to remember.
    """
    if not key or not str(key).strip():
        return "Memory key cannot be empty."
    if value is None or not str(value).strip():
        return "Memory value cannot be empty."

    key = str(key).strip().lower().replace(" ", "_")
    value = str(value).strip()

    try:
        with _lock:
            data = _load()
            data[key] = value
            _save(data)
        return f"Remembered {key}: {value}"
    except Exception as error:
        return f"Could not save memory: {error}"


def recall_memory(key: str = "") -> str:
    """Recall saved facts about the user. Pass a key for one fact, or leave empty for all.

    Args:
        key: Optional fact label to look up. Leave empty to list everything saved.
    """
    try:
        data = _load()
        if not data:
            return "I have no saved memories yet."

        key = (key or "").strip().lower().replace(" ", "_")
        if key:
            if key in data:
                return f"{key}: {data[key]}"
            return f"No memory saved for '{key}'."

        lines = [f"- {k}: {v}" for k, v in data.items()]
        return "Saved memories:\n" + "\n".join(lines)
    except Exception as error:
        return f"Could not read memory: {error}"


def forget_memory(key: str) -> str:
    """Delete one saved fact about the user.

    Args:
        key: The fact label to forget.
    """
    if not key or not str(key).strip():
        return "Memory key cannot be empty."

    key = str(key).strip().lower().replace(" ", "_")

    try:
        with _lock:
            data = _load()
            if key not in data:
                return f"No memory saved for '{key}'."
            del data[key]
            _save(data)
        return f"Forgot '{key}'."
    except Exception as error:
        return f"Could not forget memory: {error}"