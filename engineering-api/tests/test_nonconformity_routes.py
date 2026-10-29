"""T2/T4 — contratos E-NC-01..11: AuthZ, envelope, estados honestos.

Repositório: ``InMemoryNonconformityRepository`` compartilhado via
monkeypatch do composer — semântica completa, sem banco. Cobertura:
engineering.access exclusivo (401/403/manage-only/service/sem permissão),
filtros/sort/paginação, CRUD, histórico append-only, idempotência,
concorrência otimista, import dry-run/confirm_replace e contexto OV.
"""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient

import engineering_app.composition.nc_composer as nc_composer
import engineering_app.interface.http.routes.nonconformity_routes as nc_routes
from engineering_app.domain.nonconformity.models import NcActor
from engineering_app.infrastructure.persistence.nonconformity.in_memory_nonconformity_repository import (
    InMemoryNonconformityRepository,
)
from engineering_app.infrastructure.persistence.nonconformity.unavailable_nonconformity_repository import (
    UnavailableNonconformityRepository,
)
from engineering_app.main import app
from tests.conftest import rbac_payload

ENGINEERING_ACCESS = "engineering.access"
ENGINEERING_MANAGE = "engineering.manage"
LEGACY_PERMISSION = "dashboard-lmps.nc.write"

SEED_NC = {
    "status": "open",
    "sale_number": "003696",
    "lmp_number": "LMP-10",
    "customer_name": "Cliente Alfa",
    "occurrence_date": "2026-05-05",
    "launch_date": "2026-05-01",
    "executed_by": "Executor X",
    "released_by": "Liberador Y",
    "defect_description": "Medida fora da tolerância",
    "problem_tags": ["Medida", "Desenho"],
    "products": [
        {"product_code": "TRF-100", "product_description": "Transformador"}
    ],
}


@pytest.fixture
def nc_repo():
    repo = InMemoryNonconformityRepository(seed=[dict(SEED_NC)])

    class _EarliestOv:
        async def get_reference_start_date(self, access_token):
            return date(2026, 1, 1)

    real_build_repo = nc_composer.build_nonconformity_repository
    real_build_anchor = nc_composer.build_nc_earliest_ov_source
    nc_composer.build_nonconformity_repository = lambda: repo
    nc_composer.build_nc_earliest_ov_source = lambda: _EarliestOv()
    yield repo
    nc_composer.build_nonconformity_repository = real_build_repo
    nc_composer.build_nc_earliest_ov_source = real_build_anchor


@pytest.fixture
def unavailable_repo():
    repo = UnavailableNonconformityRepository()
    real = nc_composer.build_nonconformity_repository
    nc_composer.build_nonconformity_repository = lambda: repo
    yield repo
    nc_composer.build_nonconformity_repository = real


def _bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _nc_id(repo) -> str:
    return repo.export_records()[0]["id"]


class TestReadContracts:
    def test_list_returns_items_envelope(self, jwks_env, core_rbac, client, nc_repo):
        token = jwks_env["make_token"]()
        resp = client.get("/v1/nonconformities", headers=_bearer(token))
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["total"] == 1
        item = body["data"]["items"][0]
        assert item["sale_number"] == "003696"
        assert item["problem_tags"] == ["Desenho", "Medida"] or sorted(
            item["problem_tags"]
        ) == ["Desenho", "Medida"]
        assert item["product_codes"] == ["TRF-100"]

    def test_list_filters_and_sort(self, jwks_env, core_rbac, client, nc_repo):
        token = jwks_env["make_token"]()
        resp = client.get(
            "/v1/nonconformities?status=done", headers=_bearer(token)
        )
        assert resp.json()["data"]["total"] == 0

        resp = client.get(
            "/v1/nonconformities?sale_number=0036", headers=_bearer(token)
        )
        assert resp.json()["data"]["total"] == 1

        resp = client.get(
            "/v1/nonconformities?product_code=trf", headers=_bearer(token)
        )
        assert resp.json()["data"]["total"] == 1

        resp = client.get(
            "/v1/nonconformities?problem_tag=desenho", headers=_bearer(token)
        )
        assert resp.json()["data"]["total"] == 1

        resp = client.get(
            "/v1/nonconformities?date_start=2026-05-06",
            headers=_bearer(token),
        )
        assert resp.json()["data"]["total"] == 0

        resp = client.get(
            "/v1/nonconformities?sort_by=sale_number&sort_dir=asc",
            headers=_bearer(token),
        )
        assert resp.json()["data"]["sort_by"] == "sale_number"
        assert resp.json()["data"]["sort_dir"] == "asc"

    def test_list_invalid_period_400(self, jwks_env, core_rbac, client, nc_repo):
        token = jwks_env["make_token"]()
        resp = client.get(
            "/v1/nonconformities?date_start=2026-06-01&date_end=2026-05-01",
            headers=_bearer(token),
        )
        assert resp.status_code == 400

    def test_get_by_id(self, jwks_env, core_rbac, client, nc_repo):
        token = jwks_env["make_token"]()
        rid = _nc_id(nc_repo)
        resp = client.get(f"/v1/nonconformities/{rid}", headers=_bearer(token))
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == rid
        assert resp.json()["data"]["status"] == "open"

    def test_get_not_found_404(self, jwks_env, core_rbac, client, nc_repo):
        token = jwks_env["make_token"]()
        resp = client.get(
            f"/v1/nonconformities/{uuid.uuid4()}", headers=_bearer(token)
        )
        assert resp.status_code == 404

    def test_get_invalid_uuid_400(self, jwks_env, core_rbac, client, nc_repo):
        token = jwks_env["make_token"]()
        resp = client.get(
            "/v1/nonconformities/not-a-uuid", headers=_bearer(token)
        )
        assert resp.status_code == 400

    def test_history_created_event(self, jwks_env, core_rbac, client, nc_repo):
        token = jwks_env["make_token"]()
        rid = _nc_id(nc_repo)
        resp = client.get(
            f"/v1/nonconformities/{rid}/history", headers=_bearer(token)
        )
        assert resp.status_code == 200
        events = resp.json()["data"]["items"]
        assert len(events) == 1
        assert events[0]["event_type"] == "created"
        assert events[0]["changes"]["fields"]

    def test_problem_tags_catalog(self, jwks_env, core_rbac, client, nc_repo):
        token = jwks_env["make_token"]()
        resp = client.get(
            "/v1/nonconformities/problem-tags", headers=_bearer(token)
        )
        assert resp.status_code == 200
        labels = {t["label"] for t in resp.json()["data"]["items"]}
        assert {"Medida", "Desenho"} <= labels

    def test_export_shape(self, jwks_env, core_rbac, client, nc_repo):
        token = jwks_env["make_token"]()
        resp = client.get("/v1/nonconformities/export", headers=_bearer(token))
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["version"] == 1
        assert data["count"] == 1
        assert data["items"][0]["sale_number"] == "003696"

    def test_indicators_streak(self, jwks_env, core_rbac, client, nc_repo):
        token = jwks_env["make_token"]()
        resp = client.get(
            "/v1/nonconformities/indicators", headers=_bearer(token)
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["last_nc_date"] == "2026-05-05"
        assert data["nc_count"] == 1
        assert "current_days_without_nc" in data
        assert "record_days_without_nc" in data

    def test_indicators_empty_repo_uses_anchor(
        self, jwks_env, core_rbac, client
    ):
        empty = InMemoryNonconformityRepository()

        class _Anchor:
            async def get_reference_start_date(self, access_token):
                return date(2026, 5, 1)

        real_repo = nc_composer.build_nonconformity_repository
        real_anchor = nc_composer.build_nc_earliest_ov_source
        nc_composer.build_nonconformity_repository = lambda: empty
        nc_composer.build_nc_earliest_ov_source = lambda: _Anchor()
        try:
            token = jwks_env["make_token"]()
            resp = client.get(
                "/v1/nonconformities/indicators", headers=_bearer(token)
            )
            data = resp.json()["data"]
            assert data["reference_start_date"] == "2026-05-01"
            assert data["current_days_without_nc"] >= 0
        finally:
            nc_composer.build_nonconformity_repository = real_repo
            nc_composer.build_nc_earliest_ov_source = real_anchor

    def test_unavailable_repo_returns_503(
        self, jwks_env, core_rbac, client, unavailable_repo
    ):
        """Fail-honest: persistência não configurada → 503, não lista vazia."""
        token = jwks_env["make_token"]()
        resp = client.get("/v1/nonconformities", headers=_bearer(token))
        assert resp.status_code == 503
        assert resp.json()["success"] is False


class TestWriteContracts:
    def _payload(self, **over):
        base = {
            "status": "open",
            "sale_number": "003700",
            "customer_name": "Cliente Beta",
            "occurrence_date": "2026-05-10",
            "defect_description": "Terminal solto",
            "problem_tags": ["Terminal"],
            "products": [
                {"product_code": "P-1", "product_description": "Prod 1"}
            ],
        }
        base.update(over)
        return base

    def test_create_and_history(self, jwks_env, core_rbac, client, nc_repo):
        token = jwks_env["make_token"]()
        resp = client.post(
            "/v1/nonconformities",
            json=self._payload(),
            headers=_bearer(token),
        )
        assert resp.status_code == 200
        record = resp.json()["data"]
        assert record["status"] == "open"
        assert record["occurrence_date"] == "2026-05-10"
        history = client.get(
            f"/v1/nonconformities/{record['id']}/history",
            headers=_bearer(token),
        ).json()["data"]["items"]
        assert history[0]["event_type"] == "created"
        assert history[0]["actor_user_id"] == "user-1"

    def test_create_idempotent(self, jwks_env, core_rbac, client, nc_repo):
        token = jwks_env["make_token"]()
        headers = {**_bearer(token), "Idempotency-Key": "req-abc-1"}
        first = client.post(
            "/v1/nonconformities", json=self._payload(), headers=headers
        )
        second = client.post(
            "/v1/nonconformities", json=self._payload(), headers=headers
        )
        assert first.json()["data"]["id"] == second.json()["data"]["id"]
        assert len(nc_repo.export_records()) == 2  # seed + 1

    def test_create_invalid_status_400(
        self, jwks_env, core_rbac, client, nc_repo
    ):
        token = jwks_env["make_token"]()
        resp = client.post(
            "/v1/nonconformities",
            json=self._payload(status="banana"),
            headers=_bearer(token),
        )
        assert resp.status_code in (400, 422)

    def test_update_full_replace_and_history(
        self, jwks_env, core_rbac, client, nc_repo
    ):
        token = jwks_env["make_token"]()
        rid = _nc_id(nc_repo)
        resp = client.put(
            f"/v1/nonconformities/{rid}",
            json=self._payload(status="done", occurrence_date="2026-05-05"),
            headers=_bearer(token),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "done"
        events = client.get(
            f"/v1/nonconformities/{rid}/history", headers=_bearer(token)
        ).json()["data"]["items"]
        types = sorted(e["event_type"] for e in events)
        assert types == ["created", "updated"]
        assert len(events) == 2

    def test_update_requires_occurrence_date(
        self, jwks_env, core_rbac, client, nc_repo
    ):
        token = jwks_env["make_token"]()
        rid = _nc_id(nc_repo)
        payload = self._payload()
        payload["occurrence_date"] = None
        resp = client.put(
            f"/v1/nonconformities/{rid}", json=payload, headers=_bearer(token)
        )
        assert resp.status_code == 400

    def test_update_optimistic_lock_conflict(
        self, jwks_env, core_rbac, client, nc_repo
    ):
        token = jwks_env["make_token"]()
        rid = _nc_id(nc_repo)
        record = client.get(
            f"/v1/nonconformities/{rid}", headers=_bearer(token)
        ).json()["data"]
        payload = self._payload(occurrence_date="2026-05-05")
        payload["expected_updated_at"] = "1999-01-01T00:00:00+00:00"
        resp = client.put(
            f"/v1/nonconformities/{rid}", json=payload, headers=_bearer(token)
        )
        assert resp.status_code == 409

        payload["expected_updated_at"] = record["updated_at"]
        resp = client.put(
            f"/v1/nonconformities/{rid}", json=payload, headers=_bearer(token)
        )
        assert resp.status_code == 200

    def test_delete(self, jwks_env, core_rbac, client, nc_repo):
        token = jwks_env["make_token"]()
        rid = _nc_id(nc_repo)
        resp = client.delete(
            f"/v1/nonconformities/{rid}", headers=_bearer(token)
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["deleted"] is True
        resp = client.get(
            f"/v1/nonconformities/{rid}", headers=_bearer(token)
        )
        assert resp.status_code == 404

    def test_delete_not_found_404(self, jwks_env, core_rbac, client, nc_repo):
        token = jwks_env["make_token"]()
        resp = client.delete(
            f"/v1/nonconformities/{uuid.uuid4()}", headers=_bearer(token)
        )
        assert resp.status_code == 404

    def test_import_dry_run_no_side_effects(
        self, jwks_env, core_rbac, client, nc_repo
    ):
        token = jwks_env["make_token"]()
        before = len(nc_repo.export_records())
        resp = client.post(
            "/v1/nonconformities/import",
            json={
                "items": [self._payload(), {"status": "bad"}],
                "dry_run": True,
            },
            headers=_bearer(token),
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["created"] == 1
        assert data["skipped"] == 1
        assert data["deleted"] == 0
        assert len(nc_repo.export_records()) == before

    def test_import_requires_confirm_replace(
        self, jwks_env, core_rbac, client, nc_repo
    ):
        token = jwks_env["make_token"]()
        resp = client.post(
            "/v1/nonconformities/import",
            json={"items": [self._payload()]},
            headers=_bearer(token),
        )
        assert resp.status_code == 403
        assert len(nc_repo.export_records()) == 1  # seed intacto

    def test_import_replace_total(self, jwks_env, core_rbac, client, nc_repo):
        token = jwks_env["make_token"]()
        resp = client.post(
            "/v1/nonconformities/import",
            json={
                "items": [self._payload(), self._payload(sale_number="003701")],
                "confirm_replace": True,
            },
            headers=_bearer(token),
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["deleted"] == 1
        assert data["created"] == 2
        assert len(nc_repo.export_records()) == 2

    def test_import_empty_items_400(self, jwks_env, core_rbac, client, nc_repo):
        token = jwks_env["make_token"]()
        resp = client.post(
            "/v1/nonconformities/import",
            json={"items": [], "confirm_replace": True},
            headers=_bearer(token),
        )
        assert resp.status_code == 400


class TestAuthorization:
    def test_anonymous_401(self, client, nc_repo):
        resp = client.get("/v1/nonconformities")
        assert resp.status_code == 401

    def test_invalid_token_401(self, jwks_env, client, nc_repo):
        resp = client.get(
            "/v1/nonconformities",
            headers={"Authorization": "Bearer garbage"},
        )
        assert resp.status_code == 401

    def test_missing_permission_403(self, jwks_env, core_rbac, client, nc_repo):
        core_rbac["behavior"] = ("data", rbac_payload([]))
        token = jwks_env["make_token"]()
        resp = client.get("/v1/nonconformities", headers=_bearer(token))
        assert resp.status_code == 403

    def test_manage_alone_does_not_grant(self, jwks_env, core_rbac, client, nc_repo):
        core_rbac["behavior"] = ("data", rbac_payload([ENGINEERING_MANAGE]))
        token = jwks_env["make_token"]()
        resp = client.get("/v1/nonconformities", headers=_bearer(token))
        assert resp.status_code == 403

    def test_legacy_permission_not_accepted(
        self, jwks_env, core_rbac, client, nc_repo
    ):
        core_rbac["behavior"] = ("data", rbac_payload([LEGACY_PERMISSION]))
        token = jwks_env["make_token"]()
        resp = client.get("/v1/nonconformities", headers=_bearer(token))
        assert resp.status_code == 403

    def test_service_principal_403(
        self, jwks_env, core_rbac, client, nc_repo, monkeypatch
    ):
        monkeypatch.setenv(
            "API_DELPI_INTERNAL_SERVICE_TOKEN", "svc-token-for-test-only"
        )
        resp = client.get(
            "/v1/nonconformities",
            headers={"X-Delpi-Service-Token": "svc-token-for-test-only"},
        )
        assert resp.status_code == 403

    def test_core_unavailable_fail_closed(
        self, jwks_env, core_rbac, client, nc_repo
    ):
        core_rbac["behavior"] = ("raise", RuntimeError("core down"))
        token = jwks_env["make_token"]()
        resp = client.get("/v1/nonconformities", headers=_bearer(token))
        assert resp.status_code in (401, 403, 503)


class TestContextContract:
    def test_context_composes_ov_and_products(
        self, jwks_env, core_rbac, client, nc_repo, monkeypatch
    ):
        from engineering_app.application.models.lmp import LmpFactDetailResult
        from engineering_app.application.use_cases.nonconformity.context import (
            GetNonconformityContextUseCase,
        )

        class _Facts:
            async def fetch_fact(self, ctx, **params):
                return LmpFactDetailResult(
                    status="available",
                    fact={"sale_number": "003696", "customer": "Alfa"},
                )

        class _Products:
            async def fetch_product_structure(self, ctx, *, code, **kw):
                return {"status": "available", "data": {"code": code, "bom": []}}

        use_case = GetNonconformityContextUseCase(
            nc_repo, facts_source=_Facts(), product_source=_Products()
        )
        monkeypatch.setattr(
            nc_routes, "build_get_nonconformity_context_use_case",
            lambda: use_case,
        )
        token = jwks_env["make_token"]()
        rid = _nc_id(nc_repo)
        resp = client.get(
            f"/v1/nonconformities/{rid}/context", headers=_bearer(token)
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["ov_status"] == "available"
        assert data["ov"]["sale_number"] == "003696"
        assert data["product_contexts"][0]["structure_status"] == "available"

    def test_context_not_found_404(
        self, jwks_env, core_rbac, client, nc_repo, monkeypatch
    ):
        from engineering_app.application.use_cases.nonconformity.context import (
            GetNonconformityContextUseCase,
        )

        class _Facts:
            async def fetch_fact(self, ctx, **params):
                raise AssertionError("não deve chamar facts para NC inexistente")

        class _Products:
            async def fetch_product_structure(self, ctx, *, code, **kw):
                return {"status": "unavailable"}

        use_case = GetNonconformityContextUseCase(
            nc_repo, facts_source=_Facts(), product_source=_Products()
        )
        monkeypatch.setattr(
            nc_routes, "build_get_nonconformity_context_use_case",
            lambda: use_case,
        )
        token = jwks_env["make_token"]()
        resp = client.get(
            f"/v1/nonconformities/{uuid.uuid4()}/context",
            headers=_bearer(token),
        )
        assert resp.status_code == 404
