from __future__ import annotations

from typing import Any

from app.infrastructure.persistence.plugins.plugin_base_repository import PluginBaseRepository

_EVIDENCE_SELECT = """
    SELECT e.id,
           e.kaizen_id,
           e.revision_id,
           e.type,
           e.stage,
           e.file_name,
           e.stored_name,
           e.mime_type,
           e.size_bytes,
           e.description,
           e.external_url,
           e.uploaded_by_user_id,
           e.uploaded_by_name,
           e.created_at
      FROM quality.kaizen_evidences e
"""

_VALID_TYPES = {"attachment", "photo", "document", "link"}
_VALID_STAGES = {"antes", "depois", "geral"}


class PostgresKaizenEvidenceRepository(PluginBaseRepository):
    def list_evidences(self, kaizen_id: str) -> list[dict[str, Any]]:
        return self.fetch_all(
            f"""
            {_EVIDENCE_SELECT}
             WHERE e.kaizen_id = %s
               AND e.deleted_at IS NULL
             ORDER BY CASE e.stage WHEN 'antes' THEN 0 WHEN 'depois' THEN 1 ELSE 2 END,
                      e.created_at DESC
            """,
            (kaizen_id,),
        )

    def get_evidence(self, kaizen_id: str, evidence_id: str) -> dict[str, Any] | None:
        return self.fetch_one(
            f"""
            {_EVIDENCE_SELECT}
             WHERE e.kaizen_id = %s
               AND e.id = %s
               AND e.deleted_at IS NULL
            """,
            (kaizen_id, evidence_id),
        )

    def create_evidence(self, kaizen_id: str, fields: dict[str, Any]) -> dict[str, Any]:
        evidence_type = fields.get("type", "attachment")
        if evidence_type not in _VALID_TYPES:
            evidence_type = "attachment"
        stage = fields.get("stage", "geral")
        if stage not in _VALID_STAGES:
            stage = "geral"

        row = self.execute_returning_one(
            """
            INSERT INTO quality.kaizen_evidences (
                kaizen_id, revision_id, type, stage, file_name, stored_name, mime_type, size_bytes,
                description, external_url, uploaded_by_user_id, uploaded_by_name
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                kaizen_id,
                fields.get("revision_id"),
                evidence_type,
                stage,
                fields.get("file_name"),
                fields.get("stored_name"),
                fields.get("mime_type"),
                fields.get("size_bytes"),
                fields.get("description"),
                fields.get("external_url"),
                fields.get("uploaded_by_user_id", "unknown"),
                fields.get("uploaded_by_name"),
            ),
        )
        created = self.get_evidence(kaizen_id, str(row["id"])) if row else None
        return created or {}

    def update_evidence(
        self,
        kaizen_id: str,
        evidence_id: str,
        fields: dict[str, Any],
    ) -> dict[str, Any] | None:
        sets: list[str] = []
        params: list[Any] = []
        if "stage" in fields:
            stage = fields["stage"] if fields["stage"] in _VALID_STAGES else "geral"
            sets.append("stage = %s")
            params.append(stage)
        if "description" in fields:
            sets.append("description = %s")
            params.append(fields["description"])
        if not sets:
            return self.get_evidence(kaizen_id, evidence_id)

        params.extend([kaizen_id, evidence_id])
        row = self.execute_returning_one(
            f"""
            UPDATE quality.kaizen_evidences
               SET {", ".join(sets)}
             WHERE kaizen_id = %s
               AND id = %s
               AND deleted_at IS NULL
            RETURNING id
            """,
            tuple(params),
        )
        if not row:
            return None
        return self.get_evidence(kaizen_id, evidence_id)

    def delete_evidence(self, kaizen_id: str, evidence_id: str) -> dict[str, Any] | None:
        row = self.execute_returning_one(
            """
            UPDATE quality.kaizen_evidences
               SET deleted_at = NOW()
             WHERE kaizen_id = %s
               AND id = %s
               AND deleted_at IS NULL
            RETURNING id, stored_name
            """,
            (kaizen_id, evidence_id),
        )
        return row
