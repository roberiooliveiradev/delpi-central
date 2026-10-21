"""Postgres adapter for integration write-operation tracking.

Schema: ``integration_tracking`` (postgres-plugins pool). Each mutating
method performs the operation update and the append-only event insert in a
single transaction via ``self.db()`` — the two writes commit or rollback
together. No hidden per-statement commits that could break atomicity.
"""

from __future__ import annotations

import logging
from typing import Any

from psycopg.types.json import Jsonb

from app.application.services.integration_tracking.contracts import (
    NewOperationInput,
    TransitionPatch,
)
from app.domain.integrations.integration_operation import (
    IntegrationOperationConflictError,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
    PluginsRepositoryError,
    wrap_plugins_db_error,
)

logger = logging.getLogger(__name__)

_SCHEMA = "integration_tracking"


class PostgresIntegrationOperationRepository(PluginBaseRepository):
    """Implements IntegrationOperationRepository against postgres-plugins."""

    def insert_operation(
        self, data: NewOperationInput, *, schema_version: int
    ) -> None:
        """Atomic: insert operation (CREATED) + event seq 1 in one tx."""
        try:
            with self.db() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"""
                        INSERT INTO {_SCHEMA}.integration_operations (
                            operation_id, correlation_id, request_id,
                            idempotency_key, schema_version,
                            integration, resource, action, resource_key,
                            environment_key, company_scope,
                            caller_app, actor_subject, protheus_user_id,
                            authorization_context,
                            request_payload, outbound_payload,
                            request_hash, outbound_hash, payload_schema_version,
                            status
                        ) VALUES (
                            %s, %s, %s, %s, %s,
                            %s, %s, %s, %s,
                            %s, %s,
                            %s, %s, %s,
                            %s,
                            %s, %s,
                            %s, %s, %s,
                            'CREATED'
                        )
                        """,
                        (
                            data.operation_id,
                            data.correlation_id,
                            data.request_id,
                            data.idempotency_key,
                            schema_version,
                            data.integration,
                            data.resource,
                            data.action,
                            data.resource_key,
                            data.environment_key,
                            data.company_scope,
                            data.caller_app,
                            data.actor_subject,
                            data.protheus_user_id,
                            data.authorization_context,
                            Jsonb(data.request_payload)
                            if data.request_payload is not None
                            else None,
                            Jsonb(data.outbound_payload)
                            if data.outbound_payload is not None
                            else None,
                            data.request_hash,
                            data.outbound_hash,
                            data.payload_schema_version,
                        ),
                    )
                    cursor.execute(
                        f"""
                        INSERT INTO {_SCHEMA}.integration_operation_events (
                            operation_id, sequence_number, event_type,
                            status_from, status_to, event_data, correlation_id
                        ) VALUES (%s, 1, 'operation_created', NULL, 'CREATED',
                                  %s, %s)
                        """,
                        (
                            data.operation_id,
                            Jsonb(
                                {
                                    "integration": data.integration,
                                    "resource": data.resource,
                                    "action": data.action,
                                    "resource_key": data.resource_key,
                                    "environment_key": data.environment_key,
                                }
                            ),
                            data.correlation_id,
                        ),
                    )
                    for record in data.field_provenance:
                        cursor.execute(
                            f"""
                            INSERT INTO {_SCHEMA}.supplier_field_provenance (
                                operation_id, supplier_code, supplier_store,
                                environment_key, field_key,
                                source_type, change_mode,
                                source_id, source_reference,
                                source_retrieved_at,
                                reason_code, review_id, decision_id,
                                initiating_client_id, actor_subject
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s
                            )
                            """,
                            (
                                data.operation_id,
                                record.get("supplier_code"),
                                record.get("supplier_store"),
                                record.get("environment_key"),
                                record.get("field_key"),
                                record.get("source_type"),
                                record.get("change_mode"),
                                record.get("source_id"),
                                record.get("source_reference"),
                                record.get("source_retrieved_at"),
                                record.get("reason_code"),
                                record.get("review_id"),
                                record.get("decision_id"),
                                record.get("initiating_client_id"),
                                record.get("actor_subject"),
                            ),
                        )
                connection.commit()
        except PluginsRepositoryError:
            raise
        except Exception as exc:
            logger.exception(
                "integration_tracking insert_operation failed "
                "operation_id=%s",
                data.operation_id,
            )
            raise wrap_plugins_db_error("insert_operation", exc) from exc

    def apply_transition(
        self,
        operation_id: str,
        *,
        expected_version: int,
        expected_status: str,
        patch: TransitionPatch,
        correlation_id: str | None,
    ) -> None:
        """Atomic: conditional UPDATE (optimistic lock) + append event."""
        try:
            with self.db() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"""
                        UPDATE {_SCHEMA}.integration_operations SET
                            status = %s,
                            response_payload = COALESCE(%s, response_payload),
                            http_status = COALESCE(%s, http_status),
                            upstream_error_code = COALESCE(%s, upstream_error_code),
                            error_details = COALESCE(%s, error_details),
                            confirmation_evidence = COALESCE(%s, confirmation_evidence),
                            attempt_count = COALESCE(%s, attempt_count),
                            resource_key = COALESCE(%s, resource_key),
                            send_started_at = CASE WHEN %s THEN NOW() ELSE send_started_at END,
                            acknowledged_at = CASE WHEN %s THEN NOW() ELSE acknowledged_at END,
                            confirmed_at = CASE WHEN %s THEN NOW() ELSE confirmed_at END,
                            version = version + 1,
                            updated_at = NOW()
                        WHERE operation_id = %s
                          AND version = %s
                          AND status = %s
                        """,
                        (
                            patch.status_to,
                            Jsonb(patch.response_payload)
                            if patch.response_payload is not None
                            else None,
                            patch.http_status,
                            patch.upstream_error_code,
                            Jsonb(patch.error_details)
                            if patch.error_details is not None
                            else None,
                            Jsonb(patch.confirmation_evidence)
                            if patch.confirmation_evidence is not None
                            else None,
                            patch.attempt_count,
                            patch.resource_key,
                            patch.send_started_at,
                            patch.acknowledged_at,
                            patch.confirmed_at,
                            operation_id,
                            expected_version,
                            expected_status,
                        ),
                    )
                    if cursor.rowcount != 1:
                        raise IntegrationOperationConflictError(operation_id)
                    cursor.execute(
                        f"""
                        INSERT INTO {_SCHEMA}.integration_operation_events (
                            operation_id, sequence_number, event_type,
                            status_from, status_to, event_data, correlation_id
                        ) VALUES (
                            %s,
                            COALESCE((
                                SELECT MAX(sequence_number)
                                FROM {_SCHEMA}.integration_operation_events
                                WHERE operation_id = %s
                            ), 0) + 1,
                            %s, %s, %s, %s, %s
                        )
                        """,
                        (
                            operation_id,
                            operation_id,
                            patch.event_type,
                            expected_status,
                            patch.status_to,
                            Jsonb(patch.event_data)
                            if patch.event_data is not None
                            else None,
                            correlation_id,
                        ),
                    )
                connection.commit()
        except IntegrationOperationConflictError:
            raise
        except PluginsRepositoryError:
            raise
        except Exception as exc:
            logger.exception(
                "integration_tracking apply_transition failed "
                "operation_id=%s to=%s",
                operation_id,
                patch.status_to,
            )
            raise wrap_plugins_db_error("apply_transition", exc) from exc

    def get_operation(self, operation_id: str) -> dict[str, Any] | None:
        return self.fetch_one(
            f"""
            SELECT operation_id::text AS operation_id,
                   correlation_id, request_id, idempotency_key,
                   schema_version, integration, resource, action,
                   resource_key, environment_key, company_scope,
                   caller_app, actor_subject, protheus_user_id,
                   authorization_context,
                   request_payload, outbound_payload, response_payload,
                   request_hash, outbound_hash, payload_schema_version,
                   status, http_status, upstream_error_code,
                   error_details, confirmation_evidence,
                   attempt_count, version,
                   created_at, send_started_at, acknowledged_at,
                   confirmed_at, updated_at
            FROM {_SCHEMA}.integration_operations
            WHERE operation_id = %s
            """,
            (operation_id,),
        )

    def list_events(
        self, operation_id: str, *, limit: int, offset: int
    ) -> list[dict[str, Any]]:
        return self.fetch_all(
            f"""
            SELECT event_id::text AS event_id,
                   operation_id::text AS operation_id,
                   sequence_number, event_type,
                   status_from, status_to, event_data,
                   occurred_at, correlation_id
            FROM {_SCHEMA}.integration_operation_events
            WHERE operation_id = %s
            ORDER BY sequence_number ASC
            LIMIT %s OFFSET %s
            """,
            (operation_id, limit, offset),
        )

    def list_supplier_field_provenance(
        self,
        *,
        resource_key: str,
        supplier_code: str | None,
        supplier_store: str | None,
        caller_app: str | None,
        actor_subject: str | None,
        field_key: str | None,
        limit: int,
        offset: int,
    ) -> list[dict[str, Any]]:
        """Provenance rows joined to the operation status authority.

        Scope binding: an S2S caller sees only rows recorded for its own
        client_id; a direct user sees only rows of operations they recorded
        themselves without a service caller.
        """
        return self.fetch_all(
            f"""
            SELECT p.provenance_id::text AS provenance_id,
                   p.operation_id::text AS operation_id,
                   p.supplier_code, p.supplier_store,
                   p.environment_key, p.field_key,
                   p.source_type, p.change_mode,
                   p.source_id, p.source_reference,
                   p.source_retrieved_at,
                   p.reason_code, p.review_id, p.decision_id,
                   p.initiating_client_id, p.actor_subject,
                   p.provenance_schema_version, p.created_at,
                   op.status AS operation_status,
                   op.action AS operation_action,
                   op.confirmed_at AS operation_confirmed_at,
                   op.created_at AS operation_created_at
            FROM {_SCHEMA}.supplier_field_provenance p
            JOIN {_SCHEMA}.integration_operations op
              ON op.operation_id = p.operation_id
            WHERE op.integration = 'protheus'
              AND op.resource = 'supplier'
              AND (
                    op.resource_key = %s
                    OR (p.supplier_code = %s AND p.supplier_store = %s)
                  )
              AND (
                    (%s IS NOT NULL AND op.caller_app = %s)
                    OR (%s IS NULL AND op.caller_app IS NULL
                        AND op.actor_subject = %s)
                  )
              AND (%s IS NULL OR p.field_key = %s)
            ORDER BY p.created_at DESC, p.provenance_id
            LIMIT %s OFFSET %s
            """,
            (
                resource_key,
                supplier_code,
                supplier_store,
                caller_app,
                caller_app,
                caller_app,
                actor_subject,
                field_key,
                field_key,
                limit,
                offset,
            ),
        )
