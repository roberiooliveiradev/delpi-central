from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

from app.application.services.chat_turn.chat_turn_llm_assembly_service import (
    ChatTurnLlmAssemblyService,
)


def _prepared(**overrides):
    base = {
        "direct_answer": None,
        "pipeline_stages": ["prepare"],
        "tool_context": {"context": "", "toolCalls": []},
        "tool_calls": [],
        "sources": [],
        "pipeline_timings": SimpleNamespace(to_dict=lambda: {}),
        "operational_optimize": False,
        "analysis_mode": False,
        "fast_path": False,
        "skip_rag": False,
        "history": [],
        "history_summary": "",
        "rag": {"context": ""},
        "email_writing_mode": False,
        "email_subtype": None,
        "text_correction_mode": False,
        "text_correction_subtype": None,
        "text_task_mode": False,
        "intent_route": None,
        "canvas_open_payload": None,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_assemble_send_skips_admin_guidelines_on_fast_path():
    prepared = _prepared(fast_path=True)
    web_search = MagicMock()
    web_search.enhance_prepared_turn.side_effect = lambda **kwargs: (
        kwargs["direct_answer"],
        kwargs["pipeline_stages"],
    )

    result = ChatTurnLlmAssemblyService.assemble(
        request=SimpleNamespace(
            access_token=None,
            session_id=str(uuid4()),
            attachment_ids=None,
        ),
        message="oi",
        user_id=uuid4(),
        workspace_context={"skills": {}},
        attachments=[],
        previous_messages=[],
        prepared=prepared,
        user_message=SimpleNamespace(id=uuid4()),
        chat_repository=MagicMock(),
        prompt_builder_service=MagicMock(),
        web_search_synthesis_service=web_search,
        build_attachment_context=lambda **kwargs: "",
        resolve_llm_user_context=lambda *args, **kwargs: None,
        build_admin_guidelines_prompt=lambda ctx: ("guideline", [{"id": "g1"}]),
        embedding_cache_stats=lambda: None,
        channel="send",
    )

    assert result.active_guidelines == []
    assert result.direct_answer is None


def test_assemble_stream_keeps_admin_guidelines_on_fast_path():
    prepared = _prepared(fast_path=True)
    web_search = MagicMock()
    web_search.enhance_prepared_turn.side_effect = lambda **kwargs: (
        kwargs["direct_answer"],
        kwargs["pipeline_stages"],
    )
    prompt_builder = MagicMock()
    prompt_builder.build_messages.return_value = [{"role": "user", "content": "x"}]

    result = ChatTurnLlmAssemblyService.assemble(
        request=SimpleNamespace(
            access_token=None,
            session_id=str(uuid4()),
            attachment_ids=None,
        ),
        message="oi",
        user_id=uuid4(),
        workspace_context={"skills": {}},
        attachments=[],
        previous_messages=[],
        prepared=prepared,
        user_message=SimpleNamespace(id=uuid4()),
        chat_repository=MagicMock(),
        prompt_builder_service=prompt_builder,
        web_search_synthesis_service=web_search,
        build_attachment_context=lambda **kwargs: "",
        resolve_llm_user_context=lambda *args, **kwargs: None,
        build_admin_guidelines_prompt=lambda ctx: ("guideline", [{"id": "g1"}]),
        embedding_cache_stats=lambda: None,
        channel="stream",
    )

    assert result.active_guidelines == [{"id": "g1"}]
    prompt_builder.build_messages.assert_called_once()


def test_assemble_prefers_drawing_report_over_existing_direct_answer():
    report = "# Relatório de Análise de Desenho DELPI\n\nAprovado"
    prepared = _prepared(
        direct_answer="### Informações completas do produto 90260140",
        tool_context={
            "context": "",
            "toolCalls": [
                {
                    "name": "execute_external_action",
                    "metadata": {
                        "ok": True,
                        "statusCode": 200,
                        "path": "/products/90260140/analyser",
                    },
                }
            ],
            "drawingAnalysisMode": True,
            "drawingAnalysis": {"productCode": "90260140"},
            "drawingAnalysisExport": {"markdown": report},
        },
    )
    web_search = MagicMock()
    web_search.enhance_prepared_turn.side_effect = lambda **kwargs: (
        kwargs["direct_answer"],
        kwargs["pipeline_stages"],
    )

    result = ChatTurnLlmAssemblyService.assemble(
        request=SimpleNamespace(
            access_token=None,
            session_id=str(uuid4()),
            attachment_ids=["att-1"],
        ),
        message="Analise o desenho 90260140 e gere o relatório de conformidade DELPI",
        user_id=uuid4(),
        workspace_context={"skills": {"drawingAnalysis": True}},
        attachments=[],
        previous_messages=[],
        prepared=prepared,
        user_message=SimpleNamespace(id=uuid4()),
        chat_repository=MagicMock(),
        prompt_builder_service=MagicMock(),
        web_search_synthesis_service=web_search,
        build_attachment_context=lambda **kwargs: "",
        resolve_llm_user_context=lambda *args, **kwargs: None,
        build_admin_guidelines_prompt=lambda ctx: ("", []),
        embedding_cache_stats=lambda: None,
        channel="stream",
    )

    assert result.direct_answer == report
    assert result.llm_messages == []
