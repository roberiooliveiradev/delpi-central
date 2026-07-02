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
from app.application.use_cases.production.search_production_orders_by_op_use_case import (
    SearchProductionOrdersByOpUseCase,
)
from app.infrastructure.persistence.plugins.repositories.quality_labels.postgres_quality_labels_repository import (
    PostgresQualityLabelsRepository,
    unit_name,
)

_TOKEN_NBYTES = 24


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
        audit_metadata_service: QualityLabelsAuditMetadataService,
    ) -> None:
        self._repository = repository
        self._qr_service = qr_service
        self._production_order_use_case = production_order_use_case
        self._search_orders_use_case = search_orders_use_case
        self._audit_metadata_service = audit_metadata_service

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
        return {
            "productionOrder": resolved_op,
            "orderNumber": order.get("order_number"),
            "branch": resolved_branch,
            "branchName": unit_name(resolved_branch),
            "productCode": order.get("product_code"),
            "productDescription": order.get("product_description"),
            "productUnit": order.get("unit") or order.get("product_unit"),
            "existingLabels": existing_payloads,
            "hasActiveInspection": len(active_existing) > 0,
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
            product_unit=order.get("unit") or order.get("product_unit"),
            order_number=order.get("order_number"),
            inspector_user_id=inspector_user_id,
            inspector_name=inspector_name,
            result=result,
            notes=notes,
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

    def set_active(self, *, label_id: str, is_active: bool) -> dict[str, Any] | None:
        row = self._repository.set_active(label_id=label_id, is_active=is_active)
        if row is None:
            return None
        return self._repository.to_admin_payload(row)

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
        return self._repository.to_public_payload(row)

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
