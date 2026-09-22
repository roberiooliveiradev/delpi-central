"""Confirmação antes de actions de escrita/críticas — Playbook 08 / F3."""

from __future__ import annotations

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)

_SENSITIVE_SENSITIVITY = frozenset({"write", "destructive", "admin"})
_SENSITIVE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
_PARALLEL_SAFE_SENSITIVITY = frozenset({"read", "sql", "export"})
_SAFE_READ_METHODS = frozenset({"GET", "HEAD"})


class ChatWriteConfirmationService:
    @classmethod
    def _confirm_markers(cls) -> tuple[str, ...]:
        return tuple(
            ExternalActionResponseContentService.list("security", "confirmMarkers")
        )

    @classmethod
    def _write_intent_markers(cls) -> tuple[str, ...]:
        return tuple(
            ExternalActionResponseContentService.list("security", "writeIntentMarkers")
        )

    @classmethod
    def action_requires_confirmation(cls, action: dict | None) -> bool:
        """True when selection and execution must wait for user confirm.

        F3 — aligned with OpenAPI-first bridge: parallel-safe reads (GET/HEAD,
        sql/export) never require write confirmation. Explicit
        ``requiresConfirmation: true`` on the action forces confirmation.
        """
        if not isinstance(action, dict):
            return False

        if action.get("requiresConfirmation") is True:
            return True

        if cls.is_parallel_safe_read(action):
            return False

        sensitivity = str(action.get("sensitivity") or "").lower()
        method = str(action.get("method") or "").upper()

        if sensitivity in _SENSITIVE_SENSITIVITY:
            return True

        if method in _SENSITIVE_METHODS and sensitivity != "read":
            return True

        return False

    @classmethod
    def is_parallel_safe_read(cls, action: dict | None) -> bool:
        """True when the action can run concurrently with other independent reads.

        Writes/destructive stay serial. GET/HEAD and read/sql/export (incl. POST SQL)
        are eligible — aligned to OpenAPI import sensitivity, not agent flags.
        """
        if not isinstance(action, dict):
            return False

        sensitivity = str(action.get("sensitivity") or "").lower()
        method = str(action.get("method") or "").upper()

        if sensitivity in _SENSITIVE_SENSITIVITY:
            return False

        if method in _SAFE_READ_METHODS:
            return True

        return sensitivity in _PARALLEL_SAFE_SENSITIVITY

    @classmethod
    def message_requests_write(cls, message: str | None) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        return any(marker in normalized for marker in cls._write_intent_markers())

    @classmethod
    def user_confirmed(cls, message: str | None) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        if any(marker in normalized for marker in cls._confirm_markers()):
            return True

        return bool(ExternalActionResponseContentService.confirm_pattern().search(normalized))

    @classmethod
    def should_block_execution(
        cls,
        *,
        message: str | None,
        action: dict | None,
    ) -> bool:
        """F3 — same rule as OpenAPI-first selection bridge.

        ``action_requires_confirmation(action) and not user_confirmed(message)``.
        """
        if not cls.action_requires_confirmation(action):
            return False

        if cls.user_confirmed(message):
            return False

        return True

    @classmethod
    def confirmation_prompt(cls, action: dict | None) -> str:
        summary = str((action or {}).get("summary") or "").strip()
        path = str((action or {}).get("path") or "").strip()
        label = summary or path or "ação sensível"

        template = ExternalActionResponseContentService.get(
            "security",
            "writeConfirmationRequired",
        )

        if "{action}" in template:
            return template.format(action=label)

        return f"{template}\n\n**Ação:** {label}"
