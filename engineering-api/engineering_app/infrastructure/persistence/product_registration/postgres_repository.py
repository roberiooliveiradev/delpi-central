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
    PrcValidationError,
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
_T_FLAG = f"{_SCHEMA}.product_registration_flags"
_T_INFO_ROUND = f"{_SCHEMA}.product_registration_info_rounds"
_T_INFO_Q = f"{_SCHEMA}.product_registration_info_questions"
_T_INFO_A = f"{_SCHEMA}.product_registration_info_answers"
_T_CORR_RET = f"{_SCHEMA}.product_registration_correction_returns"
_T_CORR_TGT = f"{_SCHEMA}.product_registration_correction_targets"
_T_ATT = f"{_SCHEMA}.product_registration_attachments"

# Estados de rodada que bloqueiam a abertura de nova rodada / resume.
_INFO_OPEN_ROUND_STATUSES = ("awaiting_requester", "awaiting_review")
# Estados terminais de pergunta (não aguardam mais ação do analista).
_INFO_TERMINAL_QUESTION_STATUSES = frozenset(
    {"accepted", "follow_up_requested"}
)


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
                    "  created_at, updated_at, official_baseline)"
                    " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
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
                        (
                            json.dumps(request["official_baseline"])
                            if request.get("official_baseline") is not None
                            else None
                        ),
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

    _SORT_COLUMNS = {
        "createdAt": "created_at",
        "requestType": "request_type",
        "status": "status",
        "officialCode": "official_product_code",
        "requester": "requester_display_name",
        "assignedTo": "assigned_to_subject",
        "id": "id",
    }

    def list_requests(
        self,
        *,
        status=None, request_type=None, assignee=None, source=None,
        search=None, date_from=None, date_to=None,
        requester_subject=None, global_scope=False,
        page=1, page_size=25,
        sort_by=None, sort_dir=None,
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
        sort_col = self._SORT_COLUMNS.get(sort_by or "", "created_at")
        direction = "ASC" if sort_dir == "asc" else "DESC"
        with self._conn() as conn:
            total = conn.execute(
                f"SELECT count(*) AS c FROM {_T_REQ} WHERE {sql_where}",
                params,
            ).fetchone()["c"]
            status_counts = {
                r["status"]: int(r["c"])
                for r in conn.execute(
                    f"SELECT status, count(*) AS c FROM {_T_REQ}"
                    f" WHERE {sql_where} GROUP BY status",
                    params,
                ).fetchall()
            }
            rows = conn.execute(
                f"SELECT id, request_type, status, source,"
                " requester_subject, requester_display_name,"
                " assigned_to_subject, assigned_to_display_name,"
                " official_product_code, row_version, created_at"
                f" FROM {_T_REQ} WHERE {sql_where}"
                f" ORDER BY {sort_col} {direction}, id DESC"
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
                    "assignedToDisplayName": r.get(
                        "assigned_to_display_name"
                    ),
                    "officialCode": r["official_product_code"],
                    "caseVersion": r["row_version"],
                }
                for r in rows
            ],
            "page": page,
            "pageSize": page_size,
            "total": int(total),
            "statusCounts": status_counts,
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
            "  actor_subject, actor_display_name, actor_email,"
            "  occurred_at, reason, metadata,"
            "  previous_status, next_status)"
            " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                _uuid(), request_id, seq, event["event_type"],
                event["actor_subject"],
                event.get("actor_display_name"),
                event.get("actor_email"),
                _now(), event.get("reason"),
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
        actor_email: str | None = None,
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
                    "actor_display_name": actor_label,
                    "actor_email": actor_email,
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
        actor_display_name: str | None = None,
        actor_email: str | None = None,
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
                    "actor_display_name": actor_display_name,
                    "actor_email": actor_email,
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
        actor_display_name: str | None = None,
        actor_email: str | None = None,
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
            # PRC-REF-020: conclusão a partir de in_progress (legado under_review).
            req = self._lock_and_check(
                conn, request_id, expected_version,
                frozenset({"in_progress", "under_review"}),
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
                    "event_type": "completed",
                    "actor_subject": actor_subject,
                    "actor_display_name": actor_display_name,
                    "actor_email": actor_email,
                    "reason": reason,
                    "metadata": {
                        "official_code": official_code,
                        "record_id": str(rec["id"]),
                        "revision_number": rev_number,
                        "verification_id": str(ver_row["id"]),
                        "action": "complete",
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

    # --- attendance flags (D16) ------------------------------------------------

    def _flag_row(self, row: dict) -> dict[str, Any]:
        out = dict(row)
        out["id"] = str(out["id"])
        out["request_id"] = str(out["request_id"])
        sk = out.get("supplier_key")
        if isinstance(sk, str):
            try:
                out["supplier_key"] = json.loads(sk)
            except (TypeError, ValueError):
                out["supplier_key"] = None
        for key in (
            "created_at", "updated_at", "resolved_at", "deleted_at",
        ):
            out[key] = _iso(out.get(key))
        return out

    def create_flag(
        self, *, flag: dict[str, Any], event: dict[str, Any]
    ) -> dict[str, Any]:
        from psycopg.errors import UniqueViolation

        with self._conn() as conn:
            try:
                conn.execute(
                    f"INSERT INTO {_T_FLAG}"
                    " (id, request_id, title, description, status, subject,"
                    "  target_path, target_attribute, supplier_key,"
                    "  target_key, row_version,"
                    "  created_by_subject, created_by_display_name,"
                    "  created_at, updated_by_subject,"
                    "  updated_by_display_name, updated_at)"
                    " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,"
                    "         %s,%s,%s,%s,%s,%s)",
                    (
                        flag["id"], flag["request_id"], flag["title"],
                        flag["description"], flag["status"],
                        flag["subject"],
                        flag.get("target_path"),
                        flag.get("target_attribute"),
                        json.dumps(flag.get("supplier_key"))
                        if flag.get("supplier_key") is not None else None,
                        flag["target_key"],
                        flag["row_version"],
                        flag["created_by_subject"],
                        flag.get("created_by_display_name"),
                        flag["created_at"],
                        flag["updated_by_subject"],
                        flag.get("updated_by_display_name"),
                        flag["updated_at"],
                    ),
                )
            except UniqueViolation as exc:
                raise PrcStateConflictError("open_flag_exists") from exc
            seq = conn.execute(
                f"SELECT COALESCE(MAX(sequence_number),0)+1 AS n"
                f" FROM {_T_EVT} WHERE request_id=%s",
                (flag["request_id"],),
            ).fetchone()["n"]
            self._insert_event(conn, flag["request_id"], seq, event)
            row = conn.execute(
                f"SELECT * FROM {_T_FLAG} WHERE id=%s", (flag["id"],)
            ).fetchone()
        return self._flag_row(row)

    def get_flag(
        self, *, request_id: str, flag_id: str, include_deleted: bool = False
    ) -> dict[str, Any] | None:
        with self._conn() as conn:
            sql = f"SELECT * FROM {_T_FLAG} WHERE id=%s AND request_id=%s"
            params: list[Any] = [flag_id, request_id]
            if not include_deleted:
                sql += " AND deleted_at IS NULL"
            row = conn.execute(sql, params).fetchone()
        return self._flag_row(row) if row else None

    def find_open_flag_by_target(
        self, *, request_id: str, target_key: str
    ) -> dict[str, Any] | None:
        with self._conn() as conn:
            row = conn.execute(
                f"SELECT * FROM {_T_FLAG}"
                " WHERE request_id=%s AND target_key=%s"
                " AND status='OPEN' AND deleted_at IS NULL"
                " LIMIT 1",
                (request_id, target_key),
            ).fetchone()
        return self._flag_row(row) if row else None

    def list_flags(
        self,
        *,
        request_id: str,
        status: str | None = None,
        subject: str | None = None,
        target_path: str | None = None,
        target_attribute: str | None = None,
        supplier_code: str | None = None,
        store: str | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> dict[str, Any]:
        where = "request_id=%s AND deleted_at IS NULL"
        params: list[Any] = [request_id]
        if status:
            where += " AND status=%s"
            params.append(status)
        if subject:
            where += " AND subject=%s"
            params.append(subject)
        if target_path:
            where += " AND target_path=%s"
            params.append(target_path)
        if target_attribute:
            where += " AND target_attribute=%s"
            params.append(target_attribute)
        if supplier_code:
            where += " AND supplier_key->>'supplierCode'=%s"
            params.append(supplier_code)
        if store:
            where += " AND supplier_key->>'store'=%s"
            params.append(store)
        offset = (page - 1) * page_size
        with self._conn() as conn:
            total = conn.execute(
                f"SELECT COUNT(*) AS n FROM {_T_FLAG} WHERE {where}",
                params,
            ).fetchone()["n"]
            counts = conn.execute(
                f"SELECT status, COUNT(*) AS n FROM {_T_FLAG}"
                " WHERE request_id=%s AND deleted_at IS NULL"
                " GROUP BY status",
                (request_id,),
            ).fetchall()
            rows = conn.execute(
                f"SELECT * FROM {_T_FLAG} WHERE {where}"
                " ORDER BY created_at DESC, id DESC"
                " LIMIT %s OFFSET %s",
                [*params, page_size, offset],
            ).fetchall()
        by_status = {r["status"]: int(r["n"]) for r in counts}
        return {
            "items": [self._flag_row(r) for r in rows],
            "page": page,
            "pageSize": page_size,
            "total": int(total),
            "openCount": by_status.get("OPEN", 0),
            "resolvedCount": by_status.get("RESOLVED", 0),
            "hasMore": offset + page_size < int(total),
        }

    def list_flags_cross_case(
        self,
        *,
        accessible_request_ids: list[str] | None,
        global_scope: bool,
        status: str | None = None,
        subject: str | None = None,
        target_path: str | None = None,
        target_attribute: str | None = None,
        product_code: str | None = None,
        request_id: str | None = None,
        request_type: str | None = None,
        request_status: str | None = None,
        assignee: str | None = None,
        supplier_code: str | None = None,
        store: str | None = None,
        created_from: str | None = None,
        created_to: str | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> dict[str, Any]:
        """Lista transversal com AuthZ por caso (IDs acessíveis)."""
        if not global_scope and not accessible_request_ids:
            return {
                "items": [],
                "page": page,
                "pageSize": page_size,
                "total": 0,
                "openCount": 0,
                "resolvedCount": 0,
                "distinctRequestCount": 0,
                "distinctProductCount": 0,
                "hasMore": False,
            }
        where = f"f.deleted_at IS NULL"
        params: list[Any] = []
        if not global_scope:
            where += " AND f.request_id = ANY(%s::uuid[])"
            params.append(accessible_request_ids)
        if request_id:
            where += " AND f.request_id=%s"
            params.append(request_id)
        if status:
            where += " AND f.status=%s"
            params.append(status)
        if subject:
            where += " AND f.subject=%s"
            params.append(subject)
        if target_path:
            where += " AND f.target_path=%s"
            params.append(target_path)
        if target_attribute:
            where += " AND f.target_attribute=%s"
            params.append(target_attribute)
        if supplier_code:
            where += " AND f.supplier_key->>'supplierCode'=%s"
            params.append(supplier_code)
        if store:
            where += " AND f.supplier_key->>'store'=%s"
            params.append(store)
        if product_code:
            where += " AND r.official_product_code=%s"
            params.append(product_code)
        if request_type:
            where += " AND r.request_type=%s"
            params.append(request_type)
        if request_status:
            where += " AND r.status=%s"
            params.append(request_status)
        if assignee:
            where += " AND r.assigned_to_subject=%s"
            params.append(assignee)
        if created_from:
            where += " AND f.created_at >= %s::timestamptz"
            params.append(created_from)
        if created_to:
            where += " AND f.created_at <= %s::timestamptz"
            params.append(created_to)
        join = f" FROM {_T_FLAG} f JOIN {_T_REQ} r ON r.id = f.request_id"
        offset = (page - 1) * page_size
        with self._conn() as conn:
            total = conn.execute(
                f"SELECT COUNT(*) AS n{join} WHERE {where}",
                params,
            ).fetchone()["n"]
            status_rows = conn.execute(
                f"SELECT f.status, COUNT(*) AS n{join} WHERE {where}"
                " GROUP BY f.status",
                params,
            ).fetchall()
            distinct_req = conn.execute(
                f"SELECT COUNT(DISTINCT f.request_id) AS n{join}"
                f" WHERE {where}",
                params,
            ).fetchone()["n"]
            distinct_prod = conn.execute(
                f"SELECT COUNT(DISTINCT NULLIF(r.official_product_code,''))"
                f" AS n{join} WHERE {where}"
                " AND r.official_product_code IS NOT NULL"
                " AND btrim(r.official_product_code) <> ''",
                params,
            ).fetchone()["n"]
            rows = conn.execute(
                f"SELECT f.*, r.official_product_code,"
                f" r.request_type, r.status AS request_status,"
                f" r.assigned_to_subject,"
                f" coalesce("
                f"  r.requested_payload->'product'->>'description',"
                f"  r.requested_payload->>'description'"
                f" ) AS product_description"
                f"{join} WHERE {where}"
                " ORDER BY f.created_at DESC, f.id DESC"
                " LIMIT %s OFFSET %s",
                [*params, page_size, offset],
            ).fetchall()
        by_status = {r["status"]: int(r["n"]) for r in status_rows}
        items = []
        for r in rows:
            item = self._flag_row(r)
            item["product_code"] = r.get("official_product_code")
            item["request_type"] = r.get("request_type")
            item["request_status"] = r.get("request_status")
            item["assigned_to_subject"] = r.get("assigned_to_subject")
            item["product_description"] = r.get("product_description")
            items.append(item)
        return {
            "items": items,
            "page": page,
            "pageSize": page_size,
            "total": int(total),
            "openCount": by_status.get("OPEN", 0),
            "resolvedCount": by_status.get("RESOLVED", 0),
            "distinctRequestCount": int(distinct_req),
            "distinctProductCount": int(distinct_prod),
            "hasMore": offset + page_size < int(total),
        }

    def summarize_flags_cross_case(
        self,
        *,
        accessible_request_ids: list[str] | None,
        global_scope: bool,
        group_by: str,
        status: str | None = None,
        subject: str | None = None,
        target_path: str | None = None,
        target_attribute: str | None = None,
        product_code: str | None = None,
        request_status: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        if group_by not in (
            "request", "product", "targetPath", "subject", "targetAttribute",
        ):
            raise PrcRepositoryError("groupBy inválido")
        if not global_scope and not accessible_request_ids:
            return {
                "groupBy": group_by,
                "items": [],
                "page": page,
                "pageSize": page_size,
                "total": 0,
                "openCount": 0,
                "resolvedCount": 0,
                "distinctRequestCount": 0,
                "distinctProductCount": 0,
                "hasMore": False,
            }
        where = "f.deleted_at IS NULL"
        params: list[Any] = []
        if not global_scope:
            where += " AND f.request_id = ANY(%s::uuid[])"
            params.append(accessible_request_ids)
        if status:
            where += " AND f.status=%s"
            params.append(status)
        if subject:
            where += " AND f.subject=%s"
            params.append(subject)
        if target_path:
            where += " AND f.target_path=%s"
            params.append(target_path)
        if target_attribute:
            where += " AND f.target_attribute=%s"
            params.append(target_attribute)
        if product_code:
            where += " AND r.official_product_code=%s"
            params.append(product_code)
        if request_status:
            where += " AND r.status=%s"
            params.append(request_status)
        join = f" FROM {_T_FLAG} f JOIN {_T_REQ} r ON r.id = f.request_id"
        group_expr = {
            "request": "f.request_id::text",
            "product": "NULLIF(btrim(r.official_product_code),'')",
            "targetPath": "f.target_path",
            "subject": "f.subject",
            "targetAttribute": "f.target_attribute",
        }[group_by]
        offset = (page - 1) * page_size
        with self._conn() as conn:
            totals = conn.execute(
                f"SELECT COUNT(*) AS flag_n,"
                f" COUNT(DISTINCT f.request_id) AS req_n,"
                f" COUNT(DISTINCT NULLIF(btrim(r.official_product_code),''))"
                f" AS prod_n,"
                f" COUNT(*) FILTER (WHERE f.status='OPEN') AS open_n,"
                f" COUNT(*) FILTER (WHERE f.status='RESOLVED') AS resolved_n"
                f"{join} WHERE {where}",
                params,
            ).fetchone()
            group_total = conn.execute(
                f"SELECT COUNT(*) AS n FROM ("
                f" SELECT {group_expr} AS g{join} WHERE {where}"
                f" AND {group_expr} IS NOT NULL"
                f" GROUP BY 1) s",
                params,
            ).fetchone()["n"]
            rows = conn.execute(
                f"SELECT {group_expr} AS group_key,"
                f" COUNT(*) AS flag_count,"
                f" COUNT(*) FILTER (WHERE f.status='OPEN') AS open_count,"
                f" COUNT(*) FILTER (WHERE f.status='RESOLVED')"
                f" AS resolved_count,"
                f" COUNT(DISTINCT f.request_id) AS request_count,"
                f" MAX(f.created_at) AS last_created_at"
                f"{join} WHERE {where} AND {group_expr} IS NOT NULL"
                f" GROUP BY 1"
                f" ORDER BY open_count DESC, flag_count DESC, group_key ASC"
                f" LIMIT %s OFFSET %s",
                [*params, page_size, offset],
            ).fetchall()
        return {
            "groupBy": group_by,
            "items": [
                {
                    "key": str(r["group_key"]),
                    "flagCount": int(r["flag_count"]),
                    "openCount": int(r["open_count"]),
                    "resolvedCount": int(r["resolved_count"]),
                    "requestCount": int(r["request_count"]),
                    "lastCreatedAt": _iso(r.get("last_created_at")),
                }
                for r in rows
            ],
            "page": page,
            "pageSize": page_size,
            "total": int(group_total),
            "openCount": int(totals["open_n"]),
            "resolvedCount": int(totals["resolved_n"]),
            "distinctRequestCount": int(totals["req_n"]),
            "distinctProductCount": int(totals["prod_n"]),
            "hasMore": offset + page_size < int(group_total),
        }

    def update_flag(
        self,
        *,
        request_id: str,
        flag_id: str,
        expected_version: int,
        patch: dict[str, Any],
        actor_subject: str,
        actor_display_name: str | None,
        event: dict[str, Any],
    ) -> dict[str, Any]:
        """Atualiza título/descrição. Alvo técnico é imutável (REF-01)."""
        with self._conn() as conn:
            row = conn.execute(
                f"SELECT * FROM {_T_FLAG}"
                " WHERE id=%s AND request_id=%s AND deleted_at IS NULL"
                " FOR UPDATE",
                (flag_id, request_id),
            ).fetchone()
            if row is None:
                raise PrcNotFoundError("flag", flag_id)
            if int(row["row_version"]) != int(expected_version):
                raise PrcConcurrencyError("stale_version")
            before = self._flag_row(row)
            conn.execute(
                f"UPDATE {_T_FLAG} SET"
                " title=%s, description=%s, row_version=%s,"
                " updated_by_subject=%s, updated_by_display_name=%s,"
                " updated_at=%s"
                " WHERE id=%s",
                (
                    patch.get("title", row["title"]),
                    patch.get("description", row["description"]),
                    int(row["row_version"]) + 1,
                    actor_subject, actor_display_name, _now(),
                    flag_id,
                ),
            )
            meta = dict(event.get("metadata") or {})
            meta["before"] = {
                "title": before["title"],
                "description": before["description"],
                "subject": before["subject"],
                "target_path": before.get("target_path"),
                "target_attribute": before.get("target_attribute"),
                "supplier_key": before.get("supplier_key"),
                "version": before["row_version"],
            }
            event = {**event, "metadata": meta}
            seq = conn.execute(
                f"SELECT COALESCE(MAX(sequence_number),0)+1 AS n"
                f" FROM {_T_EVT} WHERE request_id=%s",
                (request_id,),
            ).fetchone()["n"]
            self._insert_event(conn, request_id, seq, event)
            updated = conn.execute(
                f"SELECT * FROM {_T_FLAG} WHERE id=%s", (flag_id,)
            ).fetchone()
        return self._flag_row(updated)

    def transition_flag(
        self,
        *,
        request_id: str,
        flag_id: str,
        expected_version: int,
        next_status: str,
        actor_subject: str,
        actor_display_name: str | None,
        event: dict[str, Any],
    ) -> dict[str, Any]:
        from psycopg.errors import UniqueViolation

        with self._conn() as conn:
            row = conn.execute(
                f"SELECT * FROM {_T_FLAG}"
                " WHERE id=%s AND request_id=%s AND deleted_at IS NULL"
                " FOR UPDATE",
                (flag_id, request_id),
            ).fetchone()
            if row is None:
                raise PrcNotFoundError("flag", flag_id)
            if int(row["row_version"]) != int(expected_version):
                raise PrcConcurrencyError("stale_version")
            prev = row["status"]
            if prev == next_status:
                raise PrcStateConflictError("state_conflict")
            if next_status == "RESOLVED" and prev != "OPEN":
                raise PrcStateConflictError("state_conflict")
            if next_status == "OPEN" and prev != "RESOLVED":
                raise PrcStateConflictError("state_conflict")
            now = _now()
            try:
                if next_status == "RESOLVED":
                    conn.execute(
                        f"UPDATE {_T_FLAG} SET status=%s, row_version=%s,"
                        " updated_by_subject=%s, updated_by_display_name=%s,"
                        " updated_at=%s, resolved_by_subject=%s,"
                        " resolved_by_display_name=%s, resolved_at=%s"
                        " WHERE id=%s",
                        (
                            next_status, int(row["row_version"]) + 1,
                            actor_subject, actor_display_name, now,
                            actor_subject, actor_display_name, now, flag_id,
                        ),
                    )
                else:
                    conn.execute(
                        f"UPDATE {_T_FLAG} SET status=%s, row_version=%s,"
                        " updated_by_subject=%s, updated_by_display_name=%s,"
                        " updated_at=%s, resolved_by_subject=NULL,"
                        " resolved_by_display_name=NULL, resolved_at=NULL"
                        " WHERE id=%s",
                        (
                            next_status, int(row["row_version"]) + 1,
                            actor_subject, actor_display_name, now, flag_id,
                        ),
                    )
            except UniqueViolation as exc:
                raise PrcStateConflictError("open_flag_exists") from exc
            event = {
                **event,
                "previous_status": prev,
                "next_status": next_status,
            }
            seq = conn.execute(
                f"SELECT COALESCE(MAX(sequence_number),0)+1 AS n"
                f" FROM {_T_EVT} WHERE request_id=%s",
                (request_id,),
            ).fetchone()["n"]
            self._insert_event(conn, request_id, seq, event)
            updated = conn.execute(
                f"SELECT * FROM {_T_FLAG} WHERE id=%s", (flag_id,)
            ).fetchone()
        return self._flag_row(updated)

    def soft_delete_flag(
        self,
        *,
        request_id: str,
        flag_id: str,
        expected_version: int,
        actor_subject: str,
        actor_display_name: str | None,
        event: dict[str, Any],
    ) -> dict[str, Any]:
        with self._conn() as conn:
            row = conn.execute(
                f"SELECT * FROM {_T_FLAG}"
                " WHERE id=%s AND request_id=%s AND deleted_at IS NULL"
                " FOR UPDATE",
                (flag_id, request_id),
            ).fetchone()
            if row is None:
                raise PrcNotFoundError("flag", flag_id)
            if int(row["row_version"]) != int(expected_version):
                raise PrcConcurrencyError("stale_version")
            now = _now()
            conn.execute(
                f"UPDATE {_T_FLAG} SET deleted_at=%s, deleted_by_subject=%s,"
                " deleted_by_display_name=%s, row_version=%s,"
                " updated_by_subject=%s, updated_by_display_name=%s,"
                " updated_at=%s WHERE id=%s",
                (
                    now, actor_subject, actor_display_name,
                    int(row["row_version"]) + 1,
                    actor_subject, actor_display_name, now, flag_id,
                ),
            )
            seq = conn.execute(
                f"SELECT COALESCE(MAX(sequence_number),0)+1 AS n"
                f" FROM {_T_EVT} WHERE request_id=%s",
                (request_id,),
            ).fetchone()["n"]
            self._insert_event(conn, request_id, seq, event)
            updated = conn.execute(
                f"SELECT * FROM {_T_FLAG} WHERE id=%s", (flag_id,)
            ).fetchone()
        return self._flag_row(updated)

    # --- information rounds (PRC-REF-019) --------------------------------------

    @staticmethod
    def _info_round_row(row: dict) -> dict[str, Any]:
        out = dict(row)
        for key in ("id", "request_id", "parent_round_id"):
            if out.get(key) is not None:
                out[key] = str(out[key])
        for key in ("created_at", "updated_at", "resolved_at"):
            out[key] = _iso(out.get(key))
        return out

    @staticmethod
    def _info_question_row(row: dict) -> dict[str, Any]:
        out = dict(row)
        for key in ("id", "round_id", "request_id"):
            out[key] = str(out[key])
        sk = out.get("supplier_key")
        if isinstance(sk, str):
            try:
                out["supplier_key"] = json.loads(sk)
            except (TypeError, ValueError):
                out["supplier_key"] = None
        for key in ("created_at", "updated_at"):
            out[key] = _iso(out.get(key))
        return out

    @staticmethod
    def _info_answer_row(row: dict) -> dict[str, Any]:
        out = dict(row)
        for key in ("id", "question_id", "round_id", "request_id"):
            out[key] = str(out[key])
        for key in ("created_at", "updated_at", "submitted_at"):
            out[key] = _iso(out.get(key))
        return out

    def _assemble_info_rounds(
        self, conn, round_rows: list[dict]
    ) -> list[dict[str, Any]]:
        """Monta rodadas com perguntas e respostas aninhadas (mesma conexão)."""
        if not round_rows:
            return []
        round_ids = [str(r["id"]) for r in round_rows]
        question_rows = conn.execute(
            f"SELECT * FROM {_T_INFO_Q} WHERE round_id = ANY(%s::uuid[])"
            " ORDER BY round_id, ordinal",
            (round_ids,),
        ).fetchall()
        answer_rows = conn.execute(
            f"SELECT * FROM {_T_INFO_A} WHERE round_id = ANY(%s::uuid[])",
            (round_ids,),
        ).fetchall()
        answers_by_question = {
            str(a["question_id"]): self._info_answer_row(a)
            for a in answer_rows
        }
        questions_by_round: dict[str, list[dict[str, Any]]] = {}
        for q in question_rows:
            question = self._info_question_row(q)
            question["answer"] = answers_by_question.get(question["id"])
            questions_by_round.setdefault(question["round_id"], []).append(
                question
            )
        out: list[dict[str, Any]] = []
        for row in round_rows:
            rnd = self._info_round_row(row)
            rnd["questions"] = questions_by_round.get(rnd["id"], [])
            out.append(rnd)
        return out

    def _load_info_round(
        self, conn, request_id: str, round_id: str
    ) -> dict[str, Any] | None:
        row = conn.execute(
            f"SELECT * FROM {_T_INFO_ROUND} WHERE id=%s AND request_id=%s",
            (round_id, request_id),
        ).fetchone()
        if row is None:
            return None
        return self._assemble_info_rounds(conn, [row])[0]

    def _lock_request_row(self, conn, request_id: str) -> dict:
        """Lock do caso (ordem de lock: request → rodada) sem CAS de versão."""
        row = conn.execute(
            f"SELECT * FROM {_T_REQ} WHERE id=%s FOR UPDATE",
            (request_id,),
        ).fetchone()
        if row is None:
            raise PrcNotFoundError("request", request_id)
        return row

    def _lock_info_round(
        self, conn, request_id: str, round_id: str
    ) -> dict:
        row = conn.execute(
            f"SELECT * FROM {_T_INFO_ROUND}"
            " WHERE id=%s AND request_id=%s FOR UPDATE",
            (round_id, request_id),
        ).fetchone()
        if row is None:
            raise PrcNotFoundError("information_round", round_id)
        return row

    def _insert_info_questions(
        self,
        conn,
        *,
        round_id: str,
        request_id: str,
        questions: list[dict[str, Any]],
    ) -> None:
        now = _now()
        for q in questions:
            supplier_key = q.get("supplier_key")
            conn.execute(
                f"INSERT INTO {_T_INFO_Q}"
                " (id, round_id, request_id, ordinal, target_type,"
                "  target_path, target_attribute, supplier_key,"
                "  target_key, target_label, question_text, status,"
                "  created_at, updated_at)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (
                    q.get("id") or _uuid(), round_id, request_id,
                    q["ordinal"], q["target_type"],
                    q.get("target_path"), q.get("target_attribute"),
                    json.dumps(supplier_key)
                    if supplier_key is not None else None,
                    q["target_key"], q["target_label"],
                    q["question_text"], q.get("status") or "pending",
                    now, now,
                ),
            )

    def _insert_info_round_row(
        self,
        conn,
        *,
        request_id: str,
        round_row: dict[str, Any],
    ) -> str:
        """Insere a rodada com ``sequence`` calculada sob lock do caso."""
        seq = conn.execute(
            f"SELECT COALESCE(MAX(sequence),0)+1 AS s"
            f" FROM {_T_INFO_ROUND} WHERE request_id=%s",
            (request_id,),
        ).fetchone()["s"]
        round_id = round_row.get("id") or _uuid()
        now = _now()
        conn.execute(
            f"INSERT INTO {_T_INFO_ROUND}"
            " (id, request_id, sequence, origin_status, status,"
            "  parent_round_id, requested_by_subject,"
            "  requested_by_display_name, requester_subject, message,"
            "  row_version, created_at, updated_at)"
            " VALUES (%s,%s,%s,%s,'awaiting_requester',%s,%s,%s,%s,%s,"
            "         1,%s,%s)",
            (
                round_id, request_id, int(seq),
                round_row["origin_status"],
                round_row.get("parent_round_id"),
                round_row["requested_by_subject"],
                round_row.get("requested_by_display_name"),
                round_row["requester_subject"],
                round_row.get("message"),
                now, now,
            ),
        )
        return str(round_id)

    def _append_info_event(
        self,
        conn,
        *,
        request_id: str,
        request_status: str,
        event: dict[str, Any],
        extra_meta: dict[str, Any] | None = None,
    ) -> None:
        """Evento do caso; rodadas não mudam o status do caso por si só."""
        meta = {**(event.get("metadata") or {}), **(extra_meta or {})}
        full = {
            **event,
            "metadata": meta,
            "previous_status": event.get("previous_status", request_status),
            "next_status": event.get("next_status", request_status),
        }
        self._insert_event(
            conn, request_id, self._next_event_seq(conn, request_id), full
        )

    def create_information_round(
        self,
        *,
        request_id: str,
        expected_version: int,
        allowed_from: frozenset[str],
        next_status: str,
        actor_label: str,
        actor_subject: str,
        actor_email: str | None,
        event_type: str,
        reason: str | None,
        event_meta: dict[str, Any],
        round_row: dict[str, Any],
        questions: list[dict[str, Any]],
        set_fields: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """CAS do caso + transição + rodada/perguntas + evento (1 txn).

        Retorna ``{"request": <caso>, "round": <rodada aninhada>}``.
        """
        with self._conn() as conn:
            req = self._lock_and_check(
                conn, request_id, expected_version, allowed_from
            )
            open_round = conn.execute(
                f"SELECT 1 FROM {_T_INFO_ROUND}"
                " WHERE request_id=%s AND status = ANY(%s) LIMIT 1",
                (request_id, list(_INFO_OPEN_ROUND_STATUSES)),
            ).fetchone()
            if open_round:
                raise PrcStateConflictError("information_round_open")
            prev = req["status"]
            now = _now()
            sets = ["row_version=row_version+1", "updated_at=%s"]
            params: list[Any] = [now]
            if next_status != prev:
                sets.insert(0, "status=%s")
                params.insert(0, next_status)
            for key, value in (set_fields or {}).items():
                sets.append(f"{key}=%s")
                params.append(value)
            params.append(request_id)
            conn.execute(
                f"UPDATE {_T_REQ} SET {', '.join(sets)} WHERE id=%s",
                params,
            )
            round_id = self._insert_info_round_row(
                conn, request_id=request_id, round_row=round_row
            )
            self._insert_info_questions(
                conn, round_id=round_id, request_id=request_id,
                questions=questions,
            )
            created = self._load_info_round(conn, request_id, round_id)
            self._append_info_event(
                conn,
                request_id=request_id,
                request_status=prev,
                event={
                    "event_type": event_type,
                    "actor_subject": actor_subject,
                    "actor_display_name": actor_label,
                    "actor_email": actor_email,
                    "reason": reason,
                    "metadata": dict(event_meta),
                    "previous_status": prev,
                    "next_status": next_status,
                },
                extra_meta={
                    "roundId": round_id,
                    "roundSequence": created["sequence"],
                    "questionCount": len(questions),
                },
            )
        return {"request": self.get_request(request_id), "round": created}

    def get_information_round(
        self, *, request_id: str, round_id: str
    ) -> dict[str, Any] | None:
        with self._conn() as conn:
            return self._load_info_round(conn, request_id, round_id)

    def list_information_rounds(
        self, *, request_id: str
    ) -> list[dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                f"SELECT * FROM {_T_INFO_ROUND} WHERE request_id=%s"
                " ORDER BY sequence",
                (request_id,),
            ).fetchall()
            return self._assemble_info_rounds(conn, rows)

    def save_information_answers_draft(
        self,
        *,
        request_id: str,
        round_id: str,
        expected_round_version: int,
        actor_subject: str,
        answers: list[dict[str, Any]],
        event: dict[str, Any],
    ) -> dict[str, Any]:
        """Upsert de rascunhos (``answers[]`` = ``question_id`` + ``text``)."""
        with self._conn() as conn:
            req = self._lock_request_row(conn, request_id)
            rnd = self._lock_info_round(conn, request_id, round_id)
            if int(rnd["row_version"]) != int(expected_round_version):
                raise PrcConcurrencyError("stale_version")
            if rnd["status"] != "awaiting_requester":
                raise PrcStateConflictError("state_conflict")
            question_ids = {
                str(r["id"])
                for r in conn.execute(
                    f"SELECT id FROM {_T_INFO_Q} WHERE round_id=%s",
                    (round_id,),
                ).fetchall()
            }
            now = _now()
            for ans in answers:
                qid = str(ans["question_id"])
                if qid not in question_ids:
                    raise PrcNotFoundError("information_question", qid)
                text = str(ans.get("text") or "")
                updated = conn.execute(
                    f"UPDATE {_T_INFO_A} SET text=%s, author_subject=%s,"
                    " status='draft', row_version=row_version+1,"
                    " updated_at=%s WHERE question_id=%s RETURNING id",
                    (text, actor_subject, now, qid),
                ).fetchone()
                if updated is None:
                    conn.execute(
                        f"INSERT INTO {_T_INFO_A}"
                        " (id, question_id, round_id, request_id,"
                        "  author_subject, text, status, row_version,"
                        "  created_at, updated_at)"
                        " VALUES (%s,%s,%s,%s,%s,%s,'draft',1,%s,%s)",
                        (
                            _uuid(), qid, round_id, request_id,
                            actor_subject, text, now, now,
                        ),
                    )
                conn.execute(
                    f"UPDATE {_T_INFO_Q} SET status=%s, updated_at=%s"
                    " WHERE id=%s",
                    ("drafted" if text.strip() else "pending", now, qid),
                )
            conn.execute(
                f"UPDATE {_T_INFO_ROUND} SET row_version=row_version+1,"
                " updated_at=%s WHERE id=%s",
                (now, round_id),
            )
            self._append_info_event(
                conn, request_id=request_id,
                request_status=req["status"], event=event,
                extra_meta={
                    "roundId": round_id,
                    "answerCount": len(answers),
                },
            )
            return self._load_info_round(conn, request_id, round_id)

    def submit_information_answers(
        self,
        *,
        request_id: str,
        round_id: str,
        expected_round_version: int,
        actor_subject: str,
        answers: list[dict[str, Any]],
        event: dict[str, Any],
    ) -> dict[str, Any]:
        """Envia respostas: todas as perguntas exigem texto não vazio
        (payload + rascunhos já salvos); rodada → ``awaiting_review``."""
        with self._conn() as conn:
            req = self._lock_request_row(conn, request_id)
            rnd = self._lock_info_round(conn, request_id, round_id)
            if int(rnd["row_version"]) != int(expected_round_version):
                raise PrcConcurrencyError("stale_version")
            if rnd["status"] != "awaiting_requester":
                raise PrcStateConflictError("state_conflict")
            question_ids = [
                str(r["id"])
                for r in conn.execute(
                    f"SELECT id FROM {_T_INFO_Q} WHERE round_id=%s"
                    " ORDER BY ordinal",
                    (round_id,),
                ).fetchall()
            ]
            known = set(question_ids)
            texts: dict[str, str] = {
                str(r["question_id"]): str(r["text"] or "")
                for r in conn.execute(
                    f"SELECT question_id, text FROM {_T_INFO_A}"
                    " WHERE round_id=%s",
                    (round_id,),
                ).fetchall()
            }
            for ans in answers:
                qid = str(ans["question_id"])
                if qid not in known:
                    raise PrcNotFoundError("information_question", qid)
                texts[qid] = str(ans.get("text") or "")
            missing = [
                qid for qid in question_ids
                if not texts.get(qid, "").strip()
            ]
            if missing:
                raise PrcValidationError(
                    "Todas as perguntas exigem resposta antes do envio.",
                    fields={
                        f"answers[{qid}].text": "required"
                        for qid in missing
                    },
                )
            now = _now()
            for qid in question_ids:
                text = texts[qid].strip()
                updated = conn.execute(
                    f"UPDATE {_T_INFO_A} SET text=%s, author_subject=%s,"
                    " status='submitted', row_version=row_version+1,"
                    " updated_at=%s, submitted_at=%s"
                    " WHERE question_id=%s RETURNING id",
                    (text, actor_subject, now, now, qid),
                ).fetchone()
                if updated is None:
                    conn.execute(
                        f"INSERT INTO {_T_INFO_A}"
                        " (id, question_id, round_id, request_id,"
                        "  author_subject, text, status, row_version,"
                        "  created_at, updated_at, submitted_at)"
                        " VALUES (%s,%s,%s,%s,%s,%s,'submitted',1,"
                        "         %s,%s,%s)",
                        (
                            _uuid(), qid, round_id, request_id,
                            actor_subject, text, now, now, now,
                        ),
                    )
                conn.execute(
                    f"UPDATE {_T_INFO_Q} SET status='submitted',"
                    " updated_at=%s WHERE id=%s",
                    (now, qid),
                )
            conn.execute(
                f"UPDATE {_T_INFO_ROUND} SET status='awaiting_review',"
                " row_version=row_version+1, updated_at=%s WHERE id=%s",
                (now, round_id),
            )
            self._append_info_event(
                conn, request_id=request_id,
                request_status=req["status"], event=event,
                extra_meta={
                    "roundId": round_id,
                    "answerCount": len(question_ids),
                },
            )
            return self._load_info_round(conn, request_id, round_id)

    def accept_information_question(
        self,
        *,
        request_id: str,
        round_id: str,
        question_id: str,
        expected_round_version: int,
        actor_subject: str,
        actor_display_name: str | None,
        event: dict[str, Any],
    ) -> dict[str, Any]:
        """Aceita a pergunta; resolve a rodada quando todas as perguntas
        estão em estado terminal (aceita ou com complemento solicitado)."""
        with self._conn() as conn:
            req = self._lock_request_row(conn, request_id)
            rnd = self._lock_info_round(conn, request_id, round_id)
            if int(rnd["row_version"]) != int(expected_round_version):
                raise PrcConcurrencyError("stale_version")
            if rnd["status"] != "awaiting_review":
                raise PrcStateConflictError("state_conflict")
            question = conn.execute(
                f"SELECT * FROM {_T_INFO_Q}"
                " WHERE id=%s AND round_id=%s FOR UPDATE",
                (question_id, round_id),
            ).fetchone()
            if question is None:
                raise PrcNotFoundError("information_question", question_id)
            if question["status"] != "submitted":
                raise PrcStateConflictError("state_conflict")
            now = _now()
            conn.execute(
                f"UPDATE {_T_INFO_Q} SET status='accepted', updated_at=%s"
                " WHERE id=%s",
                (now, question_id),
            )
            statuses = {
                r["status"]
                for r in conn.execute(
                    f"SELECT status FROM {_T_INFO_Q} WHERE round_id=%s",
                    (round_id,),
                ).fetchall()
            }
            resolved = statuses <= _INFO_TERMINAL_QUESTION_STATUSES
            if resolved:
                conn.execute(
                    f"UPDATE {_T_INFO_ROUND} SET status='resolved',"
                    " row_version=row_version+1, updated_at=%s,"
                    " resolved_at=%s, resolved_by_subject=%s,"
                    " resolved_by_display_name=%s WHERE id=%s",
                    (
                        now, now, actor_subject, actor_display_name,
                        round_id,
                    ),
                )
            else:
                conn.execute(
                    f"UPDATE {_T_INFO_ROUND} SET"
                    " row_version=row_version+1, updated_at=%s"
                    " WHERE id=%s",
                    (now, round_id),
                )
            self._append_info_event(
                conn, request_id=request_id,
                request_status=req["status"], event=event,
                extra_meta={
                    "roundId": round_id,
                    "questionId": question_id,
                    "roundResolved": resolved,
                },
            )
            return self._load_info_round(conn, request_id, round_id)

    def create_information_follow_up(
        self,
        *,
        request_id: str,
        parent_round_id: str,
        expected_parent_version: int,
        actor_label: str,
        actor_subject: str,
        actor_email: str | None,
        event: dict[str, Any],
        round_row: dict[str, Any],
        questions: list[dict[str, Any]],
        follow_up_question_ids: list[str],
    ) -> dict[str, Any]:
        """Marca perguntas do pai como ``follow_up_requested`` e abre a nova
        rodada; o caso permanece ``needs_information``.

        Retorna ``{"parentRound": ..., "round": ...}`` (ambos aninhados).
        """
        with self._conn() as conn:
            req = self._lock_request_row(conn, request_id)
            parent = self._lock_info_round(conn, request_id, parent_round_id)
            if int(parent["row_version"]) != int(expected_parent_version):
                raise PrcConcurrencyError("stale_version")
            if parent["status"] != "awaiting_review":
                raise PrcStateConflictError("state_conflict")
            if req["status"] != "needs_information":
                raise PrcStateConflictError("state_conflict")
            target_ids = [str(i) for i in follow_up_question_ids]
            if not target_ids:
                raise PrcValidationError(
                    "Informe ao menos uma pergunta para complemento.",
                    fields={"followUpQuestionIds": "required"},
                )
            parent_questions = {
                str(q["id"]): q
                for q in conn.execute(
                    f"SELECT * FROM {_T_INFO_Q} WHERE round_id=%s"
                    " FOR UPDATE",
                    (parent_round_id,),
                ).fetchall()
            }
            for qid in target_ids:
                question = parent_questions.get(qid)
                if question is None:
                    raise PrcNotFoundError("information_question", qid)
                if question["status"] != "submitted":
                    raise PrcStateConflictError("state_conflict")
            now = _now()
            conn.execute(
                f"UPDATE {_T_INFO_Q} SET status='follow_up_requested',"
                " updated_at=%s WHERE id = ANY(%s::uuid[])",
                (now, target_ids),
            )
            statuses = {
                (
                    "follow_up_requested"
                    if qid in target_ids else q["status"]
                )
                for qid, q in parent_questions.items()
            }
            parent_resolved = statuses <= _INFO_TERMINAL_QUESTION_STATUSES
            if parent_resolved:
                conn.execute(
                    f"UPDATE {_T_INFO_ROUND} SET status='resolved',"
                    " row_version=row_version+1, updated_at=%s,"
                    " resolved_at=%s, resolved_by_subject=%s,"
                    " resolved_by_display_name=%s WHERE id=%s",
                    (now, now, actor_subject, actor_label, parent_round_id),
                )
            else:
                conn.execute(
                    f"UPDATE {_T_INFO_ROUND} SET"
                    " row_version=row_version+1, updated_at=%s"
                    " WHERE id=%s",
                    (now, parent_round_id),
                )
            new_id = self._insert_info_round_row(
                conn,
                request_id=request_id,
                round_row={**round_row, "parent_round_id": parent_round_id},
            )
            self._insert_info_questions(
                conn, round_id=new_id, request_id=request_id,
                questions=questions,
            )
            created = self._load_info_round(conn, request_id, new_id)
            updated_parent = self._load_info_round(
                conn, request_id, parent_round_id
            )
            self._append_info_event(
                conn,
                request_id=request_id,
                request_status=req["status"],
                event={
                    **event,
                    "actor_subject": actor_subject,
                    "actor_display_name": (
                        event.get("actor_display_name") or actor_label
                    ),
                    "actor_email": event.get("actor_email") or actor_email,
                },
                extra_meta={
                    "parentRoundId": parent_round_id,
                    "roundId": new_id,
                    "roundSequence": created["sequence"],
                    "followUpQuestionIds": target_ids,
                    "parentResolved": parent_resolved,
                    "questionCount": len(questions),
                },
            )
        return {"parentRound": updated_parent, "round": created}


    def resolve_open_information_rounds(
        self,
        *,
        request_id: str,
        actor_subject: str,
        actor_display_name: str | None,
        event: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Resolve todas as rodadas abertas (dispensa explícita no resume)."""
        with self._conn() as conn:
            req = self._lock_request_row(conn, request_id)
            rows = conn.execute(
                f"SELECT id FROM {_T_INFO_ROUND}"
                " WHERE request_id=%s"
                " AND status IN ('awaiting_requester','awaiting_review')"
                " ORDER BY sequence FOR UPDATE",
                (request_id,),
            ).fetchall()
            now = _now()
            resolved_ids: list[str] = []
            for row in rows:
                rid = str(row["id"])
                conn.execute(
                    f"UPDATE {_T_INFO_ROUND} SET status='resolved',"
                    " row_version=row_version+1, updated_at=%s,"
                    " resolved_at=%s, resolved_by_subject=%s,"
                    " resolved_by_display_name=%s WHERE id=%s",
                    (
                        now, now, actor_subject, actor_display_name, rid,
                    ),
                )
                resolved_ids.append(rid)
            if resolved_ids:
                self._append_info_event(
                    conn, request_id=request_id,
                    request_status=req["status"], event=event,
                    extra_meta={"resolvedRoundIds": resolved_ids, "waiver": True},
                )
            return [
                self._load_info_round(conn, request_id, rid)
                for rid in resolved_ids
            ]

    # --- PRC-REF-022 correction returns --------------------------------------

    def _map_correction_target(self, row: dict[str, Any]) -> dict[str, Any]:
        out = dict(row)
        out["id"] = str(out["id"])
        out["return_id"] = str(out["return_id"])
        out["request_id"] = str(out["request_id"])
        out["created_at"] = _iso(out.get("created_at"))
        out["addressed_at"] = _iso(out.get("addressed_at"))
        return out

    def _map_correction_return(
        self, row: dict[str, Any], targets: list[dict[str, Any]]
    ) -> dict[str, Any]:
        out = dict(row)
        out["id"] = str(out["id"])
        out["request_id"] = str(out["request_id"])
        for key in (
            "created_at",
            "updated_at",
            "resubmitted_at",
        ):
            out[key] = _iso(out.get(key))
        out["targets"] = targets
        return out

    def _load_correction_targets(
        self, conn, return_id: str
    ) -> list[dict[str, Any]]:
        rows = conn.execute(
            f"SELECT * FROM {_T_CORR_TGT} WHERE return_id=%s"
            " ORDER BY ordinal",
            (return_id,),
        ).fetchall()
        return [self._map_correction_target(dict(r)) for r in rows]

    def _load_correction_return(
        self, conn, request_id: str, return_id: str
    ) -> dict[str, Any] | None:
        row = conn.execute(
            f"SELECT * FROM {_T_CORR_RET}"
            " WHERE id=%s AND request_id=%s",
            (return_id, request_id),
        ).fetchone()
        if row is None:
            return None
        targets = self._load_correction_targets(conn, return_id)
        return self._map_correction_return(dict(row), targets)

    def get_correction_return(
        self, *, request_id: str, return_id: str
    ) -> dict[str, Any] | None:
        with self._conn() as conn:
            return self._load_correction_return(conn, request_id, return_id)

    def get_open_correction_return(
        self, *, request_id: str
    ) -> dict[str, Any] | None:
        with self._conn() as conn:
            row = conn.execute(
                f"SELECT * FROM {_T_CORR_RET}"
                " WHERE request_id=%s AND status='open'"
                " ORDER BY sequence DESC LIMIT 1",
                (request_id,),
            ).fetchone()
            if row is None:
                return None
            targets = self._load_correction_targets(conn, str(row["id"]))
            return self._map_correction_return(dict(row), targets)

    def list_correction_returns(
        self, *, request_id: str
    ) -> list[dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                f"SELECT * FROM {_T_CORR_RET} WHERE request_id=%s"
                " ORDER BY sequence",
                (request_id,),
            ).fetchall()
            out = []
            for row in rows:
                rid = str(row["id"])
                targets = self._load_correction_targets(conn, rid)
                out.append(self._map_correction_return(dict(row), targets))
            return out

    def create_correction_return(
        self,
        *,
        request_id: str,
        expected_version: int,
        actor_subject: str,
        actor_label: str,
        actor_email: str | None,
        reason: str | None,
        event_meta: dict[str, Any],
        return_row: dict[str, Any],
        targets: list[dict[str, Any]],
    ) -> dict[str, Any]:
        with self._conn() as conn:
            req = self._lock_and_check(
                conn, request_id, expected_version, frozenset({"in_progress"})
            )
            open_row = conn.execute(
                f"SELECT 1 FROM {_T_CORR_RET}"
                " WHERE request_id=%s AND status='open' LIMIT 1",
                (request_id,),
            ).fetchone()
            if open_row:
                raise PrcStateConflictError("correction_return_open")
            seq_row = conn.execute(
                f"SELECT COALESCE(MAX(sequence), 0) AS mx"
                f" FROM {_T_CORR_RET} WHERE request_id=%s",
                (request_id,),
            ).fetchone()
            seq = int(seq_row["mx"]) + 1
            now = _now()
            rid = str(return_row.get("id") or _uuid())
            draft = conn.execute(
                f"SELECT technical_data FROM {_T_DRAFT}"
                " WHERE request_id=%s",
                (request_id,),
            ).fetchone()
            tech = dict((draft or {}).get("technical_data") or {})
            conn.execute(
                f"INSERT INTO {_T_CORR_RET}"
                " (id, request_id, sequence, status, origin_case_version,"
                "  returned_by_subject, returned_by_display_name,"
                "  requester_subject, draft_snapshot, row_version,"
                "  created_at, updated_at)"
                " VALUES (%s,%s,%s,'open',%s,%s,%s,%s,%s,1,%s,%s)",
                (
                    rid,
                    request_id,
                    seq,
                    int(req["row_version"]),
                    actor_subject,
                    actor_label,
                    req["requester_subject"],
                    json.dumps(tech),
                    now,
                    now,
                ),
            )
            for t in targets:
                baseline = None
                if t["target_type"] == "FIELD":
                    baseline = tech.get(t["target_path"])
                elif t["target_type"] == "SUPPLIER_LINK":
                    key = t.get("supplier_key") or {}
                    baseline = next(
                        (
                            s
                            for s in (tech.get("suppliers") or [])
                            if isinstance(s, dict)
                            and str(s.get("supplierCode") or "").strip()
                            == str(key.get("supplierCode") or "").strip()
                            and str(s.get("store") or "").strip()
                            == str(key.get("store") or "").strip()
                        ),
                        None,
                    )
                conn.execute(
                    f"INSERT INTO {_T_CORR_TGT}"
                    " (id, return_id, request_id, ordinal, target_type,"
                    "  target_path, target_attribute, supplier_key,"
                    "  target_key, target_label, reason, baseline_value,"
                    "  created_at)"
                    " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (
                        _uuid(),
                        rid,
                        request_id,
                        t["ordinal"],
                        t["target_type"],
                        t.get("target_path"),
                        t.get("target_attribute"),
                        json.dumps(t.get("supplier_key"))
                        if t.get("supplier_key") is not None
                        else None,
                        t["target_key"],
                        t["target_label"],
                        t["reason"],
                        json.dumps(baseline)
                        if baseline is not None
                        else None,
                        now,
                    ),
                )
            prev = req["status"]
            conn.execute(
                f"UPDATE {_T_REQ} SET status=%s, row_version=row_version+1,"
                " updated_at=%s WHERE id=%s",
                ("needs_correction", now, request_id),
            )
            self._insert_event(
                conn,
                request_id,
                self._next_event_seq(conn, request_id),
                {
                    "event_type": "correction_returned",
                    "actor_subject": actor_subject,
                    "actor_display_name": actor_label,
                    "actor_email": actor_email,
                    "reason": reason,
                    "metadata": {
                        **event_meta,
                        "returnId": rid,
                        "sequence": seq,
                        "targetKeys": [t["target_key"] for t in targets],
                    },
                    "previous_status": prev,
                    "next_status": "needs_correction",
                },
            )
            created = self._load_correction_return(conn, request_id, rid)
        return {
            "request": self.get_request(request_id),
            "return": created,
        }

    def update_returned_fields(
        self,
        *,
        request_id: str,
        expected_version: int,
        actor_subject: str,
        actor_display_name: str | None,
        actor_email: str | None,
        changes: list[dict[str, Any]],
        addressed_supplier_keys: set[str] | None = None,
        event_meta: dict[str, Any],
    ) -> dict[str, Any]:
        with self._conn() as conn:
            req = self._lock_and_check(
                conn,
                request_id,
                expected_version,
                frozenset({"needs_correction"}),
            )
            open_row = conn.execute(
                f"SELECT * FROM {_T_CORR_RET}"
                " WHERE request_id=%s AND status='open' FOR UPDATE",
                (request_id,),
            ).fetchone()
            if open_row is None:
                raise PrcStateConflictError("correction_return_missing")
            return_id = str(open_row["id"])
            draft = conn.execute(
                f"SELECT * FROM {_T_DRAFT} WHERE request_id=%s FOR UPDATE",
                (request_id,),
            ).fetchone()
            data = dict(draft["technical_data"] or {})
            changed = {
                c["path"]: c for c in (draft["changed_paths"] or [])
            }
            applied: list[dict[str, Any]] = []
            now = _now()
            for change in changes:
                path = change["path"]
                mode = change.get("mode") or "changed"
                old = data.get(path)
                new_val = old if mode == "confirmed" else change.get(
                    "proposedValue"
                )
                if mode != "confirmed":
                    data[path] = new_val
                    changed[path] = {
                        "path": path,
                        "reason": change.get("reason") or "correction",
                    }
                applied.append(
                    {
                        "path": path,
                        "before": old,
                        "after": new_val,
                        "reason": change.get("reason"),
                        "mode": mode,
                    }
                )
                if path == "suppliers":
                    for tkey in addressed_supplier_keys or set():
                        conn.execute(
                            f"UPDATE {_T_CORR_TGT} SET addressed_at=%s,"
                            " addressed_by_subject=%s, addressed_mode=%s,"
                            " addressed_value=%s"
                            " WHERE return_id=%s"
                            " AND target_type='SUPPLIER_LINK'"
                            " AND target_key=%s",
                            (
                                now,
                                actor_subject,
                                mode,
                                json.dumps(new_val)
                                if new_val is not None
                                else None,
                                return_id,
                                tkey,
                            ),
                        )
                else:
                    conn.execute(
                        f"UPDATE {_T_CORR_TGT} SET addressed_at=%s,"
                        " addressed_by_subject=%s, addressed_mode=%s,"
                        " addressed_value=%s"
                        " WHERE return_id=%s AND target_type='FIELD'"
                        " AND target_path=%s",
                        (
                            now,
                            actor_subject,
                            mode,
                            json.dumps(new_val)
                            if new_val is not None
                            else None,
                            return_id,
                            path,
                        ),
                    )
            conn.execute(
                f"UPDATE {_T_DRAFT} SET technical_data=%s,"
                " changed_paths=%s, row_version=row_version+1,"
                " updated_by_subject=%s, updated_at=%s"
                " WHERE request_id=%s",
                (
                    json.dumps(data),
                    json.dumps(list(changed.values())),
                    actor_subject,
                    now,
                    request_id,
                ),
            )
            conn.execute(
                f"UPDATE {_T_REQ} SET row_version=row_version+1,"
                " updated_at=%s WHERE id=%s",
                (now, request_id),
            )
            conn.execute(
                f"UPDATE {_T_CORR_RET} SET row_version=row_version+1,"
                " updated_at=%s WHERE id=%s",
                (now, return_id),
            )
            self._insert_event(
                conn,
                request_id,
                self._next_event_seq(conn, request_id),
                {
                    "event_type": "correction_fields_saved",
                    "actor_subject": actor_subject,
                    "actor_display_name": actor_display_name,
                    "actor_email": actor_email,
                    "reason": None,
                    "metadata": {
                        "changes": applied,
                        "returnId": return_id,
                        **event_meta,
                    },
                    "previous_status": req["status"],
                    "next_status": req["status"],
                },
            )
        return self.get_request(request_id)

    def resubmit_correction(
        self,
        *,
        request_id: str,
        expected_version: int,
        actor_subject: str,
        actor_label: str,
        actor_email: str | None,
        event_meta: dict[str, Any],
    ) -> dict[str, Any]:
        with self._conn() as conn:
            req = self._lock_and_check(
                conn,
                request_id,
                expected_version,
                frozenset({"needs_correction"}),
            )
            open_row = conn.execute(
                f"SELECT * FROM {_T_CORR_RET}"
                " WHERE request_id=%s AND status='open' FOR UPDATE",
                (request_id,),
            ).fetchone()
            if open_row is None:
                raise PrcStateConflictError("correction_return_missing")
            return_id = str(open_row["id"])
            now = _now()
            conn.execute(
                f"UPDATE {_T_CORR_RET} SET status='resubmitted',"
                " row_version=row_version+1, updated_at=%s,"
                " resubmitted_at=%s, resubmitted_by_subject=%s"
                " WHERE id=%s",
                (now, now, actor_subject, return_id),
            )
            prev = req["status"]
            conn.execute(
                f"UPDATE {_T_REQ} SET status=%s, row_version=row_version+1,"
                " updated_at=%s WHERE id=%s",
                ("in_progress", now, request_id),
            )
            self._insert_event(
                conn,
                request_id,
                self._next_event_seq(conn, request_id),
                {
                    "event_type": "correction_resubmitted",
                    "actor_subject": actor_subject,
                    "actor_display_name": actor_label,
                    "actor_email": actor_email,
                    "reason": None,
                    "metadata": {
                        **event_meta,
                        "returnId": return_id,
                        "sequence": open_row["sequence"],
                    },
                    "previous_status": prev,
                    "next_status": "in_progress",
                },
            )
            closed = self._load_correction_return(conn, request_id, return_id)
        return {
            "request": self.get_request(request_id),
            "return": closed,
        }

    # --- PRC-REF-023 — vínculo documental -------------------------------------

    def _attachment_row(self, row: dict) -> dict[str, Any]:
        out = dict(row)
        out["id"] = str(out["id"])
        out["request_id"] = str(out["request_id"])
        out["created_at"] = _iso(out.get("created_at"))
        return out

    def create_attachment(self, *, attachment: dict[str, Any]) -> dict[str, Any]:
        with self._conn() as conn:
            conn.execute(
                f"INSERT INTO {_T_ATT}"
                " (id, request_id, original_file_name, media_type,"
                "  size_bytes, sha256, storage_key, state,"
                "  uploaded_by_subject, uploaded_by_display_name,"
                "  uploaded_by_email, correlation_id, created_at)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (
                    attachment["id"], attachment["request_id"],
                    attachment["original_file_name"],
                    attachment["media_type"], attachment["size_bytes"],
                    attachment["sha256"], attachment["storage_key"],
                    attachment["state"],
                    attachment["uploaded_by_subject"],
                    attachment.get("uploaded_by_display_name"),
                    attachment.get("uploaded_by_email"),
                    attachment.get("correlation_id"),
                    attachment["created_at"],
                ),
            )
        return self._attachment_row(attachment)

    def list_attachments(self, *, request_id: str) -> list[dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                f"SELECT * FROM {_T_ATT} WHERE request_id=%s"
                " AND state<>'DELETED' ORDER BY created_at, id",
                (request_id,),
            ).fetchall()
        return [self._attachment_row(r) for r in rows]

    def get_attachment(
        self, *, request_id: str, attachment_id: str
    ) -> dict[str, Any] | None:
        with self._conn() as conn:
            row = conn.execute(
                f"SELECT * FROM {_T_ATT} WHERE id=%s AND request_id=%s"
                " AND state<>'DELETED'",
                (attachment_id, request_id),
            ).fetchone()
        return self._attachment_row(row) if row else None

    def find_attachment_by_hash(
        self, *, request_id: str, sha256: str, original_file_name: str
    ) -> dict[str, Any] | None:
        with self._conn() as conn:
            row = conn.execute(
                f"SELECT * FROM {_T_ATT} WHERE request_id=%s"
                " AND sha256=%s AND original_file_name=%s"
                " AND state<>'DELETED' ORDER BY created_at LIMIT 1",
                (request_id, sha256, original_file_name),
            ).fetchone()
        return self._attachment_row(row) if row else None
