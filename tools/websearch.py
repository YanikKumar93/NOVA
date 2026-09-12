
import os

from google import genai
from google.genai import types

_search_client = None 


def _get_client():
    global _search_client
    if _search_client is None:
        _search_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    return _search_client


def search_web(query: str) -> str:
    """Search the web for up-to-date information and summarize the answer.

    Use this whenever the user asks something that needs current or
    real-world information you wouldn't already know — news, facts,
    prices, "what is X", "who is Y", and similar. Not for opening a
    specific website by name.

    Args:
        query: What to search for.
    """
    client = _get_client()
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=query,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
        ),
    )
    return response.text