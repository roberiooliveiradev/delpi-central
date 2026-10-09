"""Persistence for G8 migration metadata (transformometro.processo_bpmn_migrations)."""

from __future__ import annotations

import json
from typing import Any

from tm_app.domain.ports.process_bpmn_migration_repository_port import (
    ProcessBpmnMigrationRepositoryPort,
)
from tm_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)

_S = "transformometro"


class ProcessBpmnMigrationRepository(
    PluginBaseRepository, ProcessBpmnMigrationRepositoryPort
):
    """Migration provenance records — written once at migration commit."""

    def record_migration(
        self,
        *,
        processo_id: str,
        document_id: str,
        revision_id: str,
        legacy_source_fingerprint: str,
        candidate_sha256: str,
        mapping_report: dict[str, Any],
        source_summary: dict[str, Any],
        actor_user_id: str,
        actor_name: str | None,
    ) -> dict[str, Any]:
        row = self.execute_returning_one(
            f"""
            INSERT INTO {_S}.processo_bpmn_migrations (
                processo_id, document_id, revision_id,
                legacy_source_fingerprint, candidate_sha256,
                mapping_report, source_summary,
                migrated_by_user_id, migrated_by_name
            ) VALUES (
                %s::uuid, %s::uuid, %s::uuid, %s, %s,
                %s::jsonb, %s::jsonb, %s, %s
            )
            RETURNING migration_id, created_at
            """,
            (
                processo_id,
                document_id,
                revision_id,
                legacy_source_fingerprint,
                candidate_sha256,
                json.dumps(mapping_report, ensure_ascii=False, default=str),
                json.dumps(source_summary, ensure_ascii=False, default=str),
                actor_user_id,
                actor_name,
            ),
        )
        return dict(row or {})

    def latest_for_processo(self, processo_id: str) -> dict[str, Any] | None:
        row = self.fetch_one(
            f"""
            SELECT migration_id, processo_id, document_id, revision_id,
                   legacy_source_fingerprint, candidate_sha256,
                   source_summary, migrated_by_user_id, migrated_by_name,
                   created_at
            FROM {_S}.processo_bpmn_migrations
            WHERE processo_id = %s::uuid
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (processo_id,),
        )
        return dict(row) if row is not None else None
