"""Índice recursivo da estrutura SG1010 — profundidade, pai e códigos para validação."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)


@dataclass(frozen=True)
class StructureIndexRow:
    code: str
    description: str
    type: str
    depth: int
    parent_code: str | None
    path: tuple[str, ...]


class ChatDrawingStructureIndexService:
    @classmethod
    def flatten_items(cls, structure: dict[str, Any] | None) -> tuple[StructureIndexRow, ...]:
        if not isinstance(structure, dict):
            return ()

        rows: list[StructureIndexRow] = []
        items = structure.get("items")

        if not isinstance(items, list):
            return ()

        cls._walk_items(
            items,
            depth=ChatDrawingPatternsService.structure_root_depth(),
            parent_code=None,
            path=(),
            rows=rows,
        )
        return tuple(rows)

    @classmethod
    def collect_all_codes(cls, root: dict[str, Any], product_code: str) -> set[str]:
        root_code = ChatProductQueryIntentService.normalize_product_code(product_code)
        structure = root.get("structure") if isinstance(root.get("structure"), dict) else {}
        codes: set[str] = set()

        for row in cls.flatten_items(structure):
            if row.code and row.code != root_code:
                codes.add(row.code)

        return codes

    @classmethod
    def collect_bom_line_codes(cls, root: dict[str, Any], product_code: str) -> set[str]:
        """Códigos de linha BOM na API — nível 1 + PI/PA/50xx aninhados; MPs sob PI ficam de fora."""
        root_code = ChatProductQueryIntentService.normalize_product_code(product_code)
        structure = root.get("structure") if isinstance(root.get("structure"), dict) else {}
        codes: set[str] = set()

        for row in cls.flatten_items(structure):
            if not row.code or row.code == root_code:
                continue

            item_type = str(row.type or "").strip().upper()

            if row.depth == ChatDrawingPatternsService.structure_root_depth():
                codes.add(row.code)
                continue

            if (
                item_type in ChatDrawingPatternsService.nested_bom_line_types()
                or ChatDrawingPatternsService.is_intermediate_family(row.code)
            ):
                codes.add(row.code)

        return codes

    @classmethod
    def collect_child_cable_parent_map(
        cls,
        root: dict[str, Any],
    ) -> dict[str, set[str]]:
        structure = root.get("structure") if isinstance(root.get("structure"), dict) else {}
        mapping: dict[str, set[str]] = {}

        for row in cls.flatten_items(structure):
            if not row.code or not row.parent_code:
                continue

            mapping.setdefault(row.code, set()).add(row.parent_code)

        return mapping

    @classmethod
    def collect_catalog_alternate_map(cls, root: dict[str, Any]) -> dict[str, str]:
        """MP alternativo na descrição (ex.: «= 10400111») → código MP canônico."""
        structure = root.get("structure") if isinstance(root.get("structure"), dict) else {}
        mapping: dict[str, str] = {}
        pattern = ChatDrawingPatternsService.catalog_alternate_code()

        for row in cls.flatten_items(structure):
            if not row.code:
                continue

            match = pattern.search(str(row.description or ""))

            if not match:
                continue

            alternate = ChatProductQueryIntentService.normalize_product_code(
                str(match.group(1) or "")
            )
            primary = ChatProductQueryIntentService.normalize_product_code(row.code)

            if alternate and primary and alternate != primary:
                mapping[alternate] = primary

        return mapping

    @classmethod
    def expected_bom_level(cls, code: str, *, product_code: str, root: dict[str, Any]) -> int:
        normalized = ChatProductQueryIntentService.normalize_product_code(code)
        root_code = ChatProductQueryIntentService.normalize_product_code(product_code)

        if not normalized:
            return ChatDrawingPatternsService.default_bom_level_when_unknown()

        if normalized == root_code:
            return ChatDrawingPatternsService.root_product_bom_level()

        structure = root.get("structure") if isinstance(root.get("structure"), dict) else {}

        for row in cls.flatten_items(structure):
            if row.code == normalized:
                return row.depth

        return ChatDrawingPatternsService.default_bom_level_when_unknown()

    @classmethod
    def collect_guide_expected_codes(cls, root: dict[str, Any], product_code: str) -> set[str]:
        root_code = ChatProductQueryIntentService.normalize_product_code(product_code)
        codes: set[str] = set()

        if root_code:
            codes.add(root_code)

        structure = root.get("structure") if isinstance(root.get("structure"), dict) else {}

        for row in cls.flatten_items(structure):
            if not row.code or row.code == root_code:
                continue

            if cls._item_requires_guide(row.code, item_type=row.type):
                codes.add(row.code)

        return codes

    @classmethod
    def flatten_component_rows(cls, structure: dict[str, Any] | None) -> list[dict[str, Any]]:
        """Formato legado para tabela de componentes do presenter."""
        if not isinstance(structure, dict):
            return []

        rows: list[dict[str, Any]] = []

        for item in structure.get("items") or []:
            if not isinstance(item, dict):
                continue

            parent_code = item.get("code")
            parent_description = item.get("description")
            components = item.get("components") or []

            if components:
                for component in components:
                    if not isinstance(component, dict):
                        continue

                    rows.append(
                        {
                            "parent_code": parent_code,
                            "parent_description": parent_description,
                            "component_code": component.get("code"),
                            "description": component.get("description"),
                            "type": component.get("type"),
                            "unit": component.get("unit"),
                            "quantity": component.get("quantity"),
                        }
                    )
            else:
                rows.append(
                    {
                        "parent_code": "",
                        "parent_description": "",
                        "component_code": item.get("code"),
                        "description": item.get("description"),
                        "type": item.get("type"),
                        "unit": item.get("unit"),
                        "quantity": item.get("quantity"),
                    }
                )

        return rows

    @classmethod
    def _item_requires_guide(cls, code: str, *, item_type: str) -> bool:
        if ChatDrawingPatternsService.is_intermediate_family(code):
            return True

        return str(item_type or "").strip().upper() in ChatDrawingPatternsService.guide_product_types()

    @classmethod
    def _walk_items(
        cls,
        items: list[Any],
        *,
        depth: int,
        parent_code: str | None,
        path: tuple[str, ...],
        rows: list[StructureIndexRow],
    ) -> None:
        for item in items:
            if not isinstance(item, dict):
                continue

            code = ChatProductQueryIntentService.normalize_product_code(
                str(item.get("code") or "")
            )

            if not code:
                continue

            current_path = (*path, code)
            rows.append(
                StructureIndexRow(
                    code=code,
                    description=str(item.get("description") or "").strip(),
                    type=str(item.get("type") or "").strip().upper(),
                    depth=depth,
                    parent_code=parent_code,
                    path=current_path,
                )
            )

            child_components = item.get("components")

            if isinstance(child_components, list) and child_components:
                cls._walk_items(
                    child_components,
                    depth=depth + 1,
                    parent_code=code,
                    path=current_path,
                    rows=rows,
                )
