"""G8 — ACT use case: commit a sealed legacy→BPMN migration proposal.

Contract:
- Revalidates native/external XOR at write time (fresh state, not the
  PREPARE-time check — stale proposals are refused upstream by the
  fingerprint, this is defense in depth).
- Persists: native BPMN document (working copy = sealed candidate) +
  BPMN Revision 1 (origin='migration') + external migration metadata
  row — sequential writes with fail-closed compensation (the document
  is soft-deleted if any later step fails).
- NEVER mutates flowchart_v1, instance_diagram_scope or
  revision_diagram_overlay.
- NEVER writes to bpmn_modeler.* — the artifact stays inside
  transformometro.* ownership.
- Authoritative read-back: working_copy_sha256 must equal the sealed
  candidate checksum; revision must exist with origin='migration'.
"""

from __future__ import annotations

import hashlib
from typing import Any

from tm_app.application.use_cases.manage_process_bpmn_document import (
    DualModeConflict,
    ProcessBpmnDocumentUseCases,
)
from tm_app.domain.ports.process_bpmn_document_repository_port import (
    ProcessBpmnDocumentRepositoryPort,
)
from tm_app.domain.ports.process_bpmn_migration_repository_port import (
    ProcessBpmnMigrationRepositoryPort,
)
from tm_app.domain.ports.process_bpmn_reference_repository_port import (
    ProcessBpmnReferenceRepositoryPort,
)


class MigrationExecutionError(RuntimeError):
    """Write failed mid-commit; compensation attempted."""

    status_code = 409


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class MigrateLegacyDiagramToBpmnUseCase:
    def __init__(
        self,
        docs: ProcessBpmnDocumentRepositoryPort,
        refs: ProcessBpmnReferenceRepositoryPort,
        migrations: ProcessBpmnMigrationRepositoryPort,
        document_use_cases: ProcessBpmnDocumentUseCases,
    ) -> None:
        self._docs = docs
        self._refs = refs
        self._migrations = migrations
        self._document_use_cases = document_use_cases

    def commit(
        self,
        user: Any,
        *,
        processo_id: str,
        candidate_xml: str,
        candidate_sha256: str,
        legacy_source_fingerprint: str,
        mapping_report: dict[str, Any],
        source_summary: dict[str, Any],
        revision_name: str | None = None,
    ) -> dict[str, Any]:
        """Persist the sealed candidate as the native BPMN document."""
        pid = str(processo_id or "").strip()
        actor_user_id = str(getattr(user, "id", "") or getattr(user, "sub", ""))
        actor_name = (
            str(getattr(user, "name", "") or getattr(user, "display_name", ""))
            or None
        )

        # Fresh XOR revalidation — never trust PREPARE-time state.
        if self._docs.has_active(pid):
            raise DualModeConflict("NATIVE_BPMN_ALREADY_EXISTS")
        if self._refs.get_active(pid) is not None:
            raise DualModeConflict("dual_mode_forbidden")
        if _sha256(candidate_xml) != candidate_sha256:
            raise MigrationExecutionError("Sealed candidate checksum mismatch.")

        # 1) Create the native document via the canonical G7 use case
        #    (boundary validation + intake safety + sha + XOR inside).
        doc = self._document_use_cases.create_document(
            user, pid, candidate_xml
        )

        try:
            # 2) Revision 1 — provenance origin='migration' (V054).
            rev = self._docs.create_revision(
                document_id=doc.id,
                artifact_xml=doc.working_copy_xml,
                artifact_sha256=doc.working_copy_sha256,
                origin="migration",
                restored_from_revision_id=None,
                name=revision_name or "R1 — migração do mapeamento legado",
                description=(
                    "Revisão inicial criada pela migração governada "
                    "flowchart_v1 → BPMN nativo (G8/TÉO)."
                ),
                actor_user_id=actor_user_id,
                actor_name=actor_name,
                expected_version=doc.version,
            )
            if rev is None:
                raise MigrationExecutionError(
                    "Revision write failed (stale document version)."
                )

            # 3) External migration metadata — legacy is never touched.
            migration_row = self._migrations.record_migration(
                processo_id=pid,
                document_id=doc.id,
                revision_id=rev.id,
                legacy_source_fingerprint=legacy_source_fingerprint,
                candidate_sha256=candidate_sha256,
                mapping_report=mapping_report,
                source_summary=source_summary,
                actor_user_id=actor_user_id,
                actor_name=actor_name,
            )
        except Exception:
            # Fail-closed compensation: never leave a half-migrated
            # native document active.
            try:
                self._docs.soft_delete(processo_id=pid, actor_user_id=actor_user_id)
            except Exception:
                pass
            raise

        # ---- Authoritative read-back --------------------------------------
        read_back = self._docs.get_active(pid)
        if read_back is None:
            raise MigrationExecutionError("Read-back: document not found.")
        if read_back.working_copy_sha256 != candidate_sha256:
            raise MigrationExecutionError("Read-back: checksum mismatch.")
        revisions = self._docs.list_revisions(doc.id)
        r1 = next((r for r in revisions if r.revision_number == 1), None)
        if r1 is None or getattr(r1, "origin", None) != "migration":
            raise MigrationExecutionError("Read-back: revision R1 missing.")

        return {
            "document_id": doc.id,
            "revision_id": rev.id,
            "revision_number": rev.revision_number,
            "migration_id": migration_row.get("migration_id"),
            "working_copy_sha256": read_back.working_copy_sha256,
            "persisted": True,
            "verified": True,
        }
