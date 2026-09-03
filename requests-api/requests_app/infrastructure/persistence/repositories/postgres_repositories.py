from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from psycopg.types.json import Jsonb

from requests_app.domain.entities import (
    AssignmentEntry,
    Request,
    RequestType,
    StatusHistoryEntry,
)
from requests_app.domain.exceptions import WorkflowEngineError
from requests_app.domain.ports import (
    IdempotencyRepositoryPort,
    RequestRepositoryPort,
    RequestTypeRepositoryPort,
)
from requests_app.infrastructure.persistence.plugins_postgres_connection import (
    plugins_connection,
)

_SCHEMA = "my_requests"


def _row_to_type(row: dict[str, Any]) -> RequestType:
    workflow = row.get("workflow_definition") or {}
    if isinstance(workflow, str):
        workflow = json.loads(workflow)
    form_schema = row.get("form_schema") or {}
    if isinstance(form_schema, str):
        form_schema = json.loads(form_schema)
    ui_schema = row.get("ui_schema") or {}
    if isinstance(ui_schema, str):
        ui_schema = json.loads(ui_schema)
    destination = row.get("destination_config") or {}
    if isinstance(destination, str):
        destination = json.loads(destination)
    return RequestType(
        id=row["id"],
        code=row["code"],
        name=row["name"],
        description=row.get("description"),
        category=row.get("category") or "general",
        icon=row.get("icon") or "file-text",
        active=bool(row.get("active", True)),
        version=int(row.get("version") or 1),
        presentation_mode=row.get("presentation_mode") or "specialized",
        branch_scope=row.get("branch_scope") or "optional",
        form_schema=form_schema if isinstance(form_schema, dict) else {},
        ui_schema=ui_schema if isinstance(ui_schema, dict) else {},
        workflow_definition=workflow if isinstance(workflow, dict) else {},
        destination_config=destination if isinstance(destination, dict) else {},
        permission_prefix=row["permission_prefix"],
    )


def _row_to_request(row: dict[str, Any], *, type_code: str) -> Request:
    payload = row.get("payload") or {}
    if isinstance(payload, str):
        payload = json.loads(payload)
    return Request(
        id=row["id"],
        request_number=row["request_number"],
        request_type_id=row["request_type_id"],
        type_code=type_code,
        status=row["status"],
        priority=row.get("priority") or "normal",
        branch_code=row.get("branch_code"),
        created_by_user_id=row["created_by_user_id"],
        created_by_name=row["created_by_name"],
        payload=payload if isinstance(payload, dict) else {},
        return_reason=row.get("return_reason"),
        cancel_justification=row.get("cancel_justification"),
        version=int(row.get("version") or 1),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
        completed_at=row.get("completed_at"),
        cancelled_at=row.get("cancelled_at"),
    )


class PostgresRequestTypeRepository(RequestTypeRepositoryPort):
    def get_by_code(self, code: str) -> RequestType | None:
        sql = f"""
        SELECT * FROM {_SCHEMA}.request_types
        WHERE code = %s
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, ((code or "").strip(),))
                row = cur.fetchone()
        return _row_to_type(dict(row)) if row else None

    def get_by_id(self, type_id: UUID | str) -> RequestType | None:
        sql = f"""
        SELECT * FROM {_SCHEMA}.request_types
        WHERE id = %s::uuid
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (str(type_id),))
                row = cur.fetchone()
        return _row_to_type(dict(row)) if row else None

    def list_active(self) -> list[RequestType]:
        sql = f"""
        SELECT * FROM {_SCHEMA}.request_types
        WHERE active = TRUE
        ORDER BY name ASC
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                rows = cur.fetchall()
        return [_row_to_type(dict(row)) for row in rows]


class PostgresRequestRepository(RequestRepositoryPort):
    def next_request_number(self) -> str:
        year = datetime.now(timezone.utc).year
        sql = f"SELECT nextval('{_SCHEMA}.request_number_seq') AS n"
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                row = cur.fetchone()
            conn.commit()
        return f"REQ-{year}-{int(row['n']):06d}"

    def create(self, request: Request, *, history: StatusHistoryEntry) -> Request:
        insert_sql = f"""
        INSERT INTO {_SCHEMA}.requests (
            id, request_number, request_type_id, status, priority, branch_code,
            created_by_user_id, created_by_name, payload, version
        ) VALUES (
            %s::uuid, %s, %s::uuid, %s, %s, %s,
            %s, %s, %s, %s
        )
        RETURNING *
        """
        history_sql = f"""
        INSERT INTO {_SCHEMA}.request_status_history (
            request_id, from_status, to_status, action,
            actor_user_id, actor_name, justification, changes
        ) VALUES (
            %s::uuid, %s, %s, %s, %s, %s, %s, %s
        )
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    insert_sql,
                    (
                        str(request.id),
                        request.request_number,
                        str(request.request_type_id),
                        request.status,
                        request.priority,
                        request.branch_code,
                        request.created_by_user_id,
                        request.created_by_name,
                        Jsonb(request.payload or {}),
                        request.version,
                    ),
                )
                row = cur.fetchone()
                cur.execute(
                    history_sql,
                    (
                        str(request.id),
                        history.from_status,
                        history.to_status,
                        history.action,
                        history.actor_user_id,
                        history.actor_name,
                        history.justification,
                        Jsonb(history.changes or {}),
                    ),
                )
            conn.commit()
        return _row_to_request(dict(row), type_code=request.type_code)

    def get(self, request_id: UUID | str) -> Request | None:
        sql = f"""
        SELECT r.*, t.code AS type_code
        FROM {_SCHEMA}.requests r
        JOIN {_SCHEMA}.request_types t ON t.id = r.request_type_id
        WHERE r.id = %s::uuid
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (str(request_id),))
                row = cur.fetchone()
        if not row:
            return None
        data = dict(row)
        type_code = data.pop("type_code")
        return _row_to_request(data, type_code=type_code)

    def update(
        self,
        request: Request,
        *,
        history: StatusHistoryEntry | None = None,
        assignment: AssignmentEntry | None = None,
        expected_version: int | None = None,
    ) -> Request:
        update_sql = f"""
        UPDATE {_SCHEMA}.requests SET
            status = %s,
            payload = %s,
            return_reason = %s,
            cancel_justification = %s,
            version = %s,
            updated_at = NOW(),
            completed_at = %s,
            cancelled_at = %s
        WHERE id = %s::uuid
          AND (%s::int IS NULL OR version = %s)
        RETURNING *
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    update_sql,
                    (
                        request.status,
                        Jsonb(request.payload or {}),
                        request.return_reason,
                        request.cancel_justification,
                        request.version,
                        request.completed_at,
                        request.cancelled_at,
                        str(request.id),
                        expected_version,
                        expected_version,
                    ),
                )
                row = cur.fetchone()
                if row is None:
                    raise WorkflowEngineError(code="stale_version", status_code=409)
                if history is not None:
                    cur.execute(
                        f"""
                        INSERT INTO {_SCHEMA}.request_status_history (
                            request_id, from_status, to_status, action,
                            actor_user_id, actor_name, justification, changes
                        ) VALUES (
                            %s::uuid, %s, %s, %s, %s, %s, %s, %s
                        )
                        """,
                        (
                            str(request.id),
                            history.from_status,
                            history.to_status,
                            history.action,
                            history.actor_user_id,
                            history.actor_name,
                            history.justification,
                            Jsonb(history.changes or {}),
                        ),
                    )
                if assignment is not None:
                    cur.execute(
                        f"""
                        INSERT INTO {_SCHEMA}.request_assignments (
                            request_id, role, assignee_user_id, queue_code
                        ) VALUES (%s::uuid, %s, %s, %s)
                        """,
                        (
                            str(request.id),
                            assignment.role,
                            assignment.assignee_user_id,
                            assignment.queue_code,
                        ),
                    )
            conn.commit()
        return _row_to_request(dict(row), type_code=request.type_code)

    def list_mine(
        self,
        *,
        user_id: str,
        type_code: str | None = None,
        status: str | None = None,
        branch_code: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Request], int]:
        where = ["r.created_by_user_id = %s"]
        params: list[Any] = [user_id]
        if type_code:
            where.append("t.code = %s")
            params.append(type_code)
        if status:
            where.append("r.status = %s")
            params.append(status)
        if branch_code:
            where.append("r.branch_code = %s")
            params.append(branch_code)
        where_sql = " AND ".join(where)
        count_sql = f"""
        SELECT COUNT(*) AS total
        FROM {_SCHEMA}.requests r
        JOIN {_SCHEMA}.request_types t ON t.id = r.request_type_id
        WHERE {where_sql}
        """
        list_sql = f"""
        SELECT r.*, t.code AS type_code
        FROM {_SCHEMA}.requests r
        JOIN {_SCHEMA}.request_types t ON t.id = r.request_type_id
        WHERE {where_sql}
        ORDER BY r.created_at DESC
        LIMIT %s OFFSET %s
        """
        offset = max(page - 1, 0) * page_size
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(count_sql, params)
                total = int((cur.fetchone() or {}).get("total") or 0)
                cur.execute(list_sql, [*params, page_size, offset])
                rows = cur.fetchall()
        items = []
        for row in rows:
            data = dict(row)
            code = data.pop("type_code")
            items.append(_row_to_request(data, type_code=code))
        return items, total

    def list_work_queue(
        self,
        *,
        type_codes: list[str] | None = None,
        status: str | None = None,
        branch_code: str | None = None,
        exclude_statuses: list[str] | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Request], int]:
        where = ["TRUE"]
        params: list[Any] = []
        if type_codes is not None:
            if not type_codes:
                return [], 0
            where.append("t.code = ANY(%s)")
            params.append(type_codes)
        if status:
            where.append("r.status = %s")
            params.append(status)
        if branch_code:
            where.append("r.branch_code = %s")
            params.append(branch_code)
        if exclude_statuses:
            where.append("NOT (r.status = ANY(%s))")
            params.append(exclude_statuses)
        where_sql = " AND ".join(where)
        count_sql = f"""
        SELECT COUNT(*) AS total
        FROM {_SCHEMA}.requests r
        JOIN {_SCHEMA}.request_types t ON t.id = r.request_type_id
        WHERE {where_sql}
        """
        list_sql = f"""
        SELECT r.*, t.code AS type_code
        FROM {_SCHEMA}.requests r
        JOIN {_SCHEMA}.request_types t ON t.id = r.request_type_id
        WHERE {where_sql}
        ORDER BY r.created_at DESC
        LIMIT %s OFFSET %s
        """
        offset = max(page - 1, 0) * page_size
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(count_sql, params)
                total = int((cur.fetchone() or {}).get("total") or 0)
                cur.execute(list_sql, [*params, page_size, offset])
                rows = cur.fetchall()
        items = []
        for row in rows:
            data = dict(row)
            code = data.pop("type_code")
            items.append(_row_to_request(data, type_code=code))
        return items, total


class PostgresIdempotencyRepository(IdempotencyRepositoryPort):
    def get(
        self,
        *,
        key: str,
        route: str,
        actor_user_id: str,
        max_age_hours: int = 24,
    ) -> dict[str, Any] | None:
        sql = f"""
        SELECT response_snapshot
        FROM {_SCHEMA}.idempotency_keys
        WHERE key = %s
          AND route = %s
          AND actor_user_id = %s
          AND created_at >= NOW() - (%s || ' hours')::interval
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (key, route, actor_user_id, str(max_age_hours)))
                row = cur.fetchone()
        if not row:
            return None
        snapshot = row["response_snapshot"]
        if isinstance(snapshot, str):
            return json.loads(snapshot)
        return dict(snapshot) if snapshot else None

    def save(
        self,
        *,
        key: str,
        route: str,
        actor_user_id: str,
        response_snapshot: dict[str, Any],
    ) -> None:
        sql = f"""
        INSERT INTO {_SCHEMA}.idempotency_keys
            (key, route, actor_user_id, response_snapshot)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (key, route, actor_user_id)
        DO UPDATE SET response_snapshot = EXCLUDED.response_snapshot,
                      created_at = NOW()
        """
        with plugins_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (key, route, actor_user_id, Jsonb(response_snapshot)))
            conn.commit()
