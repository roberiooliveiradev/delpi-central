"""E2.S3 — contrato canônico Turn Understanding (schema / malformed / fallback)."""

from __future__ import annotations

from app.domain.entities.turn_understanding import (
    FORBIDDEN_ENTITY_KEYS,
    TURN_UNDERSTANDING_JSON_SCHEMA,
    TurnUnderstanding,
)
from app.domain.services.chat_turn_understanding_service import ChatTurnUnderstandingService
from app.domain.services.turn_understanding_authority_shadow_service import (
    TurnUnderstandingAuthorityShadowService,
)
from app.domain.services.turn_understanding_validator_service import (
    TurnUnderstandingValidatorService,
)


def test_schema_declares_goals_not_endpoint_enums():
    props = TURN_UNDERSTANDING_JSON_SCHEMA["properties"]
    assert "goals" in props
    assert "pathToken" not in props
    goal_props = props["goals"]["items"]["properties"]
    assert "intent" in goal_props
    assert "entities" in goal_props


def test_from_dict_roundtrip_preserves_goals_and_entities():
    payload = {
        "userGoal": "estoque do 10080001",
        "goals": [
            {
                "goalId": "g1",
                "intent": "consultar estoque do produto",
                "entities": {"productCode": "10080001", "pathToken": "/stock"},
                "dependsOn": [],
                "kind": "lookup",
            }
        ],
        "confidence": 0.8,
        "needsTool": True,
        "presentationIntent": {"view": "table"},
    }
    contract = TurnUnderstanding.from_dict(payload)
    assert contract is not None
    assert contract.goals[0].entities.get("productCode") == "10080001"
    assert "pathToken" not in contract.goals[0].entities
    assert contract.presentation_intent == {"view": "table"}
    assert contract.needs_tool is True
    assert contract.as_dict()["goals"][0]["goalId"] == "g1"


def test_validator_fallback_on_malformed_payload():
    result = TurnUnderstandingValidatorService.validate(
        {"confidence": "x"},
        fallback_message="qual o estoque?",
    )
    assert result.ok is False
    assert result.used_fallback is True
    assert result.contract is not None
    assert result.contract.subtask_count == 1
    assert "estoque" in result.contract.user_goal


def test_validator_fallback_on_missing_goals():
    result = TurnUnderstandingValidatorService.validate(
        {"userGoal": "oi", "goals": [], "confidence": 0.5},
        fallback_message="oi",
    )
    assert result.used_fallback is True
    assert result.contract.goals[0].intent


def test_validator_strips_forbidden_entity_keys():
    from app.domain.entities.turn_understanding import TurnUnderstandingGoal

    draft = TurnUnderstanding(
        user_goal="x",
        goals=(
            TurnUnderstandingGoal(
                goal_id="g1",
                intent="estoque",
                entities={"productCode": "1", "pathToken": "/stock"},
                kind="lookup",
            ),
        ),
        confidence=0.5,
    )
    result = TurnUnderstandingValidatorService.validate(draft)
    assert result.contract is not None
    assert "pathToken" not in result.contract.goals[0].entities
    assert any("forbidden_entity" in err for err in result.errors)


def test_analyze_emits_validated_contract_with_product_entity():
    understanding = ChatTurnUnderstandingService.analyze(
        "qual o estoque do produto 10080001?"
    )
    assert understanding.contract_version >= 1
    assert understanding.subtask_count == 1
    assert understanding.goals[0].entities.get("productCode") == "10080001"
    assert "goals" in understanding.as_dict()
    assert understanding.needs_tool is True


def test_analyze_presentation_intent_for_table_request():
    understanding = ChatTurnUnderstandingService.analyze("mostra o estoque em tabela")
    assert understanding.presentation_intent == {"view": "table"}


def test_authority_shadow_does_not_change_contract():
    understanding = ChatTurnUnderstandingService.analyze(
        "qual o estoque do produto 10080001?"
    )
    shadow = TurnUnderstandingAuthorityShadowService.compare(
        "qual o estoque do produto 10080001?",
        understanding,
    )
    assert shadow is not None
    assert shadow["cutover"] is False
    assert shadow["agreeProduct"] is True
    assert understanding.goals[0].intent  # unchanged


def test_forbidden_entity_keys_constant_covers_path_coupling():
    assert "pathToken" in FORBIDDEN_ENTITY_KEYS
    assert "routeSegment" in FORBIDDEN_ENTITY_KEYS
