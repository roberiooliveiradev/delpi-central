from app.domain.services.chat_drawing_analyser_parameter_service import (
    ChatDrawingAnalyserParameterService,
)


def test_apply_to_parameters_forces_full_view_in_drawing_mode():
    action = {
        "path": "/products/{code}/analyser",
        "parametersSchema": [
            {"name": "code"},
            {"name": "view"},
            {"name": "page_size"},
        ],
    }

    parameters = ChatDrawingAnalyserParameterService.apply_to_parameters(
        {"code": "90264227", "view": "summary", "page_size": 3},
        action=action,
        drawing_analysis_mode=True,
    )

    assert parameters["view"] == "full"


def test_drawing_analysis_mode_forces_full_without_textual_trigger():
    action = {
        "path": "/products/{code}/analyser",
        "parametersSchema": [{"name": "code"}, {"name": "view"}],
    }

    parameters = ChatDrawingAnalyserParameterService.apply_to_parameters(
        {"code": "90264227", "view": "summary", "page_size": 3},
        action=action,
        drawing_analysis_mode=True,
        message="",
    )

    assert parameters["view"] == "full"


def test_apply_to_tool_call_patches_analyser_parameters():
    tool_call = {
        "name": "execute_external_action",
        "arguments": {
            "actionId": "get_product_analyser",
            "parameters": {"code": "90264227", "view": "summary"},
        },
    }

    patched = ChatDrawingAnalyserParameterService.apply_to_tool_call(
        tool_call,
        action={
            "path": "/products/{code}/analyser",
            "parametersSchema": [{"name": "code"}, {"name": "view"}],
        },
        drawing_analysis_mode=True,
    )

    assert patched["arguments"]["parameters"]["view"] == "full"
