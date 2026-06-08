"""Construção de contexto RAG pós-tools — Fase 3C lote 19."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from app.application.services.chat_assistant_identity_service import (
    ChatAssistantIdentityService,
)
from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_working_memory_service import ChatWorkingMemoryService
from app.infrastructure.config.settings import Settings


@dataclass(frozen=True)
class ChatTurnPreparationRagResult:
    rag: dict
    sources: list[dict]
    workspace_context: dict
    conversation_context: str


class ChatTurnPreparationRagService:
    _STREAM_BUNDLE = "stream"
    _RAG_ACTIVITY_PREFIX = ("activity", "rag")

    @classmethod
    def _rag_text(cls, key: str, field: str, *, default: str = "") -> str:
        return ChatAssistantContentService.get(
            cls._STREAM_BUNDLE,
            *cls._RAG_ACTIVITY_PREFIX,
            key,
            field,
            default=default,
        )

    @classmethod
    def _rag_format(cls, key: str, field: str, *, default: str = "", **values) -> str:
        return ChatAssistantContentService.format(
            cls._STREAM_BUNDLE,
            *cls._RAG_ACTIVITY_PREFIX,
            key,
            field,
            default=default,
            **values,
        )

    @classmethod
    def build(
        cls,
        *,
        message: str,
        skip_rag: bool,
        workspace_context: dict,
        conversation_context: str,
        tool_context: dict,
        pipeline_stages: list[str],
        pipeline_timings,
        user_id,
        session,
        attachment_ids,
        rag_context_service,
        knowledge_scope_service,
        semantic_memory_service,
        on_stream_activity: Callable[..., None] | None = None,
    ) -> ChatTurnPreparationRagResult:
        assistant_identity_question = ChatAssistantIdentityService.is_assistant_identity_question(
            message
        )
        from app.domain.services.chat_technical_description_intent_service import (
            ChatTechnicalDescriptionIntentService,
        )

        technical_description_normas = (
            ChatTechnicalDescriptionIntentService.requires_normas_knowledge(message)
        )

        if on_stream_activity and not skip_rag:
            from app.application.services.chat_stream_activity_service import (
                ChatStreamActivityService,
            )

            on_stream_activity(
                ChatStreamActivityService.entry(
                    verb=cls._rag_text("searching", "verb"),
                    target=cls._rag_text("searching", "target"),
                    phase="rag",
                    state="active",
                    message=cls._rag_text("searching", "message"),
                    detail=cls._rag_text("searching", "detail"),
                    entry_id="rag-search",
                )
            )

        if skip_rag:
            rag = {"context": "", "sources": []}
            pipeline_stages.append("skip_rag")
        else:
            pipeline_stages.append("rag")
            rag_query = message
            rag_min_score = None

            if assistant_identity_question:
                rag_query = ChatAssistantIdentityService.build_rag_query(message)
                rag_min_score = Settings.RAG_IDENTITY_QUESTION_MIN_SCORE
            elif technical_description_normas:
                rag_query = ChatTechnicalDescriptionIntentService.build_rag_query(message)
            elif semantic_memory_service.should_use_enriched_query(workspace_context):
                rag_query = semantic_memory_service.resolve_rag_query(
                    message,
                    workspace_context=workspace_context,
                    default_query=rag_query,
                )

                if "semantic_memory" not in pipeline_stages:
                    pipeline_stages.append("semantic_memory")

            rag = rag_context_service.build_context(
                rag_query,
                filters=knowledge_scope_service.build_filters(
                    user_id=user_id,
                    session=session,
                    workspace_context=workspace_context,
                    attachment_ids=attachment_ids,
                ),
                min_score=rag_min_score,
                chunk_filter=(
                    ChatAssistantIdentityService.identity_chunk_filter()
                    if assistant_identity_question
                    else None
                ),
            )

        sources = rag["sources"]
        web_sources = tool_context.get("webSources") if isinstance(tool_context, dict) else None

        if isinstance(web_sources, list) and web_sources:
            sources = [*web_sources, *sources]

        if not skip_rag and semantic_memory_service.should_use_enriched_query(
            workspace_context
        ):
            workspace_context = semantic_memory_service.attach_rag_to_workspace(
                workspace_context,
                message=message,
                rag_result=rag,
            )

            from app.domain.services.chat_semantic_memory_retriever_service import (
                ChatSemanticMemoryRetrieverService,
            )

            semantic_block = ChatSemanticMemoryRetrieverService.format_prompt_block(
                workspace_context.get("workingMemory"),
            )

            if semantic_block:
                conversation_context = ChatWorkingMemoryService.merge_conversation_context(
                    conversation_context,
                    semantic_block,
                )

        try:
            from app.application.services.chat_glossary_retrieval_service import (
                ChatGlossaryRetrievalService,
            )

            glossary_block = ChatGlossaryRetrievalService().build_context_block_for(
                message=message,
                project_id=str((workspace_context.get("project") or {}).get("id") or "")
                or None,
            )

            if glossary_block:
                existing_rag_context = rag.get("context") or ""
                rag = {
                    **rag,
                    "context": (
                        f"{existing_rag_context}\n\n{glossary_block}"
                        if existing_rag_context
                        else glossary_block
                    ),
                }

                if "glossary" not in pipeline_stages:
                    pipeline_stages.append("glossary")
        except Exception:
            pass

        rag_context_chars = len(rag.get("context") or "")
        pipeline_timings.mark("rag_done")

        if on_stream_activity:
            from app.application.services.chat_stream_activity_service import (
                ChatStreamActivityService,
            )

            if skip_rag:
                on_stream_activity(
                    ChatStreamActivityService.entry(
                        verb=cls._rag_text("skipped", "verb"),
                        target=cls._rag_text("skipped", "target"),
                        phase="rag",
                        state="done",
                        message=cls._rag_text("skipped", "message"),
                        detail=cls._rag_text("skipped", "detail"),
                        entry_id="rag-search",
                    )
                )
            elif sources:
                count = len(sources)
                on_stream_activity(
                    ChatStreamActivityService.entry(
                        verb=cls._rag_text("foundSources", "verb"),
                        target=cls._rag_format(
                            "foundSources",
                            "targetTemplate",
                            count=count,
                        ),
                        phase="rag",
                        level="success",
                        state="done",
                        message=cls._rag_format(
                            "foundSources",
                            "messageTemplate",
                            count=count,
                        ),
                        detail=cls._rag_format(
                            "foundSources",
                            "detailTemplate",
                            count=count,
                        ),
                        entry_id="rag-search",
                    )
                )
            elif rag_context_chars > 0:
                on_stream_activity(
                    ChatStreamActivityService.entry(
                        verb=cls._rag_text("foundContext", "verb"),
                        target=cls._rag_text("foundContext", "target"),
                        phase="rag",
                        level="success",
                        state="done",
                        message=cls._rag_text("foundContext", "message"),
                        detail=cls._rag_format(
                            "foundContext",
                            "detailTemplate",
                            chars=rag_context_chars,
                        ),
                        entry_id="rag-search",
                    )
                )
            else:
                on_stream_activity(
                    ChatStreamActivityService.entry(
                        verb=cls._rag_text("empty", "verb"),
                        target=cls._rag_text("empty", "target"),
                        phase="rag",
                        level="warning",
                        state="done",
                        message=cls._rag_text("empty", "message"),
                        detail=cls._rag_text("empty", "detail"),
                        entry_id="rag-search",
                    )
                )

        return ChatTurnPreparationRagResult(
            rag=rag,
            sources=sources,
            workspace_context=workspace_context,
            conversation_context=conversation_context,
        )
