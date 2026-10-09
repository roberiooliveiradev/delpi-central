"""Port for Helpdesk BFF writes — Bearer-forwarded, same-user parity.

Same ownership posture as ``HelpdeskReadPort``: the Helpdesk BFF owns the
Helpdesk contract, OAuth sessions, business revalidation, GLPI writes and
idempotency-key enforcement. TÉO forwards the authenticated user's own
Bearer plus a proposal-bound ``Idempotency-Key`` — never a service token,
never direct GLPI access, never a ticket mirror.
"""

from __future__ import annotations

from typing import Any, NamedTuple, Protocol

from tm_app.application.helpdesk.helpdesk_read_port import HelpdeskReadPort


class HelpdeskWritePort(Protocol):
    """Write contract of the Helpdesk BFF as consumed by TÉO.

    ``idempotency_key`` is proposal-bound and deterministic — the same
    proposal retried reaches the BFF under the same key, so the BFF replay
    store prevents duplicate side effects. All responses carry the stable
    identifiers needed for authoritative read-back.
    """

    def create_ticket(
        self,
        authorization: str,
        body: dict[str, Any],
        *,
        idempotency_key: str,
    ) -> dict[str, Any]:
        """POST /tickets → ``{"id": ticket_id}``."""
        ...

    def set_assignee(
        self,
        authorization: str,
        ticket_id: int,
        *,
        user_id: int,
        idempotency_key: str,
    ) -> dict[str, Any]:
        """PUT /tickets/{id}/assignee → ``{"user_id", "assigned_display_name"}``."""
        ...

    def add_followup(
        self,
        authorization: str,
        ticket_id: int,
        *,
        content: str,
        request_type_id: int | None,
        idempotency_key: str,
    ) -> dict[str, Any]:
        """POST /tickets/{id}/followups → ``{"id": followup_id}``."""
        ...

    def create_task(
        self,
        authorization: str,
        ticket_id: int,
        body: dict[str, Any],
        *,
        idempotency_key: str,
    ) -> dict[str, Any]:
        """POST /tickets/{id}/tasks → ``{"id": task_id, ...}``."""
        ...

    def add_solution(
        self,
        authorization: str,
        ticket_id: int,
        *,
        content: str,
        solution_type_id: int | None,
        idempotency_key: str,
    ) -> dict[str, Any]:
        """POST /tickets/{id}/solutions → ``{"id": solution_id, "status_id"}``."""
        ...

    def request_validation(
        self,
        authorization: str,
        ticket_id: int,
        body: dict[str, Any],
        *,
        idempotency_key: str,
    ) -> dict[str, Any]:
        """POST /tickets/{id}/validations → ``{"id": validation_id, ...}``."""
        ...

    def decide_solution(
        self,
        authorization: str,
        ticket_id: int,
        *,
        decision: str,
        content: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        """POST /tickets/{id}/solution/{accept|reject} → ``{"id","status_id"}``."""
        ...

    def submit_satisfaction(
        self,
        authorization: str,
        ticket_id: int,
        *,
        satisfaction: int,
        comment: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        """PUT /tickets/{id}/satisfaction → ``{"satisfaction","comment"}``."""
        ...

    def decide_validation(
        self,
        authorization: str,
        ticket_id: int,
        validation_id: int,
        *,
        decision: str,
        content: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        """POST /tickets/{id}/validations/{vid}/{accept|reject} → ``{"id","status"}``."""
        ...

    def delete_ticket(
        self,
        authorization: str,
        ticket_id: int,
        *,
        idempotency_key: str,
    ) -> dict[str, Any]:
        """DELETE /tickets/{id} → ``{"id","title","deleted","delete_semantics"}``.

        The BFF owns the GLPI trash operation (soft delete — never force
        purge) and its own internal read-back; a 2xx here already means
        the ticket left the same-user active view.
        """
        ...

    def unlink_glpi_session(
        self,
        authorization: str,
        *,
        idempotency_key: str,
    ) -> dict[str, Any]:
        """DELETE /auth/glpi/session → ``{"linked": false}``.

        Naturally idempotent at the BFF (unlink of an absent session is a
        no-op); the proposal-bound key is still forwarded for uniformity.
        """
        ...

    def upload_attachment(
        self,
        authorization: str,
        ticket_id: int,
        *,
        filename: str,
        content: bytes,
        mime: str,
        title: str | None,
        idempotency_key: str,
    ) -> dict[str, Any]:
        """POST /tickets/{id}/attachments (multipart) → ``{"document_id",
        "filename","mime"}``.

        The BFF owns GLPI Document creation, belongs-to-ticket validation,
        upload limits and idempotency replay; TÉO forwards bytes fetched
        from a platform-authorized file source — never an arbitrary URL.
        """
        ...


class HelpdeskFileSourcePort(Protocol):
    """Fetches bytes from a platform-authorized file reference (e.g. the
    ChatGPT ``openai/fileParams`` ``download_url``).

    Implementations enforce the host allowlist, HTTPS, redirect control
    and a byte cap — arbitrary model-supplied URLs fail closed.
    """

    def fetch(self, download_url: str) -> dict[str, Any]:
        """Return ``{"content": bytes, "mime": str, "filename": str}``
        or raise a typed error (validation/upstream)."""
        ...


class HelpdeskWriteStack(NamedTuple):
    """Composition bundle: canonical write port + read port for
    PREPARE current-state reads and ACT read-back verification."""

    read: HelpdeskReadPort
    write: HelpdeskWritePort
    files: HelpdeskFileSourcePort | None = None
