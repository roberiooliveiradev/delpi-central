"""Unit — payload de shortage_item_notes (sem Postgres)."""

from __future__ import annotations

from datetime import date, datetime, timezone

from app.infrastructure.persistence.plugins.repositories.reports.postgres_reports_repository import (
    PostgresReportsRepository,
)


def test_shortage_item_note_to_payload_formats_fields() -> None:
    payload = PostgresReportsRepository.shortage_item_note_to_payload(
        {
            "id": "11111111-1111-1111-1111-111111111111",
            "definition_id": "22222222-2222-2222-2222-222222222222",
            "branch": "01",
            "product_code": "10020113",
            "note_text": "  Chega na próxima semana  ",
            "expected_receipt_date": date(2026, 8, 5),
            "author_user_id": "user-1",
            "author_display_name": "Maria Silva",
            "created_at": datetime(2026, 7, 31, 12, 0, tzinfo=timezone.utc),
            "updated_at": datetime(2026, 7, 31, 12, 0, tzinfo=timezone.utc),
        }
    )
    assert payload["productCode"] == "10020113"
    assert payload["noteText"] == "Chega na próxima semana"
    assert payload["expectedReceiptDate"] == "2026-08-05"
    assert payload["authorDisplayName"] == "Maria Silva"
    assert payload["branch"] == "01"
    assert payload["definitionId"] == "22222222-2222-2222-2222-222222222222"
