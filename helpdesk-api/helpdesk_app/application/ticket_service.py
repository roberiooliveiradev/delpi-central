from dataclasses import replace

from helpdesk_app.application.oauth_service import OAuthService
from helpdesk_app.application.ports import GlpiGateway, IdempotencyStore
from helpdesk_app.application.services.message_html_sanitizer import (
    MAX_MESSAGE_HTML_CHARS,
    extract_bff_attachment_refs,
    prepare_outbound_message_html,
)
from helpdesk_app.domain.errors import (
    GlpiFeatureDisabled,
    GlpiForbidden,
    GlpiNotFound,
    GlpiUnauthorized,
    GlpiValidation,
    LinkRequired,
    MissingIdempotencyKey,
)
from helpdesk_app.domain.models import StoredResponse, TicketDetail, TicketListPage, TicketListQuery
from helpdesk_app.infrastructure.glpi.mapping import (
    normalize_assignee_id,
    normalize_observer_ids,
    solicitante_cycle_flags,
)


class TicketService:
    def __init__(self, glpi: GlpiGateway, oauth: OAuthService, idempotency: IdempotencyStore):
        self._glpi = glpi
        self._oauth = oauth
        self._idempotency = idempotency

    def categories(self, subject: str):
        return self._glpi.list_categories(self._token(subject))

    def users(self, subject: str, *, q: str = "", limit: int = 20):
        return self._glpi.list_users(self._token(subject), q=q, limit=limit)

    def capabilities(self, subject: str) -> dict:
        token = self._token(subject)
        return {"can_assign": bool(self._glpi.can_assign_tickets(token))}

    def tickets(self, subject: str, query: TicketListQuery) -> TicketListPage:
        return self._glpi.list_tickets(self._token(subject), query)

    def ticket(self, subject: str, ticket_id: int, viewer_email: str = "") -> TicketDetail:
        token = self._token(subject)
        detail = self._glpi.get_ticket(token, ticket_id, viewer_email=viewer_email)
        detail = replace(detail, can_assign=bool(self._glpi.can_assign_tickets(token)))
        return self._with_cycle_flags(token, detail)

    def attachment(self, subject: str, ticket_id: int, document_id: int) -> tuple[bytes, str, str]:
        token = self._token(subject)
        ticket = self._glpi.get_ticket(token, ticket_id, viewer_email="")
        match = next((item for item in ticket.attachments if item.document_id == document_id), None)
        if match is None:
            # H12: Timeline HLAPI pode omitir Document_Item recém-criado via upload legado.
            if not self._glpi.ticket_owns_document(token, ticket_id, document_id):
                raise GlpiNotFound("Anexo não encontrado.")
            content, mime = self._glpi.download_attachment(token, document_id)
            return content, mime, "anexo"
        content, mime = self._glpi.download_attachment(token, document_id)
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
        assignee_id: int | None = None,
        idempotency_key: str | None,
    ) -> StoredResponse:
        key = _require_key(idempotency_key)
        _validate_text(title, "title")
        # Opening has no ticket yet — strip every document image (upload after create).
        description_html = _prepare_message_html(description, "description", ticket_id=0)
        observers = normalize_observer_ids(observer_ids)
        assignee = normalize_assignee_id(assignee_id)
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
        if assignee is not None:
            self._glpi.add_ticket_assignee(token, ticket_id, assignee)
        stored = StoredResponse(status_code=201, body={"id": ticket_id})
        self._idempotency.save(subject, operation, key, stored)
        return stored

    def set_assignee(
        self,
        subject: str,
        ticket_id: int,
        *,
        user_id: int,
        idempotency_key: str | None,
    ) -> StoredResponse:
        key = _require_key(idempotency_key)
        assignee = normalize_assignee_id(user_id)
        if assignee is None:
            raise GlpiValidation("assignee_id inválido.")
        operation = f"set_assignee:{ticket_id}"
        existing = self._idempotency.get(subject, operation, key)
        if existing is not None:
            return existing
        token = self._token(subject)
        detail = self._glpi.get_ticket(token, ticket_id, viewer_email="")
        current = detail.assigned_user_id
        if current == assignee:
            stored = StoredResponse(
                status_code=200,
                body={"user_id": assignee, "assigned_display_name": detail.assigned_display_name},
            )
            self._idempotency.save(subject, operation, key, stored)
            return stored
        if current is not None and current != assignee:
            self._glpi.remove_ticket_assignee(token, ticket_id, current)
        self._glpi.add_ticket_assignee(token, ticket_id, assignee)
        refreshed = self._glpi.get_ticket(token, ticket_id, viewer_email="")
        stored = StoredResponse(
            status_code=200,
            body={
                "user_id": refreshed.assigned_user_id or assignee,
                "assigned_display_name": refreshed.assigned_display_name,
            },
        )
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
        # H12: Document_Item via legacy upload may still be absent from Timeline.
        token = self._token(subject)
        ticket = self._glpi.get_ticket(token, ticket_id, viewer_email="")
        allowed = {item.document_id for item in ticket.attachments}
        # H12: after upload, re-read once if HTML refs are not yet in attachments.
        html_refs = {
            doc_id
            for ref_ticket, doc_id in extract_bff_attachment_refs(content)
            if ref_ticket == ticket_id
        }
        if html_refs - allowed:
            ticket = self._glpi.get_ticket(token, ticket_id, viewer_email="")
            allowed = {item.document_id for item in ticket.attachments}
        for doc_id in html_refs - allowed:
            if self._glpi.ticket_owns_document(token, ticket_id, doc_id):
                allowed.add(doc_id)
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

    def accept_solution(
        self,
        subject: str,
        ticket_id: int,
        *,
        content: str = "",
        viewer_email: str = "",
        idempotency_key: str | None,
    ) -> StoredResponse:
        key = _require_key(idempotency_key)
        operation = f"accept_solution:{ticket_id}"
        existing = self._idempotency.get(subject, operation, key)
        if existing is not None:
            return existing
        token = self._token(subject)
        detail = self._glpi.get_ticket(token, ticket_id, viewer_email=viewer_email)
        if not detail.requester_mine:
            raise GlpiForbidden("Só o solicitante pode aceitar a solução.")
        if detail.status_id != 5:
            raise GlpiValidation("Só é possível aceitar solução em chamado solucionado.")
        message = (content or "").strip() or "Solução aceita."
        self._glpi.accept_ticket_solution(token, ticket_id, message)
        refreshed = self._with_cycle_flags(
            token, self._glpi.get_ticket(token, ticket_id, viewer_email=viewer_email)
        )
        stored = StoredResponse(
            status_code=200,
            body={"id": refreshed.id, "status_id": refreshed.status_id},
        )
        self._idempotency.save(subject, operation, key, stored)
        return stored

    def reject_solution(
        self,
        subject: str,
        ticket_id: int,
        *,
        content: str = "",
        viewer_email: str = "",
        idempotency_key: str | None,
    ) -> StoredResponse:
        key = _require_key(idempotency_key)
        operation = f"reject_solution:{ticket_id}"
        existing = self._idempotency.get(subject, operation, key)
        if existing is not None:
            return existing
        token = self._token(subject)
        detail = self._glpi.get_ticket(token, ticket_id, viewer_email=viewer_email)
        if not detail.requester_mine:
            raise GlpiForbidden("Só o solicitante pode recusar a solução.")
        if detail.status_id not in {5, 6}:
            raise GlpiValidation("Só é possível recusar/reabrir em solucionado ou fechado.")
        message = (content or "").strip() or "Solução recusada."
        self._glpi.reject_ticket_solution(token, ticket_id, message)
        refreshed = self._with_cycle_flags(
            token, self._glpi.get_ticket(token, ticket_id, viewer_email=viewer_email)
        )
        stored = StoredResponse(
            status_code=200,
            body={"id": refreshed.id, "status_id": refreshed.status_id},
        )
        self._idempotency.save(subject, operation, key, stored)
        return stored

    def satisfaction(self, subject: str, ticket_id: int, viewer_email: str = "") -> dict:
        token = self._token(subject)
        detail = self._glpi.get_ticket(token, ticket_id, viewer_email=viewer_email)
        if not detail.requester_mine:
            raise GlpiForbidden("Só o solicitante pode ver a pesquisa de satisfação.")
        row = self._glpi.get_ticket_satisfaction(token, ticket_id)
        if row is None:
            raise GlpiNotFound("Pesquisa de satisfação não encontrada.")
        score, comment = row
        return {"satisfaction": score, "comment": comment}

    def submit_satisfaction(
        self,
        subject: str,
        ticket_id: int,
        *,
        satisfaction: int,
        comment: str = "",
        viewer_email: str = "",
        idempotency_key: str | None,
    ) -> StoredResponse:
        key = _require_key(idempotency_key)
        operation = f"submit_satisfaction:{ticket_id}"
        existing = self._idempotency.get(subject, operation, key)
        if existing is not None:
            return existing
        if satisfaction not in {1, 2, 3, 4, 5}:
            raise GlpiValidation("satisfaction inválida.")
        token = self._token(subject)
        detail = self._glpi.get_ticket(token, ticket_id, viewer_email=viewer_email)
        if not detail.requester_mine:
            raise GlpiForbidden("Só o solicitante pode responder a pesquisa.")
        if detail.status_id != 6:
            raise GlpiValidation("Pesquisa só é disponível em chamado fechado.")
        existing_sat = self._glpi.get_ticket_satisfaction(token, ticket_id)
        if existing_sat is not None:
            raise GlpiValidation("Pesquisa de satisfação já registrada.")
        self._glpi.submit_ticket_satisfaction(
            token,
            ticket_id,
            satisfaction=satisfaction,
            comment=(comment or "").strip(),
        )
        stored = StoredResponse(
            status_code=201,
            body={"satisfaction": satisfaction, "comment": (comment or "").strip()},
        )
        self._idempotency.save(subject, operation, key, stored)
        return stored

    def decide_validation(
        self,
        subject: str,
        ticket_id: int,
        validation_id: int,
        *,
        accept: bool,
        comment: str = "",
        viewer_email: str = "",
        idempotency_key: str | None,
    ) -> StoredResponse:
        key = _require_key(idempotency_key)
        action = "accept" if accept else "reject"
        operation = f"validation_{action}:{ticket_id}:{validation_id}"
        existing = self._idempotency.get(subject, operation, key)
        if existing is not None:
            return existing
        token = self._token(subject)
        detail = self._glpi.get_ticket(token, ticket_id, viewer_email=viewer_email)
        match = next((item for item in detail.validations if item.id == validation_id), None)
        if match is None:
            raise GlpiNotFound("Aprovação não encontrada.")
        if not match.mine_to_decide:
            raise GlpiForbidden("Só o aprovador designado pode decidir esta validação.")
        self._glpi.decide_ticket_validation(
            token,
            ticket_id,
            validation_id,
            accept=accept,
            comment=(comment or "").strip(),
        )
        refreshed = self._glpi.get_ticket(token, ticket_id, viewer_email=viewer_email)
        stored = StoredResponse(
            status_code=200,
            body={
                "id": validation_id,
                "status": 3 if accept else 4,
                "can_decide_validation": refreshed.can_decide_validation,
            },
        )
        self._idempotency.save(subject, operation, key, stored)
        return stored

    def _with_cycle_flags(self, token: str, detail: TicketDetail) -> TicketDetail:
        legacy_on = True
        enabled_fn = getattr(self._glpi, "legacy_cycle_enabled", None)
        if callable(enabled_fn):
            legacy_on = bool(enabled_fn())
        score: int | None = None
        comment = ""
        submitted = False
        if legacy_on and detail.requester_mine and detail.status_id == 6:
            try:
                row = self._glpi.get_ticket_satisfaction(token, detail.id)
            except GlpiFeatureDisabled:
                legacy_on = False
                row = None
            if row is not None:
                score, comment = row
                submitted = True
        can_accept, can_reject, can_sat = solicitante_cycle_flags(
            requester_mine=detail.requester_mine,
            status_id=detail.status_id,
            satisfaction_submitted=submitted,
            legacy_enabled=legacy_on,
        )
        return replace(
            detail,
            can_accept_solution=can_accept,
            can_reject_solution=can_reject,
            can_submit_satisfaction=can_sat,
            satisfaction=score,
            satisfaction_comment=comment,
        )

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
