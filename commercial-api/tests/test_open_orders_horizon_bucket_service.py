from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from commercial_app.domain.services.open_orders_horizon_bucket_service import (
    BUCKET_CURRENT_MONTH,
    BUCKET_LATER,
    BUCKET_NEXT_1_3_MONTHS,
    BUCKET_OVERDUE,
    BUCKET_UNDATED,
    HORIZON_TIMEZONE,
    OpenOrdersHorizonBucketService,
)


_AS_OF = datetime(2026, 8, 13, 12, 0, 0, tzinfo=ZoneInfo(HORIZON_TIMEZONE))


def test_bucketize_empty_items() -> None:
    result = OpenOrdersHorizonBucketService().bucketize([], as_of=_AS_OF)
    assert result["timezone"] == HORIZON_TIMEZONE
    assert result["totals"] == {"openValue": 0.0, "openLineCount": 0}
    assert [b["id"] for b in result["buckets"]] == [
        BUCKET_OVERDUE,
        BUCKET_CURRENT_MONTH,
        BUCKET_NEXT_1_3_MONTHS,
        BUCKET_LATER,
        BUCKET_UNDATED,
    ]


def test_bucketize_classifies_delivery_dates() -> None:
    items = [
        {"data_entrega": "2026-08-01", "valor_aberto": 10},  # overdue (before 13)
        {"data_entrega": "2026-08-20", "valor_aberto": 20},  # current month
        {"data_entrega": "2026-09-15", "valor_aberto": 30},  # next 1-3
        {"data_entrega": "2026-11-30", "valor_aberto": 40},  # next 1-3 (month+3)
        {"data_entrega": "2026-12-01", "valor_aberto": 50},  # later
        {"data_entrega": None, "valor_aberto": 5},  # undated
        {"data_entrega": "invalid", "valor_aberto": 7},  # undated
    ]
    result = OpenOrdersHorizonBucketService().bucketize(items, as_of=_AS_OF)
    by_id = {b["id"]: b for b in result["buckets"]}
    assert by_id[BUCKET_OVERDUE] == {
        "id": BUCKET_OVERDUE,
        "openValue": 10.0,
        "openLineCount": 1,
    }
    assert by_id[BUCKET_CURRENT_MONTH]["openValue"] == 20.0
    assert by_id[BUCKET_NEXT_1_3_MONTHS]["openValue"] == 70.0
    assert by_id[BUCKET_NEXT_1_3_MONTHS]["openLineCount"] == 2
    assert by_id[BUCKET_LATER]["openValue"] == 50.0
    assert by_id[BUCKET_UNDATED]["openValue"] == 12.0
    assert by_id[BUCKET_UNDATED]["openLineCount"] == 2
    assert result["totals"]["openLineCount"] == 7
    assert result["totals"]["openValue"] == 162.0
