"""Web search for email mentions: Bing and Serper.dev providers."""

from __future__ import annotations

from urllib.parse import quote_plus

import requests


def check_email_bing(email: str, api_key: str, timeout_seconds: float = 3.0) -> tuple[bool, str | None]:
    """
    Search for email in Bing Web Search API v7 (deprecated August 2025).

    Returns:
        (found, error_msg) - found is True if email was found in search results
    """
    try:
        query = quote_plus(f'"{email}"')
        url = f"https://api.bing.microsoft.com/v7.0/search?q={query}&count=1"
        resp = requests.get(
            url,
            headers={"Ocp-Apim-Subscription-Key": api_key.strip()},
            timeout=timeout_seconds,
        )
        resp.raise_for_status()
        data = resp.json()
        web_pages = data.get("webPages") or {}
        total = web_pages.get("totalEstimatedMatches", 0)
        return int(total) > 0, None
    except requests.exceptions.Timeout:
        return False, "Timeout connecting to Bing"
    except requests.exceptions.HTTPError as e:
        return False, f"HTTP error Bing: {e.response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"Request error Bing: {type(e).__name__}"


def check_email_serper(email: str, api_key: str, timeout_seconds: float = 3.0) -> tuple[bool, str | None]:
    """
    Search for email in Serper.dev (Google Search API). 2500 searches/month free.

    Returns:
        (found, error_msg) - found is True if email was found in search results
    """
    try:
        url = "https://google.serper.dev/search"
        resp = requests.post(
            url,
            headers={
                "X-API-KEY": api_key.strip(),
                "Content-Type": "application/json",
            },
            json={"q": f'"{email}"', "num": 1},
            timeout=timeout_seconds,
        )
        resp.raise_for_status()
        data = resp.json()
        # Serper returns "organic" with results; if at least one, email appears on web
        organic = data.get("organic") or []
        return len(organic) > 0, None
    except requests.exceptions.Timeout:
        return False, "Timeout connecting to Serper"
    except requests.exceptions.HTTPError as e:
        return False, f"HTTP error Serper: {e.response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"Request error Serper: {type(e).__name__}"


def check_email_mentioned_on_web(
    email: str,
    provider: str | None = None,
    api_key: str | None = None,
    timeout_seconds: float = 3.0,
) -> tuple[bool, str | None]:
    """
    Search for email (quoted) on the web. Supports 'bing' and 'serper' as providers.

    Args:
        email: The email address to search for
        provider: 'bing' | 'serper' | None (no search)
        api_key: Provider API key
        timeout_seconds: Request timeout

    Returns:
        (found, error_msg)
        - (True, None) = found on the web
        - (False, None) = searched but not found
        - (False, "message") = error during search
    """
    if not api_key or not api_key.strip():
        return False, "API key not configured"
    if not provider or not provider.strip():
        return False, "Provider not configured"

    provider = provider.strip().lower()

    if provider == "bing":
        return check_email_bing(email, api_key, timeout_seconds)
    if provider == "serper":
        return check_email_serper(email, api_key, timeout_seconds)

    return False, f"Provider '{provider}' not supported"
