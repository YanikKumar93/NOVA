"""
tools/webSearch.py — P3: Web & Information Tools

Three tools live here:
    searchWeb        general web lookup  (opens browser + Tavily summary)
    searchYoutube    video lookup        (opens browser)
    searchWikipedia  factual lookup      (text answer, no browser)

DESIGN RULES FOR THIS FILE (please keep these if you edit it):

1. NO TOOL EVER RAISES. Every function returns a plain string, always.
   agent/nova.py calls `fn(**args)` with no try/except around it, so an
   exception here kills the reply for that user. Failure = a sentence the
   model can read out loud, not a traceback.

2. NO NEW DEPENDENCIES. Only `requests` (already in requirements.txt) and
   the standard library. Nothing for anyone to pip-install on event day.

3. NO PROVIDER-SPECIFIC SEARCH. Gemini's google_search and OpenAI's
   Responses-API web_search are locked to one vendor and would break the
   "swap providers via OPENAI_BASE_URL" design. Tavily is a plain REST API
   and works no matter which model is answering.

4. FIRST DOCSTRING LINE IS THE TOOL DESCRIPTION. tools/toolSchema.py takes
   `doc.strip().split("\\n")[0]` — only the first LINE, not the first
   sentence. So each first line below is a complete, self-contained
   sentence on ONE line, even though it's long. Do not wrap it.

ENVIRONMENT VARIABLES (all optional except the Tavily key):
    TAVILY_API_KEY      enables web-search summaries
    NOVA_OPEN_BROWSER   set to 0 / false / no to stop tools opening tabs
    NOVA_HTTP_TIMEOUT   seconds to wait for a reply (default 8)
    NOVA_CONTACT        contact string put in the Wikipedia User-Agent
"""

import os
import re
import threading
import time
import urllib.parse
import webbrowser

import requests

# ---------------------------------------------------------------- settings

# Tool results are fed straight back into the model as another message, so
# every character here costs tokens on the follow-up request. Keep it tight.
MAX_SUMMARY_CHARS = 700

# (connect timeout, read timeout). A hung socket with no timeout freezes the
# whole terminal until the user kills the process — the worst event failure.
DEFAULT_TIMEOUT = 8.0

# Wikipedia's API policy requires a descriptive User-Agent. A bare
# "python-requests/2.x" from 200 machines on one campus network is exactly
# what their rate limiter blocks first.
CONTACT = os.environ.get("NOVA_CONTACT", "nova-student-project")
USER_AGENT = f"NOVA-StudentAssistant/1.0 ({CONTACT})"

# Identical queries are near-certain at a 200-person event ("weather in
# Delhi", "who is Virat Kohli"). Caching them keeps one shared Tavily key
# alive far longer and makes repeat demos instant.
CACHE_TTL_SECONDS = 900
CACHE_MAX_ENTRIES = 256

_cache = {}
_cacheLock = threading.Lock()


def _timeout() -> tuple:
    try:
        seconds = float(os.environ.get("NOVA_HTTP_TIMEOUT", DEFAULT_TIMEOUT))
    except ValueError:
        seconds = DEFAULT_TIMEOUT
    seconds = max(2.0, min(seconds, 20.0))
    return (min(5.0, seconds), seconds)


def _cacheGet(key: str):
    now = time.time()
    with _cacheLock:
        entry = _cache.get(key)
        if not entry:
            return None
        storedAt, value = entry
        if now - storedAt > CACHE_TTL_SECONDS:
            _cache.pop(key, None)
            return None
        return value


def _cacheSet(key: str, value: str) -> None:
    with _cacheLock:
        if len(_cache) >= CACHE_MAX_ENTRIES:
            oldest = min(_cache, key=lambda k: _cache[k][0])
            _cache.pop(oldest, None)
        _cache[key] = (time.time(), value)


def _clean(text: str, limit: int = MAX_SUMMARY_CHARS) -> str:
    """Flatten whitespace, swap typographic characters for ASCII, truncate.

    The character swap matters on Windows: a default cp1252 terminal raises
    UnicodeEncodeError on a curly quote or an en dash, which crashes the
    print() in main.py rather than my tool. See the note at the bottom of
    this file for the proper fix P6 should apply.
    """
    if not text:
        return ""
    replacements = {
        "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "-", "\u2026": "...", "\u00a0": " ",
        "\u200b": "", "\u2022": "-", "\u00ad": "",
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > limit:
        cut = text[:limit].rsplit(" ", 1)[0]
        text = cut + "..."
    return text


def _validQuery(query) -> str:
    """Return a usable query string, or "" if the model sent us junk."""
    if not isinstance(query, str):
        query = str(query or "")
    query = query.strip()
    if len(query) > 300:
        query = query[:300]
    return query


def _browserEnabled() -> bool:
    # Read the env var at call time, not import time — main.py loads .env
    # after this module is imported.
    flag = os.environ.get("NOVA_OPEN_BROWSER", "1").strip().lower()
    return flag not in ("0", "false", "no", "off")


def _openBrowser(url: str) -> bool:
    """Open a URL, returning whether it actually worked.

    webbrowser.open() returns False on a headless machine, but on some
    Linux setups it raises instead — both are handled.
    """
    if not _browserEnabled():
        return False
    try:
        return bool(webbrowser.open(url))
    except Exception:
        return False


# ------------------------------------------------------------- tavily call

def _tavilySummary(query: str):
    """Ask Tavily for a short answer. Returns (ok, text)."""
    apiKey = (os.environ.get("TAVILY_API_KEY") or "").strip()
    if not apiKey:
        return (False, "no key")

    payload = {
        "query": query,
        "max_results": 3,
        # WITHOUT include_answer THE RESPONSE HAS NO "answer" FIELD AT ALL.
        # The old code read data.get("answer") without setting this, so the
        # summary was silently always empty. This one line is the fix.
        "include_answer": True,
        "search_depth": "basic",
    }
    headers = {
        "Authorization": f"Bearer {apiKey}",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    }

    try:
        response = requests.post(
            "https://api.tavily.com/search",
            json=payload,
            headers=headers,
            timeout=_timeout(),
        )

        # Older Tavily docs put the key in the JSON body instead of a header.
        # If the header form is rejected, fall back once so the tool keeps
        # working on whichever form the account expects.
        if response.status_code in (401, 403):
            response = requests.post(
                "https://api.tavily.com/search",
                json=dict(payload, api_key=apiKey),
                timeout=_timeout(),
            )

        if response.status_code in (401, 403):
            return (False, "bad key")
        if response.status_code == 429:
            return (False, "rate limited")
        if response.status_code >= 500:
            return (False, "server error")
        response.raise_for_status()

        data = response.json()

        answer = _clean(data.get("answer") or "")
        if answer:
            return (True, answer)

        # No synthesised answer came back, so stitch one from the result
        # snippets rather than telling the user we found nothing.
        pieces = []
        for item in (data.get("results") or [])[:3]:
            snippet = _clean(item.get("content") or "", 220)
            if snippet:
                pieces.append(snippet)
        if pieces:
            return (True, _clean(" ".join(pieces)))
        return (False, "empty")

    except requests.Timeout:
        return (False, "timeout")
    except requests.RequestException:
        return (False, "network")
    except ValueError:
        return (False, "bad json")
    except Exception:
        return (False, "unknown")


# ------------------------------------------------------------------ tools

def searchWeb(query: str) -> str:
    """Search the live web for current facts, prices, news, and explanations, and return a short summary.

    Args:
        query: The search terms to look up on the web.
    """
    query = _validQuery(query)
    if not query:
        return "I need something to search for. What should I look up?"

    searchUrl = "https://www.google.com/search?q=" + urllib.parse.quote(query)
    opened = _openBrowser(searchUrl)
    openedNote = "Opened the search in your browser. " if opened else ""

    cacheKey = "web:" + query.lower()
    cached = _cacheGet(cacheKey)
    if cached:
        return openedNote + cached

    ok, text = _tavilySummary(query)
    if ok:
        _cacheSet(cacheKey, text)
        return openedNote + text

    # Every failure below still tells the user something true and useful.
    messages = {
        "no key": "I don't have a search-summary key set up, so I can't read the results out - they're on screen.",
        "bad key": "My search key was rejected, so I can only show the page, not summarise it.",
        "rate limited": "The search service has hit its usage limit for now, so I can only show the page.",
        "timeout": "The search service took too long to answer, so I can only show the page.",
        "empty": "I couldn't find a clear answer for that, but the results are on screen.",
    }
    fallback = messages.get(text, "I couldn't fetch a summary just now, but the results are on screen.")
    if opened:
        return "Opened a search for '" + query + "'. " + fallback
    return "I couldn't open a browser here. " + fallback


def searchYoutube(query: str) -> str:
    """Search YouTube for a video and open the results in the browser.

    Args:
        query: What video to search YouTube for.
    """
    query = _validQuery(query)
    if not query:
        return "What video would you like me to find?"

    searchUrl = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(query)
    if _openBrowser(searchUrl):
        return f"Opened YouTube search results for '{query}'."
    return (
        f"I couldn't open a browser on this machine, but the YouTube results "
        f"for '{query}' are at: {searchUrl}"
    )


def searchWikipedia(query: str) -> str:
    """Look up a factual summary from Wikipedia and return it as text without opening a browser.

    Args:
        query: The topic, person or thing to look up on Wikipedia.
    """
    query = _validQuery(query)
    if not query:
        return "What would you like me to look up?"

    cacheKey = "wiki:" + query.lower()
    cached = _cacheGet(cacheKey)
    if cached:
        return cached

    # One request instead of two: `generator=search` finds the best-matching
    # page and `prop=extracts` returns its intro in the same response. Half
    # the requests means half the chance of being throttled at the event.
    params = {
        "action": "query",
        "format": "json",
        "formatversion": 2,
        "prop": "extracts",
        "exintro": 1,
        "explaintext": 1,
        "redirects": 1,
        "generator": "search",
        "gsrsearch": query,
        "gsrlimit": 1,
    }

    try:
        response = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params=params,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            timeout=_timeout(),
        )
        if response.status_code == 429:
            return "Wikipedia is rate-limiting us at the moment. Try again in a few seconds."
        response.raise_for_status()
        data = response.json()

        pages = (data.get("query") or {}).get("pages") or []
        if not pages:
            return f"I couldn't find a Wikipedia article about '{query}'."

        page = pages[0]
        if page.get("missing"):
            return f"I couldn't find a Wikipedia article about '{query}'."

        title = page.get("title") or query
        extract = _clean(page.get("extract") or "")
        if not extract:
            return f"I found a Wikipedia page called '{title}', but it has no summary text."

        result = f"From Wikipedia ({title}): {extract}"
        _cacheSet(cacheKey, result)
        return result

    except requests.Timeout:
        return "Wikipedia took too long to respond. Try again in a moment."
    except requests.RequestException:
        return "I couldn't reach Wikipedia just now - check the internet connection."
    except ValueError:
        return "Wikipedia sent back something I couldn't read. Try again."
    except Exception:
        return f"Something went wrong looking up '{query}' on Wikipedia."


# --------------------------------------------------------------- self-test
#
# Run this file directly to prove all three tools work WITHOUT starting the
# agent, paying for a model call, or needing anyone else's module to be
# finished:   python -m tools.webSearch
#
if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    # Don't spray browser tabs while testing.
    os.environ.setdefault("NOVA_OPEN_BROWSER", "0")

    print("TAVILY_API_KEY set:", bool(os.environ.get("TAVILY_API_KEY")))
    print("timeout:", _timeout())
    print()

    checks = [
        ("searchWikipedia", lambda: searchWikipedia("Alan Turing")),
        ("searchWikipedia (nonsense)", lambda: searchWikipedia("qwtzzzxk not a real page")),
        ("searchWeb", lambda: searchWeb("current price of gold in india")),
        ("searchWeb (cached)", lambda: searchWeb("current price of gold in india")),
        ("searchYoutube", lambda: searchYoutube("lofi study music")),
        ("empty query", lambda: searchWeb("")),
        ("wrong type", lambda: searchWeb(None)),
    ]

    failures = 0
    for name, call in checks:
        try:
            output = call()
            assert isinstance(output, str) and output, "tool returned no text"
            print(f"[ok]   {name}\n       {output[:200]}\n")
        except Exception as error:
            failures += 1
            print(f"[FAIL] {name}: {type(error).__name__}: {error}\n")

    print("all tools returned a string" if not failures else f"{failures} failure(s)")