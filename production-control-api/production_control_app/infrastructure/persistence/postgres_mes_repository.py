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
    DowntimeTreatmentConflict,
    DowntimeTreatmentNotFound,
    DowntimeReasonConflict,
    InvalidMesEvent,
    MesStateConflict,
)
from production_control_app.infrastructure.persistence.plugins_postgres_connection import (
    PC_SCHEMA_NAME,
    get_connection,
)

_REASONS = f"{PC_SCHEMA_NAME}.downtime_reason_catalog"
def _work_center_lock_key(branch: str, work_center: str) -> str:
    return f"pc-mes-wc:{branch}:{work_center}"


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
    def lock_work_center(self, *, branch: str, work_center: str, conn: Any) -> None:
        """Serialização por CT dentro da transação chamadora.

        pg_advisory_xact_lock sobre a chave do posto — toda escrita em
        fatos MES do (branch, work_center) passa por aqui ou pelo
        try_lock do tick autônomo: Play/transições e monitoramento sem
        OP nunca produzem fatos concorrentes.
        """
        with conn.cursor() as cur:
            cur.execute(
                "SELECT pg_advisory_xact_lock(hashtext(%s))",
                (_work_center_lock_key(branch, work_center),),
            )

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
        expected_updated_at: datetime | None = None,
        conn: Any | None = None,
    ) -> dict[str, Any]:
        def _run(conn_: Any) -> dict[str, Any]:
            try:
                with conn_.cursor() as cur:
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
                           AND (%s::timestamptz IS NULL OR updated_at = %s)
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
                            expected_updated_at,
                            expected_updated_at,
                        ),
                    )
                    row = cur.fetchone()
            except ForeignKeyViolation as exc:
                raise InvalidMesEvent(
                    "Motivo de parada inexistente no catálogo."
                ) from exc
            except psycopg.errors.CheckViolation as exc:
                raise InvalidMesEvent(str(exc)) from exc
            if row is None:
                if expected_updated_at is not None:
                    with conn_.cursor() as cur_:
                        cur_.execute(
                            f"SELECT 1 FROM {_DOWNTIMES} WHERE id = %s::uuid",
                            (downtime_id,),
                        )
                        if cur_.fetchone() is not None:
                            raise DowntimeConflict(
                                "A parada foi alterada por outra escrita; "
                                "recarregue antes de confirmar a classificação."
                            )
                raise DowntimeNotFound("Parada não encontrada.")
            return dict(row)

        if conn is not None:
            return _run(conn)
        with get_connection() as conn_:
            try:
                row = _run(conn_)
            except Exception:
                conn_.rollback()
                raise
            conn_.commit()
            return row

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

    def list_pending_classification(
        self, run_id: str, *, limit: int = 5
    ) -> list[dict[str, Any]]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT {_DOWNTIME_COLUMNS}
                    FROM {_DOWNTIMES}
                    WHERE run_id = %s::uuid
                      AND (confirmed = FALSE OR reason_code IS NULL)
                    ORDER BY started_at
                    LIMIT %s
                    """,
                    (run_id, int(limit)),
                )
                return [dict(row) for row in cur.fetchall()]

    def list_unclassified_for_work_center(
        self,
        *,
        branch: str,
        work_center: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT {_DOWNTIME_COLUMNS}
                    FROM {_DOWNTIMES}
                    WHERE branch = %s
                      AND work_center = %s
                      AND ended_at IS NOT NULL
                      AND (confirmed = FALSE OR reason_code IS NULL)
                    ORDER BY started_at DESC
                    LIMIT %s
                    """,
                    (branch, work_center, int(limit)),
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

    def list_all(self) -> list[dict[str, Any]]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT code, label, category, default_planned,
                           default_counts_as_availability_loss, requires_note,
                           active, sort_order, created_at, updated_at
                    FROM {_REASONS}
                    ORDER BY sort_order, code
                    """
                )
                return [dict(row) for row in cur.fetchall()]

    def create(
        self,
        *,
        code: str,
        label: str,
        category: str,
        requires_note: bool,
        sort_order: int,
    ) -> dict[str, Any]:
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"""
                        INSERT INTO {_REASONS} (
                            code, label, category, requires_note, active, sort_order
                        ) VALUES (%s, %s, %s, %s, TRUE, %s)
                        RETURNING code, label, category, default_planned,
                                  default_counts_as_availability_loss, requires_note,
                                  active, sort_order, created_at, updated_at
                        """,
                        (
                            str(code).strip().lower(),
                            str(label).strip(),
                            str(category).strip().lower(),
                            bool(requires_note),
                            int(sort_order),
                        ),
                    )
                    row = cur.fetchone()
                conn.commit()
        except UniqueViolation:
            raise DowntimeReasonConflict(
                f"Já existe motivo de parada com o código '{str(code).strip().lower()}'."
            ) from None
        return dict(row)

    def update(
        self,
        code: str,
        *,
        label: str,
        category: str,
        requires_note: bool,
        sort_order: int,
    ) -> dict[str, Any] | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE {_REASONS}
                       SET label = %s,
                           category = %s,
                           requires_note = %s,
                           sort_order = %s,
                           updated_at = NOW()
                     WHERE code = %s
                    RETURNING code, label, category, default_planned,
                              default_counts_as_availability_loss, requires_note,
                              active, sort_order, created_at, updated_at
                    """,
                    (
                        str(label).strip(),
                        str(category).strip().lower(),
                        bool(requires_note),
                        int(sort_order),
                        str(code).strip().lower(),
                    ),
                )
                row = cur.fetchone()
            conn.commit()
            return dict(row) if row else None

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


_AUDIT = f"{PC_SCHEMA_NAME}.mes_audit_events"


class PostgresMesAuditRepository:
    """Auditoria append-only das ações MES — nunca registra tokens/segredos."""

    def append(
        self,
        *,
        branch: str,
        work_center: str,
        action: str,
        actor_type: str,
        actor_ref: str | None = None,
        run_id: str | None = None,
        occurred_at: Any | None = None,
        details: dict[str, Any] | None = None,
        conn: Any | None = None,
    ) -> dict[str, Any]:
        from psycopg.types.json import Jsonb

        sql = f"""
            INSERT INTO {_AUDIT}
                (branch, work_center, run_id, action, actor_type, actor_ref,
                 occurred_at, details)
            VALUES (%s, %s, %s::uuid, %s, %s, %s,
                    COALESCE(%s, NOW()), %s)
            RETURNING id, branch, work_center, run_id::text AS run_id, action,
                      actor_type, actor_ref, occurred_at, details, created_at
        """
        params = (
            branch,
            work_center,
            run_id,
            str(action).strip(),
            actor_type,
            actor_ref,
            occurred_at,
            Jsonb(details or {}),
        )
        if conn is not None:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return dict(cur.fetchone())
        with get_connection() as conn_:
            with conn_.cursor() as cur:
                cur.execute(sql, params)
                row = dict(cur.fetchone())
            conn_.commit()
            return row

    def list_for_run(self, run_id: str) -> list[dict[str, Any]]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT id, branch, work_center, run_id::text AS run_id,
                           action, actor_type, actor_ref, occurred_at, details,
                           created_at
                    FROM {_AUDIT}
                    WHERE run_id = %s::uuid
                    ORDER BY occurred_at, created_at
                    """,
                    (run_id,),
                )
                return [dict(row) for row in cur.fetchall()]

    def list_for_downtime(self, downtime_id: str) -> list[dict[str, Any]]:
        """Eventos de auditoria da parada — details->>'downtimeId'."""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT id, branch, work_center, run_id::text AS run_id,
                           action, actor_type, actor_ref, occurred_at, details,
                           created_at
                    FROM {_AUDIT}
                    WHERE details->>'downtimeId' = %s
                    ORDER BY occurred_at, created_at
                    """,
                    (downtime_id,),
                )
                return [dict(row) for row in cur.fetchall()]


_TREATMENTS = f"{PC_SCHEMA_NAME}.mes_downtime_treatments"
_TREATMENT_COLUMNS = """
    downtime_id::text AS downtime_id, branch, work_center, analysis,
    cause_kind, cause_note, action_needed, justification, status,
    request_id::text AS request_id, request_type_code, linked_at,
    linked_by_ref, linked_by_name, conclusion_reason, concluded_at,
    concluded_by_ref, concluded_by_name, created_by_ref, created_by_name,
    updated_by_ref, updated_by_name, created_at, updated_at
"""


class PostgresMesDowntimeTreatmentRepository:
    """Triagem gerencial 1:1 da parada — concorrência otimista por updated_at.

    expected_updated_at=None no upsert significa "o registro ainda não
    existe": o INSERT é protegido pelo PK; um valor presente exige que a linha
    esteja exatamente no estado lido pelo cliente.
    """

    def get(
        self, downtime_id: str, *, conn: Any | None = None
    ) -> dict[str, Any] | None:
        def _read(c: Any) -> dict[str, Any] | None:
            with c.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT {_TREATMENT_COLUMNS}
                    FROM {_TREATMENTS}
                    WHERE downtime_id = %s::uuid
                    """,
                    (downtime_id,),
                )
                row = cur.fetchone()
                return dict(row) if row else None

        if conn is not None:
            return _read(conn)
        with get_connection() as own:
            return _read(own)

    def upsert(
        self,
        downtime_id: str,
        *,
        branch: str,
        work_center: str,
        analysis: str,
        cause_kind: str,
        cause_note: str | None,
        action_needed: bool,
        justification: str,
        expected_updated_at: datetime | None,
        actor_ref: str,
        actor_name: str,
        conn: Any | None = None,
    ) -> dict[str, Any]:
        def _run(conn_: Any) -> dict[str, Any]:
            if expected_updated_at is None:
                try:
                    with conn_.cursor() as cur:
                        cur.execute(
                            f"""
                            INSERT INTO {_TREATMENTS} (
                                downtime_id, branch, work_center, analysis,
                                cause_kind, cause_note, action_needed,
                                justification, created_by_ref, created_by_name,
                                updated_by_ref, updated_by_name
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (downtime_id) DO NOTHING
                            RETURNING {_TREATMENT_COLUMNS}
                            """,
                            (
                                downtime_id, branch, work_center, analysis,
                                cause_kind, cause_note, bool(action_needed),
                                justification, actor_ref, actor_name,
                                actor_ref, actor_name,
                            ),
                        )
                        row = cur.fetchone()
                except ForeignKeyViolation as exc:
                    raise DowntimeNotFound("Parada não encontrada.") from exc
                if row is not None:
                    return dict(row)
                raise DowntimeTreatmentConflict(
                    "A parada já possui triagem registrada; recarregue antes de "
                    "atualizar."
                )
            with conn_.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE {_TREATMENTS}
                       SET analysis = %s,
                           cause_kind = %s,
                           cause_note = %s,
                           action_needed = %s,
                           justification = %s,
                           updated_by_ref = %s,
                           updated_by_name = %s,
                           updated_at = NOW()
                     WHERE downtime_id = %s::uuid
                       AND updated_at = %s
                    RETURNING {_TREATMENT_COLUMNS}
                    """,
                    (
                        analysis, cause_kind, cause_note, bool(action_needed),
                        justification, actor_ref, actor_name, downtime_id,
                        expected_updated_at,
                    ),
                )
                row = cur.fetchone()
            if row is not None:
                return dict(row)
            existing = self.get(downtime_id, conn=conn_)
            if existing is None:
                raise DowntimeTreatmentNotFound(
                    "Triagem não encontrada para esta parada."
                )
            raise DowntimeTreatmentConflict(
                "A triagem foi alterada por outra escrita; recarregue antes de "
                "atualizar."
            )

        if conn is not None:
            return _run(conn)
        with get_connection() as own:
            try:
                row_ = _run(own)
            except Exception:
                own.rollback()
                raise
            own.commit()
            return row_

    def link_request(
        self,
        downtime_id: str,
        *,
        request_id: str,
        request_type_code: str,
        actor_ref: str,
        actor_name: str,
        conn: Any | None = None,
    ) -> dict[str, Any]:
        """Vincula a solicitação — idempotente para o mesmo request_id."""
        def _run(conn_: Any) -> dict[str, Any]:
            with conn_.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE {_TREATMENTS}
                       SET request_id = %s::uuid,
                           request_type_code = %s,
                           status = 'referred',
                           linked_at = NOW(),
                           linked_by_ref = %s,
                           linked_by_name = %s,
                           updated_at = NOW()
                     WHERE downtime_id = %s::uuid
                       AND status <> 'concluded'
                       AND (request_id IS NULL OR request_id = %s::uuid)
                    RETURNING {_TREATMENT_COLUMNS}
                    """,
                    (
                        request_id, request_type_code, actor_ref, actor_name,
                        downtime_id, request_id,
                    ),
                )
                row = cur.fetchone()
            if row is not None:
                return dict(row)
            existing = self.get(downtime_id, conn=conn_)
            if existing is None:
                raise DowntimeTreatmentNotFound(
                    "Registre a triagem antes de encaminhar a solicitação."
                )
            raise DowntimeTreatmentConflict(
                "A parada já está vinculada a outra solicitação ou encerrada."
            )

        if conn is not None:
            return _run(conn)
        with get_connection() as own:
            try:
                row_ = _run(own)
            except Exception:
                own.rollback()
                raise
            own.commit()
            return row_

    def conclude(
        self,
        downtime_id: str,
        *,
        reason: str,
        actor_ref: str,
        actor_name: str,
        conn: Any | None = None,
    ) -> dict[str, Any]:
        def _run(conn_: Any) -> dict[str, Any]:
            with conn_.cursor() as cur:
                cur.execute(
                    f"""
                    UPDATE {_TREATMENTS}
                       SET status = 'concluded',
                           conclusion_reason = %s,
                           concluded_at = NOW(),
                           concluded_by_ref = %s,
                           concluded_by_name = %s,
                           updated_at = NOW()
                     WHERE downtime_id = %s::uuid
                       AND status <> 'concluded'
                    RETURNING {_TREATMENT_COLUMNS}
                    """,
                    (reason, actor_ref, actor_name, downtime_id),
                )
                row = cur.fetchone()
            if row is not None:
                return dict(row)
            existing = self.get(downtime_id, conn=conn_)
            if existing is None:
                raise DowntimeTreatmentNotFound(
                    "Triagem não encontrada para esta parada."
                )
            raise DowntimeTreatmentConflict(
                "O tratamento desta parada já foi concluído."
            )

        if conn is not None:
            return _run(conn)
        with get_connection() as own:
            try:
                row_ = _run(own)
            except Exception:
                own.rollback()
                raise
            own.commit()
            return row_


_OBSERVERS = f"{PC_SCHEMA_NAME}.work_center_pulse_observers"
_OBSERVER_COLUMNS = """
    branch, work_center, device_id::text AS device_id, counter_epoch,
    last_counter, last_increment_at, baseline_established_at,
    device_online, degraded_reason, last_seen_at, created_at, updated_at
"""



class PostgresWorkCenterPulseObserverRepository:
    """Cursor durável do monitoramento autônomo + trava por centro de trabalho.

    A trava advisory (pg_advisory_xact_lock sobre a chave do CT) é a
    serialização entre o tick autônomo e as transições do run — dois
    pollers, um Play e um tick nunca tocam os fatos do mesmo posto ao
    mesmo tempo (ADR-03).
    """

    def try_lock_work_center(
        self, *, branch: str, work_center: str, conn: Any
    ) -> bool:
        """Trava não bloqueante do CT dentro da transação chamadora.

        Tick autônomo: se outro writer segura a trava, o ciclo é pulado —
        o próximo tick reavalia, nunca empilha espera no poller.
        """
        with conn.cursor() as cur:
            cur.execute(
                "SELECT pg_try_advisory_xact_lock(hashtext(%s)) AS locked",
                (_work_center_lock_key(branch, work_center),),
            )
            row = cur.fetchone()
            if row is None:
                return False
            # psycopg dict_row: acesso por chave — nunca posicional.
            return bool(row.get("locked") if isinstance(row, dict) else row[0])

    def lock_work_center(self, *, branch: str, work_center: str, conn: Any) -> None:
        """Trava bloqueante do CT — transições do run aguardam o tick."""
        with conn.cursor() as cur:
            cur.execute(
                "SELECT pg_advisory_xact_lock(hashtext(%s))",
                (_work_center_lock_key(branch, work_center),),
            )

    def get(self, *, branch: str, work_center: str, conn: Any) -> dict[str, Any] | None:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT {_OBSERVER_COLUMNS}
                FROM {_OBSERVERS}
                WHERE branch = %s AND work_center = %s
                """,
                (branch, work_center),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def upsert(
        self,
        *,
        branch: str,
        work_center: str,
        device_id: str | None,
        counter_epoch: int,
        last_counter: int,
        last_increment_at: Any | None,
        baseline_established_at: Any | None,
        device_online: bool,
        degraded_reason: str | None,
        last_seen_at: Any | None,
        conn: Any,
    ) -> dict[str, Any]:
        """Atualiza o cursor — o caller passa os valores efetivos.

        Quando a decisão não muda o baseline, o caller repete os valores
        já persistidos no observador.
        """
        with conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {_OBSERVERS} (
                    branch, work_center, device_id, counter_epoch,
                    last_counter, last_increment_at, baseline_established_at,
                    device_online, degraded_reason, last_seen_at, updated_at
                )
                VALUES (%s, %s, %s::uuid, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (branch, work_center) DO UPDATE SET
                    device_id = EXCLUDED.device_id,
                    counter_epoch = EXCLUDED.counter_epoch,
                    last_counter = EXCLUDED.last_counter,
                    last_increment_at = EXCLUDED.last_increment_at,
                    baseline_established_at = EXCLUDED.baseline_established_at,
                    device_online = EXCLUDED.device_online,
                    degraded_reason = EXCLUDED.degraded_reason,
                    last_seen_at = EXCLUDED.last_seen_at,
                    updated_at = NOW()
                RETURNING {_OBSERVER_COLUMNS}
                """,
                (
                    branch,
                    work_center,
                    device_id,
                    int(counter_epoch),
                    int(last_counter),
                    last_increment_at,
                    baseline_established_at,
                    bool(device_online),
                    degraded_reason,
                    last_seen_at,
                ),
            )
            return dict(cur.fetchone())
