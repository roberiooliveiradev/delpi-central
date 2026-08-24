from app.application.services.chat_grounded_insight_answer_service import (
    ChatGroundedInsightAnswerService,
)
from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_entity_capability_catalog_service import (
    ChatEntityCapabilityCatalogService,
)

configure_domain_infrastructure_ports()


def test_enrich_insight_scopes_for_structure():
    scopes = ChatEntityCapabilityCatalogService.enrich_insight_scopes("structure")

    assert "stock" in scopes
    assert "profile" in scopes


def test_artifact_enrich_key_maps_product_structure():
    key = ChatEntityCapabilityCatalogService.artifact_enrich_key(
        "product_structure",
        None,
    )

    assert key == "structure"


def test_apply_enrich_context_sets_flag():
    workspace = {
        "turnGrounding": {
            "status": "grounded",
            "stage": "grounded_enrich_insight",
            "excerpt": {"title": "Estrutura 90260149", "topKeys": ["10380044"]},
        },
        "workingMemory": {
            "lastResultExcerpt": {
                "title": "Estrutura 90260149",
                "topKeys": ["10380044"],
            }
        },
    }

    applied, tool_context = ChatGroundedInsightAnswerService.apply_enrich_context(
        "o que me diz sobre os itens?",
        [],
        {},
        workspace_context=workspace,
    )

    assert applied
    assert tool_context.get("groundedEnrichInsight") is True
    assert "90260149" in str(tool_context.get("context") or "")


def test_build_template_fallback_uses_commentary():
    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "path": "/products/10380044/stock",
                "dataCommentary": {
                    "profileKey": "stock",
                    "highlights": [
                        "Saldo disponível total: **120** un. em **1** posição(ões).",
                    ],
                },
            },
        }
    ]

    fallback = ChatGroundedInsightAnswerService.build_template_fallback(
        "o que me diz sobre os itens?",
        tool_calls,
        response_mode="normal",
    )

    assert fallback
    assert "120" in fallback or "saldo" in fallback.lower()
