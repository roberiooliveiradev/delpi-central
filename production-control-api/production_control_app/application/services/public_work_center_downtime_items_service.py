"""Paradas do turno atual no posto — detalhe para o modal do cockpit público.

Mesmo recorte do KPI «Paradas · turno»: recursos do CT na fila publicada,
dia corrente e turno via HORA_INICIO. Sem código de operador e sem valores em R$.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Callable
from zoneinfo import ZoneInfo

from production_control_app.application.services.machine_load_service import MachineLoadService
from production_control_app.application.services.public_cockpit_access_service import (
    PublicCockpitAccessService,
)
from production_control_app.domain.errors import DelpiGatewayError, PublicAccessDenied
from production_control_app.domain.services.branch_access_service import BranchAccessService

logger = logging.getLogger(__name__)

FACTORY_TIMEZONE = "America/Sao_Paulo"
ITEM_LIMIT = 80


class PublicWorkCenterDowntimeItemsService:
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

    def list_for_work_center(
        self,
        *,
        token: str,
        branch: str,
        work_center: str,
    ) -> dict[str, Any]:
        if not self._access.is_valid_token(token):
            raise PublicAccessDenied(
                self._access.message("invalidToken", "Link do cockpit inválido ou desativado.")
            )
        code = self._branch_access.assert_valid_branch(branch)
        center = str(work_center or "").strip()
        if not center:
            raise ValueError("Informe o centro de trabalho.")

        resources = self._machine_load.public_snapshot_work_center_resources(
            branch=code, work_center=center
        )
        if resources is None:
            raise ValueError(
                f"Centro de trabalho «{center}» não está na fila publicada desta filial."
            )

        today = self._clock().date().isoformat()
        shift = self._current_shift()
        shift_id = (shift or {}).get("id")
        resource_filter = ",".join(resources)

        try:
            rows = _rows(
                self._gateway.fetch_unproductive_hours_items(
                    branch=code,
                    start_date=today,
                    end_date=today,
                    resource=resource_filter,
                    shift=shift_id,
                    page=1,
                    page_size=min(200, max(ITEM_LIMIT, 50)),
                    sort="date_desc",
                )
            )
        except DelpiGatewayError:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.warning("public_downtime_items_unavailable: %s", exc)
            raise DelpiGatewayError("Não foi possível carregar as paradas do turno.") from exc

        items = [_public_item(row) for row in rows[:ITEM_LIMIT]]
        total_hours = round(
            sum(item["hours"] for item in items if item["hours"] is not None),
            4,
        )
        return {
            "branch": code,
            "work_center": center,
            "resources": list(resources),
            "period": {"start_date": today, "end_date": today},
            "shift": shift,
            "items": items,
            "summary": {
                "appointment_count": len(items),
                "total_hours": total_hours,
            },
        }

    def _current_shift(self) -> dict[str, Any] | None:
        try:
            data = _data(self._gateway.fetch_factory_shifts())
        except Exception as exc:  # noqa: BLE001
            logger.warning("public_downtime_items_shift_unavailable: %s", exc)
            return None
        current = data.get("current_shift")
        return current if isinstance(current, dict) else None


def _public_item(row: dict[str, Any]) -> dict[str, Any]:
    reason = _text(row.get("stop_reason") or row.get("motivo"))
    description = _text(
        row.get("stop_reason_description") or row.get("motivoDescricao")
    )
    return {
        "reference_date": _iso_date(row.get("reference_date") or row.get("dataReferencia")),
        "production_order": _text(row.get("production_order") or row.get("op")) or None,
        "operation": _text(row.get("operation") or row.get("operacao")) or None,
        "resource": _text(row.get("resource") or row.get("recurso")) or None,
        "operator_name": _text(row.get("operator_name") or row.get("nomeOperador")) or None,
        "stop_reason": reason or None,
        "stop_reason_description": description or None,
        "observation": _text(row.get("observation") or row.get("observacao")) or None,
        "hours": _number(row.get("hours") if "hours" in row else row.get("tempoHoras")),
    }


def _data(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    data = payload.get("data")
    return data if isinstance(data, dict) else {}


def _rows(payload: Any) -> list[dict[str, Any]]:
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
        return round(float(value), 4)
    except (TypeError, ValueError):
        return None


def _iso_date(value: Any) -> str | None:
    if value is None or value == "":
        return None
    text = str(value).strip()
    if not text:
        return None
    if "T" in text:
        text = text.split("T", 1)[0]
    if " " in text:
        text = text.split(" ", 1)[0]
    return text[:10] or None
