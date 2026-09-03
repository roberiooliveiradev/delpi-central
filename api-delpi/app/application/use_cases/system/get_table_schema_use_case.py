# app/application/use_cases/system/get_table_schema_use_case.py
"""Schema agregado Protheus — contrato composite_analysis (Playbook 10).

Entrega seções nomeadas `{items, total, truncated}` + summary escalar,
no mesmo padrão de factory-status / safety-stock detail — não listas planas.
"""

from __future__ import annotations

from typing import Any

from app.application.dto.system.system_requests import GetTableSchemaRequest
from app.application.services.composite_sections_builder import (
    PROTHEUS_TABLE_SCHEMA_SECTIONS,
    build_composite_sections,
    build_section_block,
)
from app.domain.ports.system.system_repository_port import SystemRepositoryPort

_SCHEMA_COLUMN_PAGE_SIZE = 500
# Catálogo técnico: relações SX9 podem ser centenas — cap no aggregate (total preservado).
_SCHEMA_RELATIONS_LIMIT = 100


class GetTableSchemaUseCase:

    def __init__(self, repository: SystemRepositoryPort):
        self._repository = repository

    def execute(self, request: GetTableSchemaRequest) -> dict[str, Any]:
        table_rows = self._repository.get_table(request.table_name)
        table = self._first_dict(table_rows)
        columns = self._load_all_columns(request.table_name)
        indexes = self._as_dict_list(self._repository.get_table_indexes(request.table_name))
        relations = self._as_dict_list(self._repository.get_table_relations(request.table_name))

        table_name = str(
            table.get("TableName")
            or table.get("X2_ARQUIVO")
            or request.table_name
            or ""
        ).strip()
        alias = str(table.get("X2_CHAVE") or "").strip()
        description = str(table.get("X2_NOME") or "").strip()

        return {
            "summary": {
                "tableName": table_name,
                "alias": alias,
                "description": description,
                "columnCount": len(columns),
                "indexCount": len(indexes),
                "relationCount": len(relations),
            },
            "columns": build_section_block(columns),
            "indexes": build_section_block(indexes),
            "relations": build_section_block(
                relations,
                limit=_SCHEMA_RELATIONS_LIMIT,
            ),
            "table": build_section_block([table] if table else []),
        }

    @classmethod
    def build_sections(cls, data: dict[str, Any]) -> list[dict[str, Any]]:
        return build_composite_sections(
            data,
            section_keys=PROTHEUS_TABLE_SCHEMA_SECTIONS,
        )

    def _load_all_columns(self, table_name: str) -> list[dict]:
        page = 1
        collected: list[dict] = []
        total = None

        while True:
            page_result = self._repository.get_columns_table(
                table_name=table_name,
                page=page,
                page_size=_SCHEMA_COLUMN_PAGE_SIZE,
            )
            batch = self._as_dict_list(page_result.get("results"))
            collected.extend(batch)

            if total is None:
                try:
                    total = int(page_result.get("total") or 0)
                except (TypeError, ValueError):
                    total = len(batch)

            if not batch or len(collected) >= total:
                break

            page += 1

            if page > 50:
                break

        return collected

    @staticmethod
    def _first_dict(value: Any) -> dict:
        if isinstance(value, dict):
            return value

        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    return item

        return {}

    @staticmethod
    def _as_dict_list(value: Any) -> list[dict]:
        if not isinstance(value, list):
            return []

        return [item for item in value if isinstance(item, dict)]
