class ChatIntelligenceMetadataService:
    @staticmethod
    def build(*, sources: list[dict], tool_context: dict) -> dict:
        scores = [
            float(item.get("score"))
            for item in sources
            if item.get("score") is not None
        ]

        return {
            "ragSourceCount": len(sources),
            "topRagScore": max(scores) if scores else None,
            "toolCount": len(tool_context.get("toolCalls") or []),
            "agentic": tool_context.get("agentic"),
        }
