"""Pós-processamento de respostas de correção textual."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_text_correction_intent_service import (
    ChatTextCorrectionIntentService,
)
from app.domain.services.chat_text_correction_quality_validator import (
    ChatTextCorrectionQualityValidator,
)


class ChatTextCorrectionAnswerGuardService:
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
            ChatTextCorrectionIntentService.is_text_correction(message)
            or (workspace_context or {}).get("textCorrectionMode")
        ):
            return answer, None

        ctx = ChatTextCorrectionIntentService.extract_context(message)
        subtype = ctx.get("subtype") or "text_correct_basic"
        sanitized = answer.strip()

        if ctx.get("deliverFinalOnly") or subtype == "text_correct_basic":
            sanitized = cls._trim_to_final_version(sanitized, subtype)

        quality = ChatTextCorrectionQualityValidator.validate(
            sanitized,
            user_message=message,
            subtype=subtype,
            preserved_codes=ctx.get("preservedCodes"),
        )

        guard_meta: dict[str, Any] = {
            "textCorrectionGuard": {"quality": quality},
        }

        return sanitized, guard_meta

    @classmethod
    def _trim_to_final_version(cls, text: str, subtype: str) -> str:
        if subtype in {"text_correct_explain", "text_correct_compare"}:
            return text

        lowered = text.lower()
        markers = (
            "segue a versão corrigida:",
            "segue a versão corrigida",
            "versão corrigida:",
        )

        for marker in markers:
            idx = lowered.find(marker)

            if idx >= 0:
                body = text[idx + len(marker) :].strip()

                if body:
                    return body.split("\n##")[0].strip()

        if "## versão corrigida" in lowered:
            parts = cls._section_after_heading(text, "versão corrigida")

            if parts:
                return parts

        return text

    @classmethod
    def _section_after_heading(cls, text: str, heading: str) -> str | None:
        match = re.search(
            rf"(?im)^#+\s*{re.escape(heading)}\s*$",
            text,
        )

        if not match:
            return None

        after = text[match.end() :].strip()
        next_heading = re.search(r"(?m)^#+\s+", after)

        if next_heading:
            return after[: next_heading.start()].strip()

        return after
