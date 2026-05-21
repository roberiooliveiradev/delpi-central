from __future__ import annotations

from datetime import date
from typing import Any

from tm_app.domain.services.dashboard_calculator import DashboardCalculatorService
from tm_app.infrastructure.persistence.repositories.dashboard_data_repository import (
    DashboardDataRepository,
)
from tm_app.infrastructure.persistence.repositories.revisao_repository import (
    RevisaoRepository,
)


class RevisaoRateioDiagnosticService:
    """Avisa quando custo de recurso compartilhado supera ganho operacional da revisão."""

    def diagnose(self, revisao_id: str, *, competencia: str | None = None) -> dict[str, Any] | None:
        revisao = RevisaoRepository().get(revisao_id)
        if not revisao:
            return None

        processo_id = str(revisao.get("processo_id") or "")
        raw = DashboardDataRepository().load_raw()
        calc = DashboardCalculatorService()
        rows = [
            row
            for row in calc.build_dashboard_rows(raw)
            if str(row.get("revisao_id")) == revisao_id
        ]

        if competencia:
            rows = [row for row in rows if row.get("competencia") == competencia]

        if not rows:
            target_month = competencia or date.today().strftime("%Y-%m")
            return {
                "revisao_id": revisao_id,
                "processo_id": processo_id,
                "competencia": target_month,
                "economia_bruta": 0.0,
                "custo_recursos_compartilhados_mes": 0.0,
                "economia_liquida_mes": 0.0,
                "rateio_excede_ganho": False,
                "message": "Sem dados calculados para esta revisão no período.",
            }

        latest = sorted(rows, key=lambda r: r.get("competencia") or "")[-1]
        economia_bruta = float(latest.get("economia_bruta") or 0)
        custo_rc = float(latest.get("custo_recursos_compartilhados_mes") or 0)
        economia_liquida = float(latest.get("economia_liquida_mes") or 0)
        excede = custo_rc > economia_bruta and economia_bruta >= 0

        message = "OK"
        if excede:
            message = (
                "Custo de recursos compartilhados no mês supera a economia bruta operacional. "
                "Revise vínculos, peso de rateio ou critério do recurso."
            )
        elif economia_liquida < 0:
            message = "Economia líquida negativa no mês (recorrente ou investimento)."

        return {
            "revisao_id": revisao_id,
            "processo_id": processo_id,
            "competencia": latest.get("competencia"),
            "economia_bruta": round(economia_bruta, 2),
            "custo_recursos_compartilhados_mes": round(custo_rc, 2),
            "economia_liquida_mes": round(economia_liquida, 2),
            "rateio_excede_ganho": excede,
            "message": message,
        }
