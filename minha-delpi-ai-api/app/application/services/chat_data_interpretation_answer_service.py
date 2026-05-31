"""Respostas diretas para follow-ups de interpretação de dados operacionais."""

from __future__ import annotations

import json
from typing import Any

from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)


class ChatDataInterpretationAnswerService:
    _GENERIC_LINE_MARKERS = (
        "a api retornou",
        "a consulta retornou",
        "nenhum registro encontrado",
        "dados autorizados para a consulta",
        "visualização dos dados",
    )

    _GENERIC_TITLES = (
        "consulta sql",
        "resultado da api",
        "resultado operacional",
        "consulta",
    )

    @classmethod
    def build_answer(
        cls,
        message: str,
        previous_messages: list[Any] | None,
    ) -> str | None:
        if not ChatAnalysisIntentService.is_data_interpretation_request(
            message,
            previous_messages,
        ):
            return None

        from app.application.services.chat_text_task_composer_service import (
            ChatTextTaskComposerService,
        )

        draft_meta = ChatTextTaskComposerService.build_operational_email_with_metadata(
            message=message,
            previous_messages=previous_messages,
        )

        if draft_meta:
            from app.application.services.chat_email_answer_guard_service import (
                ChatEmailAnswerGuardService,
            )

            text, _guard = ChatEmailAnswerGuardService.apply(
                str(draft_meta.get("text") or ""),
                message=message,
                workspace_context={"emailWritingMode": True, "operationalEmailDraft": draft_meta},
            )
            return text or None

        summaries = cls._collect_summaries(previous_messages)

        if not summaries:
            return None

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        latest = summaries[-1]
        title = str(latest.get("titulo") or "Consulta anterior").strip()
        lines = [
            str(line).strip()
            for line in (latest.get("linhas") or [])
            if str(line or "").strip() and not cls._is_generic_line(str(line))
        ]

        if not lines:
            return None

        if normalized in {"resume", "resuma", "resumir"} or normalized.startswith("resume "):
            return cls._format_summary(title, lines, heading="Resumo")

        if any(term in normalized for term in ("traduz", "traduca", "traduza", "traduzir")):
            return cls._format_summary(
                title,
                lines,
                heading="Tradução em linguagem simples",
                intro="Reformulei os dados da consulta anterior em linguagem mais acessível:",
            )

        if "nao entendi" in normalized or "não entendi" in normalized:
            return cls._format_summary(
                title,
                lines,
                heading="Explicação",
                intro="Vou explicar de outro jeito o que os dados anteriores mostram:",
            )

        if "o que isso quer dizer" in normalized or "o que significa" in normalized:
            return cls._format_summary(
                title,
                lines,
                heading="Significado dos dados",
                intro="Em termos práticos, os dados da consulta anterior indicam o seguinte:",
            )

        return cls._format_summary(
            title,
            lines,
            heading="Explicação dos dados",
            intro="Com base na consulta operacional já feita nesta conversa:",
        )

    @classmethod
    def _format_summary(
        cls,
        title: str,
        lines: list[str],
        *,
        heading: str,
        intro: str | None = None,
    ) -> str:
        body = "\n".join(f"- {line}" for line in lines[:12])
        parts = [f"**{heading} — {title}**"]

        if intro:
            parts.append(intro)

        parts.append(body)

        if len(lines) > 12:
            parts.append(f"_… e mais {len(lines) - 12} detalhe(s) na consulta original._")

        return "\n\n".join(parts)

    @classmethod
    def _collect_summaries(cls, previous_messages: list[Any] | None) -> list[dict]:
        if not previous_messages:
            return []

        collected: list[dict] = []

        for item in previous_messages[-12:]:
            metadata = cls._message_metadata(item)

            for tool_call in metadata.get("toolCalls") or []:
                if not isinstance(tool_call, dict):
                    continue

                if str(tool_call.get("name") or "") != "execute_external_action":
                    continue

                tool_meta = tool_call.get("metadata")

                if not isinstance(tool_meta, dict) or not tool_meta.get("ok"):
                    continue

                summary = cls._resolve_tool_summary(tool_meta)

                if summary:
                    collected.append(summary)

        return collected

    @classmethod
    def _resolve_tool_summary(cls, tool_meta: dict) -> dict | None:
        path = str(tool_meta.get("path") or "").strip()
        humanized = tool_meta.get("humanizedSummary")

        if isinstance(humanized, dict):
            title = str(humanized.get("titulo") or "").strip()
            lines = [
                str(line).strip()
                for line in (humanized.get("linhas") or [])
                if str(line or "").strip()
            ]

            if title and title.lower() not in cls._GENERIC_TITLES and cls._has_substantive_lines(lines):
                return {"titulo": title, "linhas": lines, "path": path}

            if cls._has_substantive_lines(lines):
                return {
                    "titulo": title or cls._title_from_path(path),
                    "linhas": lines,
                    "path": path,
                }

        preview = str(tool_meta.get("responsePreview") or "").strip()

        if not preview or not path:
            return None

        try:
            from app.domain.services.external_actions.external_action_result_presenter import (
                ExternalActionResultPresenter,
            )

            data = json.loads(preview)
            represented = ExternalActionResultPresenter().present(data, path=path)
        except (json.JSONDecodeError, TypeError, ValueError):
            return None

        if not isinstance(represented, dict):
            return None

        title = str(represented.get("titulo") or cls._title_from_path(path)).strip()
        lines = [
            str(line).strip()
            for line in (represented.get("linhas") or [])
            if str(line or "").strip()
        ]

        if not cls._has_substantive_lines(lines):
            return None

        return {"titulo": title, "linhas": lines, "path": path}

    @classmethod
    def _has_substantive_lines(cls, lines: list[str]) -> bool:
        substantive = [line for line in lines if not cls._is_generic_line(line)]

        return len(substantive) >= 1

    @classmethod
    def _is_generic_line(cls, line: str) -> bool:
        lowered = line.lower()

        return any(marker in lowered for marker in cls._GENERIC_LINE_MARKERS)

    @classmethod
    def _title_from_path(cls, path: str) -> str:
        lowered = str(path or "").lower()

        if "/guide" in lowered:
            return "Roteiro do produto"

        if "/stock" in lowered:
            return "Estoque do produto"

        if "/structure" in lowered:
            return "Estrutura do produto"

        if "/inspection" in lowered:
            return "Inspeção do produto"

        return "Consulta operacional"

    @classmethod
    def _message_metadata(cls, message) -> dict:
        if isinstance(message, dict):
            metadata = message.get("metadata")
            return metadata if isinstance(metadata, dict) else {}

        metadata = getattr(message, "metadata", None)

        return metadata if isinstance(metadata, dict) else {}
