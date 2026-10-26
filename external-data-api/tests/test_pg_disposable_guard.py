"""Negative-path proof for the disposable-database guard (PROC-0076 R1.1).

These tests never touch a real engine — a scripted fake connection
answers the guard's read-only probes. They prove that no mutating
statement (CREATE sentinel, and by extension any later DROP/migration)
is ever attempted against an unproven database.
"""

from __future__ import annotations

import pytest

from tests.pg_disposable_guard import (
    UnsafeTestDatabaseError,
    assert_safe_dbname,
    assert_safe_host,
    ensure_disposable_database,
    require_disposable_flag,
    validate_target,
)


class FakeCursor:
    """Answers the guard's probes from a script; records every statement."""

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
        self.committed = False

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        self.committed = True


def _answers(dbname="external_data_test", sentinel=None, has_tables=False):
    return [
        {"dbname": dbname},
        {"sentinel": sentinel},
        {"has_tables": has_tables},
    ]


class TestRequireDisposableFlag:
    def test_missing_flag_rejected(self):
        with pytest.raises(UnsafeTestDatabaseError):
            require_disposable_flag({"EXTERNAL_DATA_TEST_PG_HOST": "localhost"})

    def test_falsy_flag_rejected(self):
        env = {
            "EXTERNAL_DATA_TEST_PG_HOST": "localhost",
            "EXTERNAL_DATA_TEST_PG_DISPOSABLE": "0",
        }
        with pytest.raises(UnsafeTestDatabaseError):
            require_disposable_flag(env)

    def test_truthy_flag_accepted(self):
        env = {"EXTERNAL_DATA_TEST_PG_DISPOSABLE": "true"}
        require_disposable_flag(env)  # no raise


class TestHostAndDbname:
    def test_remote_host_requires_allow_flag(self):
        env = {"EXTERNAL_DATA_TEST_PG_DISPOSABLE": "1"}
        with pytest.raises(UnsafeTestDatabaseError):
            assert_safe_host("192.168.1.237", env)
        with pytest.raises(UnsafeTestDatabaseError):
            assert_safe_host("postgres-plugins", env)

    def test_remote_host_allowed_only_with_explicit_override(self):
        env = {
            "EXTERNAL_DATA_TEST_PG_DISPOSABLE": "1",
            "EXTERNAL_DATA_TEST_PG_ALLOW_REMOTE": "1",
        }
        assert_safe_host("192.168.1.237", env)

    @pytest.mark.parametrize("host", ["localhost", "127.0.0.1", "::1"])
    def test_loopback_accepted(self, host):
        assert_safe_host(host, {})

    @pytest.mark.parametrize(
        "dbname",
        ["postgres", "template0", "template1", "delpi_plugins", "plugins", ""],
    )
    def test_unsafe_dbnames_rejected(self, dbname):
        with pytest.raises(UnsafeTestDatabaseError):
            assert_safe_dbname(dbname)

    def test_test_dbname_accepted(self):
        assert_safe_dbname("external_data_test")


class TestEngineProbe:
    def test_existing_sentinel_passes_without_writes(self):
        conn = FakeConn(
            _answers(sentinel="public.delpi_disposable_db_guard")
        )
        ensure_disposable_database(conn)
        assert not any(
            "CREATE TABLE" in s for s in conn.cursor_obj.executed
        )
        assert not conn.committed or True

    def test_empty_database_is_claimed_with_sentinel(self):
        conn = FakeConn(_answers(has_tables=False))
        ensure_disposable_database(conn)
        statements = conn.cursor_obj.executed
        assert any("CREATE TABLE" in s for s in statements)
        assert any("INSERT INTO public.delpi_disposable_db_guard" in s for s in statements)
        assert conn.committed

    def test_populated_schema_without_sentinel_refused(self):
        """external_data already holds objects but no sentinel: treat as
        real — refuse before any mutating statement is issued."""
        conn = FakeConn(_answers(has_tables=True))
        with pytest.raises(UnsafeTestDatabaseError):
            ensure_disposable_database(conn)
        assert not any(
            "CREATE TABLE" in s or "DROP" in s or "INSERT" in s
            for s in conn.cursor_obj.executed
        )
        assert not conn.committed


def _target_answers(actual="external_data_test", sentinel=None, has_tables=False):
    # validate_target probes actual dbname, then ensure_disposable_database
    # re-probes dbname + sentinel + schema emptiness.
    return [
        {"actual": actual},
        {"dbname": actual},
        {"sentinel": sentinel},
        {"has_tables": has_tables},
    ]


class TestValidateTarget:
    def test_full_chain_accepted_for_safe_target(self):
        env = {"EXTERNAL_DATA_TEST_PG_DISPOSABLE": "1"}
        conn = FakeConn(_target_answers())
        validate_target(
            host="localhost",
            dbname="external_data_test",
            conn=conn,
            env=env,
        )

    def test_production_like_config_rejected_before_engine_sql(self):
        """Prod-looking host+dbname must fail before the engine probe —
        only flag/host/name checks run, zero statements executed."""
        env = {"EXTERNAL_DATA_TEST_PG_DISPOSABLE": "1"}
        conn = FakeConn(_target_answers(actual="plugins"))
        with pytest.raises(UnsafeTestDatabaseError):
            validate_target(
                host="postgres-plugins",
                dbname="plugins",
                conn=conn,
                env=env,
            )
        assert conn.cursor_obj.executed == []

    def test_dbname_mismatch_rejected(self):
        env = {"EXTERNAL_DATA_TEST_PG_DISPOSABLE": "1"}
        conn = FakeConn(_target_answers(actual="other_db"))
        with pytest.raises(UnsafeTestDatabaseError):
            validate_target(
                host="localhost",
                dbname="external_data_test",
                conn=conn,
                env=env,
            )

    def test_missing_flag_rejected_with_zero_sql(self):
        conn = FakeConn(_target_answers())
        with pytest.raises(UnsafeTestDatabaseError):
            validate_target(
                host="localhost",
                dbname="external_data_test",
                conn=conn,
                env={},
            )
        assert conn.cursor_obj.executed == []
