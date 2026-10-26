"""Negative-path proof for the disposable-database guard (PROC-0076 R1.2).

These tests never touch a real engine — a scripted fake connection
answers the guard's read-only probes. They prove that no mutating
statement is ever attempted against an unproven database, and that the
guard can no longer self-mint trust: an absent, foreign or forged
sentinel is rejected, and an empty ``external_data`` schema is *not*
proof of disposability.
"""

from __future__ import annotations

import pytest

from tests.pg_disposable_guard import (
    UnsafeTestDatabaseError,
    assert_safe_dbname,
    assert_safe_host,
    require_disposable_flag,
    require_provision_token,
    validate_target,
    verify_disposable,
    verify_sentinel,
)

ENV_OK = {
    "EXTERNAL_DATA_TEST_PG_DISPOSABLE": "1",
    "EXTERNAL_DATA_TEST_PG_TOKEN": "tok-provisioned",
}


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


def _sentinel_row(token="tok-provisioned", dbname="external_data_test",
                  provisioned_by="pg_provision"):
    return {"token": token, "dbname": dbname, "provisioned_by": provisioned_by}


def _sentinel_answers(sentinel_rows=None, has_sentinel=True):
    """Probe script for ``verify_sentinel``/``verify_disposable`` calls
    that already know the dbname: to_regclass → sentinel rows."""
    return [
        {"sentinel": "public.delpi_disposable_db_guard" if has_sentinel else None},
        list(sentinel_rows) if sentinel_rows is not None else [_sentinel_row()],
    ]


def _target_answers(actual="external_data_test", sentinel_rows=None,
                    has_sentinel=True):
    """Probe script for ``validate_target``/``verify_disposable``:
    current_database → to_regclass → sentinel rows."""
    return [
        {"actual": actual},
        *_sentinel_answers(sentinel_rows, has_sentinel),
    ]


def _no_mutations(conn: FakeConn) -> bool:
    return not any(
        any(k in s for k in ("CREATE", "DROP", "INSERT", "UPDATE", "DELETE",
                             "TRUNCATE", "ALTER"))
        for s in conn.cursor_obj.executed
    )


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


class TestProvisionToken:
    def test_missing_token_rejected(self):
        with pytest.raises(UnsafeTestDatabaseError):
            require_provision_token({"EXTERNAL_DATA_TEST_PG_DISPOSABLE": "1"})

    def test_empty_token_rejected(self):
        with pytest.raises(UnsafeTestDatabaseError):
            require_provision_token({"EXTERNAL_DATA_TEST_PG_TOKEN": "  "})

    def test_token_returned(self):
        assert require_provision_token(
            {"EXTERNAL_DATA_TEST_PG_TOKEN": "abc"}
        ) == "abc"


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


class TestSentinelVerification:
    def test_valid_sentinel_passes(self):
        conn = FakeConn(_sentinel_answers())
        verify_sentinel(
            conn, token="tok-provisioned", dbname="external_data_test"
        )
        assert _no_mutations(conn)

    def test_absent_sentinel_refused_without_writes(self):
        """R1.2: an empty database is NOT claimed anymore — no sentinel,
        no trust, and not a single mutating statement."""
        conn = FakeConn(_sentinel_answers(has_sentinel=False))
        with pytest.raises(UnsafeTestDatabaseError):
            verify_sentinel(
                conn, token="tok-provisioned", dbname="external_data_test"
            )
        assert _no_mutations(conn)
        assert not conn.committed

    def test_wrong_token_refused(self):
        """A sentinel provisioned for a different run cannot validate
        this env — forged/pre-existing markers fail closed."""
        conn = FakeConn(
            _sentinel_answers(sentinel_rows=[_sentinel_row(token="other")])
        )
        with pytest.raises(UnsafeTestDatabaseError):
            verify_sentinel(
                conn, token="tok-provisioned", dbname="external_data_test"
            )

    def test_sentinel_for_other_dbname_refused(self):
        conn = FakeConn(
            _sentinel_answers(
                sentinel_rows=[_sentinel_row(dbname="external_data_test_x")]
            )
        )
        with pytest.raises(UnsafeTestDatabaseError):
            verify_sentinel(
                conn, token="tok-provisioned", dbname="external_data_test"
            )

    def test_sentinel_not_written_by_provisioner_refused(self):
        """Legacy/self-created sentinels (no provisioned_by=pg_provision)
        are not proof."""
        conn = FakeConn(
            _sentinel_answers(
                sentinel_rows=[_sentinel_row(provisioned_by="test-harness")]
            )
        )
        with pytest.raises(UnsafeTestDatabaseError):
            verify_sentinel(
                conn, token="tok-provisioned", dbname="external_data_test"
            )

    def test_verify_disposable_revalidates_at_mutation_boundary(self):
        conn = FakeConn(_target_answers())
        verify_disposable(conn, ENV_OK)
        assert _no_mutations(conn)


class TestValidateTarget:
    def test_full_chain_accepted_for_safe_target(self):
        conn = FakeConn(_target_answers())
        validate_target(
            host="localhost",
            dbname="external_data_test",
            conn=conn,
            env=ENV_OK,
        )
        assert _no_mutations(conn)

    def test_production_like_config_rejected_before_engine_sql(self):
        """Prod-looking host+dbname must fail before the engine probe —
        only flag/host/name checks run, zero statements executed."""
        conn = FakeConn(_target_answers(actual="plugins"))
        with pytest.raises(UnsafeTestDatabaseError):
            validate_target(
                host="postgres-plugins",
                dbname="plugins",
                conn=conn,
                env=ENV_OK,
            )
        assert conn.cursor_obj.executed == []

    def test_missing_token_rejected_before_engine_sql(self):
        """Flag + loopback + test-name are NOT sufficient without the
        provisioner token — zero statements executed."""
        conn = FakeConn(_target_answers())
        env = {"EXTERNAL_DATA_TEST_PG_DISPOSABLE": "1"}
        with pytest.raises(UnsafeTestDatabaseError):
            validate_target(
                host="localhost",
                dbname="external_data_test",
                conn=conn,
                env=env,
            )
        assert conn.cursor_obj.executed == []

    def test_dbname_mismatch_rejected(self):
        conn = FakeConn(_target_answers(actual="other_db"))
        with pytest.raises(UnsafeTestDatabaseError):
            validate_target(
                host="localhost",
                dbname="external_data_test",
                conn=conn,
                env=ENV_OK,
            )

    def test_missing_flag_rejected_with_zero_sql(self):
        conn = FakeConn(_target_answers())
        with pytest.raises(UnsafeTestDatabaseError):
            validate_target(
                host="localhost",
                dbname="external_data_test",
                conn=conn,
                env={"EXTERNAL_DATA_TEST_PG_TOKEN": "tok-provisioned"},
            )
        assert conn.cursor_obj.executed == []
