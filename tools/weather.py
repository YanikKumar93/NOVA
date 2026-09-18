"""Weather tool for NOVA."""
import os
from dotenv import load_dotenv
from tools.client import get_json
from tools.webSearch import searchWeb

load_dotenv()

URL = "https://api.openweathermap.org/data/2.5/weather"

def get_weather(city: str) -> str:
    """
    Get current weather for a city.
        Args:
            city: Name of the city, e.g. "Delhi".
    Returns a short spoken-friendly sentence.
    """
    if not city or not city.strip():
        return "I need a city name to check the weather."

    apiKey = os.getenv("OPENWEATHER_API_KEY")
    if not apiKey:
        return searchWeb(
            f"current weather in {city.strip()}",
            openInBrowser=True,
        )

    params = {"q": city.strip(), "appid": apiKey, "units": "metric"}
    data, error = get_json(URL, params)

    if error:
        return f"I couldn't get the weather for {city} — {error}."

    try:
        description = data["weather"][0]["description"]
        temp = round(data["main"]["temp"])
        feels = round(data["main"]["feels_like"])
        humidity = data["main"]["humidity"]
        name = data["name"]
    except (KeyError, IndexError, TypeError):
        return f"I got an unexpected response while checking the weather for {city}."

    return (f"{name}: {temp} degrees, {description}. "
            f"Feels like {feels}, humidity {humidity} percent.")