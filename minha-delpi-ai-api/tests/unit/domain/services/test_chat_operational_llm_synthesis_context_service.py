from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_operational_llm_synthesis_context_service import (
    ChatOperationalLlmSynthesisContextService,
)

configure_domain_infrastructure_ports()


def _tool_calls(metadata: dict) -> list[dict]:
    return [{"name": "execute_external_action", "metadata": metadata}]


def test_collect_fact_lines_from_data_answer_and_tables():
    metadata = {
        "ok": True,
        "path": "/products/90269002/factory-status",
        "dataAnswer": {
            "summary": {"answer": "PA PRODUZIDO com saldo MP 6082"},
            "highlights": [{"text": "OP 12345 em andamento"}],
        },
        "tablePresentations": [
            {
                "title": "Panorama fabril",
                "rows": [{"situacao": "PA PRODUZIDO", "saldo_mp": "6082"}],
            }
        ],
    }

    lines = ChatOperationalLlmSynthesisContextService.collect_fact_lines(_tool_calls(metadata))

    assert any("90269002" in line or "PA PRODUZIDO" in line for line in lines)
    assert any("6082" in line for line in lines)


def test_collect_fact_lines_from_playbook_presentation_rows():
    metadata = {
        "ok": True,
        "path": "/production/consumption/top-items",
        "humanizedSummary": {"titulo": "Itens mais consumidos"},
        "presentation": {
            "type": "table",
            "title": "Itens mais consumidos",
            "rows": [
                {
                    "item_code": "10010032",
                    "description": "MP TESTE A",
                    "real_consumption_qty": 120.0,
                }
            ],
        },
    }

    lines = ChatOperationalLlmSynthesisContextService.collect_fact_lines(_tool_calls(metadata))

    assert any("10010032" in line for line in lines)
    assert any("MP TESTE A" in line for line in lines)
    assert any("120" in line for line in lines)


def test_collect_fact_lines_formats_profile_campo_valor_rows():
    metadata = {
        "ok": True,
        "path": "/products/10080024/analyser",
        "tablePresentations": [
            {
                "type": "table",
                "role": "profile",
                "title": "Produto 10080024",
                "rows": [
                    {"campo": "Código", "valor": "10080024"},
                    {"campo": "Descrição", "valor": "TERM. OLHAL M6"},
                    {"campo": "Tipo", "valor": "MP"},
                ],
            }
        ],
    }

    lines = ChatOperationalLlmSynthesisContextService.collect_fact_lines(_tool_calls(metadata))

    assert any(line.endswith("Código: 10080024") or "Código: 10080024" in line for line in lines)
    assert any("Descrição: TERM. OLHAL M6" in line for line in lines)
    assert not any("campo:" in line for line in lines)


def test_collect_fact_lines_from_archived_humanized_when_decoupled():
    metadata = {
        "ok": True,
        "path": "/products/90269002/factory-status",
        "llmProseDecoupled": True,
        "humanizedSummary": {"titulo": "Status", "linhas": []},
        "templateProseArchive": {
            "humanizedSummary": {
                "titulo": "Status",
                "linhas": ["- Saldo MP **6082**."],
            },
        },
    }

    lines = ChatOperationalLlmSynthesisContextService.collect_fact_lines(_tool_calls(metadata))

    assert any("6082" in line for line in lines)


def test_build_facts_addon_includes_title():
    metadata = {
        "ok": True,
        "path": "/products/90269002/factory-status",
        "dataAnswer": {"summary": {"answer": "PA PRODUZIDO"}},
    }

    addon = ChatOperationalLlmSynthesisContextService.build_facts_addon(_tool_calls(metadata))

    assert "Fatos já consultados" in addon
    assert "PA PRODUZIDO" in addon


def test_build_prompt_policy_includes_facts_block():
    from app.domain.services.chat_operational_narrative_synthesis_service import (
        ChatOperationalNarrativeSynthesisService,
    )

    metadata = {
        "ok": True,
        "path": "/products/90269002/factory-status",
        "presentationDecision": {"layoutMode": "stack", "presentationMode": "summary_then_evidence"},
        "dataAnswer": {"summary": {"answer": "PA PRODUZIDO"}},
    }

    addon = ChatOperationalNarrativeSynthesisService.build_prompt_policy_addon(
        "qual o status do produto 90269002 na fabrica hoje?",
        response_mode="fast",
        tool_calls=_tool_calls(metadata),
    )

    assert "Rápida" in addon or "curta" in addon.lower()
    assert "PA PRODUZIDO" in addon


def test_collect_fact_lines_from_failed_tool():
    metadata = {
        "ok": False,
        "path": "/production/consumption/top-items",
        "statusCode": 503,
        "message": "Serviço indisponível",
    }

    lines = ChatOperationalLlmSynthesisContextService.collect_fact_lines(_tool_calls(metadata))

    assert any("503" in line for line in lines)
    assert any("indisponível" in line.lower() for line in lines)


def test_collect_fact_lines_from_sql_rows():
    metadata = {
        "ok": True,
        "path": "/data/sql",
        "humanizedSummary": {
            "sqlRows": [{"produto": "90269001", "saldo": "150"}],
        },
    }

    lines = ChatOperationalLlmSynthesisContextService.collect_fact_lines(_tool_calls(metadata))

    assert any("90269001" in line for line in lines)
    assert any("150" in line for line in lines)


def test_resolve_synthesis_kind_playbook_path():
    from app.domain.services.chat_operational_narrative_synthesis_service import (
        ChatOperationalNarrativeSynthesisService,
    )

    kind = ChatOperationalNarrativeSynthesisService.resolve_synthesis_kind(
        "top itens consumo",
        _tool_calls(
            {
                "ok": True,
                "path": "/production/consumption/top-items",
            }
        ),
    )

    assert kind == "operational_data"


def test_resolve_synthesis_kind_error_recovery():
    from app.domain.services.chat_operational_narrative_synthesis_service import (
        ChatOperationalNarrativeSynthesisService,
    )

    kind = ChatOperationalNarrativeSynthesisService.resolve_synthesis_kind(
        "top itens consumo",
        _tool_calls({"ok": False, "path": "/production/consumption/top-items"}),
    )

    assert kind == "error_recovery"


def test_collect_fact_lines_skips_profile_table_rows_when_decoupled():
    metadata = {
        "ok": True,
        "llmProseDecoupled": True,
        "path": "/products/10080045/analyser",
        "tablePresentations": [
            {
                "type": "table",
                "role": "profile",
                "title": "Produto 10080045",
                "rows": [
                    {"campo": "Código", "valor": "10080045"},
                    {"campo": "Descrição", "valor": "TERM. OLHAL M6"},
                ],
            }
        ],
        "dataAnswer": {
            "highlights": [{"text": "Produto cadastrado como MP."}],
        },
    }

    lines = ChatOperationalLlmSynthesisContextService.collect_fact_lines(_tool_calls(metadata))

    assert not any("Código:" in line for line in lines)
    assert any("10080045" in line for line in lines)
    assert any("MP" in line for line in lines)


def test_build_facts_addon_includes_prose_panel_rule_when_decoupled():
    metadata = {
        "ok": True,
        "llmProseDecoupled": True,
        "path": "/products/10080045/analyser",
        "dataAnswer": {"summary": {"answer": "Produto cadastrado."}},
    }

    addon = ChatOperationalLlmSynthesisContextService.build_facts_addon(_tool_calls(metadata))

    assert "componentes visuais" in addon.lower()
    assert "painel" in addon.lower()
    assert "fidelidade" in addon.lower()


def test_collect_fact_lines_includes_api_section_counts_and_attention():
    metadata = {
        "ok": True,
        "llmProseDecoupled": True,
        "path": "/products/10080045/analyser",
        "apiDelpiResponseMeta": {
            "sections": [
                {"label": "Roteiro", "itemCount": 0},
                {"label": "Inspeção", "itemCount": 2},
            ]
        },
        "dataCommentary": {
            "attention": ["Roteiro sem operações cadastradas."],
        },
        "dataAnswer": {
            "highlights": [{"text": "Produto cadastrado como MP."}],
        },
    }

    lines = ChatOperationalLlmSynthesisContextService.collect_fact_lines(_tool_calls(metadata))

    assert any("10080045" in line for line in lines)
    assert any("Roteiro: nenhum registro" in line for line in lines)
    assert any("roteiro sem operações" in line.lower() for line in lines)
