from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, timezone
from typing import Any
from uuid import uuid4

SEEDED_CATEGORIES = [
    {"id": "lodging", "label": "Hospedagem", "sortOrder": 10, "active": True},
    {"id": "meals", "label": "Alimentação", "sortOrder": 20, "active": True},
    {"id": "fuel", "label": "Combustível", "sortOrder": 30, "active": True},
    {"id": "ground_transport", "label": "Deslocamento", "sortOrder": 40, "active": True},
    {"id": "air_transport", "label": "Aéreo", "sortOrder": 50, "active": True},
    {"id": "toll", "label": "Pedágio", "sortOrder": 60, "active": True},
    {"id": "parking", "label": "Estacionamento", "sortOrder": 70, "active": True},
    {"id": "communication", "label": "Comunicação", "sortOrder": 80, "active": True},
    {"id": "other", "label": "Outros", "sortOrder": 90, "active": True},
]


def _now() -> datetime:
    return datetime.now(timezone.utc)


class InMemoryTravelReportRepository:
    def __init__(self) -> None:
        self.categories = deepcopy(SEEDED_CATEGORIES)
        self.sequences: dict[tuple[str, int], int] = {}
        self.reports: dict[str, dict[str, Any]] = {}
        self.expenses: dict[str, dict[str, Any]] = {}
        self.receipts: dict[str, dict[str, Any]] = {}
        self.audit: list[dict[str, Any]] = []

    def list_categories(self) -> list[dict[str, Any]]:
        return [item for item in self.categories if item["active"]]

    def next_report_number(self, *, unit_code: str, year: int) -> str:
        key = (unit_code, year)
        self.sequences[key] = self.sequences.get(key, 0) + 1
        return f"TE-{year}-{self.sequences[key]:04d}"

    def create_report(self, payload: dict[str, Any]) -> dict[str, Any]:
        report_id = payload.get("id") or str(uuid4())
        now = _now()
        row = {
            "id": report_id,
            "number": payload["number"],
            "unitCode": payload["unit_code"],
            "ownerUserId": payload["owner_user_id"],
            "createdByName": payload.get("created_by_name"),
            "createdByEmail": payload.get("created_by_email"),
            "destination": payload.get("destination") or "",
            "purpose": payload.get("purpose") or "",
            "periodStart": payload.get("period_start"),
            "periodEnd": payload.get("period_end"),
            "costCenterCode": payload.get("cost_center_code"),
            "costCenterLabel": payload.get("cost_center_label"),
            "status": payload.get("status") or "draft",
            "totalAmountBrl": float(payload.get("total_amount_brl") or 0),
            "pixKeyType": payload.get("pix_key_type"),
            "pixKeyValue": payload.get("pix_key_value"),
            "createdAt": now,
            "updatedAt": now,
        }
        self.reports[report_id] = row
        return deepcopy(row)

    def get_report(self, report_id: str) -> dict[str, Any] | None:
        row = self.reports.get(report_id)
        return deepcopy(row) if row else None

    def list_reports(
        self,
        *,
        unit_codes: list[str],
        owner_user_id: str | None,
        query: str | None = None,
        period_from: date | None = None,
        period_to: date | None = None,
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for row in self.reports.values():
            if row["unitCode"] not in unit_codes:
                continue
            if owner_user_id and row["ownerUserId"] != owner_user_id:
                continue
            if query:
                hay = f"{row['number']} {row['destination']} {row.get('createdByName') or ''}".lower()
                if query.lower() not in hay:
                    continue
            start = row.get("periodStart")
            if period_from and start and start < period_from:
                continue
            end = row.get("periodEnd")
            if period_to and end and end > period_to:
                continue
            item = deepcopy(row)
            item["expenseCount"] = sum(1 for exp in self.expenses.values() if exp["reportId"] == row["id"])
            item["missingReceiptCount"] = sum(
                1
                for exp in self.expenses.values()
                if exp["reportId"] == row["id"]
                and not any(rec["expenseId"] == exp["id"] for rec in self.receipts.values())
            )
            items.append(item)
        items.sort(key=lambda row: row["updatedAt"], reverse=True)
        return items

    def update_report(self, report_id: str, changes: dict[str, Any]) -> dict[str, Any] | None:
        row = self.reports.get(report_id)
        if not row:
            return None
        mapping = {
            "destination": "destination",
            "purpose": "purpose",
            "period_start": "periodStart",
            "period_end": "periodEnd",
            "cost_center_code": "costCenterCode",
            "cost_center_label": "costCenterLabel",
            "status": "status",
            "total_amount_brl": "totalAmountBrl",
            "pix_key_type": "pixKeyType",
            "pix_key_value": "pixKeyValue",
        }
        for key, camel in mapping.items():
            if key in changes:
                row[camel] = changes[key]
        row["updatedAt"] = _now()
        return deepcopy(row)

    def delete_report(self, report_id: str) -> bool:
        if report_id not in self.reports:
            return False
        expense_ids = [eid for eid, exp in self.expenses.items() if exp["reportId"] == report_id]
        for eid in expense_ids:
            self.receipts = {rid: rec for rid, rec in self.receipts.items() if rec["expenseId"] != eid}
            self.expenses.pop(eid, None)
        self.audit = [event for event in self.audit if event["reportId"] != report_id]
        self.reports.pop(report_id)
        return True

    def refresh_total(self, report_id: str) -> float:
        total = sum(float(exp["amountBrl"]) for exp in self.expenses.values() if exp["reportId"] == report_id)
        if report_id in self.reports:
            self.reports[report_id]["totalAmountBrl"] = total
            self.reports[report_id]["updatedAt"] = _now()
        return total

    def create_expense(self, payload: dict[str, Any]) -> dict[str, Any]:
        expense_id = payload.get("id") or str(uuid4())
        now = _now()
        row = {
            "id": expense_id,
            "reportId": payload["report_id"],
            "expenseDate": payload["expense_date"],
            "categoryId": payload["category_id"],
            "merchant": payload.get("merchant") or "",
            "amountBrl": float(payload["amount_brl"]),
            "notes": payload.get("notes") or "",
            "sortOrder": int(payload.get("sort_order") or 0),
            "createdAt": now,
            "updatedAt": now,
            "receipts": [],
        }
        self.expenses[expense_id] = row
        self.refresh_total(payload["report_id"])
        return deepcopy(row)

    def get_expense(self, expense_id: str) -> dict[str, Any] | None:
        row = self.expenses.get(expense_id)
        if not row:
            return None
        item = deepcopy(row)
        item["receipts"] = [
            deepcopy(rec) for rec in self.receipts.values() if rec["expenseId"] == expense_id
        ]
        return item

    def list_expenses(self, report_id: str) -> list[dict[str, Any]]:
        items = []
        for row in self.expenses.values():
            if row["reportId"] != report_id:
                continue
            item = deepcopy(row)
            item["receipts"] = [
                deepcopy(rec) for rec in self.receipts.values() if rec["expenseId"] == row["id"]
            ]
            items.append(item)
        items.sort(key=lambda row: (row["expenseDate"] or date.min, row["sortOrder"], row["createdAt"]))
        return items

    def update_expense(self, expense_id: str, changes: dict[str, Any]) -> dict[str, Any] | None:
        row = self.expenses.get(expense_id)
        if not row:
            return None
        mapping = {
            "expense_date": "expenseDate",
            "category_id": "categoryId",
            "merchant": "merchant",
            "amount_brl": "amountBrl",
            "notes": "notes",
        }
        for key, camel in mapping.items():
            if key in changes:
                row[camel] = changes[key]
                if key == "amount_brl":
                    row[camel] = float(changes[key])
        row["updatedAt"] = _now()
        self.refresh_total(row["reportId"])
        return self.get_expense(expense_id)

    def delete_expense(self, expense_id: str) -> bool:
        row = self.expenses.get(expense_id)
        if not row:
            return False
        report_id = row["reportId"]
        self.receipts = {rid: rec for rid, rec in self.receipts.items() if rec["expenseId"] != expense_id}
        self.expenses.pop(expense_id)
        self.refresh_total(report_id)
        return True

    def create_receipt(self, payload: dict[str, Any]) -> dict[str, Any]:
        receipt_id = payload.get("id") or str(uuid4())
        row = {
            "id": receipt_id,
            "expenseId": payload["expense_id"],
            "storedName": payload["stored_name"],
            "originalName": payload["original_name"],
            "mimeType": payload["mime_type"],
            "sizeBytes": int(payload["size_bytes"]),
            "createdAt": _now(),
        }
        self.receipts[receipt_id] = row
        return deepcopy(row)

    def get_receipt(self, receipt_id: str) -> dict[str, Any] | None:
        row = self.receipts.get(receipt_id)
        return deepcopy(row) if row else None

    def delete_receipt(self, receipt_id: str) -> bool:
        return self.receipts.pop(receipt_id, None) is not None

    def add_audit(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = {
            "id": str(uuid4()),
            "reportId": payload["report_id"],
            "eventType": payload["event_type"],
            "fromStatus": payload.get("from_status"),
            "toStatus": payload.get("to_status"),
            "actorUserId": payload.get("actor_user_id"),
            "actorName": payload.get("actor_name"),
            "actorEmail": payload.get("actor_email"),
            "payload": payload.get("payload") or {},
            "createdAt": _now(),
        }
        self.audit.append(row)
        return deepcopy(row)

    def list_audit(self, report_id: str) -> list[dict[str, Any]]:
        return [deepcopy(event) for event in self.audit if event["reportId"] == report_id]
