from __future__ import annotations

import logging
import time
from typing import Any

from tm_app.application.services.dashboard_view_scope_service import (
    DashboardScopeFilters,
    DashboardView,
    DashboardViewScopeService,
)
from tm_app.domain.services.dashboard_calculator import DashboardCalculatorService
from tm_app.infrastructure.persistence.repositories.dashboard_data_repository import (
    DashboardCalculoRepository,
    DashboardDataRepository,
)

logger = logging.getLogger(__name__)


def _normalize_competencia_bound(value: str | None) -> str | None:
    """Converte filtro YYYY-MM-DD (ou ISO) para competência YYYY-MM do cache."""
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    if len(raw) == 7 and raw[4] == "-":
        return raw
    parsed = DashboardCalculatorService()._parse_date(raw)
    if parsed is None:
        return raw[:7] if len(raw) >= 7 and raw[4] == "-" else raw
    return parsed.strftime("%Y-%m")


def _filter_rows(
    rows: list[dict[str, Any]],
    *,
    revisao_id: str | None = None,
    processo_id: str | None = None,
    competencia_inicio: str | None = None,
    competencia_fim: str | None = None,
) -> list[dict[str, Any]]:
    filtered = rows
    if revisao_id:
        filtered = [r for r in filtered if str(r.get("revisao_id")) == revisao_id]
    if processo_id:
        filtered = [r for r in filtered if str(r.get("processo_id")) == processo_id]
    if competencia_inicio:
        filtered = [
            r for r in filtered if str(r.get("competencia") or "") >= competencia_inicio
        ]
    if competencia_fim:
        filtered = [
            r for r in filtered if str(r.get("competencia") or "") <= competencia_fim
        ]
    return filtered


class DashboardRecalcService:
    def __init__(self) -> None:
        self._calculator = DashboardCalculatorService()
        self._data_repo = DashboardDataRepository()
        self._dashboard_repo = DashboardCalculoRepository()

    def recalculate(
        self,
        *,
        revisao_id: str | None = None,
        processo_id: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
    ) -> dict:
        competencia_inicio = _normalize_competencia_bound(competencia_inicio)
        competencia_fim = _normalize_competencia_bound(competencia_fim)

        started = time.perf_counter()
        incremental = any(
            [revisao_id, processo_id, competencia_inicio, competencia_fim]
        )

        raw = self._data_repo.load_raw()
        escopo_unidades = DashboardViewScopeService.resolve_escopo_unidades(
            DashboardScopeFilters(
                view=DashboardView.CONSOLIDATED,
                filial_id=None,
                setor_id=None,
            )
        )
        all_rows = self._calculator.build_dashboard_rows(
            raw,
            escopo_unidades=escopo_unidades,
        )

        if not incremental:
            inserted = self._dashboard_repo.replace_all(all_rows)
            mode = "full"
            deleted = None
        else:
            target_rows = _filter_rows(
                all_rows,
                revisao_id=revisao_id,
                processo_id=processo_id,
                competencia_inicio=competencia_inicio,
                competencia_fim=competencia_fim,
            )
            deleted = 0
            if revisao_id:
                deleted = self._dashboard_repo.delete_by_revisao(revisao_id)
            elif processo_id:
                deleted = self._dashboard_repo.delete_by_processo(processo_id)
            else:
                deleted = self._dashboard_repo.delete_by_competencia_range(
                    competencia_inicio=competencia_inicio,
                    competencia_fim=competencia_fim,
                )
            inserted = self._dashboard_repo.upsert_rows(target_rows)
            mode = "incremental"

        elapsed_ms = (time.perf_counter() - started) * 1000

        logger.info(
            "transformometro_dashboard_recalc_ok mode=%s rows=%d deleted=%s elapsed_ms=%.0f",
            mode,
            inserted,
            deleted,
            elapsed_ms,
        )

        result: dict[str, Any] = {
            "mode": mode,
            "rows_upserted": inserted,
            "elapsed_ms": round(elapsed_ms),
        }
        if deleted is not None:
            result["rows_deleted"] = deleted
        if revisao_id:
            result["revisao_id"] = revisao_id
        if processo_id:
            result["processo_id"] = processo_id
        if competencia_inicio:
            result["competencia_inicio"] = competencia_inicio
        if competencia_fim:
            result["competencia_fim"] = competencia_fim
        return result
