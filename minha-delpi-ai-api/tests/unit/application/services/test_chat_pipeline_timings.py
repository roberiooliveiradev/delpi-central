from app.application.services.chat_pipeline_timings import ChatPipelineTimings


def test_pipeline_timings_tracks_spans():
    timings = ChatPipelineTimings()
    timings.mark("rag_done")
    timings.mark("tools_done")
    timings.mark("llm_done")

    payload = timings.to_dict()

    assert payload["ragMs"] is not None
    assert payload["toolsMs"] is not None
    assert payload["llmMs"] is not None
    assert payload["totalMs"] >= 0
