from app.infrastructure.config.settings import Settings


class ChatIntelligenceMetadataService:
    @staticmethod
    def build(
        *,
        sources: list[dict],
        tool_context: dict,
        embedding_cache_stats: dict | None = None,
    ) -> dict:
        scores = [
            float(item.get("score"))
            for item in sources
            if item.get("score") is not None
        ]

        metadata = {
            "ragSourceCount": len(sources),
            "topRagScore": max(scores) if scores else None,
            "toolCount": len(tool_context.get("toolCalls") or []),
            "agentic": tool_context.get("agentic"),
            "embeddingCacheBackend": Settings.EMBEDDING_CACHE_BACKEND,
        }

        if embedding_cache_stats:
            metadata["embeddingCache"] = embedding_cache_stats

        return metadata
