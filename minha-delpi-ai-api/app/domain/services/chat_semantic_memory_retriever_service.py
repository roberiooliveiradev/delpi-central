"""Orquestração de memória semântica no domínio — Playbook memória e contexto (Fase 5)."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_context_ranking_service import ChatContextRankingService
from app.domain.services.chat_procedural_memory_provider_service import (
    ChatProceduralMemoryProviderService,
)
from app.domain.services.chat_semantic_memory_intent_service import (
    ChatSemanticMemoryIntentService,
)
from app.domain.services.keyword_similarity import keyword_overlap_score


class ChatSemanticMemoryRetrieverService:
    MAX_HIT_SNIPPET_CHARS = 280

    @classmethod
    def apply_pre_turn(
        cls,
        snapshot: dict,
        *,
        message: str | None,
    ) -> dict:
        result = dict(snapshot)
        intent_kind = ChatSemanticMemoryIntentService.intent_kind(message, snapshot=result)
        result = ChatProceduralMemoryProviderService.apply_to_snapshot(
            result,
            message=message,
            intent_kind=intent_kind,
        )
        result["semanticMemoryIntent"] = intent_kind
        result["semanticMemoryRequested"] = (
            ChatSemanticMemoryIntentService.should_enrich_semantic_retrieval(
                message,
                snapshot=result,
            )
        )

        if result["semanticMemoryRequested"]:
            result["semanticMemoryQuery"] = cls.build_enriched_query(message, result)

        return result

    @classmethod
    def build_enriched_query(cls, message: str | None, snapshot: dict | None) -> str:
        parts: list[str] = [(message or "").strip()]
        snap = snapshot or {}
        state = snap.get("conversationState") or {}
        topic = str(state.get("activeTopic") or "").strip()

        if topic:
            parts.append(f"assunto: {topic}")

        task = state.get("activeTask")

        if isinstance(task, dict):
            objective = str(task.get("objective") or task.get("label") or "").strip()

            if objective:
                parts.append(f"tarefa: {objective[:160]}")

        entities = dict(snap.get("lastEntities") or {})
        active = snap.get("activeEntities") or {}

        if isinstance(active, dict):
            entities.update({k: v for k, v in active.items() if v})

        if entities.get("productCode"):
            parts.append(f"produto {entities['productCode']}")

        for hint in snap.get("proceduralMemoryHints") or []:
            if not isinstance(hint, dict):
                continue

            boost = str(hint.get("queryBoost") or "").strip()

            if boost:
                parts.append(boost)

        summary = snap.get("conversationSummary") or {}

        if isinstance(summary, dict) and summary.get("summary"):
            parts.append(str(summary["summary"])[:200])

        merged = " ".join(part for part in parts if part).strip()

        return merged[:1200] or (message or "").strip()

    @classmethod
    def normalize_hits(
        cls,
        chunks: list[dict[str, Any]],
        *,
        message: str | None = None,
        snapshot: dict | None = None,
    ) -> list[dict[str, Any]]:
        hits: list[dict[str, Any]] = []
        task_type = ChatContextRankingService._active_task_type(snapshot or {})

        for index, chunk in enumerate(chunks):
            if not isinstance(chunk, dict):
                continue

            content = str(chunk.get("content") or "").strip()

            if not content:
                continue

            metadata = chunk.get("metadata") or {}
            title = str(chunk.get("title") or "Documento").strip()
            semantic_score = float(chunk.get("score") or 0)
            overlap = keyword_overlap_score(message or "", content)
            kind = str(metadata.get("category") or chunk.get("sourceType") or "knowledge")

            hits.append(
                {
                    "id": str(chunk.get("id") or index),
                    "documentId": str(chunk.get("documentId") or ""),
                    "title": title,
                    "kind": kind,
                    "sourceType": chunk.get("sourceType"),
                    "sourceRef": chunk.get("sourceRef"),
                    "score": semantic_score,
                    "semanticScore": semantic_score,
                    "recencyScore": max(0.2, 1.0 - index * 0.08),
                    "sourceAuthority": cls._source_authority(chunk),
                    "confidence": min(1.0, semantic_score + 0.15 * overlap),
                    "taskHint": task_type,
                    "taskMatch": bool(
                        task_type
                        and task_type in str(metadata.get("domain") or "").lower()
                    ),
                    "snippet": content[: cls.MAX_HIT_SNIPPET_CHARS],
                }
            )

        return ChatContextRankingService.rank_hits(
            hits,
            message=message,
            snapshot=snapshot,
        )

    @classmethod
    def attach_rag_result(
        cls,
        snapshot: dict,
        *,
        message: str | None,
        rag_context: str | None,
        sources: list[dict[str, Any]] | None,
        chunks: list[dict[str, Any]] | None = None,
    ) -> dict:
        result = dict(snapshot)
        normalized_sources = [
            {
                "id": str(item.get("id") or ""),
                "title": item.get("title"),
                "sourceType": item.get("sourceType"),
                "sourceRef": item.get("sourceRef"),
                "score": item.get("score"),
                "scope": (item.get("scope") if isinstance(item, dict) else None)
                or (item.get("metadata") or {}).get("scope")
                if isinstance(item, dict)
                else None,
            }
            for item in (sources or [])
            if isinstance(item, dict)
        ]

        hit_chunks = list(chunks or [])

        if not hit_chunks and normalized_sources:
            hit_chunks = [
                {
                    "id": item.get("id"),
                    "documentId": item.get("documentId"),
                    "title": item.get("title"),
                    "sourceType": item.get("sourceType"),
                    "sourceRef": item.get("sourceRef"),
                    "score": item.get("score"),
                    "content": "",
                    "metadata": {"scope": item.get("scope")},
                }
                for item in normalized_sources
            ]

        hits = cls.normalize_hits(hit_chunks, message=message, snapshot=result)

        result["semanticMemoryHits"] = hits
        result["semanticMemoryUsed"] = bool(hits or (rag_context or "").strip())
        result["semanticMemorySourceCount"] = len(normalized_sources)

        if rag_context:
            result["semanticMemoryContextChars"] = len(rag_context)

        return result

    @classmethod
    def format_prompt_block(cls, snapshot: dict | None) -> str | None:
        hits = (snapshot or {}).get("semanticMemoryHits") or []

        if not hits:
            return None

        lines: list[str] = []

        for hit in hits[:4]:
            if not isinstance(hit, dict):
                continue

            title = str(hit.get("title") or "Fonte").strip()
            score = hit.get("rankScore") if hit.get("rankScore") is not None else hit.get("score")
            snippet = str(hit.get("snippet") or "").strip()

            score_label = f"{float(score):.2f}" if score is not None else "n/d"

            if snippet:
                clipped = snippet[:220]
                suffix = "…" if len(snippet) > 220 else ""
                lines.append(f"- {title} (relevância {score_label}): {clipped}{suffix}")
            else:
                lines.append(f"- {title} (relevância {score_label}).")

        if not lines:
            return None

        return "Memória semântica (documentação/playbooks):\n" + "\n".join(lines)

    @classmethod
    def compact_for_admin_debug(cls, snapshot: dict | None) -> dict[str, Any]:
        hits = (snapshot or {}).get("semanticMemoryHits") or []

        return {
            "requested": bool((snapshot or {}).get("semanticMemoryRequested")),
            "intent": (snapshot or {}).get("semanticMemoryIntent"),
            "hitsCount": len(hits),
            "topTitles": [
                str(item.get("title") or "") for item in hits[:3] if isinstance(item, dict)
            ],
            "contextChars": (snapshot or {}).get("semanticMemoryContextChars") or 0,
            "procedural": ChatProceduralMemoryProviderService.compact_for_admin_debug(snapshot),
        }

    @staticmethod
    def _source_authority(chunk: dict[str, Any]) -> float:
        metadata = chunk.get("metadata") or {}
        scope = str(metadata.get("scope") or "").lower()
        source_type = str(chunk.get("sourceType") or "").lower()

        if scope == "global":
            return 0.95

        if "playbook" in source_type or "policy" in source_type:
            return 0.9

        if scope in ("project", "session"):
            return 0.75

        return 0.65
