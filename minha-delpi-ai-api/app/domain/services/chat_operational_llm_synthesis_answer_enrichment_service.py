"""Pós-processamento canônico da prosa LLM operacional (código na abertura, anti-alucinação)."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_operational_llm_synthesis_context_content_service import (
    ChatOperationalLlmSynthesisContextContentService,
)
from app.domain.services.chat_operational_narrative_synthesis_service import (
    ChatOperationalNarrativeSynthesisService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)


class ChatOperationalLlmSynthesisAnswerEnrichmentService:
    _SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
    _MARKDOWN_TABLE_LINE_RE = re.compile(r"^\s*\|.*\|\s*$")
    _MARKDOWN_TABLE_SEPARATOR_RE = re.compile(r"^\s*\|?\s*:?-{2,}")

    @classmethod
    def finalize_answer(
        cls,
        answer: str | None,
        *,
        message: str | None,
        tool_calls: list | None,
        response_mode_effect: str | None = None,
    ) -> str:
        body = str(answer or "").strip()

        if not body or not cls._should_enrich(response_mode_effect, tool_calls):
            return str(answer or "")

        product_code = cls._resolve_product_code(message, tool_calls)

        if product_code:
            body = cls._ensure_product_code_in_opening(body, product_code)

        if cls._tool_calls_use_decoupled_panel(tool_calls):
            body = cls._strip_markdown_tables(body)

        body = cls._strip_contradictory_claims(body, tool_calls)

        if response_mode_effect == "llm_synthesis_brief":
            body = cls._trim_brief_prose(body)

        return body.strip()

    @classmethod
    def _trim_brief_prose(cls, answer: str) -> str:
        max_chars = ChatOperationalLlmSynthesisContextContentService.limit_int(
            "maxBriefProseChars",
            420,
        )
        body = str(answer or "").strip()

        if len(body) <= max_chars:
            return body

        trimmed = body[:max_chars].rstrip()

        if " " in trimmed:
            trimmed = trimmed.rsplit(" ", 1)[0].rstrip()

        return f"{trimmed}…" if trimmed else body[:max_chars]

    @classmethod
    def _tool_calls_use_decoupled_panel(cls, tool_calls: list | None) -> bool:
        if not isinstance(tool_calls, list):
            return False

        from app.domain.services.chat_presentation_prose_delivery_service import (
            ChatPresentationProseDeliveryService,
        )

        for tool_call in tool_calls:
            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata")

            if isinstance(metadata, dict) and ChatPresentationProseDeliveryService.is_llm_decoupled_metadata(
                metadata,
            ):
                return True

        return False

    @classmethod
    def _strip_markdown_tables(cls, answer: str) -> str:
        lines = str(answer or "").splitlines()
        kept: list[str] = []
        skipping_table = False

        for line in lines:
            stripped = line.strip()
            is_table_line = bool(cls._MARKDOWN_TABLE_LINE_RE.match(stripped))
            is_separator = bool(cls._MARKDOWN_TABLE_SEPARATOR_RE.match(stripped))

            if is_table_line or is_separator:
                skipping_table = True
                continue

            if skipping_table and not stripped:
                skipping_table = False
                continue

            skipping_table = False
            kept.append(line)

        collapsed = "\n".join(kept)
        collapsed = re.sub(r"\n{3,}", "\n\n", collapsed)

        return collapsed.strip()

    @classmethod
    def _should_enrich(
        cls,
        response_mode_effect: str | None,
        tool_calls: list | None,
    ) -> bool:
        if not ChatOperationalNarrativeSynthesisService.is_llm_synthesis_effect(
            response_mode_effect,
        ):
            return False

        if not isinstance(tool_calls, list):
            return False

        for tool_call in tool_calls:
            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata")

            if isinstance(metadata, dict) and metadata.get("ok"):
                return True

        return False

    @classmethod
    def _resolve_product_code(
        cls,
        message: str | None,
        tool_calls: list | None,
    ) -> str | None:
        code = ChatProductQueryIntentService.extract_product_code(message or "")

        if code:
            return code

        if not isinstance(tool_calls, list):
            return None

        for tool_call in tool_calls:
            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata")

            if not isinstance(metadata, dict):
                continue

            path_code = ChatAnalysisIntentService.extract_product_code_from_tool_path(
                str(metadata.get("path") or ""),
            )

            if path_code:
                return path_code

        return None

    @classmethod
    def _ensure_product_code_in_opening(cls, answer: str, product_code: str) -> str:
        normalized = ChatMessageNormalizationService.normalize_for_matching(answer)

        if product_code in normalized:
            return answer

        opening = ChatOperationalLlmSynthesisContextContentService.format_answer_enrichment(
            "productCodeOpening",
            productCode=product_code,
        ).strip()

        if not opening:
            opening = f"O produto **{product_code}**"

        lines = answer.splitlines()
        first = str(lines[0] or "").strip() if lines else ""

        if first.startswith("#"):
            rest = "\n".join(lines[1:]).strip()
            merged = f"{first}\n\n{opening}"

            if rest:
                merged = f"{merged}\n\n{rest}"

            return merged.strip()

        return f"{opening}\n\n{answer}".strip()

    @classmethod
    def _strip_contradictory_claims(cls, answer: str, tool_calls: list | None) -> str:
        if not cls._metadata_indicates_empty_sections(tool_calls):
            return answer

        patterns = [
            ChatMessageNormalizationService.normalize_for_matching(pattern)
            for pattern in ChatOperationalLlmSynthesisContextContentService.contradiction_patterns()
            if str(pattern or "").strip()
        ]

        if not patterns:
            return answer

        sentences = cls._SENTENCE_SPLIT_RE.split(answer.strip())
        kept: list[str] = []

        for sentence in sentences:
            text = str(sentence or "").strip()

            if not text:
                continue

            normalized = ChatMessageNormalizationService.normalize_for_matching(text)

            if any(pattern in normalized for pattern in patterns):
                continue

            kept.append(text)

        if not kept:
            return answer

        return " ".join(kept).strip()

    @classmethod
    def _metadata_indicates_empty_sections(cls, tool_calls: list | None) -> bool:
        signals = [
            ChatMessageNormalizationService.normalize_for_matching(signal)
            for signal in ChatOperationalLlmSynthesisContextContentService.empty_section_signals()
            if str(signal or "").strip()
        ]

        if not signals or not isinstance(tool_calls, list):
            return False

        for tool_call in tool_calls:
            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata")

            if not isinstance(metadata, dict):
                continue

            for chunk in cls._iter_metadata_text_chunks(metadata):
                normalized = ChatMessageNormalizationService.normalize_for_matching(chunk)

                if any(signal in normalized for signal in signals):
                    return True

        return False

    @classmethod
    def _iter_metadata_text_chunks(cls, metadata: dict[str, Any]):
        for key in ("dataCommentary", "dataAnswer"):
            node = metadata.get(key)

            if not isinstance(node, dict):
                continue

            for field in ("interpretation", "nextAction", "narrativeInsight", "summary"):
                text = str(node.get(field) or "").strip()

                if text:
                    yield text

            for list_key in ("highlights", "limitations", "attention"):
                items = node.get(list_key)

                if not isinstance(items, list):
                    continue

                for item in items:
                    if isinstance(item, dict):
                        text = str(
                            item.get("text")
                            or item.get("label")
                            or item.get("detail")
                            or "",
                        ).strip()
                    else:
                        text = str(item or "").strip()

                    if text:
                        yield text
