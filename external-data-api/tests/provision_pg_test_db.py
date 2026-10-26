"""Provisioner for the disposable PostgreSQL test database (R1.2).

Run before the PG suite:

    EXTERNAL_DATA_TEST_PG_HOST=localhost \
    EXTERNAL_DATA_TEST_PG_PORT=55438 \
    EXTERNAL_DATA_TEST_PG_USER=postgres \
    EXTERNAL_DATA_TEST_PG_PASSWORD=test \
    python -m tests.provision_pg_test_db

It creates a brand-new, uniquely named ``external_data_test_<hex>``
database on the target instance, writes the ``delpi_disposable_db_guard``
sentinel with a random token *inside that database*, and prints the
``export`` lines the test suite needs (``..._NAME`` + ``..._TOKEN``).

The token is the binding between this provisioning act and the test
process: the guard in ``pg_disposable_guard.py`` verifies it read-only
and never mints trust on its own — a database this provisioner did not
create cannot pass.

Safety: refuses non-loopback hosts unless
``EXTERNAL_DATA_TEST_PG_ALLOW_REMOTE=1``; only ever *creates* databases,
never drops them (cleanup is the container's job, or a manual
``DROP DATABASE`` by the operator).
"""

from __future__ import annotations

import os
import secrets
import sys

from tests.pg_disposable_guard import (
    PROVISIONED_BY,
    SENTINEL_TABLE,
    assert_safe_host,
)

_ADMIN_DB_ENV = "EXTERNAL_DATA_TEST_PG_ADMIN_DB"


def provision() -> dict[str, str]:
    import psycopg

    host = os.environ["EXTERNAL_DATA_TEST_PG_HOST"]
    assert_safe_host(host)
    port = int(os.getenv("EXTERNAL_DATA_TEST_PG_PORT", "5432"))
    user = os.getenv("EXTERNAL_DATA_TEST_PG_USER", "postgres")
    password = os.getenv("EXTERNAL_DATA_TEST_PG_PASSWORD", "test")
    admin_db = os.getenv(_ADMIN_DB_ENV, "postgres")

    suffix = secrets.token_hex(3)
    dbname = f"external_data_test_{suffix}"
    token = secrets.token_hex(16)

    # CREATE DATABASE cannot run inside a transaction → autocommit.
    admin = psycopg.connect(
        host=host,
        port=port,
        dbname=admin_db,
        user=user,
        password=password,
        sslmode="disable",
        connect_timeout=5,
        autocommit=True,
    )
    try:
        with admin.cursor() as cur:
            cur.execute(f'CREATE DATABASE "{dbname}"')
    finally:
        admin.close()

    conn = psycopg.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password,
        sslmode="disable",
        connect_timeout=5,
        autocommit=True,
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE TABLE public.{SENTINEL_TABLE} ("
                "  token text NOT NULL,"
                "  dbname text NOT NULL,"
                "  provisioned_by text NOT NULL,"
                "  provisioned_at timestamptz NOT NULL DEFAULT now()"
                ")"
            )
            cur.execute(
                f"INSERT INTO public.{SENTINEL_TABLE} "
                "(token, dbname, provisioned_by) VALUES (%s, %s, %s)",
                (token, dbname, PROVISIONED_BY),
            )
    finally:
        conn.close()

    return {"name": dbname, "token": token}


def main() -> int:
    result = provision()
    print(f"export EXTERNAL_DATA_TEST_PG_NAME={result['name']}")
    print(f"export EXTERNAL_DATA_TEST_PG_TOKEN={result['token']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
