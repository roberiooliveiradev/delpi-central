from app.domain.services.chat_error_handling_classifier import ChatErrorHandlingClassifier
from app.domain.services.chat_trust_signals_service import ChatTrustSignalsService


def test_missing_required_parameter_not_classified_as_api_unavailable():
    tool_calls = [
        {
            "name": "execute_external_action",
            "arguments": {"parameters": {}},
            "metadata": {
                "ok": False,
                "statusCode": 0,
                "path": "/products/{code}/drawing",
                "actionId": "api_delpi.products.get_product_drawing",
                "error": "Missing required parameter: code",
            },
        }
    ]

    classification = ChatErrorHandlingClassifier.classify(
        message="buscar desenho do produto",
        answer="Erro na consulta",
        tool_calls=tool_calls,
    )

    assert classification is not None
    assert classification.error_type == "missing_required_parameter"
    assert classification.api_failed is False


def test_missing_required_parameter_via_error_kind_metadata():
    tool_calls = [
        {
            "name": "execute_external_action",
            "arguments": {"parameters": {}},
            "metadata": {
                "ok": False,
                "statusCode": 0,
                "path": "/products/{code}/drawing",
                "actionId": "api_delpi.products.get_product_drawing",
                "errorKind": "missing_required_parameter",
                "missingParameter": "code",
                "error": "Validation failed",
            },
        }
    ]

    classification = ChatErrorHandlingClassifier.classify(
        message="buscar desenho",
        answer="Falha",
        tool_calls=tool_calls,
    )

    assert classification is not None
    assert classification.error_type == "missing_required_parameter"


def test_trust_signals_validation_failure_not_api_unavailable():
    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": False,
                "error": "Missing required parameter: code",
            },
        }
    ]

    signals = ChatTrustSignalsService.build(
        message="desenho",
        answer="erro",
        tool_calls=tool_calls,
        sources=None,
    )
    ids = {item["id"] for item in signals}

    assert "missing_required_parameter" in ids
    assert "api_unavailable" not in ids
