"""Delegate — intenção de consulta de produto."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_assistant_content_service import (
    ChatAssistantContentService,
)
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)

from app.domain.services.chat_product_query_intent.chat_product_query_intent_content_service import (
    ChatProductQueryIntentContentService,
)
from app.domain.services.chat_product_query_intent.chat_product_query_intent_facade_access import (
    intent_service,
)
from app.domain.services.chat_product_query_intent.chat_product_query_intent_models import (
    ChatProductQueryIntent,
)
from app.domain.services.chat_product_query_intent.chat_product_query_intent_vocabulary import (
    ChatProductQueryIntentVocabulary as VOCAB,
)

_INTENT_CONTENT_BUNDLE = "product_query_intent"



class ChatProductQueryIntentCodeService:
    @classmethod
    def normalize_product_code(cls, raw: str) -> str:
        digits = re.sub(r"\D", "", str(raw or ""))

        if len(digits) >= 4:
            return digits

        return str(raw or "").strip()

    @classmethod
    def _is_example_product_code_token(cls, text: str, match: re.Match[str]) -> bool:
        prefix = text[max(0, match.start() - 64) : match.start()].lower()

        return bool(VOCAB.EXAMPLE_CODE_PREFIX_RE.search(prefix))

    @classmethod
    def is_plausible_product_code(cls, code: str | None) -> bool:
        normalized = str(code or "").strip()

        if not normalized:
            return False

        digits = re.sub(r"\D", "", normalized)

        if "." in normalized and len(digits) < 5:
            return False

        if len(digits) >= 4:
            return True

        if re.search(r"[-/,]", normalized):
            return False

        return len(digits) >= 3

    @classmethod
    def _is_specification_numeric_token(cls, token: str) -> bool:
        raw = str(token or "").strip()

        if VOCAB.SPECIFICATION_TOKEN_RE.search(raw):
            return True

        if re.search(r"[-/,]", raw):
            digits = re.sub(r"\D", "", raw)

            if len(digits) < 4:
                return True

        return False

    @classmethod
    def _is_file_size_token(cls, text: str, match: re.Match[str]) -> bool:
        token = str(match.group(0) or "").strip()

        if not re.fullmatch(r"\d+\.\d+", token):
            return False

        suffix = text[match.end() : min(len(text), match.end() + 20)].casefold()

        return bool(
            re.match(r"\s*(kb|mb|gb|bytes?|b|chunk)\b", suffix)
            or "chunk(s)" in suffix
        )

    @classmethod
    def _is_document_year_token(cls, text: str, match: re.Match[str]) -> bool:
        token = str(match.group(0) or "").strip()

        if not VOCAB.CALENDAR_YEAR_RE.match(token):
            return False

        suffix = text[match.end() : min(len(text), match.end() + 12)]

        return bool(re.match(r"\s*\.(?:docx|xlsx|pdf|txt|md|csv|pptx)\b", suffix, re.IGNORECASE))

    @classmethod
    def extract_product_code(cls, text: str | None) -> str | None:
        if ChatProductQueryIntentCodeService._looks_like_lmp_context(text):
            return None

        raw = str(text or "")

        for match in VOCAB.PRODUCT_CODE_RE.finditer(raw):
            token = match.group(0)

            if ChatProductQueryIntentCodeService._is_group_code_numeric_token(raw, match):
                continue

            if ChatProductQueryIntentCodeService._is_date_numeric_token(token):
                continue

            if ChatProductQueryIntentCodeService._is_calendar_year_token(raw, match):
                continue

            if ChatProductQueryIntentCodeService._is_document_year_token(raw, match):
                continue

            if ChatProductQueryIntentCodeService._is_specification_numeric_token(token):
                continue

            if ChatProductQueryIntentCodeService._is_example_product_code_token(raw, match):
                continue

            if ChatProductQueryIntentCodeService._is_phone_contact_token(raw, match):
                continue

            if ChatProductQueryIntentCodeService._is_file_size_token(raw, match):
                continue

            code = intent_service().normalize_product_code(token)

            if intent_service().is_plausible_product_code(code):
                return code

        return None

    @classmethod
    def _is_date_numeric_token(cls, token: str) -> bool:
        return bool(VOCAB.DATE_TOKEN_RE.match(str(token or "").strip()))

    @classmethod
    def _is_calendar_year_token(cls, text: str, match: re.Match[str]) -> bool:
        token = str(match.group(0) or "").strip()

        if not VOCAB.CALENDAR_YEAR_RE.match(token):
            return False

        prefix = text[max(0, match.start() - 32) : match.start()].lower()

        if re.search(
            r"(?:\bproduto|\bitem|\bc[oó]digo|\bcode|\brefer[eê]ncia)\s*$",
            prefix,
            flags=re.IGNORECASE,
        ):
            return False

        return True

    @classmethod
    def _is_phone_contact_token(cls, text: str, match: re.Match[str]) -> bool:
        token = str(match.group(0) or "").strip()
        window = text[max(0, match.start() - 18) : min(len(text), match.end() + 18)]

        if re.search(r"\(\s*\d{2}\s*\)\s*[\d\s\-–]{5,}", window):
            return True

        if re.fullmatch(r"\d{3,4}-\d{4}", token):
            return True

        digits = re.sub(r"\D", "", token)

        if len(digits) in {7, 8}:
            prefix = text[max(0, match.start() - 12) : match.start()]

            if ")" in prefix or re.search(r"\(\s*\d{2}", prefix):
                return True

        return False

    @classmethod
    def extract_product_group_code(cls, text: str | None) -> str | None:
        """Extrai código de grupo/família (ex.: «produtos 9026») — não é PA completo."""
        raw = str(text or "")

        if not raw:
            return None

        for pattern in ChatProductQueryIntentContentService._terms("productGroupCode", "patterns"):
            match = re.search(str(pattern), raw, flags=re.IGNORECASE)

            if not match:
                continue

            digits = re.sub(r"\D", "", str(match.group(1) or ""))

            if len(digits) == 4:
                return digits

        return None

    @classmethod
    def looks_like_production_schedule_membership_question(cls, message: str | None) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        return any(term in normalized for term in ChatProductQueryIntentContentService._terms("scheduleMembership", "terms"))

    @classmethod
    def resolve_schedule_product_group_code(cls,
        message: str | None,
        *,
        product_code: str | None = None,
    ) -> str | None:
        """Grupo para filtrar programação do dia (mensagem ou chip de 4 dígitos)."""
        return cls.resolve_schedule_product_filter_code(
            message,
            product_code=product_code,
        )

    @classmethod
    def resolve_schedule_product_filter_code(cls,
        message: str | None,
        *,
        product_code: str | None = None,
    ) -> str | None:
        """Prefixo de filtro na programação do dia (grupo 4 dígitos ou PA completo)."""
        group_code = intent_service().extract_product_group_code(message)

        if group_code:
            return group_code

        explicit = intent_service().extract_product_code(message) or str(product_code or "").strip()
        digits = re.sub(r"\D", "", explicit)

        if not digits:
            return None

        if intent_service().looks_like_production_schedule_membership_question(message):
            return digits

        if len(digits) == 4:
            return digits

        return None

    @classmethod
    def _is_group_code_numeric_token(cls, text: str, match: re.Match[str]) -> bool:
        """Evita confundir «grupo 1008» ou «produtos 9026» com código de produto."""
        token_digits = re.sub(r"\D", "", str(match.group(0) or ""))
        group_code = intent_service().extract_product_group_code(text)

        if group_code and group_code == token_digits:
            return True

        prefix = text[max(0, match.start() - 48) : match.start()].lower()

        if re.search(
            r"(?:\bgrupo|\bgroup_code|\bdo\s+grupo|\bpelo\s+grupo|\bde\s+grupo)\s*$",
            prefix,
            flags=re.IGNORECASE,
        ):
            return True

        if re.search(r"\bgrupo\s+de\s+produtos?\s*$", prefix, flags=re.IGNORECASE):
            return True

        if re.search(
            r"(?:\bprodutos?|\bitens?|\bpas?\b|\bfam[ií]lia)\s*$",
            prefix,
            flags=re.IGNORECASE,
        ) and len(token_digits) == 4:
            return True

        normalized = ChatMessageNormalizationService.normalize_for_matching(text)

        if "grupo" in normalized and re.search(
            rf"\bgrupo\s+{re.escape(match.group(0).lower())}\b",
            normalized,
        ):
            return True

        return False

    @classmethod
    def _looks_like_lmp_context(cls, text: str | None) -> bool:
        normalized = str(text or "").lower()

        return any(term in normalized for term in ChatProductQueryIntentContentService._terms("lmpContext"))

    @classmethod
    def extract_last_product_code(cls, text: str | None) -> str | None:
        raw = str(text or "")
        last_code: str | None = None

        for match in VOCAB.PRODUCT_CODE_RE.finditer(raw):
            if ChatProductQueryIntentCodeService._is_group_code_numeric_token(raw, match):
                continue

            if ChatProductQueryIntentCodeService._is_date_numeric_token(match.group(0)):
                continue

            if ChatProductQueryIntentCodeService._is_calendar_year_token(raw, match):
                continue

            if ChatProductQueryIntentCodeService._is_document_year_token(raw, match):
                continue

            if ChatProductQueryIntentCodeService._is_specification_numeric_token(match.group(0)):
                continue

            if ChatProductQueryIntentCodeService._is_example_product_code_token(raw, match):
                continue

            if ChatProductQueryIntentCodeService._is_phone_contact_token(raw, match):
                continue

            if ChatProductQueryIntentCodeService._is_file_size_token(raw, match):
                continue

            code = intent_service().normalize_product_code(match.group(0))

            if intent_service().is_plausible_product_code(code):
                last_code = code

        return last_code

    @classmethod
    def extract_last_product_code_from_messages(cls,
        previous_messages: list | None,
    ) -> str | None:
        from app.domain.services.chat_analysis_intent_service import (
            ChatAnalysisIntentService,
        )

        for item in reversed((previous_messages or [])[-16:]):
            metadata = intent_service()._message_metadata(item)

            for tool_call in reversed(metadata.get("toolCalls") or []):
                if not isinstance(tool_call, dict):
                    continue

                if str(tool_call.get("name") or "") != "execute_external_action":
                    continue

                tool_meta = tool_call.get("metadata")

                if not isinstance(tool_meta, dict) or not tool_meta.get("ok"):
                    continue

                code = ChatAnalysisIntentService.extract_product_code_from_tool_path(
                    str(tool_meta.get("path") or "")
                )

                if code and intent_service().is_plausible_product_code(code):
                    return code

            content = intent_service()._message_content(item)

            if intent_service()._message_field_role(item) == "assistant":
                lowered = ChatMessageNormalizationService.normalize_for_matching(content)

                if (
                    "informe o codigo" in lowered
                    or "informe o codigo do produto" in lowered
                    or ("codigo do produto" in lowered and "ex." in lowered)
                ):
                    continue

            code = intent_service().extract_product_code(content)

            if code:
                return code

        return None

