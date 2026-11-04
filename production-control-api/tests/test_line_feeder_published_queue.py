"""Etapa 1 — leitura autenticada da fila PUBLISHED pelo Alimentador de Linha."""

from __future__ import annotations

from datetime import date, datetime, timezone
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from production_control_app.application.services.line_feeder_service import LineFeederService
from production_control_app.domain.errors import SnapshotNotFound
from production_control_app.domain.services.branch_access_service import BranchAccessService
from production_control_app.domain.services.line_feeder_published_queue import (
    build_operation_id,
    project_published_queue,
)

FULL_PERMS = (
    "production-control.access",
    "production-control.line-feeder.view",
    "production-control.view.filial-01",
)


def _user(*permissions: str):
    return SimpleNamespace(
        is_superadmin=False,
        permissions=list(permissions),
        id="user-1",
        email="alimentador@delpi.com.br",
    )


def _op(
    *,
    work_center: str,
    order: str,
    operation: str = "01",
    pending: float | None = 10.0,
    use_header: bool = False,
    **extra: Any,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "work_center": work_center,
        "work_center_name": f"BANCADA {work_center}",
        "production_order": order,
        "operation_code": operation,
        "product_code": f"P-{order}",
        "product_description": f"Produto {order}",
        "unit": "PC",
        "pieces_conversion_factor": 1.0,
        "planned_qty": 10.0,
        **extra,
    }
    if pending is None:
        pass
    elif use_header:
        row["pending_qty"] = pending
    else:
        row["operation_pending_qty"] = pending
    return row


class FakePublications:
    def __init__(self) -> None:
        self.rows: dict[str, dict[str, Any]] = {}
        self.get_calls: list[str] = []

    def put(
        self,
        branch: str,
        payload: dict[str, Any],
        *,
        generation_id: str = "gen-1",
        row_version: str = "rev-1",
    ) -> dict[str, Any]:
        row = {
            "id": f"pub-{branch}",
            "branch": branch,
            "generation_id": generation_id,
            "start_date": date(2026, 9, 1),
            "end_date": date(2026, 9, 30),
            "payload_json": payload,
            "schema_version": 1,
            "source": "api-delpi",
            "source_refreshed_at": datetime(2026, 9, 19, 10, tzinfo=timezone.utc),
            "source_refreshed_by": "pcp",
            "published_at": datetime(2026, 9, 20, 12, tzinfo=timezone.utc),
            "published_by": "pcp",
            "row_version": row_version,
        }
        self.rows[branch] = row
        return row

    def get(self, *, branch: str, conn: Any = None) -> dict[str, Any] | None:
        self.get_calls.append(branch)
        return self.rows.get(branch)

    def upsert(self, **_kwargs: Any) -> dict[str, Any]:
        raise AssertionError("Alimentador não pode publicar.")

    def update_payload(self, **_kwargs: Any) -> dict[str, Any]:
        raise AssertionError("Alimentador não pode mutar a publicação.")


class FakeSnapshots:
    """WORKING — se o alimentador cair aqui nos testes PUBLISHED, o teste falha."""

    def __init__(self, payload: dict[str, Any] | None = None) -> None:
        self.rows: dict[str, dict[str, Any]] = {}
        self.get_calls = 0
        if payload is not None:
            self.rows["01"] = {
                "branch": "01",
                "payload_json": payload,
                "generation_id": "working-only",
            }

    def get(self, *, branch: str) -> dict[str, Any] | None:
        self.get_calls += 1
        return self.rows.get(branch)


class FakeGateway:
    pass


class FakePickPlans:
    pass


def _payload(operations: list[dict[str, Any]], **extra: Any) -> dict[str, Any]:
    centers: list[dict[str, str]] = []
    for item in operations:
        code = item["work_center"]
        if not any(center["work_center"] == code for center in centers):
            centers.append(
                {
                    "work_center": code,
                    "work_center_name": item.get("work_center_name") or code,
                }
            )
    return {"work_centers": centers, "operations": operations, **extra}


def _service(
    *,
    published: dict[str, Any] | None = None,
    working: dict[str, Any] | None = None,
    publications: FakePublications | None = None,
    generation_id: str = "gen-1",
    row_version: str = "rev-1",
) -> tuple[LineFeederService, FakePublications, FakeSnapshots]:
    pubs = publications or FakePublications()
    if published is not None:
        pubs.put(
            "01",
            published,
            generation_id=generation_id,
            row_version=row_version,
        )
    snaps = FakeSnapshots(working)
    from production_control_app.application.services.line_feeder_service import (
        _RequirementsCache,
    )

    service = LineFeederService(
        FakeGateway(),  # type: ignore[arg-type]
        snapshots=snaps,  # type: ignore[arg-type]
        pick_plans=FakePickPlans(),  # type: ignore[arg-type]
        publications=pubs,  # type: ignore[arg-type]
        branch_access=BranchAccessService(),
        cache=_RequirementsCache(0),
    )
    return service, pubs, snaps


def _queue(service: LineFeederService, **kwargs: Any) -> dict[str, Any]:
    return service.get_published_queue(_user(*FULL_PERMS), branch="01", **kwargs)


# --------------------------------------------------------------------------- #
# Domínio puro
# --------------------------------------------------------------------------- #


def test_project_preserves_published_order_and_leading_zeros() -> None:
    row = {
        "generation_id": "g1",
        "row_version": "42",
        "published_at": datetime(2026, 9, 20, 12, tzinfo=timezone.utc),
        "payload_json": _payload(
            [
                _op(work_center="CNC-01", order="00012300101", operation="01"),
                _op(work_center="CNC-01", order="00012300102", operation="02"),
                _op(work_center="TOR-02", order="00099900101", operation="01"),
            ]
        ),
    }
    result = project_published_queue(row, branch="01")
    assert result["queue_status"] == "available"
    assert result["publication"]["publication_revision"] == "42"
    cnc = result["work_center_queues"][0]
    assert cnc["work_center"] == "CNC-01"
    assert [op["production_order"] for op in cnc["operations"]] == [
        "00012300101",
        "00012300102",
    ]
    assert cnc["operations"][0]["sequence_position"] == 1
    assert cnc["operations"][0]["operation_id"] == build_operation_id(
        branch="01",
        work_center="CNC-01",
        production_order="00012300101",
        operation_code="01",
    )
    assert result["work_center_queues"][1]["work_center"] == "TOR-02"


def test_closed_balance_excluded_unknown_kept() -> None:
    row = {
        "generation_id": "g1",
        "row_version": "1",
        "payload_json": _payload(
            [
                _op(work_center="A", order="OP1", pending=0.0),
                _op(work_center="A", order="OP2", pending=None),
                _op(work_center="A", order="OP3", pending=5.0),
            ]
        ),
    }
    result = project_published_queue(row, branch="01")
    ops = result["work_center_queues"][0]["operations"]
    assert [op["production_order"] for op in ops] == ["OP2", "OP3"]
    assert ops[0]["pending_qty"] is None
    assert ops[0]["balance_state"] == "unknown"
    assert ops[0]["balance_source"] == "unavailable"
    assert ops[1]["balance_state"] == "open"
    assert ops[1]["balance_source"] == "operation_pending_qty"


def test_withdrawn_operations_excluded() -> None:
    row = {
        "generation_id": "g1",
        "row_version": "1",
        "payload_json": _payload(
            [
                _op(work_center="A", order="OP1"),
                _op(work_center="A", order="OP2"),
            ],
            withdrawn_operations=[
                {
                    "work_center": "A",
                    "production_order": "OP1",
                    "operation_code": "01",
                }
            ],
        ),
    }
    result = project_published_queue(row, branch="01")
    ops = result["work_center_queues"][0]["operations"]
    assert [op["production_order"] for op in ops] == ["OP2"]


# --------------------------------------------------------------------------- #
# Serviço + RBAC
# --------------------------------------------------------------------------- #


def test_working_reordered_does_not_affect_published_queue() -> None:
    published = _payload(
        [
            _op(work_center="A", order="OP-FIRST"),
            _op(work_center="A", order="OP-SECOND"),
        ]
    )
    working = _payload(
        [
            _op(work_center="A", order="OP-SECOND"),
            _op(work_center="A", order="OP-FIRST"),
            _op(work_center="A", order="OP-DRAFT-ONLY"),
        ]
    )
    service, _pubs, snaps = _service(published=published, working=working)
    result = _queue(service)
    orders = [
        op["production_order"]
        for op in result["work_center_queues"][0]["operations"]
    ]
    assert orders == ["OP-FIRST", "OP-SECOND"]
    assert snaps.get_calls == 0


def test_new_publication_updates_sequence() -> None:
    service, pubs, _snaps = _service(
        published=_payload([_op(work_center="A", order="OLD")]),
        generation_id="gen-old",
        row_version="1",
    )
    first = _queue(service)
    assert first["work_center_queues"][0]["operations"][0]["production_order"] == "OLD"

    pubs.put(
        "01",
        _payload(
            [
                _op(work_center="A", order="NEW-1"),
                _op(work_center="A", order="NEW-2"),
            ]
        ),
        generation_id="gen-new",
        row_version="2",
    )
    second = _queue(service)
    assert second["publication"]["generation_id"] == "gen-new"
    assert second["publication"]["publication_revision"] == "2"
    assert [
        op["production_order"]
        for op in second["work_center_queues"][0]["operations"]
    ] == ["NEW-1", "NEW-2"]


def test_live_reorder_changes_revision_without_generation_change() -> None:
    service, pubs, _snaps = _service(
        published=_payload(
            [
                _op(work_center="A", order="OP1"),
                _op(work_center="A", order="OP2"),
            ]
        ),
        generation_id="gen-live",
        row_version="10",
    )
    before = _queue(service)
    assert before["publication"]["generation_id"] == "gen-live"
    assert before["publication"]["publication_revision"] == "10"

    # Mutação LIVE: mesmo generation_id, payload reordenado, row_version nova.
    pubs.put(
        "01",
        _payload(
            [
                _op(work_center="A", order="OP2"),
                _op(work_center="A", order="OP1"),
            ]
        ),
        generation_id="gen-live",
        row_version="11",
    )
    after = _queue(service)
    assert after["publication"]["generation_id"] == "gen-live"
    assert after["publication"]["publication_revision"] == "11"
    assert [
        op["production_order"]
        for op in after["work_center_queues"][0]["operations"]
    ] == ["OP2", "OP1"]


def test_transfer_moves_operation_to_target_work_center() -> None:
    service, _pubs, _snaps = _service(
        published=_payload(
            [
                _op(work_center="SRC", order="OP1"),
                _op(work_center="DST", order="OP2"),
                _op(work_center="DST", order="OP1"),  # transferida: ordem no destino
            ]
        )
    )
    result = _queue(service)
    by_center = {
        group["work_center"]: [op["production_order"] for op in group["operations"]]
        for group in result["work_center_queues"]
    }
    # Sem marca de withdrawn; a sequência publicada já reflete o CT destino.
    assert by_center["SRC"] == ["OP1"]
    assert by_center["DST"] == ["OP2", "OP1"]

    only_dst = _queue(service, work_center="DST")
    assert only_dst["work_center_count"] == 1
    assert only_dst["work_center_queues"][0]["operations"][1]["production_order"] == "OP1"


def test_no_publication_does_not_fallback_to_working() -> None:
    working = _payload([_op(work_center="A", order="SHOULD-NOT-APPEAR")])
    service, _pubs, snaps = _service(published=None, working=working)
    with pytest.raises(SnapshotNotFound):
        _queue(service)
    assert snaps.get_calls == 0


def test_empty_publication_is_available_empty_not_404() -> None:
    service, _pubs, _snaps = _service(published=_payload([]))
    result = _queue(service)
    assert result["queue_status"] == "empty"
    assert result["operation_count"] == 0
    assert result["work_center_queues"] == []


def test_branch_isolation_and_no_duplicates() -> None:
    pubs = FakePublications()
    pubs.put(
        "01",
        _payload([_op(work_center="A", order="OP-01")]),
        generation_id="g01",
        row_version="1",
    )
    pubs.put(
        "02",
        _payload([_op(work_center="B", order="OP-02")]),
        generation_id="g02",
        row_version="9",
    )
    service, _p, _s = _service(publications=pubs)
    # Filial 01: usuário sem view.filial-02
    result = service.get_published_queue(_user(*FULL_PERMS), branch="01")
    assert result["operation_count"] == 1
    assert (
        result["work_center_queues"][0]["operations"][0]["production_order"] == "OP-01"
    )

    with pytest.raises(Exception):
        service.get_published_queue(_user(*FULL_PERMS), branch="02")


def test_permission_denied_without_line_feeder_view() -> None:
    service, _pubs, _snaps = _service(
        published=_payload([_op(work_center="A", order="OP1")])
    )
    with pytest.raises(PermissionError):
        service.get_published_queue(
            _user("production-control.access", "production-control.view.filial-01"),
            branch="01",
        )


def _client(
    service: LineFeederService, *, permissions: tuple[str, ...] = FULL_PERMS
) -> TestClient:
    from production_control_app.interface.http.routes import line_feeder_routes

    line_feeder_routes.build_line_feeder_service = lambda: service  # type: ignore[assignment]
    app = FastAPI()

    @app.middleware("http")
    async def inject_user(request, call_next):  # noqa: ANN001
        request.state.user = _user(*permissions)
        return await call_next(request)

    app.include_router(line_feeder_routes.router)
    return TestClient(app)


@pytest.fixture(autouse=True)
def restore_line_feeder_routes():
    from production_control_app.interface.http.routes import line_feeder_routes

    original = line_feeder_routes.build_line_feeder_service
    yield
    line_feeder_routes.build_line_feeder_service = original  # type: ignore[assignment]


def test_http_contract_envelope_and_auth() -> None:
    service, _pubs, _snaps = _service(
        published=_payload(
            [
                _op(work_center="CNC", order="00011100101", operation="01", pending=3.0),
                _op(work_center="CNC", order="00011100101", operation="02", pending=None),
            ]
        ),
        row_version="rev-http",
    )
    ok_resp = _client(service).get("/line-feeder/published-queue", params={"branch": "01"})
    assert ok_resp.status_code == 200
    body = ok_resp.json()
    assert body["success"] is True
    data = body["data"]
    assert data["publication"]["publication_revision"] == "rev-http"
    assert data["work_center_queues"][0]["operations"][0]["sequence_position"] == 1
    assert data["work_center_queues"][0]["operations"][1]["balance_state"] == "unknown"

    denied = _client(
        service,
        permissions=("production-control.access", "production-control.view.filial-01"),
    ).get("/line-feeder/published-queue", params={"branch": "01"})
    assert denied.status_code == 403

    other_branch = _client(service).get(
        "/line-feeder/published-queue", params={"branch": "02"}
    )
    assert other_branch.status_code == 403


def test_http_404_when_publication_absent() -> None:
    service, _pubs, _snaps = _service(published=None)
    resp = _client(service).get("/line-feeder/published-queue", params={"branch": "01"})
    assert resp.status_code == 404
    assert resp.json()["success"] is False
