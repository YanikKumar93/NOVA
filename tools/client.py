"""Shared HTTP helper for all NOVA API tools."""
import requests

TIMEOUT = 10

def get_json(url, params=None):
    """
    Make a GET request and return parsed JSON.
    Returns (data, None) on success, (None, error_message) on failure.
    Never raises.
    """
    try:
        response = requests.get(url, params=params, timeout=TIMEOUT)
    except requests.exceptions.Timeout:
        return None, "the service took too long to respond"
    except requests.exceptions.ConnectionError:
        return None, "I couldn't reach the internet"
    except requests.exceptions.RequestException:
        return None, "the request failed"

    if response.status_code == 401:
        return None, "the API key is missing or invalid"
    if response.status_code == 404:
        return None, "that wasn't found"
    if response.status_code == 429:
        return None, "too many requests, try again in a minute"
    if response.status_code >= 400:
        return None, f"the service returned an error ({response.status_code})"

    try:
        return response.json(), None
    except ValueError:
        return None, "the service sent back something I couldn't read"