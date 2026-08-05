"""Testes Fase 3B.1.1 — planos/linhas de Pessoal com cargo livre (position_name)."""
from __future__ import annotations

from copy import deepcopy
from typing import Any
from uuid import uuid4

import pytest

from app.application.security import api_delpi_permissions as perms
from app.application.use_cases.planejamento_orcamentario.budget_planning_use_cases import (
    BudgetActor,
)
from app.application.use_cases.planejamento_orcamentario.personnel_plan_use_cases import (
    PersonnelPlanUseCases,
)
from app.domain.services.planejamento_orcamentario.exceptions import (
    PersonnelCostCenterBranchMismatchError,
    PersonnelInvalidHeadcountError,
    PersonnelLineDuplicatePositionError,
    PersonnelLineVersionConflictError,
    PersonnelPositionNameRequiredError,
    PersonnelPositionNameTooLongError,
    PersonnelResponsibilityRequiredError,
)
from app.domain.services.planejamento_orcamentario.personnel_budget_constants import (
    POSITION_NAME_MAX_LENGTH,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import PluginsRepositoryError
from app.interface.http.routes.planejamento_orcamentario import planejamento_orcamentario_router as router_mod
from tests.unit.planejamento_orcamentario.fake_po_repository_helpers import (
    default_po_cc_seed_with_es,
    filter_unit_cost_center_pairs,
    find_valid_responsibility_in_rows,
    get_org_cost_center_from_store,
    list_org_cost_centers_by_code_from_store,
    upsert_org_cost_center_in_store,
)


class FakeRepo:
    def __init__(self) -> None:
        self.exercises: dict[str, dict] = {}
        self.active_exercise_id: str | None = None
        self.guidance: dict[str, dict] = {}
        self.acks: set[tuple[str, str]] = set()
        self.ccs: dict[tuple[str, str], dict] = default_po_cc_seed_with_es()
        self.ccs[("02", "205")] = {
            "id": "cc-205-02",
            "code": "205",
            "name": "TI ES",
            "branch": "02",
            "unit_code": "02",
            "area_code": "ENG",
            "active": True,
            "source": "manual",
        }
        self.responsibilities: list[dict] = []
        self.plans: dict[str, dict] = {}
        self.lines: dict[str, dict] = {}
        self.history: list[dict] = []
        self.audits: list[dict] = []

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

    def seed_ack(self, user_sub: str, guidance_id: str) -> None:
        self.acks.add((user_sub, guidance_id))

    def seed_responsibility(
        self,
        *,
        user_sub: str,
        exercise_id: str,
        cost_center_id: str,
        unit_id: str = "01",
        module: str = "personnel",
        area_id: str | None = None,
    ) -> None:
        if area_id is None:
            cc = get_org_cost_center_from_store(
                self.ccs, cost_center_id, branch=unit_id
            )
            area_id = (cc or {}).get("area_code")
        self.responsibilities.append(
            {
                "id": str(uuid4()),
                "user_sub": user_sub,
                "exercise_id": exercise_id,
                "module": module,
                "cost_center_id": cost_center_id,
                "unit_id": unit_id,
                "area_id": area_id,
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

    def upsert_org_cost_center(self, payload: dict[str, Any]):
        return upsert_org_cost_center_in_store(self.ccs, payload)

    def find_valid_responsibility(self, **kwargs):
        return find_valid_responsibility_in_rows(self.responsibilities, **kwargs)

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

    def get_personnel_plan(self, plan_id: str):
        return deepcopy(self.plans.get(plan_id))

    def get_personnel_plan_by_exercise_cc(self, *, exercise_id, cost_center_id, unit_id):
        for p in self.plans.values():
            if (
                p["exercise_id"] == exercise_id
                and p["cost_center_id"] == cost_center_id
                and p["unit_id"] == unit_id
            ):
                return deepcopy(p)
        return None

    def create_personnel_plan(self, payload: dict[str, Any]):
        pid = str(uuid4())
        row = {
            **payload,
            "id": pid,
            "status": "draft",
            "version": 1,
            "submitted_by": None,
            "submitted_at": None,
            "reviewed_by": None,
            "reviewed_at": None,
            "decision_comment": None,
            "created_at": "t",
            "updated_at": "t",
            "updated_by": payload["created_by"],
        }
        self.plans[pid] = row
        return deepcopy(row)

    def list_personnel_plans(self, **kwargs):
        items = list(self.plans.values())
        if kwargs.get("exercise_id"):
            items = [i for i in items if i["exercise_id"] == kwargs["exercise_id"]]
        if kwargs.get("unit_id"):
            items = [i for i in items if i["unit_id"] == kwargs["unit_id"]]
        if kwargs.get("area_id"):
            items = [i for i in items if i.get("area_id") == kwargs["area_id"]]
        if kwargs.get("cost_center_id"):
            items = [i for i in items if i["cost_center_id"] == kwargs["cost_center_id"]]
        if kwargs.get("status"):
            items = [i for i in items if i.get("status") == kwargs["status"]]
        if kwargs.get("submitted_by"):
            items = [i for i in items if i.get("submitted_by") == kwargs["submitted_by"]]
        items = filter_unit_cost_center_pairs(
            items,
            kwargs.get("unit_cost_center_pairs"),
            unit_col="unit_id",
            cc_col="cost_center_id",
        )
        total = len(items)
        offset = int(kwargs.get("offset") or 0)
        limit = int(kwargs.get("limit") or 50)
        return deepcopy(items[offset : offset + limit]), total

    def transition_personnel_plan(
        self,
        plan_id: str,
        *,
        expected_version: int,
        new_status: str,
        actor_id: str,
        submitted_by: str | None = None,
        reviewed_by: str | None = None,
        decision_comment: str | None = None,
        clear_review: bool = False,
    ):
        row = self.plans.get(plan_id)
        if not row or int(row["version"]) != int(expected_version):
            raise PluginsRepositoryError(
                "Conflito de versão ou planejamento de Pessoal não encontrado."
            )
        row["status"] = new_status
        row["version"] = int(row["version"]) + 1
        row["updated_by"] = actor_id
        row["updated_at"] = "t"
        if submitted_by is not None:
            row["submitted_by"] = submitted_by
            row["submitted_at"] = "t"
        if clear_review:
            row["reviewed_by"] = None
            row["reviewed_at"] = None
        if reviewed_by is not None:
            row["reviewed_by"] = reviewed_by
            row["reviewed_at"] = "t"
        if decision_comment is not None:
            row["decision_comment"] = decision_comment
        return deepcopy(row)

    def append_personnel_plan_history(self, payload: dict[str, Any]):
        row = {
            "id": str(uuid4()),
            "created_at": "t",
            **payload,
        }
        self.history.append(row)
        return deepcopy(row)

    def list_personnel_plan_history(self, plan_id: str):
        return deepcopy([h for h in self.history if h["plan_id"] == plan_id])

    def get_personnel_plan_line(self, line_id: str):
        return deepcopy(self.lines.get(line_id))

    def get_personnel_plan_line_by_plan_position_name(
        self, *, plan_id, position_name, active_only=True
    ):
        key = str(position_name or "").strip().casefold()
        for ln in self.lines.values():
            if ln["plan_id"] != plan_id:
                continue
            if active_only and not ln.get("is_active", True):
                continue
            if str(ln.get("position_name") or "").strip().casefold() == key:
                return deepcopy(ln)
        return None

    def list_personnel_plan_lines(self, *, plan_id, active_only=True):
        items = [ln for ln in self.lines.values() if ln["plan_id"] == plan_id]
        if active_only:
            items = [ln for ln in items if ln.get("is_active", True)]
        return deepcopy(items)

    def create_personnel_plan_line(self, payload: dict[str, Any]):
        lid = str(uuid4())
        row = {
            **payload,
            "id": lid,
            "version": 1,
            "is_active": True,
            "created_at": "t",
            "updated_at": "t",
        }
        self.lines[lid] = row
        return deepcopy(row)

    def update_personnel_plan_line(self, line_id, fields, *, expected_version):
        row = self.lines[line_id]
        if int(row["version"]) != int(expected_version):
            raise PluginsRepositoryError("Conflito de versão da linha de Pessoal.")
        if not row.get("is_active"):
            raise PluginsRepositoryError("Linha arquivada não pode ser editada.")
        row.update(fields)
        row["version"] = int(row["version"]) + 1
        return deepcopy(row)

    def archive_personnel_plan_line(self, line_id, *, actor_id):
        row = self.lines[line_id]
        row["is_active"] = False
        row["updated_by"] = actor_id
        row["version"] = int(row["version"]) + 1
        return deepcopy(row)

    def append_audit(self, **kwargs):
        self.audits.append(kwargs)


@pytest.fixture
def editor() -> BudgetActor:
    return BudgetActor(
        user_id="u1",
        user_name="Editor",
        permissions=frozenset(
            {
                "planejamento-orcamentario.access",
                "planejamento-orcamentario.personnel.view",
                "planejamento-orcamentario.personnel.edit",
            }
        ),
    )


@pytest.fixture
def setup_ready():
    repo = FakeRepo()
    eid = repo.seed_exercise()
    gid = repo.seed_guidance(eid)
    repo.seed_ack("u1", gid)
    return repo, eid, PersonnelPlanUseCases(repository=repo)


def _resolve_plan(uc, editor, eid, unit_id="01", cc="205"):
    return uc.resolve_plan(
        editor, exercise_id=eid, unit_id=unit_id, cost_center_id=cc
    )


def test_create_line_with_free_text_and_accent(setup_ready, editor):
    repo, eid, uc = setup_ready
    repo.seed_responsibility(user_sub="u1", exercise_id=eid, cost_center_id="205")
    plan = _resolve_plan(uc, editor, eid)
    line = uc.create_line(
        editor,
        plan["id"],
        {
            "position_name": "  Analista de Qualidade  ",
            "headcount_dec_2025": 1,
            "headcount_oct_2026": 2,
            "headcount_forecast": 2,
            "headcount_dec_2027": 3,
        },
    )
    assert line["position_name"] == "Analista de Qualidade"
    assert "position_id" not in line
    assert line["is_complete"] is True


def test_trim_and_empty_and_too_long(setup_ready, editor):
    repo, eid, uc = setup_ready
    repo.seed_responsibility(user_sub="u1", exercise_id=eid, cost_center_id="205")
    plan = _resolve_plan(uc, editor, eid)
    with pytest.raises(PersonnelPositionNameRequiredError) as exc:
        uc.create_line(editor, plan["id"], {"position_name": "   "})
    assert exc.value.code == "budget_personnel_position_name_required"
    with pytest.raises(PersonnelPositionNameTooLongError) as exc2:
        uc.create_line(
            editor,
            plan["id"],
            {"position_name": "X" * (POSITION_NAME_MAX_LENGTH + 1)},
        )
    assert exc2.value.code == "budget_personnel_position_name_too_long"


def test_duplicate_exact_case_and_spaces(setup_ready, editor):
    repo, eid, uc = setup_ready
    repo.seed_responsibility(user_sub="u1", exercise_id=eid, cost_center_id="205")
    plan = _resolve_plan(uc, editor, eid)
    uc.create_line(
        editor, plan["id"], {"position_name": "Operador de Produção", "headcount_dec_2025": 1}
    )
    for name in (
        "Operador de Produção",
        "operador de produção",
        " Operador de Produção ",
    ):
        with pytest.raises(PersonnelLineDuplicatePositionError) as exc:
            uc.create_line(editor, plan["id"], {"position_name": name})
        assert exc.value.code == "budget_personnel_line_duplicate_position"


def test_same_name_different_cc_and_branches(setup_ready, editor):
    repo, eid, uc = setup_ready
    repo.seed_responsibility(
        user_sub="u1", exercise_id=eid, cost_center_id="205", unit_id="01"
    )
    repo.seed_responsibility(
        user_sub="u1", exercise_id=eid, cost_center_id="210", unit_id="01"
    )
    repo.seed_responsibility(
        user_sub="u1", exercise_id=eid, cost_center_id="205", unit_id="02"
    )
    p205 = _resolve_plan(uc, editor, eid, "01", "205")
    p210 = _resolve_plan(uc, editor, eid, "01", "210")
    p02 = _resolve_plan(uc, editor, eid, "02", "205")
    for plan in (p205, p210, p02):
        line = uc.create_line(
            editor, plan["id"], {"position_name": "Líder de Produção", "headcount_dec_2025": 1}
        )
        assert line["position_name"] == "Líder de Produção"


def test_edit_position_name_and_version_conflict(setup_ready, editor):
    repo, eid, uc = setup_ready
    repo.seed_responsibility(user_sub="u1", exercise_id=eid, cost_center_id="205")
    plan = _resolve_plan(uc, editor, eid)
    line = uc.create_line(
        editor, plan["id"], {"position_name": "Auxiliar", "headcount_dec_2025": 0}
    )
    updated = uc.update_line(
        editor,
        line["id"],
        {"version": 1, "position_name": "Supervisor de Logística", "headcount_dec_2025": 2},
    )
    assert updated["position_name"] == "Supervisor de Logística"
    assert updated["version"] == 2
    with pytest.raises(PersonnelLineVersionConflictError):
        uc.update_line(
            editor, line["id"], {"version": 1, "headcount_dec_2025": 9}
        )


def test_negative_headcount_and_archive(setup_ready, editor):
    repo, eid, uc = setup_ready
    repo.seed_responsibility(user_sub="u1", exercise_id=eid, cost_center_id="205")
    plan = _resolve_plan(uc, editor, eid)
    with pytest.raises(PersonnelInvalidHeadcountError):
        uc.create_line(
            editor,
            plan["id"],
            {"position_name": "Operador", "headcount_dec_2025": -1},
        )
    line = uc.create_line(editor, plan["id"], {"position_name": "Operador"})
    archived = uc.archive_line(editor, line["id"])
    assert archived["is_active"] is False
    assert archived["position_name"] == "Operador"


def test_resolve_idempotent_and_access(setup_ready, editor):
    repo, eid, uc = setup_ready
    repo.seed_responsibility(
        user_sub="u1", exercise_id=eid, cost_center_id="205", unit_id="01"
    )
    repo.seed_responsibility(
        user_sub="u1", exercise_id=eid, cost_center_id="205", unit_id="02"
    )
    p01 = _resolve_plan(uc, editor, eid, "01")
    assert _resolve_plan(uc, editor, eid, "01")["id"] == p01["id"]
    p02 = _resolve_plan(uc, editor, eid, "02")
    assert p01["id"] != p02["id"]


def test_access_denied_without_responsibility(setup_ready, editor):
    _, eid, uc = setup_ready
    with pytest.raises(PersonnelResponsibilityRequiredError):
        _resolve_plan(uc, editor, eid)


def test_branch_mismatch(setup_ready, editor):
    repo, eid, uc = setup_ready
    repo.seed_responsibility(
        user_sub="u1", exercise_id=eid, cost_center_id="301", unit_id="01"
    )
    with pytest.raises(PersonnelCostCenterBranchMismatchError):
        uc.resolve_plan(
            editor, exercise_id=eid, unit_id="01", cost_center_id="301"
        )


def test_catalog_endpoints_and_permission_removed():
    paths = {getattr(r, "path", None) for r in router_mod.router.routes}
    assert "/personnel/positions" not in paths
    assert "/admin/personnel/positions" not in paths
    assert not hasattr(perms, "PLANEJAMENTO_ORCAMENTARIO_PERSONNEL_POSITIONS_MANAGE")
    assert not hasattr(perms, "PLANEJAMENTO_ORCAMENTARIO_PERSONNEL_POSITIONS_MANAGE_PERMISSIONS")


def test_partial_draft_totals(setup_ready, editor):
    repo, eid, uc = setup_ready
    repo.seed_responsibility(user_sub="u1", exercise_id=eid, cost_center_id="205")
    plan = _resolve_plan(uc, editor, eid)
    uc.create_line(
        editor,
        plan["id"],
        {"position_name": "Operador", "headcount_dec_2025": 0, "headcount_oct_2026": 2},
    )
    got = uc.get_plan(editor, plan["id"])
    assert got["position_count"] == 1
    assert got["totals"]["headcount_oct_2026"] == 2
    assert got["incomplete_line_count"] == 1
    assert got["is_complete"] is False
