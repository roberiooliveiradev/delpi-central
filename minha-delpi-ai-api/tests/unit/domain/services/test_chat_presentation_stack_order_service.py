from app.domain.services.chat_presentation_stack_order_service import (
    ChatPresentationStackOrderService,
)


def test_analyser_plan_profile_first_and_attention_last():
    metadata = {
        "path": "/products/90260149/analyser",
        "textPresentation": {
            "markdown": (
                "### Título\n\n**Destaques**\n\n- Um.\n\n"
                "**Pontos de atenção encontrados na API:**\n\n1. Dois."
            ),
        },
        "presentationDecision": {"visualOrder": ["text", "table", "tree"]},
    }

    plan = ChatPresentationStackOrderService.resolve_plan(metadata)

    assert plan["profileFirst"] is True
    assert plan["attentionLast"] is True
    assert plan["tableRoleOrder"][0] == "profile"
    assert plan["narrativeOrder"][-1] == "attention"


def test_enrich_metadata_attaches_plan():
    metadata = {
        "path": "/stock/90260149",
        "textPresentation": {"markdown": "**Destaques**\n\n- Saldo."},
    }

    ChatPresentationStackOrderService.enrich_metadata(metadata)

    assert metadata["stackPresentationPlan"]["tableRoleOrder"][0] == "profile"
