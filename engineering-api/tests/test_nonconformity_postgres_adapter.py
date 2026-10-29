"""Integration tests for PostgresNonconformityRepository.

Run only against the dedicated, isolated sandbox database
(``engineering-api/sandbox/nc``). Skipped unless ``NC_SANDBOX_DSN``
is set — never pointed at shared/production postgres-plugins.
"""

import os
import uuid

import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("NC_SANDBOX_DSN"),
    reason="requires isolated NC sandbox (NC_SANDBOX_DSN)",
)

from engineering_app.application.use_cases.nonconformity.write import (
    ImportNonconformitiesUseCase,
)
from engineering_app.domain.nonconformity.errors import (
    NcConcurrencyError,
    NcUnsafeOperationError,
)
from engineering_app.domain.nonconformity.models import NcActor
from engineering_app.infrastructure.persistence.nonconformity.postgres_nonconformity_repository import (
    PostgresNonconformityRepository,
)

ACTOR = NcActor(
    user_id="sandbox-tester",
    email="tester@sandbox.local",
    name="Sandbox Tester",
    label="sandbox-tester",
)


@pytest.fixture()
def dsn():
    return os.environ["NC_SANDBOX_DSN"]


@pytest.fixture()
def repo(dsn):
    return PostgresNonconformityRepository(dsn, allow_replace=True)


@pytest.fixture()
def guarded_repo(dsn):
    return PostgresNonconformityRepository(dsn, allow_replace=False)


def test_list_records_seed_data(repo):
    result = repo.list_records(page=1, page_size=10)
    assert result["total"] >= 3
    first = result["items"][0]
    assert first["products"], "seed products should be hydrated"
    assert first["problem_tags"]


def test_get_record_round_trip(repo):
    result = repo.list_records(sale_number="004101", page=1, page_size=5)
    assert result["total"] == 2
    item = repo.get_record(result["items"][0]["id"])
    assert item is not None
    assert item["sale_number"] == "004101"
    assert item["customer_name"] == "Cliente Sintético Alfa"


def test_filter_by_status_and_tag(repo):
    assert repo.list_records(status="done")["total"] == 1
    assert repo.list_records(problem_tag="medida")["total"] == 1


def test_problem_tag_catalog(repo):
    labels = {row["label"] for row in repo.list_problem_tag_catalog()}
    assert {"Acabamento", "Desenho", "Medida"} <= labels


def test_occurrence_dates_for_streak(repo):
    dates = repo.list_occurrence_dates()
    assert len(dates) >= 3
    assert min(dates) < max(dates)


def test_create_update_delete_with_history(repo):
    record = repo.create_record(
        occurrence_date="2026-02-01",
        sale_number="004999",
        customer_name="Cliente Sandbox",
        status="open",
        defect_description="Defeito de teste de integração.",
        corrective_actions="Ação sandbox.",
        products=[{"product_code": "sbx001", "product_description": "Item sandbox"}],
        problem_tags=["Medida", "Tag Nova Sandbox"],
        actor=ACTOR,
    )
    assert uuid.UUID(record["id"])
    assert record["status"] == "open"
    assert [p["product_code"] for p in record["products"]] == ["SBX001"]
    assert record["problem_tags"] == ["Medida", "Tag Nova Sandbox"]

    history = repo.list_history(record["id"])
    assert history[0]["event_type"] == "created"
    assert history[0]["actor_user_id"] == "sandbox-tester"

    updated = repo.update_record(
        record_id=record["id"],
        status="done",
        occurrence_date="2026-02-01",
        sale_number="004999",
        customer_name="Cliente Sandbox",
        defect_description="Defeito de teste de integração.",
        corrective_actions="Ação sandbox.",
        products=[{"product_code": "SBX001", "product_description": "Item sandbox"}],
        problem_tags=["Medida"],
        actor=ACTOR,
    )
    assert updated["status"] == "done"

    history = repo.list_history(record["id"])
    assert [e["event_type"] for e in history] == ["updated", "created"]
    status_changes = [
        c for c in history[0]["changes"]["fields"] if c["field"] == "status"
    ]
    assert status_changes and status_changes[0]["new"] == "done"

    assert repo.delete_record(record["id"]) is True
    assert repo.get_record(record["id"]) is None
    assert repo.list_history(record["id"]) is None


def test_update_conflict_optimistic_lock(repo):
    record = repo.create_record(
        occurrence_date="2026-02-02",
        status="open",
        defect_description="Lock sandbox.",
        actor=ACTOR,
    )
    with pytest.raises(NcConcurrencyError):
        repo.update_record(
            record_id=record["id"],
            status="in_progress",
            occurrence_date="2026-02-02",
            defect_description="Lock sandbox.",
            actor=ACTOR,
            expected_updated_at="2000-01-01T00:00:00+00:00",
        )
    assert repo.delete_record(record["id"]) is True


def test_delete_all_records_blocked_without_opt_in(guarded_repo):
    with pytest.raises(NcUnsafeOperationError):
        guarded_repo.delete_all_records()


@pytest.mark.asyncio
async def test_import_dry_run_and_replace_use_case(repo):
    use_case = ImportNonconformitiesUseCase(repo)

    dry = await use_case.execute(
        items=[{"occurrence_date": "2026-03-01", "status": "open",
                "defect_description": "Dry run."}],
        actor=ACTOR,
        dry_run=True,
    )
    assert dry.deleted == 0
    assert dry.created == 1
    assert dry.items[0]["result"] == "would_replace_all"

    # Safety: without confirm_replace the use case refuses destruction.
    with pytest.raises(NcUnsafeOperationError):
        await use_case.execute(
            items=[{"occurrence_date": "2026-03-01"}],
            actor=ACTOR,
            confirm_replace=False,
        )

    result = await use_case.execute(
        items=[
            {"occurrence_date": "2026-03-01", "sale_number": "IMP001",
             "status": "open", "defect_description": "Importado sandbox."},
            {"status": "invalid-status", "defect_description": "skip me"},
            {"occurrence_date": "2026-03-02", "sale_number": "IMP002",
             "status": "done", "defect_description": "Segundo importado."},
        ],
        actor=ACTOR,
        confirm_replace=True,
    )
    assert result.skipped == 1
    assert result.created == 2

    remaining = repo.list_records(page=1, page_size=100)
    assert {r["sale_number"] for r in remaining["items"]} == {"IMP001", "IMP002"}
    assert remaining["total"] == 2


def test_append_only_history_trigger(dsn, repo):
    import psycopg

    record = repo.create_record(
        occurrence_date="2026-02-05",
        status="open",
        defect_description="Trigger test.",
        actor=ACTOR,
    )
    with psycopg.connect(dsn) as conn:
        with pytest.raises(Exception):
            conn.execute(
                "UPDATE engineering.lmp_nonconformity_history "
                "SET actor_name = 'tampered' WHERE nonconformity_id = %s",
                (record["id"],),
            )
        conn.rollback()
    assert repo.delete_record(record["id"]) is True
