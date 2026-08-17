from app.domain.services.console_alert_content_service import ConsoleAlertContentService


def setup_function() -> None:
    ConsoleAlertContentService.clear_cache()


def test_console_alert_content_pool_saturation_keys() -> None:
    spec = ConsoleAlertContentService.alert_spec("pool_saturation")
    assert "messageTemplate" in spec
    assert "guidance" in spec
    assert "{occupancy_pct}" in str(spec["messageTemplate"])
    assert ConsoleAlertContentService.pool_saturation_pct_default() == 90.0

    message = ConsoleAlertContentService.format_alert_message(
        "pool_saturation",
        pool_name="plugins_postgres",
        occupancy_pct=95.0,
        threshold_pct=90.0,
    )
    assert "plugins_postgres" in message
    assert "95" in message
    assert "Cache" in ConsoleAlertContentService.alert_guidance("pool_saturation")


def test_console_alert_content_slo_targets() -> None:
    slo = ConsoleAlertContentService.slo_targets()
    assert slo["availability_pct"] == 99.0
    assert slo["p95_ms"] == 3000.0
    assert ConsoleAlertContentService.sli_label("availability_pct")
