from tv_app.application.services.tv_dashboard_content_service import ui_content_bundle
from tv_app.interface.http.routes.content_routes import ui_content


def test_ui_content_bundle_has_admin_keys():
    bundle = ui_content_bundle()
    assert "admin" in bundle
    assert bundle["admin"].get("addSlideTitle")


def test_ui_content_route_returns_envelope():
    class FakeRequest:
        state = type("S", (), {"user": type("U", (), {"is_superadmin": True, "permissions": []})()})()

    response = ui_content(FakeRequest())
    body = response.body.decode("utf-8")
    assert '"success":true' in body.replace(" ", "")
    assert "addSlideTitle" in body
