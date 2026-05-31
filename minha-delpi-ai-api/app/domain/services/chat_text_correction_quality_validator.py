"""Validação de respostas de correção textual."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_text_correction_intent_service import (
    ChatTextCorrectionIntentService,
)


class ChatTextCorrectionQualityValidator:
    _INVENTED_COMMITMENT = re.compile(
        r"\b(garantimos|confirmamos\s+que|prazo\s+de\s+\d+\s+dias)\b",
        re.IGNORECASE,
    )

    @classmethod
    def validate(
        cls,
        answer: str | None,
        *,
        user_message: str | None = None,
        subtype: str | None = None,
        preserved_codes: list[str] | None = None,
    ) -> dict[str, Any]:
        text = (answer or "").strip()
        checks: list[dict[str, str]] = []
        ctx = ChatTextCorrectionIntentService.extract_context(user_message)
        resolved_subtype = subtype or ctx.get("subtype") or "text_correct_basic"
        codes = preserved_codes or ctx.get("preservedCodes") or []

        if len(text) < 3:
            checks.append(
                {"code": "empty_answer", "message": "Resposta sem texto corrigido utilizável."}
            )

        if not cls._looks_like_correction_output(text, resolved_subtype):
            checks.append(
                {
                    "code": "no_corrected_text",
                    "message": "Resposta não entrega versão corrigida clara.",
                }
            )

        for code in codes:
            if code not in text:
                checks.append(
                    {
                        "code": "code_altered",
                        "message": f"Código ou valor preservado ausente na resposta: {code}.",
                    }
                )

        if cls._INVENTED_COMMITMENT.search(text):
            checks.append(
                {
                    "code": "invented_commitment",
                    "message": "Possível compromisso ou prazo inventado.",
                }
            )

        if ctx.get("deliverFinalOnly") and cls._over_explained(text):
            checks.append(
                {
                    "code": "over_explained",
                    "message": "Usuário pediu só versão final; explicação longa demais.",
                }
            )

        if resolved_subtype == "text_correct_basic" and cls._over_explained(text):
            checks.append(
                {
                    "code": "over_explained_basic",
                    "message": "Correção simples não deve explicar em excesso.",
                }
            )

        return {
            "passed": len(checks) == 0,
            "checks": checks,
            "subtype": resolved_subtype,
        }

    @classmethod
    def _looks_like_correction_output(cls, text: str, subtype: str) -> bool:
        lowered = text.lower()

        if subtype == "text_correct_compare":
            return "antes" in lowered and "depois" in lowered

        if subtype == "text_correct_explain":
            return len(text) > 20 and (
                "versão corrigida" in lowered or "ajustes" in lowered or "##" in text
            )

        if subtype == "text_review_quality":
            return len(text) > 15

        markers = (
            "segue a versão",
            "versão corrigida",
            "texto corrigido",
        )

        if any(marker in lowered for marker in markers):
            return True

        lines = [line.strip() for line in text.splitlines() if line.strip()]

        return len(lines) >= 1 and len(text) >= 8

    @classmethod
    def _over_explained(cls, text: str) -> bool:
        lowered = text.lower()

        if text.count("##") >= 2:
            return True

        if lowered.count("- ") >= 6:
            return True

        return len(text) > 1200 and "ajustes" in lowered
