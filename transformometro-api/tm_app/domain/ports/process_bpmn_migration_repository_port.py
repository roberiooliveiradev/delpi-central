"""Port for G8 migration metadata records (processo_bpmn_migrations)."""

from __future__ import annotations

from typing import Any, Protocol


class ProcessBpmnMigrationRepositoryPort(Protocol):
    """External migration metadata — the legacy artifact is never mutated;
    provenance lives in transformometro.processo_bpmn_migrations."""

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
    ) -> dict[str, Any]: ...

    def latest_for_processo(self, processo_id: str) -> dict[str, Any] | None: ...
