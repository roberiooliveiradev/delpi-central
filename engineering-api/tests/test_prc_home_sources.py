"""Testes das fontes PRC in-process da Home (Opção A — ledger §31).

Cobre: identidade requestId, escopo mine × queue, AuthZ de objeto,
totais pré-paginação, isolamento de falha e mapeamento do href oficial.
"""

from __future__ import annotations

import pytest

from engineering_app.application.ports.home_sources import HomeSourceContext
from engineering_app.application.use_cases.product_registration.service import (
    ProductRegistrationService,
)
from engineering_app.domain.product_registration.errors import PrcForbiddenError
from engineering_app.infrastructure.gateways.prc_home_sources import (
    PrcMineHomeSource,
    PrcQueueHomeSource,
)
from engineering_app.infrastructure.persistence.product_registration.in_memory_repository import (
    InMemoryProductRegistrationRepository,
)

ENG_ACCESS = "engineering.access"
MR_ACCESS = "my-requests.access"
MR_PRC_CREATE = "my-requests.raw-material-creation"


def _ctx(user_id: str, permissions: frozenset[str]) -> HomeSourceContext:
    return HomeSourceContext(
        user_id=user_id,
        access_token="tok",
        request_id="req-1",
        permissions=permissions,
    )


def _seed(repo, *, rid: str, requester: str, status: str = "submitted",
          official: str | None = None, description: str | None = "MP teste",
          assignee: str | None = None):
    repo.create_request(
        request={
            "id": rid,
            "request_type": "create",
            "status": status,
            "source": "my-requests",
            "requester_subject": requester,
            "requester_display_name": "Solicitante",
            "assigned_to_subject": assignee,
            "assigned_to_display_name": None,
            "official_product_code": official,
            "row_version": 1,
            "created_at": "2026-11-13T12:00:00+00:00",
            "requested_payload": {"description": description},
            "external_request_id": "ext-1",
        },
        draft={},
        event={"event_type": "submitted", "sequence_number": 1},
    )


@pytest.fixture
def service_repo():
    repo = InMemoryProductRegistrationRepository()
    service = ProductRegistrationService(repo, official_reader=None)
    return service


@pytest.fixture
def queue_source(service_repo):
    return PrcQueueHomeSource(lambda: service_repo)


@pytest.fixture
def mine_source(service_repo):
    return PrcMineHomeSource(lambda: service_repo)


RID_A = "11111111-1111-4111-8111-111111111111"
RID_B = "22222222-2222-4222-8222-222222222222"


async def test_queue_source_analyst_sees_all_cases(service_repo, queue_source):
    _seed(service_repo._repo, rid=RID_A, requester="user-1")
    _seed(service_repo._repo, rid=RID_B, requester="user-2")
    ctx = _ctx("analyst-1", frozenset({ENG_ACCESS}))

    out = await queue_source.fetch(ctx, limit=10)

    assert out.status == "available"
    assert out.total == 2
    assert {i.id for i in out.items} == {RID_A, RID_B}
    assert all(i.kind == "task" for i in out.items)
    assert all(i.source == "engineering-api" for i in out.items)
    assert all(
        i.href == f"/apps/engineering/product-registration/{i.id}"
        for i in out.items
    )


async def test_mine_source_scopes_to_requester(service_repo, mine_source):
    _seed(service_repo._repo, rid=RID_A, requester="user-1")
    _seed(service_repo._repo, rid=RID_B, requester="user-2")
    ctx = _ctx("user-1", frozenset({MR_ACCESS, MR_PRC_CREATE}))

    out = await mine_source.fetch(ctx, limit=10)

    assert out.status == "available"
    assert out.total == 1
    assert [i.id for i in out.items] == [RID_A]


async def test_mine_source_analyst_still_scoped_own(service_repo, mine_source):
    """Analista na seção ``requests`` vê somente os próprios casos."""
    _seed(service_repo._repo, rid=RID_A, requester="analyst-1")
    _seed(service_repo._repo, rid=RID_B, requester="user-2")
    ctx = _ctx("analyst-1", frozenset({ENG_ACCESS}))

    out = await mine_source.fetch(ctx, limit=10)

    assert out.status == "available"
    assert out.total == 1
    assert [i.id for i in out.items] == [RID_A]


async def test_mine_excludes_assigned_only_cases(service_repo, mine_source):
    """PR#183 FIX-1: caso de terceiro apenas atribuído ao usuário NÃO entra."""
    _seed(service_repo._repo, rid=RID_A, requester="user-1")
    _seed(
        service_repo._repo,
        rid=RID_B,
        requester="user-2",
        assignee="user-1",
    )
    ctx = _ctx("user-1", frozenset({MR_ACCESS, MR_PRC_CREATE}))

    out = await mine_source.fetch(ctx, limit=10)

    assert out.status == "available"
    assert out.total == 1
    assert [i.id for i in out.items] == [RID_A]


async def test_mine_analyst_excludes_assigned_only(service_repo, mine_source):
    """Analista com caso de terceiro atribuído também vê só o que criou."""
    _seed(service_repo._repo, rid=RID_A, requester="analyst-1")
    _seed(
        service_repo._repo,
        rid=RID_B,
        requester="user-2",
        assignee="analyst-1",
    )
    ctx = _ctx("analyst-1", frozenset({ENG_ACCESS}))

    out = await mine_source.fetch(ctx, limit=10)

    assert out.status == "available"
    assert out.total == 1
    assert [i.id for i in out.items] == [RID_A]


async def test_tasks_excludes_terminal_statuses(service_repo, queue_source):
    """PR#183 FIX-2: completed/rejected não inflam pendências."""
    _seed(service_repo._repo, rid=RID_A, requester="user-1")
    _seed(
        service_repo._repo,
        rid=RID_B,
        requester="user-2",
        status="completed",
    )
    _seed(
        service_repo._repo,
        rid="33333333-3333-4333-8333-333333333333",
        requester="user-3",
        status="rejected",
    )
    ctx = _ctx("analyst-1", frozenset({ENG_ACCESS}))

    out = await queue_source.fetch(ctx, limit=10)

    assert out.status == "available"
    assert out.total == 1
    assert [i.id for i in out.items] == [RID_A]


async def test_tasks_total_counts_filtered_universe(
    service_repo, queue_source
):
    """Total reflete o universo acionável antes da paginação."""
    for i, st in enumerate(
        ["submitted", "in_progress", "needs_correction", "completed"]
    ):
        _seed(
            service_repo._repo,
            rid=f"44444444-4444-4444-8444-44444444444{i}",
            requester="user-1",
            status=st,
        )
    ctx = _ctx("analyst-1", frozenset({ENG_ACCESS}))

    out = await queue_source.fetch(ctx, limit=2)

    assert out.status == "available"
    assert len(out.items) == 2
    assert out.total == 3  # 3 acionáveis; completed fora do COUNT


async def test_denied_user_maps_forbidden(service_repo, queue_source):
    ctx = _ctx("nobody", frozenset())
    out = await queue_source.fetch(ctx, limit=10)
    assert out.status == "forbidden"


async def test_empty_result_maps_empty(service_repo, queue_source):
    ctx = _ctx("analyst-1", frozenset({ENG_ACCESS}))
    out = await queue_source.fetch(ctx, limit=10)
    assert out.status == "empty"
    assert out.total == 0


async def test_total_is_pre_pagination(service_repo, queue_source):
    for i in range(5):
        _seed(
            service_repo._repo,
            rid=f"33333333-3333-4333-8333-33333333333{i}",
            requester="user-1",
        )
    ctx = _ctx("analyst-1", frozenset({ENG_ACCESS}))
    out = await queue_source.fetch(ctx, limit=2)
    assert out.status == "available"
    assert len(out.items) == 2
    assert out.total == 5


async def test_source_failure_isolated(mine_source):
    ctx = _ctx("user-1", frozenset({MR_ACCESS}))

    class _Boom:
        def list_requests(self, **_kw):
            raise RuntimeError("db down")

    src = PrcMineHomeSource(lambda: _Boom())
    out = await src.fetch(ctx, limit=10)
    assert out.status == "unavailable"


async def test_forbidden_propagates_not_unavailable():
    ctx = _ctx("u", frozenset())

    class _Denied:
        def list_requests(self, **_kw):
            raise PrcForbiddenError("nope")

    out = await PrcQueueHomeSource(lambda: _Denied()).fetch(ctx, limit=10)
    assert out.status == "forbidden"


async def test_title_uses_official_code_or_description(
    service_repo, queue_source
):
    _seed(
        service_repo._repo,
        rid=RID_A,
        requester="user-1",
        official="30190123",
        description=None,
    )
    ctx = _ctx("analyst-1", frozenset({ENG_ACCESS}))
    out = await queue_source.fetch(ctx, limit=10)
    assert "30190123" in out.items[0].title


async def test_meta_carries_request_identity(service_repo, queue_source):
    _seed(service_repo._repo, rid=RID_A, requester="user-1")
    ctx = _ctx("analyst-1", frozenset({ENG_ACCESS}))
    out = await queue_source.fetch(ctx, limit=10)
    item = out.items[0]
    assert item.meta["request_id"] == RID_A
    assert item.meta["request_type"] == "create"
