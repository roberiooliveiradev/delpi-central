"""CLARA — tool bridge (paridade 1:1 com a BFF).

Cada tool reconstrói a Request a partir do contexto delpi_auth
estabelecido pelo transport gate (`delpi_mcp.identity`) e reaplica o
MESMO gate de autorização das rotas (`authorized_user` /
`has_permission(manage)`). Nenhuma regra de negócio aqui — os
repositórios canônicos respondem por estado, escopo e erros tipados.

Paridade READ (classe A): as tools de consulta invocam as próprias
funções de rota do Portal com a Request reconstruída — mesmo gate,
mesmo bearer delegado ao api-delpi, mesmo envelope e erros tipados.
O bridge só adapta transporte; nunca reimplementa contrato.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import logging
from typing import Any

from starlette.requests import Request
from starlette.responses import Response
from mcp.types import CallToolResult

from delpi_auth.authz_core import has_permission
from delpi_mcp.errors import mcp_tool_result
from delpi_mcp.identity import (
    build_mcp_request as _shared_build_request,
    require_mcp_context,
)

from controllership_finance_app.domain.closing_checklist.errors import (
    ChecklistDomainError,
)
from controllership_finance_app.application.clara.agent_intelligence_service import (  # noqa: E501
    ClaraAgentIntelligenceService,
)
from controllership_finance_app.application.clara.batch_orchestrator import (
    ClaraBatchOrchestrator,
)
from controllership_finance_app.application.clara.governed_writes import (
    ClaraGovernedWrites,
)
from controllership_finance_app.application.services.closing_document_service import (
    ClosingDocumentService,
)
from controllership_finance_app.infrastructure.persistence.clara_knowledge_repository import (
    ClaraKnowledgeRepository,
)
from controllership_finance_app.infrastructure.persistence.closing_checklist_repository import (
    ClosingChecklistRepository,
)
from controllership_finance_app.infrastructure.persistence.closing_p3_repository import (
    ClosingP3Repository,
)
from controllership_finance_app.infrastructure.persistence.closing_package_repository import (
    ClosingPackageRepository,
)
from controllership_finance_app.infrastructure.persistence.closing_pendency_repository import (
    ClosingPendencyRepository,
)
from controllership_finance_app.interface.http.authz import (
    ACCESS_PERMISSION,
    DRE_ACCESS_PERMISSION,
    MANAGE_PERMISSION,
    authorized_user,
    actor_subject,
)
from controllership_finance_app.interface.http.routes import (
    admin_catalogs_routes,
    admin_checklist_routes,
    closing_routes,
    competences_routes,
    documents_routes,
    me_routes,
    p3_routes,
    packages_routes,
    participants_routes,
    pendencies_routes,
    received_documents_routes,
    reports_routes,
    validations_routes,
)
from controllership_finance_app.interface.mcp.constants import TOOL_CLASS
from controllership_finance_app.interface.mcp.oauth_contract import (
    mcp_www_authenticate_meta,
)

logger = logging.getLogger(__name__)

_ERROR_KIND_BY_CODE = {
    "unauthenticated": "auth",
    "forbidden": "authz",
    "not_found": "not_found",
    "conflict": "conflict",
    "business_rule": "business_rule",
    "proposal_required": "proposal_required",
    "proposal_not_found": "proposal_not_found",
    "proposal_expired": "proposal_expired",
    "proposal_stale": "proposal_stale",
    "proposal_actor_mismatch": "proposal_mismatch",
    "outcome_verification_failed": "outcome_verification_failed",
    "persistence_unavailable": "upstream",
    "internal": "internal",
}


def build_mcp_request() -> Request:
    """Reconstrói a Request do adaptador a partir do contexto delpi_auth."""
    context = require_mcp_context()
    return _shared_build_request(
        context=context,
        server=("controllership-finance-api", 443),
        client=("127.0.0.1", 0),
    )


def _ok(data: Any, message: str = "ok") -> CallToolResult:
    return mcp_tool_result(
        {"success": True, "message": message, "data": data},
        is_error=False,
    )


def _error(
    message: str,
    *,
    status_code: int = 400,
    data: dict | None = None,
    error_code: str | None = None,
) -> CallToolResult:
    err_data = dict(data or {})
    if error_code:
        err_data.setdefault("error_code", error_code)
        err_data.setdefault(
            "error_kind",
            _ERROR_KIND_BY_CODE.get(error_code, "client"),
        )
    meta = None
    if status_code == 401:
        meta = mcp_www_authenticate_meta(
            error="invalid_token",
            error_description="Authentication required",
        )
    return mcp_tool_result(
        {
            "success": False,
            "message": message,
            "data": err_data,
            "status_code": status_code,
        },
        is_error=True,
        meta=meta,
    )


def _domain_fail(exc: ChecklistDomainError) -> CallToolResult:
    code = getattr(exc, "code", "business_rule")
    status = getattr(exc, "status", 400)
    return _error(
        str(exc) or code,
        status_code=status,
        data={"error": {"code": code}},
        error_code=code,
    )


def handle_tool_error(exc: Exception) -> CallToolResult:
    if isinstance(exc, ChecklistDomainError):
        return _domain_fail(exc)
    if isinstance(exc, PermissionError):
        msg = str(exc) or "Unauthorized"
        if msg == "Unauthorized":
            return _error(
                "Authentication required.",
                status_code=401,
                error_code="unauthenticated",
            )
        return _error(msg, status_code=403, error_code="forbidden")
    logger.exception("clara_tool_error type=%s", type(exc).__name__)
    return _error(
        "Erro interno da CLARA.",
        status_code=500,
        error_code="internal",
    )


def _user_and_access():
    """Mesmo gate das rotas: request reconstruída + authorized_user."""
    request = build_mcp_request()
    try:
        user = authorized_user(request)
    except Exception as exc:  # noqa: BLE001 — literals canônicos do middleware
        msg = str(exc)
        if msg == "Unauthorized":
            raise PermissionError("Unauthorized") from exc
        if msg == "Service Unavailable":
            raise PermissionError("Service Unavailable") from exc
        raise PermissionError(msg or "Forbidden") from exc
    return request, user


def _is_manage(user) -> bool:
    return bool(
        getattr(user, "is_superadmin", False)
        or has_permission(user, MANAGE_PERMISSION)
    )


def _mcp_identity() -> dict:
    """Identidade efetiva para os gates do catálogo governado.

    Reconstroi a Request e resolve as permissions no Core a cada
    chamada — PREPARE e ACT sempre leem a autorização vigente."""
    request = build_mcp_request()
    try:
        user = authorized_user(request)
    except Exception as exc:  # noqa: BLE001 — literals canônicos
        msg = str(exc)
        if msg == "Unauthorized":
            raise PermissionError("Unauthorized") from exc
        if msg == "Service Unavailable":
            raise PermissionError("Service Unavailable") from exc
        raise PermissionError(msg or "Forbidden") from exc
    return {
        "subject": actor_subject(user),
        "name": getattr(user, "name", None)
        or getattr(user, "email", None),
        "is_manage": _is_manage(user),
        "is_dre": bool(
            has_permission(user, DRE_ACCESS_PERMISSION)
        ),
    }


def _governed_writes() -> ClaraGovernedWrites:
    return ClaraGovernedWrites(identity_provider=_mcp_identity)


def _batch_orchestrator() -> ClaraBatchOrchestrator:
    return ClaraBatchOrchestrator(writes=_governed_writes())


# -- READ / DISCOVERY -----------------------------------------------------


def tool_get_my_context() -> CallToolResult:
    request, user = _user_and_access()
    permissions = getattr(user, "permissions", None) or []
    groups = getattr(user, "groups", None) or []
    return _ok(
        {
            "subject": actor_subject(user),
            "display_name": getattr(user, "name", None)
            or getattr(user, "email", None),
            "capabilities": {
                "access": has_permission(user, ACCESS_PERMISSION),
                "manage": _is_manage(user),
            },
            "groups": list(groups),
            "permissions": list(permissions),
            "note": (
                "Contexto de identidade — nunca autorização adicional; "
                "as regras efetivas permanecem no backend."
            ),
        }
    )


def tool_get_catalog() -> CallToolResult:
    request, user = _user_and_access()
    managed = _is_manage(user)
    governed = _governed_writes().capabilities()
    tools = []
    for name, kind in TOOL_CLASS.items():
        if kind == "PREPARE" or (
            kind == "ACT" and name != "commit_proposal"
        ):
            continue
        tools.append({"name": name, "class": kind})
    return _ok(
        {
            "tools": tools,
            "capabilities": {
                "access": True,
                "manage": managed,
            },
            "governed_operations": governed,
            "knowledge": {
                "corpus": _safe_corpus_version(),
            },
            "agent_directives": (
                ClaraAgentIntelligenceService.agent_directives()
            ),
        }
    )


def _safe_corpus_version() -> dict | None:
    try:
        version = ClaraKnowledgeRepository().current_corpus_version()
    except Exception:  # noqa: BLE001
        return None
    if version is None:
        return None
    return {
        "corpus_version_id": str(version["corpus_version_id"]),
        "published_at": str(version["published_at"]),
        "item_count": version["item_count"],
        "source_count": version["source_count"],
    }


def tool_get_competence_state(period: str) -> CallToolResult:
    request, _user = _user_and_access()
    try:
        state = ClosingPackageRepository().derive_closing_state(period)
    except ChecklistDomainError as exc:
        return _domain_fail(exc)
    return _ok(state)


def tool_get_checklist_items(
    period: str,
    sheet: str | None = None,
    recipient_area: str | None = None,
    state: str | None = None,
) -> CallToolResult:
    request, _user = _user_and_access()
    try:
        items = ClosingChecklistRepository().list_competence_items(
            period,
            sheet=sheet,
            recipient_area=recipient_area,
            state=state,
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc)
    return _ok({"items": items})


def tool_list_documents(
    period: str,
    snapshot_item_id: str | None = None,
    state: str | None = None,
    branch_scope: str | None = None,
) -> CallToolResult:
    request, _user = _user_and_access()
    try:
        result = ClosingDocumentService().list_documents(
            period=period,
            snapshot_item_id=snapshot_item_id,
            link_kind=None,
            state=state,
            branch_scope=branch_scope,
            limit=50,
            offset=0,
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc)
    return _ok(result)


def tool_get_p3_reconciliation(period: str) -> CallToolResult:
    request, _user = _user_and_access()
    try:
        state = ClosingP3Repository().get_p3_state(period)
    except ChecklistDomainError as exc:
        return _domain_fail(exc)
    return _ok(state)


def tool_list_pendencies(
    period: str,
    state: str | None = None,
    kind: str | None = None,
) -> CallToolResult:
    request, _user = _user_and_access()
    try:
        result = ClosingPendencyRepository().list_pendencies(
            period,
            state=state,
            kind=kind,
            request_scope="BOTH",
            limit=50,
            offset=0,
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc)
    return _ok(result)


def tool_get_package_review(period: str) -> CallToolResult:
    request, user = _user_and_access()
    viewer = actor_subject(user)
    is_manage = _is_manage(user)
    try:
        result = ClosingPackageRepository().list_packages(
            period, viewer=viewer, is_manage=is_manage
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc)
    return _ok(result)


# -- PARIDADE READ com rotas do Portal (classe A) ----------------------------
# `_call_route` invoca a MESMA função de rota que o Portal chama —
# gate, envelope e erros tipados ficam idênticos por construção.
# Rotas devolvem `ok()/fail()` (JSONResponse) ou dict/list direto;
# exceções de authz ("Unauthorized"/"Forbidden"/"Service Unavailable")
# seguem o literal canônico do middleware → PermissionError → 401/403/503.


def _route_fail_status(result: Response) -> int:
    status = getattr(result, "status_code", 500)
    try:
        return int(status)
    except (TypeError, ValueError):
        return 500


def _call_route(fn, request: Request, **params) -> CallToolResult:
    try:
        result = fn(request, **params)
    except Exception as exc:  # noqa: BLE001 — literals canônicos authz
        msg = str(exc)
        if msg in ("Unauthorized", "Forbidden", "Service Unavailable"):
            raise PermissionError(msg) from exc
        raise
    if inspect.isawaitable(result):
        result = asyncio.run(result)
    if isinstance(result, Response):
        try:
            body = json.loads(result.body)
        except Exception as exc:  # noqa: BLE001 — resposta não-JSON
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


def tool_list_competences() -> CallToolResult:
    request, _user = _user_and_access()
    return _call_route(
        competences_routes.list_closing_competences, request
    )


def tool_get_competence(period: str) -> CallToolResult:
    request, _user = _user_and_access()
    return _call_route(
        competences_routes.get_closing_competence,
        request,
        period=period,
    )


def tool_get_checklist_item(period: str, item_key: str) -> CallToolResult:
    request, _user = _user_and_access()
    return _call_route(
        competences_routes.get_closing_competence_item,
        request,
        period=period,
        item_key=item_key,
    )


def tool_get_closing_cockpit(period: str) -> CallToolResult:
    request, _user = _user_and_access()
    return _call_route(
        packages_routes.get_closing_cockpit, request, period=period
    )


def tool_list_my_tasks(period: str | None = None) -> CallToolResult:
    request, _user = _user_and_access()
    return _call_route(
        me_routes.list_my_tasks, request, period=period
    )


def tool_get_pendency(
    period: str,
    pendency_id: str,
    include_history: bool = True,
    branch_scope: str | None = None,
) -> CallToolResult:
    request, _user = _user_and_access()
    detail = _call_route(
        pendencies_routes.get_closing_pendency,
        request,
        period=period,
        pendency_id=pendency_id,
        branch_scope=branch_scope,
    )
    if detail.is_error or not include_history:
        return detail
    history = _call_route(
        pendencies_routes.list_pendency_history,
        request,
        period=period,
        pendency_id=pendency_id,
        branch_scope=branch_scope,
    )
    if history.is_error:
        return history
    return _merge_route_results(
        detail, history, merged_key="history"
    )


def _merge_route_results(
    base: CallToolResult,
    extra: CallToolResult,
    *,
    merged_key: str,
) -> CallToolResult:
    """Junta o `data` de duas respostas de rota (detail + coleção)."""
    try:
        base_payload = json.loads(base.content[0].text)
        extra_payload = json.loads(extra.content[0].text)
    except Exception:  # noqa: BLE001 — payload canônico do bridge
        return base
    data = dict(base_payload.get("data") or {})
    data[merged_key] = extra_payload.get("data")
    return _ok(data)


def tool_get_package(period: str, package_id: str) -> CallToolResult:
    request, _user = _user_and_access()
    return _call_route(
        packages_routes.get_closing_package,
        request,
        period=period,
        package_id=package_id,
    )


def tool_get_document(
    period: str,
    document_id: str,
    branch_scope: str | None = None,
    include_audit: bool = False,
) -> CallToolResult:
    """Detalhe + versões + mensagens + solicitações de ajuste —
    mesma visão do painel «Documentos e interações»."""
    request, _user = _user_and_access()
    detail = _call_route(
        documents_routes.get_competence_document,
        request,
        period=period,
        document_id=document_id,
        branch_scope=branch_scope,
    )
    if detail.is_error:
        return detail
    parts = [("versions", documents_routes.list_document_versions)]
    parts.append(("messages", documents_routes.list_document_messages))
    parts.append(
        ("adjustment_requests",
         documents_routes.list_document_adjustment_requests)
    )
    if include_audit:
        parts.append(("audit", documents_routes.list_document_audit))
    merged = detail
    for key, fn in parts:
        extra = _call_route(
            fn,
            request,
            period=period,
            document_id=document_id,
            branch_scope=branch_scope,
        )
        if extra.is_error:
            return extra
        merged = _merge_route_results(merged, extra, merged_key=key)
    return merged


def tool_get_item_validation(
    period: str, item_key: str, branch_scope: str | None = None
) -> CallToolResult:
    request, _user = _user_and_access()
    detail = _call_route(
        validations_routes.get_item_validation,
        request,
        period=period,
        item_key=item_key,
        branch_scope=branch_scope,
    )
    if detail.is_error:
        return detail
    corrections = _call_route(
        validations_routes.list_item_corrections,
        request,
        period=period,
        item_key=item_key,
        branch_scope=branch_scope,
    )
    if corrections.is_error:
        return corrections
    return _merge_route_results(
        detail, corrections, merged_key="corrections"
    )


def tool_list_p3_events(period: str) -> CallToolResult:
    request, _user = _user_and_access()
    return _call_route(
        p3_routes.list_p3_events, request, period=period
    )


def tool_lookup_participants(
    period: str,
    document_id: str,
    ids: list[str],
    branch_scope: str | None = None,
) -> CallToolResult:
    request, _user = _user_and_access()
    return _call_route(
        participants_routes.lookup_participants,
        request,
        body=participants_routes.ParticipantLookupBody(ids=list(ids)),
        period=period,
        document_id=document_id,
        branch_scope=branch_scope,
    )


def tool_get_financial_settlements(
    side: str,
    start_date: str,
    end_date: str,
    nature_code: str | None = None,
    movement_type: str | None = None,
    sort_by: str = "settlement_date",
    sort_dir: str = "desc",
    page: int = 1,
    page_size: int = 50,
) -> CallToolResult:
    """R01/R02 — mesma rota Portal; sort/filtro/paginação delegados."""
    request, _user = _user_and_access()
    return _call_route(
        closing_routes.get_closing_financial_settlements,
        request,
        side=side,
        start_date=start_date,
        end_date=end_date,
        nature_code=nature_code,
        movement_type=movement_type,
        sort_by=sort_by,
        sort_dir=sort_dir,
        page=page,
        page_size=page_size,
    )


def tool_get_financial_settlements_summary(
    start_date: str,
    end_date: str,
    nature_code: str | None = None,
    movement_type: str | None = None,
) -> CallToolResult:
    request, _user = _user_and_access()
    return _call_route(
        closing_routes.get_closing_financial_settlements_summary,
        request,
        start_date=start_date,
        end_date=end_date,
        nature_code=nature_code,
        movement_type=movement_type,
    )


def tool_get_stock_inventory(
    period: str,
    branch: str = "all",
    report_scope: str = "all_products",
    warehouse: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> CallToolResult:
    """R03/P7 — consulta operacional (paridade oficial PENDING)."""
    request, _user = _user_and_access()
    return _call_route(
        closing_routes.get_closing_stock_inventory,
        request,
        period=period,
        branch=branch,
        report_scope=report_scope,
        warehouse=warehouse,
        page=page,
        page_size=page_size,
    )


def tool_get_stock_movements(
    period: str,
    branch: str = "all",
    report_scope: str = "all_products",
) -> CallToolResult:
    """R05 — entradas e saídas do mês (MATR320 rule)."""
    request, _user = _user_and_access()
    return _call_route(
        closing_routes.get_closing_stock_movements,
        request,
        period=period,
        branch=branch,
        report_scope=report_scope,
    )


def tool_get_work_in_process(
    period: str,
    branch: str = "all",
    report_scope: str = "all_products",
    warehouse: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> CallToolResult:
    """R08/H02 — material em processo (MATR989 rule)."""
    request, _user = _user_and_access()
    return _call_route(
        closing_routes.get_closing_work_in_process,
        request,
        period=period,
        branch=branch,
        report_scope=report_scope,
        warehouse=warehouse,
        page=page,
        page_size=page_size,
    )


def tool_get_stock_reconciliation(
    period: str,
    branch: str = "all",
    report_scope: str = "all_products",
) -> CallToolResult:
    """Conciliação analítica R05−P7−H02 — IDENTITY_ONLY/INCONCLUSIVE
    preservados; nunca oficial parity."""
    request, _user = _user_and_access()
    return _call_route(
        closing_routes.get_closing_analytics_stock_reconciliation,
        request,
        period=period,
        branch=branch,
        report_scope=report_scope,
    )


def tool_get_stock_kardex(
    period: str,
    branch: str = "all",
    warehouse: str | None = None,
    product_code: str | None = None,
    movement_kind: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> CallToolResult:
    """R06 Kardex — motor MATR910 (SD1/SD2/SD3 + SB9 anterior + custo
    as-of TTAT). Mesma rota do Portal; paridade oficial PENDING."""
    request, _user = _user_and_access()
    return _call_route(
        closing_routes.get_closing_stock_kardex,
        request,
        period=period,
        branch=branch,
        warehouse=warehouse,
        product_code=product_code,
        product_type=None,
        movement_kind=movement_kind,
        page=page,
        page_size=page_size,
        sort="date",
        sort_dir="asc",
    )


def tool_get_stock_kardex_summary(
    period: str,
    branch: str = "all",
    warehouse: str | None = None,
    product_code: str | None = None,
) -> CallToolResult:
    """R06 — resumo do kardex por tipo/armazém + top produtos por custo."""
    request, _user = _user_and_access()
    return _call_route(
        closing_routes.get_closing_stock_kardex_summary,
        request,
        period=period,
        branch=branch,
        warehouse=warehouse,
        product_code=product_code,
        product_type=None,
    )


def tool_get_inventory_adjustments(
    period: str,
    branch: str = "all",
    warehouse: str | None = None,
    product_code: str | None = None,
    movement_kind: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> CallToolResult:
    """R07 ajustes de inventário — recorte INVENT do motor MATR910
    (TES 499/DE0 positivos, 999/RE0 negativos). READ — nenhum ajuste
    é executado no ERP."""
    request, _user = _user_and_access()
    return _call_route(
        closing_routes.get_closing_inventory_adjustments,
        request,
        period=period,
        branch=branch,
        warehouse=warehouse,
        product_code=product_code,
        movement_kind=movement_kind,
        page=page,
        page_size=page_size,
    )


def tool_get_inventory_adjustments_summary(
    period: str,
    branch: str = "all",
    warehouse: str | None = None,
    product_code: str | None = None,
) -> CallToolResult:
    """R07 — resumo dos ajustes por tipo/armazém + top produtos."""
    request, _user = _user_and_access()
    return _call_route(
        closing_routes.get_closing_inventory_adjustments_summary,
        request,
        period=period,
        branch=branch,
        warehouse=warehouse,
        product_code=product_code,
    )


def tool_get_cpv(
    period: str,
    branch: str = "all",
    top_limit: int = 10,
) -> CallToolResult:
    """CPV gerencial (D-O1) — medida viva SD2/CFOP com custo corrente;
    NÃO é o total de saídas do kardex e não deve ser reconciliado a ele."""
    request, _user = _user_and_access()
    return _call_route(
        closing_routes.get_closing_cpv,
        request,
        period=period,
        branch=branch,
        top_limit=top_limit,
    )


def tool_get_cost_center_expenses(
    period: str,
    branch: str = "all",
    universe: str = "calculation",
    view: str = "all",
    cost_center: str | None = None,
    product_code: str | None = None,
    document: str | None = None,
    supplier_code: str | None = None,
    tes: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> CallToolResult:
    """R10 Despesas por Centro de Custo — mesma rota governada do
    Portal (eixo D1_DTDIGIT). ``universe`` separa a apuração histórica
    das linhas investigativas; findings são POSSIBLE_DIVERGENCE, nunca
    erro confirmado. Correção é atividade humana externa no Protheus."""
    request, _user = _user_and_access()
    return _call_route(
        closing_routes.get_closing_cost_center_expenses,
        request,
        period=period,
        branch=branch,
        universe=universe,
        view=view,
        cost_center=cost_center,
        product_code=product_code,
        document=document,
        supplier_code=supplier_code,
        tes=tes,
        include_findings=True,
        page=page,
        page_size=page_size,
        sort="date",
        sort_dir="asc",
    )


def tool_get_report_matrix(
    period: str, branch_scope: str | None = None
) -> CallToolResult:
    request, _user = _user_and_access()
    return _call_route(
        reports_routes.list_report_matrix,
        request,
        period=period,
        branch_scope=branch_scope,
    )


def tool_list_closing_catalogs() -> CallToolResult:
    request, _user = _user_and_access()
    return _call_route(
        admin_catalogs_routes.list_closing_catalogs, request
    )


def tool_list_catalog_entries(
    catalog_key: str, include_inactive: bool = True
) -> CallToolResult:
    request, _user = _user_and_access()
    return _call_route(
        admin_catalogs_routes.list_closing_catalog_entries,
        request,
        catalog_key=catalog_key,
        include_inactive=include_inactive,
    )


def tool_list_checklist_templates() -> CallToolResult:
    request, _user = _user_and_access()
    return _call_route(
        admin_checklist_routes.list_checklist_templates, request
    )


def tool_get_checklist_template_version(
    template_id: str, version: int
) -> CallToolResult:
    request, _user = _user_and_access()
    return _call_route(
        admin_checklist_routes.get_checklist_template_version,
        request,
        template_id=template_id,
        version=version,
    )


def tool_list_received_deliveries() -> CallToolResult:
    request, _user = _user_and_access()
    return _call_route(
        received_documents_routes.list_received_deliveries, request
    )


def tool_get_received_delivery(period: str) -> CallToolResult:
    request, _user = _user_and_access()
    return _call_route(
        received_documents_routes.get_received_delivery,
        request,
        period=period,
    )


def tool_get_received_document(
    period: str, document_id: str
) -> CallToolResult:
    request, _user = _user_and_access()
    detail = _call_route(
        received_documents_routes.get_received_document,
        request,
        period=period,
        document_id=document_id,
    )
    if detail.is_error:
        return detail
    for key, fn in (
        ("messages",
         received_documents_routes.list_received_document_messages),
        ("adjustment_requests",
         received_documents_routes.list_received_adjustment_requests),
    ):
        params = {"period": period, "document_id": document_id}
        if fn is received_documents_routes.list_received_document_messages:
            params.update({"limit": 100, "offset": 0})
        extra = _call_route(fn, request, **params)
        if extra.is_error:
            return extra
        detail = _merge_route_results(detail, extra, merged_key=key)
    return detail


# -- ANALYSIS ---------------------------------------------------------------


def tool_analyze_closing_blockers(period: str) -> CallToolResult:
    """Lê o estado real e devolve análise estruturada — cada achado é
    rotulado FACT (dado do owner) ou RECOMMENDATION (orientação)."""
    request, _user = _user_and_access()
    packages_repo = ClosingPackageRepository()
    try:
        state = packages_repo.derive_closing_state(period)
        p3 = ClosingP3Repository().get_p3_state(period)
        pendencies = ClosingPendencyRepository().list_pendencies(
            period, request_scope="BOTH", limit=100, offset=0
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc)
    findings: list[dict] = []
    for blocker in state.get("blocking_reasons") or []:
        findings.append(
            {
                "kind": "FACT",
                "source": "derive_closing_state",
                "summary": f"Bloqueio vigente: {blocker}",
            }
        )
    if (state.get("terminal_rejection") or {}).get("state") == "ACTIVE":
        findings.append(
            {
                "kind": "FACT",
                "source": "derive_closing_state",
                "summary": (
                    "Rejeição terminal ATIVA — ações de revisão estão "
                    "congeladas até reversão autorizada por coordenador."
                ),
            }
        )
        findings.append(
            {
                "kind": "RECOMMENDATION",
                "source": "clara",
                "summary": (
                    "Solicite ao coordenador elegível a reversão da "
                    "rejeição terminal com motivo registrado, se o "
                    "fechamento deva prosseguir."
                ),
            }
        )
    p3_blockers = (p3 or {}).get("blockers") or []
    for blocker in p3_blockers:
        findings.append(
            {
                "kind": "FACT",
                "source": "get_p3_state",
                "summary": f"P3: {blocker}",
            }
        )
    open_pendencies = (pendencies or {}).get("items") or []
    open_count = sum(
        1 for p in open_pendencies if p.get("state") not in (
            "RESOLVED", "CANCELLED"
        )
    )
    if open_count:
        findings.append(
            {
                "kind": "FACT",
                "source": "list_pendencies",
                "summary": (
                    f"{open_count} pendência(s) abertas na competência."
                ),
            }
        )
        findings.append(
            {
                "kind": "RECOMMENDATION",
                "source": "clara",
                "summary": (
                    "Resolva ou justifique formalmente as pendências "
                    "antes da conclusão mensal."
                ),
            }
        )
    if not findings:
        findings.append(
            {
                "kind": "FACT",
                "source": "clara",
                "summary": (
                    "Nenhum bloqueio vigente identificado nas fontes "
                    "consultadas."
                ),
            }
        )
    return _ok(
        {
            "period": period,
            "monthly_state": state.get("state")
            or state.get("status"),
            "findings": findings,
            "note": (
                "FACT = dado entregue pelo owner; RECOMMENDATION = "
                "orientação da CLARA, nunca regra nova."
            ),
        }
    )


# -- KNOWLEDGE ---------------------------------------------------------------


def _access_scope_for(user) -> str:
    return "PORTAL_MANAGE" if _is_manage(user) else "PORTAL_ACCESS"


def tool_search_closing_knowledge(
    query: str | None = None,
    topic: str | None = None,
    business_step: str | None = None,
    report_id: str | None = None,
    limit: int = 8,
) -> CallToolResult:
    request, user = _user_and_access()
    try:
        items = ClaraKnowledgeRepository().search(
            query=query,
            topic=topic,
            business_step=business_step,
            report_id=report_id,
            access_scope=_access_scope_for(user),
            limit=limit,
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc)
    return _ok(
        {
            "items": [
                {
                    "knowledge_id": str(i["knowledge_id"]),
                    "title": i["title"],
                    "topic": i["topic"],
                    "business_step": i["business_step"],
                    "related_report_ids": i["related_report_ids"],
                    "evidence_classification": i[
                        "evidence_classification"
                    ],
                    "origin_authority": i["origin_authority"],
                    "citation_locator": i["citation_locator"],
                    "excerpt": (i["content"] or "")[:600],
                    "rank": i.get("rank"),
                }
                for i in items
            ],
            "count": len(items),
            "corpus": _safe_corpus_version(),
        }
    )


def tool_get_knowledge_item(knowledge_id: str) -> CallToolResult:
    request, user = _user_and_access()
    try:
        item = ClaraKnowledgeRepository().get_item(
            knowledge_id, access_scope=_access_scope_for(user)
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc)
    return _ok(
        {
            "knowledge_id": str(item["knowledge_id"]),
            "title": item["title"],
            "content": item["content"],
            "topic": item["topic"],
            "business_step": item["business_step"],
            "related_report_ids": item["related_report_ids"],
            "evidence_classification": item["evidence_classification"],
            "origin_authority": item["origin_authority"],
            "citation_locator": item["citation_locator"],
            "source": {
                "source_id": item["source_id"],
                "name": item["source_name"],
                "type": item["source_type"],
                "version": item["source_version"],
                "hash": item["source_hash"],
            },
            "last_verified_at": str(item["last_verified_at"]),
            "status": item["status"],
        }
    )


def tool_list_knowledge_sources() -> CallToolResult:
    request, user = _user_and_access()
    try:
        sources = ClaraKnowledgeRepository().list_sources(
            access_scope=_access_scope_for(user)
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc)
    return _ok(
        {
            "sources": [
                {
                    "source_id": s["source_id"],
                    "source_type": s["source_type"],
                    "name": s["name"],
                    "source_version": s["source_version"],
                    "source_hash": s["source_hash"],
                    "origin_authority": s["origin_authority"],
                    "item_count": s["item_count"],
                }
                for s in sources
            ],
            "corpus": _safe_corpus_version(),
        }
    )


# -- PREPARE / ACT -------------------------------------------------------------


def tool_prepare_governed_operation(
    capability: str, params: dict
) -> CallToolResult:
    request, user = _user_and_access()
    try:
        proposal = _governed_writes().prepare(
            capability=capability,
            params=dict(params or {}),
            actor_sub=actor_subject(user),
            user_groups=getattr(user, "groups", []) or [],
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc)
    return _ok(proposal)


def tool_commit_proposal(
    proposal_handle: str, resume: bool = False
) -> CallToolResult:
    request, user = _user_and_access()
    try:
        result = _governed_writes().commit(
            handle=proposal_handle,
            actor_sub=actor_subject(user),
            user_groups=getattr(user, "groups", []) or [],
            resume=resume,
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc)
    return _ok(result)


def tool_prepare_batch(operations: list) -> CallToolResult:
    request, user = _user_and_access()
    try:
        result = _batch_orchestrator().prepare_batch(
            operations=list(operations or []),
            actor_sub=actor_subject(user),
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc)
    return _ok(result)


def tool_confirm_batch(
    batch_handle: str,
    plan_hash: str,
    attestation: dict | None = None,
) -> CallToolResult:
    request, user = _user_and_access()
    try:
        result = _batch_orchestrator().confirm_batch(
            handle=batch_handle,
            actor_sub=actor_subject(user),
            plan_hash=plan_hash,
            attestation=attestation,
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc)
    return _ok(result)


def tool_execute_batch(
    batch_handle: str, resume: bool = False
) -> CallToolResult:
    request, user = _user_and_access()
    try:
        result = _batch_orchestrator().execute_batch(
            handle=batch_handle,
            resume=resume,
            actor_sub=actor_subject(user),
            user_groups=getattr(user, "groups", []) or [],
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc)
    return _ok(result)


def tool_get_batch_status(batch_id: str) -> CallToolResult:
    request, user = _user_and_access()
    try:
        result = _batch_orchestrator().batch_status(
            batch_id=batch_id,
            actor_sub=actor_subject(user),
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc)
    return _ok(result)


__all__ = [
    "build_mcp_request",
    "handle_tool_error",
    "tool_analyze_closing_blockers",
    "tool_commit_proposal",
    "tool_confirm_batch",
    "tool_execute_batch",
    "tool_get_batch_status",
    "tool_prepare_batch",
    "tool_get_catalog",
    "tool_get_checklist_item",
    "tool_get_checklist_items",
    "tool_get_checklist_template_version",
    "tool_get_closing_cockpit",
    "tool_get_competence",
    "tool_get_competence_state",
    "tool_get_document",
    "tool_get_financial_settlements",
    "tool_get_financial_settlements_summary",
    "tool_get_item_validation",
    "tool_get_knowledge_item",
    "tool_get_my_context",
    "tool_get_p3_reconciliation",
    "tool_get_package",
    "tool_get_package_review",
    "tool_get_pendency",
    "tool_get_received_delivery",
    "tool_get_received_document",
    "tool_get_report_matrix",
    "tool_get_stock_inventory",
    "tool_get_stock_movements",
    "tool_get_stock_reconciliation",
    "tool_get_stock_kardex",
    "tool_get_stock_kardex_summary",
    "tool_get_inventory_adjustments",
    "tool_get_inventory_adjustments_summary",
    "tool_get_cpv",
    "tool_get_work_in_process",
    "tool_list_catalog_entries",
    "tool_list_checklist_templates",
    "tool_list_closing_catalogs",
    "tool_list_competences",
    "tool_list_documents",
    "tool_list_knowledge_sources",
    "tool_list_my_tasks",
    "tool_list_p3_events",
    "tool_list_pendencies",
    "tool_list_received_deliveries",
    "tool_lookup_participants",
    "tool_prepare_governed_operation",
    "tool_search_closing_knowledge",
]
