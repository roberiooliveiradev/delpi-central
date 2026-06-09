"""Transformações de conteúdo na lousa — Playbook 05 Fase 4."""

from __future__ import annotations

import re

from app.domain.services.chat_canvas_transform_vocabulary_service import (
    ChatCanvasTransformVocabularyService,
)
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)


class ChatCanvasTransformService:
    KIND_CHECKLIST = "checklist"
    KIND_REPORT = "report"
    KIND_MINUTES = "minutes"
    KIND_ANNOUNCEMENT = "announcement"

    @classmethod
    def detect_kind(cls, message: str) -> str | None:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return None

        for kind in (
            cls.KIND_CHECKLIST,
            cls.KIND_REPORT,
            cls.KIND_MINUTES,
            cls.KIND_ANNOUNCEMENT,
        ):
            if any(term in normalized for term in ChatCanvasTransformVocabularyService.kind_terms(kind)):
                return kind

        return None

    @classmethod
    def transform(cls, markdown: str, kind: str) -> tuple[str, str]:
        token = str(kind or "").strip()

        if token == cls.KIND_CHECKLIST:
            return cls.to_checklist(markdown), ChatCanvasTransformVocabularyService.kind_label(
                cls.KIND_CHECKLIST,
                default="Checklist",
            )

        if token == cls.KIND_REPORT:
            return cls.to_report(markdown), ChatCanvasTransformVocabularyService.kind_label(
                cls.KIND_REPORT,
                default="Relatório",
            )

        if token == cls.KIND_MINUTES:
            return cls.to_minutes(markdown), ChatCanvasTransformVocabularyService.kind_label(
                cls.KIND_MINUTES,
                default="Ata de reunião",
            )

        if token == cls.KIND_ANNOUNCEMENT:
            return cls.to_announcement(markdown), ChatCanvasTransformVocabularyService.kind_label(
                cls.KIND_ANNOUNCEMENT,
                default="Comunicado",
            )

        return str(markdown or "").strip(), ChatCanvasTransformVocabularyService.kind_label(
            "default",
            default="Documento",
        )

    @classmethod
    def _template(cls, key: str, *, default: str = "") -> str:
        return ChatCanvasTransformVocabularyService.template(key, default=default)

    @classmethod
    def to_checklist(cls, markdown: str) -> str:
        lines = str(markdown or "").splitlines()
        output: list[str] = []

        for line in lines:
            stripped = line.strip()

            if not stripped:
                output.append("")
                continue

            if stripped.startswith("- [ ]") or stripped.startswith("- [x]"):
                output.append(line)
                continue

            if stripped.startswith("#"):
                output.append(line)
                continue

            if stripped.startswith("|"):
                output.append(line)
                continue

            if stripped.startswith("- "):
                output.append(f"- [ ] {stripped[2:].strip()}")
                continue

            if re.match(r"^\d+\.\s+", stripped):
                output.append(re.sub(r"^(\d+\.\s+)", r"- [ ] ", stripped))
                continue

            output.append(f"- [ ] {stripped}")

        body = "\n".join(output).strip()
        header = cls._template("checklistHeader", default="# Checklist")

        if body.lower().startswith("# checklist"):
            return body

        return f"{header}\n\n{body}"

    @classmethod
    def to_report(cls, markdown: str) -> str:
        body = str(markdown or "").strip()
        header = cls._template("reportHeader", default="# Relatório")

        if body.lower().startswith("# relat"):
            return body

        return "\n".join(
            [
                header,
                "",
                body,
                "",
                cls._template("reportConclusionHeader", default="## Conclusão"),
                "",
                cls._template(
                    "reportConclusionPlaceholder",
                    default="- (preencha recomendações e próximos passos)",
                ),
            ]
        ).strip()

    @classmethod
    def to_minutes(cls, markdown: str) -> str:
        body = str(markdown or "").strip()

        if "ata de" in body.lower()[:80]:
            return body

        placeholder = cls._template("minutesListPlaceholder", default="- ")

        return "\n".join(
            [
                cls._template("minutesHeader", default="# Ata de reunião"),
                "",
                cls._template("minutesParticipantsHeader", default="## Participantes"),
                placeholder,
                "",
                cls._template("minutesAgendaHeader", default="## Pauta"),
                placeholder,
                "",
                cls._template("minutesDiscussedHeader", default="## Pontos discutidos"),
                "",
                body,
                "",
                cls._template("minutesDecisionsHeader", default="## Decisões"),
                placeholder,
                "",
                cls._template("minutesPendingHeader", default="## Pendências"),
                cls._template("minutesPendingItem", default="- [ ] "),
            ]
        ).strip()

    @classmethod
    def to_announcement(cls, markdown: str) -> str:
        body = str(markdown or "").strip()
        header = cls._template("announcementHeader", default="# Comunicado")

        if body.lower().startswith("# comunicado"):
            return body

        return f"{header}\n\n{body}"
