from typing import Protocol

from helpdesk_app.domain.models import (
    Attachment,
    Category,
    OAuthSession,
    PendingAuthorization,
    StoredResponse,
    TicketDetail,
    TicketListPage,
    TicketListQuery,
    TokenSet,
)


class GlpiGateway(Protocol):
    def authorization_url(self, *, state: str, code_challenge: str) -> str: ...

    def exchange_code(self, *, code: str, code_verifier: str) -> TokenSet: ...

    def refresh(self, refresh_token: str) -> TokenSet: ...

    def list_categories(self, access_token: str) -> list[Category]: ...

    def list_tickets(self, access_token: str, query: TicketListQuery) -> TicketListPage: ...

    def get_ticket(self, access_token: str, ticket_id: int, viewer_email: str = "") -> TicketDetail: ...

    def create_ticket(
        self,
        access_token: str,
        *,
        title: str,
        description: str,
        category_id: int,
        urgency_id: int,
    ) -> int: ...

    def add_ticket_observer(self, access_token: str, ticket_id: int, user_id: int) -> None: ...

    def add_followup(self, access_token: str, ticket_id: int, content: str) -> int: ...

    def download_attachment(self, access_token: str, document_id: int) -> tuple[bytes, str]: ...

    def ticket_owns_document(self, access_token: str, ticket_id: int, document_id: int) -> bool: ...

    def upload_ticket_document(
        self,
        access_token: str,
        *,
        ticket_id: int,
        filename: str,
        content: bytes,
        mime: str,
    ) -> Attachment: ...


class StateStore(Protocol):
    def save(self, *, state: str, subject: str, code_verifier: str, expires_at) -> None: ...

    def consume(self, state: str) -> PendingAuthorization | None: ...


class SessionStore(Protocol):
    def get(self, subject: str) -> OAuthSession | None: ...

    def save(self, session: OAuthSession) -> None: ...

    def delete(self, subject: str) -> None: ...


class IdempotencyStore(Protocol):
    def get(self, subject: str, operation: str, key: str) -> StoredResponse | None: ...

    def save(
        self,
        subject: str,
        operation: str,
        key: str,
        response: StoredResponse,
    ) -> None: ...
