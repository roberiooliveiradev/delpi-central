from __future__ import annotations

from si_app.infrastructure.providers.totvs.connection_pool import (
    create_totvs_connection,
    get_totvs_connection_pool,
)


def get_connection():
    pool = get_totvs_connection_pool()
    if pool is not None:
        return pool.acquire()
    return create_totvs_connection()


def release_connection(connection, *, discard: bool = False) -> None:
    pool = get_totvs_connection_pool()
    if pool is not None:
        pool.release(connection, discard=discard)
        return

    if connection is not None:
        try:
            connection.close()
        except Exception:
            pass
