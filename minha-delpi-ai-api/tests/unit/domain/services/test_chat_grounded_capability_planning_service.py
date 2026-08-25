from app.domain.services.chat_grounded_capability_planning_service import (
    ChatGroundedCapabilityPlanningService,
)
from app.domain.services.chat_turn_grounding_service import ChatTurnGroundingService


class _SelectionStub:
    def __init__(self):
        self.calls: list[dict] = []

    def select_action_for_product(self, message, *, product_code, allowed_action_ids, intent, route_segment=None, previous_messages=None):
        self.calls.append(
            {
                "product_code": product_code,
                "intent": intent,
                "route_segment": route_segment,
            }
        )
        return {
            "actionId": f"action-{intent}-{product_code}",
            "intent": intent,
            "productCode": product_code,
        }


def test_plan_stock_fan_out_from_top_keys():
    selection = _SelectionStub()
    workspace = {
        "turnGrounding": {"status": "grounded"},
        "workingMemory": {
            "lastResultExcerpt": {
                "title": "Estrutura 90260149",
                "rowCount": 2,
                "topKeys": ["10380044", "10380045"],
            }
        },
    }

    planned = ChatGroundedCapabilityPlanningService.plan_actions(
        selection,
        message="e o estoque desses itens?",
        allowed_action_ids=["get_product_stock"],
        workspace_context=workspace,
    )

    assert len(planned) == 2
    assert {item["productCode"] for item in planned} == {"10380044", "10380045"}
    assert all(item["intent"] == "stock" for item in planned)


def test_plan_empty_when_narrate_excerpt():
    selection = _SelectionStub()
    excerpt = {
        "title": "Estrutura 90260149",
        "rowCount": 6,
        "topKeys": ["10380044"],
    }
    workspace = {
        "turnGrounding": {"status": "grounded"},
        "workingMemory": {"lastResultExcerpt": excerpt},
    }

    assert not ChatTurnGroundingService.should_narrate_excerpt(
        "o que me diz sobre os itens?",
        excerpt,
    )
    assert ChatTurnGroundingService.should_enrich_before_insight(
        "o que me diz sobre os itens?",
        excerpt,
    )

    planned = ChatGroundedCapabilityPlanningService.plan_actions(
        selection,
        message="o que me diz sobre os itens?",
        allowed_action_ids=["get_product_stock", "get_product_summary"],
        workspace_context=workspace,
    )

    assert len(planned) >= 1
    assert selection.calls


def test_plan_stock_fan_out_ignores_inherited_parent_code_only():
    selection = _SelectionStub()
    workspace = {
        "turnGrounding": {"status": "grounded"},
        "workingMemory": {
            "operationalFocus": {"productCode": "90260149"},
            "lastResultExcerpt": {
                "title": "Estrutura 90260149",
                "rowCount": 2,
                "topKeys": ["10380044", "10380045"],
            },
        },
    }

    planned = ChatGroundedCapabilityPlanningService.plan_actions(
        selection,
        message="e o estoque desses itens?",
        allowed_action_ids=["get_product_stock"],
        workspace_context=workspace,
    )

    assert len(planned) == 2
    assert {item["productCode"] for item in planned} == {"10380044", "10380045"}


def test_plan_stock_uses_mp_codes_for_raw_material_referent():
    selection = _SelectionStub()
    workspace = {
        "turnGrounding": {"status": "grounded"},
        "workingMemory": {
            "operationalFocus": {"productCode": "90260149"},
            "lastResultExcerpt": {
                "title": "Estrutura 90260149",
                "rowCount": 2,
                "topKeys": ["50231850", "50231851", "10080109"],
                "keysByComponentType": {
                    "PI": ["50231850", "50231851"],
                    "MP": ["10080109", "10090014"],
                },
            },
        },
    }

    planned = ChatGroundedCapabilityPlanningService.plan_actions(
        selection,
        message="estoque das matérias-primas",
        allowed_action_ids=["get_product_stock"],
        workspace_context=workspace,
    )

    assert len(planned) == 2
    assert {item["productCode"] for item in planned} == {"10080109", "10090014"}
    assert "90260149" not in {item["productCode"] for item in planned}


def test_plan_stock_mp_referent_without_bucket_does_not_fallback_to_pi():
    selection = _SelectionStub()
    workspace = {
        "turnGrounding": {"status": "grounded"},
        "workingMemory": {
            "operationalFocus": {"productCode": "90260149"},
            "lastResultExcerpt": {
                "title": "Estoque 50230130",
                "topKeys": ["50230130"],
                "path": "/products/50230130/stock",
            },
        },
    }

    planned = ChatGroundedCapabilityPlanningService.plan_actions(
        selection,
        message="qual o estoque das matérias-primas?",
        allowed_action_ids=["get_product_stock"],
        workspace_context=workspace,
    )

    assert planned == []
