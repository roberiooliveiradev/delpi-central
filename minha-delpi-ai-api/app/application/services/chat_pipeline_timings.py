import time


class ChatPipelineTimings:
    """Pipeline wall spans in real prep order: preTool → tools → postTool → rag → llm."""

    def __init__(self):
        self._started_at = time.perf_counter()
        self._marks: dict[str, float] = {"start": self._started_at}

    def mark(self, key: str) -> None:
        self._marks[key] = time.perf_counter()

    def span_ms(self, start_key: str, end_key: str) -> int | None:
        start = self._marks.get(start_key)
        end = self._marks.get(end_key)

        if start is None or end is None:
            return None

        return max(0, int((end - start) * 1000))

    def elapsed_sec(self) -> float:
        return max(0.0, time.perf_counter() - self._started_at)

    def to_dict(self) -> dict:
        total_ms = max(0, int((time.perf_counter() - self._started_at) * 1000))

        return {
            "preToolMs": self.span_ms("start", "pre_tool_done"),
            "toolsMs": self.span_ms("pre_tool_done", "tools_done"),
            "postToolMs": self.span_ms("tools_done", "post_tool_done"),
            "ragMs": self.span_ms("post_tool_done", "rag_done"),
            "llmMs": self.span_ms("rag_done", "llm_done"),
            "totalMs": total_ms,
        }
