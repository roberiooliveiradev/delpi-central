"""Serialização JSONB do histórico LNF."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

from app.domain.services.lancamento_notas_fiscais.history_serialization import (
    history_changes_json_safe,
)


def test_history_changes_json_safe_serializes_temporal_and_decimal() -> None:
    raw = {
        "issue_date": {"from": "2026-07-22", "to": date(2026, 7, 23)},
        "amount": {"from": 10.5, "to": Decimal("20.00")},
        "received_at": {
            "from": "2026-07-22T10:00:00+00:00",
            "to": datetime(2026, 7, 22, 11, 0, tzinfo=timezone.utc),
        },
        "id": uuid4(),
    }
    safe = history_changes_json_safe(raw)
    encoded = json.dumps(safe)
    assert "2026-07-23" in encoded
    assert "20.0" in encoded
    assert "2026-07-22T11:00:00" in encoded
