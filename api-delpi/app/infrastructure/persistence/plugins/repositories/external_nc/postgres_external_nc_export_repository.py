# app/infrastructure/persistence/plugins/repositories/external_nc/postgres_external_nc_export_repository.py
from __future__ import annotations

from app.domain.ports.external_nc.external_nc_export_repository import (
    ExternalNcExportRepositoryPort,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)


class PostgresExternalNcExportRepository(
    PluginBaseRepository,
    ExternalNcExportRepositoryPort,
):
    def get_nonconformity_export_payload(self, nonconformity_id: str) -> dict | None:
        nonconformity = self.fetch_one(
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

        if nonconformity is None:
            return None

        root_causes = self.fetch_all(
            """
            SELECT
                id,
                nonconformity_id,
                analysis_method,
                cause_dimension,
                category,
                why_level,
                description,
                is_root_cause,
                created_by_user_id,
                created_at
            FROM quality.external_nc_root_causes
            WHERE nonconformity_id = %s
            ORDER BY is_root_cause DESC, created_at ASC
            """,
            (nonconformity_id,),
        )

        actions = self.fetch_all(
            """
            SELECT
                id,
                nonconformity_id,
                root_cause_id,
                action_type,
                title,
                description,
                responsible_user_id,
                responsible_external_name,
                responsible_external_email,
                start_date,
                due_date,
                completed_at,
                status,
                verification_required,
                effectiveness_due_date,
                completion_notes,
                created_by_user_id,
                created_at,
                updated_at
            FROM quality.external_nc_actions
            WHERE nonconformity_id = %s
            ORDER BY created_at ASC
            """,
            (nonconformity_id,),
        )

        effectiveness_checks = self.fetch_all(
            """
            SELECT
                id,
                nonconformity_id,
                action_id,
                checked_by_user_id,
                checked_at,
                criteria,
                result,
                notes,
                next_action,
                created_at
            FROM quality.external_nc_effectiveness_checks
            WHERE nonconformity_id = %s
            ORDER BY checked_at DESC, created_at DESC
            """,
            (nonconformity_id,),
        )

        comments = self.fetch_all(
            """
            SELECT
                id,
                nonconformity_id,
                comment_type,
                content,
                is_internal,
                created_by_user_id,
                created_at
            FROM quality.external_nc_comments
            WHERE nonconformity_id = %s
            ORDER BY created_at ASC
            """,
            (nonconformity_id,),
        )

        attachments = self.fetch_all(
            """
            SELECT
                id,
                nonconformity_id,
                action_id,
                effectiveness_check_id,
                file_name,
                original_name,
                mime_type,
                size_bytes,
                storage_provider,
                storage_path,
                checksum,
                uploaded_by_user_id,
                uploaded_at
            FROM quality.external_nc_attachments
            WHERE nonconformity_id = %s
               OR action_id IN (
                    SELECT id
                    FROM quality.external_nc_actions
                    WHERE nonconformity_id = %s
               )
               OR effectiveness_check_id IN (
                    SELECT id
                    FROM quality.external_nc_effectiveness_checks
                    WHERE nonconformity_id = %s
               )
            ORDER BY uploaded_at ASC
            """,
            (nonconformity_id, nonconformity_id, nonconformity_id),
        )

        team_members = self.fetch_all(
            """
            SELECT
                id,
                nonconformity_id,
                user_id,
                role_in_case,
                joined_at
            FROM quality.external_nc_team_members
            WHERE nonconformity_id = %s
            ORDER BY joined_at ASC
            """,
            (nonconformity_id,),
        )

        audit_events = self.fetch_all(
            """
            SELECT
                id,
                nonconformity_id,
                event_type,
                actor_user_id,
                payload_json,
                created_at
            FROM quality.external_nc_audit_events
            WHERE nonconformity_id = %s
            ORDER BY created_at ASC
            """,
            (nonconformity_id,),
        )

        return {
            "nonconformity": nonconformity,
            "root_causes": root_causes,
            "actions": actions,
            "effectiveness_checks": effectiveness_checks,
            "comments": comments,
            "attachments": attachments,
            "team_members": team_members,
            "audit_events": audit_events,
        }