"""CRUD — notas de acompanhamento por item (Delpi Reports Fase 6.2)."""

from __future__ import annotations

from typing import Any, Protocol


class _ReportsRepo(Protocol):
    def get_definition(self, definition_id: str) -> dict[str, Any] | None: ...

    def list_shortage_item_notes(
        self,
        *,
        definition_id: str,
        branch: str | None = None,
    ) -> list[dict[str, Any]]: ...

    def upsert_shortage_item_note(
        self,
        *,
        definition_id: str,
        branch: str,
        product_code: str,
        note_text: str,
        author_user_id: str,
        author_display_name: str,
        expected_receipt_date: str | None = None,
    ) -> dict[str, Any]: ...

    def delete_shortage_item_note(
        self,
        *,
        definition_id: str,
        branch: str,
        product_code: str,
    ) -> bool: ...


def _definition_branch(definition: dict[str, Any]) -> str:
    params = definition.get("params") or {}
    if not isinstance(params, dict):
        params = {}
    return str(params.get("branch") or "").strip()


class ListShortageItemNotesUseCase:
    def __init__(self, repository: _ReportsRepo) -> None:
        self._repository = repository

    def execute(self, definition_id: str) -> dict[str, Any]:
        definition = self._repository.get_definition(definition_id)
        if definition is None:
            raise LookupError("Definição de relatório não encontrada.")
        branch = _definition_branch(definition)
        items = self._repository.list_shortage_item_notes(
            definition_id=definition_id,
            branch=branch or None,
        )
        return {
            "items": items,
            "total": len(items),
            "definitionId": definition_id,
            "branch": branch or None,
        }


class UpsertShortageItemNoteUseCase:
    def __init__(self, repository: _ReportsRepo) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        definition_id: str,
        product_code: str,
        note_text: str,
        author_user_id: str,
        author_display_name: str,
        expected_receipt_date: str | None = None,
        branch: str | None = None,
    ) -> dict[str, Any]:
        definition = self._repository.get_definition(definition_id)
        if definition is None:
            raise LookupError("Definição de relatório não encontrada.")
        resolved_branch = str(branch or _definition_branch(definition) or "").strip()
        if resolved_branch not in {"01", "02"}:
            raise ValueError("Filial da definição inválida para acompanhamento.")
        return self._repository.upsert_shortage_item_note(
            definition_id=definition_id,
            branch=resolved_branch,
            product_code=product_code,
            note_text=note_text,
            author_user_id=author_user_id,
            author_display_name=author_display_name,
            expected_receipt_date=expected_receipt_date,
        )


class DeleteShortageItemNoteUseCase:
    def __init__(self, repository: _ReportsRepo) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        definition_id: str,
        product_code: str,
        branch: str | None = None,
    ) -> bool:
        definition = self._repository.get_definition(definition_id)
        if definition is None:
            raise LookupError("Definição de relatório não encontrada.")
        resolved_branch = str(branch or _definition_branch(definition) or "").strip()
        if resolved_branch not in {"01", "02"}:
            raise ValueError("Filial da definição inválida para acompanhamento.")
        return self._repository.delete_shortage_item_note(
            definition_id=definition_id,
            branch=resolved_branch,
            product_code=product_code,
        )
