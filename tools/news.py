"""News headlines tool for NOVA."""
import os
from dotenv import load_dotenv
from tools.client import get_json

load_dotenv()

URL = "https://gnews.io/api/v4/top-headlines"

CATEGORIES = {"general", "world", "nation", "business", "technology",
              "entertainment", "sports", "science", "health"}


def get_news(topic: str = "", count: int = 5) -> str:
    """
    Get current news headlines, optionally about a topic.
    Args:
    topic: Optional subject, e.g. "technology". Leave empty for top headlines.
    count: How many headlines, 1 to 10.
    Returns a short numbered list as plain text.
    """
    API_KEY = os.getenv("GNEWS_API_KEY")
    if not API_KEY:
        return "News isn't set up yet — the API key is missing."

    count = max(1, min(count, 10))

    params = {"apikey": API_KEY, "lang": "en", "max": count}
    if topic and topic.strip():
        cleaned = topic.strip()
        if cleaned.lower() in CATEGORIES:
            params["category"] = cleaned.lower()
        else:
            params["q"] = cleaned
            params["in"] = "title"
    else:
        params["category"] = "general"

    data, error = get_json(URL, params)

    if error:
        return f"I couldn't get the news — {error}."

    articles = data.get("articles", []) if isinstance(data, dict) else []

    if not articles:
        subject = f" about {topic}" if topic else ""
        return f"I didn't find any news{subject} right now."

    lines = []
    seen = set()
    for article in articles:
        if not isinstance(article, dict):
            continue
        title = article.get("title", "").strip()
        sourceData = article.get("source")
        source = sourceData.get("name", "").strip() if isinstance(sourceData, dict) else ""
        if not title:
            continue
        key = title.lower()
        if key in seen:
            continue
        seen.add(key)
        lines.append(f"{len(lines) + 1}. {title}" + (f" ({source})" if source else ""))
        if len(lines) >= count:
            break

    if not lines:
        return "I found news results but couldn't read them properly."

    heading = f"Here's the latest on {topic}:" if topic else "Here are the top headlines:"
    return heading + "\n" + "\n".join(lines)