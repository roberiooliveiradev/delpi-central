"""Testes Fase 2C.1 — planejamento CAPEX por CC (submissão e aprovação)."""
from __future__ import annotations

from copy import deepcopy
from typing import Any
from uuid import uuid4

import pytest

from app.application.use_cases.planejamento_orcamentario.budget_planning_use_cases import (
    BudgetActor,
)
from app.application.use_cases.planejamento_orcamentario.capex_investment_use_cases import (
    CapexInvestmentUseCases,
)
from app.application.use_cases.planejamento_orcamentario.capex_plan_use_cases import (
    CapexPlanUseCases,
)
from app.domain.services.planejamento_orcamentario.exceptions import (
    BudgetGuidanceAcknowledgementRequiredError,
    CapexApprovalForbiddenError,
    CapexInvestmentCostCenterForbiddenError,
    CapexInvestmentNotFoundError,
    CapexPlanAlreadyApprovedError,
    CapexPlanCommentRequiredError,
    CapexPlanIncompleteError,
    CapexPlanInvalidTransitionError,
    CapexPlanLockedError,
    CapexPlanNotFoundError,
    CapexPlanVersionConflictError,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import PluginsRepositoryError
from tests.unit.planejamento_orcamentario.fake_po_repository_helpers import (
    default_po_cc_seed,
    filter_unit_cost_center_pairs,
    find_valid_responsibility_in_rows,
    get_capex_plan_by_exercise_cc_from_plans,
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
        self.ccs: dict[tuple[str, str], dict] = default_po_cc_seed()
        self.categories: dict[str, dict] = {}
        self.responsibilities: list[dict] = []
        self.investments: dict[str, dict] = {}
        self.plans: dict[str, dict] = {}
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

    def seed_category(self, *, active: bool = True) -> str:
        cid = str(uuid4())
        self.categories[cid] = {
            "id": cid,
            "code": f"CAT_{cid[:6]}",
            "name": "Ferramentas",
            "is_active": active,
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

    def seed_complete_investment(
        self, *, exercise_id: str, cost_center_id: str = "205", category_id: str | None = None
    ) -> str:
        iid = str(uuid4())
        self.investments[iid] = {
            "id": iid,
            "exercise_id": exercise_id,
            "unit_id": "01",
            "area_id": "PROD",
            "cost_center_id": cost_center_id,
            "category_id": category_id,
            "description": "Notebooks",
            "estimated_amount": "1000.00",
            "required_date": "2027-06-01",
            "priority": "2",
            "origin": "national",
            "status": "draft",
            "review_status": "pending",
            "version": 1,
            "created_by": "u1",
        }
        return iid

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
        if kwargs.get("status"):
            items = [i for i in items if i.get("status") == kwargs["status"]]
        total = len(items)
        offset = kwargs.get("offset", 0)
        limit = kwargs.get("limit", 50)
        return deepcopy(items[offset : offset + limit]), total

    def create_capex_investment(self, payload: dict[str, Any]):
        iid = str(uuid4())
        row = {**payload, "id": iid, "version": 1, "status": "draft"}
        self.investments[iid] = row
        return deepcopy(row)

    def update_capex_investment(self, investment_id, fields, *, expected_version):
        row = self.investments.get(investment_id)
        if not row or int(row["version"]) != int(expected_version):
            raise PluginsRepositoryError("Conflito de versão do investimento.")
        row.update(fields)
        row["version"] = int(row["version"]) + 1
        return deepcopy(row)

    def archive_capex_investment(self, investment_id, *, actor_id, reason=None):
        row = self.investments[investment_id]
        row["status"] = "archived"
        row["archived_by"] = actor_id
        return deepcopy(row)

    def get_capex_plan(self, plan_id: str):
        return deepcopy(self.plans.get(plan_id))

    def get_capex_plan_by_exercise_cc(
        self, *, exercise_id: str, cost_center_id: str, unit_id: str | None = None
    ):
        return get_capex_plan_by_exercise_cc_from_plans(
            self.plans,
            exercise_id=exercise_id,
            cost_center_id=cost_center_id,
            unit_id=unit_id,
        )

    def create_capex_plan(self, payload: dict[str, Any]):
        for p in self.plans.values():
            if (
                p["exercise_id"] == payload["exercise_id"]
                and p["cost_center_id"] == payload["cost_center_id"]
                and p.get("unit_id") == payload.get("unit_id")
            ):
                raise PluginsRepositoryError("duplicate plan")
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
            "updated_by": payload.get("created_by"),
        }
        self.plans[pid] = row
        return deepcopy(row)

    def rollback(self) -> None:
        return None

    def list_capex_plans(self, **kwargs):
        items = list(self.plans.values())
        if kwargs.get("exercise_id"):
            items = [i for i in items if i["exercise_id"] == kwargs["exercise_id"]]
        if kwargs.get("unit_id"):
            items = [i for i in items if i.get("unit_id") == kwargs["unit_id"]]
        if kwargs.get("area_id"):
            items = [i for i in items if i.get("area_id") == kwargs["area_id"]]
        if kwargs.get("cost_center_id"):
            items = [i for i in items if i["cost_center_id"] == kwargs["cost_center_id"]]
        items = filter_unit_cost_center_pairs(
            items, kwargs.get("unit_cost_center_pairs")
        )
        if kwargs.get("cost_center_ids") is not None and kwargs.get("unit_cost_center_pairs") is None:
            allowed = set(kwargs["cost_center_ids"])
            items = [i for i in items if i["cost_center_id"] in allowed]
        if kwargs.get("status"):
            items = [i for i in items if i.get("status") == kwargs["status"]]
        if kwargs.get("submitted_by"):
            items = [i for i in items if i.get("submitted_by") == kwargs["submitted_by"]]
        total = len(items)
        offset = kwargs.get("offset", 0)
        limit = kwargs.get("limit", 50)
        return deepcopy(items[offset : offset + limit]), total

    def transition_capex_plan(
        self,
        plan_id: str,
        *,
        expected_version: int,
        new_status: str,
        actor_id: str,
        submitted_by: str | None = None,
        submitted_by_name: str | None = None,
        clear_submission: bool = False,
        reviewed_by: str | None = None,
        decision_comment: str | None = None,
        clear_review: bool = False,
    ):
        row = self.plans.get(plan_id)
        if not row or int(row["version"]) != int(expected_version):
            raise PluginsRepositoryError("Conflito de versão")
        row["status"] = new_status
        row["version"] = int(row["version"]) + 1
        row["updated_by"] = actor_id
        if submitted_by is not None:
            row["submitted_by"] = submitted_by
            row["submitted_at"] = "t"
            if submitted_by_name is not None:
                row["submitted_by_name"] = submitted_by_name
        if clear_submission:
            row["submitted_by"] = None
            row["submitted_by_name"] = None
            row["submitted_at"] = None
        if reviewed_by is not None:
            row["reviewed_by"] = reviewed_by
            row["reviewed_at"] = "t"
        if clear_review:
            row["reviewed_by"] = None
            row["reviewed_at"] = None
        if decision_comment is not None:
            row["decision_comment"] = decision_comment
        return deepcopy(row)

    def append_capex_plan_history(self, payload: dict[str, Any]):
        row = {**payload, "id": str(uuid4()), "created_at": "t"}
        self.history.append(row)
        return deepcopy(row)

    def list_capex_plan_history(self, plan_id: str):
        return deepcopy([h for h in self.history if h["plan_id"] == plan_id])

    def append_audit(self, **kwargs):
        self.audits.append(kwargs)

    def set_capex_investment_review(
        self,
        investment_id: str,
        *,
        review_status: str,
        review_comment: str | None,
        reviewed_by: str,
        reviewed_by_name: str | None = None,
    ):
        row = self.investments.get(investment_id)
        if not row or row.get("status") != "draft":
            raise PluginsRepositoryError("Investimento CAPEX não encontrado ou arquivado.")
        row["review_status"] = review_status
        row["review_comment"] = review_comment
        row["reviewed_by"] = None if review_status == "pending" else reviewed_by
        row["reviewed_by_name"] = None if review_status == "pending" else reviewed_by_name
        row["reviewed_at"] = None if review_status == "pending" else "t"
        return deepcopy(row)

    def stamp_capex_investment_reviews(
        self,
        *,
        exercise_id: str,
        cost_center_id: str,
        unit_id: str | None,
        review_status: str,
        reviewed_by: str | None = None,
        reviewed_by_name: str | None = None,
        review_comment: str | None = None,
    ):
        for row in self.investments.values():
            if row["exercise_id"] != exercise_id:
                continue
            if row["cost_center_id"] != cost_center_id:
                continue
            if unit_id and row.get("unit_id") != unit_id:
                continue
            if row.get("status") != "draft":
                continue
            row["review_status"] = review_status
            row["review_comment"] = None if review_status == "pending" else review_comment
            row["reviewed_by"] = None if review_status == "pending" else reviewed_by
            row["reviewed_by_name"] = None if review_status == "pending" else reviewed_by_name
            row["reviewed_at"] = None if review_status == "pending" else "t"


def _actor(
    sub: str = "u1",
    *,
    admin: bool = False,
    submit: bool = True,
    approve: bool = False,
) -> BudgetActor:
    perms = {"planejamento-orcamentario.access"}
    if admin:
        perms.add("planejamento-orcamentario.admin")
    if submit:
        perms.add("planejamento-orcamentario.capex.submit")
    if approve:
        perms.add("planejamento-orcamentario.capex.approve")
    return BudgetActor(user_id=sub, user_name=sub, permissions=frozenset(perms))


def _ready(repo: FakeRepo, *, user: str = "u1", cc: str = "205") -> tuple[str, str]:
    eid = repo.seed_exercise()
    gid = repo.seed_guidance(eid)
    repo.acks.add((user, gid))
    repo.seed_responsibility(user_sub=user, exercise_id=eid, cost_center_id=cc)
    return eid, repo.seed_category()


@pytest.fixture
def ctx():
    repo = FakeRepo()
    plans = CapexPlanUseCases(repository=repo)
    inv = CapexInvestmentUseCases(repository=repo)
    return repo, plans, inv


def test_resolve_cria_e_unicidade(ctx):
    repo, plans, _inv = ctx
    eid, _cat = _ready(repo)
    first = plans.resolve_plan(_actor(), exercise_id=eid, cost_center_id="205")
    second = plans.resolve_plan(_actor(), exercise_id=eid, cost_center_id="205")
    assert first["id"] == second["id"]
    assert first["status"] == "draft"
    assert len(repo.plans) == 1


def test_resolve_recovers_from_create_race(ctx):
    """Corrida: get inicial não vê o plano, create falha por unique → recupera via SELECT."""
    repo, plans, _inv = ctx
    eid, _cat = _ready(repo)
    first = plans.resolve_plan(_actor(), exercise_id=eid, cost_center_id="205")
    original_get = repo.get_capex_plan_by_exercise_cc
    calls = {"n": 0}

    def flaky_get(**kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            return None
        return original_get(**kwargs)

    repo.get_capex_plan_by_exercise_cc = flaky_get  # type: ignore[method-assign]
    second = plans.resolve_plan(_actor(), exercise_id=eid, cost_center_id="205")
    assert second["id"] == first["id"]
    assert calls["n"] >= 2


def test_submissao_valida(ctx):
    repo, plans, _inv = ctx
    eid, cat = _ready(repo)
    repo.seed_complete_investment(exercise_id=eid, category_id=cat)
    plan = plans.resolve_plan(_actor(), exercise_id=eid, cost_center_id="205")
    submitted = plans.submit_plan(_actor(), plan["id"], version=1)
    assert submitted["status"] == "submitted"
    assert submitted["submitted_by"] == "u1"
    assert submitted["submitted_by_name"] == "u1"
    assert any(h["action"] == "submitted" for h in repo.history)


def test_plano_publico_expoe_icone_do_centro_de_custo(ctx):
    repo, plans, _inv = ctx
    eid, cat = _ready(repo)
    repo.seed_complete_investment(exercise_id=eid, category_id=cat)
    plan = plans.resolve_plan(_actor(), exercise_id=eid, cost_center_id="205")
    repo.plans[plan["id"]]["cost_center_icon_key"] = "wrench"
    repo.plans[plan["id"]]["cost_center_name"] = "Manutenção"
    repo.plans[plan["id"]]["cost_center_owner_name"] = "Ana Silva"
    repo.plans[plan["id"]]["investment_count"] = 3
    public = plans.get_plan(_actor(), plan["id"])
    assert public["cost_center_icon_key"] == "wrench"
    assert public["cost_center_name"] == "Manutenção"
    assert public["cost_center_owner_name"] == "Ana Silva"
    assert public["investment_count"] == 3


def test_submissao_sem_investimentos(ctx):
    repo, plans, _inv = ctx
    eid, _cat = _ready(repo)
    plan = plans.resolve_plan(_actor(), exercise_id=eid, cost_center_id="205")
    with pytest.raises(CapexPlanIncompleteError):
        plans.submit_plan(_actor(), plan["id"], version=1)


def test_submissao_item_incompleto(ctx):
    repo, plans, _inv = ctx
    eid, cat = _ready(repo)
    iid = repo.seed_complete_investment(exercise_id=eid, category_id=cat)
    repo.investments[iid]["description"] = None
    plan = plans.resolve_plan(_actor(), exercise_id=eid, cost_center_id="205")
    with pytest.raises(CapexPlanIncompleteError) as exc:
        plans.submit_plan(_actor(), plan["id"], version=1)
    assert exc.value.incomplete_investments
    assert "description" in exc.value.incomplete_investments[0]["missing_fields"]


def test_submissao_sem_responsabilidade(ctx):
    repo, plans, _inv = ctx
    eid, cat = _ready(repo, user="u1")
    gid = repo.guidance[eid]["id"]
    repo.acks.add(("u2", gid))
    repo.seed_complete_investment(exercise_id=eid, category_id=cat)
    plan = plans.resolve_plan(_actor("u1"), exercise_id=eid, cost_center_id="205")
    with pytest.raises(CapexInvestmentCostCenterForbiddenError):
        plans.submit_plan(_actor("u2", submit=True), plan["id"], version=1)


def test_submissao_sem_confirmacao_orientacoes(ctx):
    repo, plans, _inv = ctx
    eid = repo.seed_exercise()
    repo.seed_guidance(eid)
    repo.seed_responsibility(user_sub="u1", exercise_id=eid, cost_center_id="205")
    with pytest.raises(BudgetGuidanceAcknowledgementRequiredError):
        plans.resolve_plan(_actor(), exercise_id=eid, cost_center_id="205")


def test_bloqueio_edicao_quando_submitted(ctx):
    repo, plans, inv = ctx
    eid, cat = _ready(repo)
    iid = repo.seed_complete_investment(exercise_id=eid, category_id=cat)
    plan = plans.resolve_plan(_actor(), exercise_id=eid, cost_center_id="205")
    plans.submit_plan(_actor(), plan["id"], version=1)
    with pytest.raises(CapexPlanLockedError) as exc:
        inv.update_investment(
            _actor(),
            iid,
            {"version": 1, "description": "Alterado"},
        )
    assert exc.value.code == "budget_capex_plan_locked"


def test_request_changes_e_edicao_liberada(ctx):
    repo, plans, inv = ctx
    eid, cat = _ready(repo)
    iid = repo.seed_complete_investment(exercise_id=eid, category_id=cat)
    plan = plans.resolve_plan(_actor("u1"), exercise_id=eid, cost_center_id="205")
    submitted = plans.submit_plan(_actor("u1"), plan["id"], version=1)
    # aprovador diferente
    gid = repo.guidance[eid]["id"]
    repo.acks.add(("approver", gid))
    changed = plans.request_changes(
        _actor("approver", submit=False, approve=True),
        submitted["id"],
        version=submitted["version"],
        comment="Ajustar valores",
    )
    assert changed["status"] == "changes_requested"
    updated = inv.update_investment(
        _actor("u1"),
        iid,
        {"version": 1, "description": "Notebooks revisados"},
    )
    assert updated["description"] == "Notebooks revisados"


def test_reenvio_apos_ajustes(ctx):
    repo, plans, _inv = ctx
    eid, cat = _ready(repo)
    repo.seed_complete_investment(exercise_id=eid, category_id=cat)
    plan = plans.resolve_plan(_actor("u1"), exercise_id=eid, cost_center_id="205")
    submitted = plans.submit_plan(_actor("u1"), plan["id"], version=1)
    gid = repo.guidance[eid]["id"]
    repo.acks.add(("approver", gid))
    changed = plans.request_changes(
        _actor("approver", submit=False, approve=True),
        submitted["id"],
        version=submitted["version"],
        comment="Revise",
    )
    resubmitted = plans.submit_plan(
        _actor("u1"), changed["id"], version=changed["version"]
    )
    assert resubmitted["status"] == "submitted"


def test_reprovacao_sem_comentario(ctx):
    repo, plans, _inv = ctx
    eid, cat = _ready(repo)
    repo.seed_complete_investment(exercise_id=eid, category_id=cat)
    plan = plans.resolve_plan(_actor("u1"), exercise_id=eid, cost_center_id="205")
    submitted = plans.submit_plan(_actor("u1"), plan["id"], version=1)
    gid = repo.guidance[eid]["id"]
    repo.acks.add(("approver", gid))
    with pytest.raises(CapexPlanCommentRequiredError):
        plans.reject_plan(
            _actor("approver", submit=False, approve=True),
            submitted["id"],
            version=submitted["version"],
            comment="   ",
        )


def test_aprovacao_valida_e_bloqueia_edicao(ctx):
    repo, plans, inv = ctx
    eid, cat = _ready(repo)
    iid = repo.seed_complete_investment(exercise_id=eid, category_id=cat)
    plan = plans.resolve_plan(_actor("u1"), exercise_id=eid, cost_center_id="205")
    submitted = plans.submit_plan(_actor("u1"), plan["id"], version=1)
    gid = repo.guidance[eid]["id"]
    repo.acks.add(("approver", gid))
    approved = plans.approve_plan(
        _actor("approver", submit=False, approve=True),
        submitted["id"],
        version=submitted["version"],
    )
    assert approved["status"] == "approved"
    with pytest.raises(CapexPlanLockedError):
        inv.create_investment(
            _actor("u1"),
            {
                "exercise_id": eid,
                "cost_center_id": "205",
                "description": "Novo",
            },
        )


def test_aprovacao_repetida(ctx):
    repo, plans, _inv = ctx
    eid, cat = _ready(repo)
    repo.seed_complete_investment(exercise_id=eid, category_id=cat)
    plan = plans.resolve_plan(_actor("u1"), exercise_id=eid, cost_center_id="205")
    submitted = plans.submit_plan(_actor("u1"), plan["id"], version=1)
    gid = repo.guidance[eid]["id"]
    repo.acks.add(("approver", gid))
    approved = plans.approve_plan(
        _actor("approver", submit=False, approve=True),
        submitted["id"],
        version=submitted["version"],
    )
    with pytest.raises(CapexPlanAlreadyApprovedError):
        plans.approve_plan(
            _actor("approver", submit=False, approve=True),
            approved["id"],
            version=approved["version"],
        )


def test_aprovador_sem_permissao(ctx):
    repo, plans, _inv = ctx
    eid, cat = _ready(repo)
    repo.seed_complete_investment(exercise_id=eid, category_id=cat)
    plan = plans.resolve_plan(_actor("u1"), exercise_id=eid, cost_center_id="205")
    submitted = plans.submit_plan(_actor("u1"), plan["id"], version=1)
    with pytest.raises(CapexApprovalForbiddenError):
        plans.approve_plan(
            _actor("u1", submit=True, approve=False),
            submitted["id"],
            version=submitted["version"],
        )


def test_segregacao_submitter_nao_aprova(ctx):
    repo, plans, _inv = ctx
    eid, cat = _ready(repo)
    repo.seed_complete_investment(exercise_id=eid, category_id=cat)
    # mesmo usuário com submit+approve
    actor = _actor("u1", submit=True, approve=True)
    plan = plans.resolve_plan(actor, exercise_id=eid, cost_center_id="205")
    submitted = plans.submit_plan(actor, plan["id"], version=1)
    with pytest.raises(CapexApprovalForbiddenError):
        plans.approve_plan(actor, submitted["id"], version=submitted["version"])


def test_idor_entre_centros(ctx):
    repo, plans, _inv = ctx
    eid, cat = _ready(repo, user="u1", cc="205")
    repo.seed_complete_investment(exercise_id=eid, category_id=cat, cost_center_id="205")
    plan = plans.resolve_plan(_actor("u1"), exercise_id=eid, cost_center_id="205")
    gid = repo.guidance[eid]["id"]
    repo.acks.add(("u2", gid))
    repo.seed_responsibility(user_sub="u2", exercise_id=eid, cost_center_id="210")
    with pytest.raises(CapexPlanNotFoundError):
        plans.get_plan(_actor("u2", submit=True), plan["id"])


def test_historico(ctx):
    repo, plans, _inv = ctx
    eid, cat = _ready(repo)
    repo.seed_complete_investment(exercise_id=eid, category_id=cat)
    plan = plans.resolve_plan(_actor("u1"), exercise_id=eid, cost_center_id="205")
    submitted = plans.submit_plan(_actor("u1"), plan["id"], version=1)
    hist = plans.list_history(_actor("u1"), submitted["id"])
    actions = [h["action"] for h in hist["items"]]
    assert "created" in actions
    assert "submitted" in actions


def test_conflito_versao(ctx):
    repo, plans, _inv = ctx
    eid, cat = _ready(repo)
    repo.seed_complete_investment(exercise_id=eid, category_id=cat)
    plan = plans.resolve_plan(_actor("u1"), exercise_id=eid, cost_center_id="205")
    with pytest.raises(CapexPlanVersionConflictError):
        plans.submit_plan(_actor("u1"), plan["id"], version=99)


def test_resolve_plans_separated_by_branch(ctx):
    repo, plans, _inv = ctx
    eid, _cat = _ready(repo)
    repo.units = {"01": {"code": "01", "active": True}, "02": {"code": "02", "active": True}}
    repo.upsert_org_cost_center(
        {
            "branch": "02",
            "code": "205",
            "name": "TI ES",
            "unit_code": "02",
            "source": "manual",
        }
    )
    repo.seed_responsibility(user_sub="u1", exercise_id=eid, cost_center_id="205")
    repo.responsibilities.append(
        {
            "id": str(uuid4()),
            "user_sub": "u1",
            "exercise_id": eid,
            "module": "capex",
            "cost_center_id": "205",
            "unit_id": "02",
            "area_id": None,
            "is_active": True,
            "valid_from": None,
            "valid_until": None,
        }
    )
    p01 = plans.resolve_plan(_actor(), exercise_id=eid, cost_center_id="205", unit_id="01")
    p02 = plans.resolve_plan(_actor(), exercise_id=eid, cost_center_id="205", unit_id="02")
    assert p01["id"] != p02["id"]
    assert p01["branch"] == "01"
    assert p02["branch"] == "02"


def test_fila_paginada_filtrada(ctx):
    repo, plans, _inv = ctx
    eid, cat = _ready(repo)
    repo.seed_complete_investment(exercise_id=eid, category_id=cat)
    plan = plans.resolve_plan(_actor("u1"), exercise_id=eid, cost_center_id="205")
    plans.submit_plan(_actor("u1"), plan["id"], version=1)
    gid = repo.guidance[eid]["id"]
    repo.acks.add(("approver", gid))
    queue = plans.list_review_queue(
        _actor("approver", submit=False, approve=True),
        exercise_id=eid,
        cost_center_id="205",
        page=1,
        page_size=10,
    )
    assert queue["pagination"]["total"] == 1
    assert queue["items"][0]["status"] == "submitted"


def _approver(repo: FakeRepo, exercise_id: str) -> BudgetActor:
    gid = repo.guidance[exercise_id]["id"]
    repo.acks.add(("approver", gid))
    return _actor("approver", submit=False, approve=True)


def test_aprovacao_por_investimento_nao_fecha_plano_parcial(ctx):
    repo, plans, _inv = ctx
    eid, cat = _ready(repo)
    first = repo.seed_complete_investment(exercise_id=eid, category_id=cat)
    second = repo.seed_complete_investment(exercise_id=eid, category_id=cat)
    repo.investments[second]["description"] = "Impressora"
    plan = plans.resolve_plan(_actor("u1"), exercise_id=eid, cost_center_id="205")
    submitted = plans.submit_plan(_actor("u1"), plan["id"], version=1)
    actor = _approver(repo, eid)
    detail = plans.decide_investment(
        actor,
        submitted["id"],
        first,
        version=submitted["version"],
        action="approve",
    )
    assert detail["status"] == "submitted"
    by_id = {row["id"]: row for row in detail["investments"]}
    assert by_id[first]["review_status"] == "approved"
    assert by_id[second]["review_status"] == "pending"


def test_reprovacao_investimento_exige_comentario(ctx):
    repo, plans, _inv = ctx
    eid, cat = _ready(repo)
    iid = repo.seed_complete_investment(exercise_id=eid, category_id=cat)
    plan = plans.resolve_plan(_actor("u1"), exercise_id=eid, cost_center_id="205")
    submitted = plans.submit_plan(_actor("u1"), plan["id"], version=1)
    actor = _approver(repo, eid)
    with pytest.raises(CapexPlanCommentRequiredError):
        plans.decide_investment(
            actor,
            submitted["id"],
            iid,
            version=submitted["version"],
            action="reject",
            comment="  ",
        )


def test_decisao_mista_fecha_plano_aprovado(ctx):
    repo, plans, _inv = ctx
    eid, cat = _ready(repo)
    first = repo.seed_complete_investment(exercise_id=eid, category_id=cat)
    second = repo.seed_complete_investment(exercise_id=eid, category_id=cat)
    repo.investments[second]["description"] = "Impressora"
    plan = plans.resolve_plan(_actor("u1"), exercise_id=eid, cost_center_id="205")
    submitted = plans.submit_plan(_actor("u1"), plan["id"], version=1)
    actor = _approver(repo, eid)
    after_first = plans.decide_investment(
        actor,
        submitted["id"],
        first,
        version=submitted["version"],
        action="approve",
    )
    closed = plans.decide_investment(
        actor,
        after_first["id"],
        second,
        version=after_first["version"],
        action="reject",
        comment="Fora do teto do centro",
    )
    assert closed["status"] == "approved"
    by_id = {row["id"]: row for row in closed["investments"]}
    assert by_id[first]["review_status"] == "approved"
    assert by_id[second]["review_status"] == "rejected"
    actions = [h["action"] for h in plans.list_history(actor, closed["id"])["items"]]
    assert "investment_approved" in actions
    assert "investment_rejected" in actions
    assert "approved" in actions


def test_todos_reprovados_fecha_plano_reprovado(ctx):
    repo, plans, _inv = ctx
    eid, cat = _ready(repo)
    iid = repo.seed_complete_investment(exercise_id=eid, category_id=cat)
    plan = plans.resolve_plan(_actor("u1"), exercise_id=eid, cost_center_id="205")
    submitted = plans.submit_plan(_actor("u1"), plan["id"], version=1)
    actor = _approver(repo, eid)
    closed = plans.decide_investment(
        actor,
        submitted["id"],
        iid,
        version=submitted["version"],
        action="reject",
        comment="Não cabe no ciclo",
    )
    assert closed["status"] == "rejected"


def test_investimento_de_outro_plano(ctx):
    repo, plans, _inv = ctx
    eid, cat = _ready(repo)
    iid = repo.seed_complete_investment(exercise_id=eid, category_id=cat)
    plan = plans.resolve_plan(_actor("u1"), exercise_id=eid, cost_center_id="205")
    submitted = plans.submit_plan(_actor("u1"), plan["id"], version=1)
    actor = _approver(repo, eid)
    with pytest.raises(CapexInvestmentNotFoundError):
        plans.decide_investment(
            actor,
            submitted["id"],
            "missing-id",
            version=submitted["version"],
            action="approve",
        )
    del iid


def test_decisao_item_so_em_submitted(ctx):
    repo, plans, _inv = ctx
    eid, cat = _ready(repo)
    iid = repo.seed_complete_investment(exercise_id=eid, category_id=cat)
    plan = plans.resolve_plan(_actor("u1"), exercise_id=eid, cost_center_id="205")
    actor = _approver(repo, eid)
    with pytest.raises(CapexPlanInvalidTransitionError):
        plans.decide_investment(
            actor,
            plan["id"],
            iid,
            version=plan["version"],
            action="approve",
        )
