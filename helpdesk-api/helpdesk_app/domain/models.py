from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Actor:
    subject: str


@dataclass(frozen=True)
class Category:
    id: int
    name: str


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


@dataclass(frozen=True)
class TimelineEntry:
    id: int
    kind: str
    content: str
    created_at: str
    author_display_name: str


@dataclass(frozen=True)
class Attachment:
    document_id: int
    filename: str
    mime: str


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
