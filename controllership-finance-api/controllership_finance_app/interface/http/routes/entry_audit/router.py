"""Rotas /entry-audit. O gate é controllership-finance.access; manage herda."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel

from controllership_finance_app.application.entry_audit.errors import EntryAuditError
from controllership_finance_app.application.entry_audit.request_bearer import remember_bearer
from controllership_finance_app.core.responses import fail, ok
from controllership_finance_app.infrastructure.entry_audit.xlsx_export import build_workbook
from controllership_finance_app.interface.http.authz import (
    ACCESS_PERMISSION,
    MANAGE_PERMISSION,
    _human_user,
)
from delpi_auth.authz_core import has_any_permission

router = APIRouter(prefix="/entry-audit", tags=["Entry Audit"])


class AnalysisBody(BaseModel):
    date_from: date
    date_to: date
    document_types: list[str] | None = None
    branches: list[str] | None = None


class RerunBody(BaseModel):
    branches: list[str] | None = None


def get_entry_audit_service():
    from controllership_finance_app.application.entry_audit.composer import build_entry_audit_service

    return build_entry_audit_service()


def _actor(request: Request):
    try:
        user = _human_user(request)
    except Exception as exc:
        message = str(exc)
        status = {"Unauthorized": 401, "Forbidden": 403, "Service Unavailable": 503}.get(message)
        if status is None:
            raise
        return fail(message, status)
    if not has_any_permission(user, (ACCESS_PERMISSION, MANAGE_PERMISSION)):
        return fail("Forbidden", 403)
    return user


def _service(request: Request):
    override = getattr(request.app.state, "entry_audit_service", None)
    return override or get_entry_audit_service()


def _call(action):
    try:
        return action()
    except EntryAuditError as exc:
        return fail(str(exc), exc.status_code, {"code": exc.code})


def _filters(request: Request) -> dict:
    return {
        "branch": request.query_params.get("branch"),
        "severity": request.query_params.get("severity"),
        "theme": request.query_params.get("theme"),
        "supplier": request.query_params.get("supplier"),
        "tes": request.query_params.get("tes"),
        "document_type": request.query_params.get("document_type"),
        "day": request.query_params.get("day"),
        "status": request.query_params.get("status"),
        "q": request.query_params.get("q"),
    }


def _created(request: Request, payload: dict, operation_id: str = "create_entry_audit_analysis"):
    header = request.headers.get("authorization") or ""
    token = header[7:].strip() if header.lower().startswith("bearer ") else ""
    remember_bearer(str(payload.get("id") or ""), token)
    return ok(payload, status_code=202, operation_id=operation_id)


def _with_branches(response, payload: dict, operation_id: str):
    unavailable = payload.pop("branches_unavailable", [])
    return ok(payload, operation_id=operation_id, meta={"branches_unavailable": unavailable})


@router.post("/analyses", operation_id="create_entry_audit_analysis")
def create_analysis(body: AnalysisBody, request: Request):
    user = _actor(request)
    if not hasattr(user, "principal_type"):
        return user
    return _call(lambda: _created(request, _service(request).create(
            date_from=body.date_from,
            date_to=body.date_to,
            document_types=body.document_types,
            branches=body.branches,
            user_id=str(getattr(user, "id", "") or ""),
            user_name=str(getattr(user, "name", "") or ""),
            via="user",
        )))


@router.get("/analyses/options", operation_id="list_entry_audit_options")
def list_options(request: Request):
    user = _actor(request)
    if not hasattr(user, "principal_type"):
        return user
    return _call(lambda: ok(_service(request).options(), operation_id="list_entry_audit_options"))


@router.get("/analyses", operation_id="list_entry_audit_analyses")
def list_analyses(
    request: Request,
    date_from: date | None = None,
    date_to: date | None = None,
    branch: str | None = None,
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
):
    user = _actor(request)
    if not hasattr(user, "principal_type"):
        return user
    return _call(lambda: ok(
        _service(request).list_analyses(date_from=date_from, date_to=date_to, branch=branch, status=status, page=page, page_size=page_size),
        operation_id="list_entry_audit_analyses",
    ))


@router.get("/analyses/{analysis_id}", operation_id="get_entry_audit_analysis")
def get_analysis(analysis_id: str, request: Request):
    user = _actor(request)
    if not hasattr(user, "principal_type"):
        return user
    return _call(lambda: ok(_service(request).get_analysis(analysis_id), operation_id="get_entry_audit_analysis"))


@router.post("/analyses/{analysis_id}/rerun", operation_id="rerun_entry_audit_analysis")
def rerun_analysis(analysis_id: str, request: Request, body: RerunBody | None = None):
    user = _actor(request)
    if not hasattr(user, "principal_type"):
        return user
    branches = body.branches if body else None
    return _call(lambda: _created(request, _service(request).rerun(analysis_id, branches), operation_id="rerun_entry_audit_analysis"))


@router.get("/analyses/{analysis_id}/summary", operation_id="get_entry_audit_summary")
def get_summary(analysis_id: str, request: Request):
    user = _actor(request)
    if not hasattr(user, "principal_type"):
        return user
    return _call(lambda: _with_branches(None, _service(request).summary(analysis_id, _filters(request)), "get_entry_audit_summary"))


@router.get("/analyses/{analysis_id}/daily", operation_id="get_entry_audit_daily")
def get_daily(analysis_id: str, request: Request):
    user = _actor(request)
    if not hasattr(user, "principal_type"):
        return user
    return _call(lambda: _with_branches(None, _service(request).daily(analysis_id, _filters(request)), "get_entry_audit_daily"))


@router.get("/analyses/{analysis_id}/breakdowns", operation_id="get_entry_audit_breakdowns")
def get_breakdowns(analysis_id: str, request: Request):
    user = _actor(request)
    if not hasattr(user, "principal_type"):
        return user
    return _call(lambda: _with_branches(None, _service(request).breakdowns(analysis_id, _filters(request)), "get_entry_audit_breakdowns"))


@router.get("/analyses/{analysis_id}/facets", operation_id="get_entry_audit_facets")
def get_facets(analysis_id: str, request: Request):
    user = _actor(request)
    if not hasattr(user, "principal_type"):
        return user
    return _call(lambda: _with_branches(None, _service(request).facets(analysis_id, _filters(request)), "get_entry_audit_facets"))


@router.get("/trend", operation_id="get_entry_audit_trend")
def get_trend(request: Request, branch: str | None = None, date_from: date | None = None, date_to: date | None = None):
    user = _actor(request)
    if not hasattr(user, "principal_type"):
        return user
    return _call(lambda: ok(_service(request).trend(branch=branch, date_from=date_from, date_to=date_to), operation_id="get_entry_audit_trend"))


@router.get("/analyses/{analysis_id}/occurrences", operation_id="list_entry_audit_occurrences")
def list_occurrences(analysis_id: str, request: Request, page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200), sort: str = "severity"):
    user = _actor(request)
    if not hasattr(user, "principal_type"):
        return user
    return _call(lambda: _with_branches(None, _service(request).occurrences(analysis_id, _filters(request), page=page, page_size=page_size, sort=sort), "list_entry_audit_occurrences"))


@router.get("/analyses/{analysis_id}/occurrences/{stable_key}", operation_id="get_entry_audit_occurrence")
def get_occurrence(analysis_id: str, stable_key: str, request: Request):
    user = _actor(request)
    if not hasattr(user, "principal_type"):
        return user
    return _call(lambda: ok(_service(request).occurrence(analysis_id, stable_key), operation_id="get_entry_audit_occurrence"))


@router.get("/analyses/{analysis_id}/documents", operation_id="list_entry_audit_documents")
def list_documents(analysis_id: str, request: Request, page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200)):
    user = _actor(request)
    if not hasattr(user, "principal_type"):
        return user
    return _call(lambda: _with_branches(None, _service(request).documents(analysis_id, _filters(request), page=page, page_size=page_size), "list_entry_audit_documents"))


@router.get("/analyses/{analysis_id}/unmatched", operation_id="list_entry_audit_unmatched")
def list_unmatched(analysis_id: str, request: Request, page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200)):
    user = _actor(request)
    if not hasattr(user, "principal_type"):
        return user
    return _call(lambda: _with_branches(None, _service(request).unmatched_documents(analysis_id, _filters(request), page=page, page_size=page_size), "list_entry_audit_unmatched"))


@router.get("/analyses/{analysis_id}/cte", operation_id="list_entry_audit_cte")
def list_cte(analysis_id: str, request: Request, page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200)):
    user = _actor(request)
    if not hasattr(user, "principal_type"):
        return user
    return _call(lambda: _with_branches(None, _service(request).ctes(analysis_id, _filters(request), page=page, page_size=page_size), "list_entry_audit_cte"))


@router.get("/analyses/{analysis_id}/tes", operation_id="list_entry_audit_tes_used")
def list_tes(analysis_id: str, request: Request):
    user = _actor(request)
    if not hasattr(user, "principal_type"):
        return user
    return _call(lambda: _with_branches(None, _service(request).tes_used(analysis_id, _filters(request)), "list_entry_audit_tes_used"))


@router.post("/occurrences/{stable_key}/resolve", operation_id="resolve_entry_audit_occurrence")
@router.post("/unmatched/{stable_key}/resolve", operation_id="resolve_entry_audit_unmatched")
def resolve_occurrence(stable_key: str, request: Request):
    user = _actor(request)
    if not hasattr(user, "principal_type"):
        return user
    kind = "unmatched" if "/unmatched/" in request.url.path else "occurrence"
    return _call(lambda: ok(_service(request).resolve(stable_key, kind=kind, user_id=str(getattr(user, "id", "") or ""), user_name=str(getattr(user, "name", "") or "")), operation_id="resolve_entry_audit_occurrence"))


@router.post("/occurrences/{stable_key}/reopen", operation_id="reopen_entry_audit_occurrence")
@router.post("/unmatched/{stable_key}/reopen", operation_id="reopen_entry_audit_unmatched")
def reopen_occurrence(stable_key: str, request: Request):
    user = _actor(request)
    if not hasattr(user, "principal_type"):
        return user
    kind = "unmatched" if "/unmatched/" in request.url.path else "occurrence"
    return _call(lambda: ok(_service(request).reopen(stable_key, kind=kind, user_id=str(getattr(user, "id", "") or ""), user_name=str(getattr(user, "name", "") or "")), operation_id="reopen_entry_audit_occurrence"))


@router.get("/analyses/{analysis_id}/export", operation_id="export_entry_audit_analysis")
def export_analysis(analysis_id: str, request: Request):
    user = _actor(request)
    if not hasattr(user, "principal_type"):
        return user

    def _build():
        payload = _service(request).export_rows(analysis_id)
        content = build_workbook(payload)
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="entry-audit-{analysis_id}.xlsx"'},
        )

    return _call(_build)
