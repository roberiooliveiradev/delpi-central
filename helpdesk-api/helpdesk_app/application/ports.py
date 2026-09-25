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

    def list_request_types(self, access_token: str) -> list[Category]: ...

    def list_followup_templates(self, access_token: str): ...

    def list_solution_types(self, access_token: str) -> list[Category]: ...

    def list_solution_templates(self, access_token: str): ...

    def list_task_categories(self, access_token: str) -> list[Category]: ...

    def list_task_templates(self, access_token: str): ...

    def list_task_statuses(self): ...

    def list_groups(self, access_token: str) -> list[Category]: ...

    def list_validation_templates(self, access_token: str): ...

    def list_approval_steps(self, access_token: str) -> list[Category]: ...

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

    def add_ticket_assignee(self, access_token: str, ticket_id: int, user_id: int) -> None: ...

    def remove_ticket_assignee(self, access_token: str, ticket_id: int, user_id: int) -> None: ...

    def list_users(self, access_token: str, *, q: str = "", limit: int = 20): ...

    def list_technician_user_ids(self, access_token: str) -> set[int]: ...

    def find_user_by_email(self, access_token: str, email: str): ...

    def session_user_id(self, access_token: str) -> int | None: ...

    def can_assign_tickets(self, access_token: str) -> bool: ...

    def add_followup(
        self,
        access_token: str,
        ticket_id: int,
        content: str,
        *,
        request_type_id: int | None = None,
    ) -> int: ...

    def add_ticket_solution(
        self,
        access_token: str,
        ticket_id: int,
        content: str,
        *,
        solution_type_id: int | None = None,
    ) -> int: ...

    def add_ticket_task(
        self,
        access_token: str,
        ticket_id: int,
        content: str,
        *,
        state: int | None = None,
        duration_seconds: int | None = None,
        category_id: int | None = None,
        user_tech_id: int | None = None,
        group_tech_id: int | None = None,
        planned_begin: str | None = None,
        planned_end: str | None = None,
    ) -> int: ...

    def create_ticket_validation(
        self,
        access_token: str,
        ticket_id: int,
        *,
        approver_user_id: int | None = None,
        approver_type: str = "User",
        approver_id: int | None = None,
        comment: str = "",
    ) -> int: ...

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
        title: str | None = None,
    ) -> Attachment: ...

    def accept_ticket_solution(self, access_token: str, ticket_id: int, content: str = "") -> None: ...

    def reject_ticket_solution(self, access_token: str, ticket_id: int, content: str = "") -> None: ...

    def get_ticket_satisfaction(
        self, access_token: str, ticket_id: int
    ) -> tuple[int, str] | None: ...

    def submit_ticket_satisfaction(
        self,
        access_token: str,
        ticket_id: int,
        *,
        satisfaction: int,
        comment: str = "",
    ) -> None: ...

    def decide_ticket_validation(
        self,
        access_token: str,
        ticket_id: int,
        validation_id: int,
        *,
        accept: bool,
        comment: str = "",
    ) -> None: ...


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
