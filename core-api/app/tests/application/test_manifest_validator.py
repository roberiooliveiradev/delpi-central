# app/tests/application/test_manifest_validator.py

from app.application.validators.manifest_validator import ManifestValidator


def minimal_valid_manifest():
    return {
        "schemaVersion": "1.0.0",
        "id": "crm",
        "name": "CRM Plugin",
        "version": "1.0.0",
        "type": "microfrontend",
        "basePath": "/crm",
        "entry": "http://localhost:3000/remoteEntry.js",
        "permissions": [
            {
                "code": "crm.access",
                "name": "Access CRM",
                "module": "crm"
            }
        ],
        "routes": [
            {
                "path": "/crm",
                "label": "CRM",
                "permission": "crm.access"
            }
        ]
    }


def test_schema_validation_fails_on_missing_required():
    validator = ManifestValidator()
    result = validator.validate({})  # vazio

    assert not result.is_valid
    assert any(e.code == "schema_validation_error" for e in result.errors)


def test_business_rule_error_detected():
    validator = ManifestValidator()

    m = minimal_valid_manifest()
    m["id"] = "INVALID ID"  # quebra regra de pattern

    result = validator.validate(m)

    assert not result.is_valid
    # Pode vir como schema_validation_error ou invalid_plugin_id dependendo da ordem
    assert any(
        e.code in ["invalid_plugin_id", "schema_validation_error"]
        for e in result.errors
    )


def test_valid_manifest_passes():
    validator = ManifestValidator()

    result = validator.validate(minimal_valid_manifest())

    assert result.is_valid is True
    assert result.errors == []