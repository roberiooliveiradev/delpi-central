"""CLARA — tool bridge (paridade 1:1 com a BFF).

Cada tool reconstrói a Request a partir do contexto delpi_auth
estabelecido pelo transport gate (`delpi_mcp.identity`) e reaplica o
MESMO gate de autorização das rotas (`authorized_user` /
`has_permission(manage)`). Nenhuma regra de negócio aqui — os
repositórios canônicos respondem por estado, escopo e erros tipados.
"""

from __future__ import annotations

import logging
from typing import Any

from starlette.requests import Request
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
    MANAGE_PERMISSION,
    authorized_user,
    actor_subject,
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
    governed = ClaraGovernedWrites().capabilities()
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
            "agent_directives": {
                "read_first": (
                    "Responda estado operacional somente com resultado "
                    "de tool READ — nunca de memória."
                ),
                "citations": (
                    "Conhecimento retornado traz citation_locator e "
                    "evidence_classification — apresente ambos."
                ),
                "confirmation": (
                    "Toda ACT exige proposal_handle de PREPARE + "
                    "confirmação humana explícita da operação exata."
                ),
            },
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
        proposal = ClaraGovernedWrites().prepare(
            capability=capability,
            params=dict(params or {}),
            actor_sub=actor_subject(user),
            user_groups=getattr(user, "groups", []) or [],
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc)
    return _ok(proposal)


def tool_commit_proposal(proposal_handle: str) -> CallToolResult:
    request, user = _user_and_access()
    try:
        result = ClaraGovernedWrites().commit(
            handle=proposal_handle,
            actor_sub=actor_subject(user),
            user_groups=getattr(user, "groups", []) or [],
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc)
    return _ok(result)


def tool_prepare_batch(operations: list) -> CallToolResult:
    request, user = _user_and_access()
    try:
        result = ClaraBatchOrchestrator().prepare_batch(
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
        result = ClaraBatchOrchestrator().confirm_batch(
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
        result = ClaraBatchOrchestrator().execute_batch(
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
        result = ClaraBatchOrchestrator().batch_status(
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
    "tool_get_checklist_items",
    "tool_get_competence_state",
    "tool_get_knowledge_item",
    "tool_get_my_context",
    "tool_get_p3_reconciliation",
    "tool_get_package_review",
    "tool_list_documents",
    "tool_list_knowledge_sources",
    "tool_list_pendencies",
    "tool_prepare_governed_operation",
    "tool_search_closing_knowledge",
]
