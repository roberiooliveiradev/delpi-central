from app.interface.http.swagger_portal_bridge import build_swagger_portal_bridge_script


def test_swagger_bridge_includes_auth_theme_and_retry() -> None:
    script = build_swagger_portal_bridge_script(["http://localhost"])

    assert "DELPI_AUTH" in script
    assert "DELPI_THEME" in script
    assert "DELPI_AUTH_READY" in script
    assert "authActions.authorize" in script
    assert "normalizeBearerToken" in script
    assert 'headers.set("Authorization"' in script
    assert "data-delpi-theme" in script
    assert "--delpi-primary" in script
