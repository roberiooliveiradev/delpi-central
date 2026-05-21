from __future__ import annotations

import json
from uuid import UUID

from si_app.shared.json_encoding import to_json_safe


def test_to_json_safe_serializes_uuid() -> None:
    value = to_json_safe({"id": UUID("550e8400-e29b-41d4-a716-446655440000")})

    json.dumps(value)
    assert value["id"] == "550e8400-e29b-41d4-a716-446655440000"
