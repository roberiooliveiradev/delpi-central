"""Fase 3A.1 — filiais + centros de custo branch-aware."""
from __future__ import annotations

from copy import deepcopy
from typing import Any
from uuid import uuid4

import pytest

from app.application.use_cases.planejamento_orcamentario.budget_planning_use_cases import (
    BudgetActor,
    BudgetPlanningUseCases,
)
from app.application.use_cases.planejamento_orcamentario.budget_responsibility_use_cases import (
    BudgetResponsibilityUseCases,
)
from app.domain.services.planejamento_orcamentario.exceptions import (
    BudgetCostCenterConflictError,
    BudgetCostCenterInvalidError,
    BudgetCostCenterNotFoundError,
    BudgetResponsibilityConflictError,
    BudgetResponsibilityInvalidError,
)
from app.domain.services.planejamento_orcamentario.org_cost_center_constants import (
    COST_CENTER_SOURCE_ERP,
    normalize_budget_branch,
    serialize_org_cost_center,
)
from app.domain.services.planejamento_orcamentario.org_cost_center_resolution import (
    authorized_unit_cost_center_pairs,
    resolve_org_cost_center,
)
from app.infrastructure.persistence.totvs.financeiro_despesas_centro_custo.despesas_centro_custo_sql import (
    build_centros_custo_catalog_by_branch_query,
)


def _admin() -> BudgetActor:
    return BudgetActor(
        user_id="admin-1",
        user_name="Admin",
        permissions=frozenset({"planejamento-orcamentario.admin"}),
    )


class FakeErp:
    def __init__(self, items: list[dict[str, Any]] | None = None) -> None:
        self.items = items or [
            {"branch": "01", "code": "1234", "description": "Produção SC"},
            {"branch": "01", "code": "205", "description": "TI SC"},
            {"branch": "02", "code": "1234", "description": "Produção ES"},
            {"branch": "02", "code": "999", "description": "Só ES"},
        ]

    def list_centros_custo_by_branch(self, *, branch: str) -> list[dict]:
        return [deepcopy(i) for i in self.items if i["branch"] == branch]


class FakeRepo:
    def __init__(self) -> None:
        self.units = {
            "01": {"code": "01", "name": "SC", "active": True},
            "02": {"code": "02", "name": "ES", "active": True},
        }
        self.areas: dict[str, dict] = {}
        self.ccs: dict[tuple[str, str], dict] = {}
        self.exercises: dict[str, dict] = {}
        self.responsibilities: dict[str, dict] = {}
        self.investments: dict[str, dict] = {}
        self.plans: dict[str, dict] = {}
        self.audits: list[dict] = []

    def list_org_units(self, *, active_only: bool = True):
        return list(self.units.values())

    def list_org_areas(self, *, active_only: bool = True):
        return list(self.areas.values())

    def list_org_cost_centers(self, *, active_only: bool = True, branch: str | None = None):
        rows = list(self.ccs.values())
        if branch:
            rows = [r for r in rows if r["branch"] == branch]
        if active_only:
            rows = [r for r in rows if r.get("active", True)]
        return deepcopy(rows)

    def upsert_org_unit(self, code: str, name: str) -> None:
        self.units[code] = {"code": code, "name": name, "active": True}

    def upsert_org_area(self, code: str, name: str, unit_code: str | None) -> None:
        self.areas[code] = {
            "code": code,
            "name": name,
            "unit_code": unit_code,
            "active": True,
        }

    def upsert_org_cost_center(self, payload: dict[str, Any]) -> dict[str, Any]:
        branch = payload["branch"]
        code = payload["code"]
        key = (branch, code)
        existing = self.ccs.get(key)
        row = {
            "id": (existing or {}).get("id") or str(uuid4()),
            "branch": branch,
            "code": code,
            "name": payload["name"],
            "unit_code": payload["unit_code"],
            "area_code": payload.get("area_code"),
            "source": payload.get("source") or "manual",
            "icon_key": (existing or {}).get("icon_key"),
            "active": True,
            "created_by_user_id": payload.get("created_by_user_id"),
        }
        self.ccs[key] = row
        return deepcopy(row)

    def update_org_cost_center_icon(
        self, *, branch: str, code: str, icon_key: str | None
    ) -> dict[str, Any] | None:
        key = (branch, code)
        existing = self.ccs.get(key)
        if not existing:
            return None
        updated = {**existing, "icon_key": icon_key}
        self.ccs[key] = updated
        return deepcopy(updated)

    def get_org_unit(self, code: str):
        return deepcopy(self.units.get(code))

    def get_org_area(self, code: str):
        return deepcopy(self.areas.get(code))

    def get_org_cost_center(self, code: str, *, branch: str | None = None):
        if branch:
            return deepcopy(self.ccs.get((branch, code)))
        matches = self.list_org_cost_centers_by_code(code)
        if len(matches) != 1:
            return None
        return matches[0]

    def list_org_cost_centers_by_code(self, code: str):
        return deepcopy([r for (b, c), r in self.ccs.items() if c == code])

    def get_exercise(self, exercise_id: str):
        return deepcopy(self.exercises.get(exercise_id))

    def find_active_budget_responsibility_conflict(
        self, *, exercise_id, module, user_sub, cost_center_id, unit_id=None, exclude_id=None
    ):
        for rid, r in self.responsibilities.items():
            if exclude_id and rid == exclude_id:
                continue
            if not r.get("is_active"):
                continue
            if (
                r["exercise_id"] == exercise_id
                and r["module"] == module
                and r["user_sub"] == user_sub
                and r["cost_center_id"] == cost_center_id
                and (unit_id is None or r["unit_id"] == unit_id)
            ):
                return deepcopy(r)
        return None

    def create_budget_responsibility(self, payload: dict[str, Any]) -> dict[str, Any]:
        rid = str(uuid4())
        row = {**payload, "id": rid, "is_active": True}
        self.responsibilities[rid] = row
        return deepcopy(row)

    def append_audit(self, **kwargs) -> None:
        self.audits.append(kwargs)

    def create_capex_investment(self, payload: dict[str, Any]) -> dict[str, Any]:
        iid = str(uuid4())
        row = {**payload, "id": iid, "status": "draft", "version": 1}
        self.investments[iid] = row
        return deepcopy(row)

    def list_capex_investments(self, **kwargs):
        items = list(self.investments.values())
        pairs = kwargs.get("unit_cost_center_pairs")
        if pairs is not None:
            allowed = set(pairs)
            items = [i for i in items if (i["unit_id"], i["cost_center_id"]) in allowed]
        if kwargs.get("unit_id"):
            items = [i for i in items if i["unit_id"] == kwargs["unit_id"]]
        if kwargs.get("cost_center_id"):
            items = [i for i in items if i["cost_center_id"] == kwargs["cost_center_id"]]
        return deepcopy(items), len(items)

    def get_capex_plan_by_exercise_cc(self, *, exercise_id, cost_center_id, unit_id=None):
        for p in self.plans.values():
            if p["exercise_id"] != exercise_id or p["cost_center_id"] != cost_center_id:
                continue
            if unit_id and p["unit_id"] != unit_id:
                continue
            return deepcopy(p)
        return None

    def create_capex_plan(self, payload: dict[str, Any]) -> dict[str, Any]:
        pid = str(uuid4())
        row = {**payload, "id": pid, "status": "draft", "version": 1}
        self.plans[pid] = row
        return deepcopy(row)

    def append_capex_plan_history(self, payload: dict[str, Any]) -> dict[str, Any]:
        return payload

    def list_budget_responsibilities_for_user(self, **kwargs):
        return [
            deepcopy(r)
            for r in self.responsibilities.values()
            if r["user_sub"] == kwargs.get("user_sub")
            and (not kwargs.get("module") or r["module"] == kwargs["module"])
            and (not kwargs.get("exercise_id") or r["exercise_id"] == kwargs["exercise_id"])
            and (not kwargs.get("active_only") or r.get("is_active", True))
        ]


def test_normalize_budget_branch_accepts_only_01_02():
    assert normalize_budget_branch("01") == "01"
    assert normalize_budget_branch("02") == "02"
    with pytest.raises(ValueError):
        normalize_budget_branch("03")
    with pytest.raises(ValueError):
        normalize_budget_branch("all")


def test_same_code_can_exist_in_both_branches():
    repo = FakeRepo()
    repo.upsert_org_cost_center(
        {
            "branch": "01",
            "code": "1234",
            "name": "Produção SC",
            "unit_code": "01",
            "source": "erp",
        }
    )
    repo.upsert_org_cost_center(
        {
            "branch": "02",
            "code": "1234",
            "name": "Produção ES",
            "unit_code": "02",
            "source": "erp",
        }
    )
    assert repo.get_org_cost_center("1234", branch="01")["name"] == "Produção SC"
    assert repo.get_org_cost_center("1234", branch="02")["name"] == "Produção ES"
    assert len(repo.list_org_cost_centers_by_code("1234")) == 2
    with pytest.raises(Exception):
        resolve_org_cost_center(repo, code="1234")
    sc = resolve_org_cost_center(repo, code="1234", branch="01")
    assert serialize_org_cost_center(sc)["branch"] == "01"


def test_duplicate_same_branch_code_conflict_on_from_erp():
    repo = FakeRepo()
    erp = FakeErp()
    uc = BudgetPlanningUseCases(repository=repo, erp_cost_centers=erp)  # type: ignore[arg-type]
    uc.create_org_cost_center_from_erp(
        _admin(), {"branch": "01", "code": "1234", "unit_id": "01"}
    )
    with pytest.raises(BudgetCostCenterConflictError):
        uc.create_org_cost_center_from_erp(
            _admin(), {"branch": "01", "code": "1234", "unit_id": "01"}
        )


def test_from_erp_rejects_invalid_branch_and_free_description():
    repo = FakeRepo()
    erp = FakeErp()
    uc = BudgetPlanningUseCases(repository=repo, erp_cost_centers=erp)  # type: ignore[arg-type]
    with pytest.raises(BudgetCostCenterInvalidError):
        uc.create_org_cost_center_from_erp(
            _admin(), {"branch": "99", "code": "1234", "unit_id": "99"}
        )
    with pytest.raises(BudgetCostCenterInvalidError):
        uc.create_org_cost_center_from_erp(
            _admin(),
            {
                "branch": "01",
                "code": "1234",
                "unit_id": "01",
                "name": "Livre",
            },
        )


def test_from_erp_rejects_missing_erp_code_and_unit_mismatch():
    repo = FakeRepo()
    erp = FakeErp()
    uc = BudgetPlanningUseCases(repository=repo, erp_cost_centers=erp)  # type: ignore[arg-type]
    with pytest.raises(BudgetCostCenterNotFoundError):
        uc.create_org_cost_center_from_erp(
            _admin(), {"branch": "01", "code": "0000", "unit_id": "01"}
        )
    with pytest.raises(BudgetCostCenterInvalidError):
        uc.create_org_cost_center_from_erp(
            _admin(), {"branch": "01", "code": "1234", "unit_id": "02"}
        )


def test_from_erp_registers_snapshot_and_source():
    repo = FakeRepo()
    erp = FakeErp()
    uc = BudgetPlanningUseCases(repository=repo, erp_cost_centers=erp)  # type: ignore[arg-type]
    created = uc.create_org_cost_center_from_erp(
        _admin(), {"branch": "02", "code": "1234", "unit_id": "02"}
    )
    assert created["branch"] == "02"
    assert created["code"] == "1234"
    assert created["description"] == "Produção ES"
    assert created["source"] == COST_CENTER_SOURCE_ERP
    assert any(a["action"] == "org_cost_center.from_erp" for a in repo.audits)


def test_update_org_cost_center_icon_sets_and_clears():
    """update_planejamento_orcamentario_admin_cost_center_icon — catálogo Lucide."""
    repo = FakeRepo()
    erp = FakeErp()
    uc = BudgetPlanningUseCases(repository=repo, erp_cost_centers=erp)  # type: ignore[arg-type]
    uc.create_org_cost_center_from_erp(
        _admin(), {"branch": "01", "code": "205", "unit_id": "01"}
    )
    updated = uc.update_org_cost_center_icon(
        _admin(), {"branch": "01", "code": "205", "icon_key": "laptop"}
    )
    assert updated["icon_key"] == "laptop"
    assert any(a["action"] == "org_cost_center.icon_updated" for a in repo.audits)
    cleared = uc.update_org_cost_center_icon(
        _admin(), {"branch": "01", "code": "205", "icon_key": None}
    )
    assert cleared["icon_key"] is None


def test_update_org_cost_center_icon_rejects_unknown_key():
    repo = FakeRepo()
    erp = FakeErp()
    uc = BudgetPlanningUseCases(repository=repo, erp_cost_centers=erp)  # type: ignore[arg-type]
    uc.create_org_cost_center_from_erp(
        _admin(), {"branch": "01", "code": "205", "unit_id": "01"}
    )
    with pytest.raises(BudgetCostCenterInvalidError):
        uc.update_org_cost_center_icon(
            _admin(), {"branch": "01", "code": "205", "icon_key": "not-a-real-icon"}
        )


def test_list_erp_cost_centers_filtered_by_branch():
    repo = FakeRepo()
    erp = FakeErp()
    uc = BudgetPlanningUseCases(repository=repo, erp_cost_centers=erp)  # type: ignore[arg-type]
    items = uc.list_erp_cost_centers(branch="01")
    assert all(i["branch"] == "01" for i in items)
    assert {i["code"] for i in items} == {"1234", "205"}
    assert "999" not in {i["code"] for i in items}


def test_build_centros_custo_catalog_query_filters_branch_only():
    query, params = build_centros_custo_catalog_by_branch_query(branch="02")
    assert "dbo.vw_fin_despesas_centro_custo" in query
    assert "LTRIM(RTRIM(filial)) = ?" in query
    assert "data_emissao" not in query
    assert params == ("02",)


def test_responsibilities_separated_by_branch():
    repo = FakeRepo()
    for branch, name in (("01", "SC"), ("02", "ES")):
        repo.upsert_org_cost_center(
            {
                "branch": branch,
                "code": "205",
                "name": name,
                "unit_code": branch,
                "source": "erp",
            }
        )
    exercise_id = str(uuid4())
    repo.exercises[exercise_id] = {"id": exercise_id, "status": "open", "year": 2027}
    uc = BudgetResponsibilityUseCases(repository=repo)  # type: ignore[arg-type]
    actor = _admin()
    r01 = uc.create_responsibility(
        actor,
        {
            "exercise_id": exercise_id,
            "module": "capex",
            "user_sub": "user-a",
            "unit_id": "01",
            "cost_center_id": "205",
            "responsibility_type": "owner",
        },
    )
    r02 = uc.create_responsibility(
        actor,
        {
            "exercise_id": exercise_id,
            "module": "capex",
            "user_sub": "user-a",
            "unit_id": "02",
            "cost_center_id": "205",
            "responsibility_type": "owner",
        },
    )
    assert r01["branch"] == "01"
    assert r02["branch"] == "02"
    assert r01["id"] != r02["id"]
    with pytest.raises(BudgetResponsibilityConflictError):
        uc.create_responsibility(
            actor,
            {
                "exercise_id": exercise_id,
                "module": "capex",
                "user_sub": "user-a",
                "unit_id": "01",
                "cost_center_id": "205",
                "responsibility_type": "collaborator",
            },
        )


def test_unit_incompatible_with_cost_center():
    repo = FakeRepo()
    repo.upsert_org_cost_center(
        {
            "branch": "01",
            "code": "205",
            "name": "TI",
            "unit_code": "01",
            "source": "manual",
        }
    )
    exercise_id = str(uuid4())
    repo.exercises[exercise_id] = {"id": exercise_id, "status": "open", "year": 2027}
    uc = BudgetResponsibilityUseCases(repository=repo)  # type: ignore[arg-type]
    with pytest.raises(BudgetResponsibilityInvalidError):
        uc.create_responsibility(
            _admin(),
            {
                "exercise_id": exercise_id,
                "module": "capex",
                "user_sub": "user-a",
                "unit_id": "02",
                "cost_center_id": "205",
                "responsibility_type": "owner",
            },
        )


def test_authorized_pairs_do_not_leak_across_branches():
    pairs = authorized_unit_cost_center_pairs(
        [
            {"unit_id": "01", "cost_center_id": "205", "is_active": True},
            {"unit_id": "02", "cost_center_id": "999", "is_active": True},
        ]
    )
    assert ("01", "205") in pairs
    assert ("02", "205") not in pairs
    assert ("02", "999") in pairs


def test_plans_and_investments_separated_by_branch_keys():
    repo = FakeRepo()
    for branch in ("01", "02"):
        repo.upsert_org_cost_center(
            {
                "branch": branch,
                "code": "205",
                "name": f"CC {branch}",
                "unit_code": branch,
                "source": "erp",
            }
        )
    exercise_id = str(uuid4())
    repo.exercises[exercise_id] = {"id": exercise_id, "status": "open", "year": 2027}
    p01 = repo.create_capex_plan(
        {
            "exercise_id": exercise_id,
            "unit_id": "01",
            "area_id": None,
            "cost_center_id": "205",
            "created_by": "u1",
        }
    )
    p02 = repo.create_capex_plan(
        {
            "exercise_id": exercise_id,
            "unit_id": "02",
            "area_id": None,
            "cost_center_id": "205",
            "created_by": "u1",
        }
    )
    assert p01["id"] != p02["id"]
    assert (
        repo.get_capex_plan_by_exercise_cc(
            exercise_id=exercise_id, cost_center_id="205", unit_id="01"
        )["id"]
        == p01["id"]
    )
    repo.create_capex_investment(
        {
            "exercise_id": exercise_id,
            "unit_id": "01",
            "cost_center_id": "205",
            "description": "A",
            "created_by": "u1",
        }
    )
    repo.create_capex_investment(
        {
            "exercise_id": exercise_id,
            "unit_id": "02",
            "cost_center_id": "205",
            "description": "B",
            "created_by": "u1",
        }
    )
    only_01, _ = repo.list_capex_investments(unit_cost_center_pairs=[("01", "205")])
    assert len(only_01) == 1
    assert only_01[0]["description"] == "A"
