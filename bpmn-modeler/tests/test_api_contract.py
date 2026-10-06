from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from bpmn_modeler.application.use_cases import BpmnModelerService
from bpmn_modeler.infrastructure.runtime import SystemClock, UuidGenerator
from bpmn_modeler.infrastructure.validation.blank import (
    TemplateBlankArtifactFactory,
)
from bpmn_modeler.infrastructure.validation.engine import LxmlBpmnValidator
from bpmn_modeler.interface.http.app import create_app

from . import fixtures as fx
from .conftest import InMemoryRepository

ALL_PERMS = ["bpmn-modeler.view", "bpmn-modeler.edit", "bpmn-modeler.manage"]

EXPECTED_OPERATION_IDS = {
    "health", "ready", "listModels", "createModel", "importModel",
    "inspectImport", "getModel", "renameModel", "duplicateModel",
    "archiveModel", "unarchiveModel", "getWorkingCopy", "saveWorkingCopy",
    "validateWorkingCopy", "exportWorkingCopy", "listRevisions",
    "createRevision", "getRevision", "restoreRevision", "exportRevision",
}


@pytest.fixture(scope="module")
def validator():
    return LxmlBpmnValidator()


@pytest.fixture()
def client(validator):
    service = BpmnModelerService(
        repository=InMemoryRepository(),
        validator=validator,
        input_safety=validator,
        blank_artifacts=TemplateBlankArtifactFactory(UuidGenerator()),
        clock=SystemClock(),
        ids=UuidGenerator(),
    )
    app = create_app(service)
    return TestClient(app, raise_server_exceptions=False)


def authed(permissions=ALL_PERMS, uid: str = "u1", superadmin: bool = False):
    rbac = {
        "id": uid, "email": "u@x.dev", "name": "U", "roles": [],
        "groups": [], "permissions": permissions,
        "is_superadmin": superadmin,
    }
    return (
        patch(
            "bpmn_modeler.interface.http.auth.validate_token",
            return_value={"sub": "u1", "email": "u@x.dev"},
        ),
        patch(
            "bpmn_modeler.interface.http.auth.load_user_rbac",
            new=AsyncMock(return_value=rbac),
        ),
    )


H = {"Authorization": "Bearer fake"}


def test_health_and_ready_public(client):
    assert client.get("/health").json() == {"status": "ok"}
    ready = client.get("/ready")
    assert ready.status_code in (200, 503)
    assert set(ready.json()["checks"]) == {"database", "xsd_bundle", "schema"}
    assert ready.json()["checks"]["xsd_bundle"] is True


def test_health_public_under_root_path(client):
    """Atrás do gateway com root_path, /health segue público (regressão:
    request.url.path inclui o prefixo e mascarava _is_public)."""
    app = client.app
    prefixed = TestClient(app, root_path="/apps/bpmn-modeler-api",
                          raise_server_exceptions=False)
    assert prefixed.get("/health").json() == {"status": "ok"}
    assert prefixed.get("/openapi.json").status_code == 200
    assert prefixed.get("/models").status_code == 401


def test_unauthenticated_401_envelope(client):
    resp = client.get("/models")
    assert resp.status_code == 401
    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "UNAUTHORIZED"
    assert resp.headers["x-request-id"]


def test_forbidden_without_permission(client):
    vt, rbac = authed(permissions=[])
    with vt, rbac:
        resp = client.get("/models", headers=H)
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "UNAUTHORIZED_OPERATION"


def test_openapi_contract(client):
    spec = client.get("/openapi.json").json()
    operation_ids = {
        op["operationId"]
        for path in spec["paths"].values()
        for op in path.values()
        if isinstance(op, dict) and "operationId" in op
    }
    assert operation_ids == EXPECTED_OPERATION_IDS
    assert spec["info"]["title"] == "BPMN Modeler API"
    assert spec["info"]["version"] == "1.0.0"
    assert spec["components"]["securitySchemes"]["bearerAuth"]["scheme"] == "bearer"
    assert spec["paths"]["/health"]["get"]["security"] == []
    assert spec["paths"]["/models"]["get"]["x-required-permission"] == "bpmn-modeler.view"
    assert spec["paths"]["/models"]["post"]["x-required-permission"] == "bpmn-modeler.edit"
    assert spec["servers"] == [{"url": "/apps/bpmn-modeler-api"}]


def test_full_model_lifecycle_contract(client):
    vt, rbac = authed()
    with vt, rbac:
        # create
        resp = client.post("/models", json={"display_name": "Proc A"}, headers=H)
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["changed"] and data["version"] == 1
        assert resp.headers["etag"] == '"v1"'
        model_id = data["model_id"]

        # get metadata + etag
        resp = client.get(f"/models/{model_id}", headers=H)
        assert resp.status_code == 200
        assert resp.headers["etag"] == '"v1"'
        assert "x-artifact-sha256" in resp.headers

        # working copy raw xml
        resp = client.get(f"/models/{model_id}/working-copy", headers=H)
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("application/xml")
        assert "bpmn:definitions" in resp.text
        assert resp.headers["cache-control"] == "no-store"
        xml = resp.text

        # save identical -> no-op
        resp = client.put(
            f"/models/{model_id}/working-copy",
            content=xml.encode(),
            headers={**H, "Content-Type": "application/xml", "If-Match": '"v1"'},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["changed"] is False

        # precondition: missing If-Match -> 428
        resp = client.put(
            f"/models/{model_id}/working-copy",
            content=xml.encode(),
            headers={**H, "Content-Type": "application/xml"},
        )
        assert resp.status_code == 428
        assert resp.json()["error"]["code"] == "PRECONDITION_REQUIRED"

        # malformed If-Match -> 400
        resp = client.put(
            f"/models/{model_id}/working-copy",
            content=xml.encode(),
            headers={**H, "Content-Type": "application/xml", "If-Match": "*"},
        )
        assert resp.status_code == 400

        # wrong content type -> 415
        resp = client.put(
            f"/models/{model_id}/working-copy",
            json={},
            headers={**H, "If-Match": '"v1"'},
        )
        assert resp.status_code == 400  # INVALID_REQUEST per transport matrix

        # save edited -> v2
        edited = xml.replace("<bpmn:process", '<bpmn:process name="n"')
        resp = client.put(
            f"/models/{model_id}/working-copy",
            content=edited.encode(),
            headers={**H, "Content-Type": "application/xml", "If-Match": '"v1"'},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["version"] == 2
        assert resp.headers["etag"] == '"v2"'

        # stale If-Match -> 412 CONFLICT
        resp = client.put(
            f"/models/{model_id}/working-copy",
            content=edited.encode(),
            headers={**H, "Content-Type": "application/xml", "If-Match": '"v1"'},
        )
        assert resp.status_code == 412
        assert resp.json()["error"]["code"] == "CONFLICT"

        # revision lifecycle
        resp = client.post(
            f"/models/{model_id}/revisions", headers={**H, "If-Match": '"v2"'}
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["revision_number"] == 1

        resp = client.post(
            f"/models/{model_id}/revisions", headers={**H, "If-Match": '"v3"'}
        )
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "NO_CHANGES"

        resp = client.get(f"/models/{model_id}/revisions", headers=H)
        assert resp.status_code == 200
        assert resp.json()["data"]["items"][0]["revision_number"] == 1

        resp = client.get(f"/models/{model_id}/revisions/1/export", headers=H)
        assert resp.status_code == 200
        assert "attachment" in resp.headers["content-disposition"]
        assert resp.headers["x-content-type-options"] == "nosniff"
        assert b"process name" in resp.content.replace(b"bpmn:process", b"process")

        # validate candidate endpoint (zero write)
        resp = client.post(
            f"/models/{model_id}/working-copy/validate",
            content=fx.FX_REF_001.encode(),
            headers={**H, "Content-Type": "application/xml"},
        )
        assert resp.status_code == 200
        issues = resp.json()["data"]["issues"]
        assert any(i["rule_id"] == "BPMN-STRUCT-010" for i in issues)

        # archive -> mutations blocked
        resp = client.post(
            f"/models/{model_id}/archive", headers={**H, "If-Match": '"v3"'}
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["version"] == 4
        resp = client.patch(
            f"/models/{model_id}",
            json={"display_name": "x"},
            headers={**H, "If-Match": '"v4"'},
        )
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "MODEL_ARCHIVED"

        resp = client.post(
            f"/models/{model_id}/unarchive", headers={**H, "If-Match": '"v4"'}
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["version"] == 5


def test_import_flow(client):
    vt, rbac = authed()
    with vt, rbac:
        resp = client.post(
            "/imports/inspect",
            files={"file": ("a.bpmn", fx.FX_VALID_001.encode(), "text/xml")},
            headers=H,
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["recognition_state"] == "BPMN_RECOGNIZED"
        assert data["eligible_to_import"] is True

        resp = client.post(
            "/imports/inspect",
            files={"file": ("x.bpmn", fx.FX_SEC_001.encode(), "text/xml")},
            headers=H,
        )
        assert resp.json()["data"]["recognition_state"] == "INPUT_REJECTED_SECURITY"

        resp = client.post(
            "/models/import",
            files={"file": ("a.bpmn", fx.FX_VALID_001.encode(), "text/xml")},
            data={"display_name": "Imported"},
            headers=H,
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["version"] == 1

        resp = client.post(
            "/models/import",
            files={"file": ("x.bpmn", fx.FX_BADXML_001.encode(), "text/xml")},
            data={"display_name": "Bad"},
            headers=H,
        )
        assert resp.status_code == 422
        body = resp.json()
        assert body["error"]["code"] == "VALIDATION_BLOCKED"
        assert body["error"]["details"]["recognition_state"] == "MALFORMED_XML"
        assert "validation_report" in body["error"]["details"]


def test_pagination_contract(client):
    vt, rbac = authed()
    with vt, rbac:
        for i in range(3):
            client.post("/models", json={"display_name": f"M{i}"}, headers=H)
        resp = client.get("/models?page=1&page_size=2", headers=H)
        data = resp.json()["data"]
        assert len(data["items"]) == 2 and data["has_more"] is True
        resp = client.get("/models?page_size=0", headers=H)
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "INVALID_REQUEST"


def test_not_found_envelope(client):
    import uuid

    vt, rbac = authed()
    with vt, rbac:
        resp = client.get(f"/models/{uuid.uuid4()}", headers=H)
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "MODEL_NOT_FOUND"


def test_ownership_isolation_http(client):
    """Foreign model_id is indistinguishable from nonexistent: same 404
    envelope, no existence/owner disclosure. List is owner-scoped."""
    import uuid

    alice_vt, alice_rbac = authed(uid="alice")
    with alice_vt, alice_rbac:
        model_id = client.post(
            "/models", json={"display_name": "Alice Only"}, headers=H
        ).json()["data"]["model_id"]

    bob_vt, bob_rbac = authed(uid="bob")
    with bob_vt, bob_rbac:
        resp = client.get(f"/models/{model_id}", headers=H)
        assert resp.status_code == 404
        foreign_body = resp.json()
        assert foreign_body["error"]["code"] == "MODEL_NOT_FOUND"
        assert model_id not in str(foreign_body)
        assert "alice" not in str(foreign_body).lower()

        missing = client.get(f"/models/{uuid.uuid4()}", headers=H)
        assert missing.status_code == 404
        assert missing.json()["error"]["code"] == foreign_body["error"]["code"]
        assert missing.json()["message"] == foreign_body["message"]
        assert missing.json()["error"]["details"] == foreign_body["error"]["details"]

        # reads + writes scoped: todas viram MODEL_NOT_FOUND para estranho
        assert client.get(
            f"/models/{model_id}/working-copy", headers=H
        ).status_code == 404
        assert client.get(
            f"/models/{model_id}/revisions", headers=H
        ).status_code == 404
        assert client.put(
            f"/models/{model_id}/working-copy",
            content=b"<x/>",
            headers={
                **H,
                "If-Match": '"v1"',
                "Content-Type": "application/xml",
            },
        ).status_code == 404
        export_resp = client.get(
            f"/models/{model_id}/working-copy/export", headers=H
        )
        assert export_resp.status_code == 404
        # export negado não pode vazar XML nem filename do recurso foreign
        assert "xml" not in export_resp.headers.get("content-type", "")
        assert "Alice" not in export_resp.text
        assert "content-disposition" not in export_resp.headers
        assert client.post(
            f"/models/{model_id}/working-copy/validate",
            content=b"<x/>",
            headers={**H, "Content-Type": "application/xml"},
        ).status_code == 404
        assert client.put(
            f"/models/{model_id}/working-copy",
            content=b"<x/>",
            headers={
                **H,
                "If-Match": '"v1"',
                "Content-Type": "application/xml",
            },
        ).status_code == 404
        assert client.patch(
            f"/models/{model_id}",
            json={"display_name": "Bob Rename"},
            headers={**H, "If-Match": '"v1"'},
        ).status_code == 404
        assert client.post(
            f"/models/{model_id}/archive",
            headers={**H, "If-Match": '"v1"'},
        ).status_code == 404
        assert client.post(
            f"/models/{model_id}/unarchive",
            headers={**H, "If-Match": '"v1"'},
        ).status_code == 404
        assert client.post(
            f"/models/{model_id}/duplicate",
            json={"display_name": "x"}, headers=H,
        ).status_code == 404
        assert client.post(
            f"/models/{model_id}/revisions",
            json={"name": "x"},
            headers={**H, "If-Match": '"v1"'},
        ).status_code == 404
        assert client.get(
            f"/models/{model_id}/revisions/1", headers=H
        ).status_code == 404
        assert client.get(
            f"/models/{model_id}/revisions/1/export", headers=H
        ).status_code == 404
        assert client.post(
            f"/models/{model_id}/revisions/1/restore",
            headers={**H, "If-Match": '"v1"'},
        ).status_code == 404

        listed = client.get("/models", headers=H).json()["data"]["items"]
        assert not any(m["id"] == model_id for m in listed)

    # owner segue autorizado no mesmo path
    with alice_vt, alice_rbac:
        assert client.get(f"/models/{model_id}", headers=H).status_code == 200


def test_http_superadmin_has_no_cross_owner_access(client):
    """Real superadmin principal (RBAC is_superadmin, subject próprio):
    capabilities globais não implicam ownership — foreign é 404."""
    alice_vt, alice_rbac = authed(uid="alice")
    with alice_vt, alice_rbac:
        model_id = client.post(
            "/models", json={"display_name": "Alice Only"}, headers=H
        ).json()["data"]["model_id"]

    root_vt, root_rbac = authed(uid="root-1", superadmin=True)
    with root_vt, root_rbac:
        listed = client.get("/models", headers=H).json()["data"]["items"]
        assert not any(m["id"] == model_id for m in listed)
        assert client.get(
            f"/models/{model_id}", headers=H
        ).status_code == 404
        assert client.patch(
            f"/models/{model_id}",
            json={"display_name": "Root Rename"},
            headers={**H, "If-Match": '"v1"'},
        ).status_code == 404


def test_created_by_mass_assignment_rejected(client):
    """Ownership deriva exclusivamente do caller autenticado — campo
    created_by/owner no payload público é rejeitado (extra=forbid)."""
    vt, rbac = authed(uid="alice")
    with vt, rbac:
        assert client.post(
            "/models",
            json={"display_name": "X", "created_by": "bob"},
            headers=H,
        ).status_code == 422
        assert client.post(
            "/models",
            json={"display_name": "X", "owner": "bob"},
            headers=H,
        ).status_code == 422

        model_id = client.post(
            "/models", json={"display_name": "Y"}, headers=H
        ).json()["data"]["model_id"]
        assert client.patch(
            f"/models/{model_id}",
            json={"display_name": "Z", "created_by": "bob"},
            headers={**H, "If-Match": '"v1"'},
        ).status_code == 422


def test_rename_extra_field_rejected(client):
    vt, rbac = authed()
    with vt, rbac:
        model_id = client.post(
            "/models", json={"display_name": "A"}, headers=H
        ).json()["data"]["model_id"]
        resp = client.patch(
            f"/models/{model_id}",
            json={"display_name": "B", "version": 9},
            headers={**H, "If-Match": '"v1"'},
        )
        assert resp.status_code == 422
