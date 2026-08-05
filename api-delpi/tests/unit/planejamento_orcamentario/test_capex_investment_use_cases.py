"""Testes Fase 2B.1 — itens de investimento CAPEX (repositório fake)."""
from __future__ import annotations

from copy import deepcopy
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import uuid4

import pytest

from app.application.use_cases.planejamento_orcamentario.budget_planning_use_cases import (
    BudgetActor,
)
from app.application.use_cases.planejamento_orcamentario.capex_investment_use_cases import (
    CapexInvestmentUseCases,
)
from app.domain.services.planejamento_orcamentario.exceptions import (
    BudgetGuidanceAcknowledgementRequiredError,
    CapexInvestmentArchivedError,
    CapexInvestmentCategoryInvalidError,
    CapexInvestmentCostCenterForbiddenError,
    CapexInvestmentDateInvalidError,
    CapexInvestmentNotFoundError,
    CapexInvestmentValueInvalidError,
    CapexInvestmentVersionConflictError,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import PluginsRepositoryError
from tests.unit.planejamento_orcamentario.fake_po_repository_helpers import (
    default_po_cc_seed,
    filter_unit_cost_center_pairs,
    find_valid_responsibility_in_rows,
    get_capex_plan_by_exercise_cc_from_plans,
    get_org_cost_center_from_store,
    list_org_cost_centers_by_code_from_store,
)


class FakeRepo:
    def __init__(self) -> None:
        self.exercises: dict[str, dict] = {}
        self.active_exercise_id: str | None = None
        self.guidance: dict[str, dict] = {}
        self.acks: set[tuple[str, str]] = set()
        self.units = {"01": {"code": "01", "name": "SC", "active": True}}
        self.areas = {
            "PROD": {"code": "PROD", "name": "Produção", "unit_code": "01", "active": True}
        }
        self.ccs: dict[tuple[str, str], dict] = default_po_cc_seed()
        self.categories: dict[str, dict] = {}
        self.responsibilities: list[dict] = []
        self.investments: dict[str, dict] = {}
        self.audits: list[dict] = []
        self.plans: dict[str, dict] = {}

    def get_capex_plan_by_exercise_cc(
        self, *, exercise_id: str, cost_center_id: str, unit_id: str | None = None
    ):
        return get_capex_plan_by_exercise_cc_from_plans(
            self.plans,
            exercise_id=exercise_id,
            cost_center_id=cost_center_id,
            unit_id=unit_id,
        )

    def seed_exercise(self, *, status: str = "open") -> str:
        eid = str(uuid4())
        self.exercises[eid] = {
            "id": eid,
            "year": 2027,
            "name": "PO 2027",
            "status": status,
            "is_active": True,
        }
        self.active_exercise_id = eid
        return eid

    def seed_guidance(self, exercise_id: str) -> str:
        gid = str(uuid4())
        self.guidance[exercise_id] = {
            "id": gid,
            "exercise_id": exercise_id,
            "version_number": 1,
            "title": "Carta",
            "published_at": "2026-01-01T00:00:00Z",
        }
        return gid

    def seed_category(self, *, active: bool = True) -> str:
        cid = str(uuid4())
        self.categories[cid] = {
            "id": cid,
            "code": f"CAT_{cid[:6]}",
            "name": "Ferramentas",
            "is_active": active,
            "is_system_default": True,
            "display_order": 20,
        }
        return cid

    def seed_responsibility(self, *, user_sub: str, exercise_id: str, cost_center_id: str):
        self.responsibilities.append(
            {
                "id": str(uuid4()),
                "user_sub": user_sub,
                "exercise_id": exercise_id,
                "module": "capex",
                "cost_center_id": cost_center_id,
                "unit_id": "01",
                "area_id": "PROD",
                "is_active": True,
                "valid_from": None,
                "valid_until": None,
            }
        )

    def get_exercise(self, exercise_id: str):
        return deepcopy(self.exercises.get(exercise_id))

    def get_active_exercise(self):
        if not self.active_exercise_id:
            return None
        return deepcopy(self.exercises.get(self.active_exercise_id))

    def get_current_published_guidance(self, exercise_id: str):
        return deepcopy(self.guidance.get(exercise_id))

    def get_acknowledgement(self, *, user_sub: str, guidance_version_id: str):
        if (user_sub, guidance_version_id) in self.acks:
            return {"user_sub": user_sub, "guidance_version_id": guidance_version_id}
        return None

    def get_org_cost_center(self, code: str, *, branch: str | None = None):
        return get_org_cost_center_from_store(self.ccs, code, branch=branch)

    def list_org_cost_centers_by_code(self, code: str):
        return list_org_cost_centers_by_code_from_store(self.ccs, code)

    def get_org_unit(self, code: str):
        return deepcopy(self.units.get(code))

    def get_org_area(self, code: str):
        return deepcopy(self.areas.get(code))

    def get_capex_category(self, category_id: str):
        return deepcopy(self.categories.get(category_id))

    def find_valid_responsibility(
        self,
        *,
        user_sub,
        exercise_id,
        module,
        cost_center_id,
        unit_id=None,
        on_date=None,
    ):
        return find_valid_responsibility_in_rows(
            self.responsibilities,
            user_sub=user_sub,
            exercise_id=exercise_id,
            module=module,
            cost_center_id=cost_center_id,
            unit_id=unit_id,
            on_date=on_date,
        )

    def list_budget_responsibilities_for_user(self, **kwargs):
        items = []
        for r in self.responsibilities:
            if r["user_sub"] != kwargs["user_sub"]:
                continue
            if kwargs.get("module") and r["module"] != kwargs["module"]:
                continue
            if kwargs.get("exercise_id") and r["exercise_id"] != kwargs["exercise_id"]:
                continue
            if kwargs.get("active_only", True) and not r["is_active"]:
                continue
            items.append(deepcopy(r))
        return items

    def get_capex_investment(self, investment_id: str):
        return deepcopy(self.investments.get(investment_id))

    def list_capex_investments(self, **kwargs):
        items = list(self.investments.values())
        if kwargs.get("exercise_id"):
            items = [i for i in items if i["exercise_id"] == kwargs["exercise_id"]]
        if kwargs.get("unit_id"):
            items = [i for i in items if i.get("unit_id") == kwargs["unit_id"]]
        if kwargs.get("cost_center_id"):
            items = [i for i in items if i["cost_center_id"] == kwargs["cost_center_id"]]
        items = filter_unit_cost_center_pairs(
            items, kwargs.get("unit_cost_center_pairs")
        )
        if kwargs.get("cost_center_ids") is not None and kwargs.get("unit_cost_center_pairs") is None:
            allowed = set(kwargs["cost_center_ids"])
            items = [i for i in items if i["cost_center_id"] in allowed]
        if kwargs.get("category_id"):
            items = [i for i in items if i.get("category_id") == kwargs["category_id"]]
        if kwargs.get("priority"):
            items = [i for i in items if i.get("priority") == kwargs["priority"]]
        if kwargs.get("origin"):
            items = [i for i in items if i.get("origin") == kwargs["origin"]]
        if kwargs.get("status"):
            items = [i for i in items if i.get("status") == kwargs["status"]]
        if kwargs.get("q"):
            ql = kwargs["q"].lower()
            items = [
                i
                for i in items
                if ql in (i.get("description") or "").lower()
                or ql in (i.get("probable_supplier_name") or "").lower()
            ]
        total = len(items)
        offset = kwargs.get("offset", 0)
        limit = kwargs.get("limit", 50)
        return deepcopy(items[offset : offset + limit]), total

    def create_capex_investment(self, payload: dict[str, Any]):
        iid = str(uuid4())
        row = {
            **payload,
            "id": iid,
            "version": 1,
            "created_at": "t",
            "updated_at": "t",
            "archived_by": None,
            "archived_at": None,
        }
        if isinstance(row.get("estimated_amount"), Decimal):
            row["estimated_amount"] = str(row["estimated_amount"])
        if isinstance(row.get("required_date"), date):
            row["required_date"] = row["required_date"].isoformat()
        self.investments[iid] = row
        return deepcopy(row)

    def update_capex_investment(self, investment_id, fields, *, expected_version):
        row = self.investments.get(investment_id)
        if not row:
            raise PluginsRepositoryError("Investimento CAPEX não encontrado.")
        if row["status"] != "draft":
            raise PluginsRepositoryError("Investimento arquivado não pode ser editado.")
        if int(row["version"]) != int(expected_version):
            raise PluginsRepositoryError("Conflito de versão do investimento.")
        for k, v in fields.items():
            if isinstance(v, Decimal):
                row[k] = str(v)
            elif isinstance(v, date):
                row[k] = v.isoformat()
            else:
                row[k] = v
        row["version"] = int(row["version"]) + 1
        row["updated_at"] = "t2"
        return deepcopy(row)

    def archive_capex_investment(self, investment_id, *, actor_id, reason=None):
        row = self.investments[investment_id]
        row.update(
            {
                "status": "archived",
                "archived_by": actor_id,
                "archived_at": "now",
                "updated_by": actor_id,
                "version": int(row["version"]) + 1,
            }
        )
        return deepcopy(row)

    def append_audit(self, **kwargs):
        self.audits.append(kwargs)


def _user(sub: str = "user-1") -> BudgetActor:
    return BudgetActor(
        user_id=sub,
        user_name="User",
        permissions=frozenset(
            {
                "planejamento-orcamentario.access",
                "planejamento-orcamentario.guidance.view",
            }
        ),
    )


def _admin() -> BudgetActor:
    return BudgetActor(
        user_id="admin-1",
        user_name="Admin",
        permissions=frozenset(
            {
                "planejamento-orcamentario.access",
                "planejamento-orcamentario.admin",
            }
        ),
    )


def _setup(*, ack: bool = True, cc: str = "205"):
    repo = FakeRepo()
    eid = repo.seed_exercise()
    gid = repo.seed_guidance(eid)
    if ack:
        repo.acks.add(("user-1", gid))
        repo.acks.add(("admin-1", gid))
    cat = repo.seed_category()
    repo.seed_responsibility(user_sub="user-1", exercise_id=eid, cost_center_id=cc)
    uc = CapexInvestmentUseCases(repository=repo)  # type: ignore[arg-type]
    return uc, repo, eid, cat


def test_create_draft_incomplete():
    uc, repo, eid, cat = _setup()
    created = uc.create_investment(
        _user(),
        {"exercise_id": eid, "cost_center_id": "205"},
    )
    assert created["status"] == "draft"
    assert created["is_complete"] is False
    assert "description" in created["missing_fields"]
    assert "estimated_amount" in created["missing_fields"]
    assert any(a["action"] == "capex_investment.created" for a in repo.audits)


def test_create_complete():
    uc, repo, eid, cat = _setup()
    created = uc.create_investment(
        _user(),
        {
            "exercise_id": eid,
            "cost_center_id": "205",
            "category_id": cat,
            "description": "Notebooks Dell",
            "estimated_amount": "15000.50",
            "required_date": "2027-06-01",
            "priority": "2",
            "origin": "national",
            "classification": "3",
            "shift": "1",
            "probable_supplier_name": "Dell",
        },
    )
    assert created["is_complete"] is True
    assert created["missing_fields"] == []
    assert created["estimated_amount"] == "15000.50"
    assert created["priority"] == "2"
    assert created["currency"] == "BRL"


def test_inactive_category_blocked():
    uc, repo, eid, _ = _setup()
    inactive = repo.seed_category(active=False)
    with pytest.raises(CapexInvestmentCategoryInvalidError):
        uc.create_investment(
            _user(),
            {
                "exercise_id": eid,
                "cost_center_id": "205",
                "category_id": inactive,
                "description": "x",
            },
        )


def test_cost_center_without_responsibility():
    uc, repo, eid, cat = _setup(cc="205")
    with pytest.raises(CapexInvestmentCostCenterForbiddenError):
        uc.create_investment(
            _user(),
            {"exercise_id": eid, "cost_center_id": "210", "category_id": cat},
        )


def test_guidance_not_acknowledged():
    uc, repo, eid, cat = _setup(ack=False)
    with pytest.raises(BudgetGuidanceAcknowledgementRequiredError):
        uc.create_investment(
            _user(),
            {"exercise_id": eid, "cost_center_id": "205"},
        )


def test_value_zero_or_negative():
    uc, repo, eid, cat = _setup()
    with pytest.raises(CapexInvestmentValueInvalidError):
        uc.create_investment(
            _user(),
            {
                "exercise_id": eid,
                "cost_center_id": "205",
                "estimated_amount": "0",
            },
        )
    with pytest.raises(CapexInvestmentValueInvalidError):
        uc.create_investment(
            _user(),
            {
                "exercise_id": eid,
                "cost_center_id": "205",
                "estimated_amount": "-10",
            },
        )


def test_invalid_date():
    uc, repo, eid, cat = _setup()
    with pytest.raises(CapexInvestmentDateInvalidError):
        uc.create_investment(
            _user(),
            {
                "exercise_id": eid,
                "cost_center_id": "205",
                "required_date": "31/12/2027",
            },
        )


def test_update_and_optimistic_concurrency():
    uc, repo, eid, cat = _setup()
    created = uc.create_investment(
        _user(),
        {
            "exercise_id": eid,
            "cost_center_id": "205",
            "description": "Antes",
            "estimated_amount": "100",
        },
    )
    updated = uc.update_investment(
        _user(),
        created["id"],
        {"version": 1, "description": "Depois", "estimated_amount": "200"},
    )
    assert updated["version"] == 2
    assert updated["description"] == "Depois"
    assert any(a["action"] == "capex_investment.amount_changed" for a in repo.audits)

    with pytest.raises(CapexInvestmentVersionConflictError):
        uc.update_investment(
            _user(),
            created["id"],
            {"version": 1, "description": "Stale"},
        )
    assert any(a["action"] == "capex_investment.version_conflict" for a in repo.audits)


def test_archive_and_edit_archived_blocked():
    uc, repo, eid, cat = _setup()
    created = uc.create_investment(
        _user(),
        {"exercise_id": eid, "cost_center_id": "205", "description": "x"},
    )
    archived = uc.archive_investment(_user(), created["id"])
    assert archived["status"] == "archived"
    with pytest.raises(CapexInvestmentArchivedError):
        uc.update_investment(
            _user(), created["id"], {"version": archived["version"], "description": "y"}
        )


def test_list_scoped_to_user_cost_centers():
    uc, repo, eid, cat = _setup(cc="205")
    repo.seed_responsibility(user_sub="user-2", exercise_id=eid, cost_center_id="210")
    gid = repo.guidance[eid]["id"]
    repo.acks.add(("user-2", gid))

    a = uc.create_investment(
        _user("user-1"),
        {"exercise_id": eid, "cost_center_id": "205", "description": "A"},
    )
    uc_u2 = CapexInvestmentUseCases(repository=repo)  # type: ignore[arg-type]
    b = uc_u2.create_investment(
        _user("user-2"),
        {"exercise_id": eid, "cost_center_id": "210", "description": "B"},
    )

    listed = uc.list_investments(_user("user-1"), exercise_id=eid)
    ids = {i["id"] for i in listed["items"]}
    assert a["id"] in ids
    assert b["id"] not in ids


def test_filters_and_pagination():
    uc, repo, eid, cat = _setup()
    for i in range(3):
        uc.create_investment(
            _user(),
            {
                "exercise_id": eid,
                "cost_center_id": "205",
                "category_id": cat,
                "description": f"Item {i}",
                "priority": "2" if i else "1",
                "origin": "national",
                "estimated_amount": "10",
                "required_date": "2027-01-01",
            },
        )
    page1 = uc.list_investments(
        _user(), exercise_id=eid, priority="2", page=1, page_size=1
    )
    assert page1["pagination"]["total"] == 2
    assert len(page1["items"]) == 1
    assert page1["pagination"]["has_more"] is True
    found = uc.list_investments(_user(), exercise_id=eid, q="Item 2")
    assert found["pagination"]["total"] == 1


def test_idor_get_by_id():
    uc, repo, eid, cat = _setup()
    created = uc.create_investment(
        _user("user-1"),
        {"exercise_id": eid, "cost_center_id": "205", "description": "segredo"},
    )
    gid = repo.guidance[eid]["id"]
    repo.acks.add(("user-2", gid))
    with pytest.raises(CapexInvestmentNotFoundError):
        uc.get_investment(_user("user-2"), created["id"])


def test_change_cost_center_requires_responsibility():
    uc, repo, eid, cat = _setup(cc="205")
    created = uc.create_investment(
        _user(),
        {"exercise_id": eid, "cost_center_id": "205", "description": "x"},
    )
    with pytest.raises(CapexInvestmentCostCenterForbiddenError):
        uc.update_investment(
            _user(),
            created["id"],
            {"version": 1, "cost_center_id": "210"},
        )
    repo.seed_responsibility(user_sub="user-1", exercise_id=eid, cost_center_id="210")
    moved = uc.update_investment(
        _user(),
        created["id"],
        {"version": 1, "cost_center_id": "210"},
    )
    assert moved["cost_center_id"] == "210"
    assert any(a["action"] == "capex_investment.cost_center_changed" for a in repo.audits)


def test_is_complete_missing_fields():
    uc, repo, eid, cat = _setup()
    created = uc.create_investment(
        _user(),
        {
            "exercise_id": eid,
            "cost_center_id": "205",
            "description": "Parcial",
            "priority": "1",
        },
    )
    assert created["is_complete"] is False
    assert set(created["missing_fields"]) >= {
        "category_id",
        "estimated_amount",
        "required_date",
        "origin",
    }


def test_admin_list_all_cost_centers():
    uc, repo, eid, cat = _setup()
    repo.seed_responsibility(user_sub="user-2", exercise_id=eid, cost_center_id="210")
    gid = repo.guidance[eid]["id"]
    repo.acks.add(("user-2", gid))
    uc.create_investment(
        _user("user-1"),
        {"exercise_id": eid, "cost_center_id": "205", "description": "A"},
    )
    CapexInvestmentUseCases(repository=repo).create_investment(  # type: ignore[arg-type]
        _user("user-2"),
        {"exercise_id": eid, "cost_center_id": "210", "description": "B"},
    )
    listed = uc.list_investments(_admin(), exercise_id=eid)
    assert listed["pagination"]["total"] == 2
