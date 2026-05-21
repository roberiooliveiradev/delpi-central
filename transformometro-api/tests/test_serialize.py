import json
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from tm_app.core.serialize import json_safe, row_to_json


def test_json_safe_nested_date():
    payload = {
        "items": [
            {
                "data_inicio_vigencia": date(2025, 3, 1),
                "totais": {"economia_bruta": Decimal("10.5")},
            }
        ],
        "processo_id": UUID("00000000-0000-0000-0000-000000000099"),
        "calculated_at": datetime(2025, 3, 15, 12, 0, 0),
    }
    safe = json_safe(payload)
    json.dumps(safe)
    assert safe["items"][0]["data_inicio_vigencia"] == "2025-03-01"
    assert safe["items"][0]["totais"]["economia_bruta"] == 10.5
    assert safe["processo_id"] == "00000000-0000-0000-0000-000000000099"


def test_row_to_json_flat_row():
    row = row_to_json(
        {
            "nome": "Teste",
            "data_fim_vigencia": date(2026, 1, 31),
            "created_at": datetime(2026, 1, 1, 8, 30),
        }
    )
    assert row["data_fim_vigencia"] == "2026-01-31"
    assert row["created_at"].startswith("2026-01-01")
