"""Run this directly to test all API tools without the agent."""
import time
from tools import get_weather, get_news, convert_currency


def check(label, result):
    print(f"\n[{label}]")
    print(result)
    assert isinstance(result, str), "TOOL RETURNED A NON-STRING"
    assert result.strip(), "TOOL RETURNED AN EMPTY STRING"
    time.sleep(1)


if __name__ == "__main__":
    check("weather: normal", get_weather("Delhi"))
    check("weather: bad city", get_weather("Delhiiii"))
    check("weather: empty", get_weather(""))

    check("news: top", get_news())

    check("currency: normal", convert_currency(500, "USD", "INR"))
    check("currency: bad code", convert_currency(50, "USD", "XYZ"))
    check("currency: bad amount", convert_currency("abc", "USD", "INR"))

    print("\nAll tools returned valid strings.")