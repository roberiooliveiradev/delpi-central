"""Relatórios metalográficos — coleção em /engineering/metallographic-reports."""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, File, Header, Query, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field

from delpi_auth.authorization import require_permission
from delpi_auth.request_context import get_current_user

from app.application.security.api_delpi_permissions import (
    METALOGRAPHY_CREATE,
    METALOGRAPHY_DELETE,
    METALOGRAPHY_EDIT,
    METALOGRAPHY_EXPORT,
    METALOGRAPHY_VIEW,
)
from app.application.services.engineering.metallographic_report_service import (
    MetallographicReportService,
)
from app.core.responses import error_response
from app.domain.engineering.metallographic_report import (
    MetallographicReportError,
    etag_for,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginsRepositoryError,
    PluginsSchemaOutdatedError,
)
from app.interface.http.openapi_agent_metadata import (
    METALLOGRAPHIC_REPORT_COPY,
    METALLOGRAPHIC_REPORT_CREATE,
    METALLOGRAPHIC_REPORT_DELETE,
    METALLOGRAPHIC_REPORT_DELETE_IMAGE,
    METALLOGRAPHIC_REPORT_EXPORT_PDF,
    METALLOGRAPHIC_REPORT_GET,
    METALLOGRAPHIC_REPORT_GET_IMAGE,
    METALLOGRAPHIC_REPORT_LIST,
    METALLOGRAPHIC_REPORT_PUT_IMAGE,
    METALLOGRAPHIC_REPORT_UPDATE,
)
from app.interface.http.pagination_query import PAGE_SIZE_QUERY
from app.interface.http.query_param_enums import (
    METALLOGRAPHIC_CONCLUSION_QUERY,
    METALLOGRAPHIC_SORT_QUERY,
)
from app.interface.http.route_response_helpers import api_delpi_success
from app.utils.logger import log_error

router = APIRouter(prefix="/metallographic-reports", tags=["Engenharia — Metalografia"])


class MetallographicMeasurementBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    criterion: str | None = None
    measured: str | None = None


class MetallographicMeasurementsBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    crimp_height_ch: MetallographicMeasurementBody | None = None
    crimp_width_cb: MetallographicMeasurementBody | None = None
    void_area_av: MetallographicMeasurementBody | None = None
    left_burr_gh_e: MetallographicMeasurementBody | None = None
    right_burr_gh_d: MetallographicMeasurementBody | None = None


class MetallographicSampleBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    terminal_code: str | None = None
    terminal_part_number: str | None = None
    product_harness: str | None = None
    cable: str | None = None
    conductor_section: str | None = None
    applicator_tool: str | None = None
    press_equipment: str | None = None
    batch_production_order: str | None = None
    sample_identification: str | None = None


class MetallographicConclusionBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    result: str | None = Field(default=None, pattern="^(conforming|nonconforming)$")
    notes: str | None = None


class MetallographicAnalystBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = None


class MetallographicReportWriteBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    report_date: str | None = None
    revision: str | None = None
    sample: MetallographicSampleBody | None = None
    measurements: MetallographicMeasurementsBody | None = None
    conclusion: MetallographicConclusionBody | None = None
    analyst: MetallographicAnalystBody | None = None
    status: str | None = Field(default=None, pattern="^draft$")


def _service() -> MetallographicReportService:
    return MetallographicReportService()


def _actor() -> str:
    user = get_current_user()
    subject = str(getattr(user, "id", "") or "").strip()
    if not subject:
        subject = str(getattr(user, "email", "") or "").strip()
    return subject[:120] or "unknown"


def _json(data: dict[str, Any], *, operation_id: str, message: str, version: int | None = None):
    response = api_delpi_success(data, operation_id=operation_id, message=message)
    if version is not None:
        response.headers["ETag"] = etag_for(version)
    return response


def _failure(exc: Exception):
    if isinstance(exc, MetallographicReportError):
        return error_response(exc.message, status_code=exc.status_code, code=exc.code, recoverable=exc.status_code < 500)
    if isinstance(exc, PluginsSchemaOutdatedError):
        log_error(f"metallographic_report schema_outdated outcome=error")
        return error_response(
            "Persistência de relatórios indisponível.",
            status_code=503,
            code="SCHEMA_OUTDATED",
            recoverable=True,
        )
    if isinstance(exc, PluginsRepositoryError):
        log_error("metallographic_report persistence outcome=error")
        return error_response(
            "Falha ao persistir o relatório.",
            status_code=500,
            code="PERSISTENCE_ERROR",
            recoverable=True,
        )
    log_error("metallographic_report unexpected outcome=error")
    return error_response(
        "Erro interno ao processar o relatório metalográfico.",
        status_code=500,
        code="INTERNAL_ERROR",
        recoverable=False,
    )


@router.post("", **METALLOGRAPHIC_REPORT_CREATE)
@require_permission(METALOGRAPHY_CREATE)
def create_metallographic_report(
    body: MetallographicReportWriteBody,
    idempotency_key: Annotated[str | None, Header()] = None,
):
    try:
        report = _service().create(
            actor=_actor(),
            idempotency_key=idempotency_key,
            payload=body.model_dump(exclude_unset=False),
        )
        return _json(
            report,
            operation_id="engineering_create_metallographic_report",
            message="Relatório metalográfico criado.",
            version=report["version"],
        )
    except Exception as exc:
        return _failure(exc)


@router.get("", **METALLOGRAPHIC_REPORT_LIST)
@require_permission(METALOGRAPHY_VIEW)
def list_metallographic_reports(
    page: int = Query(1, ge=1),
    page_size: int = PAGE_SIZE_QUERY("page_20_100"),
    sort: str = METALLOGRAPHIC_SORT_QUERY(),
    report_date_from: str | None = Query(None, pattern=r"^(\d{4}-\d{2}-\d{2})?$"),
    report_date_to: str | None = Query(None, pattern=r"^(\d{4}-\d{2}-\d{2})?$"),
    report_number: str | None = Query(None, max_length=240),
    terminal_code: str | None = Query(None, max_length=240),
    terminal_part_number: str | None = Query(None, max_length=240),
    product_harness: str | None = Query(None, max_length=240),
    cable: str | None = Query(None, max_length=240),
    conductor_section: str | None = Query(None, max_length=240),
    applicator_tool: str | None = Query(None, max_length=240),
    press_equipment: str | None = Query(None, max_length=240),
    batch_production_order: str | None = Query(None, max_length=240),
    sample_identification: str | None = Query(None, max_length=240),
    conclusion_result: str | None = METALLOGRAPHIC_CONCLUSION_QUERY(),
):
    try:
        data = _service().list_reports(
            page=page,
            page_size=page_size,
            sort=sort,
            filters={
                "report_date_from": report_date_from,
                "report_date_to": report_date_to,
                "report_number": report_number,
                "terminal_code": terminal_code,
                "terminal_part_number": terminal_part_number,
                "product_harness": product_harness,
                "cable": cable,
                "conductor_section": conductor_section,
                "applicator_tool": applicator_tool,
                "press_equipment": press_equipment,
                "batch_production_order": batch_production_order,
                "sample_identification": sample_identification,
                "conclusion_result": conclusion_result,
            },
        )
        return api_delpi_success(
            data,
            operation_id="engineering_list_metallographic_reports",
            message="Relatórios metalográficos listados.",
        )
    except Exception as exc:
        return _failure(exc)


@router.get("/{report_id}", **METALLOGRAPHIC_REPORT_GET)
@require_permission(METALOGRAPHY_VIEW)
def get_metallographic_report(report_id: UUID):
    try:
        report = _service().get(str(report_id))
        return _json(
            report,
            operation_id="engineering_get_metallographic_report",
            message="Relatório metalográfico encontrado.",
            version=report["version"],
        )
    except Exception as exc:
        return _failure(exc)


@router.patch("/{report_id}", **METALLOGRAPHIC_REPORT_UPDATE)
@require_permission(METALOGRAPHY_EDIT)
def update_metallographic_report(
    report_id: UUID,
    body: MetallographicReportWriteBody,
    if_match: Annotated[str | None, Header()] = None,
):
    try:
        report = _service().update(
            actor=_actor(),
            report_id=str(report_id),
            if_match=if_match,
            payload=body.model_dump(exclude_unset=True),
        )
        return _json(
            report,
            operation_id="engineering_update_metallographic_report",
            message="Relatório metalográfico atualizado.",
            version=report["version"],
        )
    except Exception as exc:
        return _failure(exc)


@router.delete("/{report_id}", **METALLOGRAPHIC_REPORT_DELETE)
@require_permission(METALOGRAPHY_DELETE)
def delete_metallographic_report(
    report_id: UUID,
    if_match: Annotated[str | None, Header()] = None,
):
    try:
        deleted = _service().delete(
            actor=_actor(),
            report_id=str(report_id),
            if_match=if_match,
        )
        return api_delpi_success(
            deleted,
            operation_id="engineering_delete_metallographic_report",
            message="Relatório metalográfico excluído.",
        )
    except Exception as exc:
        return _failure(exc)


@router.post("/{report_id}/copies", **METALLOGRAPHIC_REPORT_COPY)
@require_permission(METALOGRAPHY_CREATE)
def copy_metallographic_report(
    report_id: UUID,
    idempotency_key: Annotated[str | None, Header()] = None,
):
    try:
        report = _service().copy(
            actor=_actor(),
            report_id=str(report_id),
            idempotency_key=idempotency_key,
        )
        return _json(
            report,
            operation_id="engineering_copy_metallographic_report",
            message="Relatório metalográfico duplicado.",
            version=report["version"],
        )
    except Exception as exc:
        return _failure(exc)


@router.put("/{report_id}/images/{slot}", **METALLOGRAPHIC_REPORT_PUT_IMAGE)
@require_permission(METALOGRAPHY_EDIT)
def put_metallographic_image(
    report_id: UUID,
    slot: str,
    if_match: Annotated[str | None, Header()] = None,
    file: UploadFile = File(...),
):
    try:
        content = file.file.read((8 * 1024 * 1024) + 1)
        image = _service().put_image(
            actor=_actor(),
            report_id=str(report_id),
            slot=slot,
            if_match=if_match,
            content=content,
            declared_type=file.content_type,
        )
        return _json(
            image,
            operation_id="engineering_put_metallographic_image",
            message="Micrografia gravada.",
            version=image["version"],
        )
    except Exception as exc:
        return _failure(exc)


@router.get("/{report_id}/images/{slot}", **METALLOGRAPHIC_REPORT_GET_IMAGE)
@require_permission(METALOGRAPHY_VIEW)
def get_metallographic_image(report_id: UUID, slot: str):
    try:
        image = _service().get_image(report_id=str(report_id), slot=slot)
        return Response(
            content=image["content"],
            media_type=image["content_type"],
            headers={
                "ETag": image["etag"],
                "Cache-Control": "private, no-store",
                "Content-Disposition": f'inline; filename="{image["filename"]}"',
            },
        )
    except Exception as exc:
        return _failure(exc)


@router.delete("/{report_id}/images/{slot}", **METALLOGRAPHIC_REPORT_DELETE_IMAGE)
@require_permission(METALOGRAPHY_EDIT)
def delete_metallographic_image(
    report_id: UUID,
    slot: str,
    if_match: Annotated[str | None, Header()] = None,
):
    try:
        deleted = _service().delete_image(
            actor=_actor(),
            report_id=str(report_id),
            slot=slot,
            if_match=if_match,
        )
        return _json(
            deleted,
            operation_id="engineering_delete_metallographic_image",
            message="Micrografia removida.",
            version=deleted["version"],
        )
    except Exception as exc:
        return _failure(exc)


@router.get("/{report_id}/pdf", **METALLOGRAPHIC_REPORT_EXPORT_PDF)
@require_permission(METALOGRAPHY_EXPORT)
def export_metallographic_report_pdf(report_id: UUID):
    try:
        pdf = _service().export_pdf(actor=_actor(), report_id=str(report_id))
        filename = pdf["filename"]
        return Response(
            content=pdf["content"],
            media_type="application/pdf",
            headers={
                "ETag": pdf["etag"],
                "Cache-Control": "private, no-store",
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )
    except Exception as exc:
        return _failure(exc)
