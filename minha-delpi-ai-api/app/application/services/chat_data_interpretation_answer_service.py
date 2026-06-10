"""Respostas diretas para follow-ups de interpretação de dados operacionais."""

from __future__ import annotations

import json
from typing import Any

from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService
from app.domain.services.chat_assistant_content_service import (
    ChatAssistantContentService,
)
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)

_CONTENT_BUNDLE = "data_interpretation"


class ChatDataInterpretationAnswerService:
    @classmethod
    def _generic_line_markers(cls) -> tuple[str, ...]:
        return tuple(
            ChatAssistantContentService.list(_CONTENT_BUNDLE, "genericLineMarkers")
        )

    @classmethod
    def _generic_titles(cls) -> tuple[str, ...]:
        return tuple(
            ChatAssistantContentService.list(_CONTENT_BUNDLE, "genericTitles")
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

        from app.domain.services.chat_presentation_row_detail_answer_service import (
            ChatPresentationRowDetailAnswerService,
        )

        if ChatPresentationRowDetailAnswerService.looks_like_request(message):
            return ChatPresentationRowDetailAnswerService.build_answer(
                message,
                previous_messages,
            )

        if ChatAnalysisIntentService.is_email_from_operational_data_request(
            message,
            previous_messages,
        ):
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

        commentary_answer = cls._build_commentary_answer(message, previous_messages)

        if commentary_answer:
            return commentary_answer

        summaries = cls._collect_summaries(previous_messages)

        if not summaries:
            return None

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        latest = summaries[-1]
        title = str(
            latest.get("titulo")
            or ChatAssistantContentService.get(
                _CONTENT_BUNDLE, "defaultTitle", default="Consulta anterior"
            )
        ).strip()
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

        if (
            "o que isso quer dizer" in normalized
            or "o que isso significa" in normalized
            or "o que significa" in normalized
        ):
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
    def _build_commentary_answer(
        cls,
        message: str,
        previous_messages: list[Any] | None,
    ) -> str | None:
        commentary = cls._resolve_latest_data_commentary(previous_messages)

        if not commentary:
            return None

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        title = str(
            cls._resolve_commentary_title(previous_messages)
            or ChatAssistantContentService.get(
                _CONTENT_BUNDLE,
                "defaultTitle",
                default="Consulta anterior",
            )
        ).strip()
        highlights = [
            str(line).strip()
            for line in (commentary.get("highlights") or [])
            if str(line or "").strip()
        ]
        attention = [
            str(line).strip()
            for line in (commentary.get("attention") or [])
            if str(line or "").strip()
        ]
        narrative = str(commentary.get("narrativeInsight") or "").strip()

        if not highlights and not attention and not narrative:
            return None

        if normalized in {"resume", "resuma", "resumir"} or normalized.startswith("resume "):
            lines = highlights[:6] or ([narrative] if narrative else [])
            return cls._format_summary(title, lines, heading="Resumo")

        if any(term in normalized for term in ("traduz", "traduca", "traduza", "traduzir")):
            lines = highlights[:8] or ([narrative] if narrative else [])
            return cls._format_summary(
                title,
                lines,
                heading="Tradução em linguagem simples",
                intro="Reformulei os dados da consulta anterior em linguagem mais acessível:",
            )

        if "nao entendi" in normalized or "não entendi" in normalized:
            lines = (highlights + attention)[:8] or ([narrative] if narrative else [])
            return cls._format_summary(
                title,
                lines,
                heading="Explicação",
                intro="Vou explicar de outro jeito o que os dados anteriores mostram:",
            )

        if (
            "o que isso quer dizer" in normalized
            or "o que isso significa" in normalized
            or "o que significa" in normalized
        ):
            lines = (highlights + attention)[:8] or ([narrative] if narrative else [])
            return cls._format_summary(
                title,
                lines,
                heading="Significado dos dados",
                intro="Em termos práticos, os dados da consulta anterior indicam o seguinte:",
            )

        lines = highlights[:6]

        if attention:
            lines.extend(f"[Atenção] {line}" for line in attention[:3])

        if narrative and narrative not in lines:
            lines.insert(0, narrative)

        if not lines:
            return None

        return cls._format_summary(
            title,
            lines,
            heading="Explicação dos dados",
            intro="Com base na consulta operacional já feita nesta conversa:",
        )

    @classmethod
    def _resolve_latest_data_commentary(
        cls,
        previous_messages: list[Any] | None,
    ) -> dict | None:
        if not previous_messages:
            return None

        for item in reversed(previous_messages[-12:]):
            metadata = cls._message_metadata(item)

            for tool_call in reversed(metadata.get("toolCalls") or []):
                if not isinstance(tool_call, dict):
                    continue

                if str(tool_call.get("name") or "") != "execute_external_action":
                    continue

                tool_meta = tool_call.get("metadata")

                if not isinstance(tool_meta, dict) or not tool_meta.get("ok"):
                    continue

                commentary = tool_meta.get("dataCommentary")

                if isinstance(commentary, dict) and (
                    commentary.get("highlights")
                    or commentary.get("attention")
                    or commentary.get("narrativeInsight")
                ):
                    return commentary

        return None

    @classmethod
    def _resolve_commentary_title(cls, previous_messages: list[Any] | None) -> str:
        if not previous_messages:
            return ""

        for item in reversed(previous_messages[-12:]):
            metadata = cls._message_metadata(item)

            for tool_call in reversed(metadata.get("toolCalls") or []):
                if not isinstance(tool_call, dict):
                    continue

                tool_meta = tool_call.get("metadata")

                if not isinstance(tool_meta, dict):
                    continue

                humanized = tool_meta.get("humanizedSummary")

                if isinstance(humanized, dict):
                    title = str(humanized.get("titulo") or "").strip()

                    if title:
                        return title

        return ""

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
        commentary = tool_meta.get("dataCommentary")
        commentary_lines: list[str] = []

        if isinstance(commentary, dict):
            commentary_lines = [
                str(line).strip()
                for line in (commentary.get("highlights") or [])
                if str(line or "").strip()
            ]
            narrative = str(commentary.get("narrativeInsight") or "").strip()

            if narrative and narrative not in commentary_lines:
                commentary_lines.insert(0, narrative)

            attention = [
                str(line).strip()
                for line in (commentary.get("attention") or [])
                if str(line or "").strip()
            ]
            commentary_lines.extend(
                line for line in attention if line not in commentary_lines
            )

        if isinstance(humanized, dict):
            title = str(humanized.get("titulo") or "").strip()
            lines = [
                str(line).strip()
                for line in (humanized.get("linhas") or [])
                if str(line or "").strip()
            ]

            for line in commentary_lines:
                if line not in lines:
                    lines.append(line)

            if (
                title
                and title.lower() not in cls._generic_titles()
                and cls._has_substantive_lines(lines)
            ):
                return {"titulo": title, "linhas": lines, "path": path}

            if cls._has_substantive_lines(lines):
                return {
                    "titulo": title or cls._title_from_path(path),
                    "linhas": lines,
                    "path": path,
                }

        if cls._has_substantive_lines(commentary_lines):
            return {
                "titulo": cls._title_from_path(path),
                "linhas": commentary_lines,
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

        return any(marker in lowered for marker in cls._generic_line_markers())

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
