"""Central de Fechamento — financial settlements (R01/R02) BFF routes.

The BFF owns: human principal check, ``controllership-finance.access``
(Core-resolved effective permissions only), delegation of the user Bearer and
typed error mapping. Dataset-scope authorization stays fail-closed at the
producer: when api-delpi answers ``scope_unavailable`` the BFF relays the
typed 403 without inventing access (doc 48 D3.1). No SQL lives here; no
physical table names leave this boundary.
"""

from __future__ import annotations

import logging
from decimal import Decimal, InvalidOperation
from typing import Any

from fastapi import APIRouter, Query, Request
from fastapi.responses import Response

from delpi_auth.authz_core import has_permission

from controllership_finance_app.core.responses import fail, ok
from controllership_finance_app.infrastructure.api_delpi_gateway import (
    ApiDelpiSettlementsGateway,
    DelpiApiGatewayError,
)

logger = logging.getLogger("controllership-finance-api.closing")

ACCESS_PERMISSION = "controllership-finance.access"

router = APIRouter(prefix="/closing", tags=["Closing"])

_SIDE_TO_PATH = {
    "payable": "/financeiro/settlements/payables",
    "receivable": "/financeiro/settlements/receivables",
}
SUMMARY_PATH = "/financeiro/settlements/summary"


def _authorized_user(request: Request):
    """Human principal + effective ``access`` — same chain as /viewer-context."""
    user = getattr(request.state, "user", None)
    if user is None:
        raise Exception("Unauthorized")
    if getattr(user, "principal_type", None) != "user":
        raise Exception("Forbidden")
    if getattr(user, "rbac_unavailable", False):
        raise Exception("Service Unavailable")
    if not has_permission(user, ACCESS_PERMISSION):
        raise Exception("Forbidden")
    return user


def _user_bearer(request: Request) -> str:
    bearer = request.headers.get("Authorization", "")
    if not bearer.startswith("Bearer "):
        raise Exception("Unauthorized")
    return bearer.split(" ", 1)[1]


def _error_data(exc: DelpiApiGatewayError) -> dict[str, Any] | None:
    """Preserve the upstream typed code so the MFE can distinguish RBAC
    denials (no code) from S2S credential/scope denials (``S2S_*``) and
    dataset-gate denials (``scope_unavailable``)."""
    if exc.error_code:
        return {"error": {"code": exc.error_code}}
    return None


def _map_gateway_error(exc: DelpiApiGatewayError, operation_id: str):
    """Typed passthrough — never turn an authorization failure into success."""
    if exc.error_code == "scope_unavailable":
        return fail(
            "Escopo de dados financeiros não autorizado.",
            403,
            data={"error": {"code": "scope_unavailable"}},
            operation_id=operation_id,
        )
    if exc.status_code == 401:
        return fail(
            "Não autorizado.", 401,
            data=_error_data(exc), operation_id=operation_id,
        )
    if exc.status_code == 403:
        return fail(
            "Acesso negado.", 403,
            data=_error_data(exc), operation_id=operation_id,
        )
    if exc.status_code == 400:
        return fail("Parâmetros inválidos.", 400, operation_id=operation_id)
    if exc.status_code == 409:
        return fail(
            "Relatório indisponível no estado atual.",
            409,
            data=_error_data(exc),
            operation_id=operation_id,
        )
    if exc.status_code is None or exc.status_code >= 500:
        return fail(
            "Origem de dados financeiros indisponível.",
            503,
            operation_id=operation_id,
        )
    return fail("Erro na origem de dados.", 502, operation_id=operation_id)


# Export workloads re-run the full engine and serialize the whole
# dataset — they legitimately exceed the interactive-read budget.
_EXPORT_TIMEOUT_SECONDS = 120.0


def _proxy_export(
    request: Request,
    *,
    upstream_path: str,
    params: dict[str, Any],
    operation_id: str,
):
    """Binary passthrough shared by the report exports — the producer
    owns serialization (metadata, SHA-256 hash, parity watermark); the
    BFF adds the ``access`` gate and relays bytes, disposition and the
    upstream media type verbatim."""
    _authorized_user(request)
    access_token = _user_bearer(request)
    try:
        content, content_disposition, content_type = (
            ApiDelpiSettlementsGateway().get_bytes(
                upstream_path,
                access_token=access_token,
                params=params,
                timeout_seconds=_EXPORT_TIMEOUT_SECONDS,
            )
        )
    except DelpiApiGatewayError as exc:
        return _map_gateway_error(exc, operation_id)
    headers = {}
    if content_disposition:
        headers["Content-Disposition"] = content_disposition
    return Response(
        content=content,
        media_type=content_type or "application/octet-stream",
        headers=headers,
    )


def _call_gateway(
    request: Request,
    *,
    path: str,
    params: dict[str, Any],
    operation_id: str,
):
    try:
        user = _authorized_user(request)
    except Exception:
        raise
    access_token = _user_bearer(request)
    _ = user  # principal already validated; subject stays in the delegated JWT
    try:
        body = ApiDelpiSettlementsGateway().get(
            path, access_token=access_token, params=params
        )
    except DelpiApiGatewayError as exc:
        return _map_gateway_error(exc, operation_id)
    if not isinstance(body, dict):
        return fail(
            "Resposta inesperada da origem de dados.", 502,
            operation_id=operation_id,
        )
    # api-delpi envelope: {success, message, data, meta} — unwrap data,
    # surface its status/quality verbatim (no fabricated totals).
    if body.get("success") is not True:
        return fail(
            body.get("message") or "Erro na origem de dados.",
            502,
            operation_id=operation_id,
        )
    return ok(
        body.get("data"),
        message=body.get("message") or "OK",
        operation_id=operation_id,
    )


@router.get(
    "/financial-settlements",
    operation_id="get_closing_financial_settlements",
)
def get_closing_financial_settlements(
    request: Request,
    side: str = Query(..., pattern="^(payable|receivable)$"),
    start_date: str = Query(...),
    end_date: str = Query(...),
    nature_code: str | None = Query(None),
    movement_type: str | None = Query(None),
    sort_by: str = Query("settlement_date"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    params: dict[str, Any] = {
        "start_date": start_date,
        "end_date": end_date,
        "sort_by": sort_by,
        "sort_dir": sort_dir,
        "page": page,
        "page_size": page_size,
    }
    if nature_code:
        params["nature_code"] = nature_code
    if movement_type:
        params["movement_type"] = movement_type
    return _call_gateway(
        request,
        path=_SIDE_TO_PATH[side],
        params=params,
        operation_id="get_closing_financial_settlements",
    )


@router.get(
    "/stock-inventory",
    operation_id="get_closing_stock_inventory",
)
def get_closing_stock_inventory(
    request: Request,
    period: str = Query(..., pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    branch: str = Query("all", pattern="^(all|01|02)$"),
    report_scope: str = Query(
        "all_products", pattern="^(all_products|mp_pi_pa)$"
    ),
    warehouse: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    params: dict[str, Any] = {
        "period": period,
        "branch": branch,
        "report_scope": report_scope,
        "page": page,
        "page_size": page_size,
    }
    if warehouse:
        params["warehouse"] = warehouse
    return _call_gateway(
        request,
        path="/financeiro/stock-inventory",
        params=params,
        operation_id="get_closing_stock_inventory",
    )


@router.get(
    "/stock-inventory/export",
    operation_id="export_closing_stock_inventory",
)
def export_closing_stock_inventory(
    request: Request,
    period: str = Query(..., pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    branch: str = Query("all", pattern="^(all|01|02)$"),
    report_scope: str = Query(
        "all_products", pattern="^(all_products|mp_pi_pa)$"
    ),
    warehouse: str | None = Query(None),
    export_format: str = Query("csv", alias="format", pattern="^(csv|pdf)$"),
):
    """Binary passthrough of the api-delpi P7 export (doc 119 §8.C) — the
    file (metadata header, SHA-256 hash, parity watermark) is produced by
    the data owner; the BFF adds the ``access`` gate, never a second
    serialization. ``access.dre`` never reaches this surface."""
    params: dict[str, Any] = {
        "period": period,
        "branch": branch,
        "report_scope": report_scope,
        "format": export_format,
    }
    if warehouse:
        params["warehouse"] = warehouse
    return _proxy_export(
        request,
        upstream_path="/financeiro/stock-inventory/export",
        params=params,
        operation_id="export_closing_stock_inventory",
    )


@router.get(
    "/financial-settlements/summary",
    operation_id="get_closing_financial_settlements_summary",
)
def get_closing_financial_settlements_summary(
    request: Request,
    start_date: str = Query(...),
    end_date: str = Query(...),
    nature_code: str | None = Query(None),
    movement_type: str | None = Query(None),
):
    params: dict[str, Any] = {
        "start_date": start_date,
        "end_date": end_date,
    }
    if nature_code:
        params["nature_code"] = nature_code
    if movement_type:
        params["movement_type"] = movement_type
    return _call_gateway(
        request,
        path=SUMMARY_PATH,
        params=params,
        operation_id="get_closing_financial_settlements_summary",
    )


@router.get(
    "/stock-movements",
    operation_id="get_closing_stock_movements",
)
def get_closing_stock_movements(
    request: Request,
    period: str = Query(..., pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    branch: str = Query("all", pattern="^(all|01|02)$"),
    report_scope: str = Query(
        "all_products", pattern="^(all_products|mp_pi_pa)$"
    ),
):
    """R05 Entradas e Saídas (MATR320 rule) — operational month query,
    independent of any open competence or document workflow."""
    return _call_gateway(
        request,
        path="/financeiro/stock-movements",
        params={
            "period": period,
            "branch": branch,
            "report_scope": report_scope,
        },
        operation_id="get_closing_stock_movements",
    )


@router.get(
    "/stock-movements/export",
    operation_id="export_closing_stock_movements",
)
def export_closing_stock_movements(
    request: Request,
    period: str = Query(..., pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    branch: str = Query("all", pattern="^(all|01|02)$"),
    report_scope: str = Query(
        "all_products", pattern="^(all_products|mp_pi_pa)$"
    ),
    export_format: str = Query("csv", alias="format", pattern="^(csv|pdf)$"),
):
    return _proxy_export(
        request,
        upstream_path="/financeiro/stock-movements/export",
        params={
            "period": period,
            "branch": branch,
            "report_scope": report_scope,
            "format": export_format,
        },
        operation_id="export_closing_stock_movements",
    )


@router.get(
    "/work-in-process",
    operation_id="get_closing_work_in_process",
)
def get_closing_work_in_process(
    request: Request,
    period: str = Query(..., pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    branch: str = Query("all", pattern="^(all|01|02)$"),
    report_scope: str = Query(
        "all_products", pattern="^(all_products|mp_pi_pa)$"
    ),
    warehouse: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """R08 Material em Processo (MATR989 rule) — standalone surface of
    the same engine the P7 report certifies; no document dependency."""
    params: dict[str, Any] = {
        "period": period,
        "branch": branch,
        "report_scope": report_scope,
        "page": page,
        "page_size": page_size,
    }
    if warehouse:
        params["warehouse"] = warehouse
    return _call_gateway(
        request,
        path="/financeiro/work-in-process",
        params=params,
        operation_id="get_closing_work_in_process",
    )


@router.get(
    "/work-in-process/export",
    operation_id="export_closing_work_in_process",
)
def export_closing_work_in_process(
    request: Request,
    period: str = Query(..., pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    branch: str = Query("all", pattern="^(all|01|02)$"),
    report_scope: str = Query(
        "all_products", pattern="^(all_products|mp_pi_pa)$"
    ),
    export_format: str = Query("csv", alias="format", pattern="^(csv|pdf)$"),
):
    return _proxy_export(
        request,
        upstream_path="/financeiro/work-in-process/export",
        params={
            "period": period,
            "branch": branch,
            "report_scope": report_scope,
            "format": export_format,
        },
        operation_id="export_closing_work_in_process",
    )


_ANALYTICS_SOURCES = {
    "entradasSaidas": "/financeiro/stock-movements",
    "p7": "/financeiro/stock-inventory",
    "h02": "/financeiro/work-in-process",
}


def _decimal_or_none(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _fetch_operand(gateway, *, path, params, access_token):
    """One analytical operand. Authorization failures propagate; data
    failures degrade to an explicit unavailable operand — a missing
    source is never silently reconciled as zero."""
    try:
        body = gateway.get(
            path, access_token=access_token, params=params
        )
    except DelpiApiGatewayError as exc:
        if exc.error_code == "scope_unavailable" or exc.status_code in (
            401,
            403,
        ):
            raise
        return {
            "available": False,
            "status": "UNAVAILABLE",
            "errorCode": exc.error_code,
            "value": None,
            "dataAsOf": None,
        }
    if not isinstance(body, dict) or body.get("success") is not True:
        return {
            "available": False,
            "status": "UNAVAILABLE",
            "errorCode": None,
            "value": None,
            "dataAsOf": None,
        }
    return body.get("data")


@router.get(
    "/analytics/stock-reconciliation",
    operation_id="get_closing_analytics_stock_reconciliation",
)
def get_closing_analytics_stock_reconciliation(
    request: Request,
    period: str = Query(..., pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    branch: str = Query("all", pattern="^(all|01|02)$"),
    report_scope: str = Query(
        "all_products", pattern="^(all_products|mp_pi_pa)$"
    ),
):
    """Analytical triple reconciliation (doc 15.1):

    ``DIVERGENCIA = ENTRADAS_SAIDAS − P7 − H02``

    Operand semantics — the only zero-capable composition, derived from
    the certified MATR320/MATR460/MATR989 measures (doc 84 §3–§5):

    - ``entradasSaidas`` = R05 ``totals.closingBalance`` — Saldo Atual
      over ALL warehouses (SB9 universe incl. loc 99);
    - ``p7`` = stock-inventory ``stockTotal`` — EM ESTOQUE (excl. the
      process warehouse);
    - ``h02`` = work-in-process ``physicalTotal`` — the sem-OP physical
      block of MATR989 (SB9 loc 99). The com-OP allocated parcel is NOT
      an operand: it is outside the stock equation and is exposed as a
      drill-down component instead — summing it would double-count.

    This is an analytical composition only: it never reads, writes or
    mutates the governed P3 ``closing_reconciliation`` projection, never
    converts an unavailable source into zero and never certifies parity
    — the governed workflow remains authoritative.
    """
    operation_id = "get_closing_analytics_stock_reconciliation"
    _authorized_user(request)
    access_token = _user_bearer(request)
    gateway = ApiDelpiSettlementsGateway()
    base_params = {
        "period": period,
        "branch": branch,
        "report_scope": report_scope,
    }

    try:
        movements = _fetch_operand(
            gateway,
            path=_ANALYTICS_SOURCES["entradasSaidas"],
            params=base_params,
            access_token=access_token,
        )
        inventory = _fetch_operand(
            gateway,
            path=_ANALYTICS_SOURCES["p7"],
            params={**base_params, "page": 1, "page_size": 1},
            access_token=access_token,
        )
        wip = _fetch_operand(
            gateway,
            path=_ANALYTICS_SOURCES["h02"],
            params={**base_params, "page": 1, "page_size": 1},
            access_token=access_token,
        )
    except DelpiApiGatewayError as exc:
        return _map_gateway_error(exc, operation_id)

    def _operand(data, *, value_getter):
        # Producer statuses arrive lowercase (``available``); canonical
        # operand statuses are uppercase (AVAILABLE/INCOMPLETE/...).
        status = str(data.get("status") or "").upper() or None
        value = value_getter(data)
        available = status == "AVAILABLE" and value is not None
        return {
            "available": available,
            "status": status,
            "errorCode": data.get("errorCode"),
            "value": value,
            "dataAsOf": data.get("dataAsOf"),
            "parityStatus": data.get("parityStatus"),
        }

    operand_es = _operand(
        movements,
        value_getter=lambda d: (d.get("totals") or {}).get(
            "closingBalance"
        ),
    )
    operand_p7 = _operand(
        inventory, value_getter=lambda d: d.get("stockTotal")
    )
    operand_h02 = _operand(
        wip, value_getter=lambda d: d.get("physicalTotal")
    )
    operands = {
        "entradasSaidas": operand_es,
        "p7": operand_p7,
        "h02": operand_h02,
    }

    ineligible = [
        name for name, op in operands.items() if not op["available"]
    ]
    eligible = not ineligible

    divergence: Decimal | None = None
    if eligible:
        divergence = (
            Decimal(str(operand_es["value"]))
            - Decimal(str(operand_p7["value"]))
            - Decimal(str(operand_h02["value"]))
        )

    divergence_cents = (
        divergence.quantize(Decimal("0.01"))
        if divergence is not None
        else None
    )
    parity = "NOT_COMPUTED"
    if divergence is not None:
        parity = (
            "EXACT_PARITY" if divergence_cents == Decimal("0.00")
            else "DIVERGENCE"
        )

    inv = inventory if isinstance(inventory, dict) else {}
    mov = movements if isinstance(movements, dict) else {}
    wipd = wip if isinstance(wip, dict) else {}
    mov_totals = mov.get("totals") or {}

    return ok(
        {
            "report": "stock-reconciliation",
            "kind": "analytical",
            "governedReconciliation": "not_persisted",
            "period": period,
            "branchCode": branch,
            "reportScope": report_scope,
            "equation": "entradasSaidas - p7 - h02",
            "operandSemantics": {
                "entradasSaidas": (
                    "R05 totals.closingBalance — Saldo Atual sobre "
                    "todos os armazéns (universo SB9 incl. 99)."
                ),
                "p7": (
                    "stock-inventory stockTotal — EM ESTOQUE (exclui "
                    "o armazém de processo)."
                ),
                "h02": (
                    "work-in-process physicalTotal — bloco físico "
                    "sem-OP do MATR989 (SB9 armazém 99)."
                ),
            },
            "eligibility": "ELIGIBLE" if eligible else "INELIGIBLE",
            "ineligibleOperands": ineligible,
            "operands": operands,
            "components": {
                "r05OpeningBalance": mov_totals.get("openingBalance"),
                "r05NetMovement": mov_totals.get("netMovement"),
                "p7ProcessPhysicalTotal": inv.get(
                    "processPhysicalTotal"
                ),
                "p7ProcessAllocatedTotal": inv.get(
                    "processAllocatedTotal"
                ),
                "p7ProcessTotal": inv.get("processTotal"),
                "p7GrandTotal": inv.get("grandTotal"),
                "p7HistoricalTotal": inv.get("historicalTotal"),
                "h02PhysicalTotal": wipd.get("physicalTotal"),
                "h02AllocatedTotal": wipd.get("allocatedTotal"),
                "h02GrandTotal": wipd.get("grandTotal"),
            },
            "divergence": (
                None
                if divergence is None
                else str(divergence.quantize(Decimal("0.000001")))
            ),
            "divergenceCents": (
                None if divergence_cents is None
                else str(divergence_cents)
            ),
            "parity": parity,
            "parityTolerance": "NONE",
            "provenance": {
                "period": period,
                "branch": branch,
                "reportScope": report_scope,
                "snapshotConvention": "month_end",
                "sources": {
                    "entradasSaidas": (
                        mov.get("provenance") or {}
                    ).get("engine"),
                    "p7": (inv.get("provenance") or {}).get("engine"),
                    "h02": (wipd.get("provenance") or {}).get(
                        "engine"
                    ),
                },
            },
            "parityNotes": [
                "Conciliação analítica — distinta da conciliação "
                "governada P3; não persiste registro nem valida "
                "fechamento.",
                "Paridade oficial dos relatórios permanece pendente de "
                "homologação por competência.",
            ],
        },
        message="Analytical stock reconciliation computed.",
        operation_id=operation_id,
    )
