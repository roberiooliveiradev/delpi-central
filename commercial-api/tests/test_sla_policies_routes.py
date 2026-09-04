from pathlib import Path


ROUTES = (
    Path(__file__).resolve().parents[1]
    / "commercial_app"
    / "interface"
    / "http"
    / "routes"
    / "settings_routes.py"
).read_text(encoding="utf-8")


def test_sla_settings_operation_ids() -> None:
    assert 'operation_id="list_sla_policies"' in ROUTES
    assert 'operation_id="create_sla_policy"' in ROUTES
    assert 'operation_id="update_sla_policy"' in ROUTES
    assert 'operation_id="deactivate_sla_policy"' in ROUTES


def test_sla_settings_paths() -> None:
    assert '"/sla-policies"' in ROUTES
    assert '"/sla-policies/{policy_id}"' in ROUTES
    assert "@router.post" in ROUTES
    assert "@router.patch" in ROUTES
    assert "@router.delete" in ROUTES


def test_sla_mutations_require_manage() -> None:
    assert "COMMERCIAL_MANAGE_PERMISSIONS" in ROUTES
    assert ROUTES.count("@require_any_permission(*COMMERCIAL_MANAGE_PERMISSIONS)") == 3


def test_sla_list_supports_include_inactive() -> None:
    assert "include_inactive" in ROUTES
    assert "has_manage" in ROUTES
