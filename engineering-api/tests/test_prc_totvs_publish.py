"""PRC-TOTVS-PUBLISH — conclusão automatizada (publish + verify + complete).

Cobre o fluxo governado: engineering-api delega as escritas à api-delpi
(``ProductPublisherPort``) e em seguida executa a mesma conclusão
verificada do caminho manual. Gate ``ENG_PRC_TOTVS_PUBLISH_ENABLED``
default OFF — habilitado aqui por injeção de serviço de teste.
"""

from __future__ import annotations

import pytest

from tests.conftest import rbac_payload
from tests.test_product_registration import (
    ANALYST,
    ENG_ACCESS,
    _advance_to_attendance,
    _create_body,
    _post,
    _product,
    _token,
)

from engineering_app.application.ports.product_registration import (
    ProductPublisherError,
)
from engineering_app.composition import prc_composer
from engineering_app.infrastructure.persistence.product_registration.in_memory_repository import (  # noqa: E501
    InMemoryProductRegistrationRepository,
)


class FakePublisher:
    """Publisher fake — registra chamadas e pode falhar sob demanda."""

    def __init__(self):
        self.calls: list[dict] = []
        self.error: ProductPublisherError | None = None
        self.supplier_names: dict[tuple[str, str], str] = {}

    async def _record(self, name: str, **kw):
        self.calls.append({"op": name, **kw})
        if self.error:
            raise self.error
        return {"status": "confirmed", "operation": name}

    async def resolve_supplier_name(
        self, *, supplier_code, store, access_token, request_id
    ):
        self.calls.append(
            {"op": "resolve_supplier_name",
             "supplier_code": supplier_code, "store": store}
        )
        if self.error:
            raise self.error
        return self.supplier_names.get((supplier_code, store))

    async def create_product(self, *, fields, access_token, request_id):
        return await self._record("create_product", fields=fields)

    async def update_product(
        self, *, product_code, fields, access_token, request_id
    ):
        return await self._record(
            "update_product", product_code=product_code, fields=fields
        )

    async def create_supplier_link(
        self, *, product_code, identity, attributes, access_token,
        request_id,
    ):
        return await self._record(
            "create_supplier_link",
            product_code=product_code,
            identity=identity,
            attributes=attributes,
        )

    async def update_supplier_link(
        self, *, product_code, identity, attributes, access_token,
        request_id,
    ):
        return await self._record(
            "update_supplier_link",
            product_code=product_code,
            identity=identity,
            attributes=attributes,
        )

    async def delete_supplier_link(
        self, *, product_code, identity, access_token, request_id
    ):
        return await self._record(
            "delete_supplier_link",
            product_code=product_code,
            identity=identity,
        )


class FakeReader:
    """Reader sequencial — pop(0) por chamada, repete o último."""

    def __init__(self, results):
        self._results = list(results)
        self.calls = 0

    async def read_product(self, *, access_token, request_id, official_code):
        self.calls += 1
        if len(self._results) > 1:
            return self._results.pop(0)
        return self._results[0]


@pytest.fixture
def prc_publish_repo(monkeypatch):
    """Service com reader+publisher injetáveis e gate habilitado."""
    prc_composer.reset_prc_singletons()
    repo = InMemoryProductRegistrationRepository()
    state = {
        "reader": None,
        "publisher": FakePublisher(),
        "repo": repo,
        "gate": True,
    }

    class _ReaderProxy:
        async def read_product(self, *, access_token, request_id,
                               official_code):
            return await state["reader"].read_product(
                access_token=access_token,
                request_id=request_id,
                official_code=official_code,
            )

    class _PublisherProxy:
        def __getattr__(self, name):
            return getattr(state["publisher"], name)

    from engineering_app.application.use_cases.product_registration.service import (  # noqa: E501
        ProductRegistrationService,
    )
    from engineering_app.infrastructure.storage.prc_attachment_storage import (  # noqa: E501
        MemoryAttachmentStorage,
    )

    prc_composer.set_prc_service_for_tests(
        ProductRegistrationService(
            repo,
            official_reader=_ReaderProxy(),
            attachment_storage=MemoryAttachmentStorage(),
            product_publisher=_PublisherProxy(),
            totvs_publish_enabled=state["gate"],
        )
    )
    yield state
    prc_composer.reset_prc_singletons()
    prc_composer.set_prc_service_for_tests(None)


@pytest.fixture
def prc_publish_disabled(monkeypatch):
    """Mesmo wiring com gate DESLIGADO — prova do default fechado."""
    prc_composer.reset_prc_singletons()
    repo = InMemoryProductRegistrationRepository()
    state = {"reader": None, "publisher": FakePublisher(), "repo": repo}

    class _ReaderProxy:
        async def read_product(self, *, access_token, request_id,
                               official_code):
            return await state["reader"].read_product(
                access_token=access_token,
                request_id=request_id,
                official_code=official_code,
            )

    class _PublisherProxy:
        def __getattr__(self, name):
            return getattr(state["publisher"], name)

    from engineering_app.application.use_cases.product_registration.service import (  # noqa: E501
        ProductRegistrationService,
    )

    prc_composer.set_prc_service_for_tests(
        ProductRegistrationService(
            repo,
            official_reader=_ReaderProxy(),
            product_publisher=_PublisherProxy(),
            totvs_publish_enabled=False,
        )
    )
    yield state
    prc_composer.reset_prc_singletons()
    prc_composer.set_prc_service_for_tests(None)


def _publish(client, jwks_env, rid, version, sub="analyst-1", **body_over):
    body = {"expectedVersion": version}
    body.update(body_over)
    return _post(
        client,
        f"/v1/product-registration/requests/{rid}/actions/publish-totvs",
        _token(jwks_env, sub),
        json=body,
        headers={"Idempotency-Key": body_over.get("idempotency_key", "pub-1")},
    )


def _create_in_progress(client, jwks_env, core_rbac, sub="user-1"):
    """Cria request create-type e avança até ``in_progress``."""
    core_rbac["behavior"] = ("data", rbac_payload(ANALYST, id=sub))
    resp = _post(
        client,
        "/v1/product-registration/intake/requests",
        _token(jwks_env, sub),
        json=_create_body(),
        headers={"Idempotency-Key": "k-1"},
    )
    assert resp.status_code == 201, resp.text
    rid = resp.json()["data"]["requestId"]
    version = _advance_to_attendance(
        client, jwks_env, core_rbac, rid, sub="analyst-1"
    )
    return rid, version


def _update_body(changes=None, ops=None, code="001234"):
    body = {
        "source": "engineering-test",
        "requestType": "update",
        "productType": "raw_material",
        "schemaVersion": 1,
        "officialProductCode": code,
        "changes": changes or [],
    }
    if ops is not None:
        body["supplierLinkChanges"] = ops
    return body


def _update_in_progress(client, jwks_env, core_rbac, body, sub="user-1"):
    core_rbac["behavior"] = ("data", rbac_payload(ANALYST, id=sub))
    resp = _post(
        client,
        "/v1/product-registration/intake/requests",
        _token(jwks_env, sub),
        json=body,
        headers={"Idempotency-Key": "k-u1"},
    )
    assert resp.status_code == 201, resp.text
    rid = resp.json()["data"]["requestId"]
    version = _advance_to_attendance(
        client, jwks_env, core_rbac, rid, sub="analyst-1"
    )
    return rid, version


class TestPublishCreate:
    def test_create_publishes_product_and_links_then_completes(
        self, client, jwks_env, core_rbac, prc_publish_repo
    ):
        prc_publish_repo["reader"] = FakeReader([_product()])
        rid, version = _create_in_progress(client, jwks_env, core_rbac)

        resp = _publish(
            client, jwks_env, rid, version, officialCode="001234"
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert data["status"] == "completed"
        assert data["officialCode"] == "001234"
        assert data["totvsPublish"] == "applied"

        calls = prc_publish_repo["publisher"].calls
        create = next(c for c in calls if c["op"] == "create_product")
        assert create["fields"]["B1_COD"] == "001234"
        assert create["fields"]["B1_DESC"] == "MATERIAL TESTE"
        assert create["fields"]["B1_GRUPO"] == "1001"
        assert create["fields"]["B1_TIPO"] == "MP"
        # read-only PO (PRC-D3) — nunca publicado
        assert "B1_CONTA" not in create["fields"]

        link = next(
            c for c in calls if c["op"] == "create_supplier_link"
        )
        assert link["identity"]["A5_FORNECE"] == "000001"
        assert link["identity"]["A5_LOJA"] == "01"
        assert link["attributes"]["A5_NOMEFOR"] == "FORNECEDOR X"
        assert link["attributes"]["A5_CODPRF"] == "PN-1"
        assert link["attributes"]["A5_DESCPRF"] == "MATERIAL TESTE"

    def test_idempotent_replay_returns_recorded_result(
        self, client, jwks_env, core_rbac, prc_publish_repo
    ):
        # OC-1 r2 — replay legitimo: mesma Idempotency-Key + mesmo body
        # apos sucesso retorna o resultado gravado (200), nao
        # state_conflict; nenhuma escrita adicional no publisher.
        prc_publish_repo["reader"] = FakeReader([_product()])
        rid, version = _create_in_progress(client, jwks_env, core_rbac)
        first = _publish(
            client, jwks_env, rid, version, officialCode="001234",
            idempotency_key="pub-replay",
        )
        assert first.status_code == 200, first.text
        calls_after = len(prc_publish_repo["publisher"].calls)

        second = _publish(
            client, jwks_env, rid, version, officialCode="001234",
            idempotency_key="pub-replay",
        )
        assert second.status_code == 200, second.text
        d2 = second.json()["data"]
        assert d2.get("replayed") is True
        inner = d2.get("response") or {}
        assert inner["status"] == "completed"
        assert inner["officialCode"] == "001234"
        assert len(prc_publish_repo["publisher"].calls) == calls_after

    def test_same_key_divergent_reason_returns_duplicate_conflict(
        self, client, jwks_env, core_rbac, prc_publish_repo
    ):
        # OC-1 r4 — caso negativo da semantica idempotente: mesma
        # Idempotency-Key com reason divergente nao e replay — e
        # PrcDuplicateError (409) sem nenhuma escrita adicional.
        prc_publish_repo["reader"] = FakeReader([_product()])
        rid, version = _create_in_progress(client, jwks_env, core_rbac)
        first = _publish(
            client, jwks_env, rid, version, officialCode="001234",
            idempotency_key="pub-div", reason="primeira publicacao",
        )
        assert first.status_code == 200, first.text
        calls_after = len(prc_publish_repo["publisher"].calls)

        second = _publish(
            client, jwks_env, rid, version, officialCode="001234",
            idempotency_key="pub-div", reason="outro motivo",
        )
        assert second.status_code == 409, second.text
        assert len(prc_publish_repo["publisher"].calls) == calls_after

    def test_create_requires_official_code(
        self, client, jwks_env, core_rbac, prc_publish_repo
    ):
        prc_publish_repo["reader"] = FakeReader([_product()])
        rid, version = _create_in_progress(client, jwks_env, core_rbac)
        resp = _publish(client, jwks_env, rid, version)
        assert resp.status_code == 422, resp.text
        assert prc_publish_repo["publisher"].calls == []

    def test_create_conflict_surfaces_honest_409(
        self, client, jwks_env, core_rbac, prc_publish_repo
    ):
        prc_publish_repo["reader"] = FakeReader([_product()])
        prc_publish_repo["publisher"].error = ProductPublisherError(
            "conflict", "B1_COD já existente no ERP."
        )
        rid, version = _create_in_progress(client, jwks_env, core_rbac)
        resp = _publish(
            client, jwks_env, rid, version, officialCode="001234"
        )
        assert resp.status_code == 409, resp.text
        detail = client.get(
            f"/v1/product-registration/requests/{rid}",
            headers={
                "Authorization":
                    f"Bearer {_token(jwks_env, 'analyst-1')}"
            },
        ).json()["data"]
        assert detail["status"] == "in_progress"


class TestPublishUpdate:
    def test_update_publishes_changed_fields_and_link_ops(
        self, client, jwks_env, core_rbac, prc_publish_repo
    ):
        baseline = _product()
        updated = _product(
            description="NOVA DESC",
            suppliers=[{
                "supplier_code": "000001",
                "supplier_store": "01",
                "supplier_name": "FORNECEDOR X",
                "supplier_part_number": "PN-2",
                "catalog_code": None,
            }],
        )
        prc_publish_repo["reader"] = FakeReader([baseline, updated])
        rid, version = _update_in_progress(
            client, jwks_env, core_rbac,
            _update_body(
                changes=[{
                    "path": "description",
                    "proposedValue": "NOVA DESC",
                    "reason": "correção",
                }],
                ops=[{
                    "operation": "update",
                    "key": {"supplierCode": "000001", "store": "01"},
                    "fields": {"partNumber": "PN-2"},
                }],
            ),
        )

        resp = _publish(client, jwks_env, rid, version)
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["status"] == "completed"

        calls = prc_publish_repo["publisher"].calls
        update = next(c for c in calls if c["op"] == "update_product")
        # somente campos alterados — merge completo é da api-delpi
        assert update["fields"] == {"B1_DESC": "NOVA DESC"}
        assert not any(c["op"] == "create_product" for c in calls)

        link = next(
            c for c in calls if c["op"] == "update_supplier_link"
        )
        assert link["attributes"] == {"A5_CODPRF": "PN-2"}
        assert not any(
            c["op"] == "resolve_supplier_name" for c in calls
        )

    def test_update_add_op_resolves_supplier_name(
        self, client, jwks_env, core_rbac, prc_publish_repo
    ):
        baseline = _product()
        after = _product(
            suppliers=[
                baseline["suppliers"][0],
                {
                    "supplier_code": "000002",
                    "supplier_store": "01",
                    "supplier_name": "FORNECEDOR Y",
                    "supplier_part_number": "PN-9",
                    "catalog_code": "CAT-9",
                },
            ],
        )
        prc_publish_repo["reader"] = FakeReader([baseline, after])
        prc_publish_repo["publisher"].supplier_names[
            ("000002", "01")
        ] = "FORNECEDOR Y"
        rid, version = _update_in_progress(
            client, jwks_env, core_rbac,
            _update_body(
                changes=[{
                    "path": "description",
                    "proposedValue": "MATERIAL TESTE",
                    "reason": "trigger",
                }],
                ops=[{
                    "operation": "add",
                    "key": {"supplierCode": "000002", "store": "01"},
                    "fields": {
                        "partNumber": "PN-9",
                        "catalogNumber": "CAT-9",
                    },
                }],
            ),
        )
        resp = _publish(client, jwks_env, rid, version)
        assert resp.status_code == 200, resp.text
        calls = prc_publish_repo["publisher"].calls
        assert any(
            c["op"] == "resolve_supplier_name" for c in calls
        )
        link = next(
            c for c in calls if c["op"] == "create_supplier_link"
        )
        assert link["attributes"]["A5_NOMEFOR"] == "FORNECEDOR Y"
        assert link["attributes"]["A5_CODPRCA"] == "CAT-9"
        assert link["attributes"]["A5_DESCPRF"] == "MATERIAL TESTE"

    def test_remove_op_blocked_before_any_write(
        self, client, jwks_env, core_rbac, prc_publish_repo
    ):
        prc_publish_repo["reader"] = FakeReader([_product()])
        rid, version = _update_in_progress(
            client, jwks_env, core_rbac,
            _update_body(
                changes=[{
                    "path": "description",
                    "proposedValue": "X",
                    "reason": "r",
                }],
                ops=[{
                    "operation": "remove",
                    "key": {"supplierCode": "000001", "store": "01"},
                }],
            ),
        )
        resp = _publish(client, jwks_env, rid, version)
        assert resp.status_code == 409, resp.text
        assert resp.json()["data"]["code"] == (
            "remove_completion_pending_owner"
        )
        assert prc_publish_repo["publisher"].calls == []


class TestPublishGuards:
    def test_gate_disabled_fails_closed(
        self, client, jwks_env, core_rbac, prc_publish_disabled
    ):
        prc_publish_disabled["reader"] = FakeReader([_product()])
        rid, version = _create_in_progress(client, jwks_env, core_rbac)
        resp = _publish(
            client, jwks_env, rid, version, officialCode="001234"
        )
        assert resp.status_code == 503, resp.text
        assert resp.json()["data"]["code"] == "official_unavailable"
        assert prc_publish_disabled["publisher"].calls == []

    def test_forbidden_actor_rejected(
        self, client, jwks_env, core_rbac, prc_publish_repo
    ):
        rid, version = _create_in_progress(client, jwks_env, core_rbac)
        core_rbac["behavior"] = ("data", rbac_payload([]))
        resp = _publish(
            client, jwks_env, rid, version, officialCode="001234"
        )
        assert resp.status_code == 403, resp.text

    def test_publisher_failure_preserves_manual_path(
        self, client, jwks_env, core_rbac, prc_publish_repo
    ):
        prc_publish_repo["reader"] = FakeReader([_product()])
        prc_publish_repo["publisher"].error = ProductPublisherError(
            "timeout", "api-delpi timeout"
        )
        rid, version = _create_in_progress(client, jwks_env, core_rbac)
        resp = _publish(
            client, jwks_env, rid, version, officialCode="001234"
        )
        assert resp.status_code == 504, resp.text

        # caminho manual intacto — complete tradicional ainda conclui
        prc_publish_repo["publisher"].error = None
        manual = _post(
            client,
            f"/v1/product-registration/requests/{rid}/actions/complete",
            _token(jwks_env, "analyst-1"),
            json={
                "expectedVersion": version,
                "officialCode": "001234",
            },
        )
        assert manual.status_code == 200, manual.text
        assert manual.json()["data"]["status"] == "completed"

    def test_state_conflict_when_not_in_progress(
        self, client, jwks_env, core_rbac, prc_publish_repo
    ):
        prc_publish_repo["reader"] = FakeReader([_product()])
        rid, version = _create_in_progress(client, jwks_env, core_rbac)
        resp = _publish(
            client, jwks_env, rid, version, officialCode="001234"
        )
        assert resp.status_code == 200, resp.text
        # segundo publish sobre caso concluído → state_conflict
        again = _publish(
            client, jwks_env, rid, version + 1, officialCode="001234",
            idempotency_key="pub-2",
        )
        assert again.status_code == 409, again.text

    def test_stale_expected_version_aborts_before_erp_writes(
        self, client, jwks_env, core_rbac, prc_publish_repo
    ):
        # OC-3 r1 — CAS antes das escritas: expectedVersion defasado
        # aborta com 409 e NENHUMA chamada ao publisher (efeito
        # colateral no ERP nunca precede o CAS).
        prc_publish_repo["reader"] = FakeReader([_product()])
        rid, version = _create_in_progress(client, jwks_env, core_rbac)
        stale = _publish(
            client, jwks_env, rid, version + 9, officialCode="001234",
            idempotency_key="pub-stale",
        )
        assert stale.status_code == 409, stale.text
        assert prc_publish_repo["publisher"].calls == []
