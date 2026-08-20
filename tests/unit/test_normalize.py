import json                                # JSON parsing utility
from pathlib import Path                  # Cross-platform path handling

import pytest                              # Test framework

from ingest.collectors.bmrs.normalize import NormalizationError, normalize_records  # Import normalize module under test

# Resolve fixtures directory path relative to this test file
FIXTURES = Path(__file__).parents[1] / "fixtures"


def _load_fixture(name: str) -> dict:
	# Helper: load JSON fixture file and return as dict
	return json.loads((FIXTURES / name).read_text())


def test_normalize_valid_response_produces_one_record():
	# Test: verify valid BMRS response normalizes to exactly one bronze record with correct field mappings
	records = normalize_records(_load_fixture("bmrs_response_valid.json"))  # Call normalize_records with valid fixture
	assert len(records) == 1  # Verify exactly one record returned
	record = records[0]  # Extract the single normalized record
	assert record["settlement_date"] == "2026-08-10"  # Verify snake_case field mapping from settlementDate
	assert record["settlement_period"] == 1  # Verify settlement_period field present
	assert record["source_dataset"] == "DISEBSP"  # Verify source_dataset extracted from metadata
	assert record["total_system_tagged_adjustment_sell_volume"] is None  # Verify nullable fields preserved
	assert "ingested_at" in record  # Verify ingested_at timestamp field present


def test_normalize_empty_response_produces_no_records():
	# Test: verify empty data array returns empty list (not yet published is valid)
	assert normalize_records(_load_fixture("bmrs_response_empty.json")) == []  # Empty data should return empty list


def test_normalize_malformed_response_raises():
	# Test: verify NormalizationError raised when required field (systemSellPrice) is missing
	with pytest.raises(NormalizationError):  # Expect NormalizationError to be raised
		normalize_records(_load_fixture("bmrs_response_malformed.json"))  # Call with fixture missing systemSellPrice
