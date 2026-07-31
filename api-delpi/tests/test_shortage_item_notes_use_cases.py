"""Unit — use cases de shortage item notes."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.application.use_cases.reports.shortage_item_notes_use_cases import (
    DeleteShortageItemNoteUseCase,
    ListShortageItemNotesUseCase,
    UpsertShortageItemNoteUseCase,
)

_DEF = {
    "id": "def-1",
    "params": {"branch": "01"},
}


def test_list_notes_requires_definition() -> None:
    repo = MagicMock()
    repo.get_definition.return_value = None
    with pytest.raises(LookupError):
        ListShortageItemNotesUseCase(repo).execute("missing")


def test_upsert_uses_definition_branch() -> None:
    repo = MagicMock()
    repo.get_definition.return_value = _DEF
    repo.upsert_shortage_item_note.return_value = {"productCode": "P1"}
    result = UpsertShortageItemNoteUseCase(repo).execute(
        definition_id="def-1",
        product_code="P1",
        note_text="ok",
        author_user_id="u1",
        author_display_name="Ana",
        expected_receipt_date="2026-08-01",
    )
    assert result["productCode"] == "P1"
    repo.upsert_shortage_item_note.assert_called_once()
    kwargs = repo.upsert_shortage_item_note.call_args.kwargs
    assert kwargs["branch"] == "01"
    assert kwargs["author_display_name"] == "Ana"


def test_delete_returns_false_when_missing() -> None:
    repo = MagicMock()
    repo.get_definition.return_value = _DEF
    repo.delete_shortage_item_note.return_value = False
    assert (
        DeleteShortageItemNoteUseCase(repo).execute(
            definition_id="def-1",
            product_code="P1",
        )
        is False
    )
