"""Apresentação tipo story a partir de dataAnswer — Playbook 13 P4."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_humanized_data_response_content_service import (
    ChatHumanizedDataResponseContentService,
)

_RISK_TO_STATUS = {
    "ok": "ok",
    "attention": "attention",
    "critical": "critical",
    "undefined": "unknown",
}


class ChatPresentationStoryService:
    @classmethod
    def enrich_metadata(cls, metadata: dict[str, Any]) -> bool:
        if not isinstance(metadata, dict):
            return False

        story = cls.build_from_metadata(metadata)

        if not story:
            return False

        metadata["storyPresentation"] = story
        cls._strip_duplicate_narrative(metadata)

        return True

    @classmethod
    def _strip_duplicate_narrative(cls, metadata: dict[str, Any]) -> None:
        from app.domain.services.chat_rich_presentation_text_service import (
            ChatRichPresentationTextService,
        )

        text_presentation = metadata.get("textPresentation")

        if not isinstance(text_presentation, dict):
            return

        markdown = str(text_presentation.get("markdown") or "").strip()

        if not markdown:
            return

        stripped = ChatRichPresentationTextService.strip_highlights_block(markdown)

        if stripped != markdown:
            text_presentation["markdown"] = stripped

    @classmethod
    def build_from_metadata(cls, metadata: dict[str, Any]) -> dict[str, Any] | None:
        if not isinstance(metadata, dict):
            return None

        data_answer = metadata.get("dataAnswer")

        if not isinstance(data_answer, dict):
            return None

        summary = data_answer.get("summary")

        if not isinstance(summary, dict):
            return None

        answer = str(summary.get("answer") or "").strip()

        if not answer:
            return None

        blocks = cls._build_blocks(data_answer, summary=summary)

        if not blocks:
            return None

        return {
            "type": "story",
            "title": cls._resolve_title(metadata, data_answer),
            "blocks": blocks,
        }

    @classmethod
    def _resolve_title(cls, metadata: dict[str, Any], data_answer: dict[str, Any]) -> str:
        text_presentation = metadata.get("textPresentation")

        if isinstance(text_presentation, dict):
            markdown = str(text_presentation.get("markdown") or "").strip()

            if markdown:
                for line in markdown.splitlines():
                    stripped = line.strip()

                    if stripped.startswith("#"):
                        return stripped.lstrip("#").strip()

        purpose = ""

        decision = metadata.get("presentationDecision")

        if isinstance(decision, dict):
            purpose = str(decision.get("purpose") or "").strip()

        if purpose:
            return purpose[:120]

        profile_key = str(data_answer.get("profileKey") or "").strip()

        if profile_key:
            return profile_key.replace("_", " ").strip().title()

        path = str(metadata.get("path") or "").strip()

        if path:
            return path.rsplit("/", 1)[-1].replace("-", " ").strip().title()

        return ChatHumanizedDataResponseContentService.get(
            "storyBlocks",
            "defaultTitle",
            default="Resumo dos dados",
        )

    @classmethod
    def _build_blocks(
        cls,
        data_answer: dict[str, Any],
        *,
        summary: dict[str, Any],
    ) -> list[dict[str, Any]]:
        blocks: list[dict[str, Any]] = []
        answer = str(summary.get("answer") or "").strip()
        meaning = str(summary.get("meaning") or "").strip()
        risk_level = str(summary.get("riskLevel") or "undefined").strip().lower()
        status = _RISK_TO_STATUS.get(risk_level, "unknown")

        verdict_text = answer

        if meaning and meaning not in answer:
            verdict_text = (
                ChatHumanizedDataResponseContentService.format(
                    "summaryTemplates",
                    "withInterpretation",
                    summary=answer,
                    interpretation=meaning,
                )
                or answer
            )

        blocks.append(
            {
                "kind": "verdict",
                "title": ChatHumanizedDataResponseContentService.get(
                    "storyBlocks",
                    "verdictTitle",
                ),
                "text": verdict_text,
                "status": status,
            }
        )

        risk_label = ChatHumanizedDataResponseContentService.get_mapping("alertLevels").get(
            risk_level,
            ChatHumanizedDataResponseContentService.get(
                "alertLevels",
                risk_level if risk_level in {"ok", "attention", "critical", "unknown"} else "unknown",
            ),
        )

        if risk_label:
            blocks.append(
                {
                    "kind": "fact",
                    "text": ChatHumanizedDataResponseContentService.format(
                        "storyBlocks",
                        "riskLevelLine",
                        riskLevel=risk_label,
                    ),
                }
            )

        for line in cls._clean_lines(summary.get("attention")):
            blocks.append(
                {
                    "kind": "fact",
                    "title": ChatHumanizedDataResponseContentService.get(
                        "storyBlocks",
                        "attentionTitle",
                    ),
                    "text": line,
                }
            )

        seen_texts = cls._collect_seen_texts(
            verdict_text=verdict_text,
            meaning=meaning,
            attention=cls._clean_lines(summary.get("attention")),
        )

        for item in data_answer.get("facts") or []:
            if not isinstance(item, dict):
                continue

            text = cls._item_text(item)

            if text and not cls._is_duplicate_text(text, seen_texts):
                seen_texts.add(cls._normalize_for_dedup(text))
                blocks.append({"kind": "fact", "text": text})

        for line in cls._analysis_lines(data_answer.get("analysis")):
            if cls._is_duplicate_text(line, seen_texts):
                continue

            seen_texts.add(cls._normalize_for_dedup(line))
            blocks.append(
                {
                    "kind": "analysis",
                    "title": ChatHumanizedDataResponseContentService.get(
                        "storyBlocks",
                        "analysisTitle",
                    ),
                    "text": line,
                }
            )

        for item in data_answer.get("hypotheses") or []:
            if not isinstance(item, dict):
                continue

            text = str(item.get("text") or "").strip()

            if not text:
                continue

            blocks.append(
                {
                    "kind": "hypothesis",
                    "text": text,
                    "confirmed": item.get("confirmed") is True,
                }
            )

        next_action = str(summary.get("nextAction") or "").strip()
        next_action_key = cls._normalize_for_dedup(next_action)

        if next_action:
            blocks.append(
                {
                    "kind": "recommendation",
                    "title": ChatHumanizedDataResponseContentService.get(
                        "storyBlocks",
                        "nextActionTitle",
                    ),
                    "text": next_action,
                }
            )

        for item in data_answer.get("recommendations") or []:
            if not isinstance(item, dict):
                continue

            label = str(item.get("label") or item.get("text") or "").strip()
            query = str(item.get("query") or item.get("intent") or label).strip()

            if not label:
                continue

            if next_action_key and cls._normalize_for_dedup(label) == next_action_key:
                continue

            blocks.append(
                {
                    "kind": "recommendation",
                    "text": label,
                    "query": query,
                }
            )

        return blocks

    @classmethod
    def _clean_lines(cls, value: object) -> list[str]:
        if not isinstance(value, list):
            return []

        lines: list[str] = []

        for line in value:
            text = cls._item_text(line)

            if text:
                lines.append(text)

        return lines

    @classmethod
    def _analysis_lines(cls, value: object) -> list[str]:
        if not isinstance(value, list):
            return []

        lines: list[str] = []

        for item in value:
            text = cls._item_text(item)

            if text:
                lines.append(text)

        return lines

    @classmethod
    def _item_text(cls, value: object) -> str:
        if isinstance(value, dict):
            return str(value.get("text") or "").strip()

        return str(value or "").strip()

    @classmethod
    def _collect_seen_texts(
        cls,
        *,
        verdict_text: str,
        meaning: str,
        attention: list[str],
    ) -> set[str]:
        seen: set[str] = set()

        for text in [verdict_text, meaning, *attention]:
            normalized = cls._normalize_for_dedup(text)

            if normalized:
                seen.add(normalized)

        return seen

    @classmethod
    def _normalize_for_dedup(cls, text: str) -> str:
        import re

        cleaned = re.sub(r"\*+", "", str(text or "")).strip().casefold()

        return " ".join(cleaned.split())

    @classmethod
    def _is_duplicate_text(cls, text: str, seen: set[str]) -> bool:
        normalized = cls._normalize_for_dedup(text)

        if not normalized:
            return True

        if normalized in seen:
            return True

        for existing in seen:
            if normalized in existing or existing in normalized:
                return True

        return False
