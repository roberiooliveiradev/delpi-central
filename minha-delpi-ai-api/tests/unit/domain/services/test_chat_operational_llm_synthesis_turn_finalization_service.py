from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_operational_llm_synthesis_turn_finalization_service import (
    ChatOperationalLlmSynthesisTurnFinalizationService,
)
from app.domain.services.chat_tool_context_presentation_service import (
    ChatToolContextPresentationService,
)

configure_domain_infrastructure_ports()


def _overview_tool_calls() -> list[dict]:
    return [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "llmProseDecoupled": True,
                "path": "/products/10080045/analyser",
                "dataCommentary": {
                    "highlights": [
                        {
                            "text": (
                                "O produto **10080045** — TERM. OLHAL M6 "
                                "(tipo **MP**, grupo **1008**)."
                            ),
                        },
                    ],
                    "attention": ["Roteiro sem operações registradas."],
                },
            },
        }
    ]


def test_finalize_persisted_answer_prepends_product_code_for_llm_answer():
    llm_answer = (
        "O roteiro analisado não contém registros para este produto específico."
    )

    result = ChatOperationalLlmSynthesisTurnFinalizationService.finalize_persisted_answer(
        llm_answer,
        _overview_tool_calls(),
        message="me fale do produto 10080045",
        response_mode="normal",
        response_mode_effect="llm_synthesis",
    )

    assert "10080045" in result
    assert result.index("10080045") < 80


def test_finalize_persisted_answer_falls_back_to_commentary_on_deflection():
    llm_answer = (
        "Para obter mais detalhes, seria necessário acessar a rota "
        "/products/10080045/analyser."
    )

    result = ChatOperationalLlmSynthesisTurnFinalizationService.finalize_persisted_answer(
        llm_answer,
        _overview_tool_calls(),
        message="me fale do produto 10080045",
        response_mode="normal",
        response_mode_effect="llm_synthesis",
    )

    assert "10080045" in result
    assert "seria necessário acessar" not in result.lower()
    assert "MP" in result or "roteiro" in result.lower()


def test_resolve_authorized_persisted_answer_uses_turn_finalization():
    persisted = ChatToolContextPresentationService.resolve_authorized_persisted_answer(
        "Preciso consultar os registros do produto.",
        _overview_tool_calls(),
        message="me fale do produto 10080045",
        skip_replacement=True,
        response_mode="thinker",
        response_mode_effect="llm_synthesis",
    )

    assert "10080045" in persisted
    assert "preciso consultar" not in persisted.lower()


def test_finalize_persisted_answer_strips_sparse_numbered_lists():
    llm_answer = (
        "O produto **10080045** está cadastrado como MP.\n\n"
        "**Destaques:**\n"
        "1. Não há registros no roteiro.\n"
        "2.\n"
        "3.\n"
        "4. O plano de inspeção está vazio.\n"
    )

    result = ChatOperationalLlmSynthesisTurnFinalizationService.finalize_persisted_answer(
        llm_answer,
        _overview_tool_calls(),
        message="me fale do produto 10080045",
        response_mode="thinker",
        response_mode_effect="llm_synthesis",
    )

    assert "10080045" in result
    assert "\n2.\n" not in result
    assert "\n3.\n" not in result


def test_finalize_persisted_answer_thinker_falls_back_on_fabricated_group():
    llm_answer = (
        "O código do produto é **10080045**, que pertence ao grupo de "
        "**Componentes Elétricos**. **Destaques:**\n1. 2. 3. 4. 5."
    )

    result = ChatOperationalLlmSynthesisTurnFinalizationService.finalize_persisted_answer(
        llm_answer,
        _overview_tool_calls(),
        message="me fale do produto 10080045",
        response_mode="thinker",
        response_mode_effect="llm_synthesis",
    )

    assert "10080045" in result
    assert "componentes eletricos" not in result.lower()
    assert "componentes elétricos" not in result.lower()
    assert "MP" in result or "1008" in result


def test_finalize_persisted_answer_normal_falls_back_when_llm_too_short():
    llm_answer = "O código do produto é 10080045."

    result = ChatOperationalLlmSynthesisTurnFinalizationService.finalize_persisted_answer(
        llm_answer,
        _overview_tool_calls(),
        message="me fale do produto 10080045",
        response_mode="normal",
        response_mode_effect="llm_synthesis",
    )

    assert len(result) >= 72
    assert "10080045" in result
    assert "MP" in result or "roteiro" in result.lower()
