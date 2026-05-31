"""Confirmação antes de actions de escrita/críticas — Playbook 08."""

from __future__ import annotations

import re

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)

_SENSITIVE_SENSITIVITY = frozenset({"write", "destructive", "admin"})
_SENSITIVE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
_CONFIRM_MARKERS = (
    "confirmo",
    "pode executar",
    "pode prosseguir",
    "autorizo",
    "sim confirmo",
    "sim, confirmo",
    "pode enviar",
    "pode publicar",
    "pode excluir",
    "pode deletar",
    "pode apagar",
)
_WRITE_INTENT_MARKERS = (
    "exclu",
    "delet",
    "apag",
    "remov",
    "enviar e-mail",
    "enviar email",
    "mandar e-mail",
    "public",
    "atualiz",
    "cadastr",
    "alterar permiss",
    "gravar",
    "inserir",
    "criar registro",
)


class ChatWriteConfirmationService:
    @classmethod
    def action_requires_confirmation(cls, action: dict | None) -> bool:
        if not isinstance(action, dict):
            return False

        sensitivity = str(action.get("sensitivity") or "").lower()
        method = str(action.get("method") or "").upper()

        if sensitivity in _SENSITIVE_SENSITIVITY:
            return True

        if method in _SENSITIVE_METHODS and sensitivity != "read":
            return True

        return False

    @classmethod
    def message_requests_write(cls, message: str | None) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        return any(marker in normalized for marker in _WRITE_INTENT_MARKERS)

    @classmethod
    def user_confirmed(cls, message: str | None) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        if any(marker in normalized for marker in _CONFIRM_MARKERS):
            return True

        return bool(re.search(r"\bconfirm(o|a|ar|ado)\b", normalized))

    @classmethod
    def should_block_execution(
        cls,
        *,
        message: str | None,
        action: dict | None,
    ) -> bool:
        if not cls.action_requires_confirmation(action):
            return False

        if cls.user_confirmed(message):
            return False

        if cls.message_requests_write(message):
            return True

        sensitivity = str((action or {}).get("sensitivity") or "").lower()

        return sensitivity in {"destructive", "admin", "write"}

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
