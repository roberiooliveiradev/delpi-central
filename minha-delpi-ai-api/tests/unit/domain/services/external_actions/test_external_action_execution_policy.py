import pytest

from app.domain.exceptions.external_action_exceptions import ExternalActionValidationError
from app.domain.services.external_actions.external_action_execution_policy import (
    ExternalActionExecutionPolicy,
)


def _provider():
    return {"enabled": True}


def _action(method):
    return {
        "enabled": True,
        "method": method,
        "path": "/produtos",
        "parametersSchema": [],
    }


def test_policy_allows_empty_body_for_get_delete_head():
    policy = ExternalActionExecutionPolicy()

    for method in ["GET", "get", "HEAD", "DELETE"]:
        policy.validate(
            _provider(),
            _action(method),
            {
                "parameters": {},
                "body": {},
            },
        )


def test_policy_rejects_non_empty_body_for_get():
    policy = ExternalActionExecutionPolicy()

    with pytest.raises(ValueError, match="body is not allowed"):
        policy.validate(
            _provider(),
            _action("GET"),
            {
                "parameters": {},
                "body": {"produto": "10080014"},
            },
        )


def test_policy_missing_required_parameter_has_error_kind():
    policy = ExternalActionExecutionPolicy()
    action = {
        "enabled": True,
        "method": "GET",
        "path": "/products/{code}/drawing",
        "parametersSchema": [
            {"name": "code", "required": True, "in": "path"},
        ],
    }

    with pytest.raises(ExternalActionValidationError) as raised:
        policy.validate(_provider(), action, {"parameters": {}})

    assert raised.value.error_kind == "missing_required_parameter"
    assert raised.value.missing_parameter == "code"
    metadata = raised.value.to_metadata()
    assert metadata["errorKind"] == "missing_required_parameter"
    assert metadata["missingParameter"] == "code"
    assert metadata["ok"] is False
