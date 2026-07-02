from __future__ import annotations

import secrets
from typing import Any

from app.application.dto.production.get_production_order_by_op_request import (
    GetProductionOrderByOpRequest,
)
from app.application.services.quality_labels.quality_labels_qr_service import (
    QualityLabelsQrService,
    build_public_url,
)
from app.application.use_cases.production.get_production_order_by_op_use_case import (
    GetProductionOrderByOpUseCase,
)
from app.infrastructure.persistence.plugins.repositories.quality_labels.postgres_quality_labels_repository import (
    PostgresQualityLabelsRepository,
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
    ) -> None:
        self._repository = repository
        self._qr_service = qr_service
        self._production_order_use_case = production_order_use_case

    def lookup_op(self, *, production_order: str, branch: str | None = None) -> dict[str, Any]:
        order = self._resolve_order(production_order=production_order, branch=branch)
        return {
            "productionOrder": order.get("production_order") or production_order.strip(),
            "orderNumber": order.get("order_number"),
            "branch": order.get("branch"),
            "productCode": order.get("product_code"),
            "productDescription": order.get("product_description"),
            "productUnit": order.get("unit") or order.get("product_unit"),
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

        token = secrets.token_urlsafe(_TOKEN_NBYTES)
        row = self._repository.insert_label(
            public_token=token,
            production_order=order.get("production_order") or production_order.strip(),
            branch=order.get("branch") or branch,
            product_code=str(order.get("product_code") or "").strip(),
            product_description=str(order.get("product_description") or "").strip(),
            product_unit=order.get("unit") or order.get("product_unit"),
            order_number=order.get("order_number"),
            inspector_user_id=inspector_user_id,
            inspector_name=inspector_name,
            result=result,
            notes=notes,
        )

        qr_filename = self._qr_service.generate(token=token)
        updated = self._repository.set_qr_filename(
            label_id=str(row["id"]),
            qr_filename=qr_filename,
        )
        row = updated or row

        payload = self._repository.to_admin_payload(row)
        payload["publicUrl"] = build_public_url(token)
        return payload

    def list_labels(
        self,
        *,
        search: str | None,
        limit: int,
        offset: int,
    ) -> dict[str, Any]:
        rows, total = self._repository.list_labels(search=search, limit=limit, offset=offset)
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
        payload = self._repository.to_admin_payload(row)
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
