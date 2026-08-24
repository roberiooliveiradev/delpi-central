from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_grounded_mp_stock_aggregation_service import (
    ChatGroundedMpStockAggregationService,
)
from app.domain.services.chat_operational_data_commentary_service import (
    ChatOperationalDataCommentaryService,
)
from app.domain.services.chat_data_insight_service import ChatDataInsightService

configure_domain_infrastructure_ports()


def _stock_tool_call(product_code: str, items: list[dict]) -> dict:
    return {
        "name": "execute_external_action",
        "metadata": {
            "ok": True,
            "path": f"/products/{product_code}/stock",
            "data": {"items": items, "total": len(items)},
        },
    }


def test_build_merged_commentary_for_mp_fan_out():
    tool_calls = [
        _stock_tool_call(
            "10080109",
            [
                {
                    "product_code": "10080109",
                    "branch": "01",
                    "available_quantity": 0,
                }
            ],
        ),
        _stock_tool_call(
            "10090014",
            [
                {
                    "product_code": "10090014",
                    "branch": "01",
                    "available_quantity": 120,
                }
            ],
        ),
    ]

    commentary = ChatGroundedMpStockAggregationService.build_merged_commentary(
        "estoque das matérias-primas",
        tool_calls,
    )

    assert commentary
    combined = "\n".join(commentary.get("highlights") or [])

    assert "2" in combined
    assert "ruptura" in combined.lower() or "zerado" in combined.lower()
    assert "10090014" in combined


def test_stock_commentary_highlights_mp_concentration():
    root = {
        "items": [
            {
                "product_code": "10080109",
                "branch": "01",
                "available_quantity": 0,
            },
            {
                "product_code": "10090014",
                "branch": "01",
                "available_quantity": 250,
            },
        ],
        "total": 2,
    }

    commentary = ChatOperationalDataCommentaryService.build("stock", root)

    assert commentary
    combined = "\n".join(commentary.get("highlights") or [])

    assert "10090014" in combined
    assert "2" in combined


def test_stock_profile_skips_row_zero_anomalies():
    metadata = {"path": "/products/10080109/stock"}
    data = {
        "items": [
            {"product_code": "10080109", "available_quantity": 0},
            {"product_code": "10090014", "available_quantity": 0},
        ]
    }

    answer = ChatDataInsightService.build(metadata, data)

    assert answer
    anomalies = (answer.get("anomalies") or []) if isinstance(answer, dict) else []

    assert not any(item.get("type") == "zero_value" for item in anomalies)
