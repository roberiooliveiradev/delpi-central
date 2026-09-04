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


def test_finalize_guards_english_cot_on_free_path_llm_synthesis():
    leaked = (
        "According to my instructions, the user's message is vague. "
        "I should ask for clarification."
    )
    result = ChatTurnCompletionFinalizeService.finalize(
        _turn(
            answer=leaked,
            tool_context={"responseModeEffect": "llm_synthesis", "toolCalls": []},
        )
    )

    assert result.answer != leaked
    assert "according to my instructions" not in result.answer.lower()
    assert result.answer.strip()


def test_finalize_keeps_clean_free_path_answer():
    clean = "Posso ajudar com consultas de estoque, estrutura e documentação."
    result = ChatTurnCompletionFinalizeService.finalize(
        _turn(
            answer=clean,
            tool_context={"responseModeEffect": "llm_synthesis", "toolCalls": []},
        )
    )

    assert result.answer == clean


def test_finalize_guards_english_cot_even_with_rag_tools():
    """Regressão: CoT EN com retrieve/RAG não pode bypassar a guarda free-path."""
    leaked = (
        "The user is asking how to describe a terminal. I have retrieved context "
        "from Normas_Tecnicas_DELPI.md. Use Portuguese. Let me structure:"
    )
    turn = _turn(
        answer=leaked,
        tool_context={"responseModeEffect": "direct", "toolCalls": [{"name": "retrieve"}]},
    )
    object.__setattr__(
        turn,
        "tool_calls",
        [
            {
                "name": "retrieve",
                "metadata": {"ok": True, "path": "/rag"},
            }
        ],
    )
    result = ChatTurnCompletionFinalizeService.finalize(turn)

    assert result.answer != leaked
    assert "let me structure" not in result.answer.lower()
    assert "the user is asking" not in result.answer.lower()
    assert result.answer.strip()


def test_finalize_guards_portuguese_meta_planning_on_fast_synthesis():
    """Regressão: Rápida + llm_synthesis_brief não pode entregar planejamento PT."""
    leaked = (
        "A pergunta é normativa sobre padrões de descrição técnica.\n\n"
        "Skill ativa: technical-description-delpi\n\n"
        "Contexto RAG: Normas_Tecnicas_DELPI.md (grupo 1008).\n\n"
        "Instruções que estou seguindo:\n"
        "- Não chamar API de produto, SQL ou catálogo neste modo\n\n"
        "Terminais PINO\n"
        "[ITEM] [TIPO DE TERMINAL] [BITOLA DO CABO]\n"
        "Exemplo: TERM. PINO RETO 2,00MM2 COMP 10,00MM ESTANHADO C/ISOLACAO GRANEL REFORÇADO ROHS"
    )
    result = ChatTurnCompletionFinalizeService.finalize(
        _turn(
            answer=leaked,
            tool_context={
                "responseModeEffect": "llm_synthesis_brief",
                "toolCalls": [],
            },
        )
    )

    assert result.answer != leaked
    assert "skill ativa" not in result.answer.lower()
    assert "contexto rag" not in result.answer.lower()
    assert "Terminais PINO" in result.answer
    assert "TERM. PINO" in result.answer
