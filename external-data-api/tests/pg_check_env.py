"""CLI entrypoint: validate the configured PG test target (R1.2).

Usage (inside external-data-api):

    EXTERNAL_DATA_TEST_PG_HOST=... python -m tests.pg_check_env

Exits 0 when the target passes the full fail-closed validation,
non-zero otherwise. Read-only: connects and verifies, never mutates.
"""

from __future__ import annotations

import os
import sys

from tests import pg_disposable_guard as g


def main() -> int:
    if not g.test_pg_configured():
        print("SKIP: EXTERNAL_DATA_TEST_PG_HOST not set")
        return 0
    import psycopg  # noqa: PLC0415 - deferred: only needed when configured

    host = os.environ.get(g.HOST_ENV, "")
    port = int(os.environ.get("EXTERNAL_DATA_TEST_PG_PORT", "5432"))
    dbname = os.environ.get("EXTERNAL_DATA_TEST_PG_NAME", "")
    user = os.environ.get("EXTERNAL_DATA_TEST_PG_USER", "")
    password = os.environ.get("EXTERNAL_DATA_TEST_PG_PASSWORD", "")
    try:
        conn = psycopg.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
            autocommit=True,
        )
    except Exception as exc:  # pragma: no cover - env dependent
        print(f"FAIL: cannot connect: {exc}")
        return 2
    try:
        g.validate_target(host=host, dbname=dbname, conn=conn)
    except g.UnsafeTestDatabaseError as exc:
        print(f"BLOCKED: {exc}")
        return 3
    finally:
        conn.close()
    print("OK: target proven disposable (provisioner sentinel + token)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
