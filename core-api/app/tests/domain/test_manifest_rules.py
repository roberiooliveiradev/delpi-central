# app/tests/domain/test_manifest_rules.py

from app.domain.plugins.manifest_rules import validate_manifest_rules


def base_manifest():
    return {
        "id": "crm",
        "version": "1.0.0",
        "basePath": "/crm",
        "type": "microfrontend",
        "permissions": [
            {"code": "crm.leads.read", "module": "crm", "name": "Read leads"}
        ],
        "routes": [
            {"path": "/crm/leads", "permission": "crm.leads.read"}
        ],
    }


def test_valid_manifest_has_no_errors():
    errors = validate_manifest_rules(base_manifest())
    assert errors == []


def test_invalid_plugin_id():
    m = base_manifest()
    m["id"] = "CRM INVALID"
    errors = validate_manifest_rules(m)

    assert any(e.code == "invalid_plugin_id" for e in errors)


def test_invalid_version():
    m = base_manifest()
    m["version"] = "1.0"
    errors = validate_manifest_rules(m)

    assert any(e.code == "invalid_version" for e in errors)


def test_duplicate_permission_code():
    m = base_manifest()
    m["permissions"].append(
        {"code": "crm.leads.read", "module": "crm", "name": "Duplicate"}
    )

    errors = validate_manifest_rules(m)
    assert any(e.code == "duplicate_permission_code_in_manifest" for e in errors)


def test_permission_module_mismatch():
    m = base_manifest()
    m["permissions"][0]["module"] = "wrong"

    errors = validate_manifest_rules(m)
    assert any(e.code == "permission_module_mismatch" for e in errors)


def test_route_outside_base_path():
    m = base_manifest()
    m["routes"][0]["path"] = "/other/path"

    errors = validate_manifest_rules(m)
    assert any(e.code == "route_outside_base_path" for e in errors)


def test_route_permission_not_declared():
    m = base_manifest()
    m["routes"][0]["permission"] = "crm.unknown"

    errors = validate_manifest_rules(m)
    assert any(e.code == "route_permission_not_declared" for e in errors)


def test_backend_required_missing_fields():
    m = base_manifest()
    m["backend"] = {"required": True}

    errors = validate_manifest_rules(m)

    assert any(e.code == "backend_missing_issuer" for e in errors)
    assert any(e.code == "backend_missing_audience" for e in errors)


def test_backend_only_requires_access_permission():
    m = base_manifest()
    m["type"] = "backend-only"
    m["permissions"] = []  # remove access permission

    errors = validate_manifest_rules(m)
    assert any(e.code == "missing_access_permission" for e in errors)