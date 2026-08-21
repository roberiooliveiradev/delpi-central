from app.domain.services.chat_error_handling_classifier import ChatErrorHandlingClassifier
from app.domain.services.chat_tool_parameter_grounding_service import (
    ChatToolParameterGroundingService,
)
from app.domain.services.external_actions.external_action_execution_policy import (
    ExternalActionExecutionPolicy,
)
from app.domain.exceptions.external_action_exceptions import ExternalActionValidationError
import pytest


_DRAWING_ACTION = {
    "enabled": True,
    "method": "GET",
    "path": "/products/{code}/drawing",
    "actionId": "api_delpi.products.get_product_drawing",
    "parametersSchema": [
        {"name": "code", "required": True, "in": "path"},
    ],
}


def test_get_product_drawing_grounds_code_from_operational_focus():
    memory = {"operationalFocus": {"productCode": "90261899"}}

    grounded = ChatToolParameterGroundingService.ground_parameters(
        _DRAWING_ACTION,
        {},
        message="confirmar revisão manual do item pendente",
        memory_snapshot=memory,
    )

    assert grounded["code"] == "90261899"

    ExternalActionExecutionPolicy().validate(
        {"enabled": True},
        _DRAWING_ACTION,
        {"parameters": grounded},
    )


def test_get_product_drawing_without_code_is_missing_required_not_api_unavailable():
    with pytest.raises(ExternalActionValidationError) as raised:
        ExternalActionExecutionPolicy().validate(
            {"enabled": True},
            _DRAWING_ACTION,
            {"parameters": {}},
        )

    tool_calls = [
        {
            "name": "execute_external_action",
            "arguments": {"parameters": {}},
            "metadata": {
                **raised.value.to_metadata(),
                "actionId": "api_delpi.products.get_product_drawing",
                "path": "/products/{code}/drawing",
            },
        }
    ]

    classification = ChatErrorHandlingClassifier.classify(
        message="buscar desenho",
        answer="erro",
        tool_calls=tool_calls,
    )

    assert classification is not None
    assert classification.error_type == "missing_required_parameter"
    assert classification.api_failed is False
