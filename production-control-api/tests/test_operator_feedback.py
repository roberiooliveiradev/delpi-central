"""C1 — fundação do Operator Feedback (impedimentos do operador ao PCP)."""

from __future__ import annotations

import copy
import os
import uuid
from contextlib import contextmanager
from datetime import date, datetime, timezone
from typing import Any

import pytest
from psycopg.errors import UniqueViolation

from production_control_app.application.services.operator_feedback_service import (
    OperatorFeedbackService,
)
from production_control_app.domain.errors import (
    InvalidOperatorFeedbackReason,
    InvalidOperatorFeedbackType,
    OperatorFeedbackConflict,
    OperatorFeedbackNotFound,
    OperatorFeedbackStateError,
)
from production_control_app.domain.operator_feedback import (
    ACTIVE_STATUSES,
    OperatorFeedbackStatus,
)
from production_control_app.domain.ports.operator_feedback_repository import (
    OperatorFeedbackRepositoryPort,
)
from production_control_app.infrastructure.persistence import (
    postgres_operator_feedback_repository as feedback_module,
)
from production_control_app.infrastructure.persistence.postgres_operator_feedback_repository import (  # noqa: E501
    PostgresOperatorFeedbackRepository,
)


def _base(**overrides: Any) -> dict[str, Any]:
    ctx = {
        "feedback_type": "cannot_produce",
        "reason_code": "missing_material",
        "branch": "01",
        "production_order": "24640401002",
        "operation_code": "03",
        "reported_work_center": "CT-63",
        "operator_code": "001234",
        "operator_name": "Maria Silva",
        "product_code": "TR-1234",
        "product_description": "Transformador 15kVA",
        "pa_product_code": "PA-5678",
        "due_date": date(2026, 10, 8),
    }
    ctx.update(overrides)
    return ctx


class FakeOperatorFeedbackRepository(OperatorFeedbackRepositoryPort):
    """Mesma regra do índice parcial: um ativo por chave lógica."""

    def __init__(self) -> None:
        self.rows: dict[str, dict[str, Any]] = {}
        self._clock = 0

    def _key(self, row: dict[str, Any]) -> tuple[Any, ...]:
        return (
            row["branch"],
            row["production_order"],
            row["operation_code"],
            row["feedback_type"],
            row["reason_code"],
        )

    def _stamp(self) -> datetime:
        self._clock += 1
        return datetime(2026, 9, 20, 12, self._clock, tzinfo=timezone.utc)

    def create(self, **kwargs: Any) -> dict[str, Any]:
        for row in self.rows.values():
            if row["status"] in ACTIVE_STATUSES and self._key(row) == (
                kwargs["branch"],
                kwargs["production_order"],
                kwargs["operation_code"],
                kwargs["feedback_type"],
                kwargs["reason_code"],
            ):
                raise OperatorFeedbackConflict("duplicado ativo")
        row = {
            "id": str(uuid.uuid4()),
            **kwargs,
            "status": "open",
            "created_at": self._stamp(),
            "acknowledged_at": None,
            "acknowledged_by": None,
            "resolved_at": None,
            "resolved_by": None,
            "resolution_note": None,
        }
        self.rows[row["id"]] = row
        return copy.deepcopy(row)

    def get(self, feedback_id: str) -> dict[str, Any] | None:
        row = self.rows.get(feedback_id)
        return copy.deepcopy(row) if row else None

    def get_active(self, **kwargs: Any) -> dict[str, Any] | None:
        for row in self.rows.values():
            if row["status"] in ACTIVE_STATUSES and self._key(row) == (
                kwargs["branch"],
                kwargs["production_order"],
                kwargs["operation_code"],
                kwargs["feedback_type"],
                kwargs["reason_code"],
            ):
                return copy.deepcopy(row)
        return None

    def list_active(
        self, *, branch: str, reported_work_center: str | None = None
    ) -> list[dict[str, Any]]:
        # Mesma ordenacao do repo real: open antes de acknowledged e, dentro
        # do grupo, os mais antigos primeiro (inbox prioriza o que espera).
        rank = {"open": 0, "acknowledged": 1}
        return [
            copy.deepcopy(row)
            for row in sorted(
                self.rows.values(),
                key=lambda r: (rank.get(r["status"], 2), r["created_at"]),
            )
            if row["branch"] == branch
            and row["status"] in ACTIVE_STATUSES
            and (reported_work_center is None
                 or row["reported_work_center"] == reported_work_center)
        ]

    def list_active_for_operation(
        self,
        *,
        branch: str,
        production_order: str,
        operation_code: str,
    ) -> list[dict[str, Any]]:
        return [
            copy.deepcopy(row)
            for row in sorted(self.rows.values(), key=lambda r: r["created_at"])
            if row["branch"] == branch
            and row["production_order"] == production_order
            and row["operation_code"] == operation_code
            and row["status"] in ACTIVE_STATUSES
        ]

    def acknowledge(
        self, feedback_id: str, *, acknowledged_by: str
    ) -> dict[str, Any] | None:
        row = self.rows.get(feedback_id)
        if row is None or row["status"] != "open":
            return None
        row["status"] = "acknowledged"
        row["acknowledged_at"] = self._stamp()
        row["acknowledged_by"] = acknowledged_by
        return copy.deepcopy(row)

    def resolve(
        self,
        feedback_id: str,
        *,
        resolved_by: str,
        resolution_note: str | None = None,
    ) -> dict[str, Any] | None:
        row = self.rows.get(feedback_id)
        if row is None or row["status"] not in ACTIVE_STATUSES:
            return None
        row["status"] = "resolved"
        row["resolved_at"] = self._stamp()
        row["resolved_by"] = resolved_by
        row["resolution_note"] = resolution_note
        return copy.deepcopy(row)


@pytest.fixture()
def service() -> OperatorFeedbackService:
    return OperatorFeedbackService(feedbacks=FakeOperatorFeedbackRepository())


# --- criação -----------------------------------------------------------------


def test_report_creates_open_cannot_produce_missing_material(
    service: OperatorFeedbackService,
) -> None:
    row = service.report(**_base())
    assert row["status"] == OperatorFeedbackStatus.OPEN.value
    assert row["feedback_type"] == "cannot_produce"
    assert row["reason_code"] == "missing_material"
    assert row["created_at"] is not None
    assert row["acknowledged_at"] is None and row["resolved_at"] is None


def test_report_preserves_the_full_report_snapshot(
    service: OperatorFeedbackService,
) -> None:
    ctx = _base(note="falta núcleo", run_id=str(uuid.uuid4()))
    row = service.report(**ctx)
    for key in (
        "branch", "production_order", "operation_code", "reported_work_center",
        "product_code", "product_description", "pa_product_code",
        "operator_code", "operator_name", "note", "run_id",
    ):
        assert row[key] == ctx[key]
    assert row["due_date"] == ctx["due_date"]


def test_optional_fields_can_be_null(service: OperatorFeedbackService) -> None:
    row = service.report(**_base(due_date=None))
    assert row["note"] is None and row["run_id"] is None
    assert row["bench_session_id"] is None and row["due_date"] is None


def test_reported_work_center_is_frozen_at_report_time(
    service: OperatorFeedbackService,
) -> None:
    row = service.report(**_base())
    assert row["reported_work_center"] == "CT-63"
    assert row["branch"] + row["production_order"] + row["operation_code"]


def test_invalid_feedback_type_rejected(service: OperatorFeedbackService) -> None:
    with pytest.raises(InvalidOperatorFeedbackType):
        service.report(**_base(feedback_type="machine_stopped"))


def test_invalid_reason_rejected(service: OperatorFeedbackService) -> None:
    with pytest.raises(InvalidOperatorFeedbackReason):
        service.report(**_base(reason_code="bad_tool"))


@pytest.mark.parametrize(
    "field",
    ["branch", "production_order", "operation_code",
     "reported_work_center", "operator_code", "operator_name"],
)
def test_identity_fields_are_required(
    service: OperatorFeedbackService, field: str
) -> None:
    with pytest.raises(ValueError):
        service.report(**_base(**{field: "  "}))


# --- duplicidade ---------------------------------------------------------------


def test_second_active_equivalent_is_rejected(
    service: OperatorFeedbackService,
) -> None:
    service.report(**_base())
    with pytest.raises(OperatorFeedbackConflict):
        service.report(**_base(operator_name="Outro operador"))


def test_acknowledged_still_blocks_duplicate(
    service: OperatorFeedbackService,
) -> None:
    row = service.report(**_base())
    service.acknowledge(row["id"], acknowledged_by="pcp.user")
    with pytest.raises(OperatorFeedbackConflict):
        service.report(**_base())


def test_new_equivalent_allowed_after_resolution(
    service: OperatorFeedbackService,
) -> None:
    first = service.report(**_base())
    service.resolve(first["id"], resolved_by="pcp.user")
    second = service.report(**_base())
    assert second["id"] != first["id"] and second["status"] == "open"


@pytest.mark.parametrize(
    "override",
    [
        {"branch": "02"},
        {"production_order": "99900011122"},
        {"operation_code": "05"},
        {"reason_code": "bad_tool"},
        {"feedback_type": "other_type"},
    ],
)
def test_active_key_isolates_distinct_impediments(
    service: OperatorFeedbackService, override: dict[str, Any]
) -> None:
    """Outro impedimento na MESMA chave conflita; chaves vizinhas coexistem.

    reason/type diferentes passam pelo repo real (índice); no service o catálogo
    C1 rejeita — aqui provamos que a chave os distingue via repo fake direto.
    """
    base = _base()
    if "feedback_type" in override or "reason_code" in override:
        repo = service._feedbacks  # noqa: SLF001
        repo.create(**{k: v for k, v in base.items()})
        # chave diferente no mesmo repo: não conflita
        other = repo.create(**{**base, **override})
        assert other["id"]
        return
    service.report(**base)
    row = service.report(**{**base, **override})
    assert row["status"] == "open"


# --- acknowledge ---------------------------------------------------------------


def test_acknowledge_records_actor_and_timestamp(
    service: OperatorFeedbackService,
) -> None:
    row = service.report(**_base())
    ack = service.acknowledge(row["id"], acknowledged_by="pcp.analyst")
    assert ack["status"] == "acknowledged"
    assert ack["acknowledged_by"] == "pcp.analyst"
    assert ack["acknowledged_at"] is not None
    assert ack["resolved_at"] is None


def test_acknowledge_preserves_original_context(
    service: OperatorFeedbackService,
) -> None:
    ctx = _base()
    row = service.report(**ctx)
    ack = service.acknowledge(row["id"], acknowledged_by="pcp.analyst")
    for key in ctx:
        assert ack[key] == row[key]


def test_acknowledge_is_idempotent_and_keeps_first_author(
    service: OperatorFeedbackService,
) -> None:
    row = service.report(**_base())
    first = service.acknowledge(row["id"], acknowledged_by="pcp.one")
    second = service.acknowledge(row["id"], acknowledged_by="pcp.two")
    assert second["acknowledged_by"] == "pcp.one"
    assert second["acknowledged_at"] == first["acknowledged_at"]


def test_acknowledge_resolved_is_state_error(
    service: OperatorFeedbackService,
) -> None:
    row = service.report(**_base())
    service.resolve(row["id"], resolved_by="pcp.user")
    with pytest.raises(OperatorFeedbackStateError):
        service.acknowledge(row["id"], acknowledged_by="pcp.user")


def test_acknowledge_unknown_id_raises_not_found(
    service: OperatorFeedbackService,
) -> None:
    with pytest.raises(OperatorFeedbackNotFound):
        service.acknowledge(str(uuid.uuid4()), acknowledged_by="pcp.user")


# --- resolve -------------------------------------------------------------------


def test_resolve_directly_from_open(service: OperatorFeedbackService) -> None:
    row = service.report(**_base())
    res = service.resolve(
        row["id"], resolved_by="pcp.user", resolution_note="material entregue"
    )
    assert res["status"] == "resolved"
    assert res["resolved_by"] == "pcp.user"
    assert res["resolved_at"] is not None
    assert res["resolution_note"] == "material entregue"
    assert res["acknowledged_at"] is None  # open -> resolved direto é válido


def test_resolve_from_acknowledged(service: OperatorFeedbackService) -> None:
    row = service.report(**_base())
    service.acknowledge(row["id"], acknowledged_by="pcp.one")
    res = service.resolve(row["id"], resolved_by="pcp.two")
    assert res["status"] == "resolved"
    assert res["acknowledged_by"] == "pcp.one"
    assert res["resolved_by"] == "pcp.two"


def test_resolve_is_idempotent_on_resolved(
    service: OperatorFeedbackService,
) -> None:
    row = service.report(**_base())
    first = service.resolve(row["id"], resolved_by="pcp.one")
    second = service.resolve(row["id"], resolved_by="pcp.two")
    assert second["resolved_by"] == "pcp.one"
    assert second["resolved_at"] == first["resolved_at"]


def test_resolve_unknown_id_raises_not_found(
    service: OperatorFeedbackService,
) -> None:
    with pytest.raises(OperatorFeedbackNotFound):
        service.resolve(str(uuid.uuid4()), resolved_by="pcp.user")


def test_get_unknown_id_raises_not_found(
    service: OperatorFeedbackService,
) -> None:
    with pytest.raises(OperatorFeedbackNotFound):
        service.get(str(uuid.uuid4()))


# --- list_active ----------------------------------------------------------------


def test_list_active_scopes_branch_and_work_center(
    service: OperatorFeedbackService,
) -> None:
    a = service.report(**_base())
    service.report(**_base(production_order="99900011122", reported_work_center="CT-99"))
    b = service.report(**_base(branch="02"))
    service.resolve(a["id"], resolved_by="pcp.user")

    branch01 = service.list_active(branch="01")
    assert [r["production_order"] for r in branch01] == ["99900011122"]
    by_wc = service.list_active(branch="01", reported_work_center="CT-99")
    assert len(by_wc) == 1
    assert service.list_active(branch="02") == [service.get(b["id"])]


# --- repositório Postgres (fake DB) ---------------------------------------------


class FakeFeedbackDb:
    """Conexão+cursor em memória espelhando a semântica da V016."""

    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []
        self.queries: list[str] = []
        self._clock = 0
        self.raise_unique = False
        self._result: dict[str, Any] | None = None
        self._result_many: list[dict[str, Any]] = []

    @contextmanager
    def connection(self):
        yield self

    def cursor(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *_exc: object) -> None:
        return None

    def _key(self, row: dict[str, Any]) -> tuple[Any, ...]:
        return (
            row["branch"], row["production_order"], row["operation_code"],
            row["feedback_type"], row["reason_code"],
        )

    def execute(self, query: str, params: tuple[Any, ...]) -> None:
        self.queries.append(query)
        self._result, self._result_many = None, []
        if "INSERT INTO" in query:
            if self.raise_unique:
                raise UniqueViolation("uq_pc_operator_feedbacks_active")
            keys = (
                "branch", "production_order", "operation_code",
                "reported_work_center", "feedback_type", "reason_code", "note",
                "operator_code", "operator_name", "bench_session_id", "run_id",
                "status", "product_code", "product_description",
                "pa_product_code", "due_date",
            )
            row = dict(zip(keys, params))
            for existing in self.rows:
                if existing["status"] in ACTIVE_STATUSES and                         self._key(existing) == self._key(row):
                    raise UniqueViolation("uq_pc_operator_feedbacks_active")
            self._clock += 1
            row.update(
                id=str(uuid.uuid4()),
                created_at=datetime(2026, 9, 20, 12, self._clock,
                                    tzinfo=timezone.utc),
                acknowledged_at=None, acknowledged_by=None,
                resolved_at=None, resolved_by=None, resolution_note=None,
            )
            self.rows.append(row)
            self._result = copy.deepcopy(row)
            return
        if "UPDATE" in query:
            if "acknowledged_at = NOW()" in query:
                status, by, feedback_id, expected = params
                for row in self.rows:
                    if row["id"] == feedback_id and row["status"] == expected:
                        self._clock += 1
                        row.update(
                            status=status, acknowledged_by=by,
                            acknowledged_at=datetime(
                                2026, 9, 20, 13, self._clock,
                                tzinfo=timezone.utc),
                        )
                        self._result = copy.deepcopy(row)
                return
            status, by, note, feedback_id = params
            for row in self.rows:
                if row["id"] == feedback_id and row["status"] in ACTIVE_STATUSES:
                    self._clock += 1
                    row.update(
                        status=status, resolved_by=by, resolution_note=note,
                        resolved_at=datetime(
                            2026, 9, 20, 14, self._clock, tzinfo=timezone.utc),
                    )
                    self._result = copy.deepcopy(row)
            return
        # SELECTs
        if "WHERE id = %s" in query:
            self._result = next(
                (copy.deepcopy(r) for r in self.rows if r["id"] == params[0]),
                None,
            )
        elif "production_order = %s" in query:
            self._result = next(
                (copy.deepcopy(r) for r in self.rows
                 if r["status"] in ACTIVE_STATUSES
                 and self._key(r) == (
                     params[0], params[1], params[2], params[3], params[4])),
                None,
            )
        else:
            self._result_many = [
                copy.deepcopy(r) for r in self.rows
                if r["branch"] == params[0]
                and r["status"] in ACTIVE_STATUSES
                and (len(params) < 2 or r["reported_work_center"] == params[1])
            ]

    def fetchone(self):
        return self._result

    def fetchall(self):
        return self._result_many


@pytest.fixture()
def db(monkeypatch: pytest.MonkeyPatch) -> FakeFeedbackDb:
    fake = FakeFeedbackDb()
    monkeypatch.setattr(feedback_module, "get_connection", fake.connection)
    return fake


def test_repo_create_returns_open_row(db: FakeFeedbackDb) -> None:
    repo = PostgresOperatorFeedbackRepository()
    row = repo.create(
        branch="01", production_order="24640401002", operation_code="03",
        reported_work_center="CT-63", feedback_type="cannot_produce",
        reason_code="missing_material", operator_code="001234",
        operator_name="Maria Silva", run_id=None,
    )
    assert row["status"] == "open" and row["id"]


def test_repo_unique_violation_becomes_domain_conflict(
    db: FakeFeedbackDb,
) -> None:
    repo = PostgresOperatorFeedbackRepository()
    base = dict(
        branch="01", production_order="24640401002", operation_code="03",
        reported_work_center="CT-63", feedback_type="cannot_produce",
        reason_code="missing_material", operator_code="001234",
        operator_name="Maria Silva",
    )
    repo.create(**base)
    with pytest.raises(OperatorFeedbackConflict):
        repo.create(**base)
    db.raise_unique = True  # emula concorrência: índice rejeita fora do fluxo
    with pytest.raises(OperatorFeedbackConflict):
        repo.create(**{**base, "production_order": "OUTRA-OP"})


def test_repo_conditional_updates_guard_transitions(
    db: FakeFeedbackDb,
) -> None:
    repo = PostgresOperatorFeedbackRepository()
    row = repo.create(
        branch="01", production_order="24640401002", operation_code="03",
        reported_work_center="CT-63", feedback_type="cannot_produce",
        reason_code="missing_material", operator_code="001234",
        operator_name="Maria Silva",
    )
    # acknowledge duas vezes: segundo UPDATE não casa (status já mudou)
    assert repo.acknowledge(row["id"], acknowledged_by="pcp") is not None
    assert repo.acknowledge(row["id"], acknowledged_by="pcp") is None
    # resolved não resolve de novo
    assert repo.resolve(row["id"], resolved_by="pcp") is not None
    assert repo.resolve(row["id"], resolved_by="pcp") is None
    # UPDATEs carregam a condição de status (anti-race entre analistas)
    updates = [q for q in db.queries if "UPDATE" in q]
    assert any("AND status = %s" in q for q in updates)
    assert any("AND status IN" in q for q in updates)


def test_repo_get_active_ignores_resolved(db: FakeFeedbackDb) -> None:
    repo = PostgresOperatorFeedbackRepository()
    base = dict(
        branch="01", production_order="24640401002", operation_code="03",
        reported_work_center="CT-63", feedback_type="cannot_produce",
        reason_code="missing_material", operator_code="001234",
        operator_name="Maria Silva",
    )
    row = repo.create(**base)
    assert repo.get_active(
        branch="01", production_order="24640401002", operation_code="03",
        feedback_type="cannot_produce", reason_code="missing_material",
    )["id"] == row["id"]
    repo.resolve(row["id"], resolved_by="pcp")
    assert repo.get_active(
        branch="01", production_order="24640401002", operation_code="03",
        feedback_type="cannot_produce", reason_code="missing_material",
    ) is None
    again = repo.create(**base)  # resolved libera a chave
    assert again["id"] != row["id"]


# --- integração Postgres real (migration + índice) -----------------------------


_DB_REQUIRED = pytest.mark.skipif(
    os.getenv("PC_TEST_MES_DB") != "1",
    reason="Testes de persistência exigem PC_TEST_MES_DB=1 e PLUGINS_DB_*",
)


@_DB_REQUIRED
class TestOperatorFeedbackPostgres:
    @pytest.fixture()
    def repo(self):
        from production_control_app.infrastructure.persistence.plugins_postgres_connection import (  # noqa: E501
            PC_SCHEMA_NAME,
            get_connection,
        )

        op = "ZZ-TEST-FEEDBACK"
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"DELETE FROM {PC_SCHEMA_NAME}.operator_feedbacks "
                    "WHERE production_order = %s",
                    (op,),
                )
            conn.commit()
        yield PostgresOperatorFeedbackRepository(), op
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"DELETE FROM {PC_SCHEMA_NAME}.operator_feedbacks "
                    "WHERE production_order = %s",
                    (op,),
                )
            conn.commit()

    def test_real_db_enforces_lifecycle_and_unique_index(self, repo) -> None:
        repo, op = repo
        service = OperatorFeedbackService(feedbacks=repo)
        row = service.report(**_base(production_order=op))
        with pytest.raises(OperatorFeedbackConflict):
            service.report(**_base(production_order=op))
        service.acknowledge(row["id"], acknowledged_by="pcp.test")
        service.resolve(row["id"], resolved_by="pcp.test",
                        resolution_note="ok")
        fresh = service.report(**_base(production_order=op))
        assert fresh["id"] != row["id"] and fresh["status"] == "open"
        with pytest.raises(OperatorFeedbackStateError):
            service.acknowledge(row["id"], acknowledged_by="pcp.test")
