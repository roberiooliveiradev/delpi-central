"""Testes Fase 3C.1 — workflow de submissão/aprovação do Orçamento de Pessoal."""
from __future__ import annotations

import pytest

from app.application.use_cases.planejamento_orcamentario.budget_planning_use_cases import (
    BudgetActor,
)
from app.application.use_cases.planejamento_orcamentario.personnel_plan_use_cases import (
    PersonnelPlanUseCases,
)
from app.domain.services.planejamento_orcamentario.exceptions import (
    BudgetGuidanceAcknowledgementRequiredError,
    PersonnelApprovalForbiddenError,
    PersonnelPlanAlreadyApprovedError,
    PersonnelPlanCommentRequiredError,
    PersonnelPlanIncompleteError,
    PersonnelPlanInvalidTransitionError,
    PersonnelPlanLockedError,
    PersonnelPlanNotFoundError,
    PersonnelPlanVersionConflictError,
    PersonnelResponsibilityRequiredError,
)
from tests.unit.planejamento_orcamentario.test_personnel_plan_use_cases import FakeRepo


def _actor(
    sub: str = "u1",
    *,
    submit: bool = True,
    approve: bool = False,
    edit: bool = True,
    admin: bool = False,
) -> BudgetActor:
    perms = {
        "planejamento-orcamentario.access",
        "planejamento-orcamentario.personnel.view",
    }
    if edit:
        perms.add("planejamento-orcamentario.personnel.edit")
    if submit:
        perms.add("planejamento-orcamentario.personnel.submit")
    if approve:
        perms.add("planejamento-orcamentario.personnel.approve")
    if admin:
        perms.add("planejamento-orcamentario.admin")
    return BudgetActor(user_id=sub, user_name=sub, permissions=frozenset(perms))


def _ready(repo: FakeRepo, *, user: str = "u1", cc: str = "205", unit_id: str = "01") -> str:
    eid = repo.seed_exercise()
    gid = repo.seed_guidance(eid)
    repo.seed_ack(user, gid)
    repo.seed_responsibility(
        user_sub=user, exercise_id=eid, cost_center_id=cc, unit_id=unit_id
    )
    return eid


def _complete_line(uc: PersonnelPlanUseCases, actor: BudgetActor, plan_id: str, name: str = "Analista"):
    return uc.create_line(
        actor,
        plan_id,
        {
            "position_name": name,
            "headcount_dec_2025": 1,
            "headcount_oct_2026": 2,
            "headcount_forecast": 2,
            "headcount_dec_2027": 3,
        },
    )


@pytest.fixture
def ctx():
    repo = FakeRepo()
    return repo, PersonnelPlanUseCases(repository=repo)


def test_submissao_valida(ctx):
    repo, uc = ctx
    eid = _ready(repo)
    actor = _actor()
    plan = uc.resolve_plan(actor, exercise_id=eid, unit_id="01", cost_center_id="205")
    _complete_line(uc, actor, plan["id"])
    submitted = uc.submit_plan(actor, plan["id"], version=1)
    assert submitted["status"] == "submitted"
    assert submitted["submitted_by"] == "u1"
    assert submitted["submitted_by_name"] == "u1"
    assert submitted["version"] == 2
    assert any(h["action"] == "submitted" for h in repo.history)


def test_submissao_sem_linhas(ctx):
    repo, uc = ctx
    eid = _ready(repo)
    actor = _actor()
    plan = uc.resolve_plan(actor, exercise_id=eid, unit_id="01", cost_center_id="205")
    with pytest.raises(PersonnelPlanIncompleteError) as exc:
        uc.submit_plan(actor, plan["id"], version=1)
    assert exc.value.code == "budget_personnel_plan_incomplete"


def test_submissao_linha_incompleta(ctx):
    repo, uc = ctx
    eid = _ready(repo)
    actor = _actor()
    plan = uc.resolve_plan(actor, exercise_id=eid, unit_id="01", cost_center_id="205")
    uc.create_line(
        actor,
        plan["id"],
        {"position_name": "Operador", "headcount_dec_2025": 1},
    )
    with pytest.raises(PersonnelPlanIncompleteError) as exc:
        uc.submit_plan(actor, plan["id"], version=1)
    assert exc.value.incomplete_lines
    missing = exc.value.incomplete_lines[0]["missing_fields"]
    assert "headcount_oct_2026" in missing
    assert "headcount_forecast" in missing
    assert "headcount_dec_2027" in missing


def test_submissao_sem_responsabilidade(ctx):
    repo, uc = ctx
    eid = _ready(repo, user="u1")
    gid = repo.guidance[eid]["id"]
    repo.seed_ack("u2", gid)
    actor1 = _actor("u1")
    plan = uc.resolve_plan(actor1, exercise_id=eid, unit_id="01", cost_center_id="205")
    _complete_line(uc, actor1, plan["id"])
    with pytest.raises(PersonnelResponsibilityRequiredError):
        uc.submit_plan(_actor("u2", submit=True), plan["id"], version=1)


def test_submissao_sem_confirmacao_orientacoes(ctx):
    repo, uc = ctx
    eid = repo.seed_exercise()
    repo.seed_guidance(eid)
    repo.seed_responsibility(user_sub="u1", exercise_id=eid, cost_center_id="205")
    with pytest.raises(BudgetGuidanceAcknowledgementRequiredError):
        uc.resolve_plan(
            _actor(), exercise_id=eid, unit_id="01", cost_center_id="205"
        )


def test_bloqueio_apos_submissao(ctx):
    repo, uc = ctx
    eid = _ready(repo)
    actor = _actor()
    plan = uc.resolve_plan(actor, exercise_id=eid, unit_id="01", cost_center_id="205")
    line = _complete_line(uc, actor, plan["id"])
    uc.submit_plan(actor, plan["id"], version=1)
    with pytest.raises(PersonnelPlanLockedError) as exc:
        uc.create_line(actor, plan["id"], {"position_name": "Novo cargo"})
    assert exc.value.code == "budget_personnel_plan_locked"
    with pytest.raises(PersonnelPlanLockedError):
        uc.update_line(
            actor, line["id"], {"version": 1, "headcount_dec_2025": 9}
        )
    with pytest.raises(PersonnelPlanLockedError):
        uc.archive_line(actor, line["id"])


def test_request_changes_e_edicao_liberada(ctx):
    repo, uc = ctx
    eid = _ready(repo)
    actor = _actor("u1")
    plan = uc.resolve_plan(actor, exercise_id=eid, unit_id="01", cost_center_id="205")
    line = _complete_line(uc, actor, plan["id"])
    submitted = uc.submit_plan(actor, plan["id"], version=1)
    gid = repo.guidance[eid]["id"]
    repo.seed_ack("approver", gid)
    changed = uc.request_changes(
        _actor("approver", submit=False, approve=True),
        submitted["id"],
        version=submitted["version"],
        comment="Ajustar headcount",
    )
    assert changed["status"] == "changes_requested"
    updated = uc.update_line(
        actor, line["id"], {"version": line["version"], "headcount_dec_2027": 5}
    )
    assert updated["headcount_dec_2027"] == 5


def test_reenvio_apos_ajustes(ctx):
    repo, uc = ctx
    eid = _ready(repo)
    actor = _actor("u1")
    plan = uc.resolve_plan(actor, exercise_id=eid, unit_id="01", cost_center_id="205")
    _complete_line(uc, actor, plan["id"])
    submitted = uc.submit_plan(actor, plan["id"], version=1)
    gid = repo.guidance[eid]["id"]
    repo.seed_ack("approver", gid)
    changed = uc.request_changes(
        _actor("approver", submit=False, approve=True),
        submitted["id"],
        version=submitted["version"],
        comment="Revise",
    )
    resubmitted = uc.submit_plan(actor, changed["id"], version=changed["version"])
    assert resubmitted["status"] == "submitted"


def test_reprovacao_sem_comentario(ctx):
    repo, uc = ctx
    eid = _ready(repo)
    actor = _actor("u1")
    plan = uc.resolve_plan(actor, exercise_id=eid, unit_id="01", cost_center_id="205")
    _complete_line(uc, actor, plan["id"])
    submitted = uc.submit_plan(actor, plan["id"], version=1)
    gid = repo.guidance[eid]["id"]
    repo.seed_ack("approver", gid)
    with pytest.raises(PersonnelPlanCommentRequiredError):
        uc.reject_plan(
            _actor("approver", submit=False, approve=True),
            submitted["id"],
            version=submitted["version"],
            comment="   ",
        )


def test_reprovacao_valida_e_bloqueia_edicao(ctx):
    repo, uc = ctx
    eid = _ready(repo)
    actor = _actor("u1")
    plan = uc.resolve_plan(actor, exercise_id=eid, unit_id="01", cost_center_id="205")
    line = _complete_line(uc, actor, plan["id"])
    submitted = uc.submit_plan(actor, plan["id"], version=1)
    gid = repo.guidance[eid]["id"]
    repo.seed_ack("approver", gid)
    rejected = uc.reject_plan(
        _actor("approver", submit=False, approve=True),
        submitted["id"],
        version=submitted["version"],
        comment="Fora do escopo orçamentário",
    )
    assert rejected["status"] == "rejected"
    with pytest.raises(PersonnelPlanLockedError):
        uc.update_line(
            actor, line["id"], {"version": line["version"], "headcount_dec_2025": 9}
        )
    with pytest.raises(PersonnelPlanInvalidTransitionError):
        uc.submit_plan(actor, rejected["id"], version=rejected["version"])


def test_transicao_invalida_aprovar_draft(ctx):
    repo, uc = ctx
    eid = _ready(repo)
    actor = _actor("u1")
    plan = uc.resolve_plan(actor, exercise_id=eid, unit_id="01", cost_center_id="205")
    _complete_line(uc, actor, plan["id"])
    gid = repo.guidance[eid]["id"]
    repo.seed_ack("approver", gid)
    with pytest.raises(PersonnelPlanInvalidTransitionError) as exc:
        uc.approve_plan(
            _actor("approver", submit=False, approve=True),
            plan["id"],
            version=plan["version"],
        )
    assert exc.value.code == "budget_personnel_plan_invalid_transition"


def test_admin_pode_decidir_plano_que_submeteu(ctx):
    repo, uc = ctx
    eid = _ready(repo, user="u1")
    admin = _actor("u1", submit=True, approve=True, admin=True)
    plan = uc.resolve_plan(admin, exercise_id=eid, unit_id="01", cost_center_id="205")
    _complete_line(uc, admin, plan["id"])
    submitted = uc.submit_plan(admin, plan["id"], version=1)
    approved = uc.approve_plan(
        admin, submitted["id"], version=submitted["version"]
    )
    assert approved["status"] == "approved"
    assert approved["reviewed_by"] == "u1"


def test_aprovacao_valida(ctx):
    repo, uc = ctx
    eid = _ready(repo)
    actor = _actor("u1")
    plan = uc.resolve_plan(actor, exercise_id=eid, unit_id="01", cost_center_id="205")
    _complete_line(uc, actor, plan["id"])
    submitted = uc.submit_plan(actor, plan["id"], version=1)
    gid = repo.guidance[eid]["id"]
    repo.seed_ack("approver", gid)
    approved = uc.approve_plan(
        _actor("approver", submit=False, approve=True),
        submitted["id"],
        version=submitted["version"],
    )
    assert approved["status"] == "approved"
    assert approved["reviewed_by"] == "approver"


def test_aprovacao_repetida(ctx):
    repo, uc = ctx
    eid = _ready(repo)
    actor = _actor("u1")
    plan = uc.resolve_plan(actor, exercise_id=eid, unit_id="01", cost_center_id="205")
    _complete_line(uc, actor, plan["id"])
    submitted = uc.submit_plan(actor, plan["id"], version=1)
    gid = repo.guidance[eid]["id"]
    repo.seed_ack("approver", gid)
    approver = _actor("approver", submit=False, approve=True)
    approved = uc.approve_plan(
        approver, submitted["id"], version=submitted["version"]
    )
    with pytest.raises(PersonnelPlanAlreadyApprovedError):
        uc.approve_plan(approver, approved["id"], version=approved["version"])


def test_segregacao_submitter_nao_decide(ctx):
    repo, uc = ctx
    eid = _ready(repo)
    actor = _actor("u1", submit=True, approve=True)
    plan = uc.resolve_plan(actor, exercise_id=eid, unit_id="01", cost_center_id="205")
    _complete_line(uc, actor, plan["id"])
    submitted = uc.submit_plan(actor, plan["id"], version=1)
    with pytest.raises(PersonnelApprovalForbiddenError) as exc:
        uc.approve_plan(actor, submitted["id"], version=submitted["version"])
    assert exc.value.code == "budget_personnel_approval_forbidden"


def test_edicao_apos_aprovacao_bloqueada(ctx):
    repo, uc = ctx
    eid = _ready(repo)
    actor = _actor("u1")
    plan = uc.resolve_plan(actor, exercise_id=eid, unit_id="01", cost_center_id="205")
    line = _complete_line(uc, actor, plan["id"])
    submitted = uc.submit_plan(actor, plan["id"], version=1)
    gid = repo.guidance[eid]["id"]
    repo.seed_ack("approver", gid)
    uc.approve_plan(
        _actor("approver", submit=False, approve=True),
        submitted["id"],
        version=submitted["version"],
    )
    with pytest.raises(PersonnelPlanLockedError):
        uc.update_line(
            actor, line["id"], {"version": line["version"], "headcount_dec_2025": 99}
        )


def test_conflito_versao(ctx):
    repo, uc = ctx
    eid = _ready(repo)
    actor = _actor()
    plan = uc.resolve_plan(actor, exercise_id=eid, unit_id="01", cost_center_id="205")
    _complete_line(uc, actor, plan["id"])
    with pytest.raises(PersonnelPlanVersionConflictError) as exc:
        uc.submit_plan(actor, plan["id"], version=99)
    assert exc.value.code == "budget_personnel_plan_version_conflict"


def test_historico(ctx):
    repo, uc = ctx
    eid = _ready(repo)
    actor = _actor("u1")
    plan = uc.resolve_plan(actor, exercise_id=eid, unit_id="01", cost_center_id="205")
    _complete_line(uc, actor, plan["id"])
    submitted = uc.submit_plan(actor, plan["id"], version=1)
    hist = uc.list_history(actor, submitted["id"])
    actions = [h["action"] for h in hist["items"]]
    assert "created" in actions
    assert "submitted" in actions


def test_fila_paginada_e_filtrada(ctx):
    repo, uc = ctx
    eid = _ready(repo)
    actor = _actor("u1")
    plan = uc.resolve_plan(actor, exercise_id=eid, unit_id="01", cost_center_id="205")
    _complete_line(uc, actor, plan["id"])
    uc.submit_plan(actor, plan["id"], version=1)
    gid = repo.guidance[eid]["id"]
    repo.seed_ack("approver", gid)
    queue = uc.list_review_queue(
        _actor("approver", submit=False, approve=True),
        exercise_id=eid,
        unit_id="01",
        cost_center_id="205",
        status="submitted",
        submitted_by="u1",
        page=1,
        page_size=10,
    )
    assert queue["pagination"]["total"] == 1
    assert queue["items"][0]["status"] == "submitted"


def test_isolamento_filiais_01_e_02(ctx):
    repo, uc = ctx
    eid = _ready(repo, unit_id="01")
    repo.seed_responsibility(
        user_sub="u1", exercise_id=eid, cost_center_id="205", unit_id="02"
    )
    actor = _actor()
    p01 = uc.resolve_plan(actor, exercise_id=eid, unit_id="01", cost_center_id="205")
    p02 = uc.resolve_plan(actor, exercise_id=eid, unit_id="02", cost_center_id="205")
    assert p01["id"] != p02["id"]
    assert p01["branch"] == "01"
    assert p02["branch"] == "02"
    _complete_line(uc, actor, p01["id"], "Analista SC")
    _complete_line(uc, actor, p02["id"], "Analista ES")
    s01 = uc.submit_plan(actor, p01["id"], version=1)
    s02 = uc.submit_plan(actor, p02["id"], version=1)
    assert s01["id"] != s02["id"]
    gid = repo.guidance[eid]["id"]
    repo.seed_ack("approver", gid)
    q01 = uc.list_review_queue(
        _actor("approver", submit=False, approve=True),
        exercise_id=eid,
        unit_id="01",
    )
    q02 = uc.list_review_queue(
        _actor("approver", submit=False, approve=True),
        exercise_id=eid,
        unit_id="02",
    )
    assert q01["pagination"]["total"] == 1
    assert q02["pagination"]["total"] == 1
    assert q01["items"][0]["unit_id"] == "01"
    assert q02["items"][0]["unit_id"] == "02"


def test_idor_entre_centros(ctx):
    repo, uc = ctx
    eid = _ready(repo, user="u1", cc="205")
    actor1 = _actor("u1")
    plan = uc.resolve_plan(actor1, exercise_id=eid, unit_id="01", cost_center_id="205")
    gid = repo.guidance[eid]["id"]
    repo.seed_ack("u2", gid)
    repo.seed_responsibility(
        user_sub="u2", exercise_id=eid, cost_center_id="210", unit_id="01"
    )
    with pytest.raises(PersonnelPlanNotFoundError):
        uc.get_plan(_actor("u2", submit=True), plan["id"])


def test_review_detail_e_endpoints_router():
    from app.interface.http.routes.planejamento_orcamentario import (
        planejamento_orcamentario_router as router_mod,
    )

    paths = {getattr(r, "path", None) for r in router_mod.router.routes}
    prefix = "/planejamento-orcamentario"
    assert f"{prefix}/personnel/plans/{{plan_id}}/submit" in paths
    assert f"{prefix}/personnel/plans/{{plan_id}}/history" in paths
    assert f"{prefix}/personnel/review-queue" in paths
    assert f"{prefix}/personnel/review/{{plan_id}}" in paths
    assert f"{prefix}/personnel/review/{{plan_id}}/request-changes" in paths
    assert f"{prefix}/personnel/review/{{plan_id}}/reject" in paths
    assert f"{prefix}/personnel/review/{{plan_id}}/approve" in paths


def test_regressao_capex_e_pessoal_workflow(ctx):
    """Garante que constantes/erros CAPEX e Pessoal permanecem distintos e usáveis juntos."""
    from app.application.use_cases.planejamento_orcamentario.capex_plan_use_cases import (
        CapexPlanUseCases,
    )
    from app.domain.services.planejamento_orcamentario import capex_plan_constants as cc
    from app.domain.services.planejamento_orcamentario import personnel_budget_constants as pc
    from tests.unit.planejamento_orcamentario.test_capex_plan_use_cases import (
        FakeRepo as CapexFakeRepo,
    )
    from tests.unit.planejamento_orcamentario.test_capex_plan_use_cases import (
        _actor as capex_actor,
    )
    from tests.unit.planejamento_orcamentario.test_capex_plan_use_cases import (
        _ready as capex_ready,
    )

    assert cc.STATUS_SUBMITTED == pc.STATUS_SUBMITTED
    assert cc.PLAN_TRANSITIONS.keys() == pc.PLAN_TRANSITIONS.keys()

    # Pessoal
    repo_p, uc_p = ctx
    eid_p = _ready(repo_p)
    actor_p = _actor()
    plan_p = uc_p.resolve_plan(
        actor_p, exercise_id=eid_p, unit_id="01", cost_center_id="205"
    )
    _complete_line(uc_p, actor_p, plan_p["id"])
    sub_p = uc_p.submit_plan(actor_p, plan_p["id"], version=1)
    assert sub_p["status"] == "submitted"

    # CAPEX (fake próprio)
    repo_c = CapexFakeRepo()
    plans_c = CapexPlanUseCases(repository=repo_c)
    eid_c, cat = capex_ready(repo_c)
    repo_c.seed_complete_investment(exercise_id=eid_c, category_id=cat)
    plan_c = plans_c.resolve_plan(
        capex_actor(), exercise_id=eid_c, cost_center_id="205"
    )
    sub_c = plans_c.submit_plan(capex_actor(), plan_c["id"], version=1)
    assert sub_c["status"] == "submitted"
