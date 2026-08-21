from app.domain.services.chat_tool_grounding_context_service import (
    ChatToolGroundingContextService,
)
from app.domain.services.chat_tool_parameter_grounding_service import (
    ChatToolParameterGroundingService,
)


def test_ground_parameters_injects_code_from_memory_snapshot():
    action = {
        "parametersSchema": [
            {"name": "code", "required": True, "in": "path"},
        ]
    }
    memory = {
        "operationalFocus": {"productCode": "90261899"},
        "userContextItems": [],
    }

    grounded = ChatToolParameterGroundingService.ground_parameters(
        action,
        {},
        message="buscar desenho",
        memory_snapshot=memory,
    )

    assert grounded["code"] == "90261899"


def test_ground_parameters_uses_contextvar_scope():
    action = {
        "parametersSchema": [
            {"name": "code", "required": True, "in": "path"},
        ]
    }
    memory = {"operationalFocus": {"productCode": "90260140"}}

    with ChatToolGroundingContextService.scope(
        message="desenho do produto",
        memory_snapshot=memory,
    ):
        grounded = ChatToolParameterGroundingService.ground_parameters(action, {})

    assert grounded["code"] == "90260140"


def test_ground_parameters_keeps_explicit_code():
    action = {
        "parametersSchema": [
            {"name": "code", "required": True, "in": "path"},
        ]
    }

    grounded = ChatToolParameterGroundingService.ground_parameters(
        action,
        {"code": "11111111"},
        memory_snapshot={"operationalFocus": {"productCode": "90261899"}},
    )

    assert grounded["code"] == "11111111"
