from app.infrastructure.config.settings import Settings


class ChatIntelligenceMetadataService:
    @staticmethod
    def build_pipeline_flags(
        *,
        fast_path: bool,
        operational_optimize: bool,
        tool_context: dict,
        skip_rag: bool,
    ) -> dict:
        return {
            "fastPath": bool(fast_path),
            "operationalFastPath": bool(operational_optimize),
            "directResponse": bool(tool_context.get("directAnswer")),
            "skipRag": bool(skip_rag),
        }

    @staticmethod
    def build(
        *,
        sources: list[dict],
        tool_context: dict,
        embedding_cache_stats: dict | None = None,
        pipeline_timings: dict | None = None,
        pipeline: dict | None = None,
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
            "nativeToolCalling": tool_context.get("nativeToolCalling"),
            "embeddingCacheBackend": Settings.EMBEDDING_CACHE_BACKEND,
        }

        if embedding_cache_stats:
            metadata["embeddingCache"] = embedding_cache_stats

        if pipeline_timings:
            metadata["timings"] = pipeline_timings

        selected_external_action = tool_context.get("selectedExternalAction")

        if isinstance(selected_external_action, dict) and selected_external_action.get(
            "actionId"
        ):
            metadata["selectedExternalAction"] = selected_external_action

        if pipeline:
            metadata["pipeline"] = pipeline

        return metadata
