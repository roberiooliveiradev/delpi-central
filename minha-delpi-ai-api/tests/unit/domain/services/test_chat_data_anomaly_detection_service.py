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


def test_attention_lines_humanize_field_labels_in_portuguese():
    anomalies = [
        {
            "type": "zero_value",
            "field": "current_quantity",
            "scope": "linha 1",
            "impact": "valor zerado pode exigir validação operacional",
            "value": 0,
        },
        {
            "type": "zero_value",
            "field": "available_quantity",
            "scope": "linha 1",
            "impact": "valor zerado pode exigir validação operacional",
            "value": 0,
        },
    ]
    metadata = {
        "path": "/products/10090016/stock",
        "apiDelpiResponseMeta": {
            "fields": {
                "current_quantity": "Quantidade atual no armazém",
                "available_quantity": "Saldo disponível (atual - empenhado - reservado)",
            }
        },
        "tablePresentation": {
            "columns": [
                {"key": "current_quantity", "label": "Qtd. atual"},
                {"key": "available_quantity", "label": "Qtd. disponível"},
            ]
        },
    }

    lines = ChatDataAnomalyDetectionService.attention_lines(
        anomalies,
        metadata=metadata,
    )

    assert lines
    joined = "\n".join(lines)
    assert "current_quantity" not in joined
    assert "available_quantity" not in joined
    assert "Quantidade atual no armazém" in joined or "Qtd. atual" in joined
    assert "Saldo disponível" in joined or "Qtd. disponível" in joined


def test_attention_lines_uses_llm_discovery_for_unknown_field(monkeypatch):
    from app.domain.services.presentation_column_label_discovery_service import (
        PresentationColumnLabelDiscoveryService,
    )

    def fake_resolve(keys, **kwargs):
        return {str(key): f"Rótulo LLM {key}" for key in keys}

    monkeypatch.setattr(
        PresentationColumnLabelDiscoveryService,
        "resolve_labels",
        classmethod(lambda cls, keys, **kwargs: fake_resolve(keys, **kwargs)),
    )

    anomalies = [
        {
            "type": "zero_value",
            "field": "weird_xyz_metric",
            "scope": "linha 1",
            "value": 0,
        }
    ]

    lines = ChatDataAnomalyDetectionService.attention_lines(
        anomalies,
        metadata={"path": "/x"},
    )

    assert lines
    joined = "\n".join(lines)
    assert "Rótulo LLM weird_xyz_metric" in joined
    assert "**weird_xyz_metric**" not in joined


def test_detect_caps_zero_value_anomalies_but_keeps_signal():
    rows = [
        {
            "available_quantity": 0,
            "current_quantity": 0,
            "quantity": 0,
            "balance": 0,
            "total": 0,
        },
        {
            "available_quantity": 0,
            "current_quantity": 0,
            "quantity": 0,
        },
    ]

    anomalies = ChatDataAnomalyDetectionService.detect(rows=rows)
    zero_values = [item for item in anomalies if item.get("type") == "zero_value"]

    assert zero_values
    assert len(zero_values) <= 3
    assert any(item.get("type") == "zero_value" for item in anomalies)


def test_detect_does_not_cap_negative_value_with_zero_cap():
    rows = [
        {"available_quantity": -1, "current_quantity": 0, "quantity": 0, "balance": 0},
        {"available_quantity": -2, "current_quantity": 0},
    ]

    anomalies = ChatDataAnomalyDetectionService.detect(rows=rows)
    negatives = [item for item in anomalies if item.get("type") == "negative_value"]
    zeros = [item for item in anomalies if item.get("type") == "zero_value"]

    assert len(negatives) >= 2
    assert len(zeros) <= 3


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
