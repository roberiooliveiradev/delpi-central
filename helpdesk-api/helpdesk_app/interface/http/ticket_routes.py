from typing import Any, Literal

from urllib.parse import quote

from fastapi import APIRouter, File, Form, Header, Request, UploadFile
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, ConfigDict, Field, model_validator

from helpdesk_app.application.services.message_html_sanitizer import (
    extract_bff_attachment_refs,
)
from helpdesk_app.application import dashboard_reader_gate
from helpdesk_app.domain.errors import (
    HelpdeskError,
    GlpiValidation,
    InstitutionalReadDenied,
    InstitutionalReaderUnavailable,
)
from helpdesk_app.infrastructure.glpi.mapping import (
    IMPACTS,
    PRIORITIES,
    TICKET_TYPES,
    URGENCIES,
    attachment_filename,
    build_ticket_list_query,
)
from helpdesk_app.interface.http.actor import require_actor

router = APIRouter(tags=["Helpdesk Tickets"])


def _attachment_refs(ticket) -> list[dict[str, int]]:
    """Deduplicated {document_id} universe: Document_Item attachments ∪
    inline refs embedded in description/timeline HTML (R4.2)."""
    refs = {item.document_id for item in ticket.attachments}
    html_sources = [ticket.description_html] + [
        entry.content_html for entry in ticket.timeline
    ]
    for html in html_sources:
        for ref_ticket, doc_id in extract_bff_attachment_refs(html):
            if ref_ticket == ticket.id:
                refs.add(doc_id)
    return [
        {"document_id": doc_id}
        for doc_id in sorted(refs)
    ]


class CreateTicketBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    description: str
    category_id: int
    urgency_id: int
    observer_ids: list[int] = Field(default_factory=list)
    assignee_id: int | None = None


class FollowupBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str = Field(min_length=1)
    request_type_id: int | None = Field(default=None, gt=0)


class FollowupUpdateBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str = Field(min_length=1)


class DescriptionUpdateBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str = Field(min_length=1)


class ClassificationUpdateBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Partial update — every field optional; the service requires >=1 and
    # validates each id against the canonical enum maps / GLPI catalog.
    urgency_id: int | None = Field(default=None, gt=0)
    impact_id: int | None = Field(default=None, gt=0)
    category_id: int | None = Field(default=None, gt=0)
    type_id: int | None = Field(default=None, gt=0)
    priority_id: int | None = Field(default=None, gt=0)
    request_type_id: int | None = Field(default=None, gt=0)


class SolutionCreateBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str = Field(min_length=1)
    solution_type_id: int | None = Field(default=None, gt=0)


class TaskCreateBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str = Field(min_length=1)
    state: int | None = Field(default=None, ge=0, le=2)
    duration_seconds: int | None = Field(default=None, ge=0)
    category_id: int | None = Field(default=None, gt=0)
    user_tech_id: int | None = Field(default=None, gt=0)
    group_tech_id: int | None = Field(default=None, gt=0)
    planned_begin: str | None = None
    planned_end: str | None = None


class ApprovalRequestBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    """Backward-compatible user target; prefer approver_type + approver_id. """
    approver_user_id: int | None = Field(default=None, gt=0)
    approver_type: Literal["user", "group"] = "user"
    approver_id: int | None = Field(default=None, gt=0)
    content: str = ""

    @model_validator(mode="after")
    def resolve_approver(self):
        if self.approver_id is None and self.approver_user_id is not None:
            object.__setattr__(self, "approver_id", self.approver_user_id)
            object.__setattr__(self, "approver_type", "user")
        if self.approver_id is None or int(self.approver_id) <= 0:
            raise ValueError("approver_id ou approver_user_id é obrigatório.")
        return self


class SolutionDecisionBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str = ""


class SatisfactionBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    satisfaction: int = Field(ge=1, le=5)
    comment: str = ""


class AssigneeBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: int = Field(gt=0)


def _tickets(request: Request):
    return request.app.state.tickets


def _error(exc: HelpdeskError, request: Request) -> JSONResponse:
    body: dict[str, Any] = {"error": exc.code}
    if exc.code == "glpi_link_required":
        body["authorize_url"] = "/apps/helpdesk-api/auth/glpi/start"
    return JSONResponse(status_code=exc.status_code, content=body)


@router.get("/ticket-categories")
def ticket_categories(request: Request):
    actor = require_actor(request)
    try:
        rows = _tickets(request).categories(actor.subject)
    except HelpdeskError as exc:
        return _error(exc, request)
    return {"items": [{"id": row.id, "name": row.name} for row in rows]}


def _catalog_items(rows) -> dict:
    return {"items": [{"id": row.id, "name": row.name} for row in rows]}


def _template_items(rows) -> dict:
    return {
        "items": [
            {
                "id": row.id,
                "name": row.name,
                "content": row.content,
                "is_private": row.is_private,
                "request_type_id": row.request_type_id,
                "solution_type_id": row.solution_type_id,
                "category_id": row.category_id,
                "state": row.state,
                "duration_seconds": row.duration_seconds,
                "user_tech_id": row.user_tech_id,
                "group_tech_id": row.group_tech_id,
                "use_current_user": row.use_current_user,
            }
            for row in rows
        ]
    }


@router.get("/request-types")
def request_types(request: Request):
    actor = require_actor(request)
    try:
        return _catalog_items(_tickets(request).request_types(actor.subject))
    except HelpdeskError as exc:
        return _error(exc, request)


@router.get("/followup-templates")
def followup_templates(request: Request):
    actor = require_actor(request)
    try:
        return _template_items(_tickets(request).followup_templates(actor.subject))
    except HelpdeskError as exc:
        return _error(exc, request)


@router.get("/solution-types")
def solution_types(request: Request):
    actor = require_actor(request)
    try:
        return _catalog_items(_tickets(request).solution_types(actor.subject))
    except HelpdeskError as exc:
        return _error(exc, request)


@router.get("/solution-templates")
def solution_templates(request: Request):
    actor = require_actor(request)
    try:
        return _template_items(_tickets(request).solution_templates(actor.subject))
    except HelpdeskError as exc:
        return _error(exc, request)


@router.get("/task-categories")
def task_categories(request: Request):
    actor = require_actor(request)
    try:
        return _catalog_items(_tickets(request).task_categories(actor.subject))
    except HelpdeskError as exc:
        return _error(exc, request)


@router.get("/task-templates")
def task_templates(request: Request):
    actor = require_actor(request)
    try:
        return _template_items(_tickets(request).task_templates(actor.subject))
    except HelpdeskError as exc:
        return _error(exc, request)


@router.get("/task-statuses")
def task_statuses(request: Request):
    require_actor(request)
    return _catalog_items(_tickets(request).task_statuses())


@router.get("/groups")
def groups(request: Request):
    actor = require_actor(request)
    try:
        return _catalog_items(_tickets(request).groups(actor.subject))
    except HelpdeskError as exc:
        return _error(exc, request)


@router.get("/validation-templates")
def validation_templates(request: Request):
    actor = require_actor(request)
    try:
        return _template_items(_tickets(request).validation_templates(actor.subject))
    except HelpdeskError as exc:
        return _error(exc, request)


@router.get("/approval-steps")
def approval_steps(request: Request):
    actor = require_actor(request)
    try:
        return _catalog_items(_tickets(request).approval_steps(actor.subject))
    except HelpdeskError as exc:
        return _error(exc, request)


@router.get("/urgencies")
def urgencies(request: Request):
    require_actor(request)
    return {"items": [{"id": row.id, "name": row.name} for row in URGENCIES]}


@router.get("/impacts")
def impacts(request: Request):
    require_actor(request)
    return {"items": [{"id": row.id, "name": row.name} for row in IMPACTS]}


@router.get("/priorities")
def priorities(request: Request):
    require_actor(request)
    return {"items": [{"id": row.id, "name": row.name} for row in PRIORITIES]}


@router.get("/ticket-types")
def ticket_types(request: Request):
    require_actor(request)
    return {"items": [{"id": row.id, "name": row.name} for row in TICKET_TYPES]}


@router.get("/users")
def list_users(request: Request, q: str = "", limit: int = 20, purpose: str = "mention"):
    actor = require_actor(request)
    try:
        rows = _tickets(request).users(actor.subject, q=q, limit=limit, purpose=purpose)
    except HelpdeskError as exc:
        return _error(exc, request)
    return {
        "items": [
            {
                "id": row.id,
                "display_name": row.display_name,
                "email": getattr(row, "email", "") or "",
                "directory_user_id": getattr(row, "directory_user_id", "") or "",
                "has_photo": bool(getattr(row, "has_photo", False)),
            }
            for row in rows
        ]
    }


@router.get("/session/capabilities")
def session_capabilities(request: Request):
    actor = require_actor(request)
    try:
        return _tickets(request).capabilities(actor.subject)
    except HelpdeskError as exc:
        return _error(exc, request)


@router.get("/tickets")
def list_tickets(
    request: Request,
    q: str = "",
    status: str = "",
    urgency_id: int | None = None,
    category_id: int | None = None,
    updated_from: str = "",
    updated_to: str = "",
    created_from: str = "",
    created_to: str = "",
    assignee_id: int | None = None,
    sort: str = "updated_at:desc",
    page: int = 1,
    page_size: int = 20,
):
    actor = require_actor(request)
    try:
        query = build_ticket_list_query(
            q=q,
            status=status,
            urgency_id=urgency_id,
            category_id=category_id,
            updated_from=updated_from,
            updated_to=updated_to,
            created_from=created_from,
            created_to=created_to,
            assignee_id=assignee_id,
            sort=sort,
            page=page,
            page_size=page_size,
        )
        decision = dashboard_reader_gate.classify_ticket_list(request)
        if decision == "denied":
            raise InstitutionalReadDenied("Leitura institucional do Helpdesk não autorizada.")
        if decision == "unavailable":
            raise InstitutionalReaderUnavailable("Leitura institucional do Helpdesk indisponível.")
        if decision == "ready":
            listed = _tickets(request).tickets_as_dashboard_reader(query)
        else:
            listed = _tickets(request).tickets(actor.subject, query)
    except HelpdeskError as exc:
        return _error(exc, request)
    return {
        "items": [
            {
                "id": row.id,
                "title": row.title,
                "status": row.status,
                "status_id": row.status_id,
                "category": row.category,
                "urgency": row.urgency,
                "updated_at": row.updated_at,
                "created_at": row.created_at,
                "solved_at": row.solved_at,
                "closed_at": row.closed_at,
                "sla_ttr": row.sla_ttr,
                "sla_tto": row.sla_tto,
                "sla_ttr_exceeded": row.sla_ttr_exceeded,
                "assigned_display_name": row.assigned_display_name,
                "assigned_user_id": row.assigned_user_id,
                "requester_display_name": row.requester_display_name,
                "requester_id": row.requester_id,
                "entity": row.entity,
                "last_editor": row.last_editor,
            }
            for row in listed.items
        ],
        "page": listed.page,
        "page_size": listed.page_size,
        "has_more": listed.has_more,
    }


@router.get("/tickets/{ticket_id}")
def get_ticket(request: Request, ticket_id: int):
    actor = require_actor(request)
    try:
        ticket = _tickets(request).ticket(actor.subject, ticket_id, viewer_email=actor.email)
    except HelpdeskError as exc:
        return _error(exc, request)
    return {
        "id": ticket.id,
        "title": ticket.title,
        "status": ticket.status,
        "status_id": ticket.status_id,
        "category": ticket.category,
        "urgency": ticket.urgency,
        "category_id": ticket.category_id,
        "urgency_id": ticket.urgency_id,
        "impact_id": ticket.impact_id,
        "priority_id": ticket.priority_id,
        "type_id": ticket.type_id,
        "impact": ticket.impact,
        "priority": ticket.priority,
        "type_name": ticket.type_name,
        "request_type_id": ticket.request_type_id,
        "can_update_classification": ticket.can_update_classification,
        "updated_at": ticket.updated_at,
        "created_at": ticket.created_at,
        "solved_at": ticket.solved_at,
        "closed_at": ticket.closed_at,
        "sla_ttr": ticket.sla_ttr,
        "sla_tto": ticket.sla_tto,
        "can_followup": ticket.can_followup,
        "requester_display_name": ticket.requester_display_name,
        "requester_mine": ticket.requester_mine,
        "assigned_display_name": ticket.assigned_display_name,
        "assigned_user_id": ticket.assigned_user_id,
        "can_assign": ticket.can_assign,
        "can_create_solution": ticket.can_create_solution,
        "can_create_task": ticket.can_create_task,
        "can_request_approval": ticket.can_request_approval,
        "can_accept_solution": ticket.can_accept_solution,
        "can_reject_solution": ticket.can_reject_solution,
        "can_submit_satisfaction": ticket.can_submit_satisfaction,
        "satisfaction": ticket.satisfaction,
        "satisfaction_comment": ticket.satisfaction_comment,
        "can_decide_validation": ticket.can_decide_validation,
        "validations": [
            {
                "id": item.id,
                "status": item.status,
                "submission_comment": item.submission_comment,
                "approval_comment": item.approval_comment,
                "requested_approver_id": item.requested_approver_id,
                "requested_approver_type": item.requested_approver_type,
                "mine_to_decide": item.mine_to_decide,
            }
            for item in ticket.validations
        ],
        "observers_display_name": ticket.observers_display_name,
        "description": ticket.description,
        "description_html": ticket.description_html,
        "timeline": [
            {
                "id": entry.id,
                "kind": entry.kind,
                "content": entry.content,
                "content_html": entry.content_html,
                "created_at": entry.created_at,
                "author_display_name": entry.author_display_name,
                "mine": entry.mine,
                "state": entry.state,
                "duration_seconds": entry.duration_seconds,
                "category_name": entry.category_name,
                "user_tech_display_name": entry.user_tech_display_name,
                "group_tech_display_name": entry.group_tech_display_name,
                "planned_begin": entry.planned_begin,
                "planned_end": entry.planned_end,
                "solution_type_name": entry.solution_type_name,
                "solution_status": entry.solution_status,
            }
            for entry in ticket.timeline
        ],
        "attachments": [
            {
                "document_id": item.document_id,
                "filename": item.filename,
                "mime": item.mime,
                "itemtype": item.itemtype,
                "items_id": item.items_id,
            }
            for item in ticket.attachments
        ],
        # Canonical document universe: attachments[] plus inline <img> refs
        # embedded in description/timeline HTML — deduplicated by
        # document_id so consumers never miss or double-fetch evidence.
        "attachment_refs": _attachment_refs(ticket),
    }


@router.delete("/tickets/{ticket_id}")
def delete_ticket(
    request: Request,
    ticket_id: int,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    actor = require_actor(request)
    try:
        stored = _tickets(request).delete(
            actor.subject, ticket_id, idempotency_key=idempotency_key
        )
    except HelpdeskError as exc:
        return _error(exc, request)
    return JSONResponse(status_code=stored.status_code, content=stored.body)


@router.get("/tickets/{ticket_id}/attachments/{document_id}")
def download_attachment(request: Request, ticket_id: int, document_id: int):
    actor = require_actor(request)
    try:
        content, mime, filename = _tickets(request).attachment(actor.subject, ticket_id, document_id)
    except HelpdeskError as exc:
        return _error(exc, request)
    safe_name = attachment_filename(filename)
    ascii_name = "".join(char if char.isascii() and char not in "\r\n\"" else "_" for char in safe_name)
    encoded_name = quote(safe_name)
    return Response(
        content=content,
        media_type=mime or "application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{encoded_name}"
        },
    )


@router.post(
    "/tickets/{ticket_id}/attachments",
    # Governed outcome contract: 201 only when authorship read-back is
    # verified; 207 = typed partial result (outcome=verification_failed)
    # with document_id preserved for reconciliation.
    responses={
        201: {"description": "Attachment created and authorship verified"},
        207: {"description": "Attachment persisted; authorship unverified (partial result)"},
    },
)
async def upload_attachment(
    request: Request,
    ticket_id: int,
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    actor = require_actor(request)
    raw = await file.read()
    try:
        if not raw:
            raise GlpiValidation("Arquivo vazio.")
        stored = _tickets(request).upload_attachment(
            actor.subject,
            ticket_id,
            filename=file.filename or "anexo",
            content=raw,
            mime=file.content_type or "application/octet-stream",
            title=title,
            idempotency_key=idempotency_key,
        )
    except HelpdeskError as exc:
        return _error(exc, request)
    return JSONResponse(status_code=stored.status_code, content=stored.body)


@router.post("/tickets")
def create_ticket(
    request: Request,
    body: CreateTicketBody,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    actor = require_actor(request)
    try:
        stored = _tickets(request).create(
            actor.subject,
            title=body.title,
            description=body.description,
            category_id=body.category_id,
            urgency_id=body.urgency_id,
            observer_ids=body.observer_ids,
            assignee_id=body.assignee_id,
            idempotency_key=idempotency_key,
        )
    except HelpdeskError as exc:
        return _error(exc, request)
    return JSONResponse(status_code=stored.status_code, content=stored.body)


@router.put("/tickets/{ticket_id}/assignee")
def set_assignee(
    request: Request,
    ticket_id: int,
    body: AssigneeBody,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    actor = require_actor(request)
    try:
        stored = _tickets(request).set_assignee(
            actor.subject,
            ticket_id,
            user_id=body.user_id,
            idempotency_key=idempotency_key,
        )
    except HelpdeskError as exc:
        return _error(exc, request)
    return JSONResponse(status_code=stored.status_code, content=stored.body)


@router.post("/tickets/{ticket_id}/followups")
def create_followup(
    request: Request,
    ticket_id: int,
    body: FollowupBody,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    actor = require_actor(request)
    try:
        stored = _tickets(request).followup(
            actor.subject,
            ticket_id,
            content=body.content,
            request_type_id=body.request_type_id,
            idempotency_key=idempotency_key,
        )
    except HelpdeskError as exc:
        return _error(exc, request)
    return JSONResponse(status_code=stored.status_code, content=stored.body)


@router.put("/tickets/{ticket_id}/followups/{followup_id}")
def update_followup(
    request: Request,
    ticket_id: int,
    followup_id: int,
    body: FollowupUpdateBody,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    actor = require_actor(request)
    try:
        stored = _tickets(request).update_followup(
            actor.subject,
            ticket_id,
            followup_id,
            content=body.content,
            viewer_email=actor.email,
            idempotency_key=idempotency_key,
        )
    except HelpdeskError as exc:
        return _error(exc, request)
    return JSONResponse(status_code=stored.status_code, content=stored.body)


@router.patch("/tickets/{ticket_id}/description")
def update_ticket_description(
    request: Request,
    ticket_id: int,
    body: DescriptionUpdateBody,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    actor = require_actor(request)
    try:
        stored = _tickets(request).update_description(
            actor.subject,
            ticket_id,
            content=body.content,
            viewer_email=actor.email,
            idempotency_key=idempotency_key,
        )
    except HelpdeskError as exc:
        return _error(exc, request)
    return JSONResponse(status_code=stored.status_code, content=stored.body)


@router.patch("/tickets/{ticket_id}/classification")
def update_ticket_classification(
    request: Request,
    ticket_id: int,
    body: ClassificationUpdateBody,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    actor = require_actor(request)
    try:
        stored = _tickets(request).update_classification(
            actor.subject,
            ticket_id,
            urgency_id=body.urgency_id,
            impact_id=body.impact_id,
            category_id=body.category_id,
            type_id=body.type_id,
            priority_id=body.priority_id,
            request_type_id=body.request_type_id,
            viewer_email=actor.email,
            idempotency_key=idempotency_key,
        )
    except HelpdeskError as exc:
        return _error(exc, request)
    return JSONResponse(status_code=stored.status_code, content=stored.body)


@router.post("/tickets/{ticket_id}/solutions")
def create_ticket_solution(
    request: Request,
    ticket_id: int,
    body: SolutionCreateBody,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    actor = require_actor(request)
    try:
        stored = _tickets(request).create_solution(
            actor.subject,
            ticket_id,
            content=body.content,
            solution_type_id=body.solution_type_id,
            viewer_email=actor.email,
            idempotency_key=idempotency_key,
        )
    except HelpdeskError as exc:
        return _error(exc, request)
    return JSONResponse(status_code=stored.status_code, content=stored.body)


@router.post("/tickets/{ticket_id}/tasks")
def create_ticket_task(
    request: Request,
    ticket_id: int,
    body: TaskCreateBody,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    actor = require_actor(request)
    try:
        stored = _tickets(request).create_task(
            actor.subject,
            ticket_id,
            content=body.content,
            state=body.state,
            duration_seconds=body.duration_seconds,
            category_id=body.category_id,
            user_tech_id=body.user_tech_id,
            group_tech_id=body.group_tech_id,
            planned_begin=body.planned_begin,
            planned_end=body.planned_end,
            viewer_email=actor.email,
            idempotency_key=idempotency_key,
        )
    except HelpdeskError as exc:
        return _error(exc, request)
    return JSONResponse(status_code=stored.status_code, content=stored.body)


@router.post("/tickets/{ticket_id}/validations")
def request_ticket_approval(
    request: Request,
    ticket_id: int,
    body: ApprovalRequestBody,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    actor = require_actor(request)
    try:
        stored = _tickets(request).request_approval(
            actor.subject,
            ticket_id,
            approver_type=body.approver_type,
            approver_id=int(body.approver_id or 0),
            content=body.content,
            viewer_email=actor.email,
            idempotency_key=idempotency_key,
        )
    except HelpdeskError as exc:
        return _error(exc, request)
    return JSONResponse(status_code=stored.status_code, content=stored.body)


@router.post(
    "/tickets/{ticket_id}/solution/accept",
    # 200 only on fully verified outcome; 207 = typed partial
    # (author_mismatch | author_unverified | status_unverified).
    responses={
        200: {"description": "Decision applied and authorship/status verified"},
        207: {"description": "Decision persisted; authorship/status unverified (partial result)"},
    },
)
def accept_solution(
    request: Request,
    ticket_id: int,
    body: SolutionDecisionBody,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    actor = require_actor(request)
    try:
        stored = _tickets(request).accept_solution(
            actor.subject,
            ticket_id,
            content=body.content,
            viewer_email=actor.email,
            idempotency_key=idempotency_key,
        )
    except HelpdeskError as exc:
        return _error(exc, request)
    return JSONResponse(status_code=stored.status_code, content=stored.body)


@router.post(
    "/tickets/{ticket_id}/solution/reject",
    # 200 only on fully verified outcome; 207 = typed partial
    # (author_mismatch | author_unverified | status_unverified).
    responses={
        200: {"description": "Decision applied and authorship/status verified"},
        207: {"description": "Decision persisted; authorship/status unverified (partial result)"},
    },
)
def reject_solution(
    request: Request,
    ticket_id: int,
    body: SolutionDecisionBody,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    actor = require_actor(request)
    try:
        stored = _tickets(request).reject_solution(
            actor.subject,
            ticket_id,
            content=body.content,
            viewer_email=actor.email,
            idempotency_key=idempotency_key,
        )
    except HelpdeskError as exc:
        return _error(exc, request)
    return JSONResponse(status_code=stored.status_code, content=stored.body)


@router.get("/tickets/{ticket_id}/satisfaction")
def get_satisfaction(request: Request, ticket_id: int):
    actor = require_actor(request)
    try:
        return _tickets(request).satisfaction(actor.subject, ticket_id, viewer_email=actor.email)
    except HelpdeskError as exc:
        return _error(exc, request)


@router.put("/tickets/{ticket_id}/satisfaction")
def put_satisfaction(
    request: Request,
    ticket_id: int,
    body: SatisfactionBody,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    actor = require_actor(request)
    try:
        stored = _tickets(request).submit_satisfaction(
            actor.subject,
            ticket_id,
            satisfaction=body.satisfaction,
            comment=body.comment,
            viewer_email=actor.email,
            idempotency_key=idempotency_key,
        )
    except HelpdeskError as exc:
        return _error(exc, request)
    return JSONResponse(status_code=stored.status_code, content=stored.body)


@router.post("/tickets/{ticket_id}/validations/{validation_id}/accept")
def accept_validation(
    request: Request,
    ticket_id: int,
    validation_id: int,
    body: SolutionDecisionBody,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    actor = require_actor(request)
    try:
        stored = _tickets(request).decide_validation(
            actor.subject,
            ticket_id,
            validation_id,
            accept=True,
            comment=body.content,
            viewer_email=actor.email,
            idempotency_key=idempotency_key,
        )
    except HelpdeskError as exc:
        return _error(exc, request)
    return JSONResponse(status_code=stored.status_code, content=stored.body)


@router.post("/tickets/{ticket_id}/validations/{validation_id}/reject")
def reject_validation(
    request: Request,
    ticket_id: int,
    validation_id: int,
    body: SolutionDecisionBody,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    actor = require_actor(request)
    try:
        stored = _tickets(request).decide_validation(
            actor.subject,
            ticket_id,
            validation_id,
            accept=False,
            comment=body.content,
            viewer_email=actor.email,
            idempotency_key=idempotency_key,
        )
    except HelpdeskError as exc:
        return _error(exc, request)
    return JSONResponse(status_code=stored.status_code, content=stored.body)
