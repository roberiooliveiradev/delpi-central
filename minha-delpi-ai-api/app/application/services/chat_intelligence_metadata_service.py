from app.infrastructure.config.settings import Settings


class ChatIntelligenceMetadataService:
    @staticmethod
    def build_pipeline_flags(
        *,
        fast_path: bool,
        operational_optimize: bool,
        tool_context: dict,
        skip_rag: bool,
        analysis_mode: bool = False,
        stages: list[str] | None = None,
        direct_answer: str | None = None,
    ) -> dict:
        resolved_direct = str(direct_answer or "").strip() or str(
            tool_context.get("directAnswer") or ""
        ).strip()
        flags = {
            "fastPath": bool(fast_path),
            "operationalFastPath": bool(operational_optimize),
            "analysisMode": bool(
                analysis_mode or tool_context.get("analysisMode")
            ),
            "directResponse": bool(resolved_direct),
            "skipRag": bool(skip_rag),
        }
        if stages:
            flags["stages"] = list(stages)
        return flags

    @staticmethod
    def build(
        *,
        sources: list[dict],
        tool_context: dict,
        embedding_cache_stats: dict | None = None,
        pipeline_timings: dict | None = None,
        pipeline: dict | None = None,
        rag_stats: dict | None = None,
    ) -> dict:
        scores = [
            float(item.get("score"))
            for item in sources
            if item.get("score") is not None
        ]

        stats = rag_stats if isinstance(rag_stats, dict) else {}
        visible_count = int(stats.get("visibleSourceCount", len(sources)))
        retrieved_count = int(stats.get("retrievedSourceCount", visible_count))
        retrieved_chunks = int(stats.get("retrievedChunkCount", 0))

        metadata = {
            "ragSourceCount": visible_count,
            "ragVisibleSourceCount": visible_count,
            "ragRetrievedCount": retrieved_count,
            "ragRetrievedChunkCount": retrieved_chunks,
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

        if tool_context.get("drawingAnalysisMode"):
            metadata["drawingAnalysisMode"] = True

        drawing_analysis = tool_context.get("drawingAnalysis")

        if isinstance(drawing_analysis, dict):
            metadata["drawingAnalysis"] = drawing_analysis

        drawing_export = tool_context.get("drawingAnalysisExport")

        if isinstance(drawing_export, dict) and drawing_export.get("markdown"):
            metadata["drawingAnalysisExport"] = drawing_export

        document_vision = tool_context.get("documentVision")

        if isinstance(document_vision, dict) and document_vision:
            metadata["documentVision"] = document_vision

        return metadata
