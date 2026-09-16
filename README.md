# NOVA API Tools (P4)

## Import

    from tools import get_weather, get_news, convert_currency

## Contract

All functions take simple arguments, return a plain string, and never raise.
Failures return a readable sentence, so the agent can speak them directly.

## Functions

### get_weather(city: str) -> str
Current weather for a city.
- `city` — city name, e.g. "Delhi"

Example: `Delhi: 30 degrees, broken clouds. Feels like 37, humidity 84 percent.`

### get_news(topic: str = "", count: int = 5) -> str
Current headlines. Leave `topic` empty for general news.
- `topic` — optional. Recognised categories: general, world, nation,
  business, technology, entertainment, sports, science, health.
  Anything else is treated as a keyword search.
- `count` — 1 to 10. Values outside that range are clamped.

Example: `Here are the top headlines:\n1. ... \n2. ...`

### convert_currency(amount: float, from_currency: str, to_currency: str) -> str
Convert between currencies using live rates.
- `amount` — number greater than zero
- `from_currency` / `to_currency` — 3-letter codes, e.g. "USD", "INR"

Example: `500 USD is about 47,837.27 INR.`

Note: the agent must map spoken words to codes ("rupees" → INR).

## Setup

    pip install requests python-dotenv

Copy `.env.example` to `.env` and fill in:

    OPENWEATHER_API_KEY=
    GNEWS_API_KEY=

Currency needs no key.

## Testing

    python -m tools.test_tools