import json
from pathlib import Path

import fastavro
import pytest

SCHEMA_PATH = Path(__file__).parents[2] / "ingest" / "contracts" / "bmrs_bronze_v1.avsc"


@pytest.fixture
def schema():
    return json.loads(SCHEMA_PATH.read_text())


def _normalized_valid_record():
    return {
        "schema_version": 1,
        "source_dataset": "DISEBSP",
        "settlement_date": "2026-08-10",
        "settlement_period": 1,
        "start_time": "2026-08-09T23:00:00Z",
        "created_date_time": "2026-08-10T23:44:25Z",
        "system_sell_price": 97.71117120592626,
        "system_buy_price": 97.71117120592626,
        "bsad_defaulted": False,
        "price_derivation_code": "N",
        "reserve_scarcity_price": 0.0,
        "net_imbalance_volume": -99.15314569444445,
        "sell_price_adjustment": 0.0,
        "buy_price_adjustment": 0.0,
        "replacement_price": 97.7595,
        "replacement_price_reference_volume": 1.0,
        "total_accepted_offer_volume": 593.2635209722222,
        "total_accepted_bid_volume": -809.8051783333333,
        "total_adjustment_sell_volume": 0.0,
        "total_adjustment_buy_volume": 117.5,
        "total_system_tagged_accepted_offer_volume": 593.2635209722222,
        "total_system_tagged_accepted_bid_volume": -808.8051783333333,
        "total_system_tagged_adjustment_sell_volume": None,
        "total_system_tagged_adjustment_buy_volume": 117.5,
        "ingested_at": "2026-08-16T12:00:00Z",
    }


def test_valid_record_matches_schema(schema):
    record = _normalized_valid_record()
    assert fastavro.validation.validate(record, schema, raise_errors=True)


def test_record_missing_required_field_fails_schema(schema):
    record = _normalized_valid_record()
    del record["system_sell_price"]
    assert not fastavro.validation.validate(record, schema, raise_errors=False)


def test_record_with_wrong_type_fails_schema(schema):
    record = _normalized_valid_record()
    record["settlement_period"] = "not-an-int"
    assert not fastavro.validation.validate(record, schema, raise_errors=False)
