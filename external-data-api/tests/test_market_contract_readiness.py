"""Contract readiness — fail-closed ledger proof (PROC-0076 R1.3).

Scenario coverage mirrors the acceptance matrix: a database at
V001–V003 (pending or failed V004), a divergent checksum, an absent
ledger, an absent catalog and an unreadable engine must all deny —
and never reach the use cases.
"""

from __future__ import annotations

import hashlib

import pytest

from app.application.contracts import ContractNotReadyError
from app.infrastructure.persistence.market_contract_readiness import (
    REQUIRED_CONTRACT_REVISION,
    check_market_contract_ready,
)
from app.infrastructure.persistence.migrations_runner import MIGRATIONS_DIR


class FakeCursor:
    def __init__(self, answers):
        self._answers = list(answers)
        self.executed: list[str] = []
        self._pending = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        self.executed.append(sql)
        self._pending = self._answers.pop(0) if self._answers else {}

    def fetchone(self):
        return self._pending

    def fetchall(self):
        return self._pending or []


class FakeConn:
    def __init__(self, answers):
        self.cursor_obj = FakeCursor(answers)

    def cursor(self):
        return self.cursor_obj


class ExplodingConn:
    def cursor(self):
        raise RuntimeError("connection lost")


def _v004_checksum() -> str:
    path = next(MIGRATIONS_DIR.glob(f"{REQUIRED_CONTRACT_REVISION}__*.sql"))
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _answers(*, ledger_rows, ledger_table=True, catalog_table=True,
             scope_column=True):
    """Probe script matching the readiness check's four queries."""
    return [
        # 1. to_regclass(schema_migrations)
        {"regclass": "external_data.schema_migrations"
         if ledger_table else None},
        # 2. SELECT version, checksum FROM schema_migrations
        ledger_rows if ledger_table else [],
        # 3. to_regclass(market_data_sources)
        {"regclass": "external_data.market_data_sources"
         if catalog_table else None},
        # 4. information_schema.columns (allowed_use_scope)
        {"column_name": "allowed_use_scope"} if scope_column else None,
    ]


def _ledger(*versions_with_checksum):
    return [
        {"version": version, "checksum": checksum}
        for version, checksum in versions_with_checksum
    ]


# --- positive: V004 applied with canonical checksum --------------------------


def test_ready_when_v004_applied_with_canonical_checksum():
    conn = FakeConn(
        _answers(
            ledger_rows=_ledger(
                ("V001", "aaa"),
                ("V002", "bbb"),
                ("V003", "ccc"),
                (REQUIRED_CONTRACT_REVISION, _v004_checksum()),
            )
        )
    )
    check_market_contract_ready(conn)  # no exception


# --- negatives: every unproven state denies -----------------------------------


def test_blocks_when_v004_missing():
    conn = FakeConn(
        _answers(
            ledger_rows=_ledger(("V001", "a"), ("V002", "b"), ("V003", "c"))
        )
    )
    with pytest.raises(ContractNotReadyError):
        check_market_contract_ready(conn)


def test_blocks_when_ledger_table_absent():
    conn = FakeConn(_answers(ledger_rows=[], ledger_table=False))
    with pytest.raises(ContractNotReadyError):
        check_market_contract_ready(conn)


def test_blocks_when_v004_checksum_diverges():
    conn = FakeConn(
        _answers(
            ledger_rows=_ledger(
                (REQUIRED_CONTRACT_REVISION, "tampered-checksum")
            )
        )
    )
    with pytest.raises(ContractNotReadyError):
        check_market_contract_ready(conn)


def test_blocks_when_catalog_table_absent():
    conn = FakeConn(
        _answers(
            ledger_rows=_ledger(
                (REQUIRED_CONTRACT_REVISION, _v004_checksum())
            ),
            catalog_table=False,
        )
    )
    with pytest.raises(ContractNotReadyError):
        check_market_contract_ready(conn)


def test_blocks_when_scope_column_absent():
    conn = FakeConn(
        _answers(
            ledger_rows=_ledger(
                (REQUIRED_CONTRACT_REVISION, _v004_checksum())
            ),
            scope_column=False,
        )
    )
    with pytest.raises(ContractNotReadyError):
        check_market_contract_ready(conn)


def test_blocks_when_engine_unreadable():
    with pytest.raises(ContractNotReadyError):
        check_market_contract_ready(ExplodingConn())


def test_failure_is_never_silent_empty_list():
    """A ledger read failure must not degrade into an empty catalog
    that could be mistaken for 'no data'."""
    conn = FakeConn(_answers(ledger_rows=[], ledger_table=False))
    with pytest.raises(ContractNotReadyError) as exc:
        check_market_contract_ready(conn)
    assert exc.value.code == "EXTERNAL_DATA_CONTRACT_NOT_READY"
    assert exc.value.http_status == 503
