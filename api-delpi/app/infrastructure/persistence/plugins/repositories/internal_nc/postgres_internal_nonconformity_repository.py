# app/infrastructure/persistence/plugins/repositories/internal_nc/postgres_internal_nonconformity_repository.py
from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional

from app.domain.entities.internal_nc.internal_nonconformity import (
    InternalNonconformity,
)
from app.domain.ports.internal_nc.internal_nonconformity_repository import (
    InternalNonconformityRepositoryPort,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)


class PostgresInternalNonconformityRepository(
    PluginBaseRepository,
    InternalNonconformityRepositoryPort,
):
    def create(self, entity: InternalNonconformity) -> InternalNonconformity:
        row = self.execute_returning_one(
            """
            INSERT INTO quality.internal_nonconformities (
                id,
                code,
                source_type,
                source_inspection_id,
                production_order,
                item_code,
                item_description,
                lot_number,
                sector,
                operation_code,
                operation_description,
                defect_category,
                defect_description,
                detected_by_user_id,
                detection_date,
                defective_quantity,
                inspected_quantity,
                severity,
                priority,
                current_status,
                containment_action_summary,
                disposition_type,
                immediate_cause_notes,
                root_cause_summary,
                responsible_user_id,
                due_date,
                closed_at,
                cancellation_reason
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s
            )
            RETURNING
                id, code, source_type, source_inspection_id, production_order,
                item_code, item_description, lot_number, sector, operation_code,
                operation_description, defect_category, defect_description,
                detected_by_user_id, detection_date, defective_quantity,
                inspected_quantity, severity, priority, current_status,
                containment_action_summary, disposition_type, immediate_cause_notes,
                root_cause_summary, responsible_user_id, due_date, closed_at,
                cancellation_reason, created_at, updated_at
            """,
            (
                entity.id,
                entity.code,
                entity.source_type,
                entity.source_inspection_id,
                entity.production_order,
                entity.item_code,
                entity.item_description,
                entity.lot_number,
                entity.sector,
                entity.operation_code,
                entity.operation_description,
                entity.defect_category,
                entity.defect_description,
                entity.detected_by_user_id,
                entity.detection_date,
                entity.defective_quantity,
                entity.inspected_quantity,
                entity.severity,
                entity.priority,
                entity.current_status,
                entity.containment_action_summary,
                entity.disposition_type,
                entity.immediate_cause_notes,
                entity.root_cause_summary,
                entity.responsible_user_id,
                entity.due_date,
                entity.closed_at,
                entity.cancellation_reason,
            ),
            auto_commit=True,
        )
        return self._to_entity(row)

    def get_by_id(self, nonconformity_id: str) -> Optional[InternalNonconformity]:
        row = self.fetch_one(
            """
            SELECT
                id, code, source_type, source_inspection_id, production_order,
                item_code, item_description, lot_number, sector, operation_code,
                operation_description, defect_category, defect_description,
                detected_by_user_id, detection_date, defective_quantity,
                inspected_quantity, severity, priority, current_status,
                containment_action_summary, disposition_type, immediate_cause_notes,
                root_cause_summary, responsible_user_id, due_date, closed_at,
                cancellation_reason, created_at, updated_at
            FROM quality.internal_nonconformities
            WHERE id = %s
            """,
            (nonconformity_id,),
        )
        return self._to_entity(row) if row else None

    def get_by_code(self, code: str) -> Optional[InternalNonconformity]:
        row = self.fetch_one(
            """
            SELECT
                id, code, source_type, source_inspection_id, production_order,
                item_code, item_description, lot_number, sector, operation_code,
                operation_description, defect_category, defect_description,
                detected_by_user_id, detection_date, defective_quantity,
                inspected_quantity, severity, priority, current_status,
                containment_action_summary, disposition_type, immediate_cause_notes,
                root_cause_summary, responsible_user_id, due_date, closed_at,
                cancellation_reason, created_at, updated_at
            FROM quality.internal_nonconformities
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
        sector: Optional[str] = None,
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

        if sector:
            conditions.append("sector = %s")
            params.append(sector)

        if search:
            conditions.append(
                """
                (
                    code ILIKE %s
                    OR item_code ILIKE %s
                    OR item_description ILIKE %s
                    OR defect_category ILIKE %s
                    OR defect_description ILIKE %s
                )
                """
            )
            search_term = f"%{search}%"
            params.extend([search_term] * 5)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        count_row = self.fetch_one(
            f"""
            SELECT COUNT(*) AS total
            FROM quality.internal_nonconformities
            {where_clause}
            """,
            tuple(params),
        )
        total = int(count_row["total"]) if count_row else 0

        items = self.fetch_all(
            f"""
            SELECT
                id, code, source_type, source_inspection_id, production_order,
                item_code, item_description, lot_number, sector, operation_code,
                operation_description, defect_category, defect_description,
                detected_by_user_id, detection_date, defective_quantity,
                inspected_quantity, severity, priority, current_status,
                containment_action_summary, disposition_type, immediate_cause_notes,
                root_cause_summary, responsible_user_id, due_date, closed_at,
                cancellation_reason, created_at, updated_at
            FROM quality.internal_nonconformities
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

    def update(self, entity: InternalNonconformity) -> InternalNonconformity:
        row = self.execute_returning_one(
            """
            UPDATE quality.internal_nonconformities
               SET source_type = %s,
                   source_inspection_id = %s,
                   production_order = %s,
                   item_code = %s,
                   item_description = %s,
                   lot_number = %s,
                   sector = %s,
                   operation_code = %s,
                   operation_description = %s,
                   defect_category = %s,
                   defect_description = %s,
                   detected_by_user_id = %s,
                   detection_date = %s,
                   defective_quantity = %s,
                   inspected_quantity = %s,
                   severity = %s,
                   priority = %s,
                   current_status = %s,
                   containment_action_summary = %s,
                   disposition_type = %s,
                   immediate_cause_notes = %s,
                   root_cause_summary = %s,
                   responsible_user_id = %s,
                   due_date = %s,
                   closed_at = %s,
                   cancellation_reason = %s
             WHERE id = %s
         RETURNING
                id, code, source_type, source_inspection_id, production_order,
                item_code, item_description, lot_number, sector, operation_code,
                operation_description, defect_category, defect_description,
                detected_by_user_id, detection_date, defective_quantity,
                inspected_quantity, severity, priority, current_status,
                containment_action_summary, disposition_type, immediate_cause_notes,
                root_cause_summary, responsible_user_id, due_date, closed_at,
                cancellation_reason, created_at, updated_at
            """,
            (
                entity.source_type,
                entity.source_inspection_id,
                entity.production_order,
                entity.item_code,
                entity.item_description,
                entity.lot_number,
                entity.sector,
                entity.operation_code,
                entity.operation_description,
                entity.defect_category,
                entity.defect_description,
                entity.detected_by_user_id,
                entity.detection_date,
                entity.defective_quantity,
                entity.inspected_quantity,
                entity.severity,
                entity.priority,
                entity.current_status,
                entity.containment_action_summary,
                entity.disposition_type,
                entity.immediate_cause_notes,
                entity.root_cause_summary,
                entity.responsible_user_id,
                entity.due_date,
                entity.closed_at,
                entity.cancellation_reason,
                entity.id,
            ),
            auto_commit=True,
        )
        return self._to_entity(row)

    def _to_entity(self, row: dict[str, Any]) -> InternalNonconformity:
        return InternalNonconformity(
            id=str(row["id"]),
            code=row["code"],
            source_type=row["source_type"],
            source_inspection_id=str(row["source_inspection_id"]) if row.get("source_inspection_id") else None,
            production_order=row.get("production_order"),
            item_code=row["item_code"],
            item_description=row["item_description"],
            lot_number=row.get("lot_number"),
            sector=row["sector"],
            operation_code=row.get("operation_code"),
            operation_description=row.get("operation_description"),
            defect_category=row["defect_category"],
            defect_description=row["defect_description"],
            detected_by_user_id=row["detected_by_user_id"],
            detection_date=row["detection_date"],
            defective_quantity=Decimal(str(row["defective_quantity"])),
            inspected_quantity=Decimal(str(row["inspected_quantity"])) if row.get("inspected_quantity") is not None else None,
            severity=row["severity"],
            priority=row["priority"],
            current_status=row["current_status"],
            containment_action_summary=row.get("containment_action_summary"),
            disposition_type=row.get("disposition_type"),
            immediate_cause_notes=row.get("immediate_cause_notes"),
            root_cause_summary=row.get("root_cause_summary"),
            responsible_user_id=row.get("responsible_user_id"),
            due_date=row.get("due_date"),
            closed_at=row.get("closed_at"),
            cancellation_reason=row.get("cancellation_reason"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )