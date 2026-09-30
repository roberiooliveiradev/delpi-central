"""E2E journeys exercisable at API level (E2E-01..17 backend-visible parts).

Runs through the real FastAPI app with in-memory repository — the same
journeys the browser tests will drive once the full stack is up.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from bpmn_modeler.application.use_cases import BpmnModelerService
from bpmn_modeler.domain.value_objects.canonical_bpmn_artifact import (
    CanonicalBpmnArtifact,
)
from bpmn_modeler.infrastructure.runtime import SystemClock, UuidGenerator
from bpmn_modeler.infrastructure.validation.blank import (
    TemplateBlankArtifactFactory,
)
from bpmn_modeler.infrastructure.validation.engine import LxmlBpmnValidator
from bpmn_modeler.interface.http.app import create_app

from . import fixtures as fx
from .conftest import InMemoryRepository

ALL_PERMS = ["bpmn-modeler.view", "bpmn-modeler.edit", "bpmn-modeler.manage"]
H = {"Authorization": "Bearer fake"}


@pytest.fixture()
def app_repo():
    return InMemoryRepository()


@pytest.fixture()
def client(app_repo):
    validator = LxmlBpmnValidator()
    service = BpmnModelerService(
        repository=app_repo,
        validator=validator,
        input_safety=validator,
        blank_artifacts=TemplateBlankArtifactFactory(UuidGenerator()),
        clock=SystemClock(),
        ids=UuidGenerator(),
    )
    app = create_app(service)
    app.state.repository = app_repo  # permite testes tamperarem o read-back
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture()
def auth():
    rbac = {
        "id": "u1", "email": "u@x.dev", "name": "U", "roles": [],
        "groups": [], "permissions": ALL_PERMS, "is_superadmin": False,
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


def _create(client) -> str:
    resp = client.post("/models", json={"display_name": "Journey"}, headers=H)
    assert resp.status_code == 201
    return resp.json()["data"]["model_id"]


def _etag(client, model_id: str) -> str:
    return client.get(f"/models/{model_id}", headers=H).headers["etag"]


def test_e2e_01_create_edit_save_reopen_export_byte_exact(client, auth):
    """E2E-01/03: create→open blank→edit→save→authoritative reload→export."""
    vt, rbac = auth
    with vt, rbac:
        model_id = _create(client)
        assert _etag(client, model_id) == '"v1"'

        xml = client.get(f"/models/{model_id}/working-copy", headers=H).text
        edited = xml.replace("<bpmn:process", '<bpmn:process name="Fluxo A"')
        resp = client.put(
            f"/models/{model_id}/working-copy",
            content=edited.encode(),
            headers={**H, "Content-Type": "application/xml", "If-Match": '"v1"'},
        )
        assert resp.status_code == 200

        # reopen → authoritative bytes são exatamente o candidato salvo
        reopened = client.get(f"/models/{model_id}/working-copy", headers=H)
        assert reopened.text == edited

        exported = client.get(f"/models/{model_id}/working-copy/export", headers=H)
        assert exported.content == edited.encode()
        assert "attachment" in exported.headers["content-disposition"]


def test_e2e_02_import_valid_roundtrip_no_normalization(client, auth):
    """E2E-02: import→open→export preserva bytes exatos."""
    vt, rbac = auth
    with vt, rbac:
        resp = client.post(
            "/models/import",
            files={"file": ("f.bpmn", fx.FX_VALID_001.encode(), "text/xml")},
            data={"display_name": "Imported"},
            headers=H,
        )
        assert resp.status_code == 201
        model_id = resp.json()["data"]["model_id"]

        exported = client.get(f"/models/{model_id}/working-copy/export", headers=H)
        assert exported.content == fx.FX_VALID_001.encode()


def test_e2e_08_malformed_inspect_blocked_no_write(client, auth):
    """E2E-08: malformed → MALFORMED_XML → blocked → nada persistido."""
    vt, rbac = auth
    with vt, rbac:
        resp = client.post(
            "/imports/inspect",
            files={"file": ("x.bpmn", fx.FX_BADXML_001.encode(), "text/xml")},
            headers=H,
        )
        assert resp.json()["data"]["recognition_state"] == "MALFORMED_XML"
        assert resp.json()["data"]["eligible_to_import"] is False

        resp = client.post(
            "/models/import",
            files={"file": ("x.bpmn", fx.FX_BADXML_001.encode(), "text/xml")},
            data={"display_name": "Bad"},
            headers=H,
        )
        assert resp.status_code == 422
        listing = client.get("/models?page_size=100", headers=H).json()["data"]
        assert listing["items"] == []


def test_e2e_09_security_inputs_rejected(client, auth):
    """E2E-09: DOCTYPE/entity/oversize → INPUT_REJECTED_SECURITY, zero writes."""
    vt, rbac = auth
    with vt, rbac:
        for content in (fx.FX_SEC_001, fx.FX_SEC_002):
            resp = client.post(
                "/imports/inspect",
                files={"file": ("x.bpmn", content.encode(), "text/xml")},
                headers=H,
            )
            assert resp.json()["data"]["recognition_state"] == "INPUT_REJECTED_SECURITY", content[:30]


def test_e2e_11_mustunderstand_readonly_gate(client, auth):
    """E2E-11 (backend part): mustUnderstand importa, mas save é bloqueado."""
    vt, rbac = auth
    with vt, rbac:
        resp = client.post(
            "/models/import",
            files={"file": ("e.bpmn", fx.FX_EXT_003.encode(), "text/xml")},
            data={"display_name": "Ext"},
            headers=H,
        )
        assert resp.status_code == 201
        model_id = resp.json()["data"]["model_id"]

        wc = client.get(f"/models/{model_id}/working-copy", headers=H).text
        mutated = wc.replace('key="a"', 'key="b"')
        resp = client.put(
            f"/models/{model_id}/working-copy",
            content=mutated.encode(),
            headers={**H, "Content-Type": "application/xml", "If-Match": '"v1"'},
        )
        assert resp.status_code == 422
        details = resp.json()["error"]["details"]
        assert details["recognition_state"] == "BPMN_RECOGNIZED_WITH_ISSUES"
        report_issues = details["validation_report"]["issues"]
        assert any(i["rule_id"] == "EXT-003" for i in report_issues)


def test_e2e_12_revision_append_only_restore(client, auth):
    """E2E-12: rev1→edit→rev2→restore rev1→rev3 (origin=restore), intactas."""
    vt, rbac = auth
    with vt, rbac:
        model_id = _create(client)
        xml_v1 = client.get(f"/models/{model_id}/working-copy", headers=H).text

        assert client.post(
            f"/models/{model_id}/revisions", headers={**H, "If-Match": '"v1"'}
        ).status_code == 201

        edited = xml_v1.replace("<bpmn:process", '<bpmn:process name="v2"')
        client.put(
            f"/models/{model_id}/working-copy", content=edited.encode(),
            headers={**H, "Content-Type": "application/xml", "If-Match": '"v2"'},
        )
        client.post(f"/models/{model_id}/revisions", headers={**H, "If-Match": '"v3"'})

        resp = client.get(f"/models/{model_id}/revisions/1/export", headers=H)
        assert resp.content == xml_v1.encode()

        # restore rev1 → new rev3 origin=restore; WC volta ao artefato de rev1
        etag = _etag(client, model_id)
        resp = client.post(
            f"/models/{model_id}/revisions/1/restore",
            headers={**H, "If-Match": etag},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["revision_number"] == 3

        wc = client.get(f"/models/{model_id}/working-copy", headers=H).text
        assert wc == xml_v1

        revs = client.get(f"/models/{model_id}/revisions", headers=H).json()["data"]["items"]
        assert sorted(r["revision_number"] for r in revs) == [1, 2, 3]
        rev3 = next(r for r in revs if r["revision_number"] == 3)
        assert rev3["origin"] == "restore"
        assert client.get(f"/models/{model_id}/revisions/2/export", headers=H).content == edited.encode()


def test_e2e_13_no_changes_revision_rejected(client, auth):
    vt, rbac = auth
    with vt, rbac:
        model_id = _create(client)
        client.post(f"/models/{model_id}/revisions", headers={**H, "If-Match": '"v1"'})
        resp = client.post(f"/models/{model_id}/revisions", headers={**H, "If-Match": '"v2"'})
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "NO_CHANGES"
        revs = client.get(f"/models/{model_id}/revisions", headers=H).json()["data"]["items"]
        assert len(revs) == 1


def test_e2e_14_archive_lifecycle(client, auth):
    """E2E-14: archive→read-only ops OK→mutations blocked→unarchive."""
    vt, rbac = auth
    with vt, rbac:
        model_id = _create(client)
        resp = client.post(f"/models/{model_id}/archive", headers={**H, "If-Match": '"v1"'})
        assert resp.status_code == 200

        # read ops OK
        assert client.get(f"/models/{model_id}", headers=H).status_code == 200
        assert client.get(f"/models/{model_id}/working-copy/export", headers=H).status_code == 200

        # mutations blocked
        xml = client.get(f"/models/{model_id}/working-copy", headers=H).text
        assert client.put(
            f"/models/{model_id}/working-copy", content=xml.encode(),
            headers={**H, "Content-Type": "application/xml", "If-Match": '"v2"'},
        ).status_code == 409
        assert client.post(
            f"/models/{model_id}/revisions", headers={**H, "If-Match": '"v2"'}
        ).status_code == 409

        # duplicate still allowed on archived source
        resp = client.post(
            f"/models/{model_id}/duplicate",
            json={"display_name": "Cópia"}, headers=H,
        )
        assert resp.status_code == 201

        resp = client.post(
            f"/models/{model_id}/unarchive", headers={**H, "If-Match": '"v2"'}
        )
        assert resp.status_code == 200
        # editable again
        edited = xml.replace("<bpmn:process", '<bpmn:process name="x"')
        etag = _etag(client, model_id)
        assert client.put(
            f"/models/{model_id}/working-copy", content=edited.encode(),
            headers={**H, "Content-Type": "application/xml", "If-Match": etag},
        ).status_code == 200


def test_e2e_15_noop_mutations(client, auth):
    """E2E-15: rename same name / identical save / re-archive / restore current."""
    vt, rbac = auth
    with vt, rbac:
        model_id = _create(client)
        resp = client.patch(
            f"/models/{model_id}", json={"display_name": "Journey"},
            headers={**H, "If-Match": '"v1"'},
        )
        assert resp.json()["data"]["changed"] is False

        xml = client.get(f"/models/{model_id}/working-copy", headers=H).text
        resp = client.put(
            f"/models/{model_id}/working-copy", content=xml.encode(),
            headers={**H, "Content-Type": "application/xml", "If-Match": '"v1"'},
        )
        assert resp.json()["data"]["changed"] is False
        assert _etag(client, model_id) == '"v1"'


def test_e2e_16_conflict_stale_writer(client, auth):
    """E2E-16: writer A vence; writer B com token stale → CONFLICT."""
    vt, rbac = auth
    with vt, rbac:
        model_id = _create(client)
        xml = client.get(f"/models/{model_id}/working-copy", headers=H).text

        a = xml.replace("<bpmn:process", '<bpmn:process name="A"')
        b = xml.replace("<bpmn:process", '<bpmn:process name="B"')

        assert client.put(
            f"/models/{model_id}/working-copy", content=a.encode(),
            headers={**H, "Content-Type": "application/xml", "If-Match": '"v1"'},
        ).status_code == 200

        resp = client.put(
            f"/models/{model_id}/working-copy", content=b.encode(),
            headers={**H, "Content-Type": "application/xml", "If-Match": '"v1"'},
        )
        assert resp.status_code == 412
        assert resp.json()["error"]["code"] == "CONFLICT"
        # sem force overwrite: B precisa reler
        assert client.get(f"/models/{model_id}/working-copy", headers=H).text == a


def test_e2e_04_import_no_di_preserved_byte_exact(client, auth):
    """E2E-04 (backend part): import sem DI → artefato persistido SEM DI injetado.

    O backend nunca gera DI; o render transitório é responsabilidade do canvas.
    Persistência e export devem ser byte-exatas ao XML importado.
    """
    vt, rbac = auth
    with vt, rbac:
        insp = client.post(
            "/imports/inspect",
            files={"file": ("nod.bpmn", fx.FX_NODI_001.encode(), "text/xml")},
            headers=H,
        )
        assert insp.json()["data"]["eligible_to_import"] is True

        resp = client.post(
            "/models/import",
            files={"file": ("nod.bpmn", fx.FX_NODI_001.encode(), "text/xml")},
            data={"display_name": "NoDI"},
            headers=H,
        )
        assert resp.status_code == 201
        model_id = resp.json()["data"]["model_id"]

        exported = client.get(f"/models/{model_id}/working-copy/export", headers=H)
        assert exported.content == fx.FX_NODI_001.encode()
        assert b"BPMNDiagram" not in exported.content


def test_e2e_07_validation_issue_repair_revalidate(client, auth):
    """E2E-07 (backend part): dangling ref → issues → repair → revalidate clean."""
    vt, rbac = auth
    with vt, rbac:
        insp = client.post(
            "/imports/inspect",
            files={"file": ("b.bpmn", fx.FX_REF_001.encode(), "text/xml")},
            headers=H,
        )
        data = insp.json()["data"]
        assert data["recognition_state"] == "BPMN_RECOGNIZED_WITH_ISSUES"
        assert any(
            i["rule_id"] == "BPMN-STRUCT-010"
            for i in data["validation_report"]["issues"]
        )

        resp = client.post(
            "/models/import",
            files={"file": ("b.bpmn", fx.FX_REF_001.encode(), "text/xml")},
            data={"display_name": "Broken"},
            headers=H,
        )
        assert resp.status_code == 201
        model_id = resp.json()["data"]["model_id"]

        repaired = fx.FX_REF_001.replace('sourceRef="GHOST"', 'sourceRef="T1"')
        resp = client.put(
            f"/models/{model_id}/working-copy",
            content=repaired.encode(),
            headers={**H, "Content-Type": "application/xml", "If-Match": '"v1"'},
        )
        assert resp.status_code == 200

        insp2 = client.post(
            "/imports/inspect",
            files={"file": ("b.bpmn", repaired.encode(), "text/xml")},
            headers=H,
        )
        assert not any(
            i["rule_id"] == "BPMN-STRUCT-010"
            for i in insp2.json()["data"]["validation_report"]["issues"]
        )


def test_e2e_10_unknown_extension_mustunderstand_false_preserved(client, auth):
    """E2E-10: extensões mustUnderstand=false importam e exportam byte-exatas."""
    vt, rbac = auth
    with vt, rbac:
        for content in (fx.FX_EXT_001, fx.FX_EXT_002, fx.FX_EXT_004):
            resp = client.post(
                "/models/import",
                files={"file": ("e.bpmn", content.encode(), "text/xml")},
                data={"display_name": "Ext"},
                headers=H,
            )
            assert resp.status_code == 201, content[:60]
            model_id = resp.json()["data"]["model_id"]
            exported = client.get(
                f"/models/{model_id}/working-copy/export", headers=H
            )
            assert exported.content == content.encode()
            assert b"vend" in exported.content


def test_e2e_17_divergent_readback_outcome_verification_failed(client, auth, app_repo):
    """E2E-17: read-back divergente → 500 OUTCOME_VERIFICATION_FAILED."""
    vt, rbac = auth
    with vt, rbac:
        model_id = _create(client)
        xml = client.get(f"/models/{model_id}/working-copy", headers=H).text

        original_get = app_repo.get_aggregate

        def divergent_get(mid: str):
            model = original_get(mid)
            if model is not None:
                model.working_copy.replace_artifact(
                    CanonicalBpmnArtifact(xml + "<!--tampered-->")
                )
            return model

        try:
            app_repo.get_aggregate = divergent_get  # type: ignore[method-assign]
            resp = client.put(
                f"/models/{model_id}/working-copy",
                content=xml.replace(
                    "<bpmn:process", '<bpmn:process name="X"'
                ).encode(),
                headers={**H, "Content-Type": "application/xml", "If-Match": '"v1"'},
            )
            assert resp.status_code == 500
            assert resp.json()["error"]["code"] == "OUTCOME_VERIFICATION_FAILED"
        finally:
            app_repo.get_aggregate = original_get  # type: ignore[method-assign]


def test_e2e_18_multiple_bpmn_diagrams_roundtrip(client, auth):
    """E2E-18: arquivo com múltiplos BPMNDiagrams importa e exporta intacto."""
    vt, rbac = auth
    with vt, rbac:
        resp = client.post(
            "/models/import",
            files={"file": ("multi.bpmn", fx.FX_DI_004.encode(), "text/xml")},
            data={"display_name": "MultiDI"},
            headers=H,
        )
        assert resp.status_code == 201
        model_id = resp.json()["data"]["model_id"]
        exported = client.get(f"/models/{model_id}/working-copy/export", headers=H)
        assert exported.content == fx.FX_DI_004.encode()
        assert exported.content.count(b"<bpmndi:BPMNDiagram") == 2


def test_e2e_20_auth_matrix(client):
    assert client.get("/models").status_code == 401

    viewer_rbac = {
        "id": "v", "email": "v@x.dev", "name": "V", "roles": [], "groups": [],
        "permissions": ["bpmn-modeler.view"], "is_superadmin": False,
    }
    with patch(
        "bpmn_modeler.interface.http.auth.validate_token",
        return_value={"sub": "v", "email": "v@x.dev"},
    ), patch(
        "bpmn_modeler.interface.http.auth.load_user_rbac",
        new=AsyncMock(return_value=viewer_rbac),
    ):
        assert client.get("/models", headers=H).status_code == 200
        assert client.post(
            "/models", json={"display_name": "X"}, headers=H
        ).status_code == 403
