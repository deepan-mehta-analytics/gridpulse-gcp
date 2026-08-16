import json  # Parse JSON schema file into Python dict
from pathlib import Path  # Path manipulation for cross-platform file paths

import fastavro  # Avro schema validation library
import pytest  # Testing framework

SCHEMA_PATH = Path(__file__).parents[2] / "ingest" / "contracts" / "bmrs_bronze_v1.avsc"  # Load Avro schema from file path relative to this test


@pytest.fixture
def schema():  # Pytest fixture that loads and parses the Avro schema once per test
    return json.loads(SCHEMA_PATH.read_text())  # Read and parse schema JSON into dict


def _normalized_valid_record():  # Helper function that returns a sample bronze-layer record for testing
    return {  # Return a complete, valid BMRS settlement system price record matching bmrs_bronze_v1.avsc schema
        "schema_version": 1,  # Schema version marker (currently 1)
        "source_dataset": "DISEBSP",  # Elexon Insights settlement system price dataset name
        "settlement_date": "2026-08-10",  # Date in yyyy-MM-dd format
        "settlement_period": 1,  # Settlement period integer (1-50 per UK market rules)
        "start_time": "2026-08-09T23:00:00Z",  # ISO-8601 UTC event time (Beam's watermark)
        "created_date_time": "2026-08-10T23:44:25Z",  # ISO-8601 UTC Elexon calculation-run timestamp
        "system_sell_price": 97.71117120592626,  # System sell price in GBP/MWh
        "system_buy_price": 97.71117120592626,  # System buy price in GBP/MWh
        "bsad_defaulted": False,  # Boolean: whether BSAD was defaulted
        "price_derivation_code": "N",  # Single-char code describing how price was derived
        "reserve_scarcity_price": 0.0,  # Reserve scarcity price component
        "net_imbalance_volume": -99.15314569444445,  # Net volume of imbalance in MWh
        "sell_price_adjustment": 0.0,  # Adjustment applied to sell price
        "buy_price_adjustment": 0.0,  # Adjustment applied to buy price
        "replacement_price": 97.7595,  # Replacement reference price for calculating adjustments
        "replacement_price_reference_volume": 1.0,  # Volume associated with replacement price reference
        "total_accepted_offer_volume": 593.2635209722222,  # Total accepted generator offers
        "total_accepted_bid_volume": -809.8051783333333,  # Total accepted demand bids (negative)
        "total_adjustment_sell_volume": 0.0,  # Adjustment volume sell side
        "total_adjustment_buy_volume": 117.5,  # Adjustment volume buy side
        "total_system_tagged_accepted_offer_volume": 593.2635209722222,  # System-tagged accepted offers
        "total_system_tagged_accepted_bid_volume": -808.8051783333333,  # System-tagged accepted bids
        "total_system_tagged_adjustment_sell_volume": None,  # System-tagged adjustment (nullable)
        "total_system_tagged_adjustment_buy_volume": 117.5,  # System-tagged adjustment buy volume
        "ingested_at": "2026-08-16T12:00:00Z",  # ISO-8601 UTC timestamp when collector fetched this record
    }


def test_valid_record_matches_schema(schema):  # Test that a well-formed record passes Avro schema validation
    record = _normalized_valid_record()  # Create a complete, valid sample record
    assert fastavro.validation.validate(record, schema, raise_errors=True)  # Assert record passes schema validation, raising exception on failure


def test_record_missing_required_field_fails_schema(schema):  # Test that removing a required field causes schema validation to fail
    record = _normalized_valid_record()  # Start with a valid record
    del record["system_sell_price"]  # Delete a required field (system_sell_price has no default)
    assert not fastavro.validation.validate(record, schema, raise_errors=False)  # Assert validation fails without raising exception


def test_record_with_wrong_type_fails_schema(schema):  # Test that assigning wrong type to a field causes schema validation to fail
    record = _normalized_valid_record()  # Start with a valid record
    record["settlement_period"] = "not-an-int"  # Assign string to field that expects int type
    assert not fastavro.validation.validate(record, schema, raise_errors=False)  # Assert validation fails for type mismatch
