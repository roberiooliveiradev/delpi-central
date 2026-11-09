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
        self._check_cas(
            req, expected_version, frozenset({"under_review"})
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
                "event_type": "verify_and_complete",
                "actor_subject": actor_subject,
                "actor_display_name": actor_display_name,
                "actor_email": actor_email,
                "reason": reason,
                "metadata": {
                    "official_code": official_code,
                    "record_id": record_id,
                    "revision_number": revision_number,
                    "verification_id": verification_row["id"],
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
