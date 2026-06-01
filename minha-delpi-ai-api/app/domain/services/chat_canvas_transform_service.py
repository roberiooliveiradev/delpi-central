"""Transformações de conteúdo na lousa — Playbook 05 Fase 4."""

from __future__ import annotations

import re

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)


class ChatCanvasTransformService:
    KIND_CHECKLIST = "checklist"
    KIND_REPORT = "report"
    KIND_MINUTES = "minutes"
    KIND_ANNOUNCEMENT = "announcement"

    _CHECKLIST_TERMS = ("checklist", "lista de tarefas", "lista de acoes", "lista de ações")
    _REPORT_TERMS = ("relatorio", "relatório")
    _MINUTES_TERMS = ("ata", "ata de reuniao", "ata de reunião")
    _ANNOUNCEMENT_TERMS = ("comunicado",)

    @classmethod
    def detect_kind(cls, message: str) -> str | None:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return None

        if any(term in normalized for term in cls._CHECKLIST_TERMS):
            return cls.KIND_CHECKLIST

        if any(term in normalized for term in cls._REPORT_TERMS):
            return cls.KIND_REPORT

        if any(term in normalized for term in cls._MINUTES_TERMS):
            return cls.KIND_MINUTES

        if any(term in normalized for term in cls._ANNOUNCEMENT_TERMS):
            return cls.KIND_ANNOUNCEMENT

        return None

    @classmethod
    def transform(cls, markdown: str, kind: str) -> tuple[str, str]:
        token = str(kind or "").strip()

        if token == cls.KIND_CHECKLIST:
            return cls.to_checklist(markdown), "Checklist"

        if token == cls.KIND_REPORT:
            return cls.to_report(markdown), "Relatório"

        if token == cls.KIND_MINUTES:
            return cls.to_minutes(markdown), "Ata de reunião"

        if token == cls.KIND_ANNOUNCEMENT:
            return cls.to_announcement(markdown), "Comunicado"

        return str(markdown or "").strip(), "Documento"

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

        if body.lower().startswith("# checklist"):
            return body

        return f"# Checklist\n\n{body}"

    @classmethod
    def to_report(cls, markdown: str) -> str:
        body = str(markdown or "").strip()

        if body.lower().startswith("# relat"):
            return body

        return "\n".join(
            [
                "# Relatório",
                "",
                body,
                "",
                "## Conclusão",
                "",
                "- (preencha recomendações e próximos passos)",
            ]
        ).strip()

    @classmethod
    def to_minutes(cls, markdown: str) -> str:
        body = str(markdown or "").strip()

        if "ata de" in body.lower()[:80]:
            return body

        return "\n".join(
            [
                "# Ata de reunião",
                "",
                "## Participantes",
                "- ",
                "",
                "## Pauta",
                "- ",
                "",
                "## Pontos discutidos",
                "",
                body,
                "",
                "## Decisões",
                "- ",
                "",
                "## Pendências",
                "- [ ] ",
            ]
        ).strip()

    @classmethod
    def to_announcement(cls, markdown: str) -> str:
        body = str(markdown or "").strip()

        if body.lower().startswith("# comunicado"):
            return body

        return f"# Comunicado\n\n{body}"
