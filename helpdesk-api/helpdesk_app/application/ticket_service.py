from helpdesk_app.application.oauth_service import OAuthService
from helpdesk_app.application.ports import GlpiGateway, IdempotencyStore
from helpdesk_app.domain.errors import GlpiUnauthorized, GlpiValidation, LinkRequired, MissingIdempotencyKey
from helpdesk_app.domain.models import StoredResponse, TicketDetail, TicketSummary


class TicketService:
    def __init__(self, glpi: GlpiGateway, oauth: OAuthService, idempotency: IdempotencyStore):
        self._glpi = glpi
        self._oauth = oauth
        self._idempotency = idempotency

    def categories(self, subject: str):
        return self._glpi.list_categories(self._token(subject))

    def tickets(self, subject: str) -> list[TicketSummary]:
        return self._glpi.list_tickets(self._token(subject))

    def ticket(self, subject: str, ticket_id: int) -> TicketDetail:
        return self._glpi.get_ticket(self._token(subject), ticket_id)

    def create(
        self,
        subject: str,
        *,
        title: str,
        description: str,
        category_id: int,
        urgency_id: int,
        idempotency_key: str | None,
    ) -> StoredResponse:
        key = _require_key(idempotency_key)
        _validate_text(title, "title")
        _validate_text(description, "description")
        operation = "create_ticket"
        existing = self._idempotency.get(subject, operation, key)
        if existing is not None:
            return existing
        ticket_id = self._glpi.create_ticket(
            self._token(subject),
            title=title.strip(),
            description=description.strip(),
            category_id=category_id,
            urgency_id=urgency_id,
        )
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
        _validate_text(content, "content")
        operation = f"followup:{ticket_id}"
        existing = self._idempotency.get(subject, operation, key)
        if existing is not None:
            return existing
        followup_id = self._glpi.add_followup(
            self._token(subject), ticket_id, content.strip()
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
