import time


class ChatPipelineTimings:
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

    def to_dict(self) -> dict:
        total_ms = max(0, int((time.perf_counter() - self._started_at) * 1000))

        return {
            "ragMs": self.span_ms("start", "rag_done"),
            "toolsMs": self.span_ms("rag_done", "tools_done"),
            "llmMs": self.span_ms("tools_done", "llm_done"),
            "totalMs": total_ms,
        }
