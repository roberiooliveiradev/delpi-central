from __future__ import annotations

from typing import Any

from tm_app.domain.entities.process_bpmn_reference import ProcessBpmnReference
from tm_app.domain.ports.process_bpmn_reference_repository_port import (
    ProcessBpmnReferenceRepositoryPort,
)
from tm_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)

_S = "transformometro"

_SELECT = f"""
SELECT
    r.reference_id AS id,
    r.processo_id,
    r.bpmn_model_id,
    r.bpmn_revision_number,
    r.created_by_user_id,
    r.updated_by_user_id,
    r.created_at,
    r.updated_at
FROM {_S}.processo_bpmn_references r
"""


def _ref(row: dict[str, Any] | None) -> ProcessBpmnReference | None:
    if not row:
        return None
    return ProcessBpmnReference(
        id=str(row["id"]),
        processo_id=str(row["processo_id"]),
        bpmn_model_id=str(row["bpmn_model_id"]),
        bpmn_revision_number=int(row["bpmn_revision_number"]),
        created_by_user_id=str(row["created_by_user_id"] or ""),
        updated_by_user_id=str(row["updated_by_user_id"] or ""),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


class ProcessBpmnReferenceRepository(
    PluginBaseRepository, ProcessBpmnReferenceRepositoryPort
):
    """Transformômetro-owned reference table. NEVER queries bpmn_modeler.* —
    cross-context resolution goes through the BPMN Modeler HTTP contract."""

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

    def get_active(self, processo_id: str) -> ProcessBpmnReference | None:
        row = self.fetch_one(
            f"""
            {_SELECT}
            WHERE r.processo_id = %s::uuid
              AND r.deleted_at IS NULL
            """,
            (processo_id,),
        )
        return _ref(row)

    def upsert(
        self,
        *,
        processo_id: str,
        bpmn_model_id: str,
        bpmn_revision_number: int,
        actor_user_id: str,
    ) -> tuple[ProcessBpmnReference, ProcessBpmnReference | None]:
        previous = self.get_active(processo_id)
        if previous is None:
            self.execute(
                f"""
                INSERT INTO {_S}.processo_bpmn_references (
                    processo_id, bpmn_model_id, bpmn_revision_number,
                    created_by_user_id, updated_by_user_id
                ) VALUES (%s::uuid, %s::uuid, %s, %s, %s)
                """,
                (
                    processo_id,
                    bpmn_model_id,
                    bpmn_revision_number,
                    actor_user_id,
                    actor_user_id,
                ),
            )
        else:
            self.execute(
                f"""
                UPDATE {_S}.processo_bpmn_references
                SET bpmn_model_id = %s::uuid,
                    bpmn_revision_number = %s,
                    updated_by_user_id = %s,
                    updated_at = NOW()
                WHERE processo_id = %s::uuid
                  AND deleted_at IS NULL
                """,
                (
                    bpmn_model_id,
                    bpmn_revision_number,
                    actor_user_id,
                    processo_id,
                ),
            )
        current = self.get_active(processo_id)
        if current is None:
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        if (
            current.bpmn_model_id != bpmn_model_id
            or current.bpmn_revision_number != bpmn_revision_number
        ):
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        return current, previous

    def soft_delete(
        self,
        *,
        processo_id: str,
        actor_user_id: str,
    ) -> ProcessBpmnReference | None:
        removed = self.get_active(processo_id)
        if removed is None:
            return None
        self.execute(
            f"""
            UPDATE {_S}.processo_bpmn_references
            SET deleted_at = NOW(),
                updated_by_user_id = %s,
                updated_at = NOW()
            WHERE processo_id = %s::uuid
              AND deleted_at IS NULL
            """,
            (actor_user_id, processo_id),
        )
        if self.get_active(processo_id) is not None:
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        return removed
