"""Montagem do payload adminDebug."""

from app.application.services.chat_admin_debug_service import ChatAdminDebugService


def _minimal_build(*, rag: dict) -> dict:
    return ChatAdminDebugService.build(
        workspace_context={"agentKey": None, "skills": {}},
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
        }
    )

    assert payload["rag"]["ragContextText"]
    assert payload["rag"]["sources"] == []
    assert "sourcesNote" in payload["rag"]
    assert "globais" in payload["rag"]["sourcesNote"].lower()


def test_no_sources_note_when_rag_empty():
    payload = _minimal_build(rag={"context": "", "sources": []})

    assert "sourcesNote" not in payload["rag"]
