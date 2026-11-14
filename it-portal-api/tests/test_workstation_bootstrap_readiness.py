"""G2-S4-S2b: regressao negativa, sem Keycloak, rede ou agente real."""
from __future__ import annotations

from pathlib import Path

import pytest

from it_portal_app.domain.workstation_bootstrap_readiness import FILES, ROUTES, FLAGS, evaluate


def sandbox(tmp_path: Path) -> Path:
    contents = {
        "compose": "\n".join(
            f"      {key}: ${{{key}:-false}}" for key in FLAGS
        ),
        "keycloak": "\n".join((
            '"enabled": False', '"publicClient": False',
            '"fullScopeAllowed": False', '"defaultClientScopes": []',
            '"optionalClientScopes": []',
            'observed.get("enabled") is not False',
        )),
        "identity": "\n".join((
            '"credentials_issued": False', '"remote_access_enabled": False',
            'self.store.request_revocation(', 'self.provisioner.disable_client(',
        )),
        "migration": "ADD COLUMN ingest_authorized BOOLEAN NOT NULL DEFAULT FALSE,",
        "installer": "\n".join((
            'if (-not $Activate) { return }', 'New-ScheduledTaskSettingsSet -Disable',
            '-LogonType Interactive', 'ConvertFrom-SecureString',
        )),
    }
    for key, relative in FILES.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents[key], encoding="utf-8")
    routes = tmp_path / ROUTES
    routes.mkdir(parents=True)
    (routes / "workstation_identities_routes.py").write_text(
        '@router.post("/{workstation_id}/agent-identity/revoke")\n', encoding="utf-8"
    )
    return tmp_path


def test_safe_sandbox_is_explicitly_blocked(tmp_path):
    result = evaluate(sandbox(tmp_path))
    assert result.ci_pass is True
    assert result.status == "BLOCKED"
    assert result.bootstrap_authorized is False


@pytest.mark.parametrize("scenario", (
    "ingest_enabled", "missing_flag", "duplicate_flag", "bootstrap_flag",
    "keycloak_enabled", "keycloak_scope", "keycloak_no_readback",
    "v013_default_true", "identity_credentials", "revocation_reordered",
    "installer_mutates_by_default", "installer_schedules_enabled",
    "new_bootstrap_file", "new_activate_route", "missing_file",
))
def test_preflight_fails_closed(tmp_path, scenario):
    root = sandbox(tmp_path)
    def patch(name, original, replacement):
        path = root / FILES[name]
        content = path.read_text(encoding="utf-8")
        assert original in content
        path.write_text(content.replace(original, replacement), encoding="utf-8")
    if scenario == "ingest_enabled":
        patch("compose", ":-false}", ":-true}")
    elif scenario == "missing_flag":
        patch("compose", f"      {FLAGS[0]}: ${{{FLAGS[0]}:-false}}", "")
    elif scenario == "duplicate_flag":
        path = root / FILES["compose"]
        path.write_text(path.read_text() + "\n      " + f"{FLAGS[0]}: ${{{FLAGS[0]}:-false}}")
    elif scenario == "bootstrap_flag":
        path = root / FILES["compose"]
        path.write_text(path.read_text() + "\n      IT_PORTAL_WORKSTATION_BOOTSTRAP_ENABLED: true")
    elif scenario == "keycloak_enabled":
        patch("keycloak", '"enabled": False', '"enabled": True')
    elif scenario == "keycloak_scope":
        patch("keycloak", '"fullScopeAllowed": False', '"fullScopeAllowed": True')
    elif scenario == "keycloak_no_readback":
        patch("keycloak", 'observed.get("enabled") is not False', 'pass')
    elif scenario == "v013_default_true":
        patch("migration", "DEFAULT FALSE", "DEFAULT TRUE")
    elif scenario == "identity_credentials":
        patch("identity", '"credentials_issued": False', '"credentials_issued": True')
    elif scenario == "revocation_reordered":
        patch("identity", "self.store.request_revocation(\nself.provisioner.disable_client(",
              "self.provisioner.disable_client(\nself.store.request_revocation(")
    elif scenario == "installer_mutates_by_default":
        patch("installer", "if (-not $Activate) { return }", "if ($Activate) { return }")
    elif scenario == "installer_schedules_enabled":
        patch("installer", "New-ScheduledTaskSettingsSet -Disable", "New-ScheduledTaskSettingsSet")
    elif scenario == "new_bootstrap_file":
        (root / ROUTES / "workstation_bootstrap_routes.py").write_text("router = object()")
    elif scenario == "new_activate_route":
        (root / ROUTES / "workstation_identities_routes.py").write_text(
            '@router.post("/{workstation_id}/activate")\n')
    elif scenario == "missing_file":
        (root / FILES["keycloak"]).unlink()
    result = evaluate(root)
    assert result.status == "INVALID", scenario
    assert result.errors
    assert result.ci_pass is False
    assert result.bootstrap_authorized is False
