from __future__ import annotations

from typing import Any

from tm_app.application.services.dashboard_live_service import DashboardLiveService


class DashboardAlertsService:
    """Processos com economia líquida negativa por N meses consecutivos."""

    def __init__(self, *, min_consecutive_months: int = 3) -> None:
        self._min_months = max(1, min_consecutive_months)

    def list_negative_savings_alerts(
        self,
        *,
        filial_id: str | None = None,
        setor_id: str | None = None,
        familia_processo: str | None = None,
        competencia_inicio: str | None = None,
        competencia_fim: str | None = None,
    ) -> dict[str, Any]:
        rows = DashboardLiveService().query_process_monthly_liquida(
            filial_id=filial_id,
            setor_id=setor_id,
            familia_processo=familia_processo,
            competencia_inicio=competencia_inicio,
            competencia_fim=competencia_fim,
        )

        by_process: dict[str, list[tuple[str, float]]] = {}
        meta: dict[str, dict[str, Any]] = {}

        for row in rows:
            pid = str(row["processo_id"])
            by_process.setdefault(pid, []).append(
                (str(row["competencia"]), float(row["economia_liquida_mes"] or 0))
            )
            meta[pid] = {
                "processo_id": pid,
                "codigo_processo": row.get("codigo_processo"),
                "nome_processo": row.get("nome_processo"),
                "filial_id": row.get("filial_id"),
                "setor_id": row.get("setor_id"),
                "familia_processo": row.get("familia_processo"),
                "agrupador_ferramenta": row.get("agrupador_ferramenta"),
            }

        alerts: list[dict[str, Any]] = []
        for pid, series in by_process.items():
            streak = self._longest_negative_streak(series)
            if streak["months"] >= self._min_months:
                alerts.append({**meta[pid], **streak})

        alerts.sort(key=lambda item: (-int(item["months"]), str(item.get("nome_processo") or "")))
        return {
            "min_consecutive_months": self._min_months,
            "total": len(alerts),
            "items": alerts,
        }

    def _longest_negative_streak(
        self,
        series: list[tuple[str, float]],
    ) -> dict[str, Any]:
        ordered = sorted(series, key=lambda item: item[0])
        best_months = 0
        best_start: str | None = None
        best_end: str | None = None
        best_total = 0.0

        current_months = 0
        current_start: str | None = None
        current_total = 0.0

        for competencia, liquida in ordered:
            if liquida < 0:
                if current_months == 0:
                    current_start = competencia
                current_months += 1
                current_total += liquida
                if current_months > best_months:
                    best_months = current_months
                    best_start = current_start
                    best_end = competencia
                    best_total = current_total
            else:
                current_months = 0
                current_start = None
                current_total = 0.0

        return {
            "months": best_months,
            "competencia_inicio": best_start,
            "competencia_fim": best_end,
            "economia_liquida_acumulada": round(best_total, 2),
        }
