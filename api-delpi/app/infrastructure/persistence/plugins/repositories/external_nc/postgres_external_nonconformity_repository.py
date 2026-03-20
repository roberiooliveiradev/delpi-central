# app/infrastructure/persistence/plugins/repositories/external_nc/postgres_external_nonconformity_repository.py
from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional

from app.domain.entities.external_nc.external_nonconformity import (
    ExternalNonconformity,
)
from app.domain.ports.external_nc.external_nonconformity_repository import (
    ExternalNonconformityRepositoryPort,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)


class PostgresExternalNonconformityRepository(
    PluginBaseRepository,
    ExternalNonconformityRepositoryPort,
):
    def create(self, entity: ExternalNonconformity) -> ExternalNonconformity:
        row = self.execute_returning_one(
            """
            INSERT INTO quality.external_nonconformities (
                id,
                code,
                company_unit,
                supplier_id,
                supplier_name_snapshot,
                customer_name,
                origin_type,
                source_channel,
                material_code,
                material_description,
                material_specification,
                lot_number,
                purchase_order,
                invoice_number,
                document_reference,
                occurrence_date,
                detection_date,
                defective_quantity,
                inspected_quantity,
                uom,
                severity,
                priority,
                occurrence_type,
                defect_category,
                recurrence_flag,
                containment_required,
                title,
                problem_description,
                business_impact,
                customer_impact,
                production_impact,
                cost_estimate,
                current_status,
                supplier_status,
                responsible_user_id,
                opened_by_user_id,
                due_date,
                closed_at,
                cancellation_reason
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            RETURNING
                id,
                code,
                company_unit,
                supplier_id,
                supplier_name_snapshot,
                customer_name,
                origin_type,
                source_channel,
                material_code,
                material_description,
                material_specification,
                lot_number,
                purchase_order,
                invoice_number,
                document_reference,
                occurrence_date,
                detection_date,
                defective_quantity,
                inspected_quantity,
                uom,
                severity,
                priority,
                occurrence_type,
                defect_category,
                recurrence_flag,
                containment_required,
                title,
                problem_description,
                business_impact,
                customer_impact,
                production_impact,
                cost_estimate,
                current_status,
                supplier_status,
                responsible_user_id,
                opened_by_user_id,
                due_date,
                closed_at,
                cancellation_reason,
                created_at,
                updated_at
            """,
            (
                entity.id,
                entity.code,
                entity.company_unit,
                entity.supplier_id,
                entity.supplier_name_snapshot,
                entity.customer_name,
                entity.origin_type,
                entity.source_channel,
                entity.material_code,
                entity.material_description,
                entity.material_specification,
                entity.lot_number,
                entity.purchase_order,
                entity.invoice_number,
                entity.document_reference,
                entity.occurrence_date,
                entity.detection_date,
                entity.defective_quantity,
                entity.inspected_quantity,
                entity.uom,
                entity.severity,
                entity.priority,
                entity.occurrence_type,
                entity.defect_category,
                entity.recurrence_flag,
                entity.containment_required,
                entity.title,
                entity.problem_description,
                entity.business_impact,
                entity.customer_impact,
                entity.production_impact,
                entity.cost_estimate,
                entity.current_status,
                entity.supplier_status,
                entity.responsible_user_id,
                entity.opened_by_user_id,
                entity.due_date,
                entity.closed_at,
                entity.cancellation_reason,
            ),
            auto_commit=True,
        )
        return self._to_entity(row)

    def get_by_id(self, nonconformity_id: str) -> Optional[ExternalNonconformity]:
        row = self.fetch_one(
            """
            SELECT
                id,
                code,
                company_unit,
                supplier_id,
                supplier_name_snapshot,
                customer_name,
                origin_type,
                source_channel,
                material_code,
                material_description,
                material_specification,
                lot_number,
                purchase_order,
                invoice_number,
                document_reference,
                occurrence_date,
                detection_date,
                defective_quantity,
                inspected_quantity,
                uom,
                severity,
                priority,
                occurrence_type,
                defect_category,
                recurrence_flag,
                containment_required,
                title,
                problem_description,
                business_impact,
                customer_impact,
                production_impact,
                cost_estimate,
                current_status,
                supplier_status,
                responsible_user_id,
                opened_by_user_id,
                due_date,
                closed_at,
                cancellation_reason,
                created_at,
                updated_at
            FROM quality.external_nonconformities
            WHERE id = %s
            """,
            (nonconformity_id,),
        )
        return self._to_entity(row) if row else None

    def get_by_code(self, code: str) -> Optional[ExternalNonconformity]:
        row = self.fetch_one(
            """
            SELECT
                id,
                code,
                company_unit,
                supplier_id,
                supplier_name_snapshot,
                customer_name,
                origin_type,
                source_channel,
                material_code,
                material_description,
                material_specification,
                lot_number,
                purchase_order,
                invoice_number,
                document_reference,
                occurrence_date,
                detection_date,
                defective_quantity,
                inspected_quantity,
                uom,
                severity,
                priority,
                occurrence_type,
                defect_category,
                recurrence_flag,
                containment_required,
                title,
                problem_description,
                business_impact,
                customer_impact,
                production_impact,
                cost_estimate,
                current_status,
                supplier_status,
                responsible_user_id,
                opened_by_user_id,
                due_date,
                closed_at,
                cancellation_reason,
                created_at,
                updated_at
            FROM quality.external_nonconformities
            WHERE code = %s
            """,
            (code,),
        )
        return self._to_entity(row) if row else None

    def list(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        current_status: Optional[str] = None,
        supplier_id: Optional[str] = None,
        search: Optional[str] = None,
    ) -> dict:
        page = max(1, page)
        page_size = max(1, min(page_size, 100))
        offset = (page - 1) * page_size

        conditions = []
        params: list[Any] = []

        if current_status:
            conditions.append("current_status = %s")
            params.append(current_status)

        if supplier_id:
            conditions.append("supplier_id = %s")
            params.append(supplier_id)

        if search:
            conditions.append(
                """
                (
                    code ILIKE %s
                    OR title ILIKE %s
                    OR supplier_name_snapshot ILIKE %s
                    OR COALESCE(material_code, '') ILIKE %s
                    OR COALESCE(material_description, '') ILIKE %s
                )
                """
            )
            search_term = f"%{search}%"
            params.extend(
                [search_term, search_term, search_term, search_term, search_term]
            )

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        count_row = self.fetch_one(
            f"""
            SELECT COUNT(*) AS total
            FROM quality.external_nonconformities
            {where_clause}
            """,
            tuple(params),
        )
        total = int(count_row["total"]) if count_row else 0

        items = self.fetch_all(
            f"""
            SELECT
                id,
                code,
                company_unit,
                supplier_id,
                supplier_name_snapshot,
                customer_name,
                origin_type,
                source_channel,
                material_code,
                material_description,
                material_specification,
                lot_number,
                purchase_order,
                invoice_number,
                document_reference,
                occurrence_date,
                detection_date,
                defective_quantity,
                inspected_quantity,
                uom,
                severity,
                priority,
                occurrence_type,
                defect_category,
                recurrence_flag,
                containment_required,
                title,
                problem_description,
                business_impact,
                customer_impact,
                production_impact,
                cost_estimate,
                current_status,
                supplier_status,
                responsible_user_id,
                opened_by_user_id,
                due_date,
                closed_at,
                cancellation_reason,
                created_at,
                updated_at
            FROM quality.external_nonconformities
            {where_clause}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
            """,
            tuple([*params, page_size, offset]),
        )

        return {
            "items": [self._to_entity(row) for row in items],
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size,
        }

    def update(self, entity: ExternalNonconformity) -> ExternalNonconformity:
        row = self.execute_returning_one(
            """
            UPDATE quality.external_nonconformities
               SET company_unit = %s,
                   supplier_id = %s,
                   supplier_name_snapshot = %s,
                   customer_name = %s,
                   origin_type = %s,
                   source_channel = %s,
                   material_code = %s,
                   material_description = %s,
                   material_specification = %s,
                   lot_number = %s,
                   purchase_order = %s,
                   invoice_number = %s,
                   document_reference = %s,
                   occurrence_date = %s,
                   detection_date = %s,
                   defective_quantity = %s,
                   inspected_quantity = %s,
                   uom = %s,
                   severity = %s,
                   priority = %s,
                   occurrence_type = %s,
                   defect_category = %s,
                   recurrence_flag = %s,
                   containment_required = %s,
                   title = %s,
                   problem_description = %s,
                   business_impact = %s,
                   customer_impact = %s,
                   production_impact = %s,
                   cost_estimate = %s,
                   current_status = %s,
                   supplier_status = %s,
                   responsible_user_id = %s,
                   due_date = %s,
                   closed_at = %s,
                   cancellation_reason = %s
             WHERE id = %s
         RETURNING
                id,
                code,
                company_unit,
                supplier_id,
                supplier_name_snapshot,
                customer_name,
                origin_type,
                source_channel,
                material_code,
                material_description,
                material_specification,
                lot_number,
                purchase_order,
                invoice_number,
                document_reference,
                occurrence_date,
                detection_date,
                defective_quantity,
                inspected_quantity,
                uom,
                severity,
                priority,
                occurrence_type,
                defect_category,
                recurrence_flag,
                containment_required,
                title,
                problem_description,
                business_impact,
                customer_impact,
                production_impact,
                cost_estimate,
                current_status,
                supplier_status,
                responsible_user_id,
                opened_by_user_id,
                due_date,
                closed_at,
                cancellation_reason,
                created_at,
                updated_at
            """,
            (
                entity.company_unit,
                entity.supplier_id,
                entity.supplier_name_snapshot,
                entity.customer_name,
                entity.origin_type,
                entity.source_channel,
                entity.material_code,
                entity.material_description,
                entity.material_specification,
                entity.lot_number,
                entity.purchase_order,
                entity.invoice_number,
                entity.document_reference,
                entity.occurrence_date,
                entity.detection_date,
                entity.defective_quantity,
                entity.inspected_quantity,
                entity.uom,
                entity.severity,
                entity.priority,
                entity.occurrence_type,
                entity.defect_category,
                entity.recurrence_flag,
                entity.containment_required,
                entity.title,
                entity.problem_description,
                entity.business_impact,
                entity.customer_impact,
                entity.production_impact,
                entity.cost_estimate,
                entity.current_status,
                entity.supplier_status,
                entity.responsible_user_id,
                entity.due_date,
                entity.closed_at,
                entity.cancellation_reason,
                entity.id,
            ),
            auto_commit=True,
        )
        return self._to_entity(row)

    def _to_entity(self, row: dict[str, Any]) -> ExternalNonconformity:
        return ExternalNonconformity(
            id=str(row["id"]),
            code=row["code"],
            company_unit=row["company_unit"],
            supplier_id=str(row["supplier_id"]),
            supplier_name_snapshot=row["supplier_name_snapshot"],
            customer_name=row.get("customer_name"),
            origin_type=row["origin_type"],
            source_channel=row.get("source_channel"),
            material_code=row.get("material_code"),
            material_description=row.get("material_description"),
            material_specification=row.get("material_specification"),
            lot_number=row.get("lot_number"),
            purchase_order=row.get("purchase_order"),
            invoice_number=row.get("invoice_number"),
            document_reference=row.get("document_reference"),
            occurrence_date=row["occurrence_date"],
            detection_date=row["detection_date"],
            defective_quantity=Decimal(str(row["defective_quantity"])),
            inspected_quantity=(
                Decimal(str(row["inspected_quantity"]))
                if row.get("inspected_quantity") is not None
                else None
            ),
            uom=row.get("uom"),
            severity=row["severity"],
            priority=row["priority"],
            occurrence_type=row.get("occurrence_type"),
            defect_category=row.get("defect_category"),
            recurrence_flag=bool(row["recurrence_flag"]),
            containment_required=bool(row["containment_required"]),
            title=row["title"],
            problem_description=row["problem_description"],
            business_impact=row.get("business_impact"),
            customer_impact=row.get("customer_impact"),
            production_impact=row.get("production_impact"),
            cost_estimate=(
                Decimal(str(row["cost_estimate"]))
                if row.get("cost_estimate") is not None
                else None
            ),
            current_status=row["current_status"],
            supplier_status=row["supplier_status"],
            responsible_user_id=row.get("responsible_user_id"),
            opened_by_user_id=row["opened_by_user_id"],
            due_date=row.get("due_date"),
            closed_at=row.get("closed_at"),
            cancellation_reason=row.get("cancellation_reason"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )