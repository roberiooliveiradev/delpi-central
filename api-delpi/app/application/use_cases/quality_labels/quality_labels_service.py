from __future__ import annotations

import secrets
from typing import Any

from app.application.dto.production.get_production_order_by_op_request import (
    GetProductionOrderByOpRequest,
)
from app.application.services.quality_labels.quality_labels_audit_metadata_service import (
    QualityLabelsAuditMetadataService,
)
from app.application.services.quality_labels.quality_labels_qr_service import (
    QualityLabelsQrService,
    build_public_url,
)
from app.application.use_cases.production.get_production_order_by_op_use_case import (
    GetProductionOrderByOpUseCase,
)
from app.application.use_cases.production.get_order_customer_by_op_use_case import (
    GetOrderCustomerByOpUseCase,
)
from app.application.use_cases.production.search_production_orders_by_op_use_case import (
    SearchProductionOrdersByOpUseCase,
)
from app.infrastructure.persistence.plugins.repositories.quality_labels.postgres_quality_labels_audit_repository import (
    PostgresQualityLabelsAuditRepository,
)
from app.infrastructure.persistence.plugins.repositories.quality_labels.postgres_quality_labels_repository import (
    PostgresQualityLabelsRepository,
    unit_name,
)
from app.utils.logger import log_error

_TOKEN_NBYTES = 24

EVENT_CREATED = "label_created"
EVENT_ACTIVATED = "label_activated"
EVENT_DEACTIVATED = "label_deactivated"
EVENT_DELETED = "label_deleted"
EVENT_VIEWED = "label_viewed"


class QualityLabelsError(Exception):
    """Erro de regra de negócio do módulo de etiquetas da qualidade."""


class ProductionOrderNotFoundError(QualityLabelsError):
    """OP não localizada na produção (TOTVS)."""


class QualityLabelsService:
    def __init__(
        self,
        *,
        repository: PostgresQualityLabelsRepository,
        qr_service: QualityLabelsQrService,
        production_order_use_case: GetProductionOrderByOpUseCase,
        search_orders_use_case: SearchProductionOrdersByOpUseCase,
        order_customer_use_case: GetOrderCustomerByOpUseCase,
        audit_metadata_service: QualityLabelsAuditMetadataService,
        audit_repository: PostgresQualityLabelsAuditRepository,
    ) -> None:
        self._repository = repository
        self._qr_service = qr_service
        self._production_order_use_case = production_order_use_case
        self._search_orders_use_case = search_orders_use_case
        self._order_customer_use_case = order_customer_use_case
        self._audit_metadata_service = audit_metadata_service
        self._audit_repository = audit_repository

    def search_ops(
        self,
        *,
        term: str,
        branches: list[str] | None = None,
        limit: int = 8,
    ) -> list[dict[str, Any]]:
        rows = self._search_orders_use_case.execute(
            term=term, branches=branches, limit=limit
        )
        return [
            {
                "productionOrder": row.get("production_order"),
                "branch": row.get("branch"),
                "branchName": unit_name(row.get("branch")),
                "productCode": row.get("product_code"),
                "productDescription": row.get("product_description"),
                "productUnit": row.get("unit") or row.get("product_unit"),
            }
            for row in rows
        ]

    def lookup_op(self, *, production_order: str, branch: str | None = None) -> dict[str, Any]:
        order = self._resolve_order(production_order=production_order, branch=branch)
        resolved_op = order.get("production_order") or production_order.strip()
        resolved_branch = order.get("branch") or branch
        existing = self._repository.list_by_production_order(
            production_order=resolved_op,
            branch=resolved_branch,
        )
        existing_payloads = [self._repository.to_admin_payload(row) for row in existing]
        active_existing = [item for item in existing_payloads if item.get("isActive")]
        customer = self._lookup_customer(
            production_order=resolved_op,
            branch=resolved_branch,
        )
        return {
            "productionOrder": resolved_op,
            "orderNumber": order.get("order_number"),
            "branch": resolved_branch,
            "branchName": unit_name(resolved_branch),
            "productCode": order.get("product_code"),
            "productDescription": order.get("product_description"),
            "productUnit": self._order_unit(order),
            "existingLabels": existing_payloads,
            "hasActiveInspection": len(active_existing) > 0,
            "customer": customer,
        }

    def create_label(
        self,
        *,
        production_order: str,
        branch: str | None,
        notes: str | None,
        result: str,
        inspector_user_id: str,
        inspector_name: str,
        inspected_quantity: int | None = None,
    ) -> dict[str, Any]:
        order = self._resolve_order(production_order=production_order, branch=branch)
        resolved_op = order.get("production_order") or production_order.strip()
        resolved_branch = order.get("branch") or branch

        audit_metadata = self._audit_metadata_service.build(
            production_order=resolved_op,
            branch=resolved_branch,
        )

        token = secrets.token_urlsafe(_TOKEN_NBYTES)
        row = self._repository.insert_label(
            public_token=token,
            production_order=resolved_op,
            branch=resolved_branch,
            product_code=str(order.get("product_code") or "").strip(),
            product_description=str(order.get("product_description") or "").strip(),
            product_unit=self._order_unit(order),
            order_number=order.get("order_number"),
            inspector_user_id=inspector_user_id,
            inspector_name=inspector_name,
            result=result,
            notes=notes,
            inspected_quantity=inspected_quantity,
            audit_metadata=audit_metadata,
        )

        qr_filename = self._qr_service.generate(token=token)
        updated = self._repository.set_qr_filename(
            label_id=str(row["id"]),
            qr_filename=qr_filename,
        )
        row = updated or row

        payload = self._repository.to_admin_payload(row, include_audit_metadata=True)
        payload["publicUrl"] = build_public_url(token)
        self._record_event(
            EVENT_CREATED,
            row=row,
            actor_user_id=inspector_user_id,
            actor_name=inspector_name,
        )
        return payload

    def list_labels(
        self,
        *,
        search: str | None,
        branches: list[str] | None,
        limit: int,
        offset: int,
    ) -> dict[str, Any]:
        rows, total = self._repository.list_labels(
            search=search, branches=branches, limit=limit, offset=offset
        )
        items = [self._repository.to_admin_payload(row) for row in rows]
        for item, row in zip(items, rows):
            item["publicUrl"] = build_public_url(row["public_token"])
        return {
            "items": items,
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "is_complete": offset + len(items) >= total,
            },
        }

    def get_label(self, *, label_id: str) -> dict[str, Any] | None:
        row = self._repository.get_by_id(label_id)
        if row is None:
            return None
        payload = self._repository.to_admin_payload(row, include_audit_metadata=True)
        payload["publicUrl"] = build_public_url(row["public_token"])
        return payload

    def set_active(
        self,
        *,
        label_id: str,
        is_active: bool,
        actor_user_id: str | None = None,
        actor_name: str | None = None,
    ) -> dict[str, Any] | None:
        row = self._repository.set_active(label_id=label_id, is_active=is_active)
        if row is None:
            return None
        self._record_event(
            EVENT_ACTIVATED if is_active else EVENT_DEACTIVATED,
            row=row,
            actor_user_id=actor_user_id,
            actor_name=actor_name,
        )
        return self._repository.to_admin_payload(row)

    def delete_label(
        self,
        *,
        label_id: str,
        actor_user_id: str | None = None,
        actor_name: str | None = None,
    ) -> bool:
        row = self._repository.get_by_id(label_id)
        if row is None:
            return False
        self._qr_service.delete(row.get("qr_filename"))
        deleted = self._repository.delete_label(label_id=label_id)
        if deleted:
            self._record_event(
                EVENT_DELETED,
                row=row,
                actor_user_id=actor_user_id,
                actor_name=actor_name,
            )
        return deleted

    def list_audit_events(
        self,
        *,
        search: str | None,
        event_types: list[str] | None,
        limit: int,
        offset: int,
    ) -> dict[str, Any]:
        rows, total = self._audit_repository.list_events(
            search=search, event_types=event_types, limit=limit, offset=offset
        )
        return {
            "items": [self._audit_repository.to_payload(row) for row in rows],
            "summary": self._audit_repository.count_by_type(),
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "is_complete": offset + len(rows) >= total,
            },
        }

    def read_qr(self, *, label_id: str) -> bytes | None:
        row = self._repository.get_by_id(label_id)
        if row is None or not row.get("qr_filename"):
            return None
        return self._qr_service.read(row["qr_filename"])

    def get_public(self, *, token: str) -> dict[str, Any] | None:
        row = self._repository.get_by_token(token)
        if row is None or not row.get("is_active", True):
            return None
        self._repository.increment_view_count(token)
        self._record_event(
            EVENT_VIEWED,
            row=row,
            actor_user_id=None,
            actor_name="Cliente (acesso público)",
        )
        return self._repository.to_public_payload(row)

    def _lookup_customer(
        self,
        *,
        production_order: str,
        branch: str | None,
    ) -> dict[str, Any] | None:
        try:
            row = self._order_customer_use_case.execute(
                production_order=production_order,
                branch=branch,
            )
        except Exception as exc:  # noqa: BLE001 - best-effort
            log_error(f"Falha ao buscar cliente da OP {production_order}: {exc}")
            return None
        if not row or not row.get("customer_name"):
            return None
        return {
            "code": row.get("customer_code"),
            "store": row.get("customer_store"),
            "name": row.get("customer_name"),
            "source": "totvs",
        }

    def _record_event(
        self,
        event_type: str,
        *,
        row: dict[str, Any],
        actor_user_id: str | None,
        actor_name: str | None,
    ) -> None:
        # Auditoria não pode quebrar a operação principal (já persistida).
        try:
            self._audit_repository.insert_event(
                event_type=event_type,
                label_id=str(row["id"]) if row.get("id") else None,
                production_order=row.get("production_order"),
                product_code=row.get("product_code"),
                branch=row.get("branch"),
                result=row.get("result"),
                actor_user_id=actor_user_id,
                actor_name=actor_name,
            )
        except Exception as exc:  # noqa: BLE001 - auditoria é best-effort
            log_error(f"Falha ao registrar evento de auditoria ({event_type}): {exc}")

    @staticmethod
    def _order_unit(order: dict[str, Any]) -> str | None:
        # Unidade da própria OP (C2_UM) — não passa pela conversão MI→UN da resposta operacional.
        for key in ("order_unit", "product_unit", "unit"):
            value = order.get(key)
            if value not in (None, ""):
                return str(value).strip() or None
        return None

    def _resolve_order(self, *, production_order: str, branch: str | None) -> dict[str, Any]:
        normalized = (production_order or "").strip()
        if not normalized:
            raise QualityLabelsError("Ordem de produção (OP) é obrigatória.")

        result = self._production_order_use_case.execute(
            GetProductionOrderByOpRequest(production_order=normalized, branch=branch)
        )
        if not result or not result.get("order"):
            raise ProductionOrderNotFoundError(
                f"OP {normalized} não localizada na produção."
            )
        return result["order"]
