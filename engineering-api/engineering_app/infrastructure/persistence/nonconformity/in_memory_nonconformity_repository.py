"""Adapter sintético NC — mesma semântica do Postgres, sem banco.

Ativado por ``ENG_NC_REPOSITORY=memory`` (dev/testes). Nunca é default:
a composição sem env explícita retorna repositório ``unavailable``
( fail-honest — dados sintéticos jamais fingem ser oficiais).
"""

from __future__ import annotations

import threading
import uuid
from datetime import date, datetime, timezone
from typing import Any

from engineering_app.domain.nonconformity.errors import (
    NcConcurrencyError,
    NcValidationError,
)
from engineering_app.domain.nonconformity.history_diff import (
    build_nc_history_changes,
)
from engineering_app.domain.nonconformity.models import NcActor
from engineering_app.domain.nonconformity.normalize import (
    normalize_problem_tag_labels,
    normalize_products,
)
from engineering_app.domain.nonconformity.sort import resolve_nc_sort

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: Any) -> str | None:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if value is None:
        return None
    return str(value)


def _blank(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


class InMemoryNonconformityRepository:
    """Implementa ``NonconformityRepository`` com estado em processo."""

    def __init__(self, *, seed: list[dict[str, Any]] | None = None) -> None:
        self._lock = threading.RLock()
        self._records: dict[str, dict[str, Any]] = {}
        self._history: dict[str, list[dict[str, Any]]] = {}
        self._tag_catalog: dict[str, str] = {}  # label_ci → label
        self._idempotency_index: dict[str, str] = {}  # key → record_id
        if seed:
            for item in seed:
                fields = dict(item)
                record = self.create_record(
                    status=fields.pop("status", "open"),
                    actor=fields.pop("actor", NcActor(label="seed")),
                    **fields,
                )
                self._idempotency_index.clear()
                rid = record["id"]
                for event in self._history.get(rid, []):
                    event["actor_user_id"] = "seed"

    # ---------------------------------------------------------- reads

    def list_records(
        self,
        *,
        status: str | None = None,
        sale_number: str | None = None,
        lmp_number: str | None = None,
        customer_name: str | None = None,
        product_code: str | None = None,
        problem_tag: str | None = None,
        date_start: str | None = None,
        date_end: str | None = None,
        sort_by: str | None = None,
        sort_dir: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        with self._lock:
            rows = list(self._records.values())
        rows = [
            row
            for row in rows
            if _matches(
                row,
                status=status,
                sale_number=sale_number,
                lmp_number=lmp_number,
                customer_name=customer_name,
                product_code=product_code,
                problem_tag=problem_tag,
                date_start=date_start,
                date_end=date_end,
            )
        ]
        key, direction = resolve_nc_sort(sort_by, sort_dir)
        rows.sort(key=lambda r: _sort_key(r, key), reverse=(direction == "desc"))
        total = len(rows)
        page = max(1, int(page))
        page_size = max(1, min(int(page_size), 200))
        offset = (page - 1) * page_size
        items = [self._to_payload(row, include_products=True) for row in rows[offset : offset + page_size]]
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "sort_by": key,
            "sort_dir": direction,
        }

    def get_record(self, record_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._records.get(str(record_id))
            if row is None:
                return None
            return self._to_payload(row, include_products=True)

    def export_records(self) -> list[dict[str, Any]]:
        with self._lock:
            rows = sorted(
                self._records.values(),
                key=lambda r: (str(r.get("registered_at") or ""), str(r["id"])),
            )
            return [
                self._to_payload(row, include_products=True) for row in rows
            ]

    def list_history(self, record_id: str) -> list[dict[str, Any]] | None:
        with self._lock:
            if str(record_id) not in self._records:
                return None
            events = list(self._history.get(str(record_id), []))
        events.sort(key=lambda e: str(e.get("created_at") or ""), reverse=True)
        return events[:200]

    def list_problem_tag_catalog(self) -> list[dict[str, Any]]:
        with self._lock:
            usage: dict[str, int] = {}
            for row in self._records.values():
                for label in row.get("problem_tags") or []:
                    usage[label.casefold()] = usage.get(label.casefold(), 0) + 1
            out = []
            for key, label in self._tag_catalog.items():
                out.append(
                    {
                        "id": key,
                        "label": label,
                        "usage_count": usage.get(key, 0),
                    }
                )
            out.sort(key=lambda item: item["label"])
            return out

    def list_occurrence_dates(self) -> list[date]:
        with self._lock:
            dates = {
                row["occurrence_date"]
                for row in self._records.values()
                if isinstance(row.get("occurrence_date"), date)
            }
        return sorted(dates)

    def find_import_duplicate(
        self,
        *,
        sale_number: str | None,
        defect_description: str | None,
        problem_tags: list[str] | None,
    ) -> dict[str, Any] | None:
        sale = (sale_number or "").strip()
        defect = (defect_description or "").strip()
        wanted = {
            str(tag).strip().casefold()
            for tag in (problem_tags or [])
            if str(tag).strip()
        }
        if not sale and not defect and not wanted:
            return None
        with self._lock:
            for row in self._records.values():
                if (row.get("sale_number") or "") != sale:
                    continue
                if (row.get("defect_description") or "") != defect:
                    continue
                existing = {t.casefold() for t in (row.get("problem_tags") or [])}
                if existing == wanted:
                    return self._to_payload(row, include_products=True)
        return None

    # --------------------------------------------------------- writes

    def create_record(
        self,
        *,
        status: str = "open",
        sale_number: str | None = None,
        lmp_number: str | None = None,
        customer_name: str | None = None,
        occurrence_date: str | None = None,
        launch_date: str | None = None,
        last_revision_date: str | None = None,
        executed_by: str | None = None,
        released_by: str | None = None,
        defect_description: str | None = None,
        corrective_actions: str | None = None,
        technical_opinion: str | None = None,
        products: list[dict[str, Any]] | None = None,
        problem_tags: list[str] | None = None,
        registered_at: str | None = None,
        actor: NcActor,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        status_norm = (status or "open").strip().lower()
        if status_norm not in {"open", "in_progress", "done"}:
            raise NcValidationError(f"Status inválido: {status}")

        with self._lock:
            if idempotency_key:
                existing_id = self._idempotency_index.get(idempotency_key)
                if existing_id and existing_id in self._records:
                    return self._to_payload(
                        self._records[existing_id], include_products=True
                    )
                duplicate = self.find_import_duplicate(
                    sale_number=sale_number,
                    defect_description=defect_description,
                    problem_tags=problem_tags,
                )
                if duplicate is not None:
                    self._idempotency_index[idempotency_key] = duplicate["id"]
                    return duplicate

            record_id = str(uuid.uuid4())
            occurred = _parse_date(occurrence_date) or date.today()
            registered = _parse_datetime(registered_at) or _now()
            tags = normalize_problem_tag_labels(problem_tags)
            for label in tags:
                self._tag_catalog.setdefault(label.casefold(), label)
            row = {
                "id": record_id,
                "registered_at": registered,
                "occurrence_date": occurred,
                "sale_number": _blank(sale_number),
                "lmp_number": _blank(lmp_number),
                "customer_name": _blank(customer_name),
                "launch_date": _parse_date(launch_date),
                "last_revision_date": _parse_date(last_revision_date),
                "executed_by": _blank(executed_by),
                "released_by": _blank(released_by),
                "status": status_norm,
                "defect_description": _blank(defect_description),
                "corrective_actions": _blank(corrective_actions),
                "technical_opinion": _blank(technical_opinion),
                "problem_tags": tags,
                "products": normalize_products(products),
                "created_by": actor.label,
                "updated_by": actor.label,
                "created_at": _now(),
                "updated_at": _now(),
            }
            self._records[record_id] = row
            self._history.setdefault(record_id, [])
            self._append_history(
                record_id,
                event_type="created",
                changes=build_nc_history_changes(None, _snapshot(row)),
                actor=actor,
            )
            if idempotency_key:
                self._idempotency_index[idempotency_key] = record_id
            return self._to_payload(row, include_products=True)

    def update_record(
        self,
        *,
        record_id: str,
        status: str,
        actor: NcActor,
        expected_updated_at: str | None = None,
        **fields: Any,
    ) -> dict[str, Any] | None:
        status_norm = (status or "").strip().lower()
        if status_norm not in {"open", "in_progress", "done"}:
            raise NcValidationError(f"Status inválido: {status}")
        occurred = _parse_date(fields.get("occurrence_date"))
        if occurred is None:
            raise NcValidationError("occurrence_date é obrigatória.")

        with self._lock:
            row = self._records.get(str(record_id))
            if row is None:
                return None
            if expected_updated_at is not None:
                current = _iso(row.get("updated_at"))
                if current != expected_updated_at:
                    raise NcConcurrencyError(
                        "Registro alterado por outro processo (updated_at)."
                    )
            before = _snapshot(row)
            tags = normalize_problem_tag_labels(fields.get("problem_tags"))
            for label in tags:
                self._tag_catalog.setdefault(label.casefold(), label)
            row.update(
                {
                    "sale_number": _blank(fields.get("sale_number")),
                    "lmp_number": _blank(fields.get("lmp_number")),
                    "customer_name": _blank(fields.get("customer_name")),
                    "occurrence_date": occurred,
                    "launch_date": _parse_date(fields.get("launch_date")),
                    "last_revision_date": _parse_date(
                        fields.get("last_revision_date")
                    ),
                    "executed_by": _blank(fields.get("executed_by")),
                    "released_by": _blank(fields.get("released_by")),
                    "status": status_norm,
                    "defect_description": _blank(fields.get("defect_description")),
                    "corrective_actions": _blank(fields.get("corrective_actions")),
                    "technical_opinion": _blank(fields.get("technical_opinion")),
                    "problem_tags": tags,
                    "products": normalize_products(fields.get("products")),
                    "updated_by": actor.label,
                    "updated_at": _now(),
                }
            )
            changes = build_nc_history_changes(before, _snapshot(row))
            if changes.get("fields"):
                self._append_history(
                    str(record_id),
                    event_type="updated",
                    changes=changes,
                    actor=actor,
                )
            return self._to_payload(row, include_products=True)

    def delete_record(self, record_id: str) -> bool:
        with self._lock:
            removed = self._records.pop(str(record_id), None)
            self._history.pop(str(record_id), None)
            return removed is not None

    def delete_all_records(self) -> int:
        with self._lock:
            count = len(self._records)
            self._records.clear()
            self._history.clear()
            self._idempotency_index.clear()
            return count

    # -------------------------------------------------------- internal

    def _append_history(
        self,
        record_id: str,
        *,
        event_type: str,
        changes: dict[str, Any],
        actor: NcActor,
    ) -> None:
        self._history.setdefault(record_id, []).append(
            {
                "id": str(uuid.uuid4()),
                "nonconformity_id": record_id,
                "event_type": event_type,
                "changes": changes,
                "actor_user_id": (actor.user_id or "unknown")[:100],
                "actor_email": actor.email,
                "actor_name": actor.name,
                "created_at": _iso(_now()),
            }
        )

    def _to_payload(
        self, row: dict[str, Any], *, include_products: bool = False
    ) -> dict[str, Any]:
        products = [
            {"product_code": p["product_code"], "product_description": p.get("product_description")}
            for p in (row.get("products") or [])
        ]
        products.sort(key=lambda p: p["product_code"])
        payload: dict[str, Any] = {
            "id": str(row["id"]),
            "registered_at": _iso(row.get("registered_at")),
            "occurrence_date": _iso(row.get("occurrence_date")),
            "sale_number": row.get("sale_number"),
            "lmp_number": row.get("lmp_number"),
            "customer_name": row.get("customer_name"),
            "launch_date": _iso(row.get("launch_date")),
            "last_revision_date": _iso(row.get("last_revision_date")),
            "executed_by": row.get("executed_by"),
            "released_by": row.get("released_by"),
            "status": row.get("status"),
            "defect_description": row.get("defect_description"),
            "problem_tags": sorted(
                row.get("problem_tags") or [], key=str.casefold
            ),
            "corrective_actions": row.get("corrective_actions"),
            "technical_opinion": row.get("technical_opinion"),
            "created_by": row.get("created_by"),
            "updated_by": row.get("updated_by"),
            "created_at": _iso(row.get("created_at")),
            "updated_at": _iso(row.get("updated_at")),
        }
        if include_products:
            payload["products"] = products
            payload["product_codes"] = [p["product_code"] for p in products]
        return payload


def _matches(
    row: dict[str, Any],
    *,
    status: str | None,
    sale_number: str | None,
    lmp_number: str | None,
    customer_name: str | None,
    product_code: str | None,
    problem_tag: str | None,
    date_start: str | None,
    date_end: str | None,
) -> bool:
    if status and row.get("status") != status:
        return False
    if sale_number and sale_number.strip().casefold() not in (row.get("sale_number") or "").casefold():
        return False
    if lmp_number and lmp_number.strip().casefold() not in (row.get("lmp_number") or "").casefold():
        return False
    if customer_name and customer_name.strip().casefold() not in (row.get("customer_name") or "").casefold():
        return False
    if product_code:
        needle = product_code.strip().casefold()
        codes = [
            p.get("product_code", "").casefold() for p in (row.get("products") or [])
        ]
        if not any(needle in code for code in codes):
            return False
    if problem_tag:
        needle = problem_tag.strip().casefold()
        labels = [t.casefold() for t in (row.get("problem_tags") or [])]
        if not any(needle in label for label in labels):
            return False
    occurred = row.get("occurrence_date")
    occurred_iso = _iso(occurred) or ""
    if date_start and occurred_iso < str(date_start)[:10]:
        return False
    if date_end and occurred_iso > str(date_end)[:10]:
        return False
    return True


def _sort_key(row: dict[str, Any], key: str) -> Any:
    if key == "problem_tags":
        return ", ".join(sorted(row.get("problem_tags") or []))
    if key == "products":
        return ", ".join(
            sorted(p.get("product_code", "") for p in (row.get("products") or []))
        )
    value = row.get(key)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return "" if value is None else str(value)


def _snapshot(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": row.get("status"),
        "sale_number": row.get("sale_number"),
        "lmp_number": row.get("lmp_number"),
        "customer_name": row.get("customer_name"),
        "occurrence_date": _iso(row.get("occurrence_date")),
        "launch_date": _iso(row.get("launch_date")),
        "last_revision_date": _iso(row.get("last_revision_date")),
        "executed_by": row.get("executed_by"),
        "released_by": row.get("released_by"),
        "defect_description": row.get("defect_description"),
        "corrective_actions": row.get("corrective_actions"),
        "technical_opinion": row.get("technical_opinion"),
        "problem_tags": list(row.get("problem_tags") or []),
        "products": normalize_products(row.get("products")),
    }


def _parse_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()[:10]
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None
