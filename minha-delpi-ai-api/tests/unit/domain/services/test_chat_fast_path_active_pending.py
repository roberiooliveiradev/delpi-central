from datetime import date
from unittest.mock import patch

from app.domain.services.chat_fast_path_service import ChatFastPathService


def test_fast_path_disabled_when_resolving_missing_date_pending():
    history = [
        {
            "role": "assistant",
            "metadata": {
                "activePending": {
                    "kind": "missing_date",
                    "context": {
                        "originalMessage": "status fabril do produto 90269002",
                        "productCode": "90269002",
                        "subIntent": "factory_status",
                    },
                }
            },
        }
    ]

    with patch("app.domain.services.chat_date_range_intent_service.date") as mock_date:
        mock_date.today.return_value = date(2026, 6, 9)

        assert not ChatFastPathService.should_use(
            "hoje",
            enabled=True,
            max_chars=30,
            previous_messages=history,
        )


def test_fast_path_disabled_when_continuing_missing_product_code_session():
    history = [
        {
            "role": "assistant",
            "metadata": {
                "activePending": {
                    "kind": "missing_product_code",
                    "expectedParam": "productCode",
                    "context": {
                        "originalMessage": "análise de preço MP",
                        "subIntent": "raw_material_price_intelligence",
                    },
                }
            },
        }
    ]

    assert not ChatFastPathService.should_use(
        "10080001",
        enabled=True,
        max_chars=30,
        previous_messages=history,
    )
