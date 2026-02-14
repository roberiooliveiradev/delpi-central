# app/domain/services/plugin_manifest_validator.py

import re
from jsonschema import validate
from jsonschema.exceptions import ValidationError

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
ID_RE = re.compile(r"^[a-z0-9\-]+$")  # lowercase, hífen ok

MANIFEST_SCHEMA_V2 = {
    "type": "object",
    "required": ["schemaVersion", "id", "name", "version", "type", "basePath", "permissions", "routes"],
    "properties": {
        "schemaVersion": {"type": "string"},
        "id": {"type": "string"},
        "name": {"type": "string"},
        "description": {"type": ["string", "null"]},
        "version": {"type": "string"},
        "category": {"type": ["string", "null"]},
        "icon": {"type": ["string", "null"]},
        "type": {"type": "string", "enum": ["microfrontend", "iframe", "backend-only"]},
        "basePath": {"type": "string"},
        "entry": {"type": ["string", "null"]},
        "healthcheck": {"type": ["string", "null"]},
        "dependencies": {"type": "array", "items": {"type": "string"}},
        "permissions": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["code", "description", "module"],
                "properties": {
                    "code": {"type": "string"},
                    "description": {"type": "string"},
                    "module": {"type": "string"}
                }
            }
        },
        "routes": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["path", "label", "permission"],
                "properties": {
                    "path": {"type": "string"},
                    "label": {"type": "string"},
                    "icon": {"type": ["string", "null"]},
                    "permission": {"type": "string"},
                    "showInMenu": {"type": ["boolean", "null"]},
                    "order": {"type": ["integer", "null"]},
                    "menuGroup": {"type": ["string", "null"]}
                }
            }
        }
    },
    "additionalProperties": True
}


class ManifestValidationError(Exception):
    pass


def validate_manifest_v2(manifest: dict) -> None:
    try:
        validate(instance=manifest, schema=MANIFEST_SCHEMA_V2)
    except ValidationError as e:
        raise ManifestValidationError(f"Schema inválido: {e.message}")

    if manifest.get("schemaVersion") != "2.0.0":
        raise ManifestValidationError("schemaVersion deve ser '2.0.0'")

    plugin_id = manifest["id"]
    if not ID_RE.match(plugin_id):
        raise ManifestValidationError("id inválido. Use lowercase, números e hífen (sem espaços).")

    version = manifest["version"]
    if not SEMVER_RE.match(version):
        raise ManifestValidationError("version inválida. Use SemVer: MAJOR.MINOR.PATCH")

    base_path = manifest["basePath"]
    if not base_path.startswith("/"):
        raise ManifestValidationError("basePath deve iniciar com '/'")

    # rotas devem iniciar com basePath
    for r in manifest["routes"]:
        if not r["path"].startswith(base_path):
            raise ManifestValidationError(f"Rota '{r['path']}' deve iniciar com basePath '{base_path}'")

    # permissions code pattern mínimo
    for p in manifest["permissions"]:
        if "." not in p["code"]:
            raise ManifestValidationError(f"permission code '{p['code']}' inválido (use module.resource.action)")
