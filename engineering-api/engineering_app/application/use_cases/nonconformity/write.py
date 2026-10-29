"""Use cases WRITE do contexto NC — E-NC-07..10.

Executáveis apenas onde o adapter configurado aponta para persistência
autorizada (sandbox/dev isolado ou, pós-ADR aprovado, o schema oficial).
IMPORT é substituição total: exige ``confirm_replace=True`` explícito no
contrato E-NC-10 + opt-in de ambiente no adapter Postgres — nunca
execução acidental contra base compartilhada/produtiva.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from engineering_app.application.ports.nonconformity_repository import (
    NonconformityRepository,
)
from engineering_app.domain.nonconformity.errors import (
    NcNotFoundError,
    NcUnsafeOperationError,
    NcValidationError,
)
from engineering_app.domain.nonconformity.models import (
    NcActor,
    normalize_nc_status,
)
from engineering_app.domain.nonconformity.normalize import (
    normalize_problem_tag_labels,
    normalize_products,
)

_REGISTERED_AT_TZ_SUFFIX = "T00:00:00-03:00"
_STRIP_IMPORT_KEYS = frozenset(
    {"id", "created_at", "updated_at", "created_by", "updated_by", "product_codes"}
)


class CreateNonconformityUseCase:
    """E-NC-07 — criação com histórico `created` e auditoria do ator.

    Idempotência: ``idempotency_key`` opcional — adapters deduplicam por
    chave natural + ator em janela curta (contrato E-NC-07 v1).
    """

    def __init__(self, repository: NonconformityRepository) -> None:
        self._repository = repository

    async def execute(
        self,
        *,
        payload: dict[str, Any],
        actor: NcActor,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        fields = normalize_nc_payload(payload, require_occurrence=False)
        return await asyncio.to_thread(
            self._repository.create_record,
            **fields,
            actor=actor,
            idempotency_key=idempotency_key,
        )


class UpdateNonconformityUseCase:
    """E-NC-08 — full-replace; ``occurrence_date`` obrigatória (legado).

    Concorrência otimista opcional: ``expected_updated_at`` (ETag do GET)
    → mismatch gera ``NcConcurrencyError`` (409 no edge).
    """

    def __init__(self, repository: NonconformityRepository) -> None:
        self._repository = repository

    async def execute(
        self,
        *,
        record_id: str,
        payload: dict[str, Any],
        actor: NcActor,
        expected_updated_at: str | None = None,
    ) -> dict[str, Any]:
        fields = normalize_nc_payload(payload, require_occurrence=True)
        result = await asyncio.to_thread(
            self._repository.update_record,
            record_id=record_id,
            **fields,
            actor=actor,
            expected_updated_at=expected_updated_at,
        )
        if result is None:
            raise NcNotFoundError(record_id)
        return result


class DeleteNonconformityUseCase:
    """E-NC-09 — hard delete com cascade do histórico (GUC V008)."""

    def __init__(self, repository: NonconformityRepository) -> None:
        self._repository = repository

    async def execute(self, record_id: str) -> dict[str, Any]:
        deleted = await asyncio.to_thread(
            self._repository.delete_record, record_id
        )
        if not deleted:
            raise NcNotFoundError(record_id)
        return {"id": record_id, "deleted": True}


@dataclass(frozen=True)
class ImportNonconformitiesResult:
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


class ImportNonconformitiesUseCase:
    """E-NC-10 — importação JSON com substituição total do acervo.

    Semântica legado preservada (dry_run, dedup por normalização,
    relatório por item). Proteção adicional do contrato novo:
    ``confirm_replace=True`` obrigatório fora de dry_run; o adapter
    Postgres adicionalmente exige ``ENG_NC_IMPORT_REPLACE_ENABLED``.
    """

    def __init__(self, repository: NonconformityRepository) -> None:
        self._repository = repository

    async def execute(
        self,
        *,
        items: list[dict[str, Any]],
        actor: NcActor,
        dry_run: bool = False,
        confirm_replace: bool = False,
    ) -> ImportNonconformitiesResult:
        if not dry_run and not confirm_replace:
            raise NcUnsafeOperationError(
                "Importação substitui todo o acervo: confirm_replace é "
                "obrigatório fora de dry_run."
            )

        created = 0
        skipped = 0
        errors = 0
        report: list[dict[str, Any]] = []
        deleted = 0

        if dry_run:
            report.append(
                {"index": -1, "result": "would_replace_all", "reason": "dry_run"}
            )
        else:
            deleted = await asyncio.to_thread(self._repository.delete_all_records)
            report.append(
                {"index": -1, "result": "deleted_all", "deleted": deleted}
            )

        for index, raw in enumerate(items):
            if not isinstance(raw, dict):
                skipped += 1
                report.append(
                    {"index": index, "result": "skipped", "reason": "invalid_item"}
                )
                continue

            fields = normalize_import_item(raw)
            status = fields["status"]
            if status not in {"open", "in_progress", "done"}:
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
                record = await asyncio.to_thread(
                    self._repository.create_record,
                    **fields,
                    actor=actor,
                    idempotency_key=None,
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

        return ImportNonconformitiesResult(
            deleted=deleted,
            created=created,
            skipped=skipped,
            errors=errors,
            items=report,
        )


def normalize_nc_payload(
    payload: dict[str, Any], *, require_occurrence: bool
) -> dict[str, Any]:
    """Normaliza e valida body create/update → kwargs do repositório."""
    status = normalize_nc_status(payload.get("status") or "open")
    if status is None:
        raise NcValidationError(
            f"Status inválido: {payload.get('status')}",
            fields={"status": str(payload.get("status"))},
        )
    occurrence_date = _blank(payload.get("occurrence_date"))
    if require_occurrence and occurrence_date is None:
        raise NcValidationError(
            "occurrence_date é obrigatória.",
            fields={"occurrence_date": "required"},
        )
    _validate_iso_date("occurrence_date", occurrence_date)
    launch = _blank(payload.get("launch_date"))
    revision = _blank(payload.get("last_revision_date"))
    _validate_iso_date("launch_date", launch)
    _validate_iso_date("last_revision_date", revision)

    return {
        "status": status,
        "sale_number": _blank(payload.get("sale_number")),
        "lmp_number": _blank(payload.get("lmp_number")),
        "customer_name": _blank(payload.get("customer_name")),
        "occurrence_date": occurrence_date,
        "launch_date": launch,
        "last_revision_date": revision,
        "executed_by": _blank(payload.get("executed_by")),
        "released_by": _blank(payload.get("released_by")),
        "defect_description": _blank(payload.get("defect_description")),
        "corrective_actions": _blank(payload.get("corrective_actions")),
        "technical_opinion": _blank(payload.get("technical_opinion")),
        "products": normalize_products(payload.get("products")),
        "problem_tags": normalize_problem_tag_labels(payload.get("problem_tags")),
        "registered_at": _blank(payload.get("registered_at")),
    }


def normalize_import_item(raw: dict[str, Any] | None) -> dict[str, Any]:
    """Extrai campos aceitos por ``create_record`` de um item exportado.

    Status inválido NÃO levanta aqui — o use case classifica como
    ``skipped`` no relatório por item (semântica legado).
    """
    source = dict(raw or {})
    for key in _STRIP_IMPORT_KEYS:
        source.pop(key, None)

    status = str(source.get("status") or "open").strip().lower() or "open"
    products = normalize_products(source.get("products"))
    if not products and isinstance(source.get("product_codes"), list):
        products = normalize_products(
            [{"product_code": code} for code in source["product_codes"]]
        )
    tags = normalize_problem_tag_labels(source.get("problem_tags"))
    occurrence_date = _normalize_occurrence_date(
        source.get("occurrence_date"), source.get("registered_at")
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
            source.get("registered_at"), occurrence_date=occurrence_date
        ),
    }


def _blank(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _validate_iso_date(name: str, value: str | None) -> None:
    if value is None:
        return
    from datetime import date

    try:
        date.fromisoformat(value[:10])
    except ValueError as exc:
        raise NcValidationError(
            f"{name} inválida (YYYY-MM-DD).", fields={name: value}
        ) from exc


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
    value: Any, *, occurrence_date: str | None = None
) -> str | None:
    """Data/hora de registro alinhada à ocorrência (semântica legado)."""
    occ = _blank(occurrence_date)
    if occ:
        occ_day = occ[:10]
        text = _blank(value)
        if text and text[:10] == occ_day:
            return text
        return f"{occ_day}{_REGISTERED_AT_TZ_SUFFIX}"
    return _blank(value)
