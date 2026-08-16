"""Thin client for the Elexon Insights BMRS settlement system-prices
endpoint. No API key required. Confirmed live 2026-08-16:
GET https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/system-prices/{settlementDate}/{settlementPeriod}
"""
from __future__ import annotations  # Enable postponed evaluation of type hints (Python 3.10+)

import time                         # Provides time.sleep() for backoff delays

import requests                     # HTTP library for making requests

# Base URL for Elexon Insights BMRS API
BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"
# URL path template with settlement date/period placeholders
SYSTEM_PRICES_PATH = "/balancing/settlement/system-prices/{settlement_date}/{settlement_period}"


class BmrsApiError(Exception):
    # Custom exception raised on BMRS API errors; stores status_code and message attributes
    def __init__(self, status_code: int | None, message: str):
        # Store status_code (may be None if connection failed before response)
        self.status_code = status_code
        # Store error message text from response body or generic error
        self.message = message
        # Call parent Exception.__init__ with formatted error message
        super().__init__(f"BMRS API error ({status_code}): {message}")


def fetch_system_prices(
    settlement_date: str,
    settlement_period: int,
    *,
    session: requests.Session | None = None,
    max_retries: int = 3,
    backoff_seconds: float = 1.0,
) -> dict:
    """Fetch one settlement period's system-price data. May return an
    empty data list if the period hasn't been published yet — that's a
    valid, non-error state, not raised as BmrsApiError. Retries transient
    failures (5xx, connection errors) with linear backoff; raises
    BmrsApiError immediately on a 4xx, or after exhausting retries."""
    # Use provided session or create a new one for this request
    session = session or requests.Session()
    # Build full URL by combining base URL and formatted path
    url = BASE_URL + SYSTEM_PRICES_PATH.format(
        settlement_date=settlement_date, settlement_period=settlement_period
    )

    # Track the most recent exception encountered during retries
    last_error: Exception | None = None
    # Loop from 1 to max_retries (inclusive) to allow initial attempt + retries
    for attempt in range(1, max_retries + 1):
        try:
            # Attempt HTTP GET with 10-second timeout
            response = session.get(url, timeout=10)
        except requests.RequestException as exc:
            # Catch transient connection errors (timeout, connection refused, etc.)
            last_error = exc
            # Wait before retrying; backoff = base * attempt (1s, 2s, 3s for 1.0 base)
            time.sleep(backoff_seconds * attempt)
            # Continue to next retry iteration
            continue

        # Check for HTTP 200 OK response
        if response.status_code == 200:
            # Parse and return JSON response body as dict
            return response.json()
        # Check for client error (4xx); these are not retryable
        if 400 <= response.status_code < 500:
            # Raise immediately; do not retry on client error
            raise BmrsApiError(response.status_code, response.text)
        # For 5xx server errors, store as last_error and retry after backoff
        last_error = BmrsApiError(response.status_code, response.text)
        # Wait before next retry attempt; backoff = base * attempt
        time.sleep(backoff_seconds * attempt)

    # All retries exhausted; raise the last error (5xx or connection failure)
    raise last_error or BmrsApiError(None, "exhausted retries with no response")
