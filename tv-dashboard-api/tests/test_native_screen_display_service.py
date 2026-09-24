from tv_app.application.services.data.native_screen_display_service import (
    apply_native_screen_display,
)


def test_oee_native_screen_display_uses_display_format_service():
    payload = {
        "oeePct": 82.5,
        "targetPct": 85,
        "seriesPoints": [{"label": "2024-01-05", "value": 80.0}],
    }
    out = apply_native_screen_display(payload, "production_oee_overview")
    assert out["serverDisplayApplied"] is True
    assert out["oeePctDisplay"] == "82,5%"
    assert out["targetPctDisplay"] == "85,0%"
    assert out["seriesPoints"][0]["displayValue"] == "80,00"
    assert out["seriesPoints"][0]["displayLabel"] == "2024-01-05"


def test_custom_message_passthrough():
    payload = {"headline": "Hi", "blocks": []}
    assert apply_native_screen_display(payload, "custom_message") is payload


def test_error_payload_passthrough():
    payload = {"error": True, "message": "x"}
    assert apply_native_screen_display(payload, "production_oee_overview") is payload
