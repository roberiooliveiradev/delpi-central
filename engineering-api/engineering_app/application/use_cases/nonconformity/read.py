"""Use cases READ do contexto NC — E-NC-01..06.

Adapters de persistência são síncronos; os use cases são async e
executam as chamadas em thread pool para não bloquear o event loop.
Erros de repositório propagam como exceções de domínio → estados
honestos no edge (nunca lista vazia falsa).
"""

from __future__ import annotations

import asyncio
from datetime import date, datetime, timezone
from typing import Any

from engineering_app.application.ports.nonconformity_repository import (
    EarliestOvDateSource,
    NonconformityRepository,
)
from engineering_app.domain.nonconformity.errors import (
    NcNotFoundError,
    NcValidationError,
)
from engineering_app.domain.nonconformity.sort import resolve_nc_sort
from engineering_app.domain.nonconformity.streak import compute_occurrence_streak

NC_EXPORT_VERSION = 1
NC_MAX_PAGE_SIZE = 200


class ListNonconformitiesUseCase:
    """E-NC-01 — listagem paginada com filtros e ordenação whitelist."""

    def __init__(self, repository: NonconformityRepository) -> None:
        self._repository = repository

    async def execute(
        self,
        *,
        status: str | None = None,
        sale_number: str | None = None,
        lmp_number: str | None = None,
        customer_name: str | None = None,
        product_code: str | None = None,
        problem_tag: str | None = None,
        date_start: str | None = None,
        date_end: str | None = None,
        sort_by: str | None = None,
        sort_dir: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        _validate_period(date_start, date_end)
        sort_key, sort_dir_resolved = resolve_nc_sort(sort_by, sort_dir)
        return await asyncio.to_thread(
            self._repository.list_records,
            status=status,
            sale_number=sale_number,
            lmp_number=lmp_number,
            customer_name=customer_name,
            product_code=product_code,
            problem_tag=problem_tag,
            date_start=date_start,
            date_end=date_end,
            sort_by=sort_key,
            sort_dir=sort_dir_resolved,
            page=page,
            page_size=page_size,
        )


class GetNonconformityUseCase:
    """E-NC-02 — detalhe de uma NC por UUID."""

    def __init__(self, repository: NonconformityRepository) -> None:
        self._repository = repository

    async def execute(self, record_id: str) -> dict[str, Any]:
        record = await asyncio.to_thread(self._repository.get_record, record_id)
        if record is None:
            raise NcNotFoundError(record_id)
        return record


class ListNonconformityHistoryUseCase:
    """E-NC-03 — eventos append-only de uma NC (mais recentes primeiro)."""

    def __init__(self, repository: NonconformityRepository) -> None:
        self._repository = repository

    async def execute(self, record_id: str) -> list[dict[str, Any]]:
        events = await asyncio.to_thread(
            self._repository.list_history, record_id
        )
        if events is None:
            raise NcNotFoundError(record_id)
        return events


class GetNonconformityIndicatorsUseCase:
    """E-NC-04 — dias sem NC (streak atual/recorde) + contadores.

    Ocorrências vêm do repositório Engineering; ``reference_start_date``
    (âncora «primeira OV») vem do port de fatos oficiais — sem NCs e sem
    âncora disponível, o indicador degrada honestamente (0 + flag).
    """

    def __init__(
        self,
        repository: NonconformityRepository,
        earliest_ov_source: EarliestOvDateSource | None = None,
    ) -> None:
        self._repository = repository
        self._earliest_ov = earliest_ov_source

    async def execute(
        self,
        *,
        as_of: date | None = None,
        access_token: str | None = None,
    ) -> dict[str, Any]:
        as_of_date = as_of or date.today()
        occurrence_dates = await asyncio.to_thread(
            self._repository.list_occurrence_dates
        )
        reference_start_date: date | None = None
        anchor_available = True
        if not occurrence_dates and self._earliest_ov is not None:
            try:
                reference_start_date = await self._earliest_ov.get_reference_start_date(
                    access_token or ""
                )
            except Exception:
                anchor_available = False
        streak = compute_occurrence_streak(
            occurrence_dates,
            as_of=as_of_date,
            reference_start_date=reference_start_date,
        )
        if not anchor_available:
            streak["reference_start_degraded"] = True
        return streak


class ListProblemTagsUseCase:
    """E-NC-05 — catálogo compartilhado de tags de problema."""

    def __init__(self, repository: NonconformityRepository) -> None:
        self._repository = repository

    async def execute(self) -> list[dict[str, Any]]:
        return await asyncio.to_thread(
            self._repository.list_problem_tag_catalog
        )


class ExportNonconformitiesUseCase:
    """E-NC-06 — export JSON completo (backup/migração)."""

    def __init__(self, repository: NonconformityRepository) -> None:
        self._repository = repository

    async def execute(self) -> dict[str, Any]:
        items = await asyncio.to_thread(self._repository.export_records)
        return {
            "version": NC_EXPORT_VERSION,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "count": len(items),
            "items": items,
        }


def _validate_period(date_start: str | None, date_end: str | None) -> None:
    for name, value in (("date_start", date_start), ("date_end", date_end)):
        if value is None:
            continue
        try:
            date.fromisoformat(str(value)[:10])
        except ValueError as exc:
            raise NcValidationError(
                f"{name} inválida (YYYY-MM-DD).",
                fields={name: str(value)},
            ) from exc
    if date_start and date_end and str(date_start)[:10] > str(date_end)[:10]:
        raise NcValidationError(
            "date_start posterior a date_end.",
            fields={"date_start": date_start, "date_end": date_end},
        )
