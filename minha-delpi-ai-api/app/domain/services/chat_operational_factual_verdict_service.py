"""Vereditos factuais operacionais — serviço transversal por profileKey (não por rota)."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_operational_factual_verdict_content_service import (
    ChatOperationalFactualVerdictContentService,
)
from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


class ChatOperationalFactualVerdictService:
    @classmethod
    def resolve_profile_key(
        cls,
        *,
        path: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str | None:
        resolved_path = path

        if resolved_path is None and isinstance(metadata, dict):
            resolved_path = str(metadata.get("path") or "")

        api_meta = metadata.get("apiDelpiResponseMeta") if isinstance(metadata, dict) else None
        entity = (
            str(api_meta.get("entity") or "").strip()
            if isinstance(api_meta, dict)
            else None
        ) or None

        profile_key = ChatPresentationProfileService.commentary_profile_key(
            path=resolved_path,
            entity=entity,
        )

        if profile_key and profile_key in ChatOperationalFactualVerdictContentService.profile_keys():
            return profile_key

        lowered = str(resolved_path or "").lower()

        for candidate in ChatOperationalFactualVerdictContentService.profile_keys():
            if cls.profile_applies_to_path(candidate, lowered):
                return candidate

        return None

    @classmethod
    def profile_applies_to_path(cls, profile_key: str, path: str | None) -> bool:
        lowered = str(path or "").lower()

        if not lowered:
            return False

        return any(
            marker.lower() in lowered
            for marker in ChatOperationalFactualVerdictContentService.path_markers(profile_key)
            if str(marker or "").strip()
        )

    @classmethod
    def extract_scalar(cls, metadata: dict[str, Any], profile_key: str) -> int | None:
        kpi = metadata.get("kpiPresentation")

        if isinstance(kpi, dict):
            label_markers = [
                ChatMessageNormalizationService.normalize_for_matching(marker)
                for marker in ChatOperationalFactualVerdictContentService.kpi_label_markers(
                    profile_key,
                )
                if str(marker or "").strip()
            ]

            for metric in (kpi.get("cards") or []) + (kpi.get("metrics") or []):
                if not isinstance(metric, dict):
                    continue

                label = ChatMessageNormalizationService.normalize_for_matching(
                    str(metric.get("label") or metric.get("name") or ""),
                )

                if label_markers and not any(marker in label for marker in label_markers):
                    continue

                raw_value = metric.get("value")

                if raw_value is None:
                    raw_value = metric.get("formattedValue")

                raw_text = str(raw_value if raw_value is not None else "").strip()

                try:
                    return int(float(raw_text.replace(",", ".").split()[0]))
                except (TypeError, ValueError, IndexError):
                    continue

        data_answer = metadata.get("dataAnswer")

        if isinstance(data_answer, dict):
            highlights = data_answer.get("highlights")

            if isinstance(highlights, list):
                verdict_no_markers = [
                    ChatMessageNormalizationService.normalize_for_matching(marker)
                    for marker in ChatOperationalFactualVerdictContentService.verdict_no_markers(
                        profile_key,
                    )
                    if str(marker or "").strip()
                ]

                for item in highlights:
                    text = ChatMessageNormalizationService.normalize_for_matching(
                        cls._stringify(item),
                    )

                    if any(marker in text for marker in verdict_no_markers):
                        return 0

        return None

    @classmethod
    def extract_scalar_from_tool_calls(
        cls,
        tool_calls: list | None,
        profile_key: str,
    ) -> int | None:
        if not isinstance(tool_calls, list):
            return None

        for tool_call in tool_calls:
            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata")

            if not isinstance(metadata, dict) or not metadata.get("ok"):
                continue

            path = str(metadata.get("path") or "")

            if not cls.profile_applies_to_path(profile_key, path):
                continue

            count = cls.extract_scalar(metadata, profile_key)

            if count is not None:
                return count

        return None

    @classmethod
    def build_llm_facts(cls, metadata: dict[str, Any]) -> list[str]:
        profile_key = cls.resolve_profile_key(metadata=metadata)

        if not profile_key:
            return []

        facts: list[str] = []
        scalar = cls.extract_scalar(metadata, profile_key)

        if scalar is not None:
            if scalar == 0:
                facts.append(
                    ChatOperationalFactualVerdictContentService.llm_fact(
                        profile_key,
                        "verdictNo",
                    ),
                )
            else:
                facts.append(
                    ChatOperationalFactualVerdictContentService.llm_fact(
                        profile_key,
                        "verdictYes",
                        count=scalar,
                    ),
                )

        text_presentation = metadata.get("textPresentation")

        if isinstance(text_presentation, dict):
            markdown = str(text_presentation.get("markdown") or "").strip()
            prefix = ChatOperationalFactualVerdictContentService.markdown_verdict_line_prefix(
                profile_key,
            ).lower()

            for line in markdown.splitlines():
                text = line.strip()

                if text.lower().startswith(prefix):
                    facts.append(text.replace("**", "").strip())
                    break

        return facts

    @classmethod
    def append_fidelity_rules_for_tool_calls(cls, text: str, tool_calls: list | None) -> str:
        if not isinstance(tool_calls, list):
            return text

        result = text

        for profile_key in ChatOperationalFactualVerdictContentService.profile_keys():
            rule = ChatOperationalFactualVerdictContentService.fidelity_rule(profile_key)

            if not rule:
                continue

            if not cls._tool_calls_match_profile(tool_calls, profile_key):
                continue

            result = f"{result}\n\n{rule}" if result else f"\n\n{rule}"

        return result

    @classmethod
    def strip_contradictory_claims_for_tool_calls(
        cls,
        answer: str,
        tool_calls: list | None,
    ) -> str:
        result = answer

        for profile_key in ChatOperationalFactualVerdictContentService.profile_keys():
            scalar = cls.extract_scalar_from_tool_calls(tool_calls, profile_key)

            if scalar is None:
                continue

            result = cls.strip_contradictory_claims(result, profile_key, scalar)

        return result

    @classmethod
    def strip_contradictory_claims(
        cls,
        answer: str,
        profile_key: str,
        scalar: int | None,
    ) -> str:
        if scalar is None:
            return answer

        triggers = [
            ChatMessageNormalizationService.normalize_for_matching(pattern)
            for pattern in ChatOperationalFactualVerdictContentService.contradiction_triggers(
                profile_key,
            )
            if str(pattern or "").strip()
        ]
        positive_markers = [
            ChatMessageNormalizationService.normalize_for_matching(marker)
            for marker in ChatOperationalFactualVerdictContentService.positive_markers(profile_key)
            if str(marker or "").strip()
        ]
        shared_markers = [
            ChatMessageNormalizationService.normalize_for_matching(marker)
            for marker in ChatOperationalFactualVerdictContentService.shared_markers(profile_key)
            if str(marker or "").strip()
        ]
        verdict_no_markers = [
            ChatMessageNormalizationService.normalize_for_matching(marker)
            for marker in ChatOperationalFactualVerdictContentService.verdict_no_markers(profile_key)
            if str(marker or "").strip()
        ]
        defined_marker = ChatMessageNormalizationService.normalize_for_matching(
            ChatOperationalFactualVerdictContentService.defined_with_shared_marker(profile_key),
        )

        sentences = _SENTENCE_SPLIT_RE.split(answer.strip())
        kept: list[str] = []

        for sentence in sentences:
            text = str(sentence or "").strip()

            if not text:
                continue

            normalized = ChatMessageNormalizationService.normalize_for_matching(text)

            if any(trigger in normalized for trigger in triggers):
                continue

            if scalar == 0:
                has_positive = any(marker in normalized for marker in positive_markers)
                has_shared = any(marker in normalized for marker in shared_markers)

                if has_positive and has_shared:
                    continue

                if has_positive and defined_marker in normalized:
                    continue

            if scalar > 0 and any(marker in normalized for marker in verdict_no_markers):
                continue

            kept.append(text)

        if not kept:
            return ""

        return " ".join(kept).strip()

    @classmethod
    def evaluate_coherence_gaps_for_tool_calls(
        cls,
        content: str,
        tool_calls: list | None,
    ) -> list[tuple[str, str]]:
        gaps: list[tuple[str, str]] = []

        for profile_key in ChatOperationalFactualVerdictContentService.profile_keys():
            gap_key = ChatOperationalFactualVerdictContentService.quality_gap_key(profile_key)

            if not gap_key:
                continue

            scalar = cls.extract_scalar_from_tool_calls(tool_calls, profile_key)
            details = cls.evaluate_coherence_gap_details(content, profile_key, scalar)

            for detail in details:
                gaps.append((gap_key, detail))

        return gaps

    @classmethod
    def evaluate_coherence_gap_details(
        cls,
        content: str,
        profile_key: str,
        scalar: int | None,
    ) -> list[str]:
        if scalar is None:
            return []

        normalized = ChatMessageNormalizationService.normalize_for_matching(content)
        triggers = [
            ChatMessageNormalizationService.normalize_for_matching(trigger)
            for trigger in ChatOperationalFactualVerdictContentService.contradiction_triggers(
                profile_key,
            )
            if str(trigger or "").strip()
        ]
        positive_markers = [
            ChatMessageNormalizationService.normalize_for_matching(marker)
            for marker in ChatOperationalFactualVerdictContentService.positive_markers(profile_key)
            if str(marker or "").strip()
        ]
        shared_markers = [
            ChatMessageNormalizationService.normalize_for_matching(marker)
            for marker in ChatOperationalFactualVerdictContentService.shared_markers(profile_key)
            if str(marker or "").strip()
        ]
        defined_marker = ChatMessageNormalizationService.normalize_for_matching(
            ChatOperationalFactualVerdictContentService.defined_with_shared_marker(profile_key),
        )

        for trigger in triggers:
            if trigger and trigger in normalized:
                return [trigger]

        if scalar == 0:
            has_positive = any(marker in normalized for marker in positive_markers)
            has_shared = any(marker in normalized for marker in shared_markers)

            if has_positive and has_shared:
                return [
                    ChatOperationalFactualVerdictContentService.coherence_gap_detail(
                        profile_key,
                        "positiveAndShared",
                    )
                    or "exclusiva + compartilhada na mesma resposta",
                ]

            if has_positive and defined_marker in normalized and has_shared:
                return [
                    ChatOperationalFactualVerdictContentService.coherence_gap_detail(
                        profile_key,
                        "definedWithShared",
                    )
                    or "exclusividade definida com MPs compartilhadas",
                ]

        return []

    @classmethod
    def _tool_calls_match_profile(cls, tool_calls: list, profile_key: str) -> bool:
        for tool_call in tool_calls:
            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata")

            if not isinstance(metadata, dict) or not metadata.get("ok"):
                continue

            path = str(metadata.get("path") or "")

            if cls.profile_applies_to_path(profile_key, path):
                return True

        return False

    @classmethod
    def _stringify(cls, value: Any) -> str:
        if isinstance(value, dict):
            return str(value.get("text") or value.get("value") or "").strip()

        return str(value or "").strip()
