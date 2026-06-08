"""Construção de contexto RAG pós-tools — Fase 3C lote 19."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from app.application.services.chat_assistant_identity_service import (
    ChatAssistantIdentityService,
)
from app.domain.services.chat_working_memory_service import ChatWorkingMemoryService
from app.infrastructure.config.settings import Settings


@dataclass(frozen=True)
class ChatTurnPreparationRagResult:
    rag: dict
    sources: list[dict]
    workspace_context: dict
    conversation_context: str


class ChatTurnPreparationRagService:
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
                    verb="Buscando",
                    target="base de conhecimento",
                    phase="rag",
                    state="active",
                    message="Procurando nas informações de apoio...",
                    detail="Consultando a base de conhecimento autorizada.",
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
                        verb="Ignorado",
                        target="base de conhecimento",
                        phase="rag",
                        state="done",
                        message="Não precisei de documentos extras desta vez.",
                        detail="Base de conhecimento não necessária neste turno.",
                        entry_id="rag-search",
                    )
                )
            elif sources:
                on_stream_activity(
                    ChatStreamActivityService.entry(
                        verb="Encontrado",
                        target=f"{len(sources)} trecho(s) relevante(s)",
                        phase="rag",
                        level="success",
                        state="done",
                        message=(
                            f"Encontrei {len(sources)} trecho(s) útil(eis) "
                            "para te responder."
                        ),
                        detail=f"Base de conhecimento: {len(sources)} trecho(s) relevante(s).",
                        entry_id="rag-search",
                    )
                )
            elif rag_context_chars > 0:
                on_stream_activity(
                    ChatStreamActivityService.entry(
                        verb="Encontrado",
                        target="contexto documental",
                        phase="rag",
                        level="success",
                        state="done",
                        message="Encontrei material de apoio relevante.",
                        detail=(
                            "Base de conhecimento: contexto aplicado "
                            f"({rag_context_chars} caracteres)."
                        ),
                        entry_id="rag-search",
                    )
                )
            else:
                on_stream_activity(
                    ChatStreamActivityService.entry(
                        verb="Sem trechos",
                        target="nenhum trecho adicional",
                        phase="rag",
                        level="warning",
                        state="done",
                        message="Vou responder com o que já sei sobre isso.",
                        detail=(
                            "Base de conhecimento consultada; "
                            "nenhum trecho adicional aplicável."
                        ),
                        entry_id="rag-search",
                    )
                )

        return ChatTurnPreparationRagResult(
            rag=rag,
            sources=sources,
            workspace_context=workspace_context,
            conversation_context=conversation_context,
        )
