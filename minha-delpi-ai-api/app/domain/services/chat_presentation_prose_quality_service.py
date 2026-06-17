"""Checklist de prosa legível — rejeita respostas confusas ou escravas da API."""

from __future__ import annotations

import re
from typing import Any


class ChatPresentationProseQualityService:
    _GENERIC_ROW_COUNT = re.compile(
        r"foram retornados\s+\*?\*?\d+\*?\*?\s+registros?",
        re.IGNORECASE,
    )
    _DUPLICATE_INTRO = re.compile(
        r"situação produtiva do produto",
        re.IGNORECASE,
    )

    @classmethod
    def evaluate(
        cls,
        metadata: dict[str, Any] | None,
        *,
        user_message: str = "",
    ) -> dict[str, Any]:
        gaps: list[str] = []

        if not isinstance(metadata, dict):
            return cls._result(gaps=["metadata_invalid"])

        markdown = cls._resolve_markdown(metadata)
        data_answer = metadata.get("dataAnswer")
        answer = ""

        if isinstance(data_answer, dict):
            summary = data_answer.get("summary") or {}
            answer = str(summary.get("answer") or "").strip()

        combined = f"{answer}\n{markdown}".strip()

        if not combined:
            gaps.append("empty_presentation")

        if cls._GENERIC_ROW_COUNT.search(combined):
            gaps.append("generic_row_count_without_intent")

        if markdown.count("###") > 2:
            gaps.append("excessive_headings")

        intro_hits = len(cls._DUPLICATE_INTRO.findall(markdown))

        if intro_hits > 1:
            gaps.append("duplicate_production_intro")

        if "Situação produtiva do PA e intermediários" in markdown and answer:
            gaps.append("scope_intro_duplicates_data_answer")

        if markdown and not cls._has_structure(markdown):
            metric_lines = sum(
                1
                for line in markdown.splitlines()
                if "**" in line and any(ch.isdigit() for ch in line)
            )

            if metric_lines >= 4 and "- " not in markdown:
                gaps.append("dense_metrics_without_bullets")

        if user_message and isinstance(data_answer, dict):
            if not answer:
                gaps.append("missing_question_answer")
            elif not cls._answer_addresses_question(user_message, answer, markdown):
                gaps.append("answer_not_aligned_with_question")

        return cls._result(gaps=gaps)

    @classmethod
    def evaluate_expectations(
        cls,
        metadata: dict[str, Any] | None,
        *,
        forbidden: list[str] | None = None,
        required: list[str] | None = None,
    ) -> list[str]:
        result = cls.evaluate(metadata)
        gaps = list(result.get("gaps") or [])
        combined = cls._combined_text(metadata)

        for token in forbidden or []:
            if token.lower() in combined.lower():
                gaps.append(f"forbidden:{token}")

        for token in required or []:
            if token.lower() not in combined.lower():
                gaps.append(f"missing_required:{token}")

        return gaps

    @classmethod
    def _resolve_markdown(cls, metadata: dict[str, Any]) -> str:
        text_presentation = metadata.get("textPresentation")

        if isinstance(text_presentation, dict):
            return str(text_presentation.get("markdown") or "").strip()

        return ""

    @classmethod
    def _combined_text(cls, metadata: dict[str, Any] | None) -> str:
        if not isinstance(metadata, dict):
            return ""

        parts: list[str] = []
        data_answer = metadata.get("dataAnswer")

        if isinstance(data_answer, dict):
            summary = data_answer.get("summary") or {}
            parts.append(str(summary.get("answer") or ""))
            parts.append(str(summary.get("meaning") or ""))

        parts.append(cls._resolve_markdown(metadata))
        return "\n".join(part for part in parts if part).strip()

    @classmethod
    def _has_structure(cls, markdown: str) -> bool:
        return (
            "**Situação" in markdown
            or "**Principais ordens**" in markdown
            or "**Matérias-primas" in markdown
            or "**Resposta:**" in markdown
            or "- " in markdown
        )

    @classmethod
    def _answer_addresses_question(
        cls,
        user_message: str,
        answer: str,
        markdown: str,
    ) -> bool:
        normalized = re.sub(r"\s+", " ", user_message.strip().lower())
        answer_lower = answer.lower()
        combined = f"{answer_lower} {markdown.lower()}"

        if any(token in normalized for token in ("exclusiv", "mp exclusiva")):
            return "sim" in answer_lower or "não" in answer_lower or "nao" in answer_lower

        if any(token in normalized for token in ("programad", "programação", "programacao")):
            return "sim" in answer_lower or "não" in answer_lower or "nao" in answer_lower

        if any(token in normalized for token in ("op aberta", "iniciou", "apontamento")):
            return "sim" in answer_lower or "não" in answer_lower or "nao" in answer_lower

        if "situação produtiva" in normalized or "situacao produtiva" in normalized:
            return "pa" in combined and ("sim" in combined or "não" in combined or "nao" in combined)

        return bool(answer.strip())

    @classmethod
    def _result(cls, *, gaps: list[str]) -> dict[str, Any]:
        return {
            "ok": not gaps,
            "gaps": gaps,
            "gapCount": len(gaps),
        }
