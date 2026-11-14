"""PROD-02 — T01/T02: snapshot consolidado, V1, Vn+1 e no-op.

Cobre a matriz ratificada: baseline V1, conclusão sem diferença
técnica (sem nova revisão), diff real → V2, UPDATE parcial
preservando omitidos/proveniência, vínculos por supplierCode+store,
dual-read de snapshot legado e fail-closed mismatch/incomparable.
"""

from __future__ import annotations

import pytest

from tests.conftest import rbac_payload
from engineering_app.composition import prc_composer
from engineering_app.infrastructure.persistence.product_registration.in_memory_repository import (
    InMemoryProductRegistrationRepository,
)
from tests.test_product_registration import (
    ANALYST,
    FakeReader,
    _advance_to_attendance,
    _attach_reader,
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


def _update_body(changes, code="001234", idem=None):
    return {
        "source": "engineering-test",
        "requestType": "update",
        "productType": "raw_material",
        "schemaVersion": 1,
        "officialProductCode": code,
        "changes": changes,
    }


def _complete_update(client, jwks_env, core_rbac, prc_service_repo,
                     changes, product=None, code="001234", idem="k",
                     sub="analyst-1"):
    """Fluxo governado completo: intake update → start → complete.

    Retorna ``(resp_complete, rid)``. ``product`` é o estado oficial
    observado no read-back da conclusão (default ``_product()``).
    """
    _attach_reader(prc_service_repo)
    core_rbac["behavior"] = ("data", rbac_payload(ANALYST, id=sub))
    resp = _post(
        client, f"{_BASE}/intake/requests", _token(jwks_env, sub),
        json=_update_body(changes, code=code),
        headers={"Idempotency-Key": idem},
    )
    assert resp.status_code == 201, resp.text
    rid = resp.json()["data"]["requestId"]
    if product is not None:
        prc_service_repo["reader"] = FakeReader(product)
    v = _advance_to_attendance(client, jwks_env, core_rbac, rid, sub=sub)
    done = _post(
        client, f"{_BASE}/requests/{rid}/actions/complete",
        _token(jwks_env, sub),
        json={"expectedVersion": v, "officialCode": code},
    )
    return done, rid


def _record_and_revisions(repo, code="001234"):
    rec = repo.get_record_by_official_code(
        official_source="api-delpi/totvs", official_code=code
    )
    revs = repo.list_revisions(rec["id"]) if rec else []
    return rec, revs


class TestV1Baseline:
    def test_first_update_matched_creates_v1(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        done, _ = _complete_update(
            client, jwks_env, core_rbac, prc_service_repo,
            changes=[{"path": "unit", "proposedValue": "UN",
                      "reason": "ajuste"}],
            idem="v1-1",
        )
        assert done.status_code == 200, done.text
        data = done.json()["data"]
        assert data["status"] == "completed"
        assert data["revisionNumber"] == 1
        assert data["publishedRevisionNumber"] == 1
        assert data["changeKind"] == "baseline_initial"
        assert data["technicalChange"] is True
        rec, revs = _record_and_revisions(prc_service_repo["repo"])
        assert rec["current_revision_number"] == 1
        assert len(revs) == 1
        snap = revs[0]["technical_snapshot"]
        assert snap["schemaVersion"] == 2
        # verificado nesta conclusão → official_verified
        assert (
            snap["fields"]["unit"]["valueOrigin"] == "official_verified"
        )
        assert snap["fields"]["unit"]["value"] == "UN"
        assert "evidenceRef" in snap["fields"]["unit"]
        # baseline capturado no intake, não re-verificado → inherited
        assert (
            snap["fields"]["description"]["valueOrigin"]
            == "inherited_confirmed"
        )
        assert snap["fields"]["description"]["value"] == "MATERIAL TESTE"

    def test_second_update_same_value_noop(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        _complete_update(
            client, jwks_env, core_rbac, prc_service_repo,
            changes=[{"path": "unit", "proposedValue": "UN",
                      "reason": "r1"}],
            idem="noop-1",
        )
        done, rid2 = _complete_update(
            client, jwks_env, core_rbac, prc_service_repo,
            changes=[{"path": "unit", "proposedValue": "UN",
                      "reason": "r2"}],
            idem="noop-2",
        )
        assert done.status_code == 200, done.text
        data = done.json()["data"]
        assert data["status"] == "completed"
        assert data["changeKind"] == "no_technical_change"
        assert data["technicalChange"] is False
        assert data["revisionNumber"] == 1
        assert data["publishedRevisionNumber"] is None
        rec, revs = _record_and_revisions(prc_service_repo["repo"])
        assert rec["current_revision_number"] == 1
        assert len(revs) == 1  # nenhum INSERT em revisions
        assert rec["id"] == data["recordId"]

    def test_metadata_only_not_technical_diff(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        """Mesmo valor re-verificado: proveniência muda para
        official_verified mas valor técnico é igual → no-op."""
        _complete_update(
            client, jwks_env, core_rbac, prc_service_repo,
            changes=[{"path": "unit", "proposedValue": "UN",
                      "reason": "r1"}],
            idem="meta-1",
        )
        done, _ = _complete_update(
            client, jwks_env, core_rbac, prc_service_repo,
            changes=[{"path": "description",
                      "proposedValue": "MATERIAL TESTE",
                      "reason": "re-verificar"}],
            idem="meta-2",
        )
        assert done.status_code == 200, done.text
        assert done.json()["data"]["changeKind"] == "no_technical_change"
        _, revs = _record_and_revisions(prc_service_repo["repo"])
        assert len(revs) == 1


class TestV2TechnicalChange:
    def test_real_diff_creates_v2(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        _complete_update(
            client, jwks_env, core_rbac, prc_service_repo,
            changes=[{"path": "unit", "proposedValue": "UN",
                      "reason": "r1"}],
            idem="v2-1",
        )
        done, _ = _complete_update(
            client, jwks_env, core_rbac, prc_service_repo,
            changes=[{"path": "unit", "proposedValue": "BX",
                      "reason": "mudança de unidade"}],
            product=_product(unit="BX"),
            idem="v2-2",
        )
        assert done.status_code == 200, done.text
        data = done.json()["data"]
        assert data["changeKind"] == "technical_change"
        assert data["technicalChange"] is True
        assert data["revisionNumber"] == 2
        assert data["publishedRevisionNumber"] == 2
        rec, revs = _record_and_revisions(prc_service_repo["repo"])
        assert rec["current_revision_number"] == 2
        assert len(revs) == 2
        snap2 = revs[1]["technical_snapshot"]
        assert snap2["fields"]["unit"]["value"] == "BX"
        # revisão anterior permanece imutável
        assert revs[0]["technical_snapshot"]["fields"]["unit"][
            "value"
        ] == "UN"
        changes = revs[1]["changes"]
        unit_diff = [c for c in changes if c["path"] == "unit"]
        assert unit_diff == [
            {"path": "unit", "before": "UN", "after": "BX"}
        ]

    def test_partial_update_preserves_omitted_and_provenance(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        _complete_update(
            client, jwks_env, core_rbac, prc_service_repo,
            changes=[
                {"path": "unit", "proposedValue": "UN",
                 "reason": "r"},
                {"path": "description",
                 "proposedValue": "MATERIAL TESTE", "reason": "r"},
            ],
            idem="part-1",
        )
        done, _ = _complete_update(
            client, jwks_env, core_rbac, prc_service_repo,
            changes=[{"path": "unit", "proposedValue": "CX",
                      "reason": "r2"}],
            product=_product(unit="CX"),
            idem="part-2",
        )
        assert done.status_code == 200, done.text
        _, revs = _record_and_revisions(prc_service_repo["repo"])
        assert len(revs) == 2
        snap2 = revs[1]["technical_snapshot"]
        # omitido preserva valor E proveniência da revisão anterior
        assert snap2["fields"]["description"]["value"] == (
            "MATERIAL TESTE"
        )
        assert (
            snap2["fields"]["description"]["valueOrigin"]
            == "official_verified"
        )
        assert snap2["fields"]["unit"]["value"] == "CX"


class TestSuppliers:
    def test_link_merge_by_code_store(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        # V1: vínculo baseline herdado
        _complete_update(
            client, jwks_env, core_rbac, prc_service_repo,
            changes=[{"path": "unit", "proposedValue": "UN",
                      "reason": "r"}],
            idem="sup-1",
        )
        # V2: UPDATE de partNumber verificado contra observado
        core_rbac["behavior"] = (
            "data", rbac_payload(ANALYST, id="analyst-1")
        )
        _attach_reader(prc_service_repo)
        resp = _post(
            client, f"{_BASE}/intake/requests",
            _token(jwks_env),
            json={
                "source": "engineering-test",
                "requestType": "update",
                "productType": "raw_material",
                "schemaVersion": 1,
                "officialProductCode": "001234",
                "changes": [],
                "supplierLinkChanges": [
                    {"operation": "update",
                     "key": {"supplierCode": "000001", "store": "01"},
                     "fields": {"partNumber": "PN-2"}}
                ],
            },
            headers={"Idempotency-Key": "sup-2"},
        )
        assert resp.status_code == 201, resp.text
        rid = resp.json()["data"]["requestId"]
        prc_service_repo["reader"] = FakeReader(
            _product(
                suppliers=[{
                    "supplier_code": "000001",
                    "supplier_store": "01",
                    "supplier_name": "FORNECEDOR X",
                    "supplier_part_number": "PN-2",
                    "catalog_code": None,
                }]
            )
        )
        v = _advance_to_attendance(
            client, jwks_env, core_rbac, rid
        )
        done = _post(
            client,
            f"{_BASE}/requests/{rid}/actions/complete",
            _token(jwks_env),
            json={"expectedVersion": v, "officialCode": "001234"},
        )
        assert done.status_code == 200, done.text
        assert done.json()["data"]["changeKind"] == "technical_change"
        _, revs = _record_and_revisions(prc_service_repo["repo"])
        assert len(revs) == 2
        links = revs[1]["technical_snapshot"]["supplierLinks"]
        key = "000001|01"
        assert key in links
        assert links[key]["linkState"] == "present"
        assert links[key]["attributes"]["partNumber"]["value"] == "PN-2"
        # atributo não alterado preservado
        assert (
            links[key]["attributes"]["supplierName"]["value"]
            == "FORNECEDOR X"
        )
        pn_diff = [
            c for c in revs[1]["changes"]
            if c["path"] == "suppliers[000001|01].partNumber"
        ]
        assert pn_diff and pn_diff[0]["after"] == "PN-2"


class TestLegacyDualRead:
    def _seed_legacy_revision(self, repo, snapshot_dict, code="001234"):
        """Revisão schema_version=1 (formato plano pré-PROD-02)."""
        from engineering_app.infrastructure.persistence.product_registration.in_memory_repository import (  # noqa: E501
            _now,
            _uuid,
        )
        rec_id = _uuid()
        repo._records[rec_id] = {
            "id": rec_id,
            "product_type": "raw_material",
            "official_product_code": code,
            "current_revision_number": 1,
            "last_official_verified_at": _now(),
            "official_source": "api-delpi/totvs",
            "created_at": _now(),
            "updated_at": _now(),
        }
        repo._record_by_key[("api-delpi/totvs", code)] = rec_id
        repo._revisions[rec_id] = [{
            "id": _uuid(),
            "record_id": rec_id,
            "revision_number": 1,
            "request_id": _uuid(),
            "schema_version": 1,
            "technical_snapshot": snapshot_dict,
            "changes": [],
            "official_evidence_id": _uuid(),
            "approved_by_subject": "legacy",
            "approved_at": _now(),
            "created_at": _now(),
        }]
        return rec_id

    def test_legacy_first_completion_consolidates_then_noop(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        """Legado→novo: primeira conclusão enriquece cobertura com
        baseline ``inherited_confirmed`` — estado consolidado muda
        (V2 de consolidação). Conclusão seguinte sem diff → no-op."""
        self._seed_legacy_revision(
            prc_service_repo["repo"],
            {"description": "MATERIAL TESTE", "unit": "UN"},
        )
        done, _ = _complete_update(
            client, jwks_env, core_rbac, prc_service_repo,
            changes=[{"path": "unit", "proposedValue": "UN",
                      "reason": "r"}],
            idem="leg-1",
        )
        assert done.status_code == 200, done.text
        # cobertura consolidada é diferença técnica real única
        assert done.json()["data"]["changeKind"] == "technical_change"
        _, revs = _record_and_revisions(prc_service_repo["repo"])
        assert len(revs) == 2
        assert revs[0]["schema_version"] == 1
        assert revs[1]["schema_version"] == 2
        done2, _ = _complete_update(
            client, jwks_env, core_rbac, prc_service_repo,
            changes=[{"path": "unit", "proposedValue": "UN",
                      "reason": "r2"}],
            idem="leg-1b",
        )
        assert done2.status_code == 200, done2.text
        assert done2.json()["data"]["changeKind"] == (
            "no_technical_change"
        )
        _, revs = _record_and_revisions(prc_service_repo["repo"])
        assert len(revs) == 2  # sem terceira revisão

    def test_legacy_diff_publishes_new_format_v2(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        self._seed_legacy_revision(
            prc_service_repo["repo"],
            {"description": "MATERIAL TESTE", "unit": "UN"},
        )
        done, _ = _complete_update(
            client, jwks_env, core_rbac, prc_service_repo,
            changes=[{"path": "unit", "proposedValue": "KG",
                      "reason": "r"}],
            product=_product(unit="KG"),
            idem="leg-2",
        )
        assert done.status_code == 200, done.text
        assert done.json()["data"]["revisionNumber"] == 2
        _, revs = _record_and_revisions(prc_service_repo["repo"])
        assert len(revs) == 2
        assert revs[0]["schema_version"] == 1  # legada preservada
        assert revs[1]["schema_version"] == 2
        # legado lido como registered_unverified — sem falsa origem
        assert (
            revs[0]["technical_snapshot"]["unit"] == "UN"
        )


class TestFailClosed:
    def test_mismatch_publishes_nothing(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        _complete_update(
            client, jwks_env, core_rbac, prc_service_repo,
            changes=[{"path": "unit", "proposedValue": "UN",
                      "reason": "r"}],
            idem="mm-1",
        )
        # segunda solicitação divergente do oficial → mismatch
        done, rid = _complete_update(
            client, jwks_env, core_rbac, prc_service_repo,
            changes=[{"path": "unit", "proposedValue": "BX",
                      "reason": "r"}],
            product=_product(unit="UN"),  # oficial difere
            idem="mm-2",
        )
        assert done.status_code == 409, done.text
        rec, revs = _record_and_revisions(prc_service_repo["repo"])
        assert rec["current_revision_number"] == 1
        assert len(revs) == 1

    def test_second_completion_rejected_completed_state(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        """Replay de conclusão na mesma request → state_conflict,
        sem duplicar revisão."""
        done, rid = _complete_update(
            client, jwks_env, core_rbac, prc_service_repo,
            changes=[{"path": "unit", "proposedValue": "UN",
                      "reason": "r"}],
            idem="rep-1",
        )
        assert done.status_code == 200
        core_rbac["behavior"] = (
            "data", rbac_payload(ANALYST, id="analyst-1")
        )
        again = _post(
            client,
            f"{_BASE}/requests/{rid}/actions/complete",
            _token(jwks_env),
            json={"expectedVersion": 3, "officialCode": "001234"},
        )
        assert again.status_code == 409
        _, revs = _record_and_revisions(prc_service_repo["repo"])
        assert len(revs) == 1


class TestPublishedRevisionReadModel:
    """§56 — solicitação não possui revisão até conclusão publicada.

    O read model do detalhe expõe ``publishedRevision`` somente quando a
    revisão efetivamente publicada registra este ``request_id``; nunca
    expõe ``baseRevision`` (dado interno de concorrência)."""

    def test_open_request_has_no_revision_fields(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        _attach_reader(prc_service_repo)
        core_rbac["behavior"] = (
            "data", rbac_payload(ANALYST, id="analyst-1")
        )
        resp = _post(
            client, f"{_BASE}/intake/requests", _token(jwks_env),
            json=_update_body(
                [{"path": "unit", "proposedValue": "UN", "reason": "r"}]
            ),
            headers={"Idempotency-Key": "open-1"},
        )
        assert resp.status_code == 201, resp.text
        rid = resp.json()["data"]["requestId"]
        detail = _get(
            client, f"{_BASE}/requests/{rid}", _token(jwks_env)
        )
        assert detail.status_code == 200, detail.text
        data = detail.json()["data"]
        assert "baseRevision" not in data
        assert data["publishedRevision"] is None
        # CAS interno preservado — não é revisão de produto.
        assert isinstance(data["caseVersion"], int)

    def test_completed_with_publish_links_revision(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        done, rid = _complete_update(
            client, jwks_env, core_rbac, prc_service_repo,
            changes=[{"path": "unit", "proposedValue": "UN",
                      "reason": "r"}],
            idem="pub-1",
        )
        assert done.status_code == 200, done.text
        detail = _get(
            client, f"{_BASE}/requests/{rid}", _token(jwks_env)
        )
        data = detail.json()["data"]
        pub = data["publishedRevision"]
        assert pub is not None
        assert pub["revisionNumber"] == 1
        assert pub["recordId"] == done.json()["data"]["recordId"]

    def test_completed_noop_has_no_published_revision(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        _complete_update(
            client, jwks_env, core_rbac, prc_service_repo,
            changes=[{"path": "unit", "proposedValue": "UN",
                      "reason": "r1"}],
            idem="pub-noop-1",
        )
        done, rid2 = _complete_update(
            client, jwks_env, core_rbac, prc_service_repo,
            changes=[{"path": "unit", "proposedValue": "UN",
                      "reason": "r2"}],
            idem="pub-noop-2",
        )
        assert done.status_code == 200, done.text
        assert done.json()["data"]["changeKind"] == "no_technical_change"
        detail = _get(
            client, f"{_BASE}/requests/{rid2}", _token(jwks_env)
        )
        data = detail.json()["data"]
        # concluída auditada sem autoria falsa da V1 preexistente
        assert data["status"] == "completed"
        assert data["publishedRevision"] is None

    def test_concurrent_requests_stale_revision_fail_closed(
        self, client, jwks_env, core_rbac, prc_service_repo
    ):
        """A e B sobre o mesmo produto; B conclui primeiro; A falha fechado
        (stale_revision) em vez de publicar sobre baseline obsoleto."""
        # produto passa a ter V1 acompanhado
        _complete_update(
            client, jwks_env, core_rbac, prc_service_repo,
            changes=[{"path": "unit", "proposedValue": "UN",
                      "reason": "v1"}],
            idem="conc-v1",
        )
        _attach_reader(prc_service_repo)
        core_rbac["behavior"] = (
            "data", rbac_payload(ANALYST, id="analyst-1")
        )
        # A e B abrem contra a revisão vigente (V1); ambos propõem a
        # mesma mudança para que a verificação oficial seja matched.
        rid_a = None
        rid_b = None
        for i, key in enumerate(("conc-a", "conc-b")):
            resp = _post(
                client, f"{_BASE}/intake/requests", _token(jwks_env),
                json=_update_body(
                    [{"path": "unit",
                      "proposedValue": "CX",
                      "reason": "r"}]
                ),
                headers={"Idempotency-Key": key},
            )
            assert resp.status_code == 201, resp.text
            if i == 0:
                rid_a = resp.json()["data"]["requestId"]
            else:
                rid_b = resp.json()["data"]["requestId"]
        # B conclui primeiro — verificação matched (oficial=CX) → V2
        prc_service_repo["reader"] = FakeReader(_product(unit="CX"))
        v_b = _advance_to_attendance(
            client, jwks_env, core_rbac, rid_b
        )
        done_b = _post(
            client, f"{_BASE}/requests/{rid_b}/actions/complete",
            _token(jwks_env),
            json={"expectedVersion": v_b, "officialCode": "001234"},
        )
        assert done_b.status_code == 200, done_b.text
        assert done_b.json()["data"]["publishedRevisionNumber"] == 2
        # A conclui depois — matched, mas baseline obsoleto → fail closed
        prc_service_repo["reader"] = FakeReader(_product(unit="CX"))
        v_a = _advance_to_attendance(
            client, jwks_env, core_rbac, rid_a
        )
        done_a = _post(
            client, f"{_BASE}/requests/{rid_a}/actions/complete",
            _token(jwks_env),
            json={"expectedVersion": v_a, "officialCode": "001234"},
        )
        assert done_a.status_code == 409, done_a.text
        rec, revs = _record_and_revisions(prc_service_repo["repo"])
        # nenhuma revisão duplicada nem publicação sobre baseline velho
        assert rec["current_revision_number"] == 2
        assert len(revs) == 2
        # A permanece em atendimento e sem vínculo de revisão
        detail_a = _get(
            client, f"{_BASE}/requests/{rid_a}", _token(jwks_env)
        )
        data_a = detail_a.json()["data"]
        assert data_a["status"] == "in_progress"
        assert data_a["publishedRevision"] is None
