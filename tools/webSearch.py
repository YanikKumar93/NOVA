"""
tools/web_search.py — real-time web search.

Two things happen here:

1. It actually opens your real browser to the search results, via
   Python's built-in `webbrowser` module — works because NOVA runs
   LOCALLY on your own machine.
2. It fetches real search results via Tavily's search API, so NOVA has
   something to actually say back to you — a real summary, not just
   "opened your browser."

WHY TAVILY, NOT A PROVIDER'S BUILT-IN SEARCH TOOL: Gemini's built-in
google_search and OpenAI's Responses-API web_search are both PROVIDER-
SPECIFIC. Using either one would silently break the whole "swap LLM
providers by changing OPENAI_BASE_URL" design agent/nova.py depends on.
Tavily is a plain, portable REST API — it works no matter which LLM
provider is answering the actual conversation.

Needs a free API key from tavily.com — set TAVILY_API_KEY in .env. No
key on hand yet? This still works: it just skips the spoken summary and
tells the user it opened a search.
"""
#ASKED COPILOT TO PROVIDE HELP WITH SMTH THATLL EAT LESS TOKENS, THIS IS WHAT IT SAID. KEPT THE ABOVE COMMENT SO ITLL
#HELP OTHERS TOO

import os
import urllib.parse
import webbrowser

import requests


def searchWeb(query: str) -> str:
    """Search the general web for a query, open the results in the
    browser, and summarize what was found.

    Use this:
    for factual or informational questions — news, prices,
    "what is X", "who is Y", general lookups. 
    Do NOT use this for:
    videos — use search_youtube for anything about watching, opening,
    or playing a video.

    Args:
        query: What to search for.
    """
    # shifted from gemini figuring out the tool to open website to pythons webbrowser package, will reduce latency i hope
    #yaar we cant do much abt default search engine warna work will increase and im tired as hell, so we will only give them google engine *nerd emoji*
    search_url = "https://www.google.com/search?q=" + urllib.parse.quote(query)
    webbrowser.open(search_url)

    # 2. Using tavily, so our openRouter credits wont get used in summarizing.
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        return f"Opened a search for '{query}' (set TAVILY_API_KEY in .env for a spoken summary too)."

    try:
        response = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": api_key, "query": query, "max_results": 3},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("answer") or f"Opened a search for '{query}'."
    except requests.RequestException:
        #incase tavily reaches max credits
        return f"Opened a search for '{query}', but couldn't fetch a summary right now."


def searchYoutube(query: str) -> str:
    """Search YouTube for a video and open the results in the browser.

    Use this whenever the user wants to watch, open, play, or find a
    video — phrases like "open this video about X", "play X on youtube",
    "search youtube for X", "find a video of X", or just "open this
    video" when X was mentioned earlier in the conversation. Do NOT use
    this for general questions or non-video searches — use search_web
    for those instead.

    Args:
        query: What video to search for.
    """
    search_url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(query)
    webbrowser.open(search_url)
    return f"Opened YouTube search results for '{query}'."