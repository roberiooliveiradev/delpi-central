"""PRC-TRACK — bandeiras de produto acompanhado + comparação Vx×Vy.

Cobre ADR-04/CR-07: OPEN propaga-se às revisões seguintes, RESOLVED
visível só na revisão de encerramento, REMOVED some já nela,
encerradas são terminais, eventos nunca criam revisão e uma única
OPEN por registro+alvo (CAS + idempotência + AuthZ fail-closed).
"""

from __future__ import annotations

import pytest

from tests.conftest import rbac_payload
from engineering_app.composition import prc_composer
from engineering_app.infrastructure.persistence.product_registration.in_memory_repository import (
    InMemoryProductRegistrationRepository,
)
from tests.test_prc_snapshot_versioning import (
    _complete_update,
    _record_and_revisions,
)
from tests.test_product_registration import (
    ANALYST,
    _get,
    _post,
    _product,
    _token,
)


@pytest.fixture
def prc_service_repo(monkeypatch):
    prc_composer.reset_prc_singletons()
    repo = InMemoryProductRegistrationRepository()
    state = {"reader": None, "repo": repo}

    class _ReaderProxy:
        async def read_product(self, *, access_token, request_id,
                               official_code):
            return await state["reader"].read_product(
                access_token=access_token,
                request_id=request_id,
                official_code=official_code,
            )

    from engineering_app.application.use_cases.product_registration.service import (  # noqa: E501
        ProductRegistrationService,
    )

    prc_composer.set_prc_service_for_tests(
        ProductRegistrationService(repo, official_reader=_ReaderProxy())
    )
    yield state
    prc_composer.reset_prc_singletons()
    prc_composer.set_prc_service_for_tests(None)


_BASE = "/v1/product-registration"


def _patch(client, url, token, json=None, headers=None):
    return client.patch(
        url, json=json or {},
        headers={"Authorization": f"Bearer {token}",
                 **(headers or {})},
    )


def _v1(client, jwks_env, core_rbac, prc_service_repo):
    done, _ = _complete_update(
        client, jwks_env, core_rbac, prc_service_repo,
        changes=[{"path": "unit", "proposedValue": "UN",
                  "reason": "r"}],
        idem="f-v1",
    )
    assert done.status_code == 200, done.text
    rec, _ = _record_and_revisions(prc_service_repo["repo"])
    return rec


def _v2(client, jwks_env, core_rbac, prc_service_repo, idem="f-v2"):
    """Segunda conclusão com diff real → V2."""
    done, _ = _complete_update(
        client, jwks_env, core_rbac, prc_service_repo,
        changes=[{"path": "unit", "proposedValue": "KG",
                  "reason": "mudança"}],
        product=_product(unit="KG"),
        idem=idem,
    )
    assert done.status_code == 200, done.text
    return done


def _flag_body(**over):
    body = {
        "title": "Descrição divergente",
        "description": "Verificar descrição junto ao cadastro oficial.",
        "subject": "FIELD",
        "targetPath": "description",
    }
    body.update(over)
    return body


def _create_flag(client, jwks_env, core_rbac, record_id, **over):
    core_rbac["behavior"] = ("data", rbac_payload(ANALYST, id="analyst-1"))
    return _post(
        client,
        f"{_BASE}/technical-records/{record_id}/flags",
        _token(jwks_env, "analyst-1"),
        json=_flag_body(**over),
        headers={"Idempotency-Key": over.get("idem", "fl-1")},
    )


class TestRecordFlagLifecycle:
    def test_create_field_flag_open(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rec = _v1(client, jwks_env, core_rbac, prc_service_repo)
        resp = _create_flag(
            client, jwks_env, core_rbac, rec["id"]
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()["data"]
        assert data["status"] == "OPEN"
        assert data["atStatus"] == "OPEN"
        assert data["targetKey"] == "FIELD:description"
        assert data["openedRevisionNumber"] == 1
        assert data["version"] == 1

    def test_duplicate_open_target_conflict(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rec = _v1(client, jwks_env, core_rbac, prc_service_repo)
        assert _create_flag(
            client, jwks_env, core_rbac, rec["id"]
        ).status_code == 201
        dup = _create_flag(
            client, jwks_env, core_rbac, rec["id"], idem="fl-2"
        )
        assert dup.status_code == 409, dup.text

    def test_general_subject_rejected(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rec = _v1(client, jwks_env, core_rbac, prc_service_repo)
        resp = _create_flag(
            client, jwks_env, core_rbac, rec["id"],
            subject="GENERAL", targetPath=None,
        )
        assert resp.status_code == 422, resp.text

    def test_target_missing_in_snapshot_rejected(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rec = _v1(client, jwks_env, core_rbac, prc_service_repo)
        resp = _create_flag(
            client, jwks_env, core_rbac, rec["id"],
            targetPath="groupCode",  # ausente no _product()
        )
        # groupCode existe no catálogo mas não no snapshot (coverage
        # unknown — _product não traz group_code? traz; uso um path
        # desconhecido de fato para forçar 422).
        if resp.status_code == 201:
            pytest.fail("alvo ausente no snapshot foi aceito")
        assert resp.status_code == 422

    def test_update_and_stale_version(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rec = _v1(client, jwks_env, core_rbac, prc_service_repo)
        flag = _create_flag(
            client, jwks_env, core_rbac, rec["id"]
        ).json()["data"]
        ok = _patch(
            client,
            f"{_BASE}/technical-records/{rec['id']}"
            f"/flags/{flag['id']}",
            _token(jwks_env, "analyst-1"),
            json={"expectedVersion": 1, "title": "Novo título"},
        )
        assert ok.status_code == 200, ok.text
        assert ok.json()["data"]["title"] == "Novo título"
        assert ok.json()["data"]["version"] == 2
        stale = _patch(
            client,
            f"{_BASE}/technical-records/{rec['id']}"
            f"/flags/{flag['id']}",
            _token(jwks_env, "analyst-1"),
            json={"expectedVersion": 1, "title": "Outro"},
        )
        assert stale.status_code == 409, stale.text

    def test_resolve_terminal_and_new_occurrence(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rec = _v1(client, jwks_env, core_rbac, prc_service_repo)
        flag = _create_flag(
            client, jwks_env, core_rbac, rec["id"]
        ).json()["data"]
        res = _post(
            client,
            f"{_BASE}/technical-records/{rec['id']}"
            f"/flags/{flag['id']}/actions/resolve",
            _token(jwks_env, "analyst-1"),
            json={"expectedVersion": 1,
                  "reason": "Corrigido no cadastro"},
        )
        assert res.status_code == 200, res.text
        assert res.json()["data"]["status"] == "RESOLVED"
        # terminal: segunda resolução rejeitada
        again = _post(
            client,
            f"{_BASE}/technical-records/{rec['id']}"
            f"/flags/{flag['id']}/actions/resolve",
            _token(jwks_env, "analyst-1"),
            json={"expectedVersion": 2},
        )
        assert again.status_code == 422, again.text
        # reincidência → novo flagId no mesmo alvo
        recur = _create_flag(
            client, jwks_env, core_rbac, rec["id"], idem="fl-r2"
        )
        assert recur.status_code == 201, recur.text
        assert recur.json()["data"]["id"] != flag["id"]

    def test_remove_flag(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rec = _v1(client, jwks_env, core_rbac, prc_service_repo)
        flag = _create_flag(
            client, jwks_env, core_rbac, rec["id"]
        ).json()["data"]
        res = _post(
            client,
            f"{_BASE}/technical-records/{rec['id']}"
            f"/flags/{flag['id']}/actions/remove",
            _token(jwks_env, "analyst-1"),
            json={"expectedVersion": 1, "reason": "Inválida"},
        )
        assert res.status_code == 200, res.text
        assert res.json()["data"]["status"] == "REMOVED"

    def test_flags_never_create_revision(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rec = _v1(client, jwks_env, core_rbac, prc_service_repo)
        flag = _create_flag(
            client, jwks_env, core_rbac, rec["id"]
        ).json()["data"]
        _post(
            client,
            f"{_BASE}/technical-records/{rec['id']}"
            f"/flags/{flag['id']}/actions/resolve",
            _token(jwks_env, "analyst-1"),
            json={"expectedVersion": 1},
        )
        rec2, revs = _record_and_revisions(
            prc_service_repo["repo"]
        )
        assert rec2["current_revision_number"] == 1
        assert len(revs) == 1

    def test_flag_events_audit(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rec = _v1(client, jwks_env, core_rbac, prc_service_repo)
        flag = _create_flag(
            client, jwks_env, core_rbac, rec["id"]
        ).json()["data"]
        ev = _get(
            client,
            f"{_BASE}/technical-records/{rec['id']}"
            f"/flags/{flag['id']}/events",
            _token(jwks_env, "analyst-1"),
        )
        assert ev.status_code == 200, ev.text
        items = ev.json()["data"]["items"]
        assert [e["eventType"] for e in items] == ["flag.created"]
        assert items[0]["revisionNumber"] == 1

    def test_denied_for_requester(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rec = _v1(client, jwks_env, core_rbac, prc_service_repo)
        core_rbac["behavior"] = (
            "data",
            rbac_payload(
                ["plugin.engineering.attendance"], id="req-1"
            ),
        )
        resp = _get(
            client,
            f"{_BASE}/technical-records/{rec['id']}/flags",
            _token(jwks_env, "req-1"),
        )
        assert resp.status_code in (403, 404)


class TestTemporalProjection:
    """ADR-04 — projeção por revisão."""

    def test_open_propagates_resolved_visible_only_at_close(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rec = _v1(client, jwks_env, core_rbac, prc_service_repo)
        flag = _create_flag(
            client, jwks_env, core_rbac, rec["id"]
        ).json()["data"]
        _v2(client, jwks_env, core_rbac, prc_service_repo)
        # resolve na revisão vigente (V2)
        _post(
            client,
            f"{_BASE}/technical-records/{rec['id']}"
            f"/flags/{flag['id']}/actions/resolve",
            _token(jwks_env, "analyst-1"),
            json={"expectedVersion": 1},
        )
        rid = rec["id"]
        rev1 = _get(
            client,
            f"{_BASE}/technical-records/{rid}/revisions/1",
            _token(jwks_env, "analyst-1"),
        ).json()["data"]
        rev2 = _get(
            client,
            f"{_BASE}/technical-records/{rid}/revisions/2",
            _token(jwks_env, "analyst-1"),
        ).json()["data"]
        f1 = {f["id"]: f for f in rev1["flags"]}
        f2 = {f["id"]: f for f in rev2["flags"]}
        assert f1[flag["id"]]["atStatus"] == "OPEN"
        assert f2[flag["id"]]["atStatus"] == "RESOLVED"
        assert rev2["allowedFlagActions"]
        assert rev1["allowedFlagActions"] == []

    def test_removed_absent_at_closing_revision(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rec = _v1(client, jwks_env, core_rbac, prc_service_repo)
        flag = _create_flag(
            client, jwks_env, core_rbac, rec["id"]
        ).json()["data"]
        _post(
            client,
            f"{_BASE}/technical-records/{rec['id']}"
            f"/flags/{flag['id']}/actions/remove",
            _token(jwks_env, "analyst-1"),
            json={"expectedVersion": 1},
        )
        rev1 = _get(
            client,
            f"{_BASE}/technical-records/{rec['id']}/revisions/1",
            _token(jwks_env, "analyst-1"),
        ).json()["data"]
        # removida já na revisão de remoção → ausente no corte
        assert flag["id"] not in {f["id"] for f in rev1["flags"]}


class TestRecordListEnrichment:
    def test_list_exposes_description_flags_evolution(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rec = _v1(client, jwks_env, core_rbac, prc_service_repo)
        _create_flag(client, jwks_env, core_rbac, rec["id"])
        resp = _get(
            client, f"{_BASE}/technical-records",
            _token(jwks_env, "analyst-1"),
        )
        assert resp.status_code == 200, resp.text
        item = next(
            i for i in resp.json()["data"]["items"]
            if i["recordId"] == rec["id"]
        )
        assert item["description"] == "MATERIAL TESTE"
        assert item["openFlagCount"] == 1
        assert item["lastEvolutionAt"]
        assert item["currentRevisionNumber"] == 1

    def test_flag_state_filter(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rec = _v1(client, jwks_env, core_rbac, prc_service_repo)
        _create_flag(client, jwks_env, core_rbac, rec["id"])
        open_list = _get(
            client,
            f"{_BASE}/technical-records?flagState=open",
            _token(jwks_env, "analyst-1"),
        ).json()["data"]["items"]
        none_list = _get(
            client,
            f"{_BASE}/technical-records?flagState=none",
            _token(jwks_env, "analyst-1"),
        ).json()["data"]["items"]
        assert any(i["recordId"] == rec["id"] for i in open_list)
        assert not any(i["recordId"] == rec["id"] for i in none_list)

    def test_search_by_description(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rec = _v1(client, jwks_env, core_rbac, prc_service_repo)
        resp = _get(
            client,
            f"{_BASE}/technical-records?search=MATERIAL",
            _token(jwks_env, "analyst-1"),
        )
        ids = [i["recordId"] for i in resp.json()["data"]["items"]]
        assert rec["id"] in ids

    def test_sort_and_enum_validation(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        _v1(client, jwks_env, core_rbac, prc_service_repo)
        ok = _get(
            client,
            f"{_BASE}/technical-records?sort=code",
            _token(jwks_env, "analyst-1"),
        )
        assert ok.status_code == 200
        bad = _get(
            client,
            f"{_BASE}/technical-records?sort=bogus",
            _token(jwks_env, "analyst-1"),
        )
        assert bad.status_code == 422


class TestRevisionComparison:
    def test_v1_vs_v2_field_changes(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rec = _v1(client, jwks_env, core_rbac, prc_service_repo)
        _v2(client, jwks_env, core_rbac, prc_service_repo)
        resp = _get(
            client,
            f"{_BASE}/technical-records/{rec['id']}"
            "/comparison?from=1&to=2",
            _token(jwks_env, "analyst-1"),
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert data["comparable"] is True
        unit = next(
            c for c in data["fieldChanges"] if c["path"] == "unit"
        )
        assert unit["before"] == "UN"
        assert unit["after"] == "KG"
        assert unit["beforePresent"] is True
        assert unit["afterPresent"] is True
        assert data["from"]["revisionNumber"] == 1
        assert data["to"]["revisionNumber"] == 2

    def test_same_revision_rejected(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rec = _v1(client, jwks_env, core_rbac, prc_service_repo)
        resp = _get(
            client,
            f"{_BASE}/technical-records/{rec['id']}"
            "/comparison?from=1&to=1",
            _token(jwks_env, "analyst-1"),
        )
        assert resp.status_code == 422

    def test_missing_revision_404(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rec = _v1(client, jwks_env, core_rbac, prc_service_repo)
        resp = _get(
            client,
            f"{_BASE}/technical-records/{rec['id']}"
            "/comparison?from=1&to=9",
            _token(jwks_env, "analyst-1"),
        )
        assert resp.status_code == 404

    def test_flag_events_in_window(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        rec = _v1(client, jwks_env, core_rbac, prc_service_repo)
        _create_flag(client, jwks_env, core_rbac, rec["id"])
        _v2(client, jwks_env, core_rbac, prc_service_repo)
        resp = _get(
            client,
            f"{_BASE}/technical-records/{rec['id']}"
            "/comparison?from=1&to=2",
            _token(jwks_env, "analyst-1"),
        )
        data = resp.json()["data"]
        types = {e["eventType"] for e in data["flagEvents"]}
        assert "flag.created" in types

    def test_idempotency_row_is_not_request_scoped(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        """FIX record-flag idempotency FK — a coluna
        product_registration_idempotency.request_id tem FK para
        product_registration_requests; passar record_id violava a FK
        pós-commit (flag persistida + 500). Deve persistir NULL."""
        rec = _v1(client, jwks_env, core_rbac, prc_service_repo)
        resp = _create_flag(
            client, jwks_env, core_rbac, rec["id"], idem="fl-idem-fk"
        )
        assert resp.status_code == 201, resp.text
        repo = prc_service_repo["repo"]
        rows = [
            row for row in repo._idempotency.values()
            if row["operation"] == "record_flag_create"
        ]
        assert rows, "registro idempotente não persistido"
        assert rows[-1]["request_id"] is None
        assert rows[-1]["request_id"] != rec["id"]
