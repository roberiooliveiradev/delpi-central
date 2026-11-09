"""D16 — bandeiras de acompanhamento PRC: domínio, REST e paridade EVA."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from tests.conftest import rbac_payload
from tests.test_product_registration import (
    ANALYST,
    _get,
    _post,
    _submit_create,
    _token,
)
from tests.test_prc_eva_parity import _confirmed, _ctx, _entry, _ref_from

from engineering_app.composition import prc_composer
from engineering_app.domain.product_registration import flags as attendance_flags
from engineering_app.domain.product_registration.errors import (
    PrcValidationError,
)
from engineering_app.infrastructure.persistence.product_registration.in_memory_repository import (
    InMemoryProductRegistrationRepository,
)
from engineering_app.interface.mcp import prc_semantic
from engineering_app.interface.mcp.semantic_bridge import (
    _EXECUTE_DISPATCH,
    _READ_DISPATCH,
)


@pytest.fixture
def prc_service_repo():
    prc_composer.reset_prc_singletons()
    repo = InMemoryProductRegistrationRepository()
    from engineering_app.application.use_cases.product_registration.service import (
        ProductRegistrationService,
    )

    prc_composer.set_prc_service_for_tests(
        ProductRegistrationService(repo, official_reader=None)
    )
    yield {"repo": repo}
    prc_composer.reset_prc_singletons()
    prc_composer.set_prc_service_for_tests(None)


def _patch(client, url, token, json=None, headers=None):
    h = {"Authorization": f"Bearer {token}"}
    if headers:
        h.update(headers)
    return client.patch(url, json=json or {}, headers=h)


def _delete(client, url, token, headers=None):
    h = {"Authorization": f"Bearer {token}"}
    if headers:
        h.update(headers)
    return client.delete(url, headers=h)


def _create_flag(client, jwks_env, core_rbac, rid, *, title="Revisar descrição",
                 description="Confirmar descrição técnica com solicitante.",
                 key="flag-k1", sub="analyst-1"):
    core_rbac["behavior"] = ("data", rbac_payload(ANALYST, id=sub))
    return _post(
        client,
        f"/v1/product-registration/requests/{rid}/flags",
        _token(jwks_env, sub),
        json={"title": title, "description": description, "subject": "GENERAL"},
        headers={"Idempotency-Key": key},
    )


class TestFlagDomainValidation:
    def test_reject_empty_title(self):
        with pytest.raises(PrcValidationError):
            attendance_flags.validate_flag_payload(
                title="  ", description="ok"
            )

    def test_reject_empty_description(self):
        with pytest.raises(PrcValidationError):
            attendance_flags.validate_flag_payload(
                title="ok", description=""
            )

    def test_title_max_length(self):
        with pytest.raises(PrcValidationError):
            attendance_flags.validate_flag_payload(
                title="x" * 121, description="ok"
            )

    def test_description_max_length(self):
        with pytest.raises(PrcValidationError):
            attendance_flags.validate_flag_payload(
                title="ok", description="y" * 1001
            )

    def test_field_path_must_be_catalog(self):
        with pytest.raises(PrcValidationError):
            attendance_flags.validate_flag_payload(
                title="ok",
                description="ok",
                subject="FIELD",
                target_path="notARealPath",
            )


class TestFlagRestCrud:
    def test_create_list_detail_update_resolve_reopen_delete(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _submit_create(
            client, jwks_env, core_rbac, sub="analyst-1"
        ).json()["data"]["requestId"]
        tok = _token(jwks_env, "analyst-1")
        core_rbac["behavior"] = (
            "data", rbac_payload(ANALYST, id="analyst-1")
        )

        created = _create_flag(client, jwks_env, core_rbac, rid)
        assert created.status_code == 201, created.text
        flag = created.json()["data"]
        assert flag["status"] == "OPEN"
        assert flag["title"] == "Revisar descrição"
        assert flag["version"] == 1
        fid = flag["id"]

        listed = _get(
            client,
            f"/v1/product-registration/requests/{rid}/flags?status=OPEN",
            tok,
        )
        assert listed.status_code == 200
        body = listed.json()["data"]
        assert body["openCount"] == 1
        assert body["total"] == 1
        assert body["items"][0]["id"] == fid

        detail = _get(
            client,
            f"/v1/product-registration/requests/{rid}/flags/{fid}",
            tok,
        )
        assert detail.status_code == 200
        assert detail.json()["data"]["description"].startswith("Confirmar")

        updated = _patch(
            client,
            f"/v1/product-registration/requests/{rid}/flags/{fid}",
            tok,
            json={
                "expectedVersion": 1,
                "description": "Texto revisado com o solicitante.",
            },
            headers={"Idempotency-Key": "flag-upd-1"},
        )
        assert updated.status_code == 200, updated.text
        assert updated.json()["data"]["version"] == 2
        assert "revisado" in updated.json()["data"]["description"]

        stale = _patch(
            client,
            f"/v1/product-registration/requests/{rid}/flags/{fid}",
            tok,
            json={"expectedVersion": 1, "title": "stale"},
        )
        assert stale.status_code == 409

        resolved = _post(
            client,
            f"/v1/product-registration/requests/{rid}/flags/{fid}/actions/resolve",
            tok,
            json={"expectedVersion": 2},
            headers={"Idempotency-Key": "flag-res-1"},
        )
        assert resolved.status_code == 200, resolved.text
        assert resolved.json()["data"]["status"] == "RESOLVED"
        assert resolved.json()["data"]["version"] == 3

        resolved_list = _get(
            client,
            f"/v1/product-registration/requests/{rid}/flags?status=RESOLVED",
            tok,
        ).json()["data"]
        assert resolved_list["resolvedCount"] == 1
        assert resolved_list["openCount"] == 0

        reopened = _post(
            client,
            f"/v1/product-registration/requests/{rid}/flags/{fid}/actions/reopen",
            tok,
            json={"expectedVersion": 3},
            headers={"Idempotency-Key": "flag-reo-1"},
        )
        assert reopened.status_code == 200
        assert reopened.json()["data"]["status"] == "OPEN"

        deleted = _delete(
            client,
            f"/v1/product-registration/requests/{rid}/flags/{fid}"
            f"?expectedVersion=4",
            tok,
            headers={"Idempotency-Key": "flag-del-1"},
        )
        assert deleted.status_code == 200, deleted.text
        assert deleted.json()["data"]["deleted"] is True

        gone = _get(
            client,
            f"/v1/product-registration/requests/{rid}/flags/{fid}",
            tok,
        )
        assert gone.status_code == 404

        second_delete = _delete(
            client,
            f"/v1/product-registration/requests/{rid}/flags/{fid}"
            f"?expectedVersion=5",
            tok,
        )
        assert second_delete.status_code == 404

        timeline = _get(
            client,
            f"/v1/product-registration/requests/{rid}/timeline",
            tok,
        ).json()["data"]["items"]
        types = {e["event_type"] for e in timeline}
        assert "flag.created" in types
        assert "flag.updated" in types
        assert "flag.resolved" in types
        assert "flag.reopened" in types
        assert "flag.deleted" in types

    def test_isolation_between_requests(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        a = _submit_create(
            client, jwks_env, core_rbac, sub="analyst-1"
        ).json()["data"]["requestId"]
        # segundo intake com outra chave
        core_rbac["behavior"] = (
            "data", rbac_payload(ANALYST, id="analyst-1")
        )
        b = _post(
            client,
            "/v1/product-registration/intake/requests",
            _token(jwks_env, "analyst-1"),
            json={
                "source": "engineering-test",
                "externalRequestId": "ext-b",
                "requestType": "create",
                "productType": "raw_material",
                "schemaVersion": 1,
                "requestedData": {
                    "description": "OUTRO",
                    "group": "1001",
                    "productKind": "MP",
                    "defaultWarehouse": "01",
                    "unit": "UN",
                    "thirdPartyProduct": "1",
                    "accountingAccount": "11401002",
                    "customerReference": "",
                    "suppliers": [],
                },
            },
            headers={"Idempotency-Key": "intake-b"},
        ).json()["data"]["requestId"]

        created = _create_flag(
            client, jwks_env, core_rbac, a, key="iso-a"
        ).json()["data"]
        tok = _token(jwks_env, "analyst-1")
        cross = _get(
            client,
            f"/v1/product-registration/requests/{b}/flags/{created['id']}",
            tok,
        )
        assert cross.status_code == 404

    def test_validation_errors(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _submit_create(
            client, jwks_env, core_rbac, sub="analyst-1"
        ).json()["data"]["requestId"]
        core_rbac["behavior"] = (
            "data", rbac_payload(ANALYST, id="analyst-1")
        )
        bad = _post(
            client,
            f"/v1/product-registration/requests/{rid}/flags",
            _token(jwks_env, "analyst-1"),
            json={"title": "", "description": "x"},
        )
        assert bad.status_code in (400, 422)

    def test_idempotent_create(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _submit_create(
            client, jwks_env, core_rbac, sub="analyst-1"
        ).json()["data"]["requestId"]
        first = _create_flag(
            client, jwks_env, core_rbac, rid, key="idem-1"
        )
        second = _create_flag(
            client, jwks_env, core_rbac, rid, key="idem-1"
        )
        assert first.status_code == 201
        assert second.status_code == 200
        assert first.json()["data"]["id"] == second.json()["data"]["id"]
        listed = _get(
            client,
            f"/v1/product-registration/requests/{rid}/flags",
            _token(jwks_env, "analyst-1"),
        ).json()["data"]
        assert listed["total"] == 1


class TestFlagEvaParity:
    @pytest.mark.asyncio
    async def test_flag_dispatch_registered(self):
        for action in ("flag_list", "flag_detail"):
            assert ("product_registration", action) in _READ_DISPATCH
        for action in (
            "flag_create", "flag_update", "flag_resolve",
            "flag_reopen", "flag_delete",
        ):
            assert ("product_registration", action) in _EXECUTE_DISPATCH

    @pytest.mark.asyncio
    async def test_create_list_resolve_via_eva(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rid = _submit_create(
            client, jwks_env, core_rbac, sub="analyst-1"
        ).json()["data"]["requestId"]
        create = await prc_semantic.execute_action(
            _ctx("analyst-1"), _entry("flag_create"), "act",
            target_ref=rid,
            payload={
                "title": "Solicitar Part Number",
                "description": "Cobrar PN correto do requisitante.",
                "subject": "GENERAL",
            },
            idempotency_key="eva-flag-1",
        )
        text = create.content[0].text
        assert '"success": true' in text or "Bandeira" in text
        data = json.loads(text)["data"]
        fid = data["id"]
        assert data["status"] == "OPEN"

        listed = await prc_semantic.read_action(
            _ctx("analyst-1"), _entry("flag_list"),
            {"request_id": rid, "status": "OPEN"},
        )
        assert fid in listed.content[0].text

        resolved = await prc_semantic.execute_action(
            _ctx("analyst-1"), _entry("flag_resolve"), "act",
            target_ref=rid,
            expected_version=1,
            payload={"flag_id": fid},
        )
        assert "RESOLVED" in resolved.content[0].text

    @pytest.mark.asyncio
    async def test_delete_requires_human_confirmation(
        self, client, jwks_env, core_rbac, prc_service_repo, monkeypatch
    ):
        rid = _submit_create(
            client, jwks_env, core_rbac, sub="analyst-1"
        ).json()["data"]["requestId"]
        created = _create_flag(
            client, jwks_env, core_rbac, rid, key="eva-del"
        ).json()["data"]
        fid = created["id"]
        prep = await prc_semantic.execute_action(
            _ctx("analyst-1"), _entry("flag_delete"), "prepare",
            target_ref=rid,
            expected_version=1,
            payload={"flag_id": fid},
        )
        assert "proposal_ref" in prep.content[0].text

        blocked = await prc_semantic.execute_action(
            _ctx("analyst-1"), _entry("flag_delete"), "commit",
            target_ref=rid,
            expected_version=1,
            payload={"flag_id": fid},
            proposal_ref=_ref_from(prep),
        )
        # sem confirmação humana simulada → não exclui
        assert (
            '"success": false' in blocked.content[0].text
            or "confirma" in blocked.content[0].text.lower()
            or "proposal" in blocked.content[0].text.lower()
            or "elicitation" in blocked.content[0].text.lower()
        )

        _confirmed(monkeypatch)
        prep2 = await prc_semantic.execute_action(
            _ctx("analyst-1"), _entry("flag_delete"), "prepare",
            target_ref=rid,
            expected_version=1,
            payload={"flag_id": fid},
        )
        commit = await prc_semantic.execute_action(
            _ctx("analyst-1"), _entry("flag_delete"), "commit",
            target_ref=rid,
            expected_version=1,
            payload={"flag_id": fid},
            proposal_ref=_ref_from(prep2),
        )
        assert '"deleted": true' in commit.content[0].text or (
            '"success": true' in commit.content[0].text
            and "exclu" in commit.content[0].text.lower()
        )
