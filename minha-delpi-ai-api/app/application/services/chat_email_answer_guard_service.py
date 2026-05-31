"""Pós-processamento seguro de rascunhos de e-mail antes de persistir."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_email_intent_service import ChatEmailIntentService
from app.domain.services.chat_email_quality_validator import ChatEmailQualityValidator


class ChatEmailAnswerGuardService:
    @classmethod
    def apply(
        cls,
        answer: str | None,
        *,
        message: str | None = None,
        workspace_context: dict | None = None,
    ) -> tuple[str, dict[str, Any] | None]:
        if not answer:
            return answer or "", None

        if not (
            ChatEmailIntentService.is_email_writing(message)
            or (workspace_context or {}).get("emailWritingMode")
        ):
            return answer, None

        ctx = ChatEmailIntentService.extract_context(message)
        sanitized, fixes = ChatEmailQualityValidator.sanitize(
            answer,
            user_provided_signature=ctx.get("senderSignature"),
        )

        quality = ChatEmailQualityValidator.validate(
            sanitized,
            user_message=message,
            expected_tone=ctx.get("tone"),
            user_provided_signature=ctx.get("senderSignature"),
        )

        guard_meta: dict[str, Any] = {"emailGuard": {"fixesApplied": fixes, "quality": quality}}

        if fixes:
            guard_meta["emailGuard"]["sanitized"] = True

        hints = ChatEmailQualityValidator.build_remediation_hints(quality)

        if hints:
            guard_meta["emailGuard"]["remediationHints"] = hints

        return sanitized, guard_meta
