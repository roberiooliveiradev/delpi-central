"""Validador de qualidade textual geral — Playbook 03 §26."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_text_correction_intent_service import (
    ChatTextCorrectionIntentService,
)
from app.domain.services.chat_text_task_service import ChatTextTaskService


class ChatTextQualityValidator:
    _INVENTED_SIGNATURE = re.compile(
        r"\b(diretor|gerente\s+de|ceo|cfo|coordenador\s+de)\b",
        re.IGNORECASE,
    )

    @classmethod
    def validate(
        cls,
        answer: str | None,
        *,
        message: str | None = None,
        workspace_context: dict | None = None,
    ) -> dict[str, Any]:
        text = (answer or "").strip()
        ctx = ChatTextTaskService.classify(message)
        subtype = ctx.get("subtype")
        checks: list[dict[str, str]] = []

        if subtype in {"text_correct", "text_rewrite", "text_formalize", "text_simplify"}:
            from app.domain.services.chat_text_correction_quality_validator import (
                ChatTextCorrectionQualityValidator,
            )

            correction = ChatTextCorrectionQualityValidator.validate(
                answer,
                user_message=message,
                subtype=subtype.replace("text_", "text_correct_")
                if subtype == "text_correct"
                else None,
                preserved_codes=ctx.get("preservedCodes"),
            )

            checks.extend(correction.get("checks") or [])

        if len(text) < 3:
            checks.append({"code": "empty_answer", "message": "Resposta sem texto utilizável."})

        for code in ctx.get("preservedCodes") or []:
            if code not in text:
                checks.append(
                    {
                        "code": "code_not_preserved",
                        "message": f"Código/termo ausente na resposta: {code}.",
                    }
                )

        if ctx.get("deliverFinalOnly") and len(text.split()) > 120:
            checks.append(
                {
                    "code": "over_explained",
                    "message": "Pedido era só versão final.",
                }
            )

        if subtype in {"text_email_create", "text_email_reply"} and "assunto" not in text.lower():
            if "subject:" not in text.lower():
                checks.append(
                    {
                        "code": "missing_subject",
                        "message": "E-mail sem linha de assunto sugerida.",
                    }
                )

        if cls._INVENTED_SIGNATURE.search(text) and not ChatTextCorrectionIntentService.extract_context(
            message
        ).get("senderSignature"):
            checks.append(
                {
                    "code": "invented_signature",
                    "message": "Possível cargo/assinatura inventada.",
                }
            )

        passed = len(checks) == 0

        return {
            "passed": passed,
            "checks": checks,
            "subtype": subtype,
            "checklist": cls.build_checklist(passed=passed),
        }

    @classmethod
    def build_checklist(cls, *, passed: bool) -> list[dict[str, bool]]:
        return [
            {"item": "Pedido textual atendido", "ok": passed},
            {"item": "Sentido preservado", "ok": passed},
            {"item": "Sem dados inventados", "ok": passed},
            {"item": "Códigos preservados", "ok": passed},
            {"item": "Pronto para copiar", "ok": passed},
        ]
