"""Contrato estrutural das rotas S2S de person-profile."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_integrations_person_profiles_controller_registered() -> None:
    controller = (
        ROOT
        / "app"
        / "interfaces"
        / "http"
        / "integrations_person_profiles_controller.py"
    ).read_text(encoding="utf-8")
    create_app = (ROOT / "app" / "create_app.py").read_text(encoding="utf-8")

    assert 'url_prefix="/integrations/person-profiles"' in controller
    assert "@require_service_token()" in controller
    assert 'route("/<user_id>"' in controller
    assert 'route("/<user_id>/photo"' in controller
    assert 'route("/lookup"' in controller
    assert "integrations_person_profiles_bp" in create_app
    assert "register_blueprint(integrations_person_profiles_bp)" in create_app
