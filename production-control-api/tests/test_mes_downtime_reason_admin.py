"""Administração S2S do catálogo de motivos de parada (Etapa Cadastros 1)."""

from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest

from production_control_app.application.services.mes_downtime_reason_admin_service import (
    MesDowntimeReasonAdminService,
)
from production_control_app.application.services.mes_downtime_classification_service import (
    MesDowntimeClassificationService,
)
from production_control_app.domain.errors import (
    DowntimeReasonConflict,
    DowntimeReasonNotFound,
    InvalidDowntimeReason,
)


class FakeReasonAdminRepo:
    def __init__(self) -> None:
        self.rows: dict[str, dict] = {}
        self._seed()

    def _seed(self) -> None:
        for code, label, category, active, order in [
            ("raw_material", "Falta de material", "material", True, 40),
            ("setup", "Setup / preparação", "setup", True, 60),
            ("other", "Outro", "other", True, 990),
            ("obsolete", "Obsoleto", "other", False, 999),
        ]:
            self.rows[code] = {
                "code": code, "label": label, "category": category,
                "default_planned": None, "default_counts_as_availability_loss": None,
                "requires_note": code == "other", "active": active,
                "sort_order": order,
                "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
                "updated_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
            }

    def get(self, code):
        return self.rows.get(str(code).strip().lower())

    def list_active(self):
        return sorted(
            (row for row in self.rows.values() if row["active"]),
            key=lambda row: (row["sort_order"], row["code"]),
        )

    def list_all(self):
        return sorted(self.rows.values(), key=lambda row: (row["sort_order"], row["code"]))

    def create(self, *, code, label, category, requires_note, sort_order):
        code = str(code).strip().lower()
        if code in self.rows:
            raise DowntimeReasonConflict(f"Já existe motivo de parada com o código '{code}'.")
        row = {
            "code": code, "label": label, "category": category,
            "default_planned": None, "default_counts_as_availability_loss": None,
            "requires_note": requires_note, "active": True, "sort_order": sort_order,
            "created_at": datetime(2026, 2, 1, tzinfo=timezone.utc),
            "updated_at": datetime(2026, 2, 1, tzinfo=timezone.utc),
        }
        self.rows[code] = row
        return row

    def update(self, code, *, label, category, requires_note, sort_order):
        row = self.rows.get(str(code).strip().lower())
        if row is None:
            return None
        row.update(
            label=label, category=category,
            requires_note=requires_note, sort_order=sort_order,
            updated_at=datetime(2026, 2, 2, tzinfo=timezone.utc),
        )
        return row

    def set_active(self, code, *, active):
        row = self.rows.get(str(code).strip().lower())
        if row is None:
            return None
        row["active"] = active
        row["updated_at"] = datetime(2026, 2, 3, tzinfo=timezone.utc)
        return row


def _service(repo: FakeReasonAdminRepo) -> MesDowntimeReasonAdminService:
    return MesDowntimeReasonAdminService(reasons=repo)


class TestAdminService:
    def test_list_returns_all_sorted(self):
        data = _service(FakeReasonAdminRepo()).list_reasons()
        codes = [item["code"] for item in data["items"]]
        assert codes == ["raw_material", "setup", "other", "obsolete"]
        item = data["items"][0]
        assert set(item) == {
            "code", "label", "category", "requiresNote",
            "active", "sortOrder", "createdAt", "updatedAt",
        }
        assert "default_planned" not in item
        assert "counts_as_availability_loss" not in item

    def test_create_normalizes_and_is_born_active(self):
        repo = FakeReasonAdminRepo()
        item = _service(repo).create_reason(
            code=" Operator_Training ", label="  Treinamento do operador  ",
            category=" PEOPLE ", requires_note=False, sort_order=120,
        )
        assert item["code"] == "operator_training"
        assert item["label"] == "Treinamento do operador"
        assert item["category"] == "people"
        assert item["active"] is True
        assert repo.rows["operator_training"]["default_planned"] is None
        assert repo.rows["operator_training"]["default_counts_as_availability_loss"] is None

    @pytest.mark.parametrize("code", ["", "   ", "Raw Material", "falta-material", "motivo@", "a" * 41, "_lead", "trail_"])
    def test_create_rejects_invalid_code(self, code):
        with pytest.raises(InvalidDowntimeReason):
            _service(FakeReasonAdminRepo()).create_reason(
                code=code, label="Ok", category="people", requires_note=False, sort_order=1,
            )

    def test_create_duplicate_conflicts(self):
        with pytest.raises(DowntimeReasonConflict):
            _service(FakeReasonAdminRepo()).create_reason(
                code="RAW_MATERIAL", label="Outra", category="material",
                requires_note=False, sort_order=1,
            )

    def test_create_rejects_empty_label_and_category(self):
        svc = _service(FakeReasonAdminRepo())
        with pytest.raises(InvalidDowntimeReason):
            svc.create_reason(code="x_ok", label="  ", category="people", requires_note=False, sort_order=1)
        with pytest.raises(InvalidDowntimeReason):
            svc.create_reason(code="x_ok", label="Ok", category=" ", requires_note=False, sort_order=1)

    @pytest.mark.parametrize("sort_order", [-1, 1.5, "10", True])
    def test_create_rejects_bad_sort_order(self, sort_order):
        with pytest.raises(InvalidDowntimeReason):
            _service(FakeReasonAdminRepo()).create_reason(
                code="x_ok", label="Ok", category="people", requires_note=False, sort_order=sort_order,
            )

    def test_create_rejects_non_boolean_requires_note(self):
        with pytest.raises(InvalidDowntimeReason):
            _service(FakeReasonAdminRepo()).create_reason(
                code="x_ok", label="Ok", category="people", requires_note="yes", sort_order=1,
            )

    def test_update_edits_admin_fields_only(self):
        repo = FakeReasonAdminRepo()
        item = _service(repo).update_reason(
            " raw_material ", label="Falta de matéria-prima", category=" MATERIAL ",
            requires_note=True, sort_order=41,
        )
        assert item["code"] == "raw_material"
        assert item["label"] == "Falta de matéria-prima"
        assert item["category"] == "material"
        assert item["requiresNote"] is True
        assert item["sortOrder"] == 41
        assert repo.rows["raw_material"]["default_planned"] is None
        assert repo.rows["raw_material"]["created_at"].year == 2026
        assert repo.rows["raw_material"]["created_at"].month == 1

    def test_update_missing_raises_not_found(self):
        with pytest.raises(DowntimeReasonNotFound):
            _service(FakeReasonAdminRepo()).update_reason(
                "ghost", label="x", category="other", requires_note=False, sort_order=1,
            )

    def test_set_active_toggle(self):
        repo = FakeReasonAdminRepo()
        svc = _service(repo)
        assert svc.set_reason_active("raw_material", active=False)["active"] is False
        assert repo.get("raw_material")["active"] is False
        assert svc.set_reason_active("raw_material", active=True)["active"] is True

    def test_set_active_missing_raises_not_found(self):
        with pytest.raises(DowntimeReasonNotFound):
            _service(FakeReasonAdminRepo()).set_reason_active("ghost", active=False)

    def test_setup_cannot_be_deactivated(self):
        with pytest.raises(DowntimeReasonConflict):
            _service(FakeReasonAdminRepo()).set_reason_active("SETUP", active=False)

    def test_setup_can_be_edited_and_activated(self):
        svc = _service(FakeReasonAdminRepo())
        item = svc.update_reason("setup", label="Setup", category="setup", requires_note=False, sort_order=60)
        assert item["code"] == "setup"
        assert svc.set_reason_active("setup", active=True)["active"] is True


class TestCockpitRegression:
    def test_classification_list_reasons_uses_active_only(self):
        repo = FakeReasonAdminRepo()
        svc = MesDowntimeClassificationService(
            run_service=None, downtimes=None, reasons=repo
        )
        codes = [row["code"] for row in svc.list_reasons()]
        assert "obsolete" not in codes
        assert codes == ["raw_material", "setup", "other"]
        # Desativar → sai do cockpit; reativar → volta.
        repo.set_active("raw_material", active=False)
        assert "raw_material" not in [row["code"] for row in svc.list_reasons()]
        repo.set_active("raw_material", active=True)
        assert "raw_material" in [row["code"] for row in svc.list_reasons()]


# ---------------------------------------------------------------------------
# HTTP S2S
# ---------------------------------------------------------------------------

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from production_control_app.interface.http.routes import integration_mes_routes  # noqa: E402


class FakeHttpAdminService:
    def __init__(self) -> None:
        self._repo = FakeReasonAdminRepo()
        self._svc = MesDowntimeReasonAdminService(reasons=self._repo)

    def list_reasons(self):
        return self._svc.list_reasons()

    def create_reason(self, **kwargs):
        return self._svc.create_reason(**kwargs)

    def update_reason(self, code, **kwargs):
        return self._svc.update_reason(code, **kwargs)

    def set_reason_active(self, code, *, active):
        return self._svc.set_reason_active(code, active=active)


def _client(monkeypatch, service=None):
    app = FastAPI()
    app.include_router(integration_mes_routes.router)
    fake = service or FakeHttpAdminService()
    monkeypatch.setattr(
        integration_mes_routes,
        "build_mes_downtime_reason_admin_service",
        lambda: fake,
    )
    return TestClient(app)


def _auth(monkeypatch):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "internal-secret")
    return {"X-Delpi-Service-Token": "internal-secret", "X-Delpi-Caller-App": "delpi-mes-api"}


def test_admin_requires_service_token(monkeypatch):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "internal-secret")
    api = _client(monkeypatch)
    for response in [
        api.get("/integrations/mes/downtime-reasons"),
        api.get("/integrations/mes/downtime-reasons", headers={"X-Delpi-Service-Token": "wrong"}),
        api.get("/integrations/mes/downtime-reasons", headers={"Authorization": "Bearer human-jwt"}),
    ]:
        assert response.status_code == 401


def test_admin_full_flow(monkeypatch):
    headers = _auth(monkeypatch)
    api = _client(monkeypatch)

    listing = api.get("/integrations/mes/downtime-reasons", headers=headers)
    assert listing.status_code == 200
    assert {item["code"] for item in listing.json()["data"]["items"]} >= {"raw_material", "obsolete"}
    assert "internal-secret" not in listing.text

    created = api.post(
        "/integrations/mes/downtime-reasons",
        headers=headers,
        json={"code": "Operator_Training", "label": "Treinamento do operador", "category": "People", "requiresNote": False, "sortOrder": 120},
    )
    assert created.status_code == 201
    assert created.json()["data"]["code"] == "operator_training"
    assert created.json()["data"]["active"] is True

    duplicated = api.post(
        "/integrations/mes/downtime-reasons",
        headers=headers,
        json={"code": "operator_training", "label": "Outro", "category": "people", "requiresNote": False},
    )
    assert duplicated.status_code == 409

    updated = api.put(
        "/integrations/mes/downtime-reasons/operator_training",
        headers=headers,
        json={"label": "Treinamento", "category": "people", "requiresNote": True, "sortOrder": 121},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["requiresNote"] is True

    missing = api.put(
        "/integrations/mes/downtime-reasons/ghost",
        headers=headers,
        json={"label": "x", "category": "other", "requiresNote": False},
    )
    assert missing.status_code == 404

    disabled = api.patch(
        "/integrations/mes/downtime-reasons/operator_training/active",
        headers=headers,
        json={"active": False},
    )
    assert disabled.status_code == 200
    assert disabled.json()["data"]["active"] is False
    assert api.patch(
        "/integrations/mes/downtime-reasons/operator_training/active",
        headers=headers, json={"active": True},
    ).json()["data"]["active"] is True

    # Desativado continua listado na visão administrativa.
    api.patch("/integrations/mes/downtime-reasons/operator_training/active", headers=headers, json={"active": False})
    codes = {item["code"]: item["active"] for item in api.get("/integrations/mes/downtime-reasons", headers=headers).json()["data"]["items"]}
    assert codes["operator_training"] is False


def test_admin_setup_protected_and_invalid_payload(monkeypatch):
    headers = _auth(monkeypatch)
    api = _client(monkeypatch)
    assert api.patch("/integrations/mes/downtime-reasons/setup/active", headers=headers, json={"active": False}).status_code == 409
    assert api.patch("/integrations/mes/downtime-reasons/setup/active", headers=headers, json={"active": True}).status_code == 200

    invalid_code = api.post(
        "/integrations/mes/downtime-reasons", headers=headers,
        json={"code": "falta-material", "label": "x", "category": "other", "requiresNote": False},
    )
    assert invalid_code.status_code == 422

    extra_field = api.post(
        "/integrations/mes/downtime-reasons", headers=headers,
        json={"code": "new_reason", "label": "x", "category": "other", "requiresNote": False, "defaultPlanned": True},
    )
    assert extra_field.status_code == 422

    rename_attempt = api.put(
        "/integrations/mes/downtime-reasons/raw_material", headers=headers,
        json={"code": "renamed", "label": "x", "category": "other", "requiresNote": False},
    )
    assert rename_attempt.status_code == 422


# ---------------------------------------------------------------------------
# Integração Postgres — PC_TEST_MES_DB=1 + PLUGINS_DB_*
# ---------------------------------------------------------------------------

_DB_REQUIRED = pytest.mark.skipif(
    os.getenv("PC_TEST_MES_DB") != "1",
    reason="Testes de persistência MES exigem PC_TEST_MES_DB=1 e PLUGINS_DB_*",
)


@_DB_REQUIRED
class TestReasonAdminPostgres:
    @pytest.fixture()
    def repo(self):
        from production_control_app.infrastructure.persistence.postgres_mes_repository import (  # noqa: E501
            PostgresDowntimeReasonRepository,
        )

        return PostgresDowntimeReasonRepository()

    @pytest.fixture()
    def temp_code(self):
        from production_control_app.infrastructure.persistence.plugins_postgres_connection import (  # noqa: E501
            PC_SCHEMA_NAME,
            get_connection,
        )

        code = "zz_admin_test"

        def _clean() -> None:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"DELETE FROM {PC_SCHEMA_NAME}.downtime_events WHERE reason_code = %s",
                        (code,),
                    )
                    cur.execute(
                        f"DELETE FROM {PC_SCHEMA_NAME}.downtime_reason_catalog WHERE code = %s",
                        (code,),
                    )
                conn.commit()

        _clean()
        yield code
        _clean()

    def test_crud_and_history_preservation(self, repo, temp_code):
        from production_control_app.infrastructure.persistence.plugins_postgres_connection import (  # noqa: E501
            PC_SCHEMA_NAME,
            get_connection,
        )

        created = repo.create(
            code=temp_code, label="Motivo de teste", category="other",
            requires_note=False, sort_order=995,
        )
        assert created["active"] is True
        assert created["default_planned"] is None
        assert created["default_counts_as_availability_loss"] is None

        with pytest.raises(DowntimeReasonConflict):
            repo.create(
                code=temp_code, label="Duplicado", category="other",
                requires_note=False, sort_order=995,
            )

        updated = repo.update(
            temp_code, label="Motivo de teste v2", category="planned",
            requires_note=True, sort_order=996,
        )
        assert updated["label"] == "Motivo de teste v2"
        assert updated["category"] == "planned"
        assert updated["updated_at"] > created["updated_at"]
        assert repo.update(
            "zz_ghost", label="x", category="other",
            requires_note=False, sort_order=0,
        ) is None

        # Histórico: parada classificada com o motivo, depois motivo desativado.
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO {PC_SCHEMA_NAME}.downtime_events (
                        branch, work_center, started_at, reason_code, source
                    ) VALUES ('01', 'ZZ-REASON-TEST', NOW(), %s, 'system')
                    RETURNING id::text AS id
                    """,
                    (temp_code,),
                )
                downtime_id = cur.fetchone()["id"]
            conn.commit()

        disabled = repo.set_active(temp_code, active=False)
        assert disabled["active"] is False
        assert temp_code not in [row["code"] for row in repo.list_active()]
        assert temp_code in [row["code"] for row in repo.list_all()]

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT reason_code FROM {PC_SCHEMA_NAME}.downtime_events WHERE id = %s",
                    (downtime_id,),
                )
                assert cur.fetchone()["reason_code"] == temp_code

        reactivated = repo.set_active(temp_code, active=True)
        assert reactivated["active"] is True
        assert temp_code in [row["code"] for row in repo.list_active()]
