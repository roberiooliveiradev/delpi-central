"""E3.S3 — contrato canônico de Turn Refinement + validator."""

from __future__ import annotations

from app.domain.entities.turn_refinement import (
    FORBIDDEN_SEMANTIC_KEYS,
    TURN_REFINEMENT_CONTRACT_VERSION,
    TurnRefinement,
    TurnRefinementTarget,
)
from app.domain.services.chat_operational_refinement.chat_operational_refinement_models import (
    OperationalRefinement,
)
from app.domain.services.turn_refinement_validator_service import (
    TurnRefinementValidatorService,
)


def test_e3_s3_from_dict_roundtrip_strips_path_decision_keys():
    raw = {
        "kind": "argument_delta",
        "confidence": 0.9,
        "target": {
            "kind": "action",
            "actionId": "acme.products.stock",
            "path": "/products/10080001/stock",
            "operationId": "get_stock",
            "routeSegment": "stock",
        },
        "argumentDelta": {
            "page": 2,
            "path": "/should/not/remain",
            "routeSegment": "stock",
            "pageSize": 50,
        },
        "reason": "próxima página",
        "source": "unit",
    }
    contract = TurnRefinement.from_dict(raw)
    assert contract is not None
    assert contract.contract_version == TURN_REFINEMENT_CONTRACT_VERSION
    assert contract.target is not None
    assert contract.target.action_id == "acme.products.stock"
    assert "path" not in contract.target.as_dict()
    assert "operationId" not in contract.target.as_dict()
    assert contract.argument_delta == {"page": 2, "page_size": 50}
    for forbidden in ("path", "routeSegment", "operationId"):
        assert forbidden in FORBIDDEN_SEMANTIC_KEYS

    roundtrip = TurnRefinement.from_dict(contract.as_dict())
    assert roundtrip is not None
    assert roundtrip.as_dict()["argumentDelta"] == {"page": 2, "page_size": 50}


def test_e3_s3_malformed_falls_back_to_clarify():
    result = TurnRefinementValidatorService.validate(None)
    assert result.ok is False
    assert result.used_fallback is True
    assert result.contract is not None
    assert result.contract.kind == "clarify"
    assert "malformed_or_missing_contract" in result.errors


def test_e3_s3_unknown_kind_normalized():
    result = TurnRefinementValidatorService.validate(
        {
            "kind": "totally_invented",
            "confidence": 0.5,
            "argumentDelta": {"branch": "02"},
        }
    )
    assert result.contract is not None
    assert result.contract.kind == "unknown"
    assert any(error.startswith("invalid_kind:") for error in result.errors)
    assert result.ok is False


def test_e3_s3_forbidden_fields_flagged_but_stripped():
    result = TurnRefinementValidatorService.validate(
        {
            "kind": "argument_delta",
            "confidence": 0.8,
            "path": "/products/x",
            "operationId": "get_x",
            "target": {"kind": "action", "actionId": "acme.x", "path": "/x"},
            "argumentDelta": {"branch": "02", "pathContains": "/stock"},
        }
    )
    assert result.ok is True
    assert result.contract is not None
    assert result.contract.argument_delta == {"branch": "02"}
    assert any(error.startswith("forbidden_") for error in result.errors)


def test_e3_s3_conflicting_inherited_arg_records_explicit_wins():
    result = TurnRefinementValidatorService.validate(
        {
            "kind": "argument_delta",
            "confidence": 0.85,
            "target": {"kind": "action", "actionId": "acme.products.stock"},
            "argumentDelta": {"branch": "02", "page": 1},
        },
        inherited_arguments={"branch": "01", "page": 1},
    )
    assert result.ok is True
    assert result.contract is not None
    assert len(result.contract.conflicts) == 1
    conflict = result.contract.conflicts[0]
    assert conflict.argument == "branch"
    assert conflict.inherited_value == "01"
    assert conflict.proposed_value == "02"
    assert conflict.resolution == "explicit_wins"
    assert "conflicting_inherited_arg:branch" in result.errors


def test_e3_s3_legacy_adapter_maps_pagination_without_path_authority():
    legacy = OperationalRefinement(
        kind="pagination_refinement",
        action_id="acme.products.stock",
        previous_path="/products/10080001/stock",
        route_segment="stock",
        page=2,
        page_size=None,
        product_code="10080001",
        previous_parameters={"page": 1, "page_size": 20, "code": "10080001"},
        reason="próxima página",
    )
    contract = TurnRefinement.from_legacy_operational_refinement(
        legacy,
        inherited_arguments={"page": 1},
    )
    ensured = TurnRefinementValidatorService.ensure(
        contract,
        inherited_arguments={"page": 1},
    )
    assert ensured.kind == "argument_delta"
    assert ensured.target == TurnRefinementTarget(
        kind="action",
        action_id="acme.products.stock",
    )
    assert ensured.argument_delta["page"] == 2
    assert ensured.argument_delta["product_code"] == "10080001"
    assert "path" not in ensured.as_dict()
    assert "routeSegment" not in ensured.as_dict().get("target", {})
    assert any(item.argument == "page" for item in ensured.conflicts)


def test_e3_s3_presentation_delta_and_clarify_shapes():
    presentation = TurnRefinementValidatorService.ensure(
        {
            "kind": "presentation_delta",
            "confidence": 0.6,
            "presentationDelta": {"view": "table", "path": "/ignore"},
        }
    )
    assert presentation.kind == "presentation_delta"
    assert presentation.presentation_delta == {"view": "table"}

    clarify = TurnRefinementValidatorService.ensure(
        {
            "kind": "clarify",
            "confidence": 0.3,
            "clarification": {
                "reason": "compare_previous",
                "promptHint": "Qual produto?",
                "candidates": ["10080001", "10080002"],
            },
        }
    )
    assert clarify.kind == "clarify"
    assert clarify.clarification is not None
    assert clarify.clarification.candidates == ("10080001", "10080002")
