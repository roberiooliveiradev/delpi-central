"""Memória de trabalho e contexto de conversa pré-tool — Fase 3C lote 16."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.application.services.chat_intelligence_pipeline_service import (
    ChatIntelligencePipelineService,
)
from app.domain.services.chat_conversation_memory_service import (
    ChatConversationMemoryService,
)
from app.domain.services.chat_project_conversation_context_service import (
    ChatProjectConversationContextService,
)
from app.domain.services.chat_working_memory_service import ChatWorkingMemoryService


@dataclass(frozen=True)
class ChatTurnPreparationMemoryContextResult:
    workspace_context: dict
    working_memory_snapshot: dict
    conversation_context: str
    pipeline_stage_additions: list[str]


class ChatTurnPreparationMemoryContextService:
    @classmethod
    def build(
        cls,
        *,
        message: str,
        workspace_context: dict,
        history_source: list,
        attachments: list[dict],
        session,
        user_id,
        session_memory_service,
    ) -> ChatTurnPreparationMemoryContextResult:
        previous_agent_id = str(workspace_context.get("agentId") or "") or None

        working_memory_snapshot = ChatConversationMemoryService.build_pre_turn(
            message=message,
            previous_messages=history_source,
            session_memory_service=session_memory_service,
            session_id=getattr(session, "id", None) if session is not None else None,
            agent_id=str(workspace_context.get("agentId") or "") or None,
            project_id=str((workspace_context.get("project") or {}).get("id") or "")
            or None,
            attachments=attachments,
            previous_agent_id=previous_agent_id,
        )

        peer_context = ChatProjectConversationContextService.build(
            project=workspace_context.get("project"),
            session_id=getattr(session, "id", None) if session is not None else None,
            user_id=user_id,
        )

        if peer_context:
            working_memory_snapshot = ChatProjectConversationContextService.merge_memory_overlay(
                working_memory_snapshot,
                peer_context.memory_overlay,
            )

        updated_workspace = dict(workspace_context)

        if peer_context:
            updated_workspace["projectPeerSessionIds"] = peer_context.peer_session_ids

        updated_workspace["workingMemory"] = working_memory_snapshot

        memory_prompt = ChatConversationMemoryService.format_prompt_block(
            working_memory_snapshot
        )
        base_conversation_context = (
            ChatIntelligencePipelineService.build_conversation_context(history_source)
            if history_source
            else ""
        )
        conversation_context = ChatWorkingMemoryService.merge_conversation_context(
            memory_prompt,
            base_conversation_context,
        )

        pipeline_stage_additions: list[str] = []

        if peer_context and peer_context.conversation_text:
            conversation_context = ChatWorkingMemoryService.merge_conversation_context(
                conversation_context,
                peer_context.conversation_text,
            )
            pipeline_stage_additions.append("project_shared_context")

        try:
            from app.application.services.chat_user_memory_service import (
                ChatUserMemoryService,
            )

            user_memory_block = ChatUserMemoryService().format_prompt_block_for(
                user_id=str(user_id) if user_id else None,
                project_id=str((updated_workspace.get("project") or {}).get("id") or "")
                or None,
            )

            if user_memory_block:
                conversation_context = ChatWorkingMemoryService.merge_conversation_context(
                    conversation_context,
                    user_memory_block,
                )
                pipeline_stage_additions.append("user_memory")
        except Exception:
            pass

        from app.application.services.chat_attachment_multi_compare_service import (
            ChatAttachmentMultiCompareService,
        )

        attachment_compare_hint = ChatAttachmentMultiCompareService.build_context_hint(
            message=message,
            attachments=attachments,
        )

        if attachment_compare_hint:
            conversation_context = ChatWorkingMemoryService.merge_conversation_context(
                conversation_context,
                attachment_compare_hint,
            )
            pipeline_stage_additions.append("attachment_compare")

        return ChatTurnPreparationMemoryContextResult(
            workspace_context=updated_workspace,
            working_memory_snapshot=working_memory_snapshot,
            conversation_context=conversation_context,
            pipeline_stage_additions=pipeline_stage_additions,
        )
