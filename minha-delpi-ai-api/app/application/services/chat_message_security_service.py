import hashlib
from uuid import UUID

from app.domain.exceptions.chat_exceptions import InvalidChatSessionInputError
from app.domain.exceptions.security_exceptions import ChatInputSecurityError
from app.domain.ports.audit_repository_port import AuditRepositoryPort
from app.domain.services.chat_input_security_service import (
    ChatInputSecurityResult,
    ChatInputSecurityService,
)
from app.infrastructure.config.settings import Settings


class ChatMessageSecurityService:
    def __init__(
        self,
        input_security_service: ChatInputSecurityService | None = None,
        audit_repository: AuditRepositoryPort | None = None,
    ):
        self.input_security_service = input_security_service or ChatInputSecurityService()
        self.audit_repository = audit_repository

    def secure_message(
        self,
        value: str,
        *,
        user_id: UUID | None = None,
        context: str | None = None,
        source: str = "chat",
    ) -> str:
        if not isinstance(value, str):
            raise InvalidChatSessionInputError("Message must be a string")

        analysis = self.input_security_service.analyze(value)
        normalized = analysis.sanitized.strip()

        if not normalized:
            raise InvalidChatSessionInputError("Message is required")

        if analysis.blocked:
            self._log_security_event(
                user_id=user_id,
                action="security.input.blocked",
                message=normalized,
                context=context,
                analysis=analysis,
                source=source,
            )
            raise ChatInputSecurityError(
                analysis.block_reason or "Message blocked by security policy",
                flags=list(analysis.flags),
                risk_score=analysis.risk_score,
            )

        if analysis.flagged:
            self._log_security_event(
                user_id=user_id,
                action="security.input.flagged",
                message=normalized,
                context=context,
                analysis=analysis,
                source=source,
            )

        return normalized

    def scan_message(self, value: str, *, source: str = "admin") -> dict:
        if not isinstance(value, str):
            raise InvalidChatSessionInputError("Message must be a string")

        analysis = self.input_security_service.analyze(value)

        return {
            "source": source,
            "analysis": self._serialize_analysis(analysis),
            "wouldBlock": analysis.blocked,
            "wouldFlag": analysis.flagged,
            "config": self.input_security_service.build_config(),
        }

    def _log_security_event(
        self,
        *,
        user_id: UUID | None,
        action: str,
        message: str,
        context: str | None,
        analysis: ChatInputSecurityResult,
        source: str,
    ) -> None:
        if not self.audit_repository:
            return

        self.audit_repository.log(
            user_id=user_id,
            action=action,
            prompt_hash=self._hash_prompt(message),
            context=context,
            metadata={
                "source": source,
                "riskScore": analysis.risk_score,
                "riskLevel": analysis.risk_level,
                "flags": list(analysis.flags),
                "originalLength": analysis.original_length,
                "sanitizedLength": analysis.sanitized_length,
                "mode": Settings.CHAT_INPUT_SECURITY_MODE,
            },
        )

    def _serialize_analysis(self, analysis: ChatInputSecurityResult) -> dict:
        return {
            "sanitizedPreview": analysis.sanitized[:240],
            "originalLength": analysis.original_length,
            "sanitizedLength": analysis.sanitized_length,
            "riskScore": analysis.risk_score,
            "riskLevel": analysis.risk_level,
            "flags": list(analysis.flags),
            "blocked": analysis.blocked,
            "flagged": analysis.flagged,
            "blockReason": analysis.block_reason,
        }

    @staticmethod
    def _hash_prompt(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()
