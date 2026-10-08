# tests/test_governed_sql_executor.py
"""S1 — GovernedSqlExecutor bounded execution tests (fake pyodbc)."""

import pytest

from app.application.services.governed_sql_errors import (
    EXECUTION_FAILED,
    OBJECT_NOT_ALLOWED,
    POLICY_UNAVAILABLE,
    QUERY_TIMEOUT,
    RESULT_TOO_LARGE,
    SQL_VALIDATION_FAILED,
    GovernedSqlError,
)
from app.infrastructure.persistence.totvs.governed_sql_executor import (
    GovernedSqlExecutor,
)


class FakeCursor:
    def __init__(self, description=None, batches=None, exc=None):
        self._description = description
        self._batches = list(batches or [])
        self._exc = exc
        self.executed = None
        self.closed = False
        self.nextset_calls = 0

    def execute(self, sql, params):
        self.executed = (sql, params)
        if self._exc:
            raise self._exc

    @property
    def description(self):
        return self._description

    def fetchmany(self, n):
        if not self._batches:
            return []
        return self._batches.pop(0)[:n]

    def nextset(self):
        self.nextset_calls += 1
        return False

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor
        self.timeout = None
        self.closed = False

    def cursor(self):
        return self._cursor

    def close(self):
        self.closed = True


class ConnectionProbe:
    """Factory that records whether a connection was opened."""

    def __init__(self, cursor=None):
        self.conn = FakeConnection(cursor or FakeCursor())
        self.calls = 0

    def __call__(self):
        self.calls += 1
        return self.conn


def _executor(cursor=None, exc=None):
    conn = FakeConnection(cursor or FakeCursor())
    return GovernedSqlExecutor(connection_factory=lambda: conn), conn


def _executor_probe(cursor=None):
    probe = ConnectionProbe(cursor)
    return GovernedSqlExecutor(connection_factory=probe), probe


def _cols(names):
    return [(n,) for n in names]


# ---------------------------------------------------------------------
# Happy path + parameter binding
# ---------------------------------------------------------------------

def test_executes_with_bound_parameters():
    cursor = FakeCursor(
        description=_cols(["B1_COD"]),
        batches=[[("10080034",)]],
    )
    ex, conn = _executor(cursor)
    result = ex.execute(
        "SELECT B1_COD FROM SB1010 WHERE B1_COD = ?",
        ["10080034"],
    )
    assert cursor.executed[1] == ("10080034",)
    assert result.row_count == 1
    assert result.columns == ["B1_COD"]
    assert result.rows == [["10080034"]]
    assert not result.truncated
    assert conn.closed


def test_parameter_count_cap():
    ex, _ = _executor(FakeCursor(description=_cols(["a"])))
    with pytest.raises(GovernedSqlError) as ei:
        ex.execute(
            "SELECT B1_COD FROM SB1010 WHERE B1_COD = ?",
            [str(i) for i in range(999)],
        )
    assert ei.value.category == RESULT_TOO_LARGE


# ---------------------------------------------------------------------
# Validation gate
# ---------------------------------------------------------------------

def test_unauthorized_table_denied():
    ex, _ = _executor(FakeCursor(description=_cols(["a"])))
    with pytest.raises(GovernedSqlError) as ei:
        ex.execute("SELECT * FROM ZZ9999")
    assert ei.value.category == OBJECT_NOT_ALLOWED


def test_write_statement_denied():
    ex, _ = _executor(FakeCursor())
    with pytest.raises(GovernedSqlError) as ei:
        ex.execute("SELECT * INTO T2 FROM SB1010")
    assert ei.value.category in (SQL_VALIDATION_FAILED, OBJECT_NOT_ALLOWED)


def test_multi_statement_denied():
    ex, _ = _executor(FakeCursor())
    with pytest.raises(GovernedSqlError):
        ex.execute("SELECT * FROM SB1010; SELECT * FROM SB2010")


# ---------------------------------------------------------------------
# Bounded retrieval
# ---------------------------------------------------------------------

def test_row_bound_truncates(monkeypatch):
    import app.infrastructure.persistence.totvs.governed_sql_executor as mod

    monkeypatch.setattr(mod, "GOVERNED_SQL_MAX_ROWS", 3)
    cursor = FakeCursor(
        description=_cols(["a"]),
        batches=[[(i,) for i in range(10)]],
    )
    ex, _ = _executor(cursor)
    result = ex.execute("SELECT a FROM SB1010")
    assert result.row_count == 3
    assert result.truncated
    assert "row_limit" in result.truncation_reasons


def test_column_bound_truncates(monkeypatch):
    import app.infrastructure.persistence.totvs.governed_sql_executor as mod

    monkeypatch.setattr(mod, "GOVERNED_SQL_MAX_COLUMNS", 2)
    cursor = FakeCursor(
        description=_cols(["a", "b", "c"]),
        batches=[[(1, 2, 3)]],
    )
    ex, _ = _executor(cursor)
    result = ex.execute("SELECT a, b, c FROM SB1010")
    assert result.columns == ["a", "b"]
    assert result.truncated
    assert "column_limit" in result.truncation_reasons


def test_cell_size_bound_truncates(monkeypatch):
    import app.infrastructure.persistence.totvs.governed_sql_executor as mod

    monkeypatch.setattr(mod, "GOVERNED_SQL_MAX_CELL_CHARS", 5)
    cursor = FakeCursor(
        description=_cols(["a"]),
        batches=[[("x" * 100,)]],
    )
    ex, _ = _executor(cursor)
    result = ex.execute("SELECT a FROM SB1010")
    assert result.rows == [["xxxxx"]]
    assert result.truncated
    assert "cell_size" in result.truncation_reasons


def test_response_bytes_bound(monkeypatch):
    import app.infrastructure.persistence.totvs.governed_sql_executor as mod

    monkeypatch.setattr(mod, "GOVERNED_SQL_MAX_RESPONSE_BYTES", 50)
    cursor = FakeCursor(
        description=_cols(["a"]),
        batches=[[("abcdefghij",) for _ in range(10)]],
    )
    ex, _ = _executor(cursor)
    result = ex.execute("SELECT a FROM SB1010")
    assert result.truncated
    assert "response_bytes" in result.truncation_reasons


def test_never_calls_fetchall(monkeypatch):
    class NoFetchAllCursor(FakeCursor):
        def fetchall(self):
            raise AssertionError("fetchall must never be used in governed path")

    cursor = NoFetchAllCursor(description=_cols(["a"]), batches=[[(1,)]])
    ex, _ = _executor(cursor)
    result = ex.execute("SELECT a FROM SB1010")
    assert result.row_count == 1


# ---------------------------------------------------------------------
# Error mapping
# ---------------------------------------------------------------------

def test_policy_unavailable_when_connection_missing():
    def bad_factory():
        raise RuntimeError("no GOVERNED_SQL_DB_*")

    ex = GovernedSqlExecutor(connection_factory=bad_factory)
    with pytest.raises(GovernedSqlError) as ei:
        ex.execute("SELECT B1_COD FROM SB1010")
    assert ei.value.category == POLICY_UNAVAILABLE


def test_timeout_mapped():
    cursor = FakeCursor(exc=Exception("HYT00 timeout expired"))
    ex, _ = _executor(cursor)
    with pytest.raises(GovernedSqlError) as ei:
        ex.execute("SELECT B1_COD FROM SB1010")
    assert ei.value.category == QUERY_TIMEOUT
    assert "HYT00" not in ei.value.message  # redacted


def test_generic_execution_error_redacted():
    cursor = FakeCursor(exc=Exception("Login failed for user 'svc' at 10.0.0.1"))
    ex, _ = _executor(cursor)
    with pytest.raises(GovernedSqlError) as ei:
        ex.execute("SELECT B1_COD FROM SB1010")
    assert ei.value.category == EXECUTION_FAILED
    assert "10.0.0.1" not in ei.value.message
    assert "svc" not in ei.value.message
    assert ei.value.detail is not None  # interno apenas


def test_no_resultset():
    cursor = FakeCursor(description=None)
    ex, _ = _executor(cursor)
    with pytest.raises(GovernedSqlError) as ei:
        ex.execute("SELECT B1_COD FROM SB1010")
    assert ei.value.category == EXECUTION_FAILED


# ---------------------------------------------------------------------
# Observability shape
# ---------------------------------------------------------------------

def test_result_metadata():
    cursor = FakeCursor(
        description=_cols(["B1_COD", "B1_DESC"]),
        batches=[[("1", "desc"), ("2", "desc2")]],
    )
    ex, _ = _executor(cursor)
    result = ex.execute("SELECT B1_COD, B1_DESC FROM SB1010", actor="u1", correlation_id="c1")
    assert result.query_hash
    assert len(result.query_hash) == 16
    assert result.duration_ms >= 0
    assert result.row_count == 2


def test_query_hash_distinct_for_params():
    cursor1 = FakeCursor(description=_cols(["a"]), batches=[[(1,)]])
    cursor2 = FakeCursor(description=_cols(["a"]), batches=[[(1,)]])
    ex1, _ = _executor(cursor1)
    ex2, _ = _executor(cursor2)
    r1 = ex1.execute("SELECT B1_COD FROM SB1010 WHERE B1_COD = ?", ["1"])
    r2 = ex2.execute("SELECT B1_COD FROM SB1010 WHERE B1_COD = ?", ["2"])
    assert r1.query_hash != r2.query_hash


# ---------------------------------------------------------------------
# S1 CORRECTIVE — table metadata propagation (validator → result → audit)
# ---------------------------------------------------------------------

from app.application.services.sql_validator import (
    PROFILE_DAVI_GOVERNED,
    SqlValidator,
)


def _run(sql, params=None):
    cursor = FakeCursor(description=_cols(["a"]), batches=[[(1,)]])
    ex, _ = _executor(cursor)
    return ex.execute(sql, params)


def test_validation_result_shape():
    r = SqlValidator().validate_with_result(
        "SELECT B1_COD FROM SB1010", profile=PROFILE_DAVI_GOVERNED
    )
    assert r.profile == PROFILE_DAVI_GOVERNED
    assert r.physical_tables == ("SB1010",)
    assert r.statement_count == 1


def test_validate_backcompat_returns_true():
    assert SqlValidator().validate("SELECT B1_COD FROM SB1010") is True


def test_tables_simple_select():
    assert _run("SELECT B1_COD FROM SB1010").tables == ["SB1010"]


def test_tables_join():
    result = _run(
        "SELECT a.B1_COD FROM SB1010 a JOIN SB2010 b ON a.B1_COD = b.B2_PROD"
    )
    assert result.tables == ["SB1010", "SB2010"]


def test_tables_cte_alias_excluded():
    result = _run(
        "WITH cte AS (SELECT B1_COD FROM SB1010) SELECT * FROM cte"
    )
    assert result.tables == ["SB1010"]


def test_tables_nested_subquery():
    result = _run(
        "SELECT B1_COD FROM SB1010 "
        "WHERE B1_COD IN (SELECT A1_COD FROM SA1010)"
    )
    assert result.tables == ["SA1010", "SB1010"]


def test_tables_union():
    result = _run(
        "SELECT B1_COD FROM SB1010 UNION ALL SELECT A1_COD FROM SA1010"
    )
    assert result.tables == ["SA1010", "SB1010"]


def test_tables_self_join_dedup():
    result = _run(
        "SELECT a.B1_COD FROM SB1010 a JOIN SB1010 b ON a.B1_COD = b.B1_COD"
    )
    assert result.tables == ["SB1010"]


def test_tables_deterministic_sorting():
    # SA1010 listed first in SQL; output must be sorted regardless.
    result = _run(
        "SELECT * FROM SA1010 a JOIN SB1010 b ON a.A1_COD = b.B1_COD"
    )
    assert result.tables == ["SA1010", "SB1010"]


def test_unauthorized_table_never_reaches_db():
    ex, probe = _executor_probe(FakeCursor(description=_cols(["a"])))
    with pytest.raises(GovernedSqlError) as ei:
        ex.execute("SELECT * FROM ZZ9999")
    assert ei.value.category == OBJECT_NOT_ALLOWED
    assert probe.calls == 0


def test_audit_tables_match_result(caplog):
    import logging

    cursor = FakeCursor(
        description=_cols(["a"]), batches=[[(1,)]]
    )
    ex, _ = _executor(cursor)
    with caplog.at_level(logging.INFO, logger="totvs.governed_sql.executor"):
        result = ex.execute(
            "SELECT a.B1_COD FROM SB1010 a JOIN SB2010 b ON a.B1_COD = b.B2_PROD"
        )
    audit = [r for r in caplog.records if "tables=" in r.getMessage()]
    assert audit
    expected = str(result.tables)
    assert all(expected in r.getMessage() for r in audit)


def test_no_independent_reparse(monkeypatch):
    """Executor must not reparse: one structural resolution only."""
    calls = []
    real = SqlValidator.validate_with_result

    def spy(self, sql, *, profile):
        calls.append(sql)
        return real(self, sql, profile=profile)

    monkeypatch.setattr(SqlValidator, "validate_with_result", spy)
    cursor = FakeCursor(description=_cols(["a"]), batches=[[(1,)]])
    ex, _ = _executor(cursor)
    ex.execute("SELECT B1_COD FROM SB1010")
    assert len(calls) == 1
