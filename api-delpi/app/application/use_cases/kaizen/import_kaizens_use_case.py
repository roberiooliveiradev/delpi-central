from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class KaizenRecordWritePort(Protocol):
    def list_records(
        self,
        *,
        branch_code: str | None = None,
        title: str | None = None,
        page_size: int = 50,
    ) -> dict[str, Any]:
        ...

    def create_record(
        self,
        *,
        fields: dict[str, Any],
        created_by_user_id: str,
        actor_name: str | None = None,
    ) -> dict[str, Any]:
        ...


@dataclass(frozen=True)
class ImportKaizensResult:
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


class ImportKaizensUseCase:
    """Importa kaizens a partir de itens já mapeados (agnóstico de fonte: JSON, planilha…).

    Cada item é um dicionário no formato aceito por ``create_record`` (branch_code,
    title, status, economia, datas etc.). A deduplicação usa filial + título + data
    de implantação para evitar duplicar registros já persistidos.
    """

    _VALID_BRANCHES = {"01", "02"}

    def __init__(self, record_repository: KaizenRecordWritePort):
        self._record_repository = record_repository

    def execute(
        self,
        items: list[dict[str, Any]],
        *,
        created_by_user_id: str,
        actor_name: str | None = None,
        dry_run: bool = False,
        skip_existing: bool = True,
    ) -> ImportKaizensResult:
        created = 0
        skipped = 0
        errors = 0
        report: list[dict[str, Any]] = []

        for index, raw in enumerate(items):
            fields = dict(raw or {})
            title = str(fields.get("title") or "").strip()
            branch_code = str(fields.get("branch_code") or "").strip()

            if not title:
                skipped += 1
                report.append({"index": index, "result": "skipped", "reason": "missing_title"})
                continue

            if branch_code not in self._VALID_BRANCHES:
                skipped += 1
                report.append(
                    {"index": index, "title": title, "result": "skipped", "reason": "invalid_branch"}
                )
                continue

            if skip_existing and self._record_exists(
                branch_code=branch_code,
                title=title,
                date_implemented=fields.get("date_implemented"),
            ):
                skipped += 1
                report.append(
                    {"index": index, "title": title, "result": "skipped", "reason": "already_exists"}
                )
                continue

            if dry_run:
                created += 1
                report.append(
                    {
                        "index": index,
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
                    actor_name=actor_name,
                )
                created += 1
                report.append(
                    {
                        "index": index,
                        "title": title,
                        "result": "created",
                        "record_id": record.get("id"),
                        "daily_savings": record.get("daily_savings"),
                    }
                )
            except Exception as exc:  # noqa: BLE001 — reporta por item, não aborta o lote
                errors += 1
                report.append(
                    {"index": index, "title": title, "result": "error", "reason": str(exc)}
                )

        return ImportKaizensResult(created=created, skipped=skipped, errors=errors, items=report)

    def _record_exists(
        self,
        *,
        branch_code: str,
        title: str,
        date_implemented: Any,
    ) -> bool:
        result = self._record_repository.list_records(
            branch_code=branch_code,
            title=title,
            page_size=10,
        )
        target = str(date_implemented) if date_implemented else None
        for item in result.get("items", []):
            existing_date = item.get("date_implemented")
            if target is None and existing_date is None:
                return True
            if existing_date and target and str(existing_date) == target:
                return True
        return False
