"""Subintenções e contexto para correção/revisão de texto (chat base)."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_email_intent_service import ChatEmailIntentService
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)
from app.domain.services.chat_text_task_intent_service import ChatTextTaskIntentService


class ChatTextCorrectionIntentService:
    _CORRECTION_LEADS = (
        r"\bcorrij",
        r"\brevise\b",
        r"\bortografia\b",
        r"\bgramática\b",
        r"\bgramatica\b",
        r"\bpontuação\b",
        r"\bpontuacao\b",
        r"\barrume\s+o\s+portugu",
        r"\bverifique\s+se\s+.*\bestá\s+bom",
        r"\bverifique\s+se\s+.*\besta\s+bom",
    )

    _SUBTYPE_PATTERNS: dict[str, tuple[str, ...]] = {
        "text_correct_compare": (
            r"\bantes\s+e\s+depois\b",
            r"\bmostre\s+.*\bantes\b",
            r"\bcompar(a|e)\b.*\bvers",
        ),
        "text_correct_explain": (
            r"\bexplique\b",
            r"\bo\s+que\s+mudou\b",
            r"\bmostre\s+.*\baltera",
        ),
        "text_correct_preserve_style": (
            r"\bsem\s+mudar\b.*\bestilo",
            r"\bmantendo\b.*\bestilo",
            r"\bpreserve\b.*\bestilo",
            r"\bapenas\s+os\s+erros\b",
            r"\bsó\s+os\s+erros\b",
        ),
        "text_correct_formal": (
            r"\bdeixe\b.*\bmais\s+formal",
            r"\bmais\s+formal\b",
            r"\bformalize\b",
        ),
        "text_correct_simple": (
            r"\bdeixe\b.*\bmais\s+simples",
            r"\bmais\s+simples\b",
            r"\bsimplifi",
        ),
        "text_correct_professional": (
            r"\bmais\s+profissional\b",
            r"\btom\s+corporativ",
            r"\btexto\s+profissional\b",
        ),
        "text_correct_clear": (
            r"\bdeixe\b.*\bmais\s+claro",
            r"\bmais\s+claro\b",
            r"\bmelhor(e|ar)\b.*\bclareza",
            r"\bclareza\b",
        ),
        "text_review_quality": (
            r"\bverifique\s+se\b",
            r"\bestá\s+bom\b",
            r"\besta\s+bom\b",
            r"\btexto\s+está\s+adequado\b",
        ),
        "text_rewrite": (
            r"\breescrev",
            r"\breformul",
        ),
    }

    _TONE_PATTERNS: dict[str, tuple[str, ...]] = {
        "formal": (r"\bformal\b",),
        "professional": (r"\bprofissional\b", r"\bcorporativ"),
        "executive": (r"\bexecutiv",),
        "cordial": (r"\bcordial\b", r"\beducad"),
        "firm": (r"\bfirme\b", r"\bassertiv"),
        "simple": (r"\bsimples\b", r"\bdireto\b"),
        "technical": (r"\btécnico\b", r"\btecnico\b",),
    }

    _TEXT_AFTER_COLON = re.compile(
        r"(?:corrij[ao]?|revise|melhor[ae]?|reescrev[ae]?|deixe)\s*(?:este\s+texto|o\s+texto|isso)?\s*:\s*(.+)$",
        re.IGNORECASE | re.DOTALL,
    )

    @classmethod
    def is_text_correction(cls, message: str | None) -> bool:
        if ChatEmailIntentService.is_email_writing(message):
            return False

        if not ChatTextTaskIntentService.is_pure_text_task(message):
            return False

        normalized = (message or "").strip().lower()

        if len(normalized) < 4:
            return False

        category = ChatTextTaskIntentService.classify(message)

        if category == "correct":
            return True

        if cls.classify_subtype(message):
            return True

        if category == "rewrite" and any(
            re.search(pattern, normalized) for pattern in cls._CORRECTION_LEADS
        ):
            return True

        if category == "tone_adjust" and re.search(
            r"\b(corrij|revise|texto)\b", normalized
        ):
            return True

        return False

    @classmethod
    def classify_subtype(cls, message: str | None) -> str | None:
        normalized = (message or "").strip().lower()

        if len(normalized) < 4:
            return None

        if ChatEmailIntentService.message_mentions_email(message):
            return None

        ordered = (
            "text_correct_compare",
            "text_correct_explain",
            "text_correct_preserve_style",
            "text_correct_formal",
            "text_correct_simple",
            "text_correct_professional",
            "text_correct_clear",
            "text_review_quality",
            "text_rewrite",
        )

        for subtype in ordered:
            patterns = cls._SUBTYPE_PATTERNS.get(subtype) or ()
            if any(re.search(pattern, normalized) for pattern in patterns):
                return subtype

        if ChatTextTaskIntentService.classify(message) == "correct":
            return "text_correct_basic"

        if ChatTextTaskIntentService.classify(message) == "rewrite" and any(
            re.search(pattern, normalized) for pattern in cls._CORRECTION_LEADS
        ):
            return "text_correct_professional"

        return None

    @classmethod
    def extract_context(cls, message: str | None) -> dict[str, Any]:
        text = (message or "").strip()
        normalized = text.lower()
        subtype = cls.classify_subtype(message) or "text_correct_basic"
        tone = cls._detect_tone(normalized)
        source_text = cls.extract_source_text(message)
        codes = cls._extract_preserved_codes(text)
        preserve_style = subtype == "text_correct_preserve_style" or bool(
            re.search(r"\bsem\s+mudar\b", normalized)
        )
        explain = subtype in {"text_correct_explain", "text_correct_compare"}
        deliver_final_only = bool(
            re.search(
                r"\b(só|somente|apenas)\s+(a\s+)?versão\s+final\b",
                normalized,
            )
            or re.search(r"\bentregue\s+só\b", normalized)
        )

        return {
            "type": "correction",
            "subtype": subtype,
            "source": "user_message",
            "sourceText": source_text,
            "preserveMeaning": True,
            "preserveStyle": preserve_style,
            "tone": tone,
            "explainChanges": explain,
            "deliverFinalOnly": deliver_final_only,
            "containsTechnicalTerms": bool(codes) or bool(
                re.search(r"\bBOM\b|\bOV\b|\bDELPI\b", text, re.IGNORECASE)
            ),
            "preservedCodes": codes,
            "changedMeaningRisk": False,
        }

    @classmethod
    def extract_source_text(cls, message: str | None) -> str | None:
        text = (message or "").strip()

        if not text:
            return None

        match = cls._TEXT_AFTER_COLON.search(text)

        if match:
            body = (match.group(1) or "").strip()
            return body[:8000] if body else None

        if text.lower().startswith(("corrija", "corrigir", "revise")):
            stripped = re.sub(
                r"^(corrij[ao]?|corrigir|revise)\s*(este\s+texto|o\s+texto)?\s*",
                "",
                text,
                flags=re.IGNORECASE,
            ).strip()

            if stripped and stripped != text:
                return stripped[:8000]

        return None

    @classmethod
    def build_text_task_metadata(
        cls,
        *,
        message: str | None,
        answer: str | None = None,
    ) -> dict[str, Any] | None:
        if not cls.is_text_correction(message):
            return None

        ctx = cls.extract_context(message)
        ctx["suggestions"] = [
            "Deixar mais formal",
            "Deixar mais curto",
            "Mostrar alterações",
            "Transformar em e-mail",
        ]

        if answer and ctx.get("subtype") == "text_review_quality":
            lowered = answer.lower()
            ctx["reviewPassed"] = "adequad" in lowered or "está bom" in lowered

        return {"textTask": ctx}

    @classmethod
    def _detect_tone(cls, normalized: str) -> str | None:
        for tone, patterns in cls._TONE_PATTERNS.items():
            if any(re.search(pattern, normalized) for pattern in patterns):
                return tone

        return None

    @classmethod
    def _extract_preserved_codes(cls, text: str) -> list[str]:
        codes: list[str] = []
        seen: set[str] = set()

        product = ChatProductQueryIntentService.extract_product_code(text)

        if product and product not in seen:
            seen.add(product)
            codes.append(product)

        for match in re.finditer(r"\b\d{4,12}\b", text):
            code = match.group(0)

            if code not in seen:
                seen.add(code)
                codes.append(code)

        return codes[:20]
