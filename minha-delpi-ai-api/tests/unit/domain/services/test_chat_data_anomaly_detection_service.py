from app.domain.services.chat_data_anomaly_detection_service import (
    ChatDataAnomalyDetectionService,
)
from app.domain.services.chat_data_insight_service import ChatDataInsightService


def test_detect_parses_brazilian_decimal_strings():
    rows = [
        {
            "reported_quantity": "174,04",
            "order_quantity": "200",
        }
    ]

    anomalies = ChatDataAnomalyDetectionService.detect(rows=rows)

    assert isinstance(anomalies, list)


def test_build_insight_does_not_fail_with_formatted_table_rows():
    metadata = {
        "path": "/products/90262404/factory-status",
        "stackPresentationPlan": {"presentationProfileKey": "factory_status"},
        "tablePresentations": [
            {
                "type": "table",
                "title": "Apontamentos",
                "rows": [
                    {
                        "reported_quantity": "174,04",
                        "order_quantity": "200,00",
                    }
                ],
            }
        ],
    }
    data = {
        "factory_status": "PA PRODUZIDO / AGUARDANDO INSPEÇÃO FINAL",
        "structure": {"summary": {"total_raw_materials": 1}},
        "production": {"summary": {"total_pa_orders": 1, "pa_production_started": True}},
        "shipping": {"summary": {"total_shipped_quantity": 0}},
        "raw_material_stock": {"items": [], "summary": {}},
    }

    data_answer = ChatDataInsightService.build(metadata, data)

    assert isinstance(data_answer, dict)
    assert data_answer.get("summary", {}).get("answer")
