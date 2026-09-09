"""Argument provenance + reference clock fixtures."""

from __future__ import annotations

from app.domain.services.chat_argument_provenance_service import (
    ChatArgumentProvenanceService,
)
from app.domain.services.chat_openapi_argument_coercion_service import (
    ChatOpenApiArgumentCoercionService,
)
from app.domain.services.chat_reference_clock import ChatReferenceClock


def test_reference_clock_uses_execution_context_reference_date():
    today = ChatReferenceClock.today({"referenceDate": "2026-08-15"})
    assert str(today) == "2026-08-15"


def test_coerce_dates_with_fixed_reference_date():
    params = ChatOpenApiArgumentCoercionService.coerce_parameters(
        {},
        [
            {"name": "start_date", "schema": {"type": "string", "format": "date"}},
            {"name": "end_date", "schema": {"type": "string", "format": "date"}},
        ],
        message="últimos 30 dias",
        execution_context={"referenceDate": "2026-09-09"},
    )
    assert params.get("start_date")
    assert params.get("end_date")
    assert params["end_date"] == "2026-09-09"


def test_provenance_current_turn_wins_over_active_topic():
    rows = ChatArgumentProvenanceService.annotate(
        {"code": "OLD"},
        source="active_topic",
    )
    rows = ChatArgumentProvenanceService.annotate(
        {"code": "NEW"},
        source="current_turn",
        previous=rows,
    )
    assert len(rows) == 1
    assert rows[0]["value"] == "NEW"
    assert rows[0]["source"] == "current_turn"
