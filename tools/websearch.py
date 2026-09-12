import os
import urllib.parse
import webbrowser

from google import genai
from google.genai import types

_search_client = None 
                        


def _get_client():
    global _search_client
    if _search_client is None:
        _search_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    return _search_client


def search_web(query: str) -> str:
    """Search the web for a query, open the results in the browser, and
    summarize what was found.

    Use this whenever the user asks to search for something, or asks a
    question needing current or real-world information. it can be news, facts,
    prices, "what is X", "who is Y", and similar. Use search_youtube function instead of search_web
    if asked to search for a yt video

    Args:
        query: What to search for.
    """
   
    search_url = "https://www.google.com/search?q=" + urllib.parse.quote(query)
    webbrowser.open(search_url)

    # 2. A grounded summary, so NOVA has something real to say.
    client = _get_client()
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=query,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
        ),
    )
    return response.text

def search_youtube(query: str) -> str:
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
