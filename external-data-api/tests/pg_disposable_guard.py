"""Fail-closed guard for destructive PostgreSQL tests (PROC-0076 R1.2).

``test_market_data_repository_pg.py`` runs ``DROP SCHEMA external_data
CASCADE`` and full migration cycles against whatever database the
``EXTERNAL_DATA_TEST_PG_*`` env vars point at. A mistyped host or dbname
could hit a real database — and the R1.1 sentinel weakened that proof by
*self-creating* trust on an empty schema: a guard that mints its own
"disposable" marker proves nothing.

R1.2 replaces self-attestation with **provisioner-originated identity**:

1. ``EXTERNAL_DATA_TEST_PG_HOST`` absent → callers skip (TEST_NOT_RUN).
2. ``EXTERNAL_DATA_TEST_PG_DISPOSABLE`` must be truthy — explicit
   operator opt-in.
3. Host must be loopback unless ``EXTERNAL_DATA_TEST_PG_ALLOW_REMOTE``
   is also truthy; dbname must contain ``test`` and must not be a
   reserved name.
4. ``EXTERNAL_DATA_TEST_PG_TOKEN`` must be a non-empty random token
   emitted by ``tests/provision_pg_test_db.py`` at provisioning time.
5. **Proof inside the engine**: ``public.delpi_disposable_db_guard``
   must already exist and carry a row written by the provisioner
   (``provisioned_by = 'pg_provision'``) whose ``token`` matches the env
   var *and* whose ``dbname`` matches the connected database. The guard
   never creates or mutates the sentinel — it only verifies it. A
   database the provisioner did not build cannot present a matching
   token.

The token binds env and engine to the same provisioning act: an env-only
declaration fails (no sentinel row), a pre-existing/foreign sentinel
fails (token mismatch), and an empty ``external_data`` schema is *not*
sufficient — empty is just a state, not an identity.
"""

from __future__ import annotations

import os

DISPOSABLE_FLAG = "EXTERNAL_DATA_TEST_PG_DISPOSABLE"
ALLOW_REMOTE_FLAG = "EXTERNAL_DATA_TEST_PG_ALLOW_REMOTE"
HOST_ENV = "EXTERNAL_DATA_TEST_PG_HOST"
TOKEN_ENV = "EXTERNAL_DATA_TEST_PG_TOKEN"
SENTINEL_TABLE = "delpi_disposable_db_guard"
PROVISIONED_BY = "pg_provision"
CANONICAL_SCHEMA = "external_data"
LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}
RESERVED_DB_NAMES = {"postgres", "template0", "template1"}


class UnsafeTestDatabaseError(RuntimeError):
    """Raised whenever the target database cannot be proven disposable."""


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def test_pg_configured(env: dict[str, str] | None = None) -> bool:
    """Whether a PG test target was configured at all (→ run, don't skip)."""
    env = os.environ if env is None else env
    return bool((env.get(HOST_ENV) or "").strip())


def require_disposable_flag(env: dict[str, str] | None = None) -> None:
    env = os.environ if env is None else env
    if not _truthy(env.get(DISPOSABLE_FLAG)):
        raise UnsafeTestDatabaseError(
            f"{DISPOSABLE_FLAG} is not set to a truthy value — refusing "
            "to run mutating tests against an unproven database. Set it "
            "only when the target database is truly disposable."
        )


def require_provision_token(env: dict[str, str] | None = None) -> str:
    """The provisioner-emitted token — proof that a dedicated, isolated
    database was created for this run by ``provision_pg_test_db``."""
    env = os.environ if env is None else env
    token = (env.get(TOKEN_ENV) or "").strip()
    if not token:
        raise UnsafeTestDatabaseError(
            f"{TOKEN_ENV} is not set — refusing to run mutating tests "
            "without provisioner-originated identity. Provision the "
            "database with `python -m tests.provision_pg_test_db`."
        )
    return token


def assert_safe_host(host: str, env: dict[str, str] | None = None) -> None:
    env = os.environ if env is None else env
    normalized = host.strip().lower()
    if normalized in LOOPBACK_HOSTS:
        return
    if not _truthy(env.get(ALLOW_REMOTE_FLAG)):
        raise UnsafeTestDatabaseError(
            f"Refusing non-loopback PG test host {host!r} without "
            f"{ALLOW_REMOTE_FLAG}=1 — a remote target cannot be assumed "
            "disposable."
        )


def assert_safe_dbname(dbname: str) -> None:
    normalized = dbname.strip().lower()
    if not normalized or normalized in RESERVED_DB_NAMES:
        raise UnsafeTestDatabaseError(
            f"Refusing reserved/empty PG test database name {dbname!r}."
        )
    if "test" not in normalized:
        raise UnsafeTestDatabaseError(
            f"Refusing PG test database name {dbname!r} — disposable "
            "databases must contain 'test' in the name."
        )


def _row_dict(cur, row):
    if isinstance(row, dict):
        return row
    return dict(zip([d[0] for d in cur.description], row))


def _fetchone(cur) -> dict:
    return _row_dict(cur, cur.fetchone())


def _fetchall(cur) -> list[dict]:
    rows = cur.fetchall()
    return [_row_dict(cur, row) for row in rows]


def verify_sentinel(conn, *, token: str, dbname: str) -> None:
    """Verify the provisioner-written sentinel — read-only, never creates.

    Raises ``UnsafeTestDatabaseError`` when the sentinel is absent, when
    no row was written by the provisioner for this database, or when the
    stored token does not match the env-provided one.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT to_regclass(%s) AS sentinel",
            (f"public.{SENTINEL_TABLE}",),
        )
        if _fetchone(cur)["sentinel"] is None:
            raise UnsafeTestDatabaseError(
                f"Database {dbname!r} carries no provisioner sentinel "
                f"(public.{SENTINEL_TABLE}) — refusing to treat it as a "
                "test database."
            )
        cur.execute(
            f"SELECT token, dbname, provisioned_by "
            f"FROM public.{SENTINEL_TABLE}"
        )
        rows = _fetchall(cur)
    matching = [
        row
        for row in rows
        if row.get("provisioned_by") == PROVISIONED_BY
        and row.get("dbname") == dbname
    ]
    if not matching:
        raise UnsafeTestDatabaseError(
            f"Database {dbname!r} sentinel was not written by "
            f"{PROVISIONED_BY!r} for this database — refusing."
        )
    if not any(row.get("token") == token for row in matching):
        raise UnsafeTestDatabaseError(
            f"Sentinel token in database {dbname!r} does not match "
            f"{TOKEN_ENV} — the env and the database were not provisioned "
            "together; refusing."
        )


def verify_disposable(conn, env: dict[str, str] | None = None) -> None:
    """Re-verify provisioner identity at a mutation boundary.

    Read-only: never issues CREATE/DROP/INSERT. Used by the per-test
    fixture so a swapped or rebuilt database is caught mid-suite.
    """
    env = os.environ if env is None else env
    token = require_provision_token(env)
    with conn.cursor() as cur:
        cur.execute("SELECT current_database() AS actual")
        actual = _fetchone(cur)["actual"]
    verify_sentinel(conn, token=token, dbname=actual)


def validate_target(
    *,
    host: str,
    dbname: str,
    conn,
    env: dict[str, str] | None = None,
) -> None:
    """Full fail-closed validation before any mutating SQL is allowed."""
    env = os.environ if env is None else env
    require_disposable_flag(env)
    assert_safe_host(host, env)
    assert_safe_dbname(dbname)
    token = require_provision_token(env)
    with conn.cursor() as cur:
        cur.execute("SELECT current_database() AS actual")
        actual = _fetchone(cur)["actual"]
    if actual != dbname:
        raise UnsafeTestDatabaseError(
            f"Connected database {actual!r} does not match configured "
            f"test database {dbname!r} — refusing to proceed."
        )
    verify_sentinel(conn, token=token, dbname=actual)
