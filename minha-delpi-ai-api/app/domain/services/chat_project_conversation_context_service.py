"""Contexto de outras conversas do mesmo projeto (opt-in)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from app.domain.services.chat_project_settings_service import ChatProjectSettingsService
from app.extensions.db import db
from app.infrastructure.db.models.chat_message_model import AiChatMessageModel
from app.infrastructure.db.models.chat_session_memory_model import AiChatSessionMemoryModel
from app.infrastructure.db.models.chat_session_model import AiChatSessionModel

_MAX_PEER_SESSIONS = 5
_MAX_LINES_PER_SESSION = 6
_ENTITY_KEYS = frozenset({"productCode", "branch", "period"})
_BEHAVIOR_KEYS = frozenset(
    {
        "responseFormat",
        "tone",
        "answerLength",
        "emailWriting",
        "textCorrection",
        "scope",
        "finalVersionOnly",
        "interactivityUsage",
    }
)


@dataclass(frozen=True)
class ProjectPeerContextBundle:
    conversation_text: str
    peer_session_ids: list[str]
    memory_overlay: dict[str, Any]


class ChatProjectConversationContextService:
    @classmethod
    def build(
        cls,
        *,
        project: dict[str, Any] | None,
        session_id: UUID | None,
        user_id: UUID | None,
    ) -> ProjectPeerContextBundle | None:
        if not project or not session_id or not user_id:
            return None

        metadata = project.get("metadata")
        share_enabled = bool(project.get("shareConversationContext")) or (
            ChatProjectSettingsService.share_conversation_context_enabled(metadata)
        )

        if not share_enabled:
            return None

        project_id = project.get("id")

        if not project_id:
            return None

        try:
            parsed_project_id = UUID(str(project_id))
        except ValueError:
            return None

        peer_sessions = cls._list_peer_sessions(
            project_id=parsed_project_id,
            exclude_session_id=session_id,
            user_id=user_id,
        )

        if not peer_sessions:
            return None

        peer_ids = [str(item.id) for item in peer_sessions]
        snippets = cls._build_session_snippets(peer_sessions)
        memory_overlay = cls._load_peer_memory_overlay(
            project_id=parsed_project_id,
            exclude_session_id=session_id,
        )

        project_name = str(project.get("name") or "projeto").strip()
        lines = [
            f"[Contexto compartilhado do projeto «{project_name}»]",
            "Resumo de outras conversas neste projeto (referência; a conversa atual continua independente):",
            "",
        ]
        lines.extend(snippets)

        return ProjectPeerContextBundle(
            conversation_text="\n".join(lines).strip(),
            peer_session_ids=peer_ids,
            memory_overlay=memory_overlay,
        )

    @classmethod
    def merge_memory_overlay(cls, snapshot: dict, overlay: dict[str, Any]) -> dict:
        if not overlay:
            return snapshot

        merged = dict(snapshot)
        entities = dict(merged.get("lastEntities") or {})
        behavior = dict(merged.get("behaviorInstructions") or {})

        for key, value in (overlay.get("lastEntities") or {}).items():
            if key not in entities or not str(entities.get(key) or "").strip():
                entities[key] = value

        for key, value in (overlay.get("behaviorInstructions") or {}).items():
            if key not in behavior or not str(behavior.get(key) or "").strip():
                behavior[key] = value

        merged["lastEntities"] = entities
        merged["behaviorInstructions"] = behavior

        if entities or behavior:
            merged["projectMemoryApplied"] = True

        return merged

    @classmethod
    def _list_peer_sessions(
        cls,
        *,
        project_id: UUID,
        exclude_session_id: UUID,
        user_id: UUID,
    ) -> list[AiChatSessionModel]:
        return (
            AiChatSessionModel.query.filter(
                AiChatSessionModel.project_id == project_id,
                AiChatSessionModel.user_id == user_id,
                AiChatSessionModel.id != exclude_session_id,
                AiChatSessionModel.archived_at.is_(None),
            )
            .order_by(AiChatSessionModel.updated_at.desc())
            .limit(_MAX_PEER_SESSIONS)
            .all()
        )

    @classmethod
    def _build_session_snippets(cls, sessions: list[AiChatSessionModel]) -> list[str]:
        blocks: list[str] = []

        for session in sessions:
            title = str(session.title or "Conversa").strip()
            header = f"### {title}"
            lines = cls._recent_message_lines(session.id)

            if not lines:
                continue

            blocks.append(header)
            blocks.extend(lines[:_MAX_LINES_PER_SESSION])
            blocks.append("")

        return blocks

    @classmethod
    def _recent_message_lines(cls, session_id: UUID) -> list[str]:
        rows = (
            AiChatMessageModel.query.filter(
                AiChatMessageModel.session_id == session_id,
            )
            .order_by(AiChatMessageModel.created_at.desc())
            .limit(8)
            .all()
        )

        lines: list[str] = []

        for row in reversed(rows):
            role = str(row.role or "").strip()

            if role == "user":
                content = str(row.content or "").strip()

                if content:
                    lines.append(f"- Usuário: {content[:280]}")

                continue

            if role != "assistant":
                continue

            metadata = row.message_metadata if isinstance(row.message_metadata, dict) else {}
            humanized = metadata.get("humanizedSummary")

            if isinstance(humanized, dict):
                titulo = str(humanized.get("titulo") or "").strip()
                summary_lines = [
                    str(line).strip()
                    for line in (humanized.get("linhas") or [])
                    if str(line or "").strip()
                ]

                if titulo:
                    lines.append(f"- Assistente ({titulo}):")

                for summary_line in summary_lines[:4]:
                    lines.append(f"  · {summary_line[:320]}")

                if titulo or summary_lines:
                    continue

            content = str(row.content or "").strip()

            if content:
                lines.append(f"- Assistente: {content[:320]}")

            tool_calls = metadata.get("toolCalls")

            if isinstance(tool_calls, list):
                for call in tool_calls[-2:]:
                    if not isinstance(call, dict):
                        continue

                    call_meta = call.get("metadata")

                    if not isinstance(call_meta, dict):
                        continue

                    tool_humanized = call_meta.get("humanizedSummary")

                    if not isinstance(tool_humanized, dict):
                        continue

                    tool_title = str(tool_humanized.get("titulo") or "").strip()

                    if tool_title:
                        lines.append(f"  · Consulta: {tool_title[:200]}")

        return lines

    @classmethod
    def _load_peer_memory_overlay(
        cls,
        *,
        project_id: UUID,
        exclude_session_id: UUID,
    ) -> dict[str, Any]:
        session_ids = [
            row[0]
            for row in db.session.query(AiChatSessionModel.id)
            .filter(
                AiChatSessionModel.project_id == project_id,
                AiChatSessionModel.id != exclude_session_id,
                AiChatSessionModel.archived_at.is_(None),
            )
            .order_by(AiChatSessionModel.updated_at.desc())
            .limit(_MAX_PEER_SESSIONS)
            .all()
        ]

        if not session_ids:
            return {"lastEntities": {}, "behaviorInstructions": {}}

        rows = (
            AiChatSessionMemoryModel.query.filter(
                AiChatSessionMemoryModel.session_id.in_(session_ids),
                AiChatSessionMemoryModel.active.is_(True),
            )
            .order_by(AiChatSessionMemoryModel.updated_at.desc())
            .all()
        )

        entities: dict[str, str] = {}
        behavior: dict[str, str] = {}

        for row in rows:
            value = row.value_json
            scalar = value if isinstance(value, str) else str(value or "").strip()

            if not scalar:
                continue

            if row.memory_type == "entity" and row.key in _ENTITY_KEYS:
                entities.setdefault(row.key, scalar)
            elif row.memory_type == "behavior" and row.key in _BEHAVIOR_KEYS:
                behavior.setdefault(row.key, scalar)

        return {
            "lastEntities": entities,
            "behaviorInstructions": behavior,
        }
