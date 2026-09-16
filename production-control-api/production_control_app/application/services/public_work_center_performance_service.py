"""Desempenho do posto para o cockpit público — composição, nunca recálculo.

Eficiência e horas improdutivas pertencem à api-delpi. Este serviço só recorta
o que o cockpit anônimo pode ver: agregados do centro de trabalho, sem nome de
operador e sem valores em reais.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any, Callable, Iterable
from zoneinfo import ZoneInfo

from production_control_app.application.services.machine_load_service import MachineLoadService
from production_control_app.application.services.public_cockpit_access_service import (
    PublicCockpitAccessService,
)
from production_control_app.application.services.public_work_center_performance_cache import (
    get_work_center_performance_cache,
    put_work_center_performance_cache,
)
from production_control_app.domain.errors import PublicAccessDenied
from production_control_app.domain.services.branch_access_service import BranchAccessService

logger = logging.getLogger(__name__)

FACTORY_TIMEZONE = "America/Sao_Paulo"

MIN_DAYS = 7
MAX_DAYS = 30
DEFAULT_DAYS = 14

STOP_REASON_LIMIT = 8
APPOINTMENT_LIMIT = 40

_UNAVAILABLE_MESSAGE = "Indicador indisponível no momento."


def clamp_days(raw: Any) -> int:
    """Janela do gráfico — o cockpit não decide quanto histórico o TOTVS varre."""
    try:
        value = int(raw) if raw is not None and str(raw).strip() != "" else DEFAULT_DAYS
    except (TypeError, ValueError):
        return DEFAULT_DAYS
    return max(MIN_DAYS, min(MAX_DAYS, value))


class PublicWorkCenterPerformanceService:
    def __init__(
        self,
        gateway: Any,
        *,
        access: PublicCockpitAccessService,
        machine_load: MachineLoadService,
        branch_access: BranchAccessService,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._gateway = gateway
        self._access = access
        self._machine_load = machine_load
        self._branch_access = branch_access
        self._clock = clock or (lambda: datetime.now(ZoneInfo(FACTORY_TIMEZONE)))

    def build(
        self,
        *,
        token: str,
        branch: str,
        work_center: str,
        days: Any = None,
    ) -> dict[str, Any]:
        if not self._access.is_valid_token(token):
            raise PublicAccessDenied(
                self._access.message("invalidToken", "Link do cockpit inválido ou desativado.")
            )
        code = self._branch_access.assert_valid_branch(branch)
        center = str(work_center or "").strip()
        if not center:
            raise ValueError("Informe o centro de trabalho.")

        # O mesmo guardrail do PDF do desenho: só responde sobre o que o PCP publicou.
        resources = self._machine_load.public_snapshot_work_center_resources(
            branch=code, work_center=center
        )
        if resources is None:
            raise ValueError(
                f"Centro de trabalho «{center}» não está na fila publicada desta filial."
            )

        window = clamp_days(days)
        cached = get_work_center_performance_cache(
            branch=code, work_center=center, days=window
        )
        if cached is not None:
            return cached

        today = self._clock().date()
        start = today - timedelta(days=window - 1)
        shift = self._current_shift()

        payload = {
            "branch": code,
            "work_center": center,
            "resources": list(resources),
            "days": window,
            "period": {
                "start_date": start.isoformat(),
                "end_date": today.isoformat(),
            },
            "generated_at": self._clock().isoformat(),
            "shift": shift,
            "efficiency": self._efficiency_block(
                branch=code,
                work_center=center,
                start=start,
                today=today,
                shift_id=(shift or {}).get("id"),
            ),
            "downtime": self._downtime_block(
                branch=code,
                resources=resources,
                start=start,
                today=today,
            ),
        }
        put_work_center_performance_cache(
            payload, branch=code, work_center=center, days=window
        )
        return payload

    def _current_shift(self) -> dict[str, Any] | None:
        try:
            data = _data(self._gateway.fetch_factory_shifts())
        except Exception as exc:  # noqa: BLE001
            logger.warning("public_performance_shift_unavailable: %s", exc)
            return None
        current = data.get("current_shift")
        return current if isinstance(current, dict) else None

    def _efficiency_block(
        self,
        *,
        branch: str,
        work_center: str,
        start: date,
        today: date,
        shift_id: str | None,
    ) -> dict[str, Any]:
        """Bloco degradável: se a eficiência falhar, a fila e as paradas continuam."""
        try:
            shift_rows = _rows(
                self._gateway.fetch_efficiency_by_work_center(
                    branch=branch,
                    start_date=today.isoformat(),
                    end_date=today.isoformat(),
                    work_center=work_center,
                    shift=shift_id,
                )
            )
            day_rows = _rows(
                self._gateway.fetch_efficiency_by_work_center(
                    branch=branch,
                    start_date=today.isoformat(),
                    end_date=today.isoformat(),
                    work_center=work_center,
                )
            )
            series_rows = _rows(
                self._gateway.fetch_efficiency_series(
                    branch=branch,
                    start_date=start.isoformat(),
                    end_date=today.isoformat(),
                    work_center=work_center,
                )
            )
            appointment_rows = _rows(
                self._gateway.fetch_eficiencia_fabril_appointments(
                    branch=branch,
                    start_date=today.isoformat(),
                    end_date=today.isoformat(),
                    work_center=work_center,
                    shift=shift_id,
                )
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("public_performance_efficiency_unavailable: %s", exc)
            return _unavailable()

        series = [
            {
                "date": _text(row.get("date")),
                "efficiency_pct": _number(row.get("efficiency_pct")),
                "appointment_count": _integer(row.get("appointment_count")),
            }
            for row in series_rows
            if _text(row.get("date"))
        ]
        shift_row = _first_center_row(shift_rows, work_center)
        day_row = _first_center_row(day_rows, work_center)
        period_values = [
            point["efficiency_pct"]
            for point in series
            if point["efficiency_pct"] is not None
        ]

        return {
            "available": True,
            "shift_pct": _number((shift_row or {}).get("efficiency_pct")),
            "shift_appointment_count": _integer((shift_row or {}).get("appointment_count")),
            "shift_produced_qty": _sum_produced_qty(appointment_rows),
            "day_pct": _number((day_row or {}).get("efficiency_pct")),
            "day_appointment_count": _integer((day_row or {}).get("appointment_count")),
            "period_avg_pct": (
                round(sum(period_values) / len(period_values), 2) if period_values else None
            ),
            "series": series,
            "appointments": [
                _public_appointment(row) for row in appointment_rows[:APPOINTMENT_LIMIT]
            ],
        }

    def _downtime_block(
        self,
        *,
        branch: str,
        resources: Iterable[str],
        start: date,
        today: date,
    ) -> dict[str, Any]:
        """Bloco degradável: se as paradas falharem, a eficiência continua respondendo."""
        # As paradas do BI são filtradas por recurso; um CT pode ter mais de um.
        resource_filter = ",".join(resources)
        try:
            today_summary = _data(
                self._gateway.fetch_unproductive_hours_summary(
                    branch=branch,
                    start_date=today.isoformat(),
                    end_date=today.isoformat(),
                    resource=resource_filter,
                )
            ).get("summary")
            reason_rows = _rows(
                self._gateway.fetch_unproductive_hours_ranking(
                    branch=branch,
                    start_date=start.isoformat(),
                    end_date=today.isoformat(),
                    rank_by="stop_reason",
                    resource=resource_filter,
                    limit=STOP_REASON_LIMIT,
                )
            )
            series_rows = _rows(
                self._gateway.fetch_unproductive_hours_series(
                    branch=branch,
                    start_date=start.isoformat(),
                    end_date=today.isoformat(),
                    resource=resource_filter,
                )
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("public_performance_downtime_unavailable: %s", exc)
            return _unavailable()

        summary = today_summary if isinstance(today_summary, dict) else {}
        series = [
            {
                "date": _text(row.get("date") or row.get("dataReferencia")),
                "hours": _number(row.get("total_hours") or row.get("totalHoras")) or 0.0,
                "appointment_count": _integer(
                    row.get("total_appointments") or row.get("totalApontamentos")
                ),
            }
            for row in series_rows
            if _text(row.get("date") or row.get("dataReferencia"))
        ]

        return {
            "available": True,
            "today_hours": _number(summary.get("total_hours") or summary.get("totalHoras"))
            or 0.0,
            "today_appointment_count": _integer(
                summary.get("total_appointments") or summary.get("totalApontamentos")
            ),
            "period_hours": round(sum(point["hours"] for point in series), 4),
            "period_appointment_count": sum(
                point["appointment_count"] or 0 for point in series
            ),
            "by_reason": [_public_stop_reason(row) for row in reason_rows],
            "series": series,
        }


def _unavailable() -> dict[str, Any]:
    return {"available": False, "message": _UNAVAILABLE_MESSAGE}


def _sum_produced_qty(rows: list[dict[str, Any]]) -> float | None:
    """Soma ``qtd_apontada`` de todos os apontamentos (não só o recorte da lista pública)."""
    total = 0.0
    found = False
    for row in rows:
        raw = row.get("qtd_apontada")
        if raw is None or raw == "":
            continue
        try:
            qty = float(raw)
        except (TypeError, ValueError):
            continue
        found = True
        total += qty
    return round(total, 3) if found else None


def _public_appointment(row: dict[str, Any]) -> dict[str, Any]:
    """Recorte do chão: nome do operador ok; sem login/código e sem valores em R$."""
    pa_code = _text(row.get("produto_acabado") or row.get("produtoAcabado"))
    product_code = _text(row.get("produto"))
    return {
        "production_order": _text(row.get("op")),
        "operation": _text(row.get("operacao")),
        "operation_description": _text(row.get("descricao_operacao")),
        "pa_product_code": pa_code or None,
        "product_code": product_code,
        "operator_name": _text(row.get("nome_operador") or row.get("nomeOperador")) or None,
        "quantity": _number(row.get("qtd_apontada")),
        "real_hours": _number(row.get("tempo_real_horas")),
        "planned_hours": _number(row.get("tempo_previsto_horas")),
        "efficiency_pct": _number(row.get("eficiencia_percentual")),
        "start_time": _text(row.get("hora_inicio")),
        "end_time": _text(row.get("hora_final")),
    }


def _public_stop_reason(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "stop_reason": _text(row.get("motivo") or row.get("stop_reason")),
        "stop_reason_description": _text(
            row.get("motivoDescricao") or row.get("stop_reason_description")
        ),
        "hours": _number(row.get("totalHoras") or row.get("total_hours")) or 0.0,
        "appointment_count": _integer(
            row.get("totalApontamentos") or row.get("total_appointments")
        ),
    }


def _first_center_row(rows: list[dict[str, Any]], work_center: str) -> dict[str, Any] | None:
    wanted = work_center.strip()
    for row in rows:
        if _text(row.get("work_center")) == wanted:
            return row
    return rows[0] if rows else None


def _data(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    data = payload.get("data")
    return data if isinstance(data, dict) else {}


def _rows(payload: Any) -> list[dict[str, Any]]:
    """A api-delpi devolve ora lista direta em ``data``, ora ``data.items``."""
    if not isinstance(payload, dict):
        return []
    data = payload.get("data")
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    if isinstance(data, dict):
        items = data.get("items")
        if isinstance(items, list):
            return [row for row in items if isinstance(row, dict)]
    return []


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return None


def _integer(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
