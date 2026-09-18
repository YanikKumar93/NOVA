"""
agent/fallback.py — shared fallback helpers for NOVA.
"""

import os
import time
from typing import Any, Callable, Optional


def safe_call(fn: Callable, *args, error_prefix: str = "Tool failed", **kwargs) -> str:
    """Run any function and always return a string. Never raise."""
    try:
        result = fn(*args, **kwargs)
        if result is None:
            return f"{error_prefix}: got empty result."
        return str(result)
    except Exception as error:
        return f"{error_prefix}: {type(error).__name__}: {error}"


def secondary_model() -> Optional[str]:
    """Optional backup model from env. Example: NOVA_FALLBACK_MODEL=llama-3.3-70b-versatile"""
    model = (os.environ.get("NOVA_FALLBACK_MODEL") or "").strip()
    return model or None


def friendly_provider_error(
    error: Optional[Exception],
    model: str,
    base_url: Optional[str] = None,
) -> str:
    """Turn provider exceptions into short user-facing messages."""
    name = type(error).__name__ if error else "UnknownError"
    msg = str(error) if error else ""
    where = f" at {base_url}" if base_url else ""

    lowered = msg.lower()

    if "RateLimit" in name or "429" in msg:
        return (
            f"The provider{where} rate-limited this request. "
            "Wait a moment and try again, or switch provider/model in .env."
        )
    if "Auth" in name or "401" in msg or "403" in msg:
        return (
            "My API key doesn't seem to be working. "
            "Check OPENAI_API_KEY in your .env file."
        )
    if "NotFound" in name or "404" in msg:
        return (
            f"The model '{model}' isn't available on this API. "
            "Update NOVA_MODEL or NOVA_FALLBACK_MODEL."
        )
    if "timeout" in lowered or "Timeout" in name:
        return "The AI service timed out. Please try again."
    if "connect" in lowered or "connection" in lowered:
        return (
            f"Could not connect to the AI provider{where}. "
            "Check internet and OPENAI_BASE_URL."
        )

    return f"The AI service had a problem ({name}: {error})."


def with_retries(
    fn: Callable,
    tries: int = 2,
    delay: float = 1.0,
    *args,
    **kwargs,
) -> Any:
    """Retry a callable with simple backoff. Raises last error if all attempts fail."""
    last_error = None
    attempts = max(1, int(tries))
    for attempt in range(attempts):
        try:
            return fn(*args, **kwargs)
        except Exception as error:
            last_error = error
            if attempt < attempts - 1:
                time.sleep(delay * (attempt + 1))
    raise last_error