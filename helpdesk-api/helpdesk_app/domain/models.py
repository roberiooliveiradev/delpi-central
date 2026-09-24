from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Actor:
    subject: str
    email: str = ""


@dataclass(frozen=True)
class PersonIdentity:
    user_id: int | None = None
    emails: tuple[str, ...] = ()


def same_person(left: PersonIdentity, right: PersonIdentity) -> bool:
    if left.user_id and right.user_id and left.user_id == right.user_id:
        return True
    return bool(set(left.emails) & set(right.emails))


@dataclass(frozen=True)
class Category:
    id: int
    name: str


@dataclass(frozen=True)
class CatalogUser:
    id: int
    display_name: str
    email: str = ""
    """Minha DELPI directory user_id (Keycloak UUID) when linked."""
    directory_user_id: str = ""
    has_photo: bool = False


@dataclass(frozen=True)
class Urgency:
    id: int
    name: str


@dataclass(frozen=True)
class TicketSummary:
    id: int
    title: str
    status: str
    category: str
    urgency: str
    updated_at: str
    created_at: str = ""
    assigned_display_name: str = ""
    requester_display_name: str = ""
    status_id: int | None = None
    solved_at: str = ""
    closed_at: str = ""
    sla_ttr: str = ""
    sla_tto: str = ""
    assigned_user_id: int | None = None


@dataclass(frozen=True)
class TicketListQuery:
    filter: str = ""
    start: int = 0
    limit: int = 21
    sort: str = "date_mod:desc"
    page: int = 1
    page_size: int = 20
    assignee_id: int | None = None
    """Original sort token from the API (`updated_at:desc`, `assigned:asc`, …)."""
    client_sort: str = "updated_at:desc"
    q: str = ""
    status: str = ""
    urgency_id: int | None = None
    category_id: int | None = None
    updated_from: str = ""
    updated_to: str = ""
    created_from: str = ""
    created_to: str = ""


@dataclass(frozen=True)
class TicketListPage:
    items: tuple[TicketSummary, ...]
    page: int
    page_size: int
    has_more: bool


@dataclass(frozen=True)
class TimelineEntry:
    id: int
    kind: str
    content: str
    created_at: str
    author_display_name: str
    author_identity: PersonIdentity = PersonIdentity()
    mine: bool = False
    content_html: str = ""


@dataclass(frozen=True)
class Attachment:
    document_id: int
    filename: str
    mime: str


@dataclass(frozen=True)
class TicketValidation:
    """GLPI Assistance Timeline Validation (approve / refuse)."""

    id: int
    status: int
    submission_comment: str = ""
    approval_comment: str = ""
    requested_approver_id: int | None = None
    mine_to_decide: bool = False


@dataclass(frozen=True)
class TicketDetail:
    id: int
    title: str
    status: str
    category: str
    urgency: str
    updated_at: str
    description: str
    timeline: tuple[TimelineEntry, ...]
    attachments: tuple[Attachment, ...] = ()
    created_at: str = ""
    requester_display_name: str = ""
    assigned_display_name: str = ""
    assigned_user_id: int | None = None
    requester_identity: PersonIdentity = PersonIdentity()
    requester_mine: bool = False
    status_id: int | None = None
    description_html: str = ""
    can_followup: bool = True
    can_assign: bool = False
    # H10 Branch B — solicitante cycle via legacy apirest (accept/reject/satisfaction).
    can_accept_solution: bool = False
    can_reject_solution: bool = False
    can_submit_satisfaction: bool = False
    satisfaction: int | None = None
    satisfaction_comment: str = ""
    # TicketValidation (HLAPI Timeline/Validation) — approver can decide when status=waiting.
    validations: tuple[TicketValidation, ...] = ()
    can_decide_validation: bool = False
    observers_display_name: str = ""
    solved_at: str = ""
    closed_at: str = ""
    sla_ttr: str = ""
    sla_tto: str = ""


@dataclass(frozen=True)
class TokenSet:
    access_token: str
    refresh_token: str
    expires_in: int


@dataclass(frozen=True)
class OAuthSession:
    subject: str
    access_token: str
    refresh_token: str
    access_expires_at: datetime


@dataclass(frozen=True)
class PendingAuthorization:
    subject: str
    code_verifier: str
    expires_at: datetime


@dataclass(frozen=True)
class StoredResponse:
    status_code: int
    body: dict
