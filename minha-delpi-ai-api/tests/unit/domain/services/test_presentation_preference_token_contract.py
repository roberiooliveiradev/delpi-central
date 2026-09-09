"""Contract test — requestedPresentation enum drift planner JSON ↔ Python."""

from __future__ import annotations

import json
from pathlib import Path

from app.domain.services.chat_presentation_preference_contract_service import (
    REQUESTED_PRESENTATION_TOKENS,
)


def test_requested_presentation_tokens_match_openapi_tool_routing_schema():
    root = Path(__file__).resolve().parents[4]
    path = root / "app" / "content" / "pt-BR" / "assistant" / "openapi_tool_routing.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    enum_values = (
        payload.get("planner", {})
        .get("schema", {})
        .get("properties", {})
        .get("requestedPresentation", {})
        .get("enum")
        or []
    )
    json_tokens = {value for value in enum_values if value not in (None,)}
    python_tokens = set(REQUESTED_PRESENTATION_TOKENS)
    assert json_tokens == python_tokens, {
        "only_in_json": sorted(json_tokens - python_tokens),
        "only_in_python": sorted(python_tokens - json_tokens),
    }
