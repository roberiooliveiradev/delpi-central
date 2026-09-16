"""Histórico de apontamentos de uma OP+operação no cockpit público.

Fonte: ``SH6010`` via ``/production/appointments`` (não a view de eficiência).
A view ``vw_Apontamentos_Eficiencia`` exclui ``CT-00`` na própria SQL — inútil
para saldo/abatimento. Recorte estrito por OP + operação. O link anônimo só
vê a OP/operação da fila publicada.

O **total** apontado e o saldo da operação vêm da fila (agregado canônico da
api-delpi sobre a SH6 inteira); a lista aqui é o detalhe da janela recente.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
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
HISTORY_DAYS = 120
ITEM_LIMIT = 80


class PublicOperationAppointmentsService:
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

    def list_for_operation(
        self,
        *,
        token: str,
        branch: str,
        production_order: str,
        operation_code: str,
    ) -> dict[str, Any]:
        if not self._access.is_valid_token(token):
            raise PublicAccessDenied(
                self._access.message("invalidToken", "Link do cockpit inválido ou desativado.")
            )
        code = self._branch_access.assert_valid_branch(branch)
        order = str(production_order or "").strip()
        operation = str(operation_code or "").strip()
        if not order or not operation:
            raise ValueError("Informe a ordem de produção e o código da operação.")

        balance = self._machine_load.public_operation_balance(
            branch=code,
            production_order=order,
            operation_code=operation,
        )
        if balance is None and not self._machine_load.public_snapshot_contains_operation(
            branch=code,
            production_order=order,
            operation_code=operation,
        ):
            raise ValueError(
                "Esta operação não está na fila publicada desta filial."
            )

        today = self._clock().date()
        start = today - timedelta(days=HISTORY_DAYS - 1)
        try:
            rows = _rows(
                self._gateway.fetch_production_appointments(
                    branch=code,
                    start_date=start.isoformat(),
                    end_date=today.isoformat(),
                    op=order,
                    page=1,
                    page_size=200,
                )
            )
        except DelpiGatewayError as exc:
            logger.warning("public_operation_appointments_unavailable: %s", exc)
            raise
        except Exception as exc:  # noqa: BLE001
            logger.warning("public_operation_appointments_unavailable: %s", exc)
            raise DelpiGatewayError("Não foi possível carregar os apontamentos.") from exc

        wanted_op = _norm_operation(operation)
        items = [
            _public_row(row)
            for row in rows
            if _norm_operation(_text(row.get("operation") or row.get("operacao")))
            == wanted_op
        ]
        items.sort(key=_sort_key)
        # Mantém a janela mais recente; a tabela sobe do mais antigo ao mais novo.
        if len(items) > ITEM_LIMIT:
            items = items[-ITEM_LIMIT:]

        quantities = [item["quantity"] for item in items if item["quantity"] is not None]
        window_produced = round(sum(quantities), 3) if quantities else None
        # Total da operação vem da fila (SH6 inteira); a janela só cobre o detalhe.
        produced = (
            balance.get("operation_produced_qty") if balance is not None else None
        )
        return {
            "branch": code,
            "production_order": order,
            "operation_code": operation,
            "period": {"start_date": start.isoformat(), "end_date": today.isoformat()},
            "items": items,
            "summary": {
                "appointment_count": len(items),
                "produced_qty": window_produced if produced is None else round(produced, 3),
                "window_produced_qty": window_produced,
                "pending_qty": (
                    balance.get("operation_pending_qty") if balance is not None else None
                ),
            },
        }


def _public_row(row: dict[str, Any]) -> dict[str, Any]:
    produced_on = _iso_date(
        row.get("appointment_date")
        or row.get("start_date")
        or row.get("data_producao")
        or row.get("dataProducao")
    )
    start_time = (
        _text(row.get("start_time") or row.get("hora_inicio") or row.get("horaInicio"))
        or None
    )
    end_time = (
        _text(row.get("end_time") or row.get("hora_final") or row.get("horaFinal"))
        or None
    )
    quantity, unit = _quantity_mi_scale(row)
    return {
        "produced_on": produced_on,
        "start_time": start_time,
        "end_time": end_time,
        "quantity": quantity,
        "unit": unit,
        "work_center": _text(row.get("work_center") or row.get("centro_trabalho"))
        or None,
        "operator_name": _text(row.get("operator_name") or row.get("nome_operador"))
        or None,
    }


def _quantity_mi_scale(row: dict[str, Any]) -> tuple[float | None, str | None]:
    """Cockpit e machine-load usam escala MI; a API de apontamentos devolve UN."""
    raw = row.get("qty_produced")
    if raw is None:
        raw = row.get("qtd_apontada") or row.get("qtdApontada")
    quantity = _number(raw)
    unit = _text(row.get("unit") or row.get("unidade")) or "MI"
    if unit.upper() == "UN" and quantity is not None:
        return round(quantity / 1000.0, 3), "MI"
    return quantity, unit or None


def _sort_key(item: dict[str, Any]) -> tuple[str, str]:
    return (item.get("produced_on") or "", item.get("start_time") or "")


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


def _norm_operation(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        return ""
    return cleaned.lstrip("0") or "0"


def _number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return round(float(value), 3)
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
    if text.isdigit() and len(text) == 8:
        return f"{text[0:4]}-{text[4:6]}-{text[6:8]}"
    return text[:10] or None
