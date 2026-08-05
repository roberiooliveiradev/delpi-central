"""Testes Fase 2A.1 — responsabilidades orçamentárias (repositório fake)."""
from __future__ import annotations

from copy import deepcopy
from datetime import date, timedelta
from typing import Any
from uuid import uuid4

import pytest

from app.application.use_cases.planejamento_orcamentario.budget_planning_use_cases import (
    BudgetActor,
)
from app.application.use_cases.planejamento_orcamentario.budget_responsibility_use_cases import (
    BudgetResponsibilityUseCases,
)
from app.domain.services.planejamento_orcamentario.exceptions import (
    BudgetResponsibilityConflictError,
    BudgetResponsibilityForbiddenError,
    BudgetResponsibilityInvalidError,
    BudgetResponsibilityNotFoundError,
    BudgetUserNotAuthorizedError,
)
from app.domain.services.planejamento_orcamentario.responsibility_guard import (
    BudgetResponsibilityGuard,
)
from tests.unit.planejamento_orcamentario.fake_po_repository_helpers import (
    default_po_cc_seed,
    find_active_budget_responsibility_conflict_in_rows,
    find_valid_responsibility_in_rows,
    list_org_cost_centers_by_code_from_store,
    upsert_org_cost_center_in_store,
    get_org_cost_center_from_store,
)


class FakeRepo:
    def __init__(self) -> None:
        self.exercises: dict[str, dict] = {}
        self.units = {"01": {"code": "01", "name": "SC", "active": True}}
        self.areas = {
            "PROD": {"code": "PROD", "name": "Produção", "unit_code": "01", "active": True}
        }
        self.ccs: dict[tuple[str, str], dict] = default_po_cc_seed()
        self.rows: dict[str, dict] = {}
        self.audits: list[dict] = []

    def get_exercise(self, exercise_id: str):
        return deepcopy(self.exercises.get(exercise_id))

    def get_org_unit(self, code: str):
        return deepcopy(self.units.get(code))

    def get_org_area(self, code: str):
        return deepcopy(self.areas.get(code))

    def get_org_cost_center(self, code: str, *, branch: str | None = None):
        return get_org_cost_center_from_store(self.ccs, code, branch=branch)

    def list_org_cost_centers_by_code(self, code: str):
        return list_org_cost_centers_by_code_from_store(self.ccs, code)

    def upsert_org_cost_center(self, payload: dict[str, Any]):
        return upsert_org_cost_center_in_store(self.ccs, payload)

    def get_budget_responsibility(self, responsibility_id: str):
        return deepcopy(self.rows.get(responsibility_id))

    def find_active_budget_responsibility_conflict(
        self,
        *,
        exercise_id,
        module,
        user_sub,
        cost_center_id,
        unit_id=None,
        exclude_id=None,
    ):
        return find_active_budget_responsibility_conflict_in_rows(
            self.rows,
            exercise_id=exercise_id,
            module=module,
            user_sub=user_sub,
            cost_center_id=cost_center_id,
            unit_id=unit_id,
            exclude_id=exclude_id,
        )

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
            self.rows,
            user_sub=user_sub,
            exercise_id=exercise_id,
            module=module,
            cost_center_id=cost_center_id,
            unit_id=unit_id,
            on_date=on_date,
        )

    def list_budget_responsibilities(self, **kwargs):
        items = list(self.rows.values())
        if kwargs.get("exercise_id"):
            items = [i for i in items if i["exercise_id"] == kwargs["exercise_id"]]
        if kwargs.get("module"):
            items = [i for i in items if i["module"] == kwargs["module"]]
        if kwargs.get("user_sub"):
            items = [i for i in items if i["user_sub"] == kwargs["user_sub"]]
        if kwargs.get("cost_center_id"):
            items = [i for i in items if i["cost_center_id"] == kwargs["cost_center_id"]]
        if kwargs.get("responsibility_type"):
            items = [
                i
                for i in items
                if i["responsibility_type"] == kwargs["responsibility_type"]
            ]
        if kwargs.get("is_active") is not None:
            items = [i for i in items if i["is_active"] is kwargs["is_active"]]
        total = len(items)
        offset = kwargs.get("offset", 0)
        limit = kwargs.get("limit", 50)
        page = items[offset : offset + limit]
        return deepcopy(page), total

    def list_budget_responsibilities_for_user(self, **kwargs):
        items, _ = self.list_budget_responsibilities(
            user_sub=kwargs["user_sub"],
            module=kwargs.get("module"),
            exercise_id=kwargs.get("exercise_id"),
            is_active=True if kwargs.get("active_only", True) else None,
            offset=0,
            limit=1000,
        )
        if kwargs.get("active_only", True):
            check = kwargs.get("on_date") or date.today()
            filtered = []
            for i in items:
                vf, vu = i.get("valid_from"), i.get("valid_until")
                if vf and check < vf:
                    continue
                if vu and check > vu:
                    continue
                filtered.append(i)
            return filtered
        return items

    def create_budget_responsibility(self, payload: dict[str, Any]):
        rid = str(uuid4())
        row = {
            **payload,
            "id": rid,
            "is_active": True,
            "created_at": "t",
            "updated_at": "t",
            "deactivated_by": None,
            "deactivated_at": None,
            "deactivation_reason": None,
        }
        self.rows[rid] = row
        return deepcopy(row)

    def update_budget_responsibility(self, responsibility_id: str, fields: dict[str, Any]):
        self.rows[responsibility_id].update(fields)
        return deepcopy(self.rows[responsibility_id])

    def deactivate_budget_responsibility(self, responsibility_id, *, actor_id, reason):
        row = self.rows[responsibility_id]
        row.update(
            {
                "is_active": False,
                "deactivated_by": actor_id,
                "deactivated_at": "now",
                "deactivation_reason": reason,
                "updated_by": actor_id,
            }
        )
        return deepcopy(row)

    def reactivate_budget_responsibility(self, responsibility_id, *, actor_id):
        row = self.rows[responsibility_id]
        row.update(
            {
                "is_active": True,
                "deactivated_by": None,
                "deactivated_at": None,
                "deactivation_reason": None,
                "updated_by": actor_id,
            }
        )
        return deepcopy(row)

    def append_audit(self, **kwargs):
        self.audits.append(kwargs)


def _admin() -> BudgetActor:
    return BudgetActor(
        user_id="admin-1",
        user_name="Admin",
        permissions=frozenset({
            "planejamento-orcamentario.access",
            "planejamento-orcamentario.admin",
            "planejamento-orcamentario.scopes.manage",
        }),
    )


def _user(sub: str = "user-1") -> BudgetActor:
    return BudgetActor(
        user_id=sub,
        user_name="User",
        permissions=frozenset({
            "planejamento-orcamentario.access",
            "planejamento-orcamentario.guidance.view",
        }),
    )


@pytest.fixture
def uc():
    repo = FakeRepo()
    eid = str(uuid4())
    repo.exercises[eid] = {
        "id": eid,
        "year": 2027,
        "name": "PO 2027",
        "status": "open",
        "is_active": True,
    }
    return BudgetResponsibilityUseCases(repository=repo), repo, eid


def _create(uc, repo, eid, **overrides):
    body = {
        "exercise_id": eid,
        "module": "capex",
        "user_sub": "user-1",
        "user_name_snapshot": "User One",
        "user_email_snapshot": "u1@delpi.local",
        "unit_id": "01",
        "area_id": "PROD",
        "cost_center_id": "205",
        "responsibility_type": "owner",
        **overrides,
    }
    return uc.create_responsibility(_admin(), body)


def test_create_valid_and_audit(uc):
    use_cases, repo, eid = uc
    created = _create(use_cases, repo, eid)
    assert created["module"] == "capex"
    assert created["cost_center_id"] == "205"
    assert repo.audits[-1]["action"] == "responsibility.created"
    assert "Bearer" not in str(repo.audits[-1])


def test_multiple_cost_centers_same_user(uc):
    use_cases, repo, eid = uc
    a = _create(use_cases, repo, eid, cost_center_id="205")
    b = _create(use_cases, repo, eid, cost_center_id="210")
    assert a["id"] != b["id"]
    assert a["user_sub"] == b["user_sub"]


def test_multiple_users_same_cost_center(uc):
    use_cases, repo, eid = uc
    a = _create(use_cases, repo, eid, user_sub="user-a")
    b = _create(use_cases, repo, eid, user_sub="user-b")
    assert a["cost_center_id"] == b["cost_center_id"] == "205"


def test_duplicate_active_blocked(uc):
    use_cases, repo, eid = uc
    _create(use_cases, repo, eid)
    with pytest.raises(BudgetResponsibilityConflictError):
        _create(use_cases, repo, eid)


def test_invalid_cost_center(uc):
    use_cases, repo, eid = uc
    with pytest.raises(BudgetResponsibilityInvalidError):
        _create(use_cases, repo, eid, cost_center_id="999")


def test_invalid_org_hierarchy(uc):
    use_cases, repo, eid = uc
    repo.units["02"] = {"code": "02", "name": "ES", "active": True}
    with pytest.raises(BudgetResponsibilityInvalidError):
        # unidade 02 existe, mas CC 205 pertence à unidade 01
        _create(use_cases, repo, eid, unit_id="02")


def test_invalid_validity(uc):
    use_cases, repo, eid = uc
    with pytest.raises(BudgetResponsibilityInvalidError):
        _create(
            use_cases,
            repo,
            eid,
            valid_from="2026-12-01",
            valid_until="2026-01-01",
        )


def test_expired_and_inactive_denied_by_guard(uc):
    use_cases, repo, eid = uc
    created = _create(
        use_cases,
        repo,
        eid,
        valid_from=(date.today() - timedelta(days=30)).isoformat(),
        valid_until=(date.today() - timedelta(days=1)).isoformat(),
    )
    guard = BudgetResponsibilityGuard(repo)
    with pytest.raises(BudgetResponsibilityForbiddenError):
        guard.assert_user_has_budget_responsibility(
            "user-1", eid, "capex", "205"
        )
    use_cases.deactivate_responsibility(_admin(), created["id"], reason="fim")
    # even with open validity, inactive fails
    repo.rows[created["id"]]["valid_until"] = (date.today() + timedelta(days=10))
    with pytest.raises(BudgetResponsibilityForbiddenError):
        guard.assert_user_has_budget_responsibility(
            "user-1", eid, "capex", "205"
        )


def test_deactivate_and_reactivate(uc):
    use_cases, repo, eid = uc
    created = _create(use_cases, repo, eid)
    deactivated = use_cases.deactivate_responsibility(
        _admin(), created["id"], reason="troca"
    )
    assert deactivated["is_active"] is False
    assert any(a["action"] == "responsibility.deactivated" for a in repo.audits)
    reactivated = use_cases.reactivate_responsibility(_admin(), created["id"])
    assert reactivated["is_active"] is True
    assert any(a["action"] == "responsibility.reactivated" for a in repo.audits)


def test_reactivate_conflict(uc):
    use_cases, repo, eid = uc
    first = _create(use_cases, repo, eid, user_sub="user-1")
    use_cases.deactivate_responsibility(_admin(), first["id"])
    _create(use_cases, repo, eid, user_sub="user-1")  # novo ativo
    with pytest.raises(BudgetResponsibilityConflictError):
        use_cases.reactivate_responsibility(_admin(), first["id"])


def test_user_without_permission(uc):
    use_cases, repo, eid = uc
    with pytest.raises(BudgetUserNotAuthorizedError):
        use_cases.create_responsibility(_user(), {
            "exercise_id": eid,
            "user_sub": "x",
            "unit_id": "01",
            "cost_center_id": "205",
            "responsibility_type": "owner",
        })


def test_my_responsibilities_from_jwt_only(uc):
    use_cases, repo, eid = uc
    _create(use_cases, repo, eid, user_sub="user-1")
    _create(use_cases, repo, eid, user_sub="user-2", cost_center_id="210")
    mine = use_cases.list_my_responsibilities(_user("user-1"), module="capex")
    assert mine["user_sub"] == "user-1"
    assert len(mine["items"]) == 1
    assert mine["items"][0]["cost_center_id"] == "205"
    # unknown JWT
    with pytest.raises(BudgetResponsibilityForbiddenError):
        use_cases.list_my_responsibilities(
            BudgetActor(user_id="unknown", user_name="x", permissions=frozenset({"planejamento-orcamentario.access"}))
        )


def test_guard_valid_responsibility(uc):
    use_cases, repo, eid = uc
    _create(use_cases, repo, eid)
    state = use_cases.assert_user_has_budget_responsibility(
        "user-1", eid, "capex", "205"
    )
    assert state["responsibility"]["user_sub"] == "user-1"


def test_module_not_capex_blocked(uc):
    use_cases, repo, eid = uc
    with pytest.raises(BudgetResponsibilityInvalidError):
        _create(use_cases, repo, eid, module="revenue")


def test_idor_get_requires_admin(uc):
    use_cases, repo, eid = uc
    created = _create(use_cases, repo, eid, user_sub="user-1")
    with pytest.raises(BudgetUserNotAuthorizedError):
        use_cases.get_responsibility(_user("user-2"), created["id"])
    with pytest.raises(BudgetUserNotAuthorizedError):
        use_cases.update_responsibility(
            _user("user-1"), created["id"], {"responsibility_type": "collaborator"}
        )


def test_update_type_and_validity_audited(uc):
    use_cases, repo, eid = uc
    created = _create(use_cases, repo, eid)
    updated = use_cases.update_responsibility(
        _admin(),
        created["id"],
        {
            "responsibility_type": "collaborator",
            "valid_from": date.today().isoformat(),
            "valid_until": (date.today() + timedelta(days=90)).isoformat(),
        },
    )
    assert updated["responsibility_type"] == "collaborator"
    actions = {a["action"] for a in repo.audits}
    assert "responsibility.type_changed" in actions
    assert "responsibility.validity_changed" in actions


def test_not_found(uc):
    use_cases, repo, eid = uc
    with pytest.raises(BudgetResponsibilityNotFoundError):
        use_cases.get_responsibility(_admin(), str(uuid4()))


def test_list_filter_by_responsibility_type(uc):
    use_cases, repo, eid = uc
    _create(use_cases, repo, eid, user_sub="u-owner", responsibility_type="owner")
    _create(
        use_cases,
        repo,
        eid,
        user_sub="u-collab",
        cost_center_id="210",
        responsibility_type="collaborator",
    )
    owners = use_cases.list_responsibilities(
        _admin(), exercise_id=eid, responsibility_type="owner"
    )
    assert owners["pagination"]["total"] == 1
    assert owners["items"][0]["responsibility_type"] == "owner"
    collabs = use_cases.list_responsibilities(
        _admin(), exercise_id=eid, responsibility_type="collaborator"
    )
    assert collabs["pagination"]["total"] == 1
    assert collabs["items"][0]["user_sub"] == "u-collab"


def test_same_code_in_both_branches_allowed(uc):
    use_cases, repo, eid = uc
    repo.units["02"] = {"code": "02", "name": "ES", "active": True}
    repo.upsert_org_cost_center(
        {
            "branch": "02",
            "code": "205",
            "name": "TI ES",
            "unit_code": "02",
            "area_code": None,
            "source": "manual",
        }
    )
    a = _create(use_cases, repo, eid, unit_id="01", cost_center_id="205")
    b = _create(
        use_cases,
        repo,
        eid,
        unit_id="02",
        cost_center_id="205",
        area_id=None,
    )
    assert a["branch"] == "01"
    assert b["branch"] == "02"
    assert a["id"] != b["id"]


def test_duplicate_responsibility_same_branch_blocked(uc):
    use_cases, repo, eid = uc
    _create(use_cases, repo, eid, unit_id="01", cost_center_id="205")
    with pytest.raises(BudgetResponsibilityConflictError):
        _create(
            use_cases,
            repo,
            eid,
            unit_id="01",
            cost_center_id="205",
            responsibility_type="collaborator",
        )


def test_invalid_branch_rejected_on_create(uc):
    use_cases, repo, eid = uc
    with pytest.raises(BudgetResponsibilityInvalidError):
        _create(use_cases, repo, eid, unit_id="99", cost_center_id="205")

