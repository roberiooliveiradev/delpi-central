"""Validação canônica — síntese LLM distinta do template, com contexto e modos diferenciados."""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from typing import Any

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)
from app.domain.services.chat_response_mode_synthesis_quality_content_service import (
    ChatResponseModeSynthesisQualityContentService,
)
from app.domain.services.chat_tool_context_presentation_service import (
    ChatToolContextPresentationService,
)

_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9./%-]{3,}", re.IGNORECASE)


class ChatResponseModeSynthesisQualityService:
    @classmethod
    def evaluate_turn(
        cls,
        *,
        mode: str,
        question: str,
        content: str,
        assistant_metadata: dict[str, Any] | None,
        elapsed_sec: float | None = None,
    ) -> list[str]:
        gaps: list[str] = []
        metadata = assistant_metadata if isinstance(assistant_metadata, dict) else {}
        pipeline = ((metadata.get("intelligence") or {}).get("pipeline") or {})
        body = str(content or "").strip()
        normalized_mode = str(mode or "normal").strip().lower()
        tool_calls = metadata.get("toolCalls") if isinstance(metadata.get("toolCalls"), list) else []

        gaps.extend(cls._evaluate_pipeline(pipeline, normalized_mode))
        gaps.extend(cls._evaluate_answer_shape(body, normalized_mode, elapsed_sec))
        gaps.extend(cls._evaluate_prose_decoupling(tool_calls, pipeline))
        gaps.extend(cls._evaluate_not_template_clone(body, tool_calls))
        gaps.extend(cls._evaluate_synthesis_coherence(body, question, tool_calls))

        return gaps

    @classmethod
    def evaluate_synthesis_coherence(
        cls,
        *,
        mode: str,
        question: str,
        content: str,
        tool_calls: list[dict[str, Any]] | None,
    ) -> list[str]:
        return cls._evaluate_synthesis_coherence(
            str(content or "").strip(),
            question,
            tool_calls if isinstance(tool_calls, list) else None,
        )

    @classmethod
    def _evaluate_synthesis_coherence(
        cls,
        content: str,
        question: str,
        tool_calls: list[dict[str, Any]] | None,
    ) -> list[str]:
        gaps: list[str] = []

        if not content:
            gaps.append(
                ChatResponseModeSynthesisQualityContentService.coherence_gap(
                    "emptyAnswer",
                    default="resposta vazia após síntese LLM",
                ),
            )
            return gaps

        gaps.extend(cls._evaluate_context_and_assertiveness(content, question, tool_calls))
        gaps.extend(cls._evaluate_deflection(content))
        gaps.extend(cls._evaluate_hallucination_markers(content))
        gaps.extend(cls._evaluate_sparse_numbered_lists(content))
        gaps.extend(cls._evaluate_repeated_sentences(content))

        return gaps

    @classmethod
    def _evaluate_repeated_sentences(cls, content: str) -> list[str]:
        from app.domain.services.chat_message_normalization_service import (
            ChatMessageNormalizationService,
        )

        sentences = re.split(r"(?<=[.!?])\s+", content.strip())
        seen: set[str] = set()
        repeats = 0

        min_sentence_chars = ChatResponseModeSynthesisQualityContentService.coherence_limit_int(
            "repeatedSentenceMinChars",
            default=48,
        )
        key_chars = ChatResponseModeSynthesisQualityContentService.coherence_limit_int(
            "repeatedSentenceKeyChars",
            default=160,
        )
        min_repeats = ChatResponseModeSynthesisQualityContentService.coherence_limit_int(
            "minRepeatedSentences",
            default=1,
        )

        for sentence in sentences:
            text = str(sentence or "").strip()

            if len(text) < min_sentence_chars:
                continue

            key = ChatMessageNormalizationService.normalize_for_matching(text)[:key_chars]

            if key in seen:
                repeats += 1
                continue

            seen.add(key)

        if repeats >= min_repeats:
            return [
                ChatResponseModeSynthesisQualityContentService.coherence_gap(
                    "repeatedSentences",
                    default="resposta com frases repetidas",
                ),
            ]

        return []

    @classmethod
    def _evaluate_sparse_numbered_lists(cls, content: str) -> list[str]:
        sparse_lines = 0
        patterns = ChatResponseModeSynthesisQualityContentService.sparse_list_patterns()
        min_lines = ChatResponseModeSynthesisQualityContentService.coherence_limit_int(
            "sparseListMinLines",
            default=2,
        )

        for line in content.splitlines():
            stripped = line.strip()

            if not stripped:
                continue

            if any(pattern.search(stripped) for pattern in patterns):
                sparse_lines += 1

        if sparse_lines >= min_lines:
            return [
                ChatResponseModeSynthesisQualityContentService.coherence_gap(
                    "sparseNumberedList",
                    default="lista numerada com itens vazios ou esparsos",
                ),
            ]

        return []

    @classmethod
    def evaluate_mode_ladder(cls, results: list[dict[str, Any]]) -> list[str]:
        gaps: list[str] = []

        if len(results) < 2:
            return gaps

        by_mode = {str(item.get("mode") or ""): item for item in results}
        required_pairs = (("fast", "normal"), ("normal", "thinker"))
        min_distance = ChatResponseModeSynthesisQualityContentService.mode_ladder_float(
            "minPairwiseContentDistance",
            default=0.06,
        )

        for left_mode, right_mode in required_pairs:
            left = by_mode.get(left_mode) or {}
            right = by_mode.get(right_mode) or {}
            left_text = cls._normalize_compare(str(left.get("content") or ""))
            right_text = cls._normalize_compare(str(right.get("content") or ""))

            if not left_text or not right_text:
                continue

            distance = 1.0 - SequenceMatcher(None, left_text, right_text).ratio()

            if distance < min_distance:
                gaps.append(
                    f"{left_mode} vs {right_mode}: respostas equivalentes "
                    f"(distância {distance:.2f} < {min_distance:.2f})"
                )

        fast = by_mode.get("fast") or {}
        normal = by_mode.get("normal") or {}

        fast_chars = int(fast.get("chars") or len(str(fast.get("content") or "")))
        normal_chars = int(normal.get("chars") or len(str(normal.get("content") or "")))
        fast_direct = bool(fast.get("directResponse"))
        normal_direct = bool(normal.get("directResponse"))

        if fast_chars and normal_chars and not (fast_direct and not normal_direct):
            ratio_limit = ChatResponseModeSynthesisQualityContentService.mode_ladder_float(
                "fastMaxCharsVsNormalRatio",
                default=1.05,
            )

            if fast_chars > normal_chars * ratio_limit:
                gaps.append(
                    "modo Rápida deveria ser mais curto que Normal "
                    f"({fast_chars} vs {normal_chars} chars)"
                )

        fast_elapsed = float(fast.get("elapsedSec") or 0.0)
        normal_elapsed = float(normal.get("elapsedSec") or 0.0)
        both_commentary_direct = bool(fast.get("directResponse")) and bool(
            normal.get("directResponse")
        )

        if fast_elapsed and normal_elapsed and not both_commentary_direct:
            elapsed_ratio_limit = ChatResponseModeSynthesisQualityContentService.mode_ladder_float(
                "fastMaxElapsedVsNormalRatio",
                default=1.25,
            )

            if fast_elapsed > normal_elapsed * elapsed_ratio_limit:
                gaps.append(
                    "modo Rápida demorou desproporcionalmente vs Normal "
                    f"({fast_elapsed}s vs {normal_elapsed}s)"
                )

            if normal_elapsed + 5.0 < fast_elapsed and normal_chars < fast_chars * 0.85:
                gaps.append(
                    "modo Normal ficou mais rápido que Rápida sem resposta mais rica "
                    f"({normal_elapsed}s vs {fast_elapsed}s; {normal_chars} vs {fast_chars} chars)"
                )

        return gaps

    @classmethod
    def extract_template_markdown(cls, tool_calls: list[dict[str, Any]] | None) -> str:
        if not isinstance(tool_calls, list):
            return ""

        return ChatToolContextPresentationService.build_authorized_answer_from_tool_calls(
            tool_calls
        ) or ""

    @classmethod
    def extract_context_tokens(cls, tool_calls: list[dict[str, Any]] | None) -> set[str]:
        if not isinstance(tool_calls, list):
            return set()

        tokens: set[str] = set()
        stopwords = ChatResponseModeSynthesisQualityContentService.generic_context_stopwords()
        min_len = ChatResponseModeSynthesisQualityContentService.limit_int(
            "minContextTokenLength",
            default=4,
        )

        for tool_call in tool_calls:
            metadata = tool_call.get("metadata")

            if not isinstance(metadata, dict):
                continue

            cls._collect_tokens_from_object(metadata.get("dataAnswer"), tokens, stopwords, min_len)
            cls._collect_tokens_from_object(metadata.get("humanizedSummary"), tokens, stopwords, min_len)
            cls._collect_tokens_from_object(metadata.get("kpiPresentation"), tokens, stopwords, min_len)

            for table in metadata.get("tablePresentations") or []:
                if not isinstance(table, dict):
                    continue

                cls._collect_tokens_from_object(table.get("rows"), tokens, stopwords, min_len)
                cls._collect_tokens_from_object(table.get("title"), tokens, stopwords, min_len)

            cls._collect_tokens_from_object(metadata.get("path"), tokens, stopwords, min_len)

        return tokens

    @classmethod
    def template_similarity(cls, content: str, template: str) -> float:
        left = cls._normalize_compare(content)
        right = cls._normalize_compare(template)

        if not left or not right:
            return 0.0

        if left == right:
            return 1.0

        if left in right or right in left:
            shorter = min(len(left), len(right))
            longer = max(len(left), len(right)) or 1

            return shorter / longer

        return SequenceMatcher(None, left, right).ratio()

    @classmethod
    def _evaluate_pipeline(cls, pipeline: dict[str, Any], mode: str) -> list[str]:
        gaps: list[str] = []
        effect = str(pipeline.get("responseModeEffect") or "").strip()

        if mode == "fast" and effect != "llm_synthesis_brief":
            gaps.append(f"pipeline.responseModeEffect esperado llm_synthesis_brief, veio {effect!r}")

        if mode in {"normal", "thinker"} and effect != "llm_synthesis":
            gaps.append(f"pipeline.responseModeEffect esperado llm_synthesis, veio {effect!r}")

        if pipeline.get("directResponse"):
            allowed = ChatResponseModeSynthesisQualityContentService.pipeline_modes_allowing_direct_response()

            if mode not in allowed:
                gaps.append(
                    "pipeline.directResponse=true — resposta ainda veio do template/direct answer"
                )
            else:
                expected_effect = (
                    ChatResponseModeSynthesisQualityContentService.pipeline_direct_response_effect(
                        mode
                    )
                )

                if expected_effect and effect != expected_effect:
                    gaps.append(
                        f"pipeline.directResponse=true em {mode!r} exige "
                        f"responseModeEffect {expected_effect!r}, veio {effect!r}"
                    )

        return gaps

    @classmethod
    def _evaluate_answer_shape(
        cls,
        content: str,
        mode: str,
        elapsed_sec: float | None,
    ) -> list[str]:
        gaps: list[str] = []
        chars = len(content)

        min_chars = ChatResponseModeSynthesisQualityContentService.mode_limit_int(
            "minAnswerChars",
            mode,
            default=120,
        )
        max_chars = ChatResponseModeSynthesisQualityContentService.mode_limit_int(
            "maxAnswerChars",
            mode,
            default=4000,
        )

        if chars < min_chars:
            gaps.append(f"resposta curta demais para {mode} ({chars} < {min_chars} chars)")

        if max_chars and chars > max_chars:
            gaps.append(f"resposta longa demais para {mode} ({chars} > {max_chars} chars)")

        if elapsed_sec is not None:
            max_elapsed = ChatResponseModeSynthesisQualityContentService.mode_limit_int(
                "maxElapsedSec",
                mode,
                default=180,
            )

            if max_elapsed and elapsed_sec > max_elapsed:
                gaps.append(f"tempo excedido em {mode} ({elapsed_sec}s > {max_elapsed}s)")

        return gaps

    @classmethod
    def _evaluate_prose_decoupling(
        cls,
        tool_calls: list[dict[str, Any]] | None,
        pipeline: dict[str, Any],
    ) -> list[str]:
        """P2.6 — turno LLM deve ter metadata data-only (sem markdown template nos toolCalls)."""
        gaps: list[str] = []
        effect = str(pipeline.get("responseModeEffect") or "").strip()

        if effect not in {"llm_synthesis", "llm_synthesis_brief"}:
            return gaps

        if not isinstance(tool_calls, list) or not tool_calls:
            return gaps

        for index, tool_call in enumerate(tool_calls):
            if not isinstance(tool_call, dict):
                continue

            metadata = tool_call.get("metadata")

            if not isinstance(metadata, dict) or not metadata.get("ok"):
                continue

            if not metadata.get("presentationDecision"):
                continue

            prefix = f"toolCalls[{index}]"

            if not (
                metadata.get("dataOnlyPresentation") or metadata.get("llmProseDecoupled")
            ):
                gaps.append(
                    f"{prefix}: síntese LLM sem dataOnlyPresentation/llmProseDecoupled"
                )
                continue

            text_presentation = metadata.get("textPresentation")

            if isinstance(text_presentation, dict):
                markdown = str(text_presentation.get("markdown") or "").strip()

                if markdown:
                    gaps.append(
                        f"{prefix}: textPresentation.markdown ainda preenchido em turno data-only"
                    )

            humanized = metadata.get("humanizedSummary")

            if isinstance(humanized, dict):
                linhas = humanized.get("linhas") or []
                linhas_detalhe = humanized.get("linhas_detalhe") or []

                if linhas or linhas_detalhe:
                    gaps.append(
                        f"{prefix}: humanizedSummary ainda contém linhas template em data-only"
                    )

            if str(metadata.get("proseDeliveryMode") or "") != "llm":
                gaps.append(
                    f"{prefix}: proseDeliveryMode esperado 'llm', "
                    f"veio {metadata.get('proseDeliveryMode')!r}"
                )

        return gaps

    @classmethod
    def _evaluate_not_template_clone(
        cls,
        content: str,
        tool_calls: list[dict[str, Any]] | None,
    ) -> list[str]:
        gaps: list[str] = []
        template = cls.extract_template_markdown(tool_calls)

        if not template:
            return gaps

        similarity = cls.template_similarity(content, template)
        max_similarity = ChatResponseModeSynthesisQualityContentService.limit_float(
            "maxTemplateSimilarity",
            default=0.72,
        )

        if similarity >= max_similarity:
            gaps.append(
                "resposta reproduz o template operacional "
                f"(similaridade {similarity:.2f} >= {max_similarity:.2f})"
            )

        return gaps

    @classmethod
    def _evaluate_context_and_assertiveness(
        cls,
        content: str,
        question: str,
        tool_calls: list[dict[str, Any]] | None,
    ) -> list[str]:
        gaps: list[str] = []
        normalized_content = ChatMessageNormalizationService.normalize_for_matching(content)
        product_code = ChatProductQueryIntentService.extract_product_code(question or "")

        if product_code and product_code not in normalized_content:
            gaps.append(f"código do produto {product_code} ausente na resposta")

        context_tokens = cls.extract_context_tokens(tool_calls)

        if not context_tokens:
            return gaps

        overlap = sum(
            1
            for token in context_tokens
            if token in normalized_content
        )
        min_overlap = ChatResponseModeSynthesisQualityContentService.limit_int(
            "minContextTokenOverlap",
            default=2,
        )

        if overlap < min_overlap:
            sample = ", ".join(sorted(context_tokens)[:6])
            gaps.append(
                "pouco contexto operacional na resposta "
                f"({overlap}/{min_overlap} tokens; esperado algo como: {sample})"
            )

        return gaps

    @classmethod
    def _evaluate_deflection(cls, content: str) -> list[str]:
        normalized = ChatMessageNormalizationService.normalize_for_matching(content)

        for marker in ChatResponseModeSynthesisQualityContentService.deflection_markers():
            if marker in normalized:
                return [f"resposta evasiva/genérica detectada ({marker})"]

        return []

    @classmethod
    def _evaluate_hallucination_markers(cls, content: str) -> list[str]:
        from app.domain.services.chat_operational_llm_synthesis_context_content_service import (
            ChatOperationalLlmSynthesisContextContentService,
        )

        normalized = ChatMessageNormalizationService.normalize_for_matching(content)

        for marker in ChatOperationalLlmSynthesisContextContentService.hallucination_markers():
            normalized_marker = ChatMessageNormalizationService.normalize_for_matching(marker)

            if normalized_marker and normalized_marker in normalized:
                return [f"marcador de alucinação detectado ({marker})"]

        return []

    @classmethod
    def _collect_tokens_from_object(
        cls,
        value: Any,
        tokens: set[str],
        stopwords: frozenset[str],
        min_len: int,
    ) -> None:
        if value is None:
            return

        if isinstance(value, str):
            for token in _TOKEN_RE.findall(cls._normalize_compare(value)):
                if len(token) >= min_len and token not in stopwords:
                    tokens.add(token)
            return

        if isinstance(value, dict):
            for nested in value.values():
                cls._collect_tokens_from_object(nested, tokens, stopwords, min_len)
            return

        if isinstance(value, list):
            for nested in value:
                cls._collect_tokens_from_object(nested, tokens, stopwords, min_len)

    @classmethod
    def _normalize_compare(cls, text: str) -> str:
        normalized = ChatMessageNormalizationService.normalize_for_matching(text)
        normalized = unicodedata.normalize("NFKD", normalized)
        normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
        normalized = re.sub(r"\s+", " ", normalized).strip()
        normalized = re.sub(r"[#*|_>`]", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()

        return normalized
