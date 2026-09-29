from delpi_mes_app.config import settings


def test_default_configuration_is_internal_and_bounded():
    assert settings.API_ROOT_PATH == "/apps/delpi-mes-api"
    assert settings.PRODUCTION_CONTROL_API_URL.startswith("http://")
    assert settings.PRODUCTION_CONTROL_API_TIMEOUT > 0
