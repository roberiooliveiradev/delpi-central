from helpdesk_app.application.oauth_service import OAuthService
from helpdesk_app.application.ports import GlpiGateway, IdempotencyStore
from helpdesk_app.application.services.message_html_sanitizer import (
    MAX_MESSAGE_HTML_CHARS,
    extract_bff_attachment_refs,
    prepare_outbound_message_html,
)
from helpdesk_app.domain.errors import (
    GlpiNotFound,
    GlpiUnauthorized,
    GlpiValidation,
    LinkRequired,
    MissingIdempotencyKey,
)
from helpdesk_app.domain.models import StoredResponse, TicketDetail, TicketListPage, TicketListQuery
from helpdesk_app.infrastructure.glpi.mapping import normalize_observer_ids


class TicketService:
    def __init__(self, glpi: GlpiGateway, oauth: OAuthService, idempotency: IdempotencyStore):
        self._glpi = glpi
        self._oauth = oauth
        self._idempotency = idempotency

    def categories(self, subject: str):
        return self._glpi.list_categories(self._token(subject))

    def tickets(self, subject: str, query: TicketListQuery) -> TicketListPage:
        return self._glpi.list_tickets(self._token(subject), query)

    def ticket(self, subject: str, ticket_id: int, viewer_email: str = "") -> TicketDetail:
        return self._glpi.get_ticket(self._token(subject), ticket_id, viewer_email=viewer_email)

    def attachment(self, subject: str, ticket_id: int, document_id: int) -> tuple[bytes, str, str]:
        ticket = self.ticket(subject, ticket_id, viewer_email="")
        match = next((item for item in ticket.attachments if item.document_id == document_id), None)
        if match is None:
            raise GlpiNotFound("Anexo não encontrado.")
        content, mime = self._glpi.download_attachment(self._token(subject), document_id)
        return content, mime, match.filename

    def upload_attachment(
        self,
        subject: str,
        ticket_id: int,
        *,
        filename: str,
        content: bytes,
        mime: str,
        idempotency_key: str | None,
    ) -> StoredResponse:
        key = _require_key(idempotency_key)
        operation = f"upload_attachment:{ticket_id}"
        existing = self._idempotency.get(subject, operation, key)
        if existing is not None:
            return existing
        uploaded = self._glpi.upload_ticket_document(
            self._token(subject),
            ticket_id=ticket_id,
            filename=filename,
            content=content,
            mime=mime,
        )
        stored = StoredResponse(
            status_code=201,
            body={
                "document_id": uploaded.document_id,
                "filename": uploaded.filename,
                "mime": uploaded.mime,
            },
        )
        self._idempotency.save(subject, operation, key, stored)
        return stored

    def create(
        self,
        subject: str,
        *,
        title: str,
        description: str,
        category_id: int,
        urgency_id: int,
        observer_ids: list[int] | tuple[int, ...] | None = None,
        idempotency_key: str | None,
    ) -> StoredResponse:
        key = _require_key(idempotency_key)
        _validate_text(title, "title")
        # Opening has no ticket yet — strip every document image (upload after create).
        description_html = _prepare_message_html(description, "description", ticket_id=0)
        observers = normalize_observer_ids(observer_ids)
        operation = "create_ticket"
        existing = self._idempotency.get(subject, operation, key)
        if existing is not None:
            return existing
        token = self._token(subject)
        ticket_id = self._glpi.create_ticket(
            token,
            title=title.strip(),
            description=description_html,
            category_id=category_id,
            urgency_id=urgency_id,
        )
        for user_id in observers:
            self._glpi.add_ticket_observer(token, ticket_id, user_id)
        stored = StoredResponse(status_code=201, body={"id": ticket_id})
        self._idempotency.save(subject, operation, key, stored)
        return stored

    def followup(
        self,
        subject: str,
        ticket_id: int,
        *,
        content: str,
        idempotency_key: str | None,
    ) -> StoredResponse:
        key = _require_key(idempotency_key)
        ticket = self.ticket(subject, ticket_id, viewer_email="")
        allowed = {item.document_id for item in ticket.attachments}
        # H12: after upload, re-read once if HTML refs are not yet in attachments.
        html_refs = {
            doc_id
            for ref_ticket, doc_id in extract_bff_attachment_refs(content)
            if ref_ticket == ticket_id
        }
        if html_refs - allowed:
            ticket = self.ticket(subject, ticket_id, viewer_email="")
            allowed = {item.document_id for item in ticket.attachments}
        content_html = _prepare_message_html(
            content,
            "content",
            ticket_id=ticket_id,
            allowed_document_ids=allowed,
        )
        operation = f"followup:{ticket_id}"
        existing = self._idempotency.get(subject, operation, key)
        if existing is not None:
            return existing
        followup_id = self._glpi.add_followup(
            self._token(subject), ticket_id, content_html
        )
        stored = StoredResponse(status_code=201, body={"id": followup_id})
        self._idempotency.save(subject, operation, key, stored)
        return stored

    def _token(self, subject: str) -> str:
        try:
            return self._oauth.access_token_for(subject)
        except GlpiUnauthorized as exc:
            raise LinkRequired("A sessão do GLPI expirou. Autorize de novo.") from exc


def _require_key(value: str | None) -> str:
    if value is None or not value.strip():
        raise MissingIdempotencyKey("Informe Idempotency-Key.")
    return value.strip()


def _validate_text(value: str, field: str) -> None:
    if not value or not value.strip():
        raise GlpiValidation(f"{field} é obrigatório.")


def _prepare_message_html(
    value: str,
    field: str,
    *,
    ticket_id: int = 0,
    allowed_document_ids: set[int] | frozenset[int] | None = None,
) -> str:
    if value is None:
        raise GlpiValidation(f"{field} é obrigatório.")
    if len(value) > MAX_MESSAGE_HTML_CHARS:
        raise GlpiValidation(f"{field} excede o tamanho máximo permitido.")
    cleaned = prepare_outbound_message_html(
        value,
        ticket_id=ticket_id,
        allowed_document_ids=allowed_document_ids or (),
    )
    if not cleaned:
        raise GlpiValidation(f"{field} é obrigatório.")
    return cleaned
