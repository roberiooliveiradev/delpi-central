"""Importação em lote de NCs LMP a partir de JSON (substituição total)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

_VALID_STATUS = frozenset({"open", "in_progress", "done"})
_STRIP_KEYS = frozenset(
    {
        "id",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "product_codes",
    }
)
_REGISTERED_AT_TZ_SUFFIX = "T00:00:00-03:00"


class LmpNonconformityImportRepository(Protocol):
    def delete_all_records(self) -> int: ...

    def create_record(
        self,
        *,
        status: str = "open",
        sale_number: str | None = None,
        lmp_number: str | None = None,
        customer_name: str | None = None,
        occurrence_date: str | None = None,
        launch_date: str | None = None,
        last_revision_date: str | None = None,
        executed_by: str | None = None,
        released_by: str | None = None,
        defect_description: str | None = None,
        corrective_actions: str | None = None,
        technical_opinion: str | None = None,
        products: list[dict[str, Any]] | None = None,
        problem_tags: list[str] | None = None,
        created_by: str | None = None,
        registered_at: str | None = None,
        actor_user_id: str | None = None,
        actor_email: str | None = None,
        actor_name: str | None = None,
    ) -> dict[str, Any]: ...


@dataclass(frozen=True)
class ImportLmpNonconformitiesResult:
    deleted: int
    created: int
    skipped: int
    errors: int
    items: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "deleted": self.deleted,
            "created": self.created,
            "skipped": self.skipped,
            "errors": self.errors,
            "items": self.items,
        }


def _blank(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalize_products(raw: Any, product_codes: Any = None) -> list[dict[str, str]]:
    if isinstance(raw, list) and raw:
        out: list[dict[str, str]] = []
        seen: set[str] = set()
        for item in raw:
            if not isinstance(item, dict):
                continue
            code = str(item.get("product_code") or item.get("code") or "").strip().upper()
            if not code or code in seen:
                continue
            seen.add(code)
            description = str(
                item.get("product_description") or item.get("description") or ""
            ).strip()
            out.append(
                {
                    "product_code": code,
                    "product_description": description[:255] if description else "",
                }
            )
        return out
    if isinstance(product_codes, list):
        out = []
        seen = set()
        for code_raw in product_codes:
            code = str(code_raw or "").strip().upper()
            if not code or code in seen:
                continue
            seen.add(code)
            out.append({"product_code": code, "product_description": ""})
        return out
    return []


def _normalize_tags(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for item in raw:
        label = str(item or "").strip()
        if not label:
            continue
        key = label.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(label[:80])
    return out


def _normalize_occurrence_date(value: Any, registered_at: Any = None) -> str | None:
    """YYYY-MM-DD; se ausente, deriva da data de registered_at."""
    text = _blank(value)
    if text:
        return text[:10]
    registered = _blank(registered_at)
    if registered:
        return registered[:10]
    return None


def _normalize_registered_at(
    value: Any,
    *,
    occurrence_date: str | None = None,
) -> str | None:
    """
    Data/hora de registro alinhada à ocorrência.

    Se há ``occurrence_date``, ``registered_at`` fica no mesmo dia
    (mantém horário do JSON se já for do mesmo dia; senão 00:00 -03).
    """
    occ = _blank(occurrence_date)
    if occ:
        occ_day = occ[:10]
        text = _blank(value)
        if text and text[:10] == occ_day:
            return text
        return f"{occ_day}{_REGISTERED_AT_TZ_SUFFIX}"
    return _blank(value)


def normalize_import_item(raw: dict[str, Any] | None) -> dict[str, Any]:
    """Extrai campos aceitos por ``create_record`` a partir de um item exportado."""
    source = dict(raw or {})
    for key in _STRIP_KEYS:
        source.pop(key, None)

    status = str(source.get("status") or "open").strip().lower() or "open"
    products = _normalize_products(source.get("products"), raw.get("product_codes") if raw else None)
    tags = _normalize_tags(source.get("problem_tags"))
    occurrence_date = _normalize_occurrence_date(
        source.get("occurrence_date"),
        source.get("registered_at"),
    )

    return {
        "status": status,
        "sale_number": _blank(source.get("sale_number")),
        "lmp_number": _blank(source.get("lmp_number")),
        "customer_name": _blank(source.get("customer_name")),
        "occurrence_date": occurrence_date,
        "launch_date": _blank(source.get("launch_date")),
        "last_revision_date": _blank(source.get("last_revision_date")),
        "executed_by": _blank(source.get("executed_by")),
        "released_by": _blank(source.get("released_by")),
        "defect_description": _blank(source.get("defect_description")),
        "corrective_actions": _blank(source.get("corrective_actions")),
        "technical_opinion": _blank(source.get("technical_opinion")),
        "products": products,
        "problem_tags": tags,
        "registered_at": _normalize_registered_at(
            source.get("registered_at"),
            occurrence_date=occurrence_date,
        ),
    }


class ImportLmpNonconformitiesUseCase:
    """Importa NCs LMP substituindo todo o acervo existente (sem merge)."""

    def __init__(self, repository: LmpNonconformityImportRepository) -> None:
        self._repository = repository

    def execute(
        self,
        items: list[dict[str, Any]],
        *,
        created_by: str | None = None,
        actor_user_id: str | None = None,
        actor_email: str | None = None,
        actor_name: str | None = None,
        dry_run: bool = False,
        skip_existing: bool = False,  # legado; ignorado — importação é replace-all
    ) -> ImportLmpNonconformitiesResult:
        del skip_existing  # API antiga ainda pode enviar; comportamento é sempre replace.

        created = 0
        skipped = 0
        errors = 0
        report: list[dict[str, Any]] = []
        deleted = 0

        if dry_run:
            deleted = 0
            report.append(
                {
                    "index": -1,
                    "result": "would_replace_all",
                    "reason": "dry_run",
                }
            )
        else:
            deleted = self._repository.delete_all_records()
            report.append(
                {
                    "index": -1,
                    "result": "deleted_all",
                    "deleted": deleted,
                }
            )

        for index, raw in enumerate(items):
            if not isinstance(raw, dict):
                skipped += 1
                report.append(
                    {
                        "index": index,
                        "result": "skipped",
                        "reason": "invalid_item",
                    }
                )
                continue

            fields = normalize_import_item(raw)
            status = fields["status"]
            if status not in _VALID_STATUS:
                skipped += 1
                report.append(
                    {
                        "index": index,
                        "result": "skipped",
                        "reason": "invalid_status",
                        "status": status,
                        "sale_number": fields["sale_number"],
                    }
                )
                continue

            if dry_run:
                created += 1
                report.append(
                    {
                        "index": index,
                        "result": "would_create",
                        "sale_number": fields["sale_number"],
                        "occurrence_date": fields["occurrence_date"],
                        "status": status,
                    }
                )
                continue

            try:
                record = self._repository.create_record(
                    status=status,
                    sale_number=fields["sale_number"],
                    lmp_number=fields["lmp_number"],
                    customer_name=fields["customer_name"],
                    occurrence_date=fields["occurrence_date"],
                    launch_date=fields["launch_date"],
                    last_revision_date=fields["last_revision_date"],
                    executed_by=fields["executed_by"],
                    released_by=fields["released_by"],
                    defect_description=fields["defect_description"],
                    corrective_actions=fields["corrective_actions"],
                    technical_opinion=fields["technical_opinion"],
                    products=fields["products"],
                    problem_tags=fields["problem_tags"],
                    registered_at=fields.get("registered_at"),
                    created_by=created_by,
                    actor_user_id=actor_user_id,
                    actor_email=actor_email,
                    actor_name=actor_name,
                )
                created += 1
                report.append(
                    {
                        "index": index,
                        "result": "created",
                        "record_id": record.get("id"),
                        "sale_number": record.get("sale_number"),
                        "occurrence_date": record.get("occurrence_date"),
                    }
                )
            except Exception as exc:  # noqa: BLE001 — reporta por item
                errors += 1
                report.append(
                    {
                        "index": index,
                        "result": "error",
                        "reason": str(exc),
                        "sale_number": fields["sale_number"],
                    }
                )

        return ImportLmpNonconformitiesResult(
            deleted=deleted,
            created=created,
            skipped=skipped,
            errors=errors,
            items=report,
        )
