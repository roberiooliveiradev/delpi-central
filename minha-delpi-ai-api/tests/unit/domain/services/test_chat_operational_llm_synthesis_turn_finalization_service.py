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


def test_finalize_persisted_answer_falls_back_when_instruction_leaks():
    llm_answer = (
        "O produto **10080045** está cadastrado. "
        "Não transcreva listas: o painel exibe os dados."
    )

    result = ChatOperationalLlmSynthesisTurnFinalizationService.finalize_persisted_answer(
        llm_answer,
        _overview_tool_calls(),
        message="me fale do produto 10080045",
        response_mode="normal",
        response_mode_effect="llm_synthesis",
    )

    assert "10080045" in result
    assert "não transcreva listas" not in result.lower()
    assert "o painel exibe" not in result.lower()

def test_finalize_persisted_answer_falls_back_when_access_directive_leaks():
    llm_answer = (
        "O produto **10080045** está cadastrado. "
        "Responda com o que já veio — não peça acesso à rota."
    )

    result = ChatOperationalLlmSynthesisTurnFinalizationService.finalize_persisted_answer(
        llm_answer,
        _overview_tool_calls(),
        message="me fale do produto 10080045",
        response_mode="normal",
        response_mode_effect="llm_synthesis",
    )

    assert "10080045" in result
    assert "não peça acesso" not in result.lower()


def _structure_tool_calls() -> list[dict]:
    return [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "llmProseDecoupled": True,
                "path": "/products/90260149/structure",
                "dataCommentary": {
                    "profileKey": "structure",
                    "highlights": [
                        "Produto **90260149** — CHICOTE DE LIGACAO.",
                        "A composição tem **2** componente(s) de nível 1.",
                        "Na árvore: **2** intermediário(s) (PI) e **1** matéria(s)-prima(s) distinta(s).",
                    ],
                    "summaryLines": [
                        "Produto **90260149** — CHICOTE DE LIGACAO.",
                    ],
                    "visualHints": ["tree"],
                },
            },
        }
    ]


def test_finalize_persisted_answer_structure_uses_commentary_not_reformule():
    safe = (
        "Não consegui formular a resposta de forma clara. "
        "Pode reformular a pergunta em uma frase?"
    )

    result = ChatOperationalLlmSynthesisTurnFinalizationService.finalize_persisted_answer(
        safe,
        _structure_tool_calls(),
        message="estrutura do produto 90260149",
        response_mode="normal",
        response_mode_effect="llm_synthesis",
    )

    assert "reformular" not in result.lower()
    assert "90260149" in result
    assert "composição" in result.lower() or "PI" in result


def test_finalize_persisted_answer_structure_replaces_english_cot_with_commentary():
    llm_answer = (
        "The user is asking about the BOM structure of product 90260149. "
        "The structure has 2 items in the first level with MPs underneath."
    )

    result = ChatOperationalLlmSynthesisTurnFinalizationService.finalize_persisted_answer(
        llm_answer,
        _structure_tool_calls(),
        message="estrutura do produto 90260149",
        response_mode="thinker",
        response_mode_effect="llm_synthesis",
    )

    assert "the user is asking" not in result.lower()
    assert "reformular" not in result.lower()
    assert "90260149" in result
    assert "PI" in result or "composição" in result.lower()

