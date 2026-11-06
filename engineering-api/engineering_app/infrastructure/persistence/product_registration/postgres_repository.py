"""Adapter Postgres do Product Registration — principal dedicado.

Conecta APENAS via ``ENG_PRC_DB_*`` (DSN própria do bounded context).
Schema ``engineering`` no plugins_hub; tabelas
``product_registration_*`` criadas por migrations do runner oficial
(api-delpi/migrations/plugins/engineering V012+).

CAS via ``row_version`` + ``SELECT ... FOR UPDATE``; ledger append-only;
conclusão atômica (verification + revision + record pointer + request +
evento em uma única transação).
"""

from __future__ import annotations

import json
import logging
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator

from engineering_app.domain.product_registration.errors import (
    PrcConcurrencyError,
    PrcDuplicateError,
    PrcNotFoundError,
    PrcRepositoryError,
    PrcStaleRevisionError,
    PrcStateConflictError,
)

logger = logging.getLogger(__name__)

_SCHEMA = "engineering"
_T_REQ = f"{_SCHEMA}.product_registration_requests"
_T_DRAFT = f"{_SCHEMA}.product_registration_drafts"
_T_REC = f"{_SCHEMA}.product_registration_records"
_T_REV = f"{_SCHEMA}.product_registration_revisions"
_T_EVT = f"{_SCHEMA}.product_registration_events"
_T_VER = f"{_SCHEMA}.product_registration_verifications"
_T_IDEM = f"{_SCHEMA}.product_registration_idempotency"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


def _iso(value: Any) -> Any:
    return value.isoformat() if hasattr(value, "isoformat") else value


def _request_row(row: dict) -> dict[str, Any]:
    out = dict(row)
    for key in ("created_at", "updated_at", "completed_at", "rejected_at"):
        out[key] = _iso(out.get(key))
    return out


class PostgresProductRegistrationRepository:
    """Implementa ``ProductRegistrationRepository`` sobre psycopg3."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    @contextmanager
    def _conn(self) -> Iterator[Any]:
        import psycopg
        from psycopg.rows import dict_row

        try:
            conn = psycopg.connect(
                self._dsn, row_factory=dict_row, autocommit=False
            )
        except Exception as exc:
            raise PrcRepositoryError(
                f"postgres connect failed: {exc}"
            ) from exc
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # --- idempotência --------------------------------------------------------

    def find_idempotent(
        self, *, actor_or_source: str, operation: str, idempotency_key: str
    ) -> dict[str, Any] | None:
        with self._conn() as conn:
            row = conn.execute(
                f"SELECT * FROM {_T_IDEM}"
                " WHERE actor_or_source=%s AND operation=%s"
                " AND idempotency_key=%s AND expires_at > now()",
                (actor_or_source, operation, idempotency_key),
            ).fetchone()
            return dict(row) if row else None

    def save_idempotent(
        self,
        *,
        actor_or_source: str,
        operation: str,
        idempotency_key: str,
        request_fingerprint: str,
        request_id: str | None,
        response_status: int,
        response_payload: dict[str, Any],
    ) -> None:
        with self._conn() as conn:
            conn.execute(
                f"INSERT INTO {_T_IDEM}"
                " (id, actor_or_source, operation, idempotency_key,"
                "  request_fingerprint, request_id, response_status,"
                "  response_payload, created_at, expires_at)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s, now() + interval '7 days')"
                " ON CONFLICT (actor_or_source, operation, idempotency_key)"
                " DO NOTHING",
                (
                    _uuid(), actor_or_source, operation, idempotency_key,
                    request_fingerprint, request_id, response_status,
                    json.dumps(response_payload), _now(),
                ),
            )

    # --- requests + drafts ------------------------------------------------------

    def create_request(
        self, *, request: dict, draft: dict, event: dict
    ) -> dict[str, Any]:
        try:
            with self._conn() as conn:
                conn.execute(
                    f"INSERT INTO {_T_REQ}"
                    " (id, request_type, product_type, source,"
                    "  external_request_id, external_item_id,"
                    "  requester_subject, requester_display_name,"
                    "  official_product_code, base_revision_number,"
                    "  requested_payload, payload_schema_version, status,"
                    "  assigned_to_subject, row_version,"
                    "  created_at, updated_at)"
                    " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (
                        request["id"], request["request_type"],
                        request["product_type"], request["source"],
                        request["external_request_id"],
                        request["external_item_id"],
                        request["requester_subject"],
                        request["requester_display_name"],
                        request["official_product_code"],
                        request["base_revision_number"],
                        json.dumps(request["requested_payload"]),
                        request["payload_schema_version"],
                        request["status"],
                        request["assigned_to_subject"],
                        request["row_version"],
                        request["created_at"], request["updated_at"],
                    ),
                )
                conn.execute(
                    f"INSERT INTO {_T_DRAFT}"
                    " (request_id, schema_version, technical_data,"
                    "  changed_paths, row_version, updated_by_subject,"
                    "  updated_at)"
                    " VALUES (%s,%s,%s,%s,%s,%s,%s)",
                    (
                        request["id"], draft["schema_version"],
                        json.dumps(draft["technical_data"]),
                        json.dumps(draft["changed_paths"]),
                        draft["row_version"], draft["updated_by_subject"],
                        draft["updated_at"],
                    ),
                )
                conn.execute(
                    f"INSERT INTO {_T_EVT}"
                    " (id, request_id, sequence_number, event_type,"
                    "  actor_subject, occurred_at, reason, metadata,"
                    "  previous_status, next_status)"
                    " VALUES (%s,%s,1,%s,%s,%s,%s,%s,%s,%s)",
                    (
                        _uuid(), request["id"], event["event_type"],
                        event["actor_subject"], _now(), event["reason"],
                        json.dumps(event["metadata"]),
                        event["previous_status"], event["next_status"],
                    ),
                )
        except Exception as exc:
            if "uq_prc_requests_external" in str(exc) or (
                "unique" in str(exc).lower()
            ):
                raise PrcDuplicateError(
                    "duplicate_external_reference"
                ) from exc
            raise
        return self.get_request(request["id"])

    def get_request(self, request_id: str) -> dict[str, Any] | None:
        with self._conn() as conn:
            row = conn.execute(
                f"SELECT * FROM {_T_REQ} WHERE id=%s", (request_id,)
            ).fetchone()
            if row is None:
                return None
            draft = conn.execute(
                f"SELECT * FROM {_T_DRAFT} WHERE request_id=%s",
                (request_id,),
            ).fetchone()
        out = _request_row(row)
        if draft:
            out["draft"] = {
                "request_id": str(draft["request_id"]),
                "schema_version": draft["schema_version"],
                "technical_data": draft["technical_data"],
                "changed_paths": draft["changed_paths"],
                "row_version": draft["row_version"],
                "updated_by_subject": draft["updated_by_subject"],
                "updated_at": _iso(draft["updated_at"]),
            }
        out["id"] = str(out["id"])
        if out.get("completed_record_id"):
            out["completed_record_id"] = str(out["completed_record_id"])
        return out

    def get_request_by_external_ref(
        self, *, source: str, external_request_id: str, external_item_id: str | None
    ) -> dict[str, Any] | None:
        with self._conn() as conn:
            row = conn.execute(
                f"SELECT id FROM {_T_REQ} WHERE source=%s"
                " AND external_request_id=%s"
                " AND external_item_id IS NOT DISTINCT FROM %s",
                (source, external_request_id, external_item_id),
            ).fetchone()
        return self.get_request(str(row["id"])) if row else None

    def list_requests(
        self,
        *,
        status=None, request_type=None, assignee=None, source=None,
        search=None, date_from=None, date_to=None,
        requester_subject=None, global_scope=False,
        page=1, page_size=25,
    ) -> dict[str, Any]:
        where = ["1=1"]
        params: list[Any] = []
        if not global_scope:
            where.append(
                "(requester_subject=%s OR assigned_to_subject=%s)"
            )
            params += [requester_subject, requester_subject]
        for clause, value in (
            ("status=%s", status),
            ("request_type=%s", request_type),
            ("assigned_to_subject=%s", assignee),
            ("source=%s", source),
            ("created_at>=%s", date_from),
            ("created_at<=%s", date_to),
        ):
            if value:
                where.append(clause)
                params.append(value)
        if search:
            where.append(
                "(official_product_code ILIKE %s OR id::text ILIKE %s"
                " OR requested_payload->>'description' ILIKE %s)"
            )
            like = f"%{search}%"
            params += [like, like, like]
        sql_where = " AND ".join(where)
        with self._conn() as conn:
            total = conn.execute(
                f"SELECT count(*) AS c FROM {_T_REQ} WHERE {sql_where}",
                params,
            ).fetchone()["c"]
            rows = conn.execute(
                f"SELECT id, request_type, status, source,"
                " requester_subject, requester_display_name,"
                " assigned_to_subject, official_product_code,"
                " row_version, created_at"
                f" FROM {_T_REQ} WHERE {sql_where}"
                " ORDER BY created_at DESC, id DESC"
                " LIMIT %s OFFSET %s",
                params + [page_size, (page - 1) * page_size],
            ).fetchall()
        return {
            "items": [
                {
                    "id": str(r["id"]),
                    "requestType": r["request_type"],
                    "status": r["status"],
                    "requester": {
                        "subject": r["requester_subject"],
                        "displayName": r["requester_display_name"],
                    },
                    "source": r["source"],
                    "createdAt": _iso(r["created_at"]),
                    "assignedTo": r["assigned_to_subject"],
                    "officialCode": r["official_product_code"],
                    "caseVersion": r["row_version"],
                }
                for r in rows
            ],
            "page": page,
            "pageSize": page_size,
            "total": int(total),
        }

    def list_events(
        self, request_id: str, page: int = 1, page_size: int = 50
    ) -> dict[str, Any]:
        with self._conn() as conn:
            exists = conn.execute(
                f"SELECT 1 FROM {_T_REQ} WHERE id=%s", (request_id,)
            ).fetchone()
            if not exists:
                raise PrcNotFoundError("request", request_id)
            total = conn.execute(
                f"SELECT count(*) AS c FROM {_T_EVT} WHERE request_id=%s",
                (request_id,),
            ).fetchone()["c"]
            rows = conn.execute(
                f"SELECT * FROM {_T_EVT} WHERE request_id=%s"
                " ORDER BY sequence_number LIMIT %s OFFSET %s",
                (request_id, page_size, (page - 1) * page_size),
            ).fetchall()
        for r in rows:
            r["id"] = str(r["id"])
            r["request_id"] = str(r["request_id"])
            r["occurred_at"] = _iso(r["occurred_at"])
        return {
            "items": rows,
            "page": page,
            "pageSize": page_size,
            "total": int(total),
        }

    def _lock_and_check(
        self, conn, request_id: str, expected_version: int,
        allowed_from: frozenset[str],
    ) -> dict:
        row = conn.execute(
            f"SELECT * FROM {_T_REQ} WHERE id=%s FOR UPDATE",
            (request_id,),
        ).fetchone()
        if row is None:
            raise PrcNotFoundError("request", request_id)
        if int(row["row_version"]) != int(expected_version):
            raise PrcConcurrencyError("stale_version")
        if row["status"] not in allowed_from:
            raise PrcStateConflictError("state_conflict")
        return row

    def _next_event_seq(self, conn, request_id: str) -> int:
        row = conn.execute(
            f"SELECT COALESCE(MAX(sequence_number),0)+1 AS s"
            f" FROM {_T_EVT} WHERE request_id=%s",
            (request_id,),
        ).fetchone()
        return int(row["s"])

    def _insert_event(self, conn, request_id, seq, event) -> None:
        conn.execute(
            f"INSERT INTO {_T_EVT}"
            " (id, request_id, sequence_number, event_type,"
            "  actor_subject, occurred_at, reason, metadata,"
            "  previous_status, next_status)"
            " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                _uuid(), request_id, seq, event["event_type"],
                event["actor_subject"], _now(), event.get("reason"),
                json.dumps(event.get("metadata") or {}),
                event.get("previous_status"), event.get("next_status"),
            ),
        )

    def apply_transition(
        self,
        *,
        request_id: str,
        expected_version: int,
        allowed_from: frozenset[str],
        actor_label: str,
        actor_subject: str,
        event_type: str,
        next_status: str,
        set_fields: dict[str, Any],
        reason: str | None,
        event_meta: dict[str, Any],
    ) -> dict[str, Any]:
        with self._conn() as conn:
            row = self._lock_and_check(
                conn, request_id, expected_version, allowed_from
            )
            sets = ["status=%s", "row_version=row_version+1",
                    "updated_at=%s"]
            params: list[Any] = [next_status, _now()]
            for key, value in set_fields.items():
                sets.append(f"{key}=%s")
                params.append(value)
            if next_status == "completed":
                sets.append("completed_at=%s")
                params.append(_now())
            if next_status == "rejected":
                sets.append("rejected_at=%s")
                params.append(_now())
            params.append(request_id)
            conn.execute(
                f"UPDATE {_T_REQ} SET {', '.join(sets)} WHERE id=%s",
                params,
            )
            self._insert_event(
                conn, request_id, self._next_event_seq(conn, request_id),
                {
                    "event_type": event_type,
                    "actor_subject": actor_subject,
                    "reason": reason,
                    "metadata": event_meta,
                    "previous_status": row["status"],
                    "next_status": next_status,
                },
            )
        return self.get_request(request_id)

    def update_draft(
        self,
        *,
        request_id: str,
        expected_version: int,
        actor_subject: str,
        changes: list[dict[str, Any]],
        event_meta: dict[str, Any],
    ) -> dict[str, Any]:
        with self._conn() as conn:
            row = self._lock_and_check(
                conn, request_id, expected_version,
                frozenset({"in_progress"}),
            )
            draft = conn.execute(
                f"SELECT * FROM {_T_DRAFT} WHERE request_id=%s FOR UPDATE",
                (request_id,),
            ).fetchone()
            data = dict(draft["technical_data"] or {})
            changed = {
                c["path"]: c for c in (draft["changed_paths"] or [])
            }
            applied = []
            for change in changes:
                path = change["path"]
                applied.append({
                    "path": path, "before": data.get(path),
                    "after": change["proposedValue"],
                    "reason": change["reason"],
                })
                data[path] = change["proposedValue"]
                changed[path] = {
                    "path": path, "reason": change["reason"],
                }
            conn.execute(
                f"UPDATE {_T_DRAFT} SET technical_data=%s,"
                " changed_paths=%s, row_version=row_version+1,"
                " updated_by_subject=%s, updated_at=%s"
                " WHERE request_id=%s",
                (
                    json.dumps(data), json.dumps(list(changed.values())),
                    actor_subject, _now(), request_id,
                ),
            )
            conn.execute(
                f"UPDATE {_T_REQ} SET row_version=row_version+1,"
                " updated_at=%s WHERE id=%s",
                (_now(), request_id),
            )
            self._insert_event(
                conn, request_id, self._next_event_seq(conn, request_id),
                {
                    "event_type": "draft_changed",
                    "actor_subject": actor_subject,
                    "reason": None,
                    "metadata": {"changes": applied, **event_meta},
                    "previous_status": row["status"],
                    "next_status": row["status"],
                },
            )
        return self.get_request(request_id)

    # --- verificações -------------------------------------------------------------

    def insert_verification(
        self, *, request_id: str, verification: dict[str, Any]
    ) -> dict[str, Any]:
        with self._conn() as conn:
            row = conn.execute(
                f"INSERT INTO {_T_VER}"
                " (id, request_id, official_product_code,"
                "  requested_by_subject, checked_at, official_source,"
                "  result, expected_fields, observed_fields,"
                "  field_results, evidence_fingerprint, correlation_id,"
                "  error_code)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                " RETURNING *",
                (
                    _uuid(), request_id,
                    verification["official_product_code"],
                    verification["requested_by_subject"],
                    verification["checked_at"],
                    verification["official_source"],
                    verification["result"],
                    json.dumps(verification["expected_fields"]),
                    json.dumps(verification.get("observed_fields")),
                    json.dumps(verification["field_results"]),
                    verification["evidence_fingerprint"],
                    verification["correlation_id"],
                    verification.get("error_code"),
                ),
            ).fetchone()
        row["id"] = str(row["id"])
        row["request_id"] = str(row["request_id"])
        row["checked_at"] = _iso(row["checked_at"])
        return row

    def list_verifications(self, request_id: str) -> list[dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                f"SELECT * FROM {_T_VER} WHERE request_id=%s"
                " ORDER BY checked_at",
                (request_id,),
            ).fetchall()
        for r in rows:
            r["id"] = str(r["id"])
            r["request_id"] = str(r["request_id"])
            r["checked_at"] = _iso(r["checked_at"])
        return rows

    # --- records + revisions -------------------------------------------------------

    def get_record(self, record_id: str) -> dict[str, Any] | None:
        with self._conn() as conn:
            row = conn.execute(
                f"SELECT * FROM {_T_REC} WHERE id=%s", (record_id,)
            ).fetchone()
        if not row:
            return None
        row["id"] = str(row["id"])
        for k in ("created_at", "updated_at", "last_official_verified_at"):
            row[k] = _iso(row[k])
        return row

    def get_record_by_official_code(
        self, *, official_source: str, official_code: str
    ) -> dict[str, Any] | None:
        with self._conn() as conn:
            row = conn.execute(
                f"SELECT id FROM {_T_REC} WHERE official_source=%s"
                " AND official_product_code=%s",
                (official_source, official_code),
            ).fetchone()
        return self.get_record(str(row["id"])) if row else None

    def list_revisions(self, record_id: str) -> list[dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                f"SELECT * FROM {_T_REV} WHERE record_id=%s"
                " ORDER BY revision_number",
                (record_id,),
            ).fetchall()
        for r in rows:
            for k in ("id", "record_id", "request_id", "official_evidence_id"):
                r[k] = str(r[k])
            r["approved_at"] = _iso(r["approved_at"])
            r["created_at"] = _iso(r["created_at"])
        return rows

    def get_revision(
        self, record_id: str, revision_number: int
    ) -> dict[str, Any] | None:
        with self._conn() as conn:
            row = conn.execute(
                f"SELECT * FROM {_T_REV} WHERE record_id=%s"
                " AND revision_number=%s",
                (record_id, revision_number),
            ).fetchone()
        if not row:
            return None
        for k in ("id", "record_id", "request_id", "official_evidence_id"):
            row[k] = str(row[k])
        row["approved_at"] = _iso(row["approved_at"])
        row["created_at"] = _iso(row["created_at"])
        return row

    def complete_request(
        self,
        *,
        request_id: str,
        expected_version: int,
        actor_subject: str,
        official_code: str,
        official_source: str,
        base_revision: int | None,
        revision_snapshot: dict[str, Any],
        revision_changes: list[dict[str, Any]],
        verification: dict[str, Any],
        reason: str | None,
        event_meta: dict[str, Any],
    ) -> dict[str, Any]:
        with self._conn() as conn:
            req = self._lock_and_check(
                conn, request_id, expected_version,
                frozenset({"under_review"}),
            )
            rec = conn.execute(
                f"SELECT * FROM {_T_REC} WHERE official_source=%s"
                " AND official_product_code=%s FOR UPDATE",
                (official_source, official_code),
            ).fetchone()
            if rec is None:
                if base_revision not in (None, 0):
                    raise PrcStaleRevisionError("stale_revision")
                rec = conn.execute(
                    f"INSERT INTO {_T_REC}"
                    " (id, product_type, official_product_code,"
                    "  current_revision_number,"
                    "  last_official_verified_at, official_source,"
                    "  created_at, updated_at)"
                    " VALUES (%s,%s,%s,0,%s,%s,%s,%s) RETURNING *",
                    (
                        _uuid(), req["product_type"], official_code,
                        _now(), official_source, _now(), _now(),
                    ),
                ).fetchone()
            if base_revision is not None and base_revision != int(
                rec["current_revision_number"]
            ):
                raise PrcStaleRevisionError("stale_revision")
            rev_number = int(rec["current_revision_number"]) + 1
            ver_row = conn.execute(
                f"INSERT INTO {_T_VER}"
                " (id, request_id, official_product_code,"
                "  requested_by_subject, checked_at, official_source,"
                "  result, expected_fields, observed_fields,"
                "  field_results, evidence_fingerprint, correlation_id,"
                "  error_code)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                " RETURNING *",
                (
                    _uuid(), request_id,
                    verification["official_product_code"],
                    verification["requested_by_subject"],
                    verification["checked_at"],
                    verification["official_source"],
                    verification["result"],
                    json.dumps(verification["expected_fields"]),
                    json.dumps(verification.get("observed_fields")),
                    json.dumps(verification["field_results"]),
                    verification["evidence_fingerprint"],
                    verification["correlation_id"],
                    verification.get("error_code"),
                ),
            ).fetchone()
            rev = conn.execute(
                f"INSERT INTO {_T_REV}"
                " (id, record_id, revision_number, request_id,"
                "  schema_version, technical_snapshot, changes,"
                "  official_evidence_id, approved_by_subject,"
                "  approved_at, created_at)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                " RETURNING *",
                (
                    _uuid(), rec["id"], rev_number, request_id, 1,
                    json.dumps(revision_snapshot),
                    json.dumps(revision_changes),
                    ver_row["id"], actor_subject, _now(), _now(),
                ),
            ).fetchone()
            conn.execute(
                f"UPDATE {_T_REC} SET current_revision_number=%s,"
                " last_official_verified_at=%s, updated_at=%s"
                " WHERE id=%s",
                (rev_number, _now(), _now(), rec["id"]),
            )
            conn.execute(
                f"UPDATE {_T_REQ} SET status='completed',"
                " row_version=row_version+1, completed_at=%s,"
                " updated_at=%s, completed_record_id=%s,"
                " official_product_code=%s WHERE id=%s",
                (_now(), _now(), rec["id"], official_code, request_id),
            )
            self._insert_event(
                conn, request_id, self._next_event_seq(conn, request_id),
                {
                    "event_type": "verify_and_complete",
                    "actor_subject": actor_subject,
                    "reason": reason,
                    "metadata": {
                        "official_code": official_code,
                        "record_id": str(rec["id"]),
                        "revision_number": rev_number,
                        "verification_id": str(ver_row["id"]),
                        **event_meta,
                    },
                    "previous_status": req["status"],
                    "next_status": "completed",
                },
            )
        ver_row["id"] = str(ver_row["id"])
        ver_row["request_id"] = str(ver_row["request_id"])
        ver_row["checked_at"] = _iso(ver_row["checked_at"])
        for k in ("id", "record_id", "request_id", "official_evidence_id"):
            rev[k] = str(rev[k])
        rev["approved_at"] = _iso(rev["approved_at"])
        rev["created_at"] = _iso(rev["created_at"])
        rec["id"] = str(rec["id"])
        for k in ("created_at", "updated_at", "last_official_verified_at"):
            rec[k] = _iso(rec[k])
        rec["current_revision_number"] = rev_number
        return {
            "request": self.get_request(request_id),
            "record": rec,
            "revision": rev,
            "verification": ver_row,
        }
