"""
tools/memory.py — persistent key facts about the user.

Survives restarts. Injected into the chat on createNova().
NO TOOL EVER RAISES — always returns a plain string.
"""

import json
import os
import re
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
        key: Short label for the fact (e.g. name, city, friend, favorite_language).
        value: The fact to remember.
    """
    if not key or not str(key).strip():
        return "Memory key cannot be empty."
    if value is None or not str(value).strip():
        return "Memory value cannot be empty."

    clean_key = re.sub(r"[^a-zA-Z0-9_]+", "_", str(key).strip().lower()).strip("_")
    val_str = str(value).strip()

    try:
        with _lock:
            data = _load()
            data[clean_key] = val_str
            _save(data)
        return f"Remembered {clean_key}: {val_str}"
    except Exception as error:
        return f"Could not save memory: {error}"


def _find_matching_key(search_key: str, data: dict) -> str | None:
    """find the best matching key in saved memories with fuzzy/normalized lookup."""
    if not search_key or not data:
        return None

    raw_clean = search_key.lower().replace("'s", "").replace("?", "").strip()
    norm = re.sub(r"\b(my|the|a|an|user|is|what|who|tell|me|about)\b", "", raw_clean).strip()
    clean_search = re.sub(r"[^a-zA-Z0-9_]+", "_", norm).strip("_")

    if search_key in data:
        return search_key
    if clean_search in data:
        return clean_search

    stemmed_search = re.sub(r"s\b", "", clean_search)
    if stemmed_search in data:
        return stemmed_search

    tokens = set(t for t in clean_search.split("_") if t)

    stemmed_tokens = set(re.sub(r"s\b", "", t) for t in tokens)
    all_tokens = tokens | stemmed_tokens
    
    specific_tokens = all_tokens - {"name", "val", "value", "key", "info"}
    search_set = specific_tokens if specific_tokens else all_tokens

    best_key = None
    best_score = 0

    for k in data:
        k_clean = k.lower()
        k_stemmed = re.sub(r"s\b", "", k_clean)
        k_tokens = set(t for t in k_clean.split("_") if t)
        k_tokens.add(k_stemmed)

        overlap = len(search_set & k_tokens)
        if overlap > best_score:
            best_score = overlap
            best_key = k
        elif any(st in k_clean or k_clean in st for st in search_set) and best_score == 0:
            best_key = k

    return best_key


def recall_memory(key: str = "") -> str:
    """recall saved facts about the user. pass a key for a fact, leave empty to just get everything

    """
    try:
        data = _load()
        if not data:
            return "I have no saved memories yet."

        clean_key = (key or "").strip()
        if clean_key:
            matched_key = _find_matching_key(clean_key, data)
            if matched_key:
                return f"{matched_key}: {data[matched_key]}"
            return f"No memory saved for '{clean_key}'."

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

    try:
        with _lock:
            data = _load()
            matched_key = _find_matching_key(key, data) or key.strip().lower().replace(" ", "_")
            if matched_key not in data:
                return f"No memory saved for '{key}'."
            del data[matched_key]
            _save(data)
        return f"Forgot '{matched_key}'."
    except Exception as error:
        return f"Could not forget memory: {error}"