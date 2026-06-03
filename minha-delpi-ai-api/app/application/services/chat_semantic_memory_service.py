"""Ponte entre memória semântica (domínio) e RAG existente — Fase 5."""

from __future__ import annotations

from typing import Any

from app.application.services.rag_context_service import RagContextService
from app.domain.services.chat_semantic_memory_retriever_service import (
    ChatSemanticMemoryRetrieverService,
)


class ChatSemanticMemoryService:
    def __init__(self, rag_context_service: RagContextService | None = None):
        self.rag_context_service = rag_context_service

    def resolve_rag_query(
        self,
        message: str,
        *,
        workspace_context: dict | None = None,
        default_query: str | None = None,
    ) -> str:
        snapshot = (workspace_context or {}).get("workingMemory") or {}

        if snapshot.get("semanticMemoryQuery"):
            return str(snapshot["semanticMemoryQuery"])

        enriched = ChatSemanticMemoryRetrieverService.build_enriched_query(message, snapshot)

        if enriched:
            return enriched

        return default_query or message

    def should_use_enriched_query(self, workspace_context: dict | None) -> bool:
        snapshot = (workspace_context or {}).get("workingMemory") or {}

        return bool(snapshot.get("semanticMemoryRequested"))

    def attach_rag_to_workspace(
        self,
        workspace_context: dict,
        *,
        message: str,
        rag_result: dict[str, Any],
        raw_chunks: list[dict[str, Any]] | None = None,
    ) -> dict:
        context = dict(workspace_context)
        snapshot = dict(context.get("workingMemory") or {})
        updated = ChatSemanticMemoryRetrieverService.attach_rag_result(
            snapshot,
            message=message,
            rag_context=str(rag_result.get("context") or ""),
            sources=rag_result.get("sources"),
            chunks=raw_chunks,
        )
        context["workingMemory"] = updated
        return context

    def build_context(
        self,
        query: str,
        filters: dict | None,
        *,
        min_score: float | None = None,
    ) -> dict:
        if not self.rag_context_service:
            return {"context": "", "sources": []}

        return self.rag_context_service.build_context(
            query,
            filters=filters,
            min_score=min_score,
        )
