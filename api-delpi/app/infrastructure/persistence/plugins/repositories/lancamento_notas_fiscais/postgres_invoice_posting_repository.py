"""Persistência Postgres — solicitações de lançamento de NF."""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Sequence
from uuid import UUID

import psycopg
from psycopg.errors import ForeignKeyViolation, UniqueViolation
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.domain.services.lancamento_notas_fiscais.exceptions import (
    DuplicateFiscalKeyError,
)
from app.domain.services.lancamento_notas_fiscais.fiscal_normalization import (
    RECONCILIATION_ELIGIBLE_STATUSES,
    RECONCILIATION_LOCK_CLASS_ID,
    RECONCILIATION_LOCK_OBJECT_ID,
)
from app.domain.services.lancamento_notas_fiscais.history_serialization import (
    history_changes_json_safe,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
    PluginsRepositoryError,
)
from app.infrastructure.providers.database.plugins_postgres_connection import (
    get_plugins_connection_settings,
)


def _is_unique_violation(exc: BaseException) -> bool:
    current: BaseException | None = exc
    while current is not None:
        if isinstance(current, UniqueViolation):
            return True
        current = current.__cause__ or current.__context__  # type: ignore[assignment]
    return False


SCHEMA = "lancamento_notas_fiscais"

_REQUEST_COLUMNS = """
    id, branch_code, document_number, document_match_key, series,
    supplier_code, supplier_store, supplier_name, supplier_short_name,
    issue_date, amount, received_at, observation, status,
    block_reason, block_description,
    created_by_user_id, created_by_name, assignee_user_id, assignee_name,
    cancelled_at, cancelled_by_user_id, cancelled_by_name, cancel_justification,
    completion_source, sf1_recno, erp_entry_date, reconciled_at,
    divergence_alert, divergence_detected_at, divergence_detail,
    created_at, updated_at
"""


class PostgresInvoicePostingRepository(PluginBaseRepository):
    def __init__(self, connection=None) -> None:
        super().__init__(connection=connection)
        self._reconciliation_lock_conn: Any | None = None

    def find_active_by_fiscal_key(
        self,
        *,
        branch_code: str,
        supplier_code: str,
        supplier_store: str,
        document_match_key: str,
        series: str,
        exclude_id: str | None = None,
    ) -> dict[str, Any] | None:
        params: list[Any] = [
            branch_code,
            supplier_code,
            supplier_store,
            document_match_key,
            series,
        ]
        exclude_sql = ""
        if exclude_id:
            exclude_sql = " AND id <> %s::uuid"
            params.append(exclude_id)
        row = self.fetch_one(
            f"""
            SELECT {_REQUEST_COLUMNS}
              FROM {SCHEMA}.invoice_posting_requests
             WHERE branch_code = %s
               AND supplier_code = %s
               AND supplier_store = %s
               AND document_match_key = %s
               AND series = %s
               AND status <> 'cancelled'
               {exclude_sql}
             LIMIT 1
            """,
            tuple(params),
        )
        return _serialize_request(row) if row else None

    def create_request_with_history(
        self,
        *,
        request_fields: dict[str, Any],
        history_fields: dict[str, Any],
    ) -> dict[str, Any]:
        try:
            row = self.execute_returning_one(
                f"""
                INSERT INTO {SCHEMA}.invoice_posting_requests (
                    branch_code, document_number, document_match_key, series,
                    supplier_code, supplier_store, supplier_name, supplier_short_name,
                    issue_date, amount, received_at, observation, status,
                    created_by_user_id, created_by_name
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s
                )
                RETURNING {_REQUEST_COLUMNS}
                """,
                (
                    request_fields["branch_code"],
                    request_fields["document_number"],
                    request_fields["document_match_key"],
                    request_fields["series"],
                    request_fields["supplier_code"],
                    request_fields["supplier_store"],
                    request_fields["supplier_name"],
                    request_fields.get("supplier_short_name"),
                    request_fields["issue_date"],
                    request_fields["amount"],
                    request_fields["received_at"],
                    request_fields.get("observation"),
                    request_fields["status"],
                    request_fields["created_by_user_id"],
                    request_fields["created_by_name"],
                ),
                auto_commit=False,
            )
            assert row is not None
            history_fields = {
                **history_fields,
                "request_id": row["id"],
            }
            self._insert_history(history_fields, auto_commit=False)
            self.commit()
            return _serialize_request(row)
        except PluginsRepositoryError as exc:
            if _is_unique_violation(exc):
                raise DuplicateFiscalKeyError() from exc
            raise
        except UniqueViolation as exc:
            self.rollback()
            raise DuplicateFiscalKeyError() from exc
        except Exception:
            self.rollback()
            raise

    def get_request(self, request_id: str) -> dict[str, Any] | None:
        row = self.fetch_one(
            f"""
            SELECT {_REQUEST_COLUMNS}
              FROM {SCHEMA}.invoice_posting_requests
             WHERE id = %s::uuid
            """,
            (request_id,),
        )
        return _serialize_request(row) if row else None

    def list_history(self, request_id: str) -> list[dict[str, Any]]:
        rows = self.fetch_all(
            f"""
            SELECT id, request_id, event_type, actor_origin, actor_user_id, actor_name,
                   from_status, to_status, changes, justification, created_at
              FROM {SCHEMA}.invoice_posting_history
             WHERE request_id = %s::uuid
             ORDER BY created_at ASC, id ASC
            """,
            (request_id,),
        )
        return [_serialize_history(r) for r in rows]

    def list_comments(self, request_id: str) -> list[dict[str, Any]]:
        rows = self.fetch_all(
            f"""
            SELECT id, request_id, author_user_id, author_name, body, created_at
              FROM {SCHEMA}.invoice_posting_comments
             WHERE request_id = %s::uuid
             ORDER BY created_at ASC, id ASC
            """,
            (request_id,),
        )
        return [_serialize_comment(r) for r in rows]

    def list_requests(
        self,
        *,
        filters: dict[str, Any],
        created_by_user_id: str | None,
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        where = ["TRUE"]
        params: list[Any] = []

        if created_by_user_id:
            where.append("created_by_user_id = %s")
            params.append(created_by_user_id)
        if filters.get("branch"):
            where.append("branch_code = %s")
            params.append(filters["branch"])
        if filters.get("status"):
            where.append("status = %s")
            params.append(filters["status"])
        if filters.get("supplier"):
            where.append(
                "(supplier_code ILIKE %s OR supplier_name ILIKE %s)"
            )
            pattern = f"%{filters['supplier']}%"
            params.extend([pattern, pattern])
        if filters.get("document"):
            where.append(
                "(document_number LIKE %s OR document_match_key LIKE %s)"
            )
            digits = "".join(ch for ch in str(filters["document"]) if ch.isdigit())
            pattern = f"%{digits or filters['document']}%"
            params.extend([pattern, pattern])
        if filters.get("issued_from"):
            where.append("issue_date >= %s")
            params.append(filters["issued_from"])
        if filters.get("issued_to"):
            where.append("issue_date <= %s")
            params.append(filters["issued_to"])
        if filters.get("received_from"):
            where.append("received_at >= %s")
            params.append(filters["received_from"])
        if filters.get("received_to"):
            where.append("received_at <= %s")
            params.append(filters["received_to"])

        where_sql = " AND ".join(where)
        count_row = self.fetch_one(
            f"""
            SELECT COUNT(*) AS total
              FROM {SCHEMA}.invoice_posting_requests
             WHERE {where_sql}
            """,
            tuple(params),
        )
        total = int(count_row["total"]) if count_row else 0
        page = max(int(page), 1)
        page_size = max(1, min(int(page_size), 100))
        offset = (page - 1) * page_size
        rows = self.fetch_all(
            f"""
            SELECT {_REQUEST_COLUMNS}
              FROM {SCHEMA}.invoice_posting_requests
             WHERE {where_sql}
             ORDER BY received_at ASC, created_at ASC
             LIMIT %s OFFSET %s
            """,
            tuple(params + [page_size, offset]),
        )
        return {
            "items": [_serialize_request(r) for r in rows],
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": max((total + page_size - 1) // page_size, 1) if total else 0,
        }

    def list_reconciliation_candidates(
        self,
        *,
        limit: int,
        prioritize_ids: Sequence[str] | None = None,
        order_by: str = "fifo",
    ) -> list[dict[str, Any]]:
        statuses = tuple(sorted(RECONCILIATION_ELIGIBLE_STATUSES))
        limit = max(0, int(limit))
        if limit == 0:
            return []

        selected: list[dict[str, Any]] = []
        seen: set[str] = set()

        if prioritize_ids:
            ids = [str(x) for x in prioritize_ids if str(x).strip()]
            if ids:
                rows = self.fetch_all(
                    f"""
                    SELECT {_REQUEST_COLUMNS}
                      FROM {SCHEMA}.invoice_posting_requests
                     WHERE id = ANY(%s::uuid[])
                       AND status = ANY(%s)
                    """,
                    (ids, list(statuses)),
                )
                for row in rows:
                    item = _serialize_request(row)
                    rid = str(item["id"])
                    if rid not in seen:
                        seen.add(rid)
                        selected.append(item)

        remaining = limit - len(selected)
        if remaining > 0:
            order_sql = (
                "updated_at DESC, received_at ASC, created_at ASC"
                if order_by == "recent"
                else "received_at ASC, created_at ASC"
            )
            params: list[Any] = [list(statuses)]
            exclude_sql = ""
            if seen:
                exclude_sql = " AND NOT (id = ANY(%s::uuid[]))"
                params.append(list(seen))
            params.append(remaining)
            rows = self.fetch_all(
                f"""
                SELECT {_REQUEST_COLUMNS}
                  FROM {SCHEMA}.invoice_posting_requests
                 WHERE status = ANY(%s)
                   {exclude_sql}
                 ORDER BY {order_sql}
                 LIMIT %s
                """,
                tuple(params),
            )
            for row in rows:
                item = _serialize_request(row)
                rid = str(item["id"])
                if rid not in seen:
                    seen.add(rid)
                    selected.append(item)

        return selected[:limit]

    def mark_reconciled_posted_batch(
        self,
        items: Sequence[dict[str, Any]],
    ) -> int:
        if not items:
            return 0

        posted = 0
        try:
            for item in items:
                request_id = item["request_id"]
                from_status = item.get("from_status")
                row = self.execute_returning_one(
                    f"""
                    UPDATE {SCHEMA}.invoice_posting_requests
                       SET status = 'posted',
                           block_reason = NULL,
                           block_description = NULL,
                           completion_source = 'auto',
                           sf1_recno = %s,
                           erp_entry_date = %s,
                           reconciled_at = NOW(),
                           updated_at = NOW()
                     WHERE id = %s::uuid
                       AND status = ANY(%s)
                 RETURNING {_REQUEST_COLUMNS}
                    """,
                    (
                        item.get("sf1_recno"),
                        item.get("erp_entry_date"),
                        request_id,
                        list(sorted(RECONCILIATION_ELIGIBLE_STATUSES)),
                    ),
                    auto_commit=False,
                )
                if row is None:
                    continue
                self._insert_history(
                    {
                        "request_id": request_id,
                        "event_type": "reconciled",
                        "actor_origin": "system",
                        "actor_user_id": None,
                        "actor_name": None,
                        "from_status": from_status,
                        "to_status": "posted",
                        "changes": {
                            "completion_source": "auto",
                            "sf1_recno": item.get("sf1_recno"),
                            "erp_entry_date": (
                                item["erp_entry_date"].isoformat()
                                if hasattr(item.get("erp_entry_date"), "isoformat")
                                else item.get("erp_entry_date")
                            ),
                        },
                        "justification": None,
                    },
                    auto_commit=False,
                )
                posted += 1
            self.commit()
            return posted
        except Exception:
            self.rollback()
            raise

    def try_acquire_reconciliation_lock(self) -> bool:
        if self._reconciliation_lock_conn is not None:
            return False
        settings = get_plugins_connection_settings()
        conn = psycopg.connect(
            conninfo=settings.dsn,
            row_factory=dict_row,
            autocommit=True,
        )
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT pg_try_advisory_lock(%s, %s) AS acquired
                    """,
                    (RECONCILIATION_LOCK_CLASS_ID, RECONCILIATION_LOCK_OBJECT_ID),
                )
                row = cursor.fetchone()
            acquired = bool(row and row.get("acquired"))
            if not acquired:
                conn.close()
                return False
            self._reconciliation_lock_conn = conn
            return True
        except Exception:
            try:
                conn.close()
            except Exception:
                pass
            raise

    def release_reconciliation_lock(self) -> None:
        conn = self._reconciliation_lock_conn
        if conn is None:
            return
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT pg_advisory_unlock(%s, %s) AS released
                    """,
                    (RECONCILIATION_LOCK_CLASS_ID, RECONCILIATION_LOCK_OBJECT_ID),
                )
                cursor.fetchone()
        finally:
            try:
                if not conn.closed:
                    conn.close()
            finally:
                self._reconciliation_lock_conn = None

    def is_reconciliation_refresh_cooldown_active(
        self,
        cooldown_seconds: int,
    ) -> bool:
        seconds = max(0, int(cooldown_seconds))
        if seconds <= 0:
            return False
        row = self.fetch_one(
            f"""
            SELECT last_started_at
              FROM {SCHEMA}.reconciliation_refresh_control
             WHERE singleton = 1
            """
        )
        if not row or row.get("last_started_at") is None:
            return False
        last_started = row["last_started_at"]
        if isinstance(last_started, str):
            text = last_started.replace("Z", "+00:00")
            last_started = datetime.fromisoformat(text)
        if last_started.tzinfo is None:
            last_started = last_started.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        elapsed = (now - last_started.astimezone(timezone.utc)).total_seconds()
        return elapsed < seconds

    def mark_reconciliation_refresh_started(self) -> None:
        self.execute(
            f"""
            INSERT INTO {SCHEMA}.reconciliation_refresh_control (
                singleton, last_started_at, updated_at
            ) VALUES (1, NOW(), NOW())
            ON CONFLICT (singleton) DO UPDATE
               SET last_started_at = NOW(),
                   updated_at = NOW()
            """
        )

    def update_request_with_history(
        self,
        *,
        request_id: str,
        updates: dict[str, Any],
        history_fields: dict[str, Any],
    ) -> dict[str, Any]:
        if not updates:
            current = self.get_request(request_id)
            if current is None:
                raise LookupError(request_id)
            return current

        assignments = []
        params: list[Any] = []
        for key, value in updates.items():
            assignments.append(f"{key} = %s")
            params.append(value)
        assignments.append("updated_at = NOW()")
        params.append(request_id)

        try:
            row = self.execute_returning_one(
                f"""
                UPDATE {SCHEMA}.invoice_posting_requests
                   SET {", ".join(assignments)}
                 WHERE id = %s::uuid
             RETURNING {_REQUEST_COLUMNS}
                """,
                tuple(params),
                auto_commit=False,
            )
            if row is None:
                self.rollback()
                raise LookupError(request_id)
            history_fields = {**history_fields, "request_id": row["id"]}
            self._insert_history(history_fields, auto_commit=False)
            self.commit()
            return _serialize_request(row)
        except PluginsRepositoryError as exc:
            if _is_unique_violation(exc):
                raise DuplicateFiscalKeyError() from exc
            raise
        except UniqueViolation as exc:
            self.rollback()
            raise DuplicateFiscalKeyError() from exc
        except Exception:
            self.rollback()
            raise

    def add_comment(
        self,
        *,
        request_id: str,
        author_user_id: str,
        author_name: str,
        body: str,
    ) -> dict[str, Any]:
        try:
            row = self.execute_returning_one(
                f"""
                INSERT INTO {SCHEMA}.invoice_posting_comments (
                    request_id, author_user_id, author_name, body
                ) VALUES (%s::uuid, %s, %s, %s)
                RETURNING id, request_id, author_user_id, author_name, body, created_at
                """,
                (request_id, author_user_id, author_name, body),
                auto_commit=False,
            )
            assert row is not None
            self._insert_history(
                {
                    "request_id": request_id,
                    "event_type": "comment_added",
                    "actor_origin": "user",
                    "actor_user_id": author_user_id,
                    "actor_name": author_name,
                    "from_status": None,
                    "to_status": None,
                    "changes": {"comment_id": str(row["id"])},
                    "justification": None,
                },
                auto_commit=False,
            )
            self.commit()
            return _serialize_comment(row)
        except ForeignKeyViolation as exc:
            self.rollback()
            raise LookupError(request_id) from exc
        except Exception:
            self.rollback()
            raise

    def _insert_history(
        self,
        fields: dict[str, Any],
        *,
        auto_commit: bool,
    ) -> None:
        changes = history_changes_json_safe(fields.get("changes") or {})
        self.execute(
            f"""
            INSERT INTO {SCHEMA}.invoice_posting_history (
                request_id, event_type, actor_origin, actor_user_id, actor_name,
                from_status, to_status, changes, justification
            ) VALUES (
                %s::uuid, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """,
            (
                fields["request_id"],
                fields["event_type"],
                fields["actor_origin"],
                fields.get("actor_user_id"),
                fields.get("actor_name"),
                fields.get("from_status"),
                fields.get("to_status"),
                Jsonb(changes),
                fields.get("justification"),
            ),
            auto_commit=auto_commit,
        )


def _serialize_request(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    for key in ("id",):
        if isinstance(out.get(key), UUID):
            out[key] = str(out[key])
    for key in (
        "issue_date",
        "erp_entry_date",
        "received_at",
        "cancelled_at",
        "reconciled_at",
        "divergence_detected_at",
        "created_at",
        "updated_at",
    ):
        out[key] = _iso(out.get(key))
    if isinstance(out.get("amount"), Decimal):
        out["amount"] = float(out["amount"])
    return out


def _serialize_history(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    if isinstance(out.get("id"), UUID):
        out["id"] = str(out["id"])
    if isinstance(out.get("request_id"), UUID):
        out["request_id"] = str(out["request_id"])
    changes = out.get("changes")
    if isinstance(changes, str):
        out["changes"] = json.loads(changes)
    out["created_at"] = _iso(out.get("created_at"))
    return out


def _serialize_comment(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    for key in ("id", "request_id"):
        if isinstance(out.get(key), UUID):
            out[key] = str(out[key])
    out["created_at"] = _iso(out.get("created_at"))
    return out


def _iso(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value
