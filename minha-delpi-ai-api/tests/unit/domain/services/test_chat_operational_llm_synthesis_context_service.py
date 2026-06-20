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
