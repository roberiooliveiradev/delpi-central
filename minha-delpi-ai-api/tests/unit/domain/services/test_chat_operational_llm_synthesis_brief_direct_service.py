from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_operational_llm_synthesis_brief_direct_service import (
    ChatOperationalLlmSynthesisBriefDirectService,
)
from app.domain.services.chat_response_mode_service import ChatResponseModeService

configure_domain_infrastructure_ports()


def _tool_calls(metadata: dict) -> list[dict]:
    return [{"name": "execute_external_action", "metadata": metadata}]


def test_fast_commentary_direct_builds_answer_without_llm():
    metadata = {
        "ok": True,
        "llmProseDecoupled": True,
        "path": "/products/10080045/analyser",
        "dataCommentary": {
            "highlights": [{"text": "O produto **10080045** está cadastrado como MP."}],
            "attention": ["Roteiro sem operações registradas."],
        },
    }

    answer = ChatOperationalLlmSynthesisBriefDirectService.try_build_direct_answer(
        "me fale do produto 10080045",
        _tool_calls(metadata),
        response_mode="fast",
    )

    assert answer
    assert "10080045" in answer
    assert "MP" in answer


def test_apply_turn_direct_answer_policy_fast_uses_commentary_direct():
    tool_context: dict = {}
    metadata = {
        "ok": True,
        "llmProseDecoupled": True,
        "path": "/products/10080045/analyser",
        "presentationDecision": {"layoutMode": "stack", "selected": "table"},
        "dataCommentary": {
            "highlights": [
                {"text": "O produto **10080045** está cadastrado como MP."},
            ],
        },
    }

    direct, skip_rag, effect = ChatResponseModeService.apply_turn_direct_answer_policy(
        message="me fale do produto 10080045",
        response_mode="fast",
        direct_answer=None,
        skip_rag=False,
        tool_calls=_tool_calls(metadata),
        tool_context=tool_context,
    )

    assert direct
    assert "10080045" in direct
    assert skip_rag is True
    assert effect == "llm_synthesis_brief"
    assert tool_context.get("commentaryBriefDirect") is True


def test_apply_turn_direct_answer_policy_fast_prefers_commentary_over_composite_direct():
    tool_context: dict = {}
    composite_direct = "### Status fabril\n\nProsa longa do presenter."
    metadata = {
        "ok": True,
        "llmProseDecoupled": True,
        "path": "/products/90260140/factory-status",
        "dataCommentary": {
            "highlights": [
                {
                    "text": (
                        "Status fabril **INTERMEDIÁRIOS EM PRODUÇÃO / PA NÃO FINALIZADO** "
                        "para o produto **90260140**."
                    ),
                },
            ],
        },
    }

    direct, skip_rag, effect = ChatResponseModeService.apply_turn_direct_answer_policy(
        message="Qual o status completo na fábrica do produto 90260140 hoje?",
        response_mode="fast",
        direct_answer=composite_direct,
        skip_rag=True,
        tool_calls=_tool_calls(metadata),
        tool_context=tool_context,
    )

    assert direct
    assert direct != composite_direct
    assert "90260140" in direct
    assert effect == "llm_synthesis_brief"
    assert tool_context.get("commentaryBriefDirect") is True


def test_normal_commentary_direct_builds_answer_when_enabled():
    metadata = {
        "ok": True,
        "llmProseDecoupled": True,
        "path": "/commercial/rol/summary",
        "dataCommentary": {
            "highlights": [
                "**rol:** R$ 3.717.926,47",
                "**Meta:** 3.466.000",
                "**% meta ROL:** 107,27%",
            ],
            "interpretation": "**Meta:** 3.466.000 **% meta ROL:** 107,27%",
        },
        "dataAnswer": {
            "summary": {
                "answer": "**rol:** R$ 3.717.926,47",
                "meaning": "**Meta:** 3.466.000 **% meta ROL:** 107,27%",
            }
        },
    }

    answer = ChatOperationalLlmSynthesisBriefDirectService.try_build_direct_answer(
        "maio de 2026",
        _tool_calls(metadata),
        response_mode="normal",
    )

    assert answer
    assert "% meta ROL" in answer
    assert "107,27%" in answer or "107.27%" in answer
    assert "3.466.000" in answer or "3466000" in answer.replace(".", "")


def test_apply_turn_direct_answer_policy_normal_uses_commentary_direct():
    tool_context: dict = {}
    metadata = {
        "ok": True,
        "llmProseDecoupled": True,
        "path": "/commercial/rol/summary",
        "dataCommentary": {
            "highlights": [
                "**rol:** R$ 3.717.926,47",
                "**% meta ROL:** 107,27%",
            ],
        },
    }

    direct, skip_rag, effect = ChatResponseModeService.apply_turn_direct_answer_policy(
        message="maio de 2026",
        response_mode="normal",
        direct_answer=None,
        skip_rag=False,
        tool_calls=_tool_calls(metadata),
        tool_context=tool_context,
    )

    assert direct
    assert "107,27%" in direct or "meta ROL" in direct
    assert skip_rag is True
    assert effect == "llm_synthesis"
    assert tool_context.get("commentaryBriefDirect") is True


def test_brief_direct_skips_sql_schema_prefetch_metadata():
    metadata = {
        "ok": True,
        "llmProseDecoupled": True,
        "sqlSchemaPrefetch": True,
        "suppressClientPresentation": True,
        "path": "/system/tables/search",
        "dataCommentary": {
            "summary": "Foram retornados **50** registros.",
            "highlights": [{"text": "Foram retornados **50** registros."}],
        },
    }

    assert not ChatOperationalLlmSynthesisBriefDirectService.try_build_direct_answer(
        "use sql para construir uma query que liste 5 produtos na tabela de produtos, grupo 1008",
        _tool_calls(metadata),
        response_mode="normal",
    )


def test_apply_turn_direct_answer_policy_respects_sql_requires_llm():
    tool_context = {
        "sqlRequiresLlm": True,
        "skipRag": False,
    }
    metadata = {
        "ok": True,
        "llmProseDecoupled": True,
        "sqlSchemaPrefetch": True,
        "path": "/system/tables/search",
        "dataCommentary": {
            "summary": "Foram retornados **50** registros.",
            "highlights": [{"text": "Foram retornados **50** registros."}],
        },
    }

    direct, skip_rag, effect = ChatResponseModeService.apply_turn_direct_answer_policy(
        message="use sql para construir uma query que liste 5 produtos",
        response_mode="normal",
        direct_answer=None,
        skip_rag=False,
        tool_calls=_tool_calls(metadata),
        tool_context=tool_context,
    )

    assert direct is None
    assert effect == "llm_synthesis"
    assert tool_context.get("commentaryBriefDirect") is not True


def test_apply_turn_direct_answer_policy_prefers_commentary_over_stale_tool_context_direct():
    tool_context: dict = {}
    metadata = {
        "ok": True,
        "llmProseDecoupled": True,
        "path": "/commercial/rol/summary",
        "dataCommentary": {
            "highlights": [
                "**rol:** R$ 3.717.926,47",
                "**% meta ROL:** 107,27%",
            ],
        },
    }

    direct, skip_rag, effect = ChatResponseModeService.apply_turn_direct_answer_policy(
        message="maio de 2026",
        response_mode="normal",
        direct_answer="Olá! Eu sou o assistente corporativo Minha DELPI Chat.",
        skip_rag=True,
        tool_calls=_tool_calls(metadata),
        tool_context=tool_context,
        pipeline_stages=["ingress", "tools", "post_tool", "direct_answer"],
    )

    assert direct
    assert "107,27%" in direct or "meta ROL" in direct
    assert "assistente corporativo" not in direct.lower()
    assert effect == "llm_synthesis"
    assert tool_context.get("commentaryBriefDirect") is True


def test_fast_brief_direct_uses_summary_when_no_highlights():
    metadata = {
        "ok": True,
        "llmProseDecoupled": True,
        "path": "/products/10080001/stock",
        "dataCommentary": {
            "profileKey": "stock",
            "summary": "Estoque consolidado de **120** unidades para o produto **10080001**.",
            "highlights": [],
        },
    }

    answer = ChatOperationalLlmSynthesisBriefDirectService.try_build_direct_answer(
        "estoque do produto 10080001",
        _tool_calls(metadata),
        response_mode="fast",
    )

    assert answer
    assert "120" in answer
    assert "10080001" in answer


def test_empty_result_does_not_qualify_for_brief_direct():
    metadata = {
        "ok": True,
        "llmProseDecoupled": True,
        "path": "/products/90260148/outbound-invoice-items",
        "emptyResult": True,
        "dataCommentary": {
            "profileKey": "generic_list",
            "emptyResult": True,
            "summary": "Nenhuma nota fiscal de saída encontrada para o produto 90260148.",
            "highlights": [],
        },
        "dataAnswer": {
            "emptyResult": True,
            "profileKey": "generic_list",
            "summary": {"answer": "Nenhuma nota fiscal de saída encontrada para o produto 90260148."},
        },
    }

    assert (
        ChatOperationalLlmSynthesisBriefDirectService.try_build_direct_answer(
            "ultimas notas fiscais do 90260148",
            _tool_calls(metadata),
            response_mode="normal",
        )
        is None
    )


def test_generic_list_summary_only_does_not_brief_direct_in_normal():
    metadata = {
        "ok": True,
        "llmProseDecoupled": True,
        "path": "/products/90260148/sales",
        "dataCommentary": {
            "profileKey": "generic_list",
            "summary": "Foram retornados **12** registros.",
            "highlights": [],
        },
    }

    tool_context: dict = {}
    direct, _, effect = ChatResponseModeService.apply_turn_direct_answer_policy(
        message="vendas do 90260148",
        response_mode="normal",
        direct_answer=None,
        skip_rag=False,
        tool_calls=_tool_calls(metadata),
        tool_context=tool_context,
    )

    assert tool_context.get("commentaryBriefDirect") is not True
    assert effect != "llm_synthesis_brief" or direct is None


def _stock_tool(code: str) -> dict:
    return {
        "name": "execute_external_action",
        "metadata": {
            "ok": True,
            "llmProseDecoupled": True,
            "path": f"/products/{code}/stock",
            "operationId": "get_product_stock",
            "dataCommentary": {
                "profileKey": "stock",
                "highlights": [
                    {"text": f"O produto **{code}** Saldo disponível total: **0** un."}
                ],
                "attention": [f"Valor zerado em estoque ({code})."],
            },
        },
    }


def test_normal_brief_direct_skips_when_grounded_enrich_insight_flag():
    tools = [_stock_tool("50230130")]
    tool_context = {"groundedEnrichInsight": True}

    answer = ChatOperationalLlmSynthesisBriefDirectService.try_build_direct_answer(
        "o que me diz sobre os itens?",
        tools,
        response_mode="normal",
        tool_context=tool_context,
    )

    assert answer is None
    assert ChatOperationalLlmSynthesisBriefDirectService.should_skip_for_cross_tool_insight(
        tools,
        tool_context=tool_context,
    )


def test_normal_brief_direct_skips_when_multi_tool_ok():
    tools = [
        _stock_tool("50230130"),
        _stock_tool("50230131"),
        _stock_tool("50230132"),
        _stock_tool("50230133"),
    ]

    answer = ChatOperationalLlmSynthesisBriefDirectService.try_build_direct_answer(
        "o que me diz sobre os itens?",
        tools,
        response_mode="normal",
        tool_context={},
    )

    assert answer is None


def test_normal_brief_direct_keeps_single_stock_without_enrich_flag():
    tools = [_stock_tool("10080109")]

    answer = ChatOperationalLlmSynthesisBriefDirectService.try_build_direct_answer(
        "estoque do 10080109",
        tools,
        response_mode="normal",
        tool_context={},
    )

    assert answer
    assert "10080109" in answer


def test_apply_turn_policy_normal_enrich_multi_tool_forces_llm_synthesis():
    tools = [
        _stock_tool("50230130"),
        _stock_tool("50230131"),
    ]
    tool_context = {"groundedEnrichInsight": True}

    direct, _, effect = ChatResponseModeService.apply_turn_direct_answer_policy(
        message="o que me diz sobre os itens?",
        response_mode="normal",
        direct_answer=None,
        skip_rag=False,
        tool_calls=tools,
        tool_context=tool_context,
    )

    assert direct is None
    assert tool_context.get("commentaryBriefDirect") is not True
    assert effect == "llm_synthesis"


def test_to_commentary_mirror_accepts_string_summary():
    from app.domain.services.chat_humanized_data_response_service import (
        ChatHumanizedDataResponseService,
    )

    mirror = ChatHumanizedDataResponseService.to_commentary_mirror(
        {"summary": "Saldo disponível em duas filiais.", "facts": []}
    )

    assert mirror is not None
    assert mirror.get("summary") == "Saldo disponível em duas filiais."
