from __future__ import annotations

from datetime import date, datetime
from typing import Any

from travel_expenses_app.application.security import travel_expenses_permissions as perms
from travel_expenses_app.application.services.package_storage import PackageStorageService
from travel_expenses_app.application.services.receipt_storage import (
    ReceiptStorageError,
    ReceiptStorageService,
)
from travel_expenses_app.core.auth_actor import actor_from_user
from travel_expenses_app.domain.services.completeness_service import (
    TravelReportCompletenessService,
)
from travel_expenses_app.domain.services.pix_key_service import normalize_pix_key
from travel_expenses_app.domain.services.status_transition_service import (
    TravelReportStatusTransitionService,
)
from travel_expenses_app.infrastructure.pdf.package_pdf_renderer import TravelPackagePdfRenderer


class TravelReportError(ValueError):
    """Domain or validation error for travel reports."""


def _parse_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def _parse_amount(value: Any) -> float:
    amount = float(value)
    if amount < 0:
        raise TravelReportError("O valor da despesa não pode ser negativo.")
    return amount


class TravelReportService:
    def __init__(
        self,
        repo,
        receipt_storage: ReceiptStorageService | None = None,
        package_storage: PackageStorageService | None = None,
        pdf_renderer: TravelPackagePdfRenderer | None = None,
    ) -> None:
        self.repo = repo
        self.receipt_storage = receipt_storage or ReceiptStorageService()
        self.package_storage = package_storage or PackageStorageService()
        self.pdf_renderer = pdf_renderer or TravelPackagePdfRenderer()

    def _with_completeness(self, report: dict[str, Any]) -> dict[str, Any]:
        expenses = self.repo.list_expenses(report["id"])
        completeness = TravelReportCompletenessService.evaluate(report, expenses)
        payload = dict(report)
        payload["expenses"] = expenses
        payload["completeness"] = completeness
        return payload

    def list_categories(self) -> list[dict[str, Any]]:
        return self.repo.list_categories()

    def _actor(self, user) -> tuple[str, str | None, str | None]:
        user_id, email, name = actor_from_user(user)
        if not user_id:
            raise PermissionError("Usuário não identificado.")
        return user_id, email, name

    def _load_visible(self, user, report_id: str) -> dict[str, Any]:
        report = self.repo.get_report(report_id)
        if not report:
            raise TravelReportError("Prestação não encontrada.")
        perms.assert_unit_action(user, "view", report["unitCode"])
        user_id, _, _ = self._actor(user)
        if report["ownerUserId"] != user_id and not perms.can_view_all_in_unit(user, report["unitCode"]):
            raise PermissionError("Sem permissão para ver esta prestação.")
        return report

    def _assert_editable(self, user, report: dict[str, Any]) -> None:
        perms.assert_unit_action(user, "write", report["unitCode"])
        user_id, _, _ = self._actor(user)
        if report["ownerUserId"] != user_id and not perms.is_admin(user):
            raise PermissionError("Somente o autor pode editar esta prestação.")
        if not TravelReportStatusTransitionService.can_edit(report["status"]):
            raise TravelReportError("Esta prestação não pode ser editada no status atual.")

    def create(self, user, body: dict[str, Any]) -> dict[str, Any]:
        unit_code = perms.normalize_unit_code(body.get("unitCode") or body.get("unit_code"))
        if not unit_code:
            raise TravelReportError("Unidade inválida.")
        perms.assert_unit_action(user, "write", unit_code)
        user_id, email, name = self._actor(user)
        year = datetime.now().year
        number = self.repo.next_report_number(unit_code=unit_code, year=year)
        report = self.repo.create_report(
            {
                "number": number,
                "unit_code": unit_code,
                "owner_user_id": user_id,
                "created_by_name": name or email,
                "created_by_email": email,
                "destination": (body.get("destination") or "").strip(),
                "purpose": (body.get("purpose") or "").strip(),
                "period_start": _parse_date(body.get("periodStart") or body.get("period_start")),
                "period_end": _parse_date(body.get("periodEnd") or body.get("period_end")),
                "cost_center_code": (body.get("costCenterCode") or body.get("cost_center_code") or "").strip()
                or None,
                "cost_center_label": (body.get("costCenterLabel") or body.get("cost_center_label") or "").strip()
                or None,
                "status": "draft",
            }
        )
        self.repo.add_audit(
            {
                "report_id": report["id"],
                "event_type": "created",
                "to_status": "draft",
                "actor_user_id": user_id,
                "actor_name": name,
                "actor_email": email,
                "payload": {"number": number},
            }
        )
        return self._with_completeness(report)

    def list_reports(
        self,
        user,
        *,
        scope: str = "mine",
        unit_code: str | None = None,
        query: str | None = None,
        period_from: str | None = None,
        period_to: str | None = None,
    ) -> list[dict[str, Any]]:
        readable = perms.unit_codes_for_read(user)
        if unit_code:
            code = perms.normalize_unit_code(unit_code)
            if not code or code not in readable:
                raise PermissionError("Sem permissão para esta unidade.")
            readable = [code]
        if not readable:
            return []
        user_id, _, _ = self._actor(user)
        owner = None if scope == "unit" else user_id
        if scope == "unit":
            readable = [code for code in readable if perms.can_view_all_in_unit(user, code)]
            if not readable:
                raise PermissionError("Sem permissão para ver prestações da unidade.")
        return self.repo.list_reports(
            unit_codes=readable,
            owner_user_id=owner,
            query=(query or "").strip() or None,
            period_from=_parse_date(period_from),
            period_to=_parse_date(period_to),
        )

    def get_detail(self, user, report_id: str) -> dict[str, Any]:
        report = self._load_visible(user, report_id)
        return self._with_completeness(report)

    def update(self, user, report_id: str, body: dict[str, Any]) -> dict[str, Any]:
        report = self._load_visible(user, report_id)
        self._assert_editable(user, report)
        changes: dict[str, Any] = {}
        if "destination" in body:
            changes["destination"] = str(body.get("destination") or "").strip()
        if "purpose" in body:
            changes["purpose"] = str(body.get("purpose") or "").strip()
        if "periodStart" in body or "period_start" in body:
            changes["period_start"] = _parse_date(body.get("periodStart") or body.get("period_start"))
        if "periodEnd" in body or "period_end" in body:
            changes["period_end"] = _parse_date(body.get("periodEnd") or body.get("period_end"))
        if "costCenterCode" in body or "cost_center_code" in body:
            changes["cost_center_code"] = (
                str(body.get("costCenterCode") or body.get("cost_center_code") or "").strip() or None
            )
        if "costCenterLabel" in body or "cost_center_label" in body:
            changes["cost_center_label"] = (
                str(body.get("costCenterLabel") or body.get("cost_center_label") or "").strip() or None
            )
        if any(
            key in body
            for key in ("pixKeyType", "pix_key_type", "pixKeyValue", "pix_key_value")
        ):
            pix_type = body.get("pixKeyType") if "pixKeyType" in body else body.get("pix_key_type")
            pix_value = body.get("pixKeyValue") if "pixKeyValue" in body else body.get("pix_key_value")
            try:
                norm_type, norm_value = normalize_pix_key(pix_type, pix_value)
            except ValueError as exc:
                raise TravelReportError(str(exc)) from exc
            changes["pix_key_type"] = norm_type
            changes["pix_key_value"] = norm_value
        updated = self.repo.update_report(report_id, changes) or report
        user_id, email, name = self._actor(user)
        audit_events: list[dict[str, Any]] = [
            {
                "report_id": report_id,
                "event_type": "updated",
                "actor_user_id": user_id,
                "actor_name": name,
                "actor_email": email,
                "payload": {"fields": list(changes.keys())},
            }
        ]
        had_pix = bool(report.get("pixKeyType") and report.get("pixKeyValue"))
        has_pix = bool(updated.get("pixKeyType") and updated.get("pixKeyValue"))
        if has_pix and not had_pix:
            audit_events.append(
                {
                    "report_id": report_id,
                    "event_type": "pix_added",
                    "actor_user_id": user_id,
                    "actor_name": name,
                    "actor_email": email,
                    "payload": {
                        "pixKeyType": updated.get("pixKeyType"),
                        "pixKeyValue": updated.get("pixKeyValue"),
                    },
                }
            )
        for event in audit_events:
            self.repo.add_audit(event)
        return self._with_completeness(updated)

    def delete(self, user, report_id: str) -> None:
        report = self._load_visible(user, report_id)
        self._assert_editable(user, report)
        if not TravelReportStatusTransitionService.can_delete(report["status"]):
            raise TravelReportError("Somente rascunhos podem ser excluídos.")
        for expense in self.repo.list_expenses(report_id):
            for receipt in expense.get("receipts") or []:
                self.receipt_storage.delete(report_id=report_id, stored_name=receipt["storedName"])
        self.repo.delete_report(report_id)

    def add_expense(self, user, report_id: str, body: dict[str, Any]) -> dict[str, Any]:
        report = self._load_visible(user, report_id)
        self._assert_editable(user, report)
        category_id = str(body.get("categoryId") or body.get("category_id") or "").strip()
        known = {item["id"] for item in self.repo.list_categories()}
        if category_id not in known:
            raise TravelReportError("Categoria inválida.")
        expense_date = _parse_date(body.get("expenseDate") or body.get("expense_date"))
        if not expense_date:
            raise TravelReportError("Informe a data da despesa.")
        amount = _parse_amount(body.get("amountBrl") if "amountBrl" in body else body.get("amount_brl") or 0)
        expense = self.repo.create_expense(
            {
                "report_id": report_id,
                "expense_date": expense_date,
                "category_id": category_id,
                "merchant": str(body.get("merchant") or "").strip(),
                "amount_brl": amount,
                "notes": str(body.get("notes") or "").strip(),
            }
        )
        user_id, email, name = self._actor(user)
        self.repo.add_audit(
            {
                "report_id": report_id,
                "event_type": "expense_added",
                "actor_user_id": user_id,
                "actor_name": name,
                "actor_email": email,
                "payload": {"expenseId": expense["id"]},
            }
        )
        return expense

    def update_expense(self, user, report_id: str, expense_id: str, body: dict[str, Any]) -> dict[str, Any]:
        report = self._load_visible(user, report_id)
        self._assert_editable(user, report)
        expense = self.repo.get_expense(expense_id)
        if not expense or expense["reportId"] != report_id:
            raise TravelReportError("Despesa não encontrada.")
        changes: dict[str, Any] = {}
        if "categoryId" in body or "category_id" in body:
            category_id = str(body.get("categoryId") or body.get("category_id") or "").strip()
            known = {item["id"] for item in self.repo.list_categories()}
            if category_id not in known:
                raise TravelReportError("Categoria inválida.")
            changes["category_id"] = category_id
        if "expenseDate" in body or "expense_date" in body:
            expense_date = _parse_date(body.get("expenseDate") or body.get("expense_date"))
            if not expense_date:
                raise TravelReportError("Informe a data da despesa.")
            changes["expense_date"] = expense_date
        if "amountBrl" in body or "amount_brl" in body:
            changes["amount_brl"] = _parse_amount(
                body.get("amountBrl") if "amountBrl" in body else body.get("amount_brl")
            )
        if "merchant" in body:
            changes["merchant"] = str(body.get("merchant") or "").strip()
        if "notes" in body:
            changes["notes"] = str(body.get("notes") or "").strip()
        return self.repo.update_expense(expense_id, changes) or expense

    def delete_expense(self, user, report_id: str, expense_id: str) -> None:
        report = self._load_visible(user, report_id)
        self._assert_editable(user, report)
        expense = self.repo.get_expense(expense_id)
        if not expense or expense["reportId"] != report_id:
            raise TravelReportError("Despesa não encontrada.")
        for receipt in expense.get("receipts") or []:
            self.receipt_storage.delete(report_id=report_id, stored_name=receipt["storedName"])
            self.repo.delete_receipt(receipt["id"])
        self.repo.delete_expense(expense_id)

    def add_receipt(
        self,
        user,
        report_id: str,
        expense_id: str,
        *,
        original_name: str,
        mime_type: str | None,
        content: bytes,
    ) -> dict[str, Any]:
        report = self._load_visible(user, report_id)
        self._assert_editable(user, report)
        expense = self.repo.get_expense(expense_id)
        if not expense or expense["reportId"] != report_id:
            raise TravelReportError("Despesa não encontrada.")
        try:
            stored_name = self.receipt_storage.save(
                report_id=report_id,
                original_name=original_name,
                content=content,
                mime_type=mime_type,
            )
        except ReceiptStorageError as exc:
            raise TravelReportError(str(exc)) from exc
        receipt = self.repo.create_receipt(
            {
                "expense_id": expense_id,
                "stored_name": stored_name,
                "original_name": original_name,
                "mime_type": mime_type or "application/octet-stream",
                "size_bytes": len(content),
            }
        )
        user_id, email, name = self._actor(user)
        self.repo.add_audit(
            {
                "report_id": report_id,
                "event_type": "receipt_added",
                "actor_user_id": user_id,
                "actor_name": name,
                "actor_email": email,
                "payload": {"expenseId": expense_id, "receiptId": receipt["id"]},
            }
        )
        return receipt

    def get_receipt_file(self, user, report_id: str, expense_id: str, receipt_id: str):
        report = self._load_visible(user, report_id)
        expense = self.repo.get_expense(expense_id)
        if not expense or expense["reportId"] != report_id:
            raise TravelReportError("Despesa não encontrada.")
        receipt = self.repo.get_receipt(receipt_id)
        if not receipt or receipt["expenseId"] != expense_id:
            raise TravelReportError("Cupom não encontrado.")
        try:
            path = self.receipt_storage.resolve(report_id=report["id"], stored_name=receipt["storedName"])
        except ReceiptStorageError as exc:
            raise TravelReportError(str(exc)) from exc
        return receipt, path

    def delete_receipt(self, user, report_id: str, expense_id: str, receipt_id: str) -> None:
        report = self._load_visible(user, report_id)
        self._assert_editable(user, report)
        expense = self.repo.get_expense(expense_id)
        if not expense or expense["reportId"] != report_id:
            raise TravelReportError("Despesa não encontrada.")
        receipt = self.repo.get_receipt(receipt_id)
        if not receipt or receipt["expenseId"] != expense_id:
            raise TravelReportError("Cupom não encontrado.")
        self.receipt_storage.delete(report_id=report_id, stored_name=receipt["storedName"])
        self.repo.delete_receipt(receipt_id)

    def list_audit(self, user, report_id: str) -> list[dict[str, Any]]:
        self._load_visible(user, report_id)
        return self.repo.list_audit(report_id)

    def build_package_pdf(self, user, report_id: str) -> bytes:
        detail = self.get_detail(user, report_id)
        receipt_attachments: list[dict[str, Any]] = []
        for expense in detail["expenses"]:
            for receipt in expense.get("receipts") or []:
                try:
                    file_path = self.receipt_storage.resolve(
                        report_id=report_id,
                        stored_name=receipt["storedName"],
                    )
                    receipt_attachments.append(
                        {
                            "receiptId": receipt["id"],
                            "expenseId": expense["id"],
                            "mimeType": receipt.get("mimeType"),
                            "content": file_path.read_bytes(),
                        }
                    )
                except ReceiptStorageError:
                    continue
        content = self.pdf_renderer.render(
            detail,
            detail["expenses"],
            self.repo.list_categories(),
            receipt_attachments=receipt_attachments,
        )
        self.package_storage.save(report_id=report_id, content=content)
        return content
