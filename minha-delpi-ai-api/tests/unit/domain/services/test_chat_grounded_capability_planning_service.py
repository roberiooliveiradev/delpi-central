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


class _ReviseSelectionStub:
    def __init__(self):
        self.repository = self

    def list_actions(self):
        return [
            {
                "actionId": "financial-rol",
                "operationId": "get_financial_rol",
                "path": "/financial/rol",
                "parametersSchema": [
                    {"name": "branch", "in": "query"},
                    {"name": "start_date", "in": "query"},
                    {"name": "end_date", "in": "query"},
                ],
            }
        ]

    def _list_allowed_candidates(self, message, *, allowed_action_ids, limit):
        return [
            action
            for action in self.list_actions()
            if action["actionId"] in set(allowed_action_ids)
        ]


def test_plan_revise_last_query_reexec_with_branch():
    selection = _ReviseSelectionStub()
    workspace = {
        "turnGrounding": {
            "status": "grounded",
            "stage": "grounded_revise_query",
            "excerpt": {"title": "ROL", "preview": "total"},
        },
        "workingMemory": {
            "lastResultExcerpt": {"title": "ROL", "preview": "total", "rowCount": 1},
            "lastAction": {
                "name": "financial_rol",
                "path": "/financial/rol",
                "operationId": "get_financial_rol",
                "params": {
                    "start_date": "01-08-2026",
                    "end_date": "28-08-2026",
                },
            },
        },
    }

    planned = ChatGroundedCapabilityPlanningService.plan_actions(
        selection,
        message="somente da filial 01",
        allowed_action_ids=["financial-rol"],
        workspace_context=workspace,
    )

    assert len(planned) == 1
    assert planned[0]["path"] == "/financial/rol"
    assert planned[0]["parameters"]["branch"] == "01"
    assert planned[0]["parameters"]["start_date"] == "01-08-2026"


def test_plan_revise_applies_period_slot_delta_dates():
    selection = _ReviseSelectionStub()
    workspace = {
        "turnGrounding": {
            "status": "grounded",
            "stage": "grounded_revise_query",
            "followUp": {
                "decision": "revise_last_query",
                "continuityMode": "consume_last_action",
                "slotDelta": {
                    "period": "previous_year_same_range",
                    "start_date": "01-08-2025",
                    "end_date": "28-08-2025",
                },
            },
            "excerpt": {"title": "ROL", "preview": "total"},
        },
        "workingMemory": {
            "lastResultExcerpt": {"title": "ROL", "preview": "total", "rowCount": 1},
            "lastAction": {
                "name": "financial_rol",
                "path": "/financial/rol",
                "operationId": "get_financial_rol",
                "params": {
                    "start_date": "01-08-2026",
                    "end_date": "28-08-2026",
                    "branch": "all",
                },
            },
        },
    }

    planned = ChatGroundedCapabilityPlanningService.plan_actions(
        selection,
        message="comparar com ano anterior",
        allowed_action_ids=["financial-rol"],
        workspace_context=workspace,
    )

    assert len(planned) == 1
    assert planned[0]["parameters"]["start_date"] == "01-08-2025"
    assert planned[0]["parameters"]["end_date"] == "28-08-2025"
    assert planned[0]["parameters"]["branch"] == "all"


def test_plan_revise_matches_action_id_leaf_across_locale_prefix():
    """lastAction pode vir com prefixo de catálogo legado (financeiro) ≠ action permitida (financial)."""

    class _LocaleStub(_ReviseSelectionStub):
        def list_actions(self):
            return [
                {
                    "actionId": "api_delpi.financial.get_financial_rol",
                    "operationId": None,
                    "path": "",
                    "parametersSchema": [
                        {"name": "branch", "in": "query"},
                        {"name": "start_date", "in": "query"},
                        {"name": "end_date", "in": "query"},
                    ],
                }
            ]

    selection = _LocaleStub()
    workspace = {
        "turnGrounding": {
            "status": "grounded",
            "stage": "grounded_revise_query",
            "followUp": {
                "decision": "revise_last_query",
                "continuityMode": "consume_last_action",
                "slotDelta": {"branch": "01"},
            },
        },
        "workingMemory": {
            "lastAction": {
                "name": "external_action",
                "path": "/financial/rol",
                "actionId": "api_delpi.financeiro.get_financial_rol",
                "params": {
                    "start_date": "01-08-2026",
                    "end_date": "31-08-2026",
                },
            },
        },
    }

    planned = ChatGroundedCapabilityPlanningService.plan_actions(
        selection,
        message="somente da filial 01",
        allowed_action_ids=["api_delpi.financial.get_financial_rol"],
        workspace_context=workspace,
    )

    assert len(planned) == 1
    assert planned[0]["actionId"] == "api_delpi.financial.get_financial_rol"
    assert planned[0]["parameters"]["branch"] == "01"
    assert planned[0]["parameters"]["start_date"] == "01-08-2026"


def test_plan_revise_without_excerpt_still_reexecs():
    selection = _ReviseSelectionStub()
    workspace = {
        "turnGrounding": {
            "status": "ungrounded",
            "stage": "grounded_revise_query",
            "followUp": {
                "decision": "revise_last_query",
                "continuityMode": "consume_last_action",
                "slotDelta": {"branch": "01"},
            },
        },
        "workingMemory": {
            "lastAction": {
                "name": "financial_rol",
                "path": "/financial/rol",
                "operationId": "get_financial_rol",
                "params": {"start_date": "01-08-2026", "end_date": "28-08-2026"},
            },
        },
    }

    planned = ChatGroundedCapabilityPlanningService.plan_actions(
        selection,
        message="somente da filial 01",
        allowed_action_ids=["financial-rol"],
        workspace_context=workspace,
    )

    assert len(planned) == 1
    assert planned[0]["parameters"]["branch"] == "01"


def test_plan_revise_strips_invented_limit_without_schema():
    class _NoSchemaStub(_ReviseSelectionStub):
        def list_actions(self):
            return [
                {
                    "actionId": "api_delpi.financial.get_financial_rol",
                    "path": "",
                    "parametersSchema": [],
                }
            ]

    selection = _NoSchemaStub()
    workspace = {
        "turnGrounding": {
            "status": "grounded",
            "stage": "grounded_revise_query",
            "followUp": {
                "decision": "revise_last_query",
                "continuityMode": "consume_last_action",
                "slotDelta": {"branch": "01"},
            },
        },
        "workingMemory": {
            "lastAction": {
                "path": "/financial/rol",
                "actionId": "api_delpi.financeiro.get_financial_rol",
                "params": {
                    "start_date": "01-08-2026",
                    "end_date": "31-08-2026",
                },
            },
        },
    }

    planned = ChatGroundedCapabilityPlanningService.plan_actions(
        selection,
        message="somente da filial 01",
        allowed_action_ids=["api_delpi.financial.get_financial_rol"],
        workspace_context=workspace,
    )

    assert len(planned) == 1
    assert planned[0]["parameters"]["branch"] == "01"
    assert planned[0]["parameters"]["start_date"] == "01-08-2026"
    assert "limit" not in planned[0]["parameters"]
    assert "granularity" not in planned[0]["parameters"]


def test_plan_revise_without_last_action_returns_empty():
    selection = _ReviseSelectionStub()
    workspace = {
        "turnGrounding": {
            "status": "grounded",
            "stage": "grounded_revise_query",
        },
        "workingMemory": {
            "lastResultExcerpt": {"title": "ROL", "preview": "total", "rowCount": 1},
        },
    }

    planned = ChatGroundedCapabilityPlanningService.plan_actions(
        selection,
        message="somente da filial 01",
        allowed_action_ids=["financial-rol"],
        workspace_context=workspace,
    )

    assert planned == []
