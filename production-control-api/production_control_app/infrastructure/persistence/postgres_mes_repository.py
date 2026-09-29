"""Adapter Postgres — fundação MES: estados do CT, paradas e catálogo.

Somente persistência: toda validação de domínio acontece em
``domain/services/mes_operational_state.py`` e toda orquestração ficará no
application service da Etapa 02. Aqui os índices únicos parciais do banco são
a última barreira contra dois eventos abertos; violações viram erros de
domínio, nunca erro cru do Postgres.

Para transações multi-tabela (ex.: Pause → fecha estado + abre parada + pausa
run), os métodos aceitam ``conn`` opcional: o orquestrador abre a conexão,
executa tudo e faz commit/rollback uma única vez.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import psycopg
from psycopg.errors import ForeignKeyViolation, UniqueViolation

from production_control_app.domain.errors import (
    DowntimeConflict,
    DowntimeNotFound,
    InvalidMesEvent,
    MesStateConflict,
)
from production_control_app.infrastructure.persistence.plugins_postgres_connection import (
    PC_SCHEMA_NAME,
    get_connection,
)

_REASONS = f"{PC_SCHEMA_NAME}.downtime_reason_catalog"
_STATE_EVENTS = f"{PC_SCHEMA_NAME}.work_center_state_events"
_DOWNTIMES = f"{PC_SCHEMA_NAME}.downtime_events"

_STATE_COLUMNS = """
    id::text AS id, branch, work_center, run_id::text AS run_id, state, source,
    started_at, ended_at, created_at
"""

_DOWNTIME_COLUMNS = """
    id::text AS id, branch, work_center, run_id::text AS run_id,
    state_event_id::text AS state_event_id, production_order, operation_code,
    started_at, ended_at, reason_code, planned, counts_as_availability_loss,
    source, confirmed, confirmed_at, confirmed_by_type, confirmed_by_ref,
    note, created_at, updated_at
"""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PostgresWorkCenterStateRepository:
    def get_open(
        self, *, branch: str, work_center: str, conn: Any | None = None
    ) -> dict[str, Any] | None:
        def _read(c: Any) -> dict[str, Any] | None:
            with c.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT {_STATE_COLUMNS}
                    FROM {_STATE_EVENTS}
                    WHERE branch = %s AND work_center = %s AND ended_at IS NULL
                    LIMIT 1
                    """,
                    (branch, work_center),
                )
                row = cur.fetchone()
                return dict(row) if row else None

        if conn is not None:
            return _read(conn)
        with get_connection() as own:
            return _read(own)

    def open_event(
        self,
        *,
        branch: str,
        work_center: str,
        state: str,
        source: str,
        run_id: str | None = None,
        started_at: datetime | None = None,
        conn: Any | None = None,
    ) -> dict[str, Any]:
        if conn is not None:
            return self._open_event(
                conn,
                branch=branch,
                work_center=work_center,
                state=state,
                source=source,
                run_id=run_id,
                started_at=started_at,
            )
        with get_connection() as own:
            row = self._open_event(
                own,
                branch=branch,
                work_center=work_center,
                state=state,
                source=source,
                run_id=run_id,
                started_at=started_at,
            )
            own.commit()
            return row

    def _open_event(self, conn: Any, **kwargs: Any) -> dict[str, Any]:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO {_STATE_EVENTS} (
                        branch, work_center, run_id, state, source, started_at
                    )
                    VALUES (%s, %s, %s::uuid, %s, %s, %s)
                    RETURNING {_STATE_COLUMNS}
                    """,
                    (
                        kwargs["branch"],
                        kwargs["work_center"],
                        kwargs["run_id"],
                        kwargs["state"],
                        kwargs["source"],
                        kwargs["started_at"] or _utc_now(),
                    ),
                )
                return dict(cur.fetchone())
        except UniqueViolation as exc:
            raise MesStateConflict(
                "Já existe um estado operacional aberto neste posto."
            ) from exc
        except ForeignKeyViolation as exc:
            raise InvalidMesEvent("run_id referenciado não existe.") from exc

    def close_open(
        self,
        *,
        branch: str,
        work_center: str,
        ended_at: datetime | None = None,
        conn: Any | None = None,
    ) -> dict[str, Any] | None:
        if conn is not None:
            return self._close_open(
                conn, branch=branch, work_center=work_center, ended_at=ended_at
            )
        with get_connection() as own:
            row = self._close_open(
                own, branch=branch, work_center=work_center, ended_at=ended_at
            )
            own.commit()
            return row

    def _close_open(self, conn: Any, **kwargs: Any) -> dict[str, Any] | None:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE {_STATE_EVENTS}
                   SET ended_at = %s
                 WHERE branch = %s AND work_center = %s AND ended_at IS NULL
                RETURNING {_STATE_COLUMNS}
                """,
                (
                    kwargs["ended_at"] or _utc_now(),
                    kwargs["branch"],
                    kwargs["work_center"],
                ),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def list_for_work_center(
        self, *, branch: str, work_center: str, limit: int = 200
    ) -> list[dict[str, Any]]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT {_STATE_COLUMNS}
                    FROM {_STATE_EVENTS}
                    WHERE branch = %s AND work_center = %s
                    ORDER BY started_at DESC
                    LIMIT %s
                    """,
                    (branch, work_center, int(limit)),
                )
                return [dict(row) for row in cur.fetchall()]

    def list_for_run(self, run_id: str) -> list[dict[str, Any]]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT {_STATE_COLUMNS}
                    FROM {_STATE_EVENTS}
                    WHERE run_id = %s::uuid
                    ORDER BY started_at
                    """,
                    (run_id,),
                )
                return [dict(row) for row in cur.fetchall()]


class PostgresDowntimeEventRepository:
    def get_open(
        self, *, branch: str, work_center: str, conn: Any | None = None
    ) -> dict[str, Any] | None:
        def _read(c: Any) -> dict[str, Any] | None:
            with c.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT {_DOWNTIME_COLUMNS}
                    FROM {_DOWNTIMES}
                    WHERE branch = %s AND work_center = %s AND ended_at IS NULL
                    LIMIT 1
                    """,
                    (branch, work_center),
                )
                row = cur.fetchone()
                return dict(row) if row else None

        if conn is not None:
            return _read(conn)
        with get_connection() as own:
            return _read(own)

    def get(self, downtime_id: str) -> dict[str, Any] | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT {_DOWNTIME_COLUMNS}
                    FROM {_DOWNTIMES}
                    WHERE id = %s::uuid
                    LIMIT 1
                    """,
                    (downtime_id,),
                )
                row = cur.fetchone()
                return dict(row) if row else None

    def create(
        self,
        *,
        branch: str,
        work_center: str,
        source: str,
        run_id: str | None = None,
        state_event_id: str | None = None,
        production_order: str | None = None,
        operation_code: str | None = None,
        started_at: datetime | None = None,
        conn: Any | None = None,
    ) -> dict[str, Any]:
        if conn is not None:
            return self._create(
                conn,
                branch=branch,
                work_center=work_center,
                source=source,
                run_id=run_id,
                state_event_id=state_event_id,
                production_order=production_order,
                operation_code=operation_code,
                started_at=started_at,
            )
        with get_connection() as own:
            row = self._create(
                own,
                branch=branch,
                work_center=work_center,
                source=source,
                run_id=run_id,
                state_event_id=state_event_id,
                production_order=production_order,
                operation_code=operation_code,
                started_at=started_at,
            )
            own.commit()
            return row

    def _create(self, conn: Any, **kwargs: Any) -> dict[str, Any]:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO {_DOWNTIMES} (
                        branch, work_center, run_id, state_event_id,
                        production_order, operation_code, source, started_at
                    )
                    VALUES (%s, %s, %s::uuid, %s::uuid, %s, %s, %s, %s)
                    RETURNING {_DOWNTIME_COLUMNS}
                    """,
                    (
                        kwargs["branch"],
                        kwargs["work_center"],
                        kwargs["run_id"],
                        kwargs["state_event_id"],
                        kwargs["production_order"],
                        kwargs["operation_code"],
                        kwargs["source"],
                        kwargs["started_at"] or _utc_now(),
                    ),
                )
                return dict(cur.fetchone())
        except UniqueViolation as exc:
            raise DowntimeConflict(
                "Já existe uma parada aberta neste posto."
            ) from exc
        except ForeignKeyViolation as exc:
            raise InvalidMesEvent(
                "run_id, state_event_id ou reason_code referenciado não existe."
            ) from exc

    def classify(
        self,
        downtime_id: str,
        *,
        reason_code: str,
        planned: bool | None,
        counts_as_availability_loss: bool | None,
        note: str | None = None,
        confirmed_by_type: str | None = None,
        confirmed_by_ref: str | None = None,
        confirmed: bool = True,
    ) -> dict[str, Any]:
        with get_connection() as conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        f"""
                        UPDATE {_DOWNTIMES}
                           SET reason_code = %s,
                               planned = %s,
                               counts_as_availability_loss = %s,
                               note = COALESCE(%s, note),
                               confirmed = %s,
                               confirmed_at = CASE WHEN %s THEN NOW() ELSE NULL END,
                               confirmed_by_type = %s,
                               confirmed_by_ref = %s,
                               updated_at = NOW()
                         WHERE id = %s::uuid
                        RETURNING {_DOWNTIME_COLUMNS}
                        """,
                        (
                            reason_code,
                            planned,
                            counts_as_availability_loss,
                            note,
                            bool(confirmed),
                            bool(confirmed),
                            confirmed_by_type,
                            confirmed_by_ref,
                            downtime_id,
                        ),
                    )
                    row = cur.fetchone()
            except ForeignKeyViolation as exc:
                conn.rollback()
                raise InvalidMesEvent(
                    "Motivo de parada inexistente no catálogo."
                ) from exc
            except psycopg.errors.CheckViolation as exc:
                conn.rollback()
                raise InvalidMesEvent(str(exc)) from exc
            if row is None:
                conn.rollback()
                raise DowntimeNotFound("Parada não encontrada.")
            conn.commit()
            return dict(row)

    def close_open(
        self,
        *,
        branch: str,
        work_center: str,
        ended_at: datetime | None = None,
        conn: Any | None = None,
    ) -> dict[str, Any] | None:
        if conn is not None:
            return self._close_open(
                conn, branch=branch, work_center=work_center, ended_at=ended_at
            )
        with get_connection() as own:
            row = self._close_open(
                own, branch=branch, work_center=work_center, ended_at=ended_at
            )
            own.commit()
            return row

    def _close_open(self, conn: Any, **kwargs: Any) -> dict[str, Any] | None:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE {_DOWNTIMES}
                   SET ended_at = %s,
                       updated_at = NOW()
                 WHERE branch = %s AND work_center = %s AND ended_at IS NULL
                RETURNING {_DOWNTIME_COLUMNS}
                """,
                (
                    kwargs["ended_at"] or _utc_now(),
                    kwargs["branch"],
                    kwargs["work_center"],
                ),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def list_for_run(self, run_id: str) -> list[dict[str, Any]]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT {_DOWNTIME_COLUMNS}
                    FROM {_DOWNTIMES}
                    WHERE run_id = %s::uuid
                    ORDER BY started_at
                    """,
                    (run_id,),
                )
                return [dict(row) for row in cur.fetchall()]

    def list_for_work_center(
        self,
        *,
        branch: str,
        work_center: str,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        clauses = ["branch = %s", "work_center = %s"]
        params: list[Any] = [branch, work_center]
        if start is not None:
            clauses.append("started_at >= %s")
            params.append(start)
        if end is not None:
            clauses.append("started_at < %s")
            params.append(end)
        params.append(int(limit))
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT {_DOWNTIME_COLUMNS}
                    FROM {_DOWNTIMES}
                    WHERE {" AND ".join(clauses)}
                    ORDER BY started_at DESC
                    LIMIT %s
                    """,
                    params,
                )
                return [dict(row) for row in cur.fetchall()]


class PostgresDowntimeReasonRepository:
    def get(self, code: str) -> dict[str, Any] | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT code, label, category, default_planned,
                           default_counts_as_availability_loss, requires_note,
                           active, sort_order, created_at, updated_at
                    FROM {_REASONS}
                    WHERE code = %s
                    LIMIT 1
                    """,
                    (str(code).strip().lower(),),
                )
                row = cur.fetchone()
                return dict(row) if row else None

    def list_active(self) -> list[dict[str, Any]]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT code, label, category, default_planned,
                           default_counts_as_availability_loss, requires_note,
                           active, sort_order, created_at, updated_at
                    FROM {_REASONS}
                    WHERE active
                    ORDER BY sort_order, code
                    """
                )
                return [dict(row) for row in cur.fetchall()]

    def set_active(self, code: str, *, active: bool) -> dict[str, Any] | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE {_REASONS}
                       SET active = %s,
                           updated_at = NOW()
                     WHERE code = %s
                    RETURNING code, label, category, default_planned,
                              default_counts_as_availability_loss, requires_note,
                              active, sort_order, created_at, updated_at
                    """,
                    (bool(active), str(code).strip().lower()),
                )
                row = cur.fetchone()
            conn.commit()
            return dict(row) if row else None
