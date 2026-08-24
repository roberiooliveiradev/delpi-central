import time
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator


_current_timings: ContextVar["ChatPipelineTimings | None"] = ContextVar(
    "chat_pipeline_timings",
    default=None,
)
_current_tools_wave: ContextVar[str | None] = ContextVar(
    "chat_pipeline_tools_wave",
    default=None,
)


class ChatPipelineTimings:
    """Pipeline wall spans in real prep order: preTool → tools → postTool → rag → llm."""

    _TOOLS_BREAKDOWN_SPANS: tuple[tuple[str, str, str], ...] = (
        ("selectionMs", "pre_tool_done", "tools_selection_done"),
        ("wave1Ms", "tools_selection_done", "tools_wave1_done"),
        ("criticMs", "tools_wave1_done", "tools_critic_done"),
        ("wave2Ms", "tools_critic_done", "tools_wave2_done"),
        ("assembleMs", "tools_wave2_done", "tools_assemble_done"),
        ("agenticExtendMs", "tools_assemble_done", "tools_agentic_done"),
        ("finalizeAfterToolsMs", "tools_agentic_done", "tools_done"),
    )

    def __init__(self):
        self._started_at = time.perf_counter()
        self._marks: dict[str, float] = {"start": self._started_at}
        self._extras_ms: dict[str, int] = {}

    def mark(self, key: str) -> None:
        self._marks[key] = time.perf_counter()

    def span_ms(self, start_key: str, end_key: str) -> int | None:
        start = self._marks.get(start_key)
        end = self._marks.get(end_key)

        if start is None or end is None:
            return None

        return max(0, int((end - start) * 1000))

    def add_extra_ms(self, key: str, ms: int) -> None:
        if ms < 0:
            return

        self._extras_ms[key] = self._extras_ms.get(key, 0) + int(ms)

    def elapsed_sec(self) -> float:
        return max(0.0, time.perf_counter() - self._started_at)

    def tools_breakdown(self) -> dict[str, int | None]:
        breakdown: dict[str, int | None] = {}

        for key, start_key, end_key in self._TOOLS_BREAKDOWN_SPANS:
            breakdown[key] = self.span_ms(start_key, end_key)

        for extra_key, value in self._extras_ms.items():
            breakdown[extra_key] = value

        return breakdown

    def to_dict(self) -> dict:
        total_ms = max(0, int((time.perf_counter() - self._started_at) * 1000))
        payload: dict = {
            "preToolMs": self.span_ms("start", "pre_tool_done"),
            "toolsMs": self.span_ms("pre_tool_done", "tools_done"),
            "postToolMs": self.span_ms("tools_done", "post_tool_done"),
            "ragMs": self.span_ms("post_tool_done", "rag_done"),
            "llmMs": self.span_ms("rag_done", "llm_done"),
            "totalMs": total_ms,
        }
        breakdown = self.tools_breakdown()

        if any(value is not None for value in breakdown.values()):
            payload["toolsBreakdown"] = breakdown

        return payload

    @classmethod
    def current(cls) -> "ChatPipelineTimings | None":
        return _current_timings.get()

    @classmethod
    def mark_current(cls, key: str) -> None:
        timings = cls.current()

        if timings is not None:
            timings.mark(key)

    @classmethod
    def add_current_extra_ms(cls, key: str, ms: int) -> None:
        timings = cls.current()

        if timings is not None:
            timings.add_extra_ms(key, ms)

    @classmethod
    def record_wave_http_ms(cls, ms: int) -> None:
        wave = _current_tools_wave.get()

        if wave == "wave1":
            cls.add_current_extra_ms("wave1HttpMs", ms)
        elif wave == "wave2":
            cls.add_current_extra_ms("wave2HttpMs", ms)

    @classmethod
    def record_wave_presentation_ms(cls, ms: int) -> None:
        wave = _current_tools_wave.get()

        if wave == "wave1":
            cls.add_current_extra_ms("wave1PresentationMs", ms)
        elif wave == "wave2":
            cls.add_current_extra_ms("wave2PresentationMs", ms)

    @classmethod
    @contextmanager
    def bind(cls, timings: "ChatPipelineTimings") -> Iterator["ChatPipelineTimings"]:
        token = _current_timings.set(timings)

        try:
            yield timings
        finally:
            _current_timings.reset(token)

    @classmethod
    @contextmanager
    def tools_wave(cls, wave: str) -> Iterator[None]:
        token = _current_tools_wave.set(wave)

        try:
            yield
        finally:
            _current_tools_wave.reset(token)
