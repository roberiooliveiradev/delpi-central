from datetime import date

import pytest

from it_portal_app.application.action_plan_service import ActionPlanService
from it_portal_app.application.dashboard_service import DashboardService
from it_portal_app.application.ports import Actor, ServerQuery
from it_portal_app.application.server_service import ServerService
from it_portal_app.domain.errors import ConflictError, NotFoundError, ValidationError

from tests.conftest import USER_ID, server_payload
from tests.fakes import InMemoryItPortalRepository

TODAY = date(2026, 11, 10)
ACTOR = Actor(id=USER_ID, name="Ana TI")


@pytest.fixture
def repo():
    return InMemoryItPortalRepository()


@pytest.fixture
def servers(repo):
    return ServerService(repo)


@pytest.fixture
def actions(repo):
    return ActionPlanService(repo, lambda: TODAY)


def test_create_server_records_author_and_audit(servers, repo):
    created = servers.create_server(server_payload(), ACTOR)
    assert created["code"] == "SRV-0001"
    assert created["created_by_name"] == "Ana TI"
    assert repo.audit[-1]["event_type"] == "server_created"
    assert repo.audit[-1]["actor_id"] == USER_ID


def test_identity_uniqueness_considers_unit_and_environment(servers):
    servers.create_server(server_payload(), ACTOR)
    with pytest.raises(ConflictError):
        servers.create_server(server_payload(hostname="SRV-ERP-01.delpi.local"), ACTOR)
    servers.create_server(server_payload(environment="staging"), ACTOR)
    servers.create_server(server_payload(unit_code="02"), ACTOR)


def test_update_requires_current_revision_and_audits_diff(servers, repo):
    created = servers.create_server(server_payload(), ACTOR)
    updated = servers.update_server(
        created["id"], server_payload(criticality="high"), created["revision"], ACTOR
    )
    assert updated["revision"] == 2
    assert repo.audit[-1]["changes"] == {"criticality": {"from": "critical", "to": "high"}}
    with pytest.raises(ConflictError) as exc:
        servers.update_server(created["id"], server_payload(name="Outro"), 1, ACTOR)
    assert exc.value.code == "revision_conflict"


def test_archive_blocked_with_open_action_plans(servers, actions):
    created = servers.create_server(server_payload(), ACTOR)
    plan = actions.create_action_plan(
        created["id"], {"title": "Patch", "priority": "high"}, ACTOR
    )
    with pytest.raises(ConflictError) as exc:
        servers.archive_server(created["id"], created["revision"], ACTOR)
    assert exc.value.code == "server_has_open_action_plans"

    actions.change_status(plan["id"], "done", plan["revision"], ACTOR)
    archived = servers.archive_server(created["id"], created["revision"], ACTOR)
    assert archived["archived"] is True


def test_archived_server_rejects_edits_notes_and_actions(servers, actions):
    created = servers.create_server(server_payload(), ACTOR)
    archived = servers.archive_server(created["id"], created["revision"], ACTOR)
    for call in (
        lambda: servers.update_server(created["id"], server_payload(), archived["revision"], ACTOR),
        lambda: servers.add_note(created["id"], "Nota", ACTOR),
        lambda: actions.create_action_plan(created["id"], {"title": "x", "priority": "low"}, ACTOR),
    ):
        with pytest.raises(ConflictError) as exc:
            call()
        assert exc.value.code == "server_archived"

    restored = servers.restore_server(created["id"], archived["revision"], ACTOR)
    assert restored["archived"] is False
    assert servers.list_servers(ServerQuery())["total"] == 1


def test_archived_hostname_can_be_registered_again_but_not_restored_over_it(servers):
    created = servers.create_server(server_payload(), ACTOR)
    archived = servers.archive_server(created["id"], created["revision"], ACTOR)
    servers.create_server(server_payload(), ACTOR)
    with pytest.raises(ConflictError):
        servers.restore_server(created["id"], archived["revision"], ACTOR)


def test_unknown_server_is_not_found(servers):
    with pytest.raises(NotFoundError):
        servers.get_server("00000000-0000-0000-0000-000000000000")


def test_list_query_validation(servers):
    with pytest.raises(ValidationError):
        servers.list_servers(ServerQuery(environment="prod"))
    page = servers.list_servers(ServerQuery(page=0, page_size=1000))
    assert page["page"] == 1
    assert page["page_size"] == 100


def test_action_plan_status_flow_and_overdue(servers, actions):
    server = servers.create_server(server_payload(), ACTOR)
    plan = actions.create_action_plan(
        server["id"],
        {"title": "Renovar certificado", "priority": "urgent", "due_date": "2026-11-01"},
        ACTOR,
    )
    assert plan["status"] == "pending"
    assert plan["is_overdue"] is True

    started = actions.change_status(plan["id"], "in_progress", plan["revision"], ACTOR)
    done = actions.change_status(plan["id"], "done", started["revision"], ACTOR)
    assert done["completed_at"] is not None
    assert done["is_overdue"] is False

    with pytest.raises(ConflictError):
        actions.change_status(plan["id"], "cancelled", done["revision"], ACTOR)
    reopened = actions.change_status(plan["id"], "in_progress", done["revision"], ACTOR)
    assert reopened["completed_at"] is None


def test_dashboard_hides_action_section_without_permission(repo, servers, actions):
    server = servers.create_server(server_payload(), ACTOR)
    servers.create_server(server_payload(hostname="srv-dev", criticality="low"), ACTOR)
    actions.create_action_plan(
        server["id"], {"title": "Backup", "priority": "medium", "due_date": "2026-11-05"}, ACTOR
    )
    dashboard = DashboardService(repo, lambda: TODAY)

    full = dashboard.overview(include_action_plans=True)
    assert full["servers"] == {"total": 2, "high_or_critical": 1}
    assert full["action_plans"] == {"open": 1, "overdue": 1}
    assert full["attention_action_plans"][0]["is_overdue"] is True

    restricted = dashboard.overview(include_action_plans=False)
    assert restricted["action_plans"] is None
    assert restricted["attention_action_plans"] is None


def test_dashboard_empty_inventory_returns_zeros(repo):
    overview = DashboardService(repo, lambda: TODAY).overview(include_action_plans=True)
    assert overview["servers"] == {"total": 0, "high_or_critical": 0}
    assert overview["recent_servers"] == []
    assert overview["attention_action_plans"] == []
