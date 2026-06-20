from app.application.services.chat_drawing_validation_assertiveness_metrics_service import (
    ChatDrawingValidationAssertivenessMetricsService,
)


def test_aggregate_flags_false_critical_above_baseline():
    rows = [
        {
            "code": "90263149",
            "validationStatus": "rejected",
            "criticalErrors": 2,
            "checklistItems": 10,
            "pendingItems": [],
        },
        {
            "code": "90264227",
            "validationStatus": "approved",
            "criticalErrors": 0,
            "checklistItems": 8,
            "pendingItems": [],
        },
    ]
    metrics = ChatDrawingValidationAssertivenessMetricsService.aggregate(rows)

    assert metrics["sampleCount"] == 2
    assert metrics["falseCriticalCount"] == 1
    assert metrics["falseCriticalRate"] == 0.5
    assert metrics["passesGate"] is False


def test_aggregate_passes_when_within_baseline():
    rows = [
        {
            "code": "90263149",
            "validationStatus": "approved_with_notes",
            "criticalErrors": 0,
            "checklistItems": 12,
            "pendingItems": [{"templateKey": "bom_quantity_pending"}],
        }
    ]
    metrics = ChatDrawingValidationAssertivenessMetricsService.aggregate(rows)

    assert metrics["passesGate"] is True
    assert metrics["samples"][0]["falseCritical"] is False


def test_evaluate_row_respects_allowed_statuses():
    baseline = {
        "maxFalseCriticalRate": 0.05,
        "samples": {
            "90263149": {
                "maxCriticalErrors": 0,
                "allowedStatuses": ["approved", "approved_with_notes"],
            }
        },
    }
    result = ChatDrawingValidationAssertivenessMetricsService.evaluate_row(
        {
            "code": "90263149",
            "validationStatus": "rejected",
            "criticalErrors": 0,
            "checklistItems": 5,
            "pendingItems": [],
        },
        baseline=baseline,
    )

    assert result["falseCritical"] is False
    assert result["statusOk"] is False
