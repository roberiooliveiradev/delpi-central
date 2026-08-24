import time

from app.application.services.chat_pipeline_timings import ChatPipelineTimings


def test_pipeline_timings_tracks_spans_in_prep_order():
    timings = ChatPipelineTimings()
    time.sleep(0.001)
    timings.mark("pre_tool_done")
    time.sleep(0.001)
    timings.mark("tools_done")
    time.sleep(0.001)
    timings.mark("post_tool_done")
    time.sleep(0.001)
    timings.mark("rag_done")
    time.sleep(0.001)
    timings.mark("llm_done")

    payload = timings.to_dict()

    assert payload["preToolMs"] is not None and payload["preToolMs"] >= 0
    assert payload["toolsMs"] is not None and payload["toolsMs"] >= 0
    assert payload["postToolMs"] is not None and payload["postToolMs"] >= 0
    assert payload["ragMs"] is not None and payload["ragMs"] >= 0
    assert payload["llmMs"] is not None and payload["llmMs"] >= 0
    assert payload["totalMs"] >= 0
    assert payload["totalMs"] >= (
        (payload["preToolMs"] or 0)
        + (payload["toolsMs"] or 0)
        + (payload["postToolMs"] or 0)
        + (payload["ragMs"] or 0)
        + (payload["llmMs"] or 0)
    )


def test_pipeline_timings_legacy_order_no_longer_zeros_tools():
    """tools before rag must yield non-null toolsMs (regression vs old to_dict)."""
    timings = ChatPipelineTimings()
    timings.mark("pre_tool_done")
    timings.mark("tools_done")
    timings.mark("post_tool_done")
    timings.mark("rag_done")
    timings.mark("llm_done")

    payload = timings.to_dict()
    assert payload["toolsMs"] is not None
    assert payload["ragMs"] is not None
    assert payload["llmMs"] is not None


def test_pipeline_timings_tools_breakdown_order_and_extras():
    timings = ChatPipelineTimings()
    timings.mark("pre_tool_done")
    time.sleep(0.001)
    timings.mark("tools_selection_done")
    time.sleep(0.001)
    timings.mark("tools_wave1_done")
    time.sleep(0.001)
    timings.mark("tools_critic_done")
    time.sleep(0.001)
    timings.mark("tools_wave2_done")
    time.sleep(0.001)
    timings.mark("tools_assemble_done")
    time.sleep(0.001)
    timings.mark("tools_agentic_done")
    time.sleep(0.001)
    timings.mark("tools_done")
    timings.add_extra_ms("wave1HttpMs", 12)
    timings.add_extra_ms("wave1PresentationMs", 34)
    timings.add_extra_ms("wave2HttpMs", 5)
    timings.add_extra_ms("wave2PresentationMs", 8)

    payload = timings.to_dict()
    breakdown = payload["toolsBreakdown"]

    assert breakdown["selectionMs"] is not None and breakdown["selectionMs"] >= 0
    assert breakdown["wave1Ms"] is not None and breakdown["wave1Ms"] >= 0
    assert breakdown["criticMs"] is not None and breakdown["criticMs"] >= 0
    assert breakdown["wave2Ms"] is not None and breakdown["wave2Ms"] >= 0
    assert breakdown["assembleMs"] is not None and breakdown["assembleMs"] >= 0
    assert breakdown["agenticExtendMs"] is not None and breakdown["agenticExtendMs"] >= 0
    assert (
        breakdown["finalizeAfterToolsMs"] is not None
        and breakdown["finalizeAfterToolsMs"] >= 0
    )
    assert breakdown["wave1HttpMs"] == 12
    assert breakdown["wave1PresentationMs"] == 34
    assert breakdown["wave2HttpMs"] == 5
    assert breakdown["wave2PresentationMs"] == 8

    tools_ms = payload["toolsMs"] or 0
    sum_spans = sum(
        breakdown[key] or 0
        for key in (
            "selectionMs",
            "wave1Ms",
            "criticMs",
            "wave2Ms",
            "assembleMs",
            "agenticExtendMs",
            "finalizeAfterToolsMs",
        )
    )
    assert abs(tools_ms - sum_spans) <= 1


def test_pipeline_timings_bind_and_wave_records_extras():
    timings = ChatPipelineTimings()

    with ChatPipelineTimings.bind(timings):
        with ChatPipelineTimings.tools_wave("wave1"):
            ChatPipelineTimings.record_wave_http_ms(40)
            ChatPipelineTimings.record_wave_presentation_ms(100)
        with ChatPipelineTimings.tools_wave("wave2"):
            ChatPipelineTimings.record_wave_http_ms(7)
            ChatPipelineTimings.record_wave_presentation_ms(9)
        ChatPipelineTimings.mark_current("tools_selection_done")

    breakdown = timings.tools_breakdown()
    assert breakdown["wave1HttpMs"] == 40
    assert breakdown["wave1PresentationMs"] == 100
    assert breakdown["wave2HttpMs"] == 7
    assert breakdown["wave2PresentationMs"] == 9
    assert timings.span_ms("start", "tools_selection_done") is not None
