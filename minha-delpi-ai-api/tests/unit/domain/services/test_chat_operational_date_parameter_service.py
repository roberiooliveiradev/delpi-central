from datetime import date
from unittest.mock import patch

from app.application.services.external_actions.external_action_selection_service import (
    ExternalActionSelectionService,
)
from app.application.services.chat_active_pending_service import (
    ChatActivePendingService,
)
from app.domain.services.chat_operational_date_parameter_service import (
    ChatOperationalDateParameterService,
)
from app.domain.services.chat_operational_parameter_service import (
    ChatOperationalParameterService,
)
from tests.unit.application.services.test_external_action_selection_service import (
    FakeRepository,
)


def test_optional_date_not_required_for_raw_material_price_intelligence():
    action = {
        "path": "/products/{code}/raw-material-price-intelligence",
        "parametersSchema": [
            {"name": "code"},
            {"name": "date_start"},
            {"name": "date_end"},
        ],
    }

    assert ChatOperationalDateParameterService.action_has_date_query_params(action) is True
    assert ChatOperationalDateParameterService.action_requires_explicit_date(action) is False


def test_missing_date_not_requested_for_raw_material_price_intelligence():
    answer = ChatOperationalParameterService.resolve_missing_date_answer(
        "Análise de preço da matéria-prima 10080001"
    )

    assert answer is None


def test_resolve_missing_date_answer_for_factory_status_without_period():
    answer = ChatOperationalParameterService.resolve_missing_date_answer(
        "Qual o status completo na fábrica do produto 90263059?"
    )

    assert answer is not None
    assert "data" in answer.lower() or "período" in answer.lower() or "periodo" in answer.lower()


def test_missing_date_not_requested_for_stock_with_product_code():
    answer = ChatOperationalParameterService.resolve_missing_date_answer(
        "estoque do produto 90263059"
    )

    assert answer is None


def test_missing_date_not_requested_when_hoje_in_same_message():
    answer = ChatOperationalParameterService.resolve_missing_date_answer(
        "Qual o status completo na fábrica do produto 90263059 hoje?"
    )

    assert answer is None


def test_merge_into_parameters_sets_reference_date_for_playbook_route():
    action = {
        "path": "/products/{code}/factory-status",
        "parametersSchema": [
            {"name": "code"},
            {"name": "reference_date"},
            {"name": "date_start"},
            {"name": "date_end"},
        ],
    }

    with patch("app.domain.services.chat_date_range_intent_service.date") as mock_date:
        mock_date.today.return_value = date(2026, 6, 9)

        parameters = ChatOperationalDateParameterService.merge_into_parameters(
            action,
            "status fabril do 90263059 hoje",
            {"code": "90263059"},
            previous_messages=None,
        )

    assert parameters["reference_date"] == "09-06-2026"
    assert parameters["date_start"] == "09-06-2026"
    assert parameters["date_end"] == "09-06-2026"


def test_compose_selection_message_after_missing_date_reply():
    history = [
        {
            "role": "assistant",
            "metadata": {
                "activePending": {
                    "kind": "missing_date",
                    "context": {
                        "originalMessage": "status fabril do 90263059",
                        "productCode": "90263059",
                        "subIntent": "factory_status",
                    },
                }
            },
        }
    ]

    with patch("app.domain.services.chat_date_range_intent_service.date") as mock_date:
        mock_date.today.return_value = date(2026, 6, 9)

        composed = ChatOperationalDateParameterService.compose_selection_message(
            "hoje",
            previous_messages=history,
        )

    assert "90263059" in composed
    assert "hoje" in composed


def test_try_resolve_missing_date_pending_with_hoje():
    pending = {
        "kind": "missing_date",
        "context": {
            "originalMessage": "status fabril do 90263059",
            "productCode": "90263059",
        },
    }

    with patch("app.domain.services.chat_date_range_intent_service.date") as mock_date:
        mock_date.today.return_value = date(2026, 6, 9)

        resolved = ChatActivePendingService.try_resolve("hoje", pending)

    assert resolved is not None
    assert resolved["resolvedParams"]["referenceDate"] == "09-06-2026"
    assert resolved["resolvedParams"]["productCode"] == "90263059"


def test_product_selection_skipped_without_date_for_factory_status():
    service = ExternalActionSelectionService(
        FakeRepository(
            [
                {
                    "actionId": "factory-status",
                    "method": "GET",
                    "path": "/products/{code}/factory-status",
                    "operationId": "get_product_factory_status",
                    "summary": "Status fabril",
                    "parametersSchema": [
                        {"name": "code"},
                        {"name": "reference_date"},
                        {"name": "date_start"},
                        {"name": "date_end"},
                    ],
                }
            ]
        )
    )

    selected = service.select_action_for_product(
        "status fabril do 90263059",
        product_code="90263059",
        allowed_action_ids=["factory-status"],
        previous_messages=None,
    )

    assert selected is None


def test_product_selection_includes_reference_date_for_factory_status_today():
    service = ExternalActionSelectionService(
        FakeRepository(
            [
                {
                    "actionId": "factory-status",
                    "method": "GET",
                    "path": "/products/{code}/factory-status",
                    "operationId": "get_product_factory_status",
                    "summary": "Status fabril",
                    "parametersSchema": [
                        {"name": "code"},
                        {"name": "reference_date"},
                        {"name": "date_start"},
                        {"name": "date_end"},
                    ],
                }
            ]
        )
    )

    with patch("app.domain.services.chat_date_range_intent_service.date") as mock_date:
        mock_date.today.return_value = date(2026, 6, 9)

        selected = service.select_action_for_product(
            "status fabril do 90263059 hoje",
            product_code="90263059",
            allowed_action_ids=["factory-status"],
            previous_messages=None,
        )

    assert selected is not None
    params = selected["arguments"]["parameters"]
    assert params["reference_date"] == "09-06-2026"
    assert params["date_start"] == "09-06-2026"
