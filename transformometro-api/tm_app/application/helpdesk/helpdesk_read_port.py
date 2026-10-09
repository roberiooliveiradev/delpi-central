"""Port for Helpdesk BFF reads — Bearer-forwarded, user-parity.

Helpdesk demand is OBSERVED operational evidence owned by GLPI through
the Helpdesk BFF. TÉO never calls GLPI directly, never stores ticket
truth, and never receives GLPI/OAuth token material. Knowledge about
tickets is not authorization and not process truth.
"""

from __future__ import annotations

from typing import Any, Protocol

HELPDESK_READ_ACTIONS: tuple[str, ...] = (
    "session",
    "capabilities",
    "tickets",
    "ticket",
    "attachment",
    "catalog",
)

HELPDESK_CATALOG_KINDS: tuple[str, ...] = (
    "categories",
    "urgencies",
    "request_types",
    "users",
    "groups",
    "followup_templates",
    "solution_types",
    "solution_templates",
    "task_categories",
    "task_templates",
    "task_statuses",
    "validation_templates",
    "approval_steps",
)

TICKET_FILTER_KEYS: tuple[str, ...] = (
    "q",
    "status",
    "urgency_id",
    "category_id",
    "assignee_id",
    "updated_from",
    "updated_to",
    "created_from",
    "created_to",
    "sort",
    "page",
    "page_size",
)


class HelpdeskReadPort(Protocol):
    """Read contract of the Helpdesk BFF as consumed by TÉO.

    `authorization` is the authenticated user's own Bearer header value —
    never a service token.
    """

    def session(self, authorization: str) -> dict[str, Any]:
        """GLPI link/session state for the authenticated user."""
        ...

    def capabilities(self, authorization: str) -> dict[str, Any]:
        """Effective Helpdesk/GLPI capability flags for this session."""
        ...

    def tickets(
        self, authorization: str, filters: dict[str, Any]
    ) -> dict[str, Any]:
        """Paginated ticket list for the authenticated user."""
        ...

    def ticket(self, authorization: str, ticket_id: int) -> dict[str, Any]:
        """Ticket detail incl. timeline, attachments metadata, can_* flags."""
        ...

    def attachment(
        self, authorization: str, ticket_id: int, document_id: int
    ) -> dict[str, Any]:
        """Binary content of one ticket attachment — ``content`` bytes,
        ``mime`` and ``filename``. The BFF enforces document-belongs-to-
        ticket under the same-user OAuth session."""
        ...

    def catalog(
        self,
        authorization: str,
        catalog_kind: str,
        *,
        q: str | None = None,
        purpose: str | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """Helpdesk catalog list (categories, urgencies, users, ...)."""
        ...
