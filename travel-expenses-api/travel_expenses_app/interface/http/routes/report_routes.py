from __future__ import annotations

from fastapi import APIRouter, File, Query, Request, UploadFile
from fastapi.responses import Response

from travel_expenses_app.application.use_cases.travel_report_service import (
    TravelReportError,
    TravelReportService,
)
from travel_expenses_app.core.responses import fail, ok
from travel_expenses_app.interface.http.deps import get_travel_report_service

router = APIRouter(tags=["Travel Expense Reports"])


def _service() -> TravelReportService:
    return get_travel_report_service()


def _handle(exc: Exception):
    if isinstance(exc, PermissionError):
        return fail(str(exc), 403)
    if isinstance(exc, TravelReportError):
        status = 404 if "não encontrada" in str(exc).lower() or "não encontrado" in str(exc).lower() else 400
        return fail(str(exc), status)
    raise exc


@router.get("/categories")
def list_categories():
    return ok(_service().list_categories())


@router.get("/reports")
def list_reports(
    request: Request,
    scope: str = Query(default="mine"),
    unit: str | None = Query(default=None),
    q: str | None = Query(default=None),
    periodFrom: str | None = Query(default=None),
    periodTo: str | None = Query(default=None),
):
    try:
        return ok(
            _service().list_reports(
                request.state.user,
                scope=scope,
                unit_code=unit,
                query=q,
                period_from=periodFrom,
                period_to=periodTo,
            )
        )
    except (PermissionError, TravelReportError) as exc:
        return _handle(exc)


@router.post("/reports")
async def create_report(request: Request):
    body = await request.json()
    try:
        return ok(_service().create(request.state.user, body), status_code=201)
    except (PermissionError, TravelReportError) as exc:
        return _handle(exc)


@router.get("/reports/{report_id}")
def get_report(request: Request, report_id: str):
    try:
        return ok(_service().get_detail(request.state.user, report_id))
    except (PermissionError, TravelReportError) as exc:
        return _handle(exc)


@router.patch("/reports/{report_id}")
async def update_report(request: Request, report_id: str):
    body = await request.json()
    try:
        return ok(_service().update(request.state.user, report_id, body))
    except (PermissionError, TravelReportError) as exc:
        return _handle(exc)


@router.delete("/reports/{report_id}")
def delete_report(request: Request, report_id: str):
    try:
        _service().delete(request.state.user, report_id)
        return ok({"deleted": True})
    except (PermissionError, TravelReportError) as exc:
        return _handle(exc)


@router.get("/reports/{report_id}/audit")
def list_audit(request: Request, report_id: str):
    try:
        return ok(_service().list_audit(request.state.user, report_id))
    except (PermissionError, TravelReportError) as exc:
        return _handle(exc)


@router.get("/reports/{report_id}/package.pdf")
def download_package(request: Request, report_id: str):
    try:
        content = _service().build_package_pdf(request.state.user, report_id)
    except (PermissionError, TravelReportError) as exc:
        return _handle(exc)
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="prestacao-{report_id}.pdf"'},
    )


@router.post("/reports/{report_id}/expenses")
async def add_expense(request: Request, report_id: str):
    body = await request.json()
    try:
        return ok(_service().add_expense(request.state.user, report_id, body), status_code=201)
    except (PermissionError, TravelReportError) as exc:
        return _handle(exc)


@router.patch("/reports/{report_id}/expenses/{expense_id}")
async def update_expense(request: Request, report_id: str, expense_id: str):
    body = await request.json()
    try:
        return ok(_service().update_expense(request.state.user, report_id, expense_id, body))
    except (PermissionError, TravelReportError) as exc:
        return _handle(exc)


@router.delete("/reports/{report_id}/expenses/{expense_id}")
def delete_expense(request: Request, report_id: str, expense_id: str):
    try:
        _service().delete_expense(request.state.user, report_id, expense_id)
        return ok({"deleted": True})
    except (PermissionError, TravelReportError) as exc:
        return _handle(exc)


@router.post("/reports/{report_id}/expenses/{expense_id}/receipts")
async def add_receipt(
    request: Request,
    report_id: str,
    expense_id: str,
    file: UploadFile = File(...),
):
    content = await file.read()
    try:
        return ok(
            _service().add_receipt(
                request.state.user,
                report_id,
                expense_id,
                original_name=file.filename or "cupom",
                mime_type=file.content_type,
                content=content,
            ),
            status_code=201,
        )
    except (PermissionError, TravelReportError) as exc:
        return _handle(exc)


@router.get("/reports/{report_id}/expenses/{expense_id}/receipts/{receipt_id}/file")
def get_receipt_file(request: Request, report_id: str, expense_id: str, receipt_id: str):
    try:
        receipt, path = _service().get_receipt_file(
            request.state.user, report_id, expense_id, receipt_id
        )
    except (PermissionError, TravelReportError) as exc:
        return _handle(exc)
    return Response(
        content=path.read_bytes(),
        media_type=receipt.get("mimeType") or "application/octet-stream",
        headers={
            "Content-Disposition": f'inline; filename="{receipt.get("originalName") or "cupom"}"'
        },
    )


@router.delete("/reports/{report_id}/expenses/{expense_id}/receipts/{receipt_id}")
def delete_receipt(request: Request, report_id: str, expense_id: str, receipt_id: str):
    try:
        _service().delete_receipt(request.state.user, report_id, expense_id, receipt_id)
        return ok({"deleted": True})
    except (PermissionError, TravelReportError) as exc:
        return _handle(exc)
