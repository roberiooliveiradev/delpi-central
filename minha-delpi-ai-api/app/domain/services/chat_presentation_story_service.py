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

        return True

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

        for item in data_answer.get("facts") or []:
            if not isinstance(item, dict):
                continue

            text = str(item.get("text") or "").strip()

            if text:
                blocks.append({"kind": "fact", "text": text})

        for line in cls._clean_lines(data_answer.get("analysis")):
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

            blocks.append(
                {
                    "kind": "recommendation",
                    "text": label,
                    "query": query,
                }
            )

        for line in cls._clean_lines(data_answer.get("limitations")):
            blocks.append(
                {
                    "kind": "limitation",
                    "title": ChatHumanizedDataResponseContentService.get(
                        "storyBlocks",
                        "limitationTitle",
                    ),
                    "text": line,
                }
            )

        return blocks

    @classmethod
    def _clean_lines(cls, value: object) -> list[str]:
        if not isinstance(value, list):
            return []

        return [str(line).strip() for line in value if str(line or "").strip()]
