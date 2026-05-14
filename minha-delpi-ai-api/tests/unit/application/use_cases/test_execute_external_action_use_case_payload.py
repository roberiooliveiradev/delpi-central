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


def test_normalize_get_body_dict_into_parameters():
    use_case = _use_case()

    arguments = use_case._normalize_arguments_for_method(
        {"method": "GET"},
        {
            "parameters": {"existing": "kept"},
            "body": {
                "produto": "10080014",
                "empty": "",
                "none": None,
            },
        },
    )

    assert arguments["parameters"] == {
        "existing": "kept",
        "produto": "10080014",
    }
    assert arguments["body"] is None


def test_normalize_get_body_does_not_override_existing_parameter():
    use_case = _use_case()

    arguments = use_case._normalize_arguments_for_method(
        {"method": "GET"},
        {
            "parameters": {"produto": "query-value"},
            "body": {"produto": "body-value"},
        },
    )

    assert arguments["parameters"] == {"produto": "query-value"}
    assert arguments["body"] is None


def test_normalize_post_keeps_body():
    use_case = _use_case()

    arguments = use_case._normalize_arguments_for_method(
        {"method": "POST"},
        {
            "parameters": {},
            "body": {"produto": "10080014"},
        },
    )

    assert arguments["parameters"] == {}
    assert arguments["body"] == {"produto": "10080014"}


def test_normalize_get_non_dict_body_is_removed():
    use_case = _use_case()

    arguments = use_case._normalize_arguments_for_method(
        {"method": "GET"},
        {
            "parameters": {"produto": "10080014"},
            "body": "raw body",
        },
    )

    assert arguments["parameters"] == {"produto": "10080014"}
    assert arguments["body"] is None
