"""G0-SEC: preflight negativo; suites verdes NAO significam acesso aprovado."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from it_portal_app.domain.remote_security_readiness import (
    REGISTRY_PATH, REQUIRED_CHECKS, evaluate,
)

REPO = Path(__file__).resolve().parents[2]


def base_registry():
    return {
        "schema_version": 1,
        "scope": "delpi-remote",
        "checkpoints": [
            {"id": name, "state": "pending", "public_reference": None}
            for name in REQUIRED_CHECKS
        ],
    }


def sandbox_repo(tmp_path):
    paths = {
        "it-portal-api/it_portal_app/main.py": "app.include_router(workstations_router)\n",
        "infra/docker-compose.yml": "services:\n  it-portal-api:\n    image: test\n",
        "plugins/it-portal/it-portal.manifest.json": json.dumps({
            "permissions": [{"code": "it-portal.computers.view"}]
        }),
        "it-portal-api/it_portal_app/interface/http/routes/workstations_routes.py": "router = object()\n",
    }
    for rel, value in paths.items():
        full = tmp_path / rel
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(value, encoding="utf-8")
    return tmp_path


def test_current_repository_gate_is_blocked_not_approved():
    manifest = json.loads((REPO / REGISTRY_PATH).read_text(encoding="utf-8"))
    result = evaluate(REPO, manifest)
    assert result.status == "BLOCKED", result.errors
    assert result.safe_to_continue_offline is True
    assert result.remote_access_authorized is False
    assert len(result.pending) + len(result.documented) == len(REQUIRED_CHECKS)


def test_valid_manifest_does_not_authorize_even_if_all_documented(tmp_path):
    root = sandbox_repo(tmp_path)
    manifest = base_registry()
    for row in manifest["checkpoints"]:
        row["state"] = "documented"
        row["public_reference"] = "https://example.org/review"
    result = evaluate(root, manifest)
    assert result.status == "BLOCKED"
    assert result.safe_to_continue_offline
    assert not result.remote_access_authorized
    assert len(result.documented) == len(REQUIRED_CHECKS)


@pytest.mark.parametrize("change", ["missing", "duplicate", "unknown", "unreviewed", "unexpected_secret"])
def test_invalid_registry_fails_closed(tmp_path, change):
    root = sandbox_repo(tmp_path)
    registry = base_registry()
    rows = registry["checkpoints"]
    if change == "missing":
        rows.pop()
    elif change == "duplicate":
        rows[0] = copy.deepcopy(rows[1])
    elif change == "unknown":
        rows[0]["id"] = "bypass_security"
    elif change == "unreviewed":
        rows[0]["state"] = "approved"  # approvacao nao pode ser declarada no GitHub publico
    elif change == "unexpected_secret":
        rows[0]["secret"] = "password"
    result = evaluate(root, registry)
    assert result.status == "INVALID"
    assert not result.safe_to_continue_offline
    assert not result.remote_access_authorized


@pytest.mark.parametrize("scenario", ["remote_router", "meshcentral_compose", "remote_permission", "remote_flag", "remote_file"])
def test_cannot_introduce_active_remote_surface_before_approval(tmp_path, scenario):
    root = sandbox_repo(tmp_path)
    if scenario == "remote_router":
        p = root / "it-portal-api/it_portal_app/main.py"
        p.write_text(p.read_text() + "app.include_router(remote_router)\n", encoding="utf-8")
    elif scenario == "meshcentral_compose":
        p = root / "infra/docker-compose.yml"
        p.write_text(p.read_text() + "  meshcentral:\n    image: example\n", encoding="utf-8")
    elif scenario == "remote_permission":
        p = root / "plugins/it-portal/it-portal.manifest.json"
        p.write_text(json.dumps({"permissions": [{"code": "it-portal.remote.connect"}]}), encoding="utf-8")
    elif scenario == "remote_flag":
        p = root / "infra/docker-compose.yml"
        p.write_text(p.read_text() + "    environment:\n      IT_PORTAL_REMOTE_ENABLED: true\n", encoding="utf-8")
    else:
        p = root / "it-portal-api/it_portal_app/interface/http/routes/remote_sessions_routes.py"
        p.write_text("router = object()\n", encoding="utf-8")
    result = evaluate(root, base_registry())
    assert result.status == "INVALID"
    assert result.errors
    assert not result.safe_to_continue_offline


def test_documented_gate_must_have_public_evidence(tmp_path):
    root = sandbox_repo(tmp_path)
    manifest = base_registry()
    manifest["checkpoints"][0]["state"] = "documented"
    invalid = evaluate(root, manifest)
    assert invalid.status == "INVALID"
    manifest["checkpoints"][0]["public_reference"] = "https://example.org/security-review"
    valid = evaluate(root, manifest)
    assert valid.status == "BLOCKED"
    assert len(valid.documented) == 1
