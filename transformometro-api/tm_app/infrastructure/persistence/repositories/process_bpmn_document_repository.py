from __future__ import annotations

from typing import Any

from tm_app.domain.entities.process_bpmn_document import (
    ProcessBpmnDocument,
    ProcessBpmnRevision,
)
from tm_app.domain.ports.process_bpmn_document_repository_port import (
    ProcessBpmnDocumentRepositoryPort,
)
from tm_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)

_S = "transformometro"

_DOC_SELECT = f"""
SELECT
    d.document_id AS id,
    d.processo_id,
    d.working_copy_xml,
    d.working_copy_sha256,
    d.version,
    d.created_by_user_id,
    d.updated_by_user_id,
    d.created_at,
    d.updated_at
FROM {_S}.processo_bpmn_documents d
"""

_REV_SELECT = f"""
SELECT
    r.revision_id AS id,
    r.document_id,
    r.revision_number,
    r.artifact_sha256,
    r.origin,
    r.restored_from_revision_id,
    src.revision_number AS source_revision_number,
    r.name,
    r.description,
    r.created_by_user_id,
    r.created_by_name,
    r.created_at,
    {{artifact}}
FROM {_S}.processo_bpmn_revisions r
LEFT JOIN {_S}.processo_bpmn_revisions src
    ON src.revision_id = r.restored_from_revision_id
"""


def _doc(row: dict[str, Any] | None) -> ProcessBpmnDocument | None:
    if not row:
        return None
    return ProcessBpmnDocument(
        id=str(row["id"]),
        processo_id=str(row["processo_id"]),
        working_copy_xml=str(row["working_copy_xml"]),
        working_copy_sha256=str(row["working_copy_sha256"]),
        version=int(row["version"]),
        created_by_user_id=str(row["created_by_user_id"] or ""),
        updated_by_user_id=str(row["updated_by_user_id"] or ""),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


def _rev(row: dict[str, Any] | None) -> ProcessBpmnRevision | None:
    if not row:
        return None
    return ProcessBpmnRevision(
        id=str(row["id"]),
        document_id=str(row["document_id"]),
        revision_number=int(row["revision_number"]),
        artifact_sha256=str(row["artifact_sha256"]),
        origin=str(row["origin"]),
        restored_from_revision_id=(
            str(row["restored_from_revision_id"])
            if row.get("restored_from_revision_id")
            else None
        ),
        name=row.get("name"),
        description=row.get("description"),
        created_by_user_id=str(row["created_by_user_id"] or ""),
        created_by_name=row.get("created_by_name"),
        source_revision_number=row.get("source_revision_number"),
        created_at=row.get("created_at"),
        artifact_xml=row.get("artifact_xml"),
    )


class ProcessBpmnDocumentRepository(
    PluginBaseRepository, ProcessBpmnDocumentRepositoryPort
):
    """Documento BPMN nativo do processo — ownership Transformômetro (G7)."""

    def process_exists(self, processo_id: str) -> bool:
        row = self.fetch_one(
            f"""
            SELECT 1 AS ok
            FROM {_S}.processos
            WHERE processo_id = %s::uuid AND deletado = FALSE
            """,
            (processo_id,),
        )
        return row is not None

    def get_active(self, processo_id: str) -> ProcessBpmnDocument | None:
        row = self.fetch_one(
            f"""
            {_DOC_SELECT}
            WHERE d.processo_id = %s::uuid
              AND d.deleted_at IS NULL
            """,
            (processo_id,),
        )
        return _doc(row)

    def has_active(self, processo_id: str) -> bool:
        row = self.fetch_one(
            f"""
            SELECT 1 AS ok
            FROM {_S}.processo_bpmn_documents
            WHERE processo_id = %s::uuid AND deleted_at IS NULL
            """,
            (processo_id,),
        )
        return row is not None

    def create(
        self,
        *,
        processo_id: str,
        working_copy_xml: str,
        working_copy_sha256: str,
        actor_user_id: str,
    ) -> ProcessBpmnDocument:
        self.execute(
            f"""
            INSERT INTO {_S}.processo_bpmn_documents (
                processo_id, working_copy_xml, working_copy_sha256,
                version, created_by_user_id, updated_by_user_id
            ) VALUES (%s::uuid, %s, %s, 1, %s, %s)
            """,
            (
                processo_id,
                working_copy_xml,
                working_copy_sha256,
                actor_user_id,
                actor_user_id,
            ),
        )
        created = self.get_active(processo_id)
        if created is None:
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        return created

    def update_working_copy(
        self,
        *,
        document_id: str,
        working_copy_xml: str,
        working_copy_sha256: str,
        expected_version: int,
        actor_user_id: str,
    ) -> ProcessBpmnDocument | None:
        row = self.execute_returning_one(
            f"""
            UPDATE {_S}.processo_bpmn_documents
            SET working_copy_xml = %s,
                working_copy_sha256 = %s,
                version = version + 1,
                updated_by_user_id = %s,
                updated_at = NOW()
            WHERE document_id = %s::uuid
              AND version = %s
              AND deleted_at IS NULL
            RETURNING processo_id
            """,
            (
                working_copy_xml,
                working_copy_sha256,
                actor_user_id,
                document_id,
                expected_version,
            ),
        )
        if row is None:
            return None
        return self.get_active(str(row["processo_id"]))

    def soft_delete(
        self,
        *,
        processo_id: str,
        actor_user_id: str,
    ) -> ProcessBpmnDocument | None:
        removed = self.get_active(processo_id)
        if removed is None:
            return None
        self.execute(
            f"""
            UPDATE {_S}.processo_bpmn_documents
            SET deleted_at = NOW(),
                updated_by_user_id = %s,
                updated_at = NOW()
            WHERE processo_id = %s::uuid
              AND deleted_at IS NULL
            """,
            (actor_user_id, processo_id),
        )
        return removed

    def list_revisions(self, document_id: str) -> list[ProcessBpmnRevision]:
        rows = self.fetch_all(
            _REV_SELECT.format(artifact="NULL AS artifact_xml")
            + """
            WHERE r.document_id = %s::uuid
            ORDER BY r.revision_number DESC
            """,
            (document_id,),
        )
        return [rev for row in rows if (rev := _rev(row)) is not None]

    def get_revision(
        self,
        document_id: str,
        revision_number: int,
        *,
        with_artifact: bool = False,
    ) -> ProcessBpmnRevision | None:
        artifact_col = (
            "r.artifact_xml" if with_artifact else "NULL AS artifact_xml"
        )
        row = self.fetch_one(
            _REV_SELECT.format(artifact=artifact_col)
            + """
            WHERE r.document_id = %s::uuid
              AND r.revision_number = %s
            """,
            (document_id, revision_number),
        )
        return _rev(row)

    def get_latest_revision_number(self, document_id: str) -> int | None:
        row = self.fetch_one(
            f"""
            SELECT MAX(revision_number) AS latest
            FROM {_S}.processo_bpmn_revisions
            WHERE document_id = %s::uuid
            """,
            (document_id,),
        )
        latest = (row or {}).get("latest")
        return int(latest) if latest is not None else None

    def create_revision(
        self,
        *,
        document_id: str,
        artifact_xml: str,
        artifact_sha256: str,
        origin: str,
        restored_from_revision_id: str | None,
        name: str | None,
        description: str | None,
        actor_user_id: str,
        actor_name: str | None,
        expected_version: int,
    ) -> ProcessBpmnRevision | None:
        """Checkpoint atômico sob guard de versão: snapshot do working copy
        atual + número sequencial, numa única transação."""
        with self.db() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT 1 FROM {_S}.processo_bpmn_documents
                    WHERE document_id = %s::uuid
                      AND version = %s
                      AND deleted_at IS NULL
                    FOR UPDATE
                    """,
                    (document_id, expected_version),
                )
                if cursor.fetchone() is None:
                    conn.rollback()
                    return None
                cursor.execute(
                    f"""
                    INSERT INTO {_S}.processo_bpmn_revisions (
                        document_id, revision_number,
                        artifact_xml, artifact_sha256, origin,
                        restored_from_revision_id, name, description,
                        created_by_user_id, created_by_name
                    )
                    SELECT
                        %s::uuid,
                        COALESCE(MAX(revision_number), 0) + 1,
                        %s, %s, %s, %s::uuid, %s, %s, %s, %s
                    FROM {_S}.processo_bpmn_revisions
                    WHERE document_id = %s::uuid
                    RETURNING revision_id, revision_number
                    """,
                    (
                        document_id,
                        artifact_xml,
                        artifact_sha256,
                        origin,
                        restored_from_revision_id,
                        name,
                        description,
                        actor_user_id,
                        actor_name,
                        document_id,
                    ),
                )
                created = cursor.fetchone()
            conn.commit()
        if created is None:
            return None
        return self.get_revision(document_id, int(created["revision_number"]))

    def restore_revision(
        self,
        *,
        document_id: str,
        revision_number: int,
        expected_version: int,
        actor_user_id: str,
        actor_name: str | None,
    ) -> tuple[ProcessBpmnDocument, ProcessBpmnRevision] | None:
        """Restore transacional (mesma semântica do Modeler):
        working_copy ← artefato + bump version + nova revisão 'restore'
        com proveniência — tudo ou nada."""
        target = self.get_revision(document_id, revision_number, with_artifact=True)
        if target is None or target.artifact_xml is None:
            return None

        with self.db() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    UPDATE {_S}.processo_bpmn_documents
                    SET working_copy_xml = %s,
                        working_copy_sha256 = %s,
                        version = version + 1,
                        updated_by_user_id = %s,
                        updated_at = NOW()
                    WHERE document_id = %s::uuid
                      AND version = %s
                      AND deleted_at IS NULL
                    RETURNING processo_id, version
                    """,
                    (
                        target.artifact_xml,
                        target.artifact_sha256,
                        actor_user_id,
                        document_id,
                        expected_version,
                    ),
                )
                updated = cursor.fetchone()
                if updated is None:
                    conn.rollback()
                    return None
                cursor.execute(
                    f"""
                    INSERT INTO {_S}.processo_bpmn_revisions (
                        document_id, revision_number,
                        artifact_xml, artifact_sha256, origin,
                        restored_from_revision_id, name, description,
                        created_by_user_id, created_by_name
                    )
                    SELECT
                        %s::uuid,
                        COALESCE(MAX(revision_number), 0) + 1,
                        %s, %s, 'restore', %s::uuid, NULL, NULL, %s, %s
                    FROM {_S}.processo_bpmn_revisions
                    WHERE document_id = %s::uuid
                    RETURNING revision_id, revision_number
                    """,
                    (
                        document_id,
                        target.artifact_xml,
                        target.artifact_sha256,
                        target.id,
                        actor_user_id,
                        actor_name,
                        document_id,
                    ),
                )
                created = cursor.fetchone()
            conn.commit()

        doc = self.get_active(str(updated["processo_id"]))
        rev = self.get_revision(document_id, int(created["revision_number"]))
        if doc is None or rev is None:
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        return doc, rev
