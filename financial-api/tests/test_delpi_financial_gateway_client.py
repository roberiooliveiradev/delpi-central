from importlib import reload

from financial_app.infrastructure.gateways.delpi_financial_gateway import DelpiFinancialGateway


def test_settings_default_delpi_timeout_is_ninety(monkeypatch) -> None:
    monkeypatch.delenv("FINANCIAL_DELPI_API_TIMEOUT", raising=False)
    monkeypatch.delenv("DELPI_API_TIMEOUT", raising=False)
    import financial_app.config as config_module

    reload(config_module)
    assert config_module.Settings.DELPI_API_TIMEOUT == 90.0


def test_settings_prefers_financial_timeout_env(monkeypatch) -> None:
    monkeypatch.setenv("FINANCIAL_DELPI_API_TIMEOUT", "120")
    monkeypatch.setenv("DELPI_API_TIMEOUT", "30")
    import financial_app.config as config_module

    reload(config_module)
    assert config_module.Settings.DELPI_API_TIMEOUT == 120.0


def test_gateway_reuses_httpx_client() -> None:
    gateway = DelpiFinancialGateway(base_url="http://example.test", timeout=5)
    first = gateway._http()
    second = gateway._http()
    assert first is second
    gateway.close()
    assert gateway._client is None
