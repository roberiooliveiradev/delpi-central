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
