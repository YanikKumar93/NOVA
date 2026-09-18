"""Currency conversion tool for NOVA."""
from tools.client import get_json

URL = "https://open.er-api.com/v6/latest/"


def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """
    Convert an amount from one currency to another.
    Args:
    amount: How much to convert, e.g. 500.
    from_currency: 3-letter code, e.g. "USD".
    to_currency: 3-letter code, e.g. "INR".
    Returns a short spoken-friendly sentence.
    """
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return "I need a number to convert."

    if amount <= 0:
        return "I need an amount greater than zero."

    if not isinstance(from_currency, str) or not isinstance(to_currency, str):
        return "I need both currencies to convert between."

    source = from_currency.strip().upper()
    target = to_currency.strip().upper()

    if not source or not target:
        return "I need both currencies to convert between."
    if source == target:
        return f"{amount:g} {source} is just {amount:g} {source}."

    data, error = get_json(URL + source)

    if error:
        return f"I couldn't convert that — {error}."

    if not isinstance(data, dict) or data.get("result") != "success":
        return f"I don't recognise the currency {source}."

    rates = data.get("rates", {})
    rate = rates.get(target)

    if rate is None:
        return f"I don't recognise the currency {target}."

    converted = amount * rate
    return f"{amount:g} {source} is about {converted:,.2f} {target}."