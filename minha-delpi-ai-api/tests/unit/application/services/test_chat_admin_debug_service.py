"""Montagem do payload adminDebug."""

from app.application.services.chat_admin_debug_service import ChatAdminDebugService


def _minimal_build(*, rag: dict) -> dict:
    return ChatAdminDebugService.build(
        workspace_context={"agentId": None, "skills": {}},
        tool_context={"context": "", "toolCalls": []},
        rag=rag,
        llm_messages=[{"role": "system", "content": "x"}],
        history_summary="",
        operational_optimize=False,
        analysis_mode=False,
        fast_path=False,
        skip_rag=False,
    )


def test_sources_note_when_rag_text_without_client_visible_sources():
    payload = _minimal_build(
        rag={
            "context": "[Fonte 1]\nTítulo: Normas\nTrecho: texto",
            "sources": [],
            "retrievedSourceCount": 3,
            "visibleSourceCount": 0,
            "retrievedChunkCount": 3,
        }
    )

    assert payload["rag"]["ragContextText"]
    assert payload["rag"]["sources"] == []
    assert payload["rag"]["retrievedSourceCount"] == 3
    assert payload["rag"]["visibleSourceCount"] == 0
    assert "sourcesNote" in payload["rag"]
    assert "Recuperadas 3 fonte(s)" in payload["rag"]["sourcesNote"]


def test_no_sources_note_when_rag_empty():
    payload = _minimal_build(rag={"context": "", "sources": []})

    assert "sourcesNote" not in payload["rag"]


def test_build_includes_intent_route_when_provided():
    payload = ChatAdminDebugService.build(
        workspace_context={"agentId": None, "skills": {}},
        tool_context={"context": "", "toolCalls": []},
        rag={"context": "", "sources": []},
        llm_messages=[],
        history_summary="",
        operational_optimize=True,
        analysis_mode=False,
        fast_path=False,
        skip_rag=True,
        intent_route={"intent": "operational_query", "subIntent": "stock_lookup"},
    )

    assert payload["intentRoute"]["intent"] == "operational_query"


def test_attach_includes_intelligence_timings():
    admin_debug = {"pipeline": {"skipRag": True}}
    intelligence = {
        "timings": {"rag_done_ms": 12, "tools_done_ms": 34, "llm_done_ms": 890},
        "pipeline": {"stages": ["utility_direct"], "skipRag": True},
        "nativeToolCalling": {"used": False},
    }
    metadata: dict = {}

    ChatAdminDebugService.attach_to_assistant_metadata(
        metadata,
        admin_debug,
        intelligence_metadata=intelligence,
    )

    assert metadata["adminDebug"]["intelligence"]["timings"]["llm_done_ms"] == 890
    assert metadata["adminDebug"]["intelligence"]["pipeline"]["stages"] == ["utility_direct"]


def test_resolve_client_admin_debug_merges_assertiveness_from_metadata():
    build_payload = {"pipeline": {"skipRag": True}}
    assistant_metadata = {
        "adminDebug": {
            "memory": {"operationalFocus": {"productCode": "10080001"}},
            "contextAssertiveness": {"score": 92.0, "flags": ["follow_up_entity_reused"]},
        }
    }

    class _Req:
        admin_debug = True

    merged = ChatAdminDebugService.resolve_client_admin_debug(
        _Req(),
        build_payload=build_payload,
        assistant_metadata=assistant_metadata,
    )

    assert merged is not None
    assert merged["contextAssertiveness"]["score"] == 92.0
    assert merged["memory"]["operationalFocus"]["productCode"] == "10080001"
    assert merged["pipeline"]["skipRag"] is True


def test_sync_text_correction_trace_copies_metrics_into_admin_debug():
    metadata = {
        "adminDebug": {"pipeline": {"skipRag": True}},
        "textCorrectionMetrics": {"subtype": "text_correct_basic", "source": "user_message"},
        "textTask": {"type": "correction", "subtype": "text_correct_basic", "source": "user_message"},
        "textCorrectionQuality": {"passed": True, "checks": []},
        "textCorrectionPreferences": {"labels": ["Só versão final"]},
    }

    ChatAdminDebugService.sync_text_correction_trace(metadata)

    admin = metadata["adminDebug"]
    assert admin["textCorrectionMetrics"]["subtype"] == "text_correct_basic"
    assert admin["textCorrectionTask"]["subtype"] == "text_correct_basic"
    assert admin["textCorrectionQuality"]["passed"] is True
    assert admin["textCorrectionPreferences"]["labels"] == ["Só versão final"]


def test_resolve_client_admin_debug_includes_text_correction_trace():
    build_payload = {"pipeline": {"skipRag": True}}
    assistant_metadata = {
        "adminDebug": {
            "textCorrectionMetrics": {"subtype": "text_formal"},
            "textCorrectionTask": {"subtype": "text_formal", "source": "user_message"},
            "pipeline": {"textCorrectionMode": True},
        }
    }

    class _Req:
        admin_debug = True

    merged = ChatAdminDebugService.resolve_client_admin_debug(
        _Req(),
        build_payload=build_payload,
        assistant_metadata=assistant_metadata,
    )

    assert merged is not None
    assert merged["textCorrectionMetrics"]["subtype"] == "text_formal"
    assert merged["pipeline"]["textCorrectionMode"] is True


def test_build_pipeline_flags_text_correction_mode():
    payload = ChatAdminDebugService.build(
        workspace_context={"agentId": None, "textCorrectionMode": True},
        tool_context={"context": "", "toolCalls": []},
        rag={"context": "", "sources": []},
        llm_messages=[],
        history_summary="",
        operational_optimize=False,
        analysis_mode=False,
        fast_path=False,
        skip_rag=True,
    )

    assert payload["pipeline"]["textCorrectionMode"] is True
