import json          # JSON parsing utility
from pathlib import Path  # Cross-platform path handling

import pytest        # Test framework

from ingest.collectors.bmrs.client import BASE_URL, BmrsApiError, fetch_system_prices  # Import client module under test

# Resolve fixtures directory path relative to this test file
FIXTURES = Path(__file__).parents[1] / "fixtures"


def _load_fixture(name: str) -> dict:
    # Helper: load JSON fixture file and return as dict
    return json.loads((FIXTURES / name).read_text())


def test_fetch_system_prices_returns_parsed_json(requests_mock):
    # Test: verify fetch_system_prices returns parsed JSON dict matching fixture response
    fixture = _load_fixture("bmrs_response_valid.json")
    # Mock the HTTP GET to return valid fixture
    requests_mock.get(
        f"{BASE_URL}/balancing/settlement/system-prices/2026-08-10/1", json=fixture
    )
    # Assert returned dict equals fixture
    assert fetch_system_prices("2026-08-10", 1) == fixture


def test_fetch_system_prices_handles_not_yet_published(requests_mock):
    # Test: verify function handles empty data list (not-yet-published period) as valid response
    fixture = _load_fixture("bmrs_response_empty.json")
    # Mock the HTTP GET with empty response
    requests_mock.get(
        f"{BASE_URL}/balancing/settlement/system-prices/2026-08-10/48", json=fixture
    )
    # Assert empty data list is returned without raising
    assert fetch_system_prices("2026-08-10", 48)["data"] == []


def test_fetch_system_prices_raises_on_4xx_without_retry(requests_mock):
    # Test: verify 4xx errors raise immediately without retrying
    mocked = requests_mock.get(
        f"{BASE_URL}/balancing/settlement/system-prices/2026-08-10/99",
        status_code=400,
        text="invalid settlement period",
    )
    # Assert BmrsApiError is raised
    with pytest.raises(BmrsApiError):
        fetch_system_prices("2026-08-10", 99, max_retries=3, backoff_seconds=0)
    # Verify request was made exactly once (no retries)
    assert mocked.call_count == 1


def test_fetch_system_prices_retries_then_raises_on_persistent_5xx(requests_mock):
    # Test: verify 5xx errors trigger retries, then raise after exhausting max_retries
    mocked = requests_mock.get(
        f"{BASE_URL}/balancing/settlement/system-prices/2026-08-10/1",
        status_code=503,
        text="service unavailable",
    )
    # Assert BmrsApiError is raised after retries exhausted
    with pytest.raises(BmrsApiError):
        fetch_system_prices("2026-08-10", 1, max_retries=3, backoff_seconds=0)
    # Verify request was attempted 3 times (initial + 2 retries)
    assert mocked.call_count == 3
