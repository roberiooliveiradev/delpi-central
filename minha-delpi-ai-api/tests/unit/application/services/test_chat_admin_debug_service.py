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


def test_build_includes_degraded_stages_from_tool_context():
    payload = ChatAdminDebugService.build(
        workspace_context={"agentId": None, "skills": {}},
        tool_context={
            "context": "",
            "toolCalls": [],
            "degradedStages": ["rag", "message_search"],
        },
        rag={"context": "", "sources": []},
        llm_messages=[],
        history_summary="",
        operational_optimize=False,
        analysis_mode=False,
        fast_path=False,
        skip_rag=True,
    )

    assert payload["pipeline"]["degradedStages"] == ["rag", "message_search"]


def test_build_includes_enrichment_plan_sufficiency_and_evidence_refs():
    payload = ChatAdminDebugService.build(
        workspace_context={"agentId": None, "skills": {}},
        tool_context={
            "context": "",
            "toolCalls": [],
            "enrichmentPlan": {
                "kind": "product_enrichment_composition",
                "sufficiency": {
                    "verdict": "execute",
                    "planId": "stock_low_needs_sales",
                    "reasonKey": "stockLowNeedsSales",
                },
            },
            "evidenceRefs": [
                {"path": "/products/x/stock", "operationId": "get_product_stock", "ok": True},
                {"path": "/products/x/sales", "operationId": "get_product_sales", "ok": True},
            ],
        },
        rag={"context": "", "sources": []},
        llm_messages=[],
        history_summary="",
        operational_optimize=False,
        analysis_mode=False,
        fast_path=False,
        skip_rag=True,
    )

    assert payload["tooling"]["enrichmentPlan"]["sufficiency"]["planId"] == (
        "stock_low_needs_sales"
    )
    assert payload["intelligence"]["enrichmentPlan"]["sufficiency"]["verdict"] == "execute"
    assert len(payload["tooling"]["evidenceRefs"]) == 2


def test_attach_includes_intelligence_timings():
    admin_debug = {"pipeline": {"skipRag": True}}
    intelligence = {
        "timings": {"rag_done_ms": 12, "tools_done_ms": 34, "llm_done_ms": 890},
        "pipeline": {"stages": ["utility_direct"], "skipRag": True},
        "nativeToolCalling": {"used": False},
    }
    metadata: dict = {
        "provider": "openai_compatible",
        "model": "moonshotai/kimi-k3",
        "responseMode": "normal",
        "llm": {
            "provider": "openai_compatible",
            "model": "moonshotai/kimi-k3",
            "baseUrl": "https://openrouter.ai/api/v1",
            "maxTokens": 256,
            "numCtx": 1536,
            "temperature": 0.1,
        },
        "metrics": {
            "latencyMs": 18218,
            "promptTokensEstimated": 4200,
            "completionTokensEstimated": 380,
            "totalTokensEstimated": 4580,
            "estimatedCost": 0.012345,
        },
        "responseQuality": {"llmSkipped": False},
    }

    ChatAdminDebugService.attach_to_assistant_metadata(
        metadata,
        admin_debug,
        intelligence_metadata=intelligence,
    )

    assert metadata["adminDebug"]["intelligence"]["timings"]["llm_done_ms"] == 890
    assert metadata["adminDebug"]["intelligence"]["pipeline"]["stages"] == ["utility_direct"]
    assert metadata["adminDebug"]["llm"]["provider"] == "openai_compatible"
    assert metadata["adminDebug"]["llm"]["model"] == "moonshotai/kimi-k3"
    assert metadata["adminDebug"]["llm"]["baseUrl"] == "https://openrouter.ai/api/v1"
    assert metadata["adminDebug"]["llm"]["skipped"] is False
    assert metadata["adminDebug"]["llm"]["usage"]["promptTokensEstimated"] == 4200
    assert metadata["adminDebug"]["llm"]["usage"]["completionTokensEstimated"] == 380
    assert metadata["adminDebug"]["llm"]["usage"]["totalTokensEstimated"] == 4580
    assert metadata["adminDebug"]["llm"]["usage"]["estimatedCost"] == 0.012345
    assert metadata["adminDebug"]["llm"]["usage"]["latencyMs"] == 18218
    assert metadata["adminDebug"]["metrics"]["totalTokensEstimated"] == 4580
    assert metadata["adminDebug"]["llm"]["maxTokens"] == 256
    assert metadata["adminDebug"]["llm"]["temperature"] == 0.1


def test_build_includes_llm_runtime_fields(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai_compatible")
    monkeypatch.setenv("KIMI_BASE_URL", "https://openrouter.ai/api/v1")
    monkeypatch.setenv("KIMI_MODEL", "moonshotai/kimi-k3")
    monkeypatch.setenv("KIMI_API_KEY", "sk-or-test")
    monkeypatch.delenv("LLM_TEXT_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_TEXT_MODEL", raising=False)
    monkeypatch.delenv("LLM_TEXT_API_KEY", raising=False)

    payload = ChatAdminDebugService.build(
        workspace_context={"agentId": None, "skills": {}},
        tool_context={"context": "", "toolCalls": []},
        rag={"context": "", "sources": []},
        llm_messages=[{"role": "user", "content": "oi"}],
        history_summary="",
        operational_optimize=False,
        analysis_mode=False,
        fast_path=False,
        skip_rag=True,
    )

    assert payload["llm"]["provider"] == "openai_compatible"
    assert payload["llm"]["model"]
    assert payload["llm"]["baseUrl"] == "https://openrouter.ai/api/v1"
    assert payload["llm"]["messages"][0]["role"] == "user"

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
