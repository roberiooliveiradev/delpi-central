from __future__ import annotations

from typing import Any

from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)


class PostgresQualityLabelsChecklistTemplateRepository(PluginBaseRepository):
    """Template padrão do checklist do Certificado de Qualidade (RQ-032)."""

    def list_active(self) -> list[dict[str, Any]]:
        return self.fetch_all(
            """
            SELECT id, position, description
              FROM quality_labels.checklist_template_items
             WHERE is_active = TRUE
             ORDER BY position ASC
            """
        )

    @staticmethod
    def to_payload(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "position": row.get("position"),
            "description": row.get("description"),
        }
