"""Postgres repository for Comex analysis (PROC-0076.COMEX.S2/S3).

Owns transactions: a status transition and its audit event commit
together; optimistic concurrency is enforced by updating the governance
row guarded on the expected revision.
"""

from __future__ import annotations

import json
from typing import Any

from psycopg.errors import IntegrityError

from app.infrastructure.persistence.migrations_runner import get_connection


class GovernanceRevisionConflictError(RuntimeError):
    pass


class ComexAnalysisRepository:
    # -- governance -----------------------------------------------------

    def create_governance(
        self, *, record: dict[str, Any]
    ) -> dict[str, Any]:
        """Create or resume the single governance row for an NCM.

        If a row for ``ncm_code`` already exists it is returned with the
        ``existing`` flag — the service decides whether to resubmit or
        reject as conflict.
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT * FROM supplies.comex_ncm_governance
                    WHERE ncm_code = %s
                    """,
                    (record["ncm_code"],),
                )
                existing = cur.fetchone()
                if existing is not None:
                    return _governance_dto(existing) | {"_existing": True}

                try:
                    cur.execute(
                        """
                        INSERT INTO supplies.comex_ncm_governance (
                            ncm_code, ncm_version, description, family_code,
                            product_codes, status, notes, requested_by
                        ) VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s, %s)
                        RETURNING *
                        """,
                        (
                            record["ncm_code"],
                            record.get("ncm_version"),
                            record.get("description"),
                            record.get("family_code"),
                            json.dumps(record.get("product_codes") or []),
                            record["status"],
                            record.get("notes"),
                            record["requested_by"],
                        ),
                    )
                except IntegrityError:
                    # Concurrent insert won the race — the shared catalog
                    # is single-row per NCM, so return the winner's record.
                    conn.rollback()
                    cur.execute(
                        """
                        SELECT * FROM supplies.comex_ncm_governance
                        WHERE ncm_code = %s
                        """,
                        (record["ncm_code"],),
                    )
                    existing = cur.fetchone()
                    if existing is not None:
                        return _governance_dto(existing) | {
                            "_existing": True
                        }
                    raise
                row = cur.fetchone()
                self._insert_event(
                    cur,
                    governance_id=row["governance_id"],
                    actor=record["requested_by"],
                    event_type="requested",
                    to_status=record["status"],
                    notes=record.get("notes"),
                )
            conn.commit()
        return _governance_dto(row)

    def get_governance(self, governance_id: str) -> dict[str, Any] | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT * FROM supplies.comex_ncm_governance
                    WHERE governance_id = %s
                    """,
                    (governance_id,),
                )
                row = cur.fetchone()
        return _governance_dto(row) if row else None

    def get_governance_by_ncm(self, ncm_code: str) -> dict[str, Any] | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT * FROM supplies.comex_ncm_governance
                    WHERE ncm_code = %s
                    """,
                    (ncm_code,),
                )
                row = cur.fetchone()
        return _governance_dto(row) if row else None

    def list_governance(
        self, *, status: str | None = None, limit: int = 200
    ) -> list[dict[str, Any]]:
        sql = "SELECT * FROM supplies.comex_ncm_governance"
        params: list[Any] = []
        if status:
            sql += " WHERE status = %s"
            params.append(status)
        sql += " ORDER BY updated_at DESC LIMIT %s"
        params.append(limit)
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return [_governance_dto(r) for r in cur.fetchall()]

    def transition_governance(
        self,
        *,
        governance_id: str,
        expected_revision: int,
        to_status: str,
        actor: str,
        notes: str | None,
        event_type: str,
        extra_columns: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Optimistic-concurrency transition + audit event, one commit."""
        decided = {"approved", "rejected"}
        deactivated = {"inactive"}
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE supplies.comex_ncm_governance
                    SET status = %s,
                        revision = revision + 1,
                        updated_at = NOW(),
                        notes = COALESCE(%s, notes),
                        decided_by = CASE WHEN %s THEN %s ELSE decided_by END,
                        decided_at = CASE WHEN %s THEN NOW() ELSE decided_at END,
                        decision_notes = CASE WHEN %s THEN %s ELSE decision_notes END,
                        deactivated_by = CASE WHEN %s THEN %s ELSE deactivated_by END,
                        deactivated_at = CASE WHEN %s THEN NOW() ELSE deactivated_at END
                    WHERE governance_id = %s AND revision = %s
                    RETURNING *
                    """,
                    (
                        to_status,
                        notes,
                        to_status in decided, actor,
                        to_status in decided,
                        to_status in decided, notes,
                        to_status in deactivated, actor,
                        to_status in deactivated,
                        governance_id,
                        expected_revision,
                    ),
                )
                row = cur.fetchone()
                if row is None:
                    conn.rollback()
                    raise GovernanceRevisionConflictError(
                        "governance record changed — reload and retry"
                    )
                self._insert_event(
                    cur,
                    governance_id=governance_id,
                    actor=actor,
                    event_type=event_type,
                    from_status=extra_columns.get("from_status") if extra_columns else None,
                    to_status=to_status,
                    notes=notes,
                    metadata=extra_columns.get("metadata") if extra_columns else None,
                )
            conn.commit()
        return _governance_dto(row)

    def record_sync_event(
        self,
        *,
        governance_id: str,
        actor: str | None,
        event_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                self._insert_event(
                    cur,
                    governance_id=governance_id,
                    actor=actor,
                    event_type=event_type,
                    metadata=metadata,
                )
            conn.commit()

    def list_governance_events(
        self, governance_id: str, *, limit: int = 100
    ) -> list[dict[str, Any]]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT * FROM supplies.comex_ncm_governance_events
                    WHERE governance_id = %s
                    ORDER BY created_at DESC, event_id DESC
                    LIMIT %s
                    """,
                    (governance_id, limit),
                )
                return [_event_dto(r) for r in cur.fetchall()]

    @staticmethod
    def _insert_event(
        cur,
        *,
        governance_id,
        actor,
        event_type: str,
        from_status: str | None = None,
        to_status: str | None = None,
        notes: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        cur.execute(
            """
            INSERT INTO supplies.comex_ncm_governance_events (
                governance_id, actor_subject, event_type,
                from_status, to_status, notes, metadata
            ) VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
            """,
            (
                governance_id,
                actor,
                event_type,
                from_status,
                to_status,
                notes,
                json.dumps(metadata) if metadata else None,
            ),
        )

    # -- saved views ------------------------------------------------------

    def create_view(self, *, record: dict[str, Any]) -> dict[str, Any]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO supplies.comex_market_views (
                        owner_user_id, unit_scope, name,
                        selected_product_codes, selected_materials,
                        approved_ncm_references, selected_metrics,
                        date_range, granularity, view_mode
                    ) VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb,
                              %s::jsonb, %s::jsonb, %s, %s)
                    RETURNING *
                    """,
                    (
                        record["owner_user_id"],
                        record.get("unit_scope"),
                        record["name"],
                        json.dumps(record.get("selected_product_codes") or []),
                        json.dumps(record.get("selected_materials") or []),
                        json.dumps(record.get("approved_ncm_references") or []),
                        json.dumps(record.get("selected_metrics") or []),
                        (
                            json.dumps(record["date_range"])
                            if record.get("date_range") is not None
                            else None
                        ),
                        record.get("granularity") or "month",
                        record.get("view_mode") or "chart",
                    ),
                )
                row = cur.fetchone()
            conn.commit()
        return _view_dto(row)

    def get_view(
        self, view_id: str, *, owner_user_id: str
    ) -> dict[str, Any] | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT * FROM supplies.comex_market_views
                    WHERE view_id = %s AND owner_user_id = %s
                    """,
                    (view_id, owner_user_id),
                )
                row = cur.fetchone()
        return _view_dto(row) if row else None

    def list_views(self, *, owner_user_id: str) -> list[dict[str, Any]]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT * FROM supplies.comex_market_views
                    WHERE owner_user_id = %s
                    ORDER BY updated_at DESC
                    """,
                    (owner_user_id,),
                )
                return [_view_dto(r) for r in cur.fetchall()]

    def update_view(
        self,
        view_id: str,
        *,
        owner_user_id: str,
        record: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Ownership-guarded update — None when the view is not theirs."""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE supplies.comex_market_views
                    SET name = %s,
                        unit_scope = %s,
                        selected_product_codes = %s::jsonb,
                        selected_materials = %s::jsonb,
                        approved_ncm_references = %s::jsonb,
                        selected_metrics = %s::jsonb,
                        date_range = %s::jsonb,
                        granularity = %s,
                        view_mode = %s,
                        updated_at = NOW()
                    WHERE view_id = %s AND owner_user_id = %s
                    RETURNING *
                    """,
                    (
                        record["name"],
                        record.get("unit_scope"),
                        json.dumps(record.get("selected_product_codes") or []),
                        json.dumps(record.get("selected_materials") or []),
                        json.dumps(record.get("approved_ncm_references") or []),
                        json.dumps(record.get("selected_metrics") or []),
                        (
                            json.dumps(record["date_range"])
                            if record.get("date_range") is not None
                            else None
                        ),
                        record.get("granularity") or "month",
                        record.get("view_mode") or "chart",
                        view_id,
                        owner_user_id,
                    ),
                )
                row = cur.fetchone()
            conn.commit()
        return _view_dto(row) if row else None

    def delete_view(self, view_id: str, *, owner_user_id: str) -> bool:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM supplies.comex_market_views
                    WHERE view_id = %s AND owner_user_id = %s
                    """,
                    (view_id, owner_user_id),
                )
                deleted = cur.rowcount > 0
            conn.commit()
        return deleted


def _json_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            return []
    return value if isinstance(value, list) else []


def _governance_dto(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "governance_id": str(row["governance_id"]),
        "ncm_code": row["ncm_code"],
        "ncm_version": row.get("ncm_version"),
        "description": row.get("description"),
        "family_code": row.get("family_code"),
        "product_codes": _json_list(row.get("product_codes")),
        "status": row["status"],
        "notes": row.get("notes"),
        "requested_by": str(row["requested_by"]),
        "requested_at": row["requested_at"].isoformat(),
        "decided_by": str(row["decided_by"]) if row.get("decided_by") else None,
        "decided_at": (
            row["decided_at"].isoformat() if row.get("decided_at") else None
        ),
        "decision_notes": row.get("decision_notes"),
        "deactivated_by": (
            str(row["deactivated_by"]) if row.get("deactivated_by") else None
        ),
        "deactivated_at": (
            row["deactivated_at"].isoformat()
            if row.get("deactivated_at")
            else None
        ),
        "revision": row["revision"],
        "created_at": row["created_at"].isoformat(),
        "updated_at": row["updated_at"].isoformat(),
    }


def _event_dto(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_id": str(row["event_id"]),
        "governance_id": str(row["governance_id"]),
        "actor_subject": (
            str(row["actor_subject"]) if row.get("actor_subject") else None
        ),
        "event_type": row["event_type"],
        "from_status": row.get("from_status"),
        "to_status": row.get("to_status"),
        "notes": row.get("notes"),
        "metadata": row.get("metadata"),
        "created_at": row["created_at"].isoformat(),
    }


def _view_dto(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "view_id": str(row["view_id"]),
        "owner_user_id": str(row["owner_user_id"]),
        "unit_scope": row.get("unit_scope"),
        "name": row["name"],
        "selected_product_codes": _json_list(row.get("selected_product_codes")),
        "selected_materials": _json_list(row.get("selected_materials")),
        "approved_ncm_references": _json_list(
            row.get("approved_ncm_references")
        ),
        "selected_metrics": _json_list(row.get("selected_metrics")),
        "date_range": row.get("date_range"),
        "granularity": row["granularity"],
        "view_mode": row["view_mode"],
        "created_at": row["created_at"].isoformat(),
        "updated_at": row["updated_at"].isoformat(),
    }
