import json
from pathlib import Path

from app.application.plugins.manifest_validator import ManifestValidator


def load_fixture(name: str):
    path = Path(__file__).parent.parent / "fixtures" / name
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_valid_manifest_should_pass():
    validator = ManifestValidator()

    manifest = load_fixture("valid_manifest.json")

    result = validator.validate(manifest)

    assert result.is_valid is True
    assert result.errors == []

def test_invalid_semver_should_fail():
    validator = ManifestValidator()

    manifest = load_fixture("invalid_manifest_semver.json")

    result = validator.validate(manifest)

    assert result.is_valid is False
    assert any(e.code == "invalid_version" for e in result.errors)

def test_route_outside_basepath_should_fail():
    validator = ManifestValidator()

    manifest = {
        "schemaVersion": "2.0.0",
        "id": "crm",
        "name": "CRM",
        "version": "1.0.0",
        "type": "microfrontend",
        "basePath": "/crm",
        "entry": "/apps/crm/remoteEntry.js",
        "permissions": [
            {"code": "crm.access", "description": "x", "module": "crm"}
        ],
        "routes": [
            {"path": "/gpt", "label": "x", "permission": "crm.access"}
        ]
    }

    result = validator.validate(manifest)

    assert result.is_valid is False
    assert any(e.code == "route_outside_base_path" for e in result.errors)