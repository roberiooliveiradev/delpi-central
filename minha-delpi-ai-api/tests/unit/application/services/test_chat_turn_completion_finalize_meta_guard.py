from unittest.mock import MagicMock
from uuid import uuid4

from app.application.services.chat_pipeline_timings import ChatPipelineTimings
from app.application.services.chat_turn.chat_turn_completion_finalize_service import (
    ChatTurnCompletionFinalizeService,
)
from app.application.services.chat_turn.chat_turn_completion_models import (
    ChatTurnCompletionInput,
)
from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_meta_llm_synthesis_service import (
    ChatMetaLlmSynthesisService,
    MetaLlmSynthesisSection,
    SECTION_CAPABILITIES,
)
from types import SimpleNamespace

configure_domain_infrastructure_ports()


def _turn(*, answer: str, tool_context: dict) -> ChatTurnCompletionInput:
    prepared = SimpleNamespace(
        email_writing_mode=False,
        text_correction_mode=False,
        text_task_mode=False,
    )
    request = MagicMock()
    request.response_mode = None
    return ChatTurnCompletionInput(
        request=request,
        message="o que você pode fazer?",
        user_id=uuid4(),
        session_id=uuid4(),
        workspace_context={},
        attachments=[],
        previous_messages=[],
        history_source=[],
        prepared=prepared,
        answer=answer,
        sources=[],
        tool_context=tool_context,
        tool_calls=[],
        direct_answer=None,
        pipeline_timings=ChatPipelineTimings(),
        pipeline_stages=[],
        fast_path=False,
        operational_optimize=False,
        skip_rag=True,
        analysis_mode=False,
        llm_messages=[],
        admin_debug_payload=None,
        active_guidelines=[],
        started_at=0.0,
        user_message=MagicMock(),
        canvas_open_payload=None,
    )


def test_finalize_guards_capabilities_meta_synthesis_without_profile_flag():
    catalog = "Posso ajudar você nestes formatos:\n\n- RAG autorizado"
    tool_context = ChatMetaLlmSynthesisService.enrich_tool_context(
        {"context": "", "toolCalls": []},
        sections=[
            MetaLlmSynthesisSection(
                section_id=SECTION_CAPABILITIES,
                title="Capacidades desta sessão",
                facts=catalog,
            )
        ],
    )

    assert not tool_context.get("userProfileLlmSynthesis")

    leaked = "Resposta com vazamento: não invente rotas. Liste o catálogo."
    result = ChatTurnCompletionFinalizeService.finalize(
        _turn(answer=leaked, tool_context=tool_context)
    )

    assert result.answer == catalog
    assert "não invente rotas" not in result.answer.lower()
