"""Cache do snapshot por versão da tupla — a fila de 1,8 MB não volta do banco sem motivo."""

from __future__ import annotations

import json
from contextlib import contextmanager
from datetime import date
from typing import Any

import pytest

from production_control_app.infrastructure.persistence import (
    postgres_machine_load_snapshot_repository as repo_module,
)
from production_control_app.infrastructure.persistence.machine_load_snapshot_row_cache import (
    clear_snapshot_row_cache,
)
from production_control_app.infrastructure.persistence.postgres_machine_load_snapshot_repository import (
    PostgresMachineLoadSnapshotRepository,
)


class FakePostgres:
    """Tabela em memória que se comporta como a tupla real: `xmin` muda a cada escrita."""

    def __init__(self) -> None:
        self.rows: dict[str, dict[str, Any]] = {}
        self.version_probes = 0
        self.payload_reads = 0
        self._next_version = 1000

    def seed(self, branch: str, payload: dict[str, Any]) -> None:
        self._next_version += 1
        self.rows[branch] = {
            "id": "snap-1",
            "branch": branch,
            "start_date": date(2026, 8, 1),
            "end_date": date(2026, 9, 2),
            "payload_json": payload,
            "schema_version": 1,
            "source": "api-delpi",
            "refreshed_at": None,
            "refreshed_by": None,
            "row_version": str(self._next_version),
        }

    # -- protocolo mínimo de conexão/cursor usado pelo repositório --

    @contextmanager
    def connection(self):
        yield self

    def cursor(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *_exc: object) -> None:
        return None

    def commit(self) -> None:
        return None

    def execute(self, query: str, params: tuple[Any, ...]) -> None:
        branch = str(params[-1])
        if "UPDATE" in query:
            # O repositório grava texto; o Postgres devolve `jsonb` já decodificado.
            payload = json.loads(params[0])
            existing = self.rows.get(branch)
            self._result = None if existing is None else {**existing}
            if self._result is not None:
                self._next_version += 1
                self._result["payload_json"] = payload
                self._result["row_version"] = str(self._next_version)
                self.rows[branch] = self._result
            return
        if "xmin::text AS row_version\n            FROM" in query:
            self.version_probes += 1
            row = self.rows.get(branch)
            self._result = None if row is None else {"row_version": row["row_version"]}
            return
        self.payload_reads += 1
        row = self.rows.get(branch)
        self._result = None if row is None else dict(row)

    def fetchone(self) -> dict[str, Any] | None:
        return self._result


@pytest.fixture
def fake_db(monkeypatch: pytest.MonkeyPatch) -> FakePostgres:
    db = FakePostgres()
    clear_snapshot_row_cache()
    monkeypatch.setattr(repo_module, "get_connection", db.connection)
    yield db
    clear_snapshot_row_cache()


def test_unchanged_snapshot_is_not_fetched_again(fake_db: FakePostgres) -> None:
    fake_db.seed("01", {"operations": [{"work_center": "CT-01A"}]})
    repo = PostgresMachineLoadSnapshotRepository()

    first = repo.get(branch="01")
    second = repo.get(branch="01")

    assert first is not None and second is not None
    assert second["payload_json"] == first["payload_json"]
    assert fake_db.payload_reads == 1
    assert fake_db.version_probes == 2


def test_new_row_version_invalidates_the_cache(fake_db: FakePostgres) -> None:
    fake_db.seed("01", {"operations": [{"work_center": "CT-01A"}]})
    repo = PostgresMachineLoadSnapshotRepository()
    repo.get(branch="01")

    repo.update_payload(branch="01", payload={"operations": [{"work_center": "CT-02"}]})
    after_write = repo.get(branch="01")

    assert after_write is not None
    assert after_write["payload_json"]["operations"][0]["work_center"] == "CT-02"
    # A escrita já devolve a linha nova: a leitura seguinte não rebusca o payload.
    assert fake_db.payload_reads == 1


def test_missing_snapshot_returns_none_and_forgets_the_cache(fake_db: FakePostgres) -> None:
    fake_db.seed("01", {"operations": []})
    repo = PostgresMachineLoadSnapshotRepository()
    repo.get(branch="01")

    fake_db.rows.pop("01")

    assert repo.get(branch="01") is None
    assert fake_db.version_probes == 2


def test_each_branch_keeps_its_own_queue(fake_db: FakePostgres) -> None:
    fake_db.seed("01", {"operations": [{"work_center": "CT-01A"}]})
    fake_db.seed("02", {"operations": [{"work_center": "CT-90"}]})
    repo = PostgresMachineLoadSnapshotRepository()

    first = repo.get(branch="01")
    second = repo.get(branch="02")
    again = repo.get(branch="01")

    assert first is not None and second is not None and again is not None
    assert second["payload_json"]["operations"][0]["work_center"] == "CT-90"
    assert again["payload_json"]["operations"][0]["work_center"] == "CT-01A"
    assert fake_db.payload_reads == 2
