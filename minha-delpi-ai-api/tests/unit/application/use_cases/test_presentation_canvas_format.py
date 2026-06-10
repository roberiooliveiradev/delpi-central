from app.application.use_cases.execute_external_action_use_case import (
    ExecuteExternalActionUseCase,
)


def _use_case():
    return ExecuteExternalActionUseCase(
        repository=None,
        gateway=None,
        policy=None,
        audit_repository=None,
    )


def test_canvas_session_format_does_not_map_to_text_preference():
    use_case = _use_case()
    meta = use_case._build_presentation_metadata(
        action={"path": "/commercial/closing-rate"},
        sanitized_data={
            "value": 82.5,
            "target": 90.0,
            "previous": 80.0,
            "unit": "%",
        },
        resolved_path="/commercial/closing-rate",
        request_parameters={"sessionResponseFormat": "canvas"},
    )

    assert meta["preferredFormat"] == "canvas"
    assert meta["presentationDecision"]["selected"] == "canvas"
