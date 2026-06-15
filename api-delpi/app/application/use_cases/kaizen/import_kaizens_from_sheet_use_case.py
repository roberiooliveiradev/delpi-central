from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from app.domain.entities.kaizen.kaizen import KaizenDetail
from app.domain.services.kaizen.kaizen_sheet_import_mapper import sheet_detail_to_record_fields
from app.infrastructure.persistence.plugins.plugin_base_repository import PluginsRepositoryError


class KaizenSheetImportSourcePort(Protocol):
    def list_active_kaizen_details(self) -> list[KaizenDetail]:
        ...


class KaizenRecordWritePort(Protocol):
    def list_records(
        self,
        *,
        branch_code: str | None = None,
        title: str | None = None,
        page_size: int = 50,
    ) -> dict[str, Any]:
        ...

    def create_record(self, *, fields: dict[str, Any], created_by_user_id: str) -> dict[str, Any]:
        ...


@dataclass(frozen=True)
class ImportKaizensFromSheetResult:
    created: int
    skipped: int
    errors: int
    items: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "created": self.created,
            "skipped": self.skipped,
            "errors": self.errors,
            "items": self.items,
        }


class ImportKaizensFromSheetUseCase:
    def __init__(
        self,
        sheet_source: KaizenSheetImportSourcePort,
        record_repository: KaizenRecordWritePort,
    ):
        self._sheet_source = sheet_source
        self._record_repository = record_repository

    def execute(
        self,
        *,
        created_by_user_id: str,
        dry_run: bool = False,
    ) -> ImportKaizensFromSheetResult:
        created = 0
        skipped = 0
        errors = 0
        items: list[dict[str, Any]] = []

        for detail in self._sheet_source.list_active_kaizen_details():
            fields = sheet_detail_to_record_fields(detail)
            title = fields["title"]
            branch_code = fields["branch_code"]

            if branch_code not in {"01", "02"}:
                skipped += 1
                items.append(
                    {
                        "sheet_id": detail.id,
                        "title": title,
                        "result": "skipped",
                        "reason": "invalid_branch",
                    }
                )
                continue

            if self._record_exists(
                branch_code=branch_code,
                title=title,
                date_implemented=fields.get("date_implemented"),
            ):
                skipped += 1
                items.append(
                    {
                        "sheet_id": detail.id,
                        "title": title,
                        "result": "skipped",
                        "reason": "already_exists",
                    }
                )
                continue

            if dry_run:
                created += 1
                items.append(
                    {
                        "sheet_id": detail.id,
                        "title": title,
                        "result": "would_create",
                        "status": fields.get("status"),
                    }
                )
                continue

            try:
                record = self._record_repository.create_record(
                    fields=fields,
                    created_by_user_id=created_by_user_id,
                )
                created += 1
                items.append(
                    {
                        "sheet_id": detail.id,
                        "title": title,
                        "result": "created",
                        "record_id": record.get("id"),
                        "daily_savings": record.get("daily_savings"),
                    }
                )
            except PluginsRepositoryError as exc:
                errors += 1
                items.append(
                    {
                        "sheet_id": detail.id,
                        "title": title,
                        "result": "error",
                        "reason": str(exc),
                    }
                )

        return ImportKaizensFromSheetResult(
            created=created,
            skipped=skipped,
            errors=errors,
            items=items,
        )

    def _record_exists(
        self,
        *,
        branch_code: str,
        title: str,
        date_implemented: str | None,
    ) -> bool:
        result = self._record_repository.list_records(
            branch_code=branch_code,
            title=title,
            page_size=10,
        )
        for item in result.get("items", []):
            existing_date = item.get("date_implemented")
            if date_implemented is None and existing_date is None:
                return True
            if existing_date and date_implemented and str(existing_date) == date_implemented:
                return True
        return False
