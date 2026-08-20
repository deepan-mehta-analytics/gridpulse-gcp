"""Normalizes raw Elexon Insights BMRS API responses into the versioned
bronze contract (ingest/contracts/bmrs_bronze_v1.avsc)."""
from __future__ import annotations  # Enable postponed evaluation of type hints (Python 3.10+)

from datetime import datetime, timezone  # For generating ingested_at timestamp in UTC


class NormalizationError(Exception):
    # Custom exception raised when a raw API response can't be mapped onto the bronze contract
    """Raised when a raw API response can't be mapped onto the bronze contract."""


# Tuple of required field names that must be present in each API response record
REQUIRED_FIELDS = (
    "settlementDate", "settlementPeriod", "startTime", "createdDateTime",
    "systemSellPrice", "systemBuyPrice", "bsadDefaulted", "priceDerivationCode",
    "reserveScarcityPrice", "netImbalanceVolume", "sellPriceAdjustment",
    "buyPriceAdjustment", "replacementPrice", "replacementPriceReferenceVolume",
    "totalAcceptedOfferVolume", "totalAcceptedBidVolume", "totalAdjustmentBuyVolume",
    "totalSystemTaggedAcceptedOfferVolume", "totalSystemTaggedAcceptedBidVolume",
    "totalSystemTaggedAdjustmentBuyVolume",
)


def normalize_records(raw_response: dict) -> list[dict]:
    """Convert one raw API response into zero or more bronze records. Zero
    is valid (period not yet published). Raises NormalizationError if a
    returned record is missing a required field."""
    # Extract source dataset name from metadata (e.g., "DISEBSP"); default to empty list if metadata missing
    source_dataset = raw_response.get("metadata", {}).get("datasets", [None])[0]
    # Raise error if datasets[0] is missing or None; source_dataset is required for all records
    if not source_dataset:
        raise NormalizationError("response metadata missing datasets[0]")

    # Initialize empty list to accumulate normalized records
    records = []
    # Iterate over each entry in the data array (may be zero entries if period not yet published)
    for entry in raw_response.get("data", []):
        # Build list of required fields that are missing from this entry
        missing = [f for f in REQUIRED_FIELDS if f not in entry]
        # Raise error if any required field is absent; all fields must be present
        if missing:
            raise NormalizationError(f"record missing required fields: {missing}")

        # Append normalized record dict to list; transform camelCase API fields to snake_case bronze fields
        records.append({
            "schema_version": 1,  # Bronze contract version; required by Avro schema
            "source_dataset": source_dataset,  # Dataset identifier extracted from response metadata
            "settlement_date": entry["settlementDate"],  # Transform camelCase to snake_case
            "settlement_period": entry["settlementPeriod"],  # Settlement period number (1-48)
            "start_time": entry["startTime"],  # ISO 8601 start time of settlement period
            "created_date_time": entry["createdDateTime"],  # ISO 8601 timestamp when record was created
            "system_sell_price": entry["systemSellPrice"],  # System-wide sell price in GBP/MWh
            "system_buy_price": entry["systemBuyPrice"],  # System-wide buy price in GBP/MWh
            "bsad_defaulted": entry["bsadDefaulted"],  # Boolean: whether BSAD defaulted for this period
            "price_derivation_code": entry["priceDerivationCode"],  # Single character code indicating derivation method
            "reserve_scarcity_price": entry["reserveScarcityPrice"],  # Reserve scarcity price in GBP/MWh
            "net_imbalance_volume": entry["netImbalanceVolume"],  # Net system imbalance volume in MW
            "sell_price_adjustment": entry["sellPriceAdjustment"],  # Adjustment to sell price in GBP/MWh
            "buy_price_adjustment": entry["buyPriceAdjustment"],  # Adjustment to buy price in GBP/MWh
            "replacement_price": entry.get("replacementPrice"),  # Replacement price for imbalance in GBP/MWh (nullable field)
            "replacement_price_reference_volume": entry.get("replacementPriceReferenceVolume"),  # Reference volume for replacement price (nullable field)
            "total_accepted_offer_volume": entry["totalAcceptedOfferVolume"],  # Total volume of accepted offers in MW
            "total_accepted_bid_volume": entry["totalAcceptedBidVolume"],  # Total volume of accepted bids in MW
            "total_adjustment_sell_volume": entry.get("totalAdjustmentSellVolume"),  # Total adjustment sell volume (nullable field)
            "total_adjustment_buy_volume": entry.get("totalAdjustmentBuyVolume"),  # Total adjustment buy volume in MW (nullable field)
            "total_system_tagged_accepted_offer_volume": entry["totalSystemTaggedAcceptedOfferVolume"],  # System-tagged accepted offers
            "total_system_tagged_accepted_bid_volume": entry["totalSystemTaggedAcceptedBidVolume"],  # System-tagged accepted bids
            "total_system_tagged_adjustment_sell_volume": entry.get("totalSystemTaggedAdjustmentSellVolume"),  # System-tagged adjust sell (nullable)
            "total_system_tagged_adjustment_buy_volume": entry.get("totalSystemTaggedAdjustmentBuyVolume"),  # System-tagged adjustment buy (nullable field)
            "ingested_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),  # Current UTC timestamp when record was ingested
        })
    # Return list of normalized records; may be empty if data array was empty
    return records
