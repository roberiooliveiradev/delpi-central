"""Adapter in-memory do Product Registration — dev/testes.

Mesma semântica do adapter Postgres: CAS por ``row_version``, ledger
append-only de eventos, verificações auditáveis, idempotência por chave
e conclusão atômica com revisão imutável.
"""

from __future__ import annotations

import copy
import uuid
from datetime import datetime, timezone
from typing import Any

from engineering_app.domain.product_registration.errors import (
    PrcConcurrencyError,
    PrcNotFoundError,
    PrcRepositoryError,
    PrcStaleRevisionError,
    PrcStateConflictError,
    PrcValidationError,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _uuid() -> str:
    return str(uuid.uuid4())


class InMemoryProductRegistrationRepository:
    def __init__(self) -> None:
        self._requests: dict[str, dict] = {}
        self._drafts: dict[str, dict] = {}
        self._events: dict[str, list[dict]] = {}
        self._event_seq: dict[str, int] = {}
        self._verifications: dict[str, list[dict]] = {}
        self._records: dict[str, dict] = {}
        self._record_by_key: dict[tuple[str, str], str] = {}
        self._revisions: dict[str, list[dict]] = {}
        self._idempotency: dict[tuple[str, str, str], dict] = {}
        self._flags: dict[str, dict] = {}  # flag_id → row
        # PRC-REF-019 — rodadas de esclarecimento.
        self._info_rounds: dict[str, dict] = {}  # round_id → row
        self._info_questions: dict[str, dict] = {}  # question_id → row
        self._info_answers: dict[str, dict] = {}  # question_id → row

    # --- helpers internos ------------------------------------------------------

    def _require_request(self, request_id: str) -> dict:
        req = self._requests.get(request_id)
        if req is None:
            raise PrcNotFoundError("request", request_id)
        return req

    def _append_event(self, request_id: str, event: dict) -> dict:
        seq = self._event_seq.get(request_id, 0) + 1
        self._event_seq[request_id] = seq
        row = {
            "id": _uuid(),
            "request_id": request_id,
            "sequence_number": seq,
            "occurred_at": _now(),
            **event,
        }
        self._events.setdefault(request_id, []).append(row)
        return copy.deepcopy(row)

    def _check_cas(
        self, req: dict, expected_version: int, allowed_from: frozenset[str]
    ) -> None:
        if int(req["row_version"]) != int(expected_version):
            raise PrcConcurrencyError("stale_version")
        if req["status"] not in allowed_from:
            raise PrcStateConflictError("state_conflict")

    # --- idempotência -----------------------------------------------------------

    def find_idempotent(
        self, *, actor_or_source: str, operation: str, idempotency_key: str
    ) -> dict[str, Any] | None:
        row = self._idempotency.get((actor_or_source, operation, idempotency_key))
        return copy.deepcopy(row) if row else None

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
        key = (actor_or_source, operation, idempotency_key)
        self._idempotency.setdefault(
            key,
            {
                "id": _uuid(),
                "actor_or_source": actor_or_source,
                "operation": operation,
                "idempotency_key": idempotency_key,
                "request_fingerprint": request_fingerprint,
                "request_id": request_id,
                "response_status": response_status,
                "response_payload": copy.deepcopy(response_payload),
                "created_at": _now(),
                "expires_at": None,
            },
        )

    # --- requests + drafts -------------------------------------------------------

    def create_request(
        self, *, request: dict, draft: dict, event: dict
    ) -> dict[str, Any]:
        rid = request["id"]
        req = dict(request)
        self._requests[rid] = req
        self._drafts[rid] = dict(draft)
        self._append_event(rid, event)
        return self.get_request(rid)

    def get_request(self, request_id: str) -> dict[str, Any] | None:
        req = self._requests.get(request_id)
        if req is None:
            return None
        out = copy.deepcopy(req)
        draft = self._drafts.get(request_id)
        if draft is not None:
            out["draft"] = copy.deepcopy(draft)
        return out

    def get_request_by_external_ref(
        self, *, source: str, external_request_id: str, external_item_id: str | None
    ) -> dict[str, Any] | None:
        for req in self._requests.values():
            if (
                req["source"] == source
                and req.get("external_request_id") == external_request_id
                and req.get("external_item_id") == external_item_id
            ):
                return self.get_request(req["id"])
        return None

    def list_requests(
        self,
        *,
        status: str | None = None,
        request_type: str | None = None,
        assignee: str | None = None,
        source: str | None = None,
        search: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        requester_subject: str | None = None,
        global_scope: bool = False,
        page: int = 1,
        page_size: int = 25,
        sort_by: str | None = None,
        sort_dir: str | None = None,
    ) -> dict[str, Any]:
        items = list(self._requests.values())
        if not global_scope:
            items = [
                r
                for r in items
                if r["requester_subject"] == requester_subject
                or r.get("assigned_to_subject") == requester_subject
            ]
        if status:
            items = [r for r in items if r["status"] == status]
        if request_type:
            items = [r for r in items if r["request_type"] == request_type]
        if assignee:
            items = [
                r for r in items if r.get("assigned_to_subject") == assignee
            ]
        if source:
            items = [r for r in items if r["source"] == source]
        if search:
            needle = search.strip().lower()
            items = [
                r
                for r in items
                if needle in (r.get("official_product_code") or "").lower()
                or needle in r["id"].lower()
                or needle
                in str(r["requested_payload"].get("description", "")).lower()
            ]
        if date_from:
            items = [r for r in items if r["created_at"] >= date_from]
        if date_to:
            items = [r for r in items if r["created_at"] <= date_to]
        status_counts: dict[str, int] = {}
        for r in items:
            status_counts[r["status"]] = status_counts.get(r["status"], 0) + 1
        sort_keys = {
            "createdAt": "created_at",
            "requestType": "request_type",
            "status": "status",
            "officialCode": "official_product_code",
            "requester": "requester_display_name",
            "assignedTo": "assigned_to_subject",
            "id": "id",
        }
        col = sort_keys.get(sort_by or "", "created_at")
        items.sort(
            key=lambda r: (str(r.get(col) or ""), r["id"]),
            reverse=(sort_dir != "asc"),
        )
        total = len(items)
        start = (page - 1) * page_size
        page_items = [self._summary(r) for r in items[start : start + page_size]]
        return {
            "items": page_items,
            "page": page,
            "pageSize": page_size,
            "total": total,
            "statusCounts": status_counts,
        }

    @staticmethod
    def _summary(req: dict) -> dict[str, Any]:
        return {
            "id": req["id"],
            "requestType": req["request_type"],
            "status": req["status"],
            "requester": {
                "subject": req["requester_subject"],
                "displayName": req.get("requester_display_name"),
            },
            "source": req["source"],
            "createdAt": req["created_at"],
            "assignedTo": req.get("assigned_to_subject"),
            "assignedToDisplayName": req.get("assigned_to_display_name"),
            "officialCode": req.get("official_product_code"),
            "caseVersion": req["row_version"],
        }

    def list_events(
        self, request_id: str, page: int = 1, page_size: int = 50
    ) -> dict[str, Any]:
        self._require_request(request_id)
        events = self._events.get(request_id, [])
        total = len(events)
        start = (page - 1) * page_size
        return {
            "items": copy.deepcopy(events[start : start + page_size]),
            "page": page,
            "pageSize": page_size,
            "total": total,
        }

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
        req = self._require_request(request_id)
        self._check_cas(req, expected_version, allowed_from)
        prev = req["status"]
        req.update(set_fields)
        req["status"] = next_status
        req["row_version"] = int(req["row_version"]) + 1
        req["updated_at"] = _now()
        if next_status == "completed":
            req["completed_at"] = req["updated_at"]
        if next_status == "rejected":
            req["rejected_at"] = req["updated_at"]
        self._append_event(
            request_id,
            {
                "event_type": event_type,
                "actor_subject": actor_subject,
                "actor_display_name": actor_label,
                "actor_email": actor_email,
                "reason": reason,
                "metadata": dict(event_meta),
                "previous_status": prev,
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
        req = self._require_request(request_id)
        self._check_cas(req, expected_version, frozenset({"in_progress"}))
        draft = self._drafts[request_id]
        applied: list[dict[str, Any]] = []
        for change in changes:
            path = change["path"]
            old = draft["technical_data"].get(path)
            draft["technical_data"][path] = change["proposedValue"]
            applied.append(
                {"path": path, "before": old, "after": change["proposedValue"],
                 "reason": change["reason"]}
            )
        # changed_paths: última razão por path prevalece.
        changed = {
            item["path"]: item for item in draft.get("changed_paths", [])
        }
        for change in changes:
            changed[change["path"]] = {
                "path": change["path"],
                "reason": change["reason"],
            }
        draft["changed_paths"] = list(changed.values())
        draft["row_version"] = int(draft.get("row_version", 1)) + 1
        draft["updated_by_subject"] = actor_subject
        draft["updated_at"] = _now()
        req["row_version"] = int(req["row_version"]) + 1
        req["updated_at"] = draft["updated_at"]
        self._append_event(
            request_id,
            {
                "event_type": "draft_changed",
                "actor_subject": actor_subject,
                "actor_display_name": actor_display_name,
                "actor_email": actor_email,
                "reason": None,
                "metadata": {"changes": applied, **event_meta},
                "previous_status": req["status"],
                "next_status": req["status"],
            },
        )
        return self.get_request(request_id)

    # --- verificações -------------------------------------------------------------

    def insert_verification(
        self, *, request_id: str, verification: dict[str, Any]
    ) -> dict[str, Any]:
        self._require_request(request_id)
        row = {"id": _uuid(), "request_id": request_id, **verification}
        self._verifications.setdefault(request_id, []).append(row)
        return copy.deepcopy(row)

    def list_verifications(self, request_id: str) -> list[dict[str, Any]]:
        return copy.deepcopy(self._verifications.get(request_id, []))

    # --- records + revisions -------------------------------------------------------

    def get_record(self, record_id: str) -> dict[str, Any] | None:
        rec = self._records.get(record_id)
        return copy.deepcopy(rec) if rec else None

    def get_record_by_official_code(
        self, *, official_source: str, official_code: str
    ) -> dict[str, Any] | None:
        rid = self._record_by_key.get((official_source, official_code))
        return self.get_record(rid) if rid else None

    def list_revisions(self, record_id: str) -> list[dict[str, Any]]:
        return copy.deepcopy(self._revisions.get(record_id, []))

    def get_revision(
        self, record_id: str, revision_number: int
    ) -> dict[str, Any] | None:
        for rev in self._revisions.get(record_id, []):
            if rev["revision_number"] == revision_number:
                return copy.deepcopy(rev)
        return None

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
        req = self._require_request(request_id)
        # PRC-REF-020: conclusão a partir de in_progress (legado under_review).
        self._check_cas(
            req, expected_version, frozenset({"in_progress", "under_review"})
        )
        key = (official_source, official_code)
        record_id = self._record_by_key.get(key)
        if record_id is None:
            if base_revision not in (None, 0):
                raise PrcStaleRevisionError("stale_revision")
            record = {
                "id": _uuid(),
                "product_type": req["product_type"],
                "official_product_code": official_code,
                "current_revision_number": 0,
                "last_official_verified_at": _now(),
                "official_source": official_source,
                "created_at": _now(),
                "updated_at": _now(),
            }
            record_id = record["id"]
            self._records[record_id] = record
            self._record_by_key[key] = record_id
        else:
            record = self._records[record_id]
        if base_revision is not None and base_revision != int(
            record["current_revision_number"]
        ):
            raise PrcStaleRevisionError("stale_revision")
        revision_number = int(record["current_revision_number"]) + 1
        verification_row = self.insert_verification(
            request_id=request_id, verification=verification
        )
        revision = {
            "id": _uuid(),
            "record_id": record_id,
            "revision_number": revision_number,
            "request_id": request_id,
            "schema_version": 1,
            "technical_snapshot": copy.deepcopy(revision_snapshot),
            "changes": copy.deepcopy(revision_changes),
            "official_evidence_id": verification_row["id"],
            "approved_by_subject": actor_subject,
            "approved_at": _now(),
            "created_at": _now(),
        }
        self._revisions.setdefault(record_id, []).append(revision)
        record["current_revision_number"] = revision_number
        record["last_official_verified_at"] = revision["approved_at"]
        record["updated_at"] = revision["approved_at"]
        prev = req["status"]
        req["status"] = "completed"
        req["row_version"] = int(req["row_version"]) + 1
        req["completed_at"] = _now()
        req["updated_at"] = req["completed_at"]
        req["completed_record_id"] = record_id
        req["official_product_code"] = official_code
        self._append_event(
            request_id,
            {
                "event_type": "completed",
                "actor_subject": actor_subject,
                "actor_display_name": actor_display_name,
                "actor_email": actor_email,
                "reason": reason,
                "metadata": {
                    "official_code": official_code,
                    "record_id": record_id,
                    "revision_number": revision_number,
                    "verification_id": verification_row["id"],
                    "action": "complete",
                    **event_meta,
                },
                "previous_status": prev,
                "next_status": "completed",
            },
        )
        return {
            "request": self.get_request(request_id),
            "record": copy.deepcopy(record),
            "revision": copy.deepcopy(revision),
            "verification": verification_row,
        }

    # --- attendance flags (D16 / D16-REF-01) -----------------------------------

    def create_flag(
        self, *, flag: dict[str, Any], event: dict[str, Any]
    ) -> dict[str, Any]:
        self._require_request(flag["request_id"])
        target_key = flag.get("target_key")
        if target_key and any(
            f["request_id"] == flag["request_id"]
            and f.get("target_key") == target_key
            and f["status"] == "OPEN"
            and not f.get("deleted_at")
            for f in self._flags.values()
        ):
            raise PrcStateConflictError("open_flag_exists")
        row = dict(flag)
        self._flags[row["id"]] = row
        self._append_event(row["request_id"], event)
        return copy.deepcopy(row)

    def get_flag(
        self, *, request_id: str, flag_id: str, include_deleted: bool = False
    ) -> dict[str, Any] | None:
        self._require_request(request_id)
        row = self._flags.get(flag_id)
        if row is None or row["request_id"] != request_id:
            return None
        if row.get("deleted_at") and not include_deleted:
            return None
        return copy.deepcopy(row)

    def find_open_flag_by_target(
        self, *, request_id: str, target_key: str
    ) -> dict[str, Any] | None:
        for f in self._flags.values():
            if (
                f["request_id"] == request_id
                and f.get("target_key") == target_key
                and f["status"] == "OPEN"
                and not f.get("deleted_at")
            ):
                return copy.deepcopy(f)
        return None

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
        self._require_request(request_id)
        items = [
            copy.deepcopy(f)
            for f in self._flags.values()
            if f["request_id"] == request_id and not f.get("deleted_at")
        ]
        if status:
            items = [f for f in items if f["status"] == status]
        if subject:
            items = [f for f in items if f["subject"] == subject]
        if target_path:
            items = [f for f in items if f.get("target_path") == target_path]
        if target_attribute:
            items = [
                f for f in items
                if f.get("target_attribute") == target_attribute
            ]
        if supplier_code:
            items = [
                f for f in items
                if (f.get("supplier_key") or {}).get("supplierCode")
                == supplier_code
            ]
        if store:
            items = [
                f for f in items
                if (f.get("supplier_key") or {}).get("store") == store
            ]
        items.sort(key=lambda f: (f["created_at"], f["id"]), reverse=True)
        open_count = sum(
            1
            for f in self._flags.values()
            if f["request_id"] == request_id
            and not f.get("deleted_at")
            and f["status"] == "OPEN"
        )
        resolved_count = sum(
            1
            for f in self._flags.values()
            if f["request_id"] == request_id
            and not f.get("deleted_at")
            and f["status"] == "RESOLVED"
        )
        total = len(items)
        start = (page - 1) * page_size
        return {
            "items": items[start : start + page_size],
            "page": page,
            "pageSize": page_size,
            "total": total,
            "openCount": open_count,
            "resolvedCount": resolved_count,
            "hasMore": start + page_size < total,
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
        allowed = None if global_scope else set(accessible_request_ids or [])
        items = []
        for f in self._flags.values():
            if f.get("deleted_at"):
                continue
            if allowed is not None and f["request_id"] not in allowed:
                continue
            if request_id and f["request_id"] != request_id:
                continue
            if status and f["status"] != status:
                continue
            if subject and f["subject"] != subject:
                continue
            if target_path and f.get("target_path") != target_path:
                continue
            if (
                target_attribute
                and f.get("target_attribute") != target_attribute
            ):
                continue
            if supplier_code and (f.get("supplier_key") or {}).get(
                "supplierCode"
            ) != supplier_code:
                continue
            if store and (f.get("supplier_key") or {}).get("store") != store:
                continue
            req = self._requests.get(f["request_id"]) or {}
            if product_code and req.get("official_product_code") != product_code:
                continue
            if request_type and req.get("request_type") != request_type:
                continue
            if request_status and req.get("status") != request_status:
                continue
            if assignee and req.get("assigned_to_subject") != assignee:
                continue
            item = copy.deepcopy(f)
            item["product_code"] = req.get("official_product_code")
            item["request_type"] = req.get("request_type")
            item["request_status"] = req.get("status")
            item["assigned_to_subject"] = req.get("assigned_to_subject")
            item["product_description"] = None
            items.append(item)
        items.sort(key=lambda x: (x["created_at"], x["id"]), reverse=True)
        open_count = sum(1 for i in items if i["status"] == "OPEN")
        resolved_count = sum(1 for i in items if i["status"] == "RESOLVED")
        distinct_req = len({i["request_id"] for i in items})
        distinct_prod = len({
            i["product_code"] for i in items
            if i.get("product_code")
        })
        total = len(items)
        start = (page - 1) * page_size
        return {
            "items": items[start : start + page_size],
            "page": page,
            "pageSize": page_size,
            "total": total,
            "openCount": open_count,
            "resolvedCount": resolved_count,
            "distinctRequestCount": distinct_req,
            "distinctProductCount": distinct_prod,
            "hasMore": start + page_size < total,
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
        listed = self.list_flags_cross_case(
            accessible_request_ids=accessible_request_ids,
            global_scope=global_scope,
            status=status,
            subject=subject,
            target_path=target_path,
            target_attribute=target_attribute,
            product_code=product_code,
            request_status=request_status,
            page=1,
            page_size=10_000,
        )
        key_fn = {
            "request": lambda i: i["request_id"],
            "product": lambda i: i.get("product_code"),
            "targetPath": lambda i: i.get("target_path"),
            "subject": lambda i: i.get("subject"),
            "targetAttribute": lambda i: i.get("target_attribute"),
        }.get(group_by)
        if key_fn is None:
            raise PrcRepositoryError("groupBy inválido")
        buckets: dict[str, dict[str, Any]] = {}
        for item in listed["items"]:
            key = key_fn(item)
            if key is None or key == "":
                continue
            key_s = str(key)
            bucket = buckets.setdefault(
                key_s,
                {
                    "key": key_s,
                    "flagCount": 0,
                    "openCount": 0,
                    "resolvedCount": 0,
                    "request_ids": set(),
                    "lastCreatedAt": item.get("created_at"),
                },
            )
            bucket["flagCount"] += 1
            if item["status"] == "OPEN":
                bucket["openCount"] += 1
            if item["status"] == "RESOLVED":
                bucket["resolvedCount"] += 1
            bucket["request_ids"].add(item["request_id"])
            if str(item.get("created_at") or "") > str(
                bucket.get("lastCreatedAt") or ""
            ):
                bucket["lastCreatedAt"] = item.get("created_at")
        rows = sorted(
            buckets.values(),
            key=lambda b: (-b["openCount"], -b["flagCount"], b["key"]),
        )
        total = len(rows)
        start = (page - 1) * page_size
        page_rows = rows[start : start + page_size]
        return {
            "groupBy": group_by,
            "items": [
                {
                    "key": r["key"],
                    "flagCount": r["flagCount"],
                    "openCount": r["openCount"],
                    "resolvedCount": r["resolvedCount"],
                    "requestCount": len(r["request_ids"]),
                    "lastCreatedAt": r["lastCreatedAt"],
                }
                for r in page_rows
            ],
            "page": page,
            "pageSize": page_size,
            "total": total,
            "openCount": listed["openCount"],
            "resolvedCount": listed["resolvedCount"],
            "distinctRequestCount": listed["distinctRequestCount"],
            "distinctProductCount": listed["distinctProductCount"],
            "hasMore": start + page_size < total,
        }

    def _require_flag_cas(
        self, request_id: str, flag_id: str, expected_version: int
    ) -> dict:
        row = self._flags.get(flag_id)
        if row is None or row["request_id"] != request_id or row.get("deleted_at"):
            raise PrcNotFoundError("flag", flag_id)
        if int(row["row_version"]) != int(expected_version):
            raise PrcConcurrencyError("stale_version")
        return row

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
        row = self._require_flag_cas(request_id, flag_id, expected_version)
        before = copy.deepcopy(row)
        if "title" in patch:
            row["title"] = patch["title"]
        if "description" in patch:
            row["description"] = patch["description"]
        row["row_version"] = int(row["row_version"]) + 1
        row["updated_by_subject"] = actor_subject
        row["updated_by_display_name"] = actor_display_name
        row["updated_at"] = _now()
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
        self._append_event(request_id, event)
        return copy.deepcopy(row)

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
        row = self._require_flag_cas(request_id, flag_id, expected_version)
        prev = row["status"]
        if prev == next_status:
            raise PrcStateConflictError("state_conflict")
        if next_status == "RESOLVED" and prev != "OPEN":
            raise PrcStateConflictError("state_conflict")
        if next_status == "OPEN" and prev != "RESOLVED":
            raise PrcStateConflictError("state_conflict")
        if next_status == "OPEN":
            conflict = self.find_open_flag_by_target(
                request_id=request_id,
                target_key=row.get("target_key") or "",
            )
            if conflict is not None and conflict["id"] != flag_id:
                raise PrcStateConflictError("open_flag_exists")
        row["status"] = next_status
        row["row_version"] = int(row["row_version"]) + 1
        row["updated_by_subject"] = actor_subject
        row["updated_by_display_name"] = actor_display_name
        row["updated_at"] = _now()
        if next_status == "RESOLVED":
            row["resolved_by_subject"] = actor_subject
            row["resolved_by_display_name"] = actor_display_name
            row["resolved_at"] = row["updated_at"]
        else:
            row["resolved_by_subject"] = None
            row["resolved_by_display_name"] = None
            row["resolved_at"] = None
        event = {
            **event,
            "previous_status": prev,
            "next_status": next_status,
        }
        self._append_event(request_id, event)
        return copy.deepcopy(row)

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
        row = self._require_flag_cas(request_id, flag_id, expected_version)
        row["deleted_by_subject"] = actor_subject
        row["deleted_by_display_name"] = actor_display_name
        row["deleted_at"] = _now()
        row["row_version"] = int(row["row_version"]) + 1
        row["updated_by_subject"] = actor_subject
        row["updated_by_display_name"] = actor_display_name
        row["updated_at"] = row["deleted_at"]
        self._append_event(request_id, event)
        return copy.deepcopy(row)

    # --- information rounds (PRC-REF-019) --------------------------------------

    _INFO_OPEN_STATUSES = ("awaiting_requester", "awaiting_review")
    _INFO_TERMINAL_QUESTION = frozenset({"accepted", "follow_up_requested"})

    def _info_questions_of(self, round_id: str) -> list[dict]:
        return sorted(
            (q for q in self._info_questions.values()
             if q["round_id"] == round_id),
            key=lambda q: q["ordinal"],
        )

    def _assemble_info_round(self, round_id: str) -> dict[str, Any]:
        rnd = copy.deepcopy(self._info_rounds[round_id])
        questions = []
        for q in self._info_questions_of(round_id):
            item = copy.deepcopy(q)
            answer = self._info_answers.get(q["id"])
            item["answer"] = copy.deepcopy(answer) if answer else None
            questions.append(item)
        rnd["questions"] = questions
        return rnd

    def _require_info_round_cas(
        self, request_id: str, round_id: str, expected_version: int,
    ) -> dict:
        rnd = self._info_rounds.get(round_id)
        if rnd is None or rnd["request_id"] != request_id:
            raise PrcNotFoundError("information_round", round_id)
        if int(rnd["row_version"]) != int(expected_version):
            raise PrcConcurrencyError("stale_version")
        return rnd

    def _insert_info_round(
        self, request_id: str, round_row: dict[str, Any],
        questions: list[dict[str, Any]],
    ) -> str:
        seq = 1 + max(
            (r["sequence"] for r in self._info_rounds.values()
             if r["request_id"] == request_id),
            default=0,
        )
        now = _now()
        round_id = round_row.get("id") or _uuid()
        self._info_rounds[round_id] = {
            "id": round_id,
            "request_id": request_id,
            "sequence": seq,
            "origin_status": round_row["origin_status"],
            "status": "awaiting_requester",
            "parent_round_id": round_row.get("parent_round_id"),
            "requested_by_subject": round_row["requested_by_subject"],
            "requested_by_display_name": round_row.get(
                "requested_by_display_name"
            ),
            "requester_subject": round_row["requester_subject"],
            "message": round_row.get("message"),
            "row_version": 1,
            "created_at": now,
            "updated_at": now,
            "resolved_at": None,
            "resolved_by_subject": None,
            "resolved_by_display_name": None,
        }
        for q in questions:
            qid = q.get("id") or _uuid()
            self._info_questions[qid] = {
                "id": qid,
                "round_id": round_id,
                "request_id": request_id,
                "ordinal": q["ordinal"],
                "target_type": q["target_type"],
                "target_path": q.get("target_path"),
                "target_attribute": q.get("target_attribute"),
                "supplier_key": copy.deepcopy(q.get("supplier_key")),
                "target_key": q["target_key"],
                "target_label": q["target_label"],
                "question_text": q["question_text"],
                "status": q.get("status") or "pending",
                "created_at": now,
                "updated_at": now,
            }
        return round_id

    def _append_info_event(
        self, request_id: str, request_status: str, event: dict[str, Any],
        extra_meta: dict[str, Any] | None = None,
    ) -> None:
        meta = {**(event.get("metadata") or {}), **(extra_meta or {})}
        self._append_event(
            request_id,
            {
                **event,
                "metadata": meta,
                "previous_status": event.get(
                    "previous_status", request_status
                ),
                "next_status": event.get("next_status", request_status),
            },
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
        """CAS do caso + transição + rodada/perguntas + evento."""
        req = self._require_request(request_id)
        self._check_cas(req, expected_version, allowed_from)
        if any(
            r["request_id"] == request_id
            and r["status"] in self._INFO_OPEN_STATUSES
            for r in self._info_rounds.values()
        ):
            raise PrcStateConflictError("information_round_open")
        prev = req["status"]
        req.update(set_fields or {})
        if next_status != prev:
            req["status"] = next_status
        req["row_version"] = int(req["row_version"]) + 1
        req["updated_at"] = _now()
        round_id = self._insert_info_round(request_id, round_row, questions)
        created = self._assemble_info_round(round_id)
        self._append_info_event(
            request_id, prev,
            {
                "event_type": event_type,
                "actor_subject": actor_subject,
                "actor_display_name": actor_label,
                "actor_email": actor_email,
                "reason": reason,
                "metadata": dict(event_meta),
                "previous_status": prev,
                "next_status": next_status,
            },
            {
                "roundId": round_id,
                "roundSequence": created["sequence"],
                "questionCount": len(questions),
            },
        )
        return {"request": self.get_request(request_id), "round": created}

    def get_information_round(
        self, *, request_id: str, round_id: str
    ) -> dict[str, Any] | None:
        rnd = self._info_rounds.get(round_id)
        if rnd is None or rnd["request_id"] != request_id:
            return None
        return self._assemble_info_round(round_id)

    def list_information_rounds(
        self, *, request_id: str
    ) -> list[dict[str, Any]]:
        rounds = sorted(
            (r for r in self._info_rounds.values()
             if r["request_id"] == request_id),
            key=lambda r: r["sequence"],
        )
        return [self._assemble_info_round(r["id"]) for r in rounds]

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
        req = self._require_request(request_id)
        rnd = self._require_info_round_cas(
            request_id, round_id, expected_round_version
        )
        if rnd["status"] != "awaiting_requester":
            raise PrcStateConflictError("state_conflict")
        question_ids = {q["id"] for q in self._info_questions_of(round_id)}
        for ans in answers:
            if str(ans["question_id"]) not in question_ids:
                raise PrcNotFoundError(
                    "information_question", str(ans["question_id"])
                )
        now = _now()
        for ans in answers:
            qid = str(ans["question_id"])
            text = str(ans.get("text") or "")
            existing = self._info_answers.get(qid)
            if existing is None:
                self._info_answers[qid] = {
                    "id": _uuid(),
                    "question_id": qid,
                    "round_id": round_id,
                    "request_id": request_id,
                    "author_subject": actor_subject,
                    "text": text,
                    "status": "draft",
                    "row_version": 1,
                    "created_at": now,
                    "updated_at": now,
                    "submitted_at": None,
                }
            else:
                existing.update(
                    text=text,
                    author_subject=actor_subject,
                    status="draft",
                    row_version=int(existing["row_version"]) + 1,
                    updated_at=now,
                )
            self._info_questions[qid]["status"] = (
                "drafted" if text.strip() else "pending"
            )
            self._info_questions[qid]["updated_at"] = now
        rnd["row_version"] = int(rnd["row_version"]) + 1
        rnd["updated_at"] = now
        self._append_info_event(
            request_id, req["status"], event,
            {"roundId": round_id, "answerCount": len(answers)},
        )
        return self._assemble_info_round(round_id)

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
        req = self._require_request(request_id)
        rnd = self._require_info_round_cas(
            request_id, round_id, expected_round_version
        )
        if rnd["status"] != "awaiting_requester":
            raise PrcStateConflictError("state_conflict")
        question_ids = [q["id"] for q in self._info_questions_of(round_id)]
        known = set(question_ids)
        texts = {
            qid: str(self._info_answers[qid]["text"] or "")
            for qid in question_ids
            if qid in self._info_answers
        }
        for ans in answers:
            qid = str(ans["question_id"])
            if qid not in known:
                raise PrcNotFoundError("information_question", qid)
            texts[qid] = str(ans.get("text") or "")
        missing = [
            qid for qid in question_ids if not texts.get(qid, "").strip()
        ]
        if missing:
            raise PrcValidationError(
                "Todas as perguntas exigem resposta antes do envio.",
                fields={f"answers[{qid}].text": "required" for qid in missing},
            )
        now = _now()
        for qid in question_ids:
            text = texts[qid].strip()
            existing = self._info_answers.get(qid)
            if existing is None:
                self._info_answers[qid] = {
                    "id": _uuid(),
                    "question_id": qid,
                    "round_id": round_id,
                    "request_id": request_id,
                    "author_subject": actor_subject,
                    "text": text,
                    "status": "submitted",
                    "row_version": 1,
                    "created_at": now,
                    "updated_at": now,
                    "submitted_at": now,
                }
            else:
                existing.update(
                    text=text,
                    author_subject=actor_subject,
                    status="submitted",
                    row_version=int(existing["row_version"]) + 1,
                    updated_at=now,
                    submitted_at=now,
                )
            self._info_questions[qid]["status"] = "submitted"
            self._info_questions[qid]["updated_at"] = now
        rnd["status"] = "awaiting_review"
        rnd["row_version"] = int(rnd["row_version"]) + 1
        rnd["updated_at"] = now
        self._append_info_event(
            request_id, req["status"], event,
            {"roundId": round_id, "answerCount": len(question_ids)},
        )
        return self._assemble_info_round(round_id)

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
        req = self._require_request(request_id)
        rnd = self._require_info_round_cas(
            request_id, round_id, expected_round_version
        )
        if rnd["status"] != "awaiting_review":
            raise PrcStateConflictError("state_conflict")
        question = self._info_questions.get(question_id)
        if question is None or question["round_id"] != round_id:
            raise PrcNotFoundError("information_question", question_id)
        if question["status"] != "submitted":
            raise PrcStateConflictError("state_conflict")
        now = _now()
        question["status"] = "accepted"
        question["updated_at"] = now
        resolved = {
            q["status"] for q in self._info_questions_of(round_id)
        } <= self._INFO_TERMINAL_QUESTION
        if resolved:
            rnd["status"] = "resolved"
            rnd["resolved_at"] = now
            rnd["resolved_by_subject"] = actor_subject
            rnd["resolved_by_display_name"] = actor_display_name
        rnd["row_version"] = int(rnd["row_version"]) + 1
        rnd["updated_at"] = now
        self._append_info_event(
            request_id, req["status"], event,
            {
                "roundId": round_id,
                "questionId": question_id,
                "roundResolved": resolved,
            },
        )
        return self._assemble_info_round(round_id)

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
        req = self._require_request(request_id)
        parent = self._require_info_round_cas(
            request_id, parent_round_id, expected_parent_version
        )
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
        for qid in target_ids:
            question = self._info_questions.get(qid)
            if question is None or question["round_id"] != parent_round_id:
                raise PrcNotFoundError("information_question", qid)
            if question["status"] != "submitted":
                raise PrcStateConflictError("state_conflict")
        now = _now()
        for qid in target_ids:
            self._info_questions[qid]["status"] = "follow_up_requested"
            self._info_questions[qid]["updated_at"] = now
        parent_resolved = {
            q["status"] for q in self._info_questions_of(parent_round_id)
        } <= self._INFO_TERMINAL_QUESTION
        if parent_resolved:
            parent["status"] = "resolved"
            parent["resolved_at"] = now
            parent["resolved_by_subject"] = actor_subject
            parent["resolved_by_display_name"] = actor_label
        parent["row_version"] = int(parent["row_version"]) + 1
        parent["updated_at"] = now
        new_id = self._insert_info_round(
            request_id,
            {**round_row, "parent_round_id": parent_round_id},
            questions,
        )
        created = self._assemble_info_round(new_id)
        self._append_info_event(
            request_id, req["status"],
            {
                **event,
                "actor_subject": actor_subject,
                "actor_display_name": (
                    event.get("actor_display_name") or actor_label
                ),
                "actor_email": event.get("actor_email") or actor_email,
            },
            {
                "parentRoundId": parent_round_id,
                "roundId": new_id,
                "roundSequence": created["sequence"],
                "followUpQuestionIds": target_ids,
                "parentResolved": parent_resolved,
                "questionCount": len(questions),
            },
        )
        return {
            "parentRound": self._assemble_info_round(parent_round_id),
            "round": created,
        }


    def resolve_open_information_rounds(
        self,
        *,
        request_id: str,
        actor_subject: str,
        actor_display_name: str | None,
        event: dict[str, Any],
    ) -> list[dict[str, Any]]:
        self._require_request(request_id)
        now = _now()
        resolved: list[dict] = []
        for rnd in self._info_rounds.values():
            if rnd["request_id"] != request_id:
                continue
            if rnd["status"] not in ("awaiting_requester", "awaiting_review"):
                continue
            rnd["status"] = "resolved"
            rnd["row_version"] = int(rnd["row_version"]) + 1
            rnd["updated_at"] = now
            rnd["resolved_at"] = now
            rnd["resolved_by_subject"] = actor_subject
            rnd["resolved_by_display_name"] = actor_display_name
            resolved.append(copy.deepcopy(self.get_information_round(
                request_id=request_id, round_id=rnd["id"]
            )))
        if resolved:
            meta = dict(event.get("metadata") or {})
            meta["resolvedRoundIds"] = [r["id"] for r in resolved]
            meta["waiver"] = True
            self._append_event(request_id, {**event, "metadata": meta})
        return resolved
