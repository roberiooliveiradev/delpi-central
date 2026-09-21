from typing import Any

from urllib.parse import quote

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, ConfigDict, Field

from helpdesk_app.domain.errors import HelpdeskError
from helpdesk_app.infrastructure.glpi.mapping import URGENCIES, attachment_filename
from helpdesk_app.interface.http.actor import require_actor

router = APIRouter(tags=["Helpdesk Tickets"])


class CreateTicketBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    description: str
    category_id: int
    urgency_id: int


class FollowupBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str = Field(min_length=1)


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


@router.get("/urgencies")
def urgencies(request: Request):
    require_actor(request)
    return {"items": [{"id": row.id, "name": row.name} for row in URGENCIES]}


@router.get("/tickets")
def list_tickets(request: Request):
    actor = require_actor(request)
    try:
        rows = _tickets(request).tickets(actor.subject)
    except HelpdeskError as exc:
        return _error(exc, request)
    return {
        "items": [
            {
                "id": row.id,
                "title": row.title,
                "status": row.status,
                "category": row.category,
                "urgency": row.urgency,
                "updated_at": row.updated_at,
            }
            for row in rows
        ]
    }


@router.get("/tickets/{ticket_id}")
def get_ticket(request: Request, ticket_id: int):
    actor = require_actor(request)
    try:
        ticket = _tickets(request).ticket(actor.subject, ticket_id)
    except HelpdeskError as exc:
        return _error(exc, request)
    return {
        "id": ticket.id,
        "title": ticket.title,
        "status": ticket.status,
        "category": ticket.category,
        "urgency": ticket.urgency,
        "updated_at": ticket.updated_at,
        "description": ticket.description,
        "timeline": [
            {
                "id": entry.id,
                "kind": entry.kind,
                "content": entry.content,
                "created_at": entry.created_at,
                "author_display_name": entry.author_display_name,
            }
            for entry in ticket.timeline
        ],
        "attachments": [
            {
                "document_id": item.document_id,
                "filename": item.filename,
                "mime": item.mime,
            }
            for item in ticket.attachments
        ],
    }


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
            idempotency_key=idempotency_key,
        )
    except HelpdeskError as exc:
        return _error(exc, request)
    return JSONResponse(status_code=stored.status_code, content=stored.body)
