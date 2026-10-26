"""Fail-closed guard for destructive PostgreSQL tests (PROC-0076 R1.1).

``test_market_data_repository_pg.py`` runs ``DROP SCHEMA external_data
CASCADE`` and full migration cycles against whatever database the
``EXTERNAL_DATA_TEST_PG_*`` env vars point at. A mistyped host or dbname
could hit a real database — the mere presence of env vars is no proof of
disposability.

This module centralizes a four-layer check, all required before any
mutating statement is allowed:

1. ``EXTERNAL_DATA_TEST_PG_HOST`` absent → callers skip (TEST_NOT_RUN).
2. ``EXTERNAL_DATA_TEST_PG_DISPOSABLE`` must be an explicit truthy value —
   the operator declares "this database may be destroyed".
3. Host must be loopback unless ``EXTERNAL_DATA_TEST_PG_ALLOW_REMOTE`` is
   also truthy; dbname must contain ``test`` and must not be a reserved
   name (``postgres``, ``template*``, anything looking like a real app
   database).
4. **Proof inside the engine**: the database must either already carry
   the sentinel table ``public.delpi_disposable_db_guard`` (claimed as
   disposable by a previous guarded run) or be *claimable* — the
   ``external_data`` schema absent or empty. A database that holds rows
   under ``external_data`` without the sentinel is treated as real and
   refused.

Nothing here trusts comments, hostnames or defaults alone: the sentinel
is written *inside* the database by this guard itself, so only a
database that this harness has already proven empty can be re-used.
"""

from __future__ import annotations

import os

DISPOSABLE_FLAG = "EXTERNAL_DATA_TEST_PG_DISPOSABLE"
ALLOW_REMOTE_FLAG = "EXTERNAL_DATA_TEST_PG_ALLOW_REMOTE"
HOST_ENV = "EXTERNAL_DATA_TEST_PG_HOST"
SENTINEL_TABLE = "delpi_disposable_db_guard"
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


def _fetchall(cur) -> list[dict]:
    rows = cur.fetchall()
    out = []
    for row in rows:
        if isinstance(row, dict):
            out.append(row)
        else:
            out.append(dict(zip([d[0] for d in cur.description], row)))
    return out


def ensure_disposable_database(conn) -> None:
    """Probe the engine and claim it only when provably disposable.

    Executes only read-only queries until the sentinel is written; never
    runs destructive SQL itself. Raises ``UnsafeTestDatabaseError`` when
    the database looks like it may contain real data.
    """
    with conn.cursor() as cur:
        cur.execute("SELECT current_database() AS dbname")
        dbname = cur.fetchone()["dbname"]

        cur.execute(
            "SELECT to_regclass(%s) AS sentinel",
            (f"public.{SENTINEL_TABLE}",),
        )
        if cur.fetchone()["sentinel"] is not None:
            return  # claimed by a previous guarded run

        cur.execute(
            "SELECT EXISTS ("
            "  SELECT 1 FROM information_schema.tables "
            "  WHERE table_schema = %s"
            ") AS has_tables",
            (CANONICAL_SCHEMA,),
        )
        if cur.fetchone()["has_tables"]:
            raise UnsafeTestDatabaseError(
                f"Database {dbname!r} already holds objects under schema "
                f"{CANONICAL_SCHEMA!r} but carries no disposable sentinel "
                f"(public.{SENTINEL_TABLE}) — refusing to treat it as a "
                "test database."
            )

        cur.execute(
            f"CREATE TABLE IF NOT EXISTS public.{SENTINEL_TABLE} ("
            "  disposable boolean NOT NULL CHECK (disposable),"
            "  declared_at timestamptz NOT NULL DEFAULT now()"
            ")"
        )
        cur.execute(
            f"INSERT INTO public.{SENTINEL_TABLE} (disposable) "
            "VALUES (true)"
        )
        conn.commit()


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
    with conn.cursor() as cur:
        cur.execute("SELECT current_database() AS actual")
        actual = cur.fetchone()["actual"]
    if actual != dbname:
        raise UnsafeTestDatabaseError(
            f"Connected database {actual!r} does not match configured "
            f"test database {dbname!r} — refusing to proceed."
        )
    ensure_disposable_database(conn)
