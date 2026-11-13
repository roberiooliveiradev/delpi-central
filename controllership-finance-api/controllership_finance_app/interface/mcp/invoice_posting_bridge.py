"""CLARA MCP bridge — LNF (invoice_posting) reads/analyze via BFF routes.

Paridade 1:1 com as rotas HTTP de ``invoice_posting``: o ContextVar
``delpi_auth`` (JWT do usuário final) já está estabelecido pelo
transporte MCP; as tools chamam as funções de rota decoradas, sem
reimplementar AuthZ/negócio. PDFs/XML não são entregues aqui — a
resposta aponta para a tela do app.
"""

from __future__ import annotations

import calendar
import inspect
import json
from datetime import date, datetime, timezone
from typing import Any
from uuid import UUID

from fastapi.params import Param
from mcp.types import CallToolResult
from pydantic_core import PydanticUndefined
from starlette.responses import Response

from controllership_finance_app.interface.http.routes.invoice_posting import (
    router as lnf_router,
)
from controllership_finance_app.interface.mcp.tool_bridge import (
    _error,
    _ok,
    _user_and_access,
    handle_tool_error,
)

_APP_BASE = "/apps/lancamento-notas-fiscais"


def _app_links(*, request_id: str | None = None) -> dict[str, str]:
    links = {
        "app_url": _APP_BASE,
        "pdf_xml_note": (
            "DANFE/PDF/XML: abra a solicitação no app LNF para baixar "
            "pelos botões existentes (a CLARA não entrega binários)."
        ),
    }
    if request_id:
        links["request_url"] = f"{_APP_BASE}?requestId={request_id}"
    return links


def _route_fail_status(result: Response) -> int:
    try:
        return int(result.status_code)
    except Exception:  # noqa: BLE001
        return 500


def _resolved_route_kwargs(fn, params: dict[str, Any]) -> dict[str, Any]:
    """Materializa defaults FastAPI ``Query``/``Param`` fora do framework.

    Chamada direta da função decorada deixa ``Query(None)`` como objeto
    truthy — ele vazaria para filtros/SQL (``cannot adapt type 'Query'``).
    """
    resolved = dict(params)
    try:
        signature = inspect.signature(fn)
    except (TypeError, ValueError):
        return resolved
    for name, param in signature.parameters.items():
        if name in resolved:
            continue
        default = param.default
        if default is inspect.Parameter.empty:
            continue
        if isinstance(default, Param):
            value = default.default
            resolved[name] = None if value is PydanticUndefined else value
        else:
            resolved[name] = default
    return resolved


def _call_lnf_route(fn, **params) -> CallToolResult:
    """Invoca rota LNF sem Request posicional (rotas usam ContextVar)."""
    _user_and_access()
    kwargs = _resolved_route_kwargs(fn, params)
    try:
        result = fn(**kwargs)
    except Exception as exc:  # noqa: BLE001 — literals canônicos authz
        msg = str(exc)
        if msg in ("Unauthorized", "Forbidden", "Service Unavailable"):
            raise PermissionError(msg) from exc
        raise
    if isinstance(result, Response):
        try:
            body = json.loads(result.body)
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError("route_response_not_json") from exc
        if isinstance(body, dict) and body.get("success") is False:
            data = body.get("data")
            err_code = None
            if isinstance(data, dict):
                err_code = (data.get("error") or {}).get("code")
            return _error(
                body.get("message") or "Erro na operação.",
                status_code=_route_fail_status(result),
                data=data if isinstance(data, dict) else {},
                error_code=err_code,
            )
        if isinstance(body, dict) and "data" in body:
            return _ok(
                body.get("data"),
                message=body.get("message") or "ok",
            )
        return _ok(body)
    return _ok(result)


def _as_uuid(request_id: str) -> UUID:
    return UUID(str(request_id))


def tool_list_invoice_postings(
    branch: str | None = None,
    status: str | None = None,
    supplier: str | None = None,
    document: str | None = None,
    issued_from: str | None = None,
    issued_to: str | None = None,
    received_from: str | None = None,
    received_to: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> CallToolResult:
    """Lista solicitações LNF (mesmos filtros da rota GET /requests)."""
    try:
        kwargs: dict[str, Any] = {}
        if branch is not None:
            kwargs["branch"] = branch
        if status is not None:
            kwargs["status"] = status
        if supplier is not None:
            kwargs["supplier"] = supplier
        if document is not None:
            kwargs["document"] = document
        if issued_from is not None:
            kwargs["issued_from"] = issued_from
        if issued_to is not None:
            kwargs["issued_to"] = issued_to
        if received_from is not None:
            kwargs["received_from"] = received_from
        if received_to is not None:
            kwargs["received_to"] = received_to
        if page is not None:
            kwargs["page"] = int(page)
        if page_size is not None:
            kwargs["page_size"] = int(page_size)
        result = _call_lnf_route(lnf_router.list_requests, **kwargs)
        if not result.is_error:
            payload = dict(getattr(result, "structured_content", None) or {})
            data = payload.get("data")
            if isinstance(data, dict):
                data = dict(data)
                data["app_links"] = _app_links()
                payload["data"] = data
                return _ok(data, message=payload.get("message") or "ok")
        return result
    except Exception as exc:
        return handle_tool_error(exc)


def tool_get_invoice_posting(request_id: str) -> CallToolResult:
    """Detalhe de uma solicitação LNF (+ deep link do app para PDF/XML)."""
    try:
        result = _call_lnf_route(
            lnf_router.get_request, request_id=_as_uuid(request_id)
        )
        if not result.is_error:
            payload = dict(getattr(result, "structured_content", None) or {})
            data = payload.get("data")
            if isinstance(data, dict):
                data = dict(data)
                data["app_links"] = _app_links(request_id=str(request_id))
                return _ok(data, message=payload.get("message") or "ok")
        return result
    except Exception as exc:
        return handle_tool_error(exc)


def tool_list_invoice_posting_purchase_orders(
    request_id: str,
) -> CallToolResult:
    """Pedidos de compra vinculados/candidatos da solicitação."""
    try:
        return _call_lnf_route(
            lnf_router.list_request_purchase_orders,
            request_id=_as_uuid(request_id),
        )
    except Exception as exc:
        return handle_tool_error(exc)


def tool_list_open_purchase_orders(
    branch: str,
    supplier_code: str,
    supplier_store: str,
) -> CallToolResult:
    """Pedidos de compra abertos no ERP (create)."""
    try:
        return _call_lnf_route(
            lnf_router.list_open_purchase_orders,
            branch=branch,
            supplier_code=supplier_code,
            supplier_store=supplier_store,
        )
    except Exception as exc:
        return handle_tool_error(exc)


def tool_list_received_invoices(
    invoice_number: str | None = None,
    supplier_cnpj: str | None = None,
    document_type: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> CallToolResult:
    """Notas recebidas (financial) candidatas a lançamento."""
    try:
        kwargs: dict[str, Any] = {}
        if invoice_number is not None:
            kwargs["invoice_number"] = invoice_number
        if supplier_cnpj is not None:
            kwargs["supplier_cnpj"] = supplier_cnpj
        if document_type is not None:
            kwargs["document_type"] = document_type
        if page is not None:
            kwargs["page"] = int(page)
        if page_size is not None:
            kwargs["page_size"] = int(page_size)
        result = _call_lnf_route(lnf_router.list_received_invoices, **kwargs)
        if not result.is_error:
            payload = dict(getattr(result, "structured_content", None) or {})
            data = payload.get("data")
            if isinstance(data, dict):
                data = dict(data)
                data["app_links"] = _app_links()
                return _ok(data, message=payload.get("message") or "ok")
        return result
    except Exception as exc:
        return handle_tool_error(exc)


def tool_received_invoice_detail(
    document_id: str,
    document_type: str | None = None,
    branch: str | None = None,
    file_id: str | None = None,
    access_key: str | None = None,
    provider_entity_id: str | None = None,
    supplier_code: str | None = None,
    supplier_store: str | None = None,
) -> CallToolResult:
    """Detalhe fiscal de nota recebida (+ link do app)."""
    try:
        kwargs: dict[str, Any] = {"document_id": str(document_id)}
        if document_type is not None:
            kwargs["document_type"] = document_type
        if branch is not None:
            kwargs["branch"] = branch
        if file_id is not None:
            kwargs["file_id"] = file_id
        if access_key is not None:
            kwargs["access_key"] = access_key
        if provider_entity_id is not None:
            kwargs["provider_entity_id"] = provider_entity_id
        if supplier_code is not None:
            kwargs["supplier_code"] = supplier_code
        if supplier_store is not None:
            kwargs["supplier_store"] = supplier_store
        result = _call_lnf_route(lnf_router.received_fiscal_detail, **kwargs)
        if not result.is_error:
            payload = dict(getattr(result, "structured_content", None) or {})
            data = payload.get("data")
            if isinstance(data, dict):
                data = dict(data)
                data["app_links"] = _app_links()
                return _ok(data, message=payload.get("message") or "ok")
        return result
    except Exception as exc:
        return handle_tool_error(exc)


def tool_list_unmapped_products(
    branch: str | None = None,
    supplier: str | None = None,
    product_code: str | None = None,
    mapping_status: str | None = None,
    request_id: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> CallToolResult:
    """Produtos de fornecedor sem código Delpi."""
    try:
        kwargs: dict[str, Any] = {}
        for key, value in (
            ("branch", branch),
            ("supplier", supplier),
            ("product_code", product_code),
            ("mapping_status", mapping_status),
            ("request_id", request_id),
        ):
            if value is not None:
                kwargs[key] = value
        if page is not None:
            kwargs["page"] = int(page)
        if page_size is not None:
            kwargs["page_size"] = int(page_size)
        return _call_lnf_route(lnf_router.list_unmapped_products, **kwargs)
    except Exception as exc:
        return handle_tool_error(exc)


def tool_search_suppliers(
    query: str,
    limit: int | None = None,
) -> CallToolResult:
    """Busca fornecedores Protheus para criação de solicitação."""
    try:
        kwargs: dict[str, Any] = {"query": query}
        if limit is not None:
            kwargs["limit"] = int(limit)
        return _call_lnf_route(lnf_router.search_suppliers, **kwargs)
    except Exception as exc:
        return handle_tool_error(exc)


def _parse_iso_date(raw: str | None) -> date | None:
    if not raw:
        return None
    text = str(raw).strip()[:10]
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _age_days(received_at: str | None, *, today: date) -> int | None:
    parsed = _parse_iso_date(received_at)
    if parsed is None:
        return None
    return max(0, (today - parsed).days)


def tool_analyze_invoice_posting_backlog(
    branch: str | None = None,
    period: str | None = None,
    page_size: int | None = None,
) -> CallToolResult:
    """Backlog LNF — FACT/RECOMMENDATION composto só de reads da BFF.

    Não acessa banco/SQL próprio. Ausência de fonte ≠ zero.
    """
    try:
        _user_and_access()
        today = datetime.now(timezone.utc).date()
        size = int(page_size or 100)
        list_kwargs: dict[str, Any] = {"page": 1, "page_size": size}
        if branch:
            list_kwargs["branch"] = branch
        if period:
            # competência YYYY-MM → recorte issued_from/to do mês
            year_month = str(period).strip()
            if len(year_month) >= 7:
                ym = year_month[:7]
                list_kwargs["issued_from"] = f"{ym}-01"
                try:
                    y, m = int(ym[:4]), int(ym[5:7])
                    last = calendar.monthrange(y, m)[1]
                    list_kwargs["issued_to"] = f"{y}-{m:02d}-{last:02d}"
                except ValueError:
                    pass

        pending = _call_lnf_route(
            lnf_router.list_requests, status="pending", **list_kwargs
        )
        blocked = _call_lnf_route(
            lnf_router.list_requests, status="blocked", **list_kwargs
        )
        in_progress = _call_lnf_route(
            lnf_router.list_requests, status="in_progress", **list_kwargs
        )

        def _items(result: CallToolResult) -> tuple[list, dict | None]:
            if result.is_error:
                return [], {
                    "error": True,
                    "payload": getattr(result, "structured_content", None),
                }
            payload = dict(getattr(result, "structured_content", None) or {})
            data = payload.get("data")
            if not isinstance(data, dict):
                return [], {"error": True, "payload": payload}
            items = data.get("items") or data.get("requests") or []
            if not isinstance(items, list):
                items = []
            return items, {
                "total": data.get("total"),
                "page": data.get("page"),
                "source": "GET /lancamento-notas-fiscais/requests",
            }

        pending_items, pending_meta = _items(pending)
        blocked_items, blocked_meta = _items(blocked)
        progress_items, progress_meta = _items(in_progress)

        by_branch: dict[str, int] = {}
        ages: list[int] = []
        block_reasons: dict[str, int] = {}
        for item in pending_items + blocked_items + progress_items:
            if not isinstance(item, dict):
                continue
            b = str(item.get("branch_code") or item.get("branch") or "?")
            by_branch[b] = by_branch.get(b, 0) + 1
            age = _age_days(
                item.get("received_at") or item.get("receivedAt"),
                today=today,
            )
            if age is not None:
                ages.append(age)
            reason = item.get("block_reason") or item.get("blockReason")
            if reason:
                key = str(reason)
                block_reasons[key] = block_reasons.get(key, 0) + 1

        findings: list[dict[str, Any]] = []
        if pending_meta and not pending_meta.get("error"):
            findings.append(
                {
                    "kind": "FACT",
                    "code": "pending_count",
                    "message": (
                        f"{pending_meta.get('total')} solicitações "
                        "pendentes (fonte: list status=pending)."
                    ),
                    "value": pending_meta.get("total"),
                    "source": pending_meta.get("source"),
                }
            )
        else:
            findings.append(
                {
                    "kind": "FACT",
                    "code": "pending_unavailable",
                    "message": (
                        "Contagem de pendentes indisponível — ausência "
                        "de fonte ≠ zero."
                    ),
                    "value": None,
                    "source": None,
                }
            )

        if blocked_meta and not blocked_meta.get("error"):
            findings.append(
                {
                    "kind": "FACT",
                    "code": "blocked_count",
                    "message": (
                        f"{blocked_meta.get('total')} solicitações "
                        "bloqueadas."
                    ),
                    "value": blocked_meta.get("total"),
                    "source": blocked_meta.get("source"),
                    "by_reason": block_reasons or None,
                }
            )

        if by_branch:
            findings.append(
                {
                    "kind": "FACT",
                    "code": "open_by_branch",
                    "message": "Distribuição do recorte aberto por filial.",
                    "value": by_branch,
                    "source": "composição dos reads list",
                }
            )

        if ages:
            findings.append(
                {
                    "kind": "FACT",
                    "code": "age_since_received",
                    "message": (
                        f"Idade desde o recebimento no recorte: "
                        f"mín={min(ages)}d mediana="
                        f"{sorted(ages)[len(ages)//2]}d máx={max(ages)}d."
                    ),
                    "value": {
                        "min": min(ages),
                        "median": sorted(ages)[len(ages) // 2],
                        "max": max(ages),
                        "sample_size": len(ages),
                    },
                    "source": "received_at dos items listados",
                }
            )
            if max(ages) >= 5:
                findings.append(
                    {
                        "kind": "RECOMMENDATION",
                        "code": "review_aged_pending",
                        "message": (
                            "Há solicitações com ≥5 dias desde o "
                            "recebimento — priorize no app LNF "
                            "(não lançar/validar por inferência)."
                        ),
                        "value": max(ages),
                    }
                )

        findings.append(
            {
                "kind": "RECOMMENDATION",
                "code": "use_app_for_pdf_xml",
                "message": (
                    "Para DANFE/PDF/XML e lançamento no ERP, use a tela "
                    "do app; a CLARA não baixa binários nem escreve no "
                    "Protheus."
                ),
                "app_links": _app_links(),
            }
        )

        return _ok(
            {
                "analysis_type": "invoice_posting_backlog",
                "filters": {
                    "branch": branch,
                    "period": period,
                    "page_size": size,
                },
                "sources": {
                    "pending": pending_meta,
                    "blocked": blocked_meta,
                    "in_progress": progress_meta,
                },
                "findings": findings,
                "app_links": _app_links(),
                "invariants": [
                    "somente reads da BFF",
                    "ausência de fonte ≠ zero",
                    "nunca validar/lançar por inferência",
                ],
            },
            message="Backlog LNF analisado a partir dos reads da BFF.",
        )
    except Exception as exc:
        return handle_tool_error(exc)
