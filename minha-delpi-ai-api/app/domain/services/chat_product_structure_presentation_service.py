from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class StructureNode:
    code: str
    description: str
    item_type: str
    unit: str
    quantity: float | None
    components: list[StructureNode] = field(default_factory=list)


@dataclass(frozen=True)
class ProductStructureModel:
    product_code: str
    root: StructureNode
    level1: list[StructureNode]

    def all_mp_nodes(self) -> list[tuple[str | None, StructureNode]]:
        """Retorna (pai_intermediário, nó MP) para MPs folha."""

        rows: list[tuple[str | None, StructureNode]] = []

        for intermediate in self.level1:
            children = intermediate.components or []

            if not children:
                continue

            if all(self._is_mp(child) for child in children):
                for child in children:
                    rows.append((intermediate.code, child))
            else:
                for child in children:
                    if self._is_mp(child):
                        rows.append((intermediate.code, child))

        return rows

    def unique_mp_codes(self) -> set[str]:
        return {node.code for _, node in self.all_mp_nodes()}

    @staticmethod
    def _is_mp(node: StructureNode) -> bool:
        return str(node.item_type or "").upper() == "MP"


class ChatProductStructurePresentationService:
    """Formata resposta de GET /products/{code}/structure em markdown hierárquico."""

    _LENGTH_IN_CODE_RE = re.compile(r"-(\d{3,5})/")

    @classmethod
    def parse_payload(cls, data) -> ProductStructureModel | None:
        root_dict = cls._unwrap(data)

        if not isinstance(root_dict, dict):
            return None

        root_node = root_dict.get("root")
        items = root_dict.get("items")

        if not isinstance(root_node, dict) or not isinstance(items, list):
            return None

        product_code = str(root_node.get("code") or "").strip()

        if not product_code:
            return None

        return ProductStructureModel(
            product_code=product_code,
            root=cls._node_from_dict(root_node),
            level1=[cls._node_from_dict(item) for item in items if isinstance(item, dict)],
        )

    @classmethod
    def format_markdown(cls, data, *, source_path: str | None = None) -> str | None:
        model = cls.parse_payload(data)

        if not model:
            return None

        parts = [
            f"**Estrutura do produto {model.product_code}**",
            "",
            "**Produto pai**",
            cls._table(
                ["Código", "Descrição", "Tipo", "Unid.", "Qtde"],
                [
                    [
                        model.root.code,
                        model.root.description,
                        model.root.item_type,
                        model.root.unit,
                        cls._qty(model.root.quantity),
                    ]
                ],
            ),
            "",
            "**Componentes nível 1**",
            cls._table(
                ["Código", "Descrição", "Tipo", "Unid.", "Qtde"],
                [
                    [
                        node.code,
                        node.description,
                        node.item_type,
                        node.unit,
                        cls._qty(node.quantity),
                    ]
                    for node in model.level1
                ],
            ),
            "",
            "**Estrutura detalhada**",
        ]

        parts.append(cls._format_detailed(model))
        parts.extend(cls._footer(source_path, model.product_code))

        return "\n".join(parts).strip()

    @classmethod
    def _format_detailed(cls, model: ProductStructureModel) -> str:
        if cls._prefer_flat_detailed(model):
            rows = [
                [
                    parent or "",
                    node.code,
                    node.description,
                    node.item_type,
                    node.unit,
                    cls._qty(node.quantity),
                ]
                for parent, node in model.all_mp_nodes()
            ]

            return cls._table(
                ["Pai", "Componente", "Descrição", "Tipo", "Unid.", "Qtde"],
                rows,
            )

        blocks: list[str] = []

        for intermediate in model.level1:
            children = intermediate.components or []

            if not children:
                continue

            header = f"{intermediate.code} — {intermediate.description}".strip(" —")
            blocks.append(header)
            blocks.append(
                cls._table(
                    ["Código", "Descrição", "Tipo", "Unid.", "Qtde"],
                    [
                        [
                            child.code,
                            child.description,
                            child.item_type,
                            child.unit,
                            cls._qty(child.quantity),
                        ]
                        for child in children
                    ],
                )
            )
            blocks.append("")

        return "\n".join(blocks).strip()

    @classmethod
    def _prefer_flat_detailed(cls, model: ProductStructureModel) -> bool:
        if not model.level1:
            return True

        for intermediate in model.level1:
            children = intermediate.components or []

            if len(children) != 1:
                return False

            if not cls._is_mp(children[0]):
                return False

        return True

    @classmethod
    def _is_mp(cls, node: StructureNode) -> bool:
        return ProductStructureModel._is_mp(node)

    @classmethod
    def extract_length_from_intermediate(cls, description: str) -> int | None:
        match = cls._LENGTH_IN_CODE_RE.search(str(description or ""))

        if not match:
            return None

        try:
            return int(match.group(1))
        except ValueError:
            return None

    @classmethod
    def _node_from_dict(cls, raw: dict) -> StructureNode:
        components_raw = raw.get("components") or []
        components = [
            cls._node_from_dict(item)
            for item in components_raw
            if isinstance(item, dict)
        ]

        return StructureNode(
            code=str(raw.get("code") or "").strip(),
            description=str(raw.get("description") or "").strip(),
            item_type=str(raw.get("type") or "").strip(),
            unit=str(raw.get("unit") or "").strip(),
            quantity=cls._parse_qty(raw.get("quantity")),
            components=components,
        )

    @classmethod
    def _unwrap(cls, data):
        root = data

        if isinstance(root, dict) and "data" in root:
            root = root["data"]

        if isinstance(root, dict) and "data" in root:
            root = root["data"]

        return root

    @classmethod
    def _table(cls, headers: list[str], rows: list[list]) -> str:
        if not rows:
            return "_Sem registros._"

        lines = [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join("---" for _ in headers) + " |",
        ]

        for row in rows:
            cells = [cls._cell(value) for value in row]
            lines.append("| " + " | ".join(cells) + " |")

        return "\n".join(lines)

    @classmethod
    def _cell(cls, value) -> str:
        text = str(value if value is not None else "").strip()
        return text.replace("|", "\\|")

    @classmethod
    def _qty(cls, value: float | None) -> str:
        if value is None:
            return ""

        if float(value).is_integer():
            return str(int(value))

        return str(value)

    @classmethod
    def _parse_qty(cls, value) -> float | None:
        if value is None or value == "":
            return None

        try:
            return float(str(value).replace(",", "."))
        except (TypeError, ValueError):
            return None

    @classmethod
    def _footer(cls, source_path: str | None, product_code: str) -> list[str]:
        path = source_path or f"/products/{product_code}/structure"

        return [
            "",
            f"_Fonte: API DELPI — {path}_",
            "_Status: sucesso._",
        ]

    @classmethod
    def build_tree_presentation(
        cls,
        data,
        *,
        source_path: str | None = None,
        path: str = "",
    ) -> dict | None:
        """Monta apresentação em árvore para BOM, parents ou analyser."""
        from app.domain.services.chat_presentation_profile_service import (
            ChatPresentationProfileService,
        )

        effective_path = str(path or source_path or "")
        entity = ChatPresentationProfileService.resolve_entity_from_path(effective_path)
        root_dict = cls._unwrap(data)

        if entity == "product_analyser" and isinstance(root_dict, dict):
            structure = root_dict.get("structure")

            if isinstance(structure, dict):
                root_dict = structure

        if entity == "product_parents" and isinstance(root_dict, dict):
            normalized = cls._normalize_parents_payload(root_dict)

            if normalized is not None:
                root_dict = normalized

        if entity == "product_structure_exclusivity" and isinstance(root_dict, dict):
            exclusivity_tree = cls._build_structure_exclusivity_tree(
                root_dict,
                source_path=effective_path,
            )

            if isinstance(exclusivity_tree, dict) and exclusivity_tree.get("type") == "tree":
                return exclusivity_tree

        if not isinstance(root_dict, dict) or not isinstance(root_dict.get("root"), dict):
            return None

        if entity == "product_parents":
            return cls._build_parents_tree(root_dict, source_path=effective_path)

        model = cls.parse_payload(root_dict)

        if not model:
            return None

        children = [cls._structure_node_to_tree(item) for item in model.level1]

        return {
            "type": "tree",
            "title": f"Estrutura do produto {model.product_code}",
            "root": cls._serialize_tree_node(
                model.root.code,
                model.root.description,
                model.root.item_type,
                model.root.unit,
                model.root.quantity,
                children=children or None,
            ),
        }

    @classmethod
    def _build_structure_exclusivity_tree(
        cls,
        root_dict: dict,
        *,
        source_path: str | None,
    ) -> dict | None:
        """Monta árvore BOM a partir de items planos (path/parent_code) da rota exclusivity."""
        product = root_dict.get("product")
        items_raw = root_dict.get("items")

        if not isinstance(product, dict) or not isinstance(items_raw, list) or not items_raw:
            return None

        product_code = str(product.get("product_code") or product.get("code") or "").strip()

        if not product_code:
            return None

        normalized: list[dict] = []

        for raw in items_raw:
            if not isinstance(raw, dict):
                continue

            item = cls._normalize_exclusivity_item(raw)

            if item:
                normalized.append(item)

        if not normalized:
            return None

        items_by_level: dict[int, list[dict]] = {}

        for item in normalized:
            level = item.get("level")

            if isinstance(level, int):
                items_by_level.setdefault(level, []).append(item)

        for item in normalized:
            item["parent"] = cls._resolve_exclusivity_parent(
                item,
                product_code=product_code,
                items_by_level=items_by_level,
            )

        children_by_parent: dict[str, list[dict]] = {}

        for item in normalized:
            parent = str(item.get("parent") or product_code).strip() or product_code
            children_by_parent.setdefault(parent, []).append(item)

        for children in children_by_parent.values():
            children.sort(key=lambda row: (row.get("level") or 0, row.get("code") or ""))

        from app.domain.services.chat_presentation_vocabulary_service import (
            ChatPresentationVocabularyService,
        )
        from app.domain.services.external_actions.presenters.product_operational_table_row_enrichment import (
            ROW_EMPHASIS_EXCLUSIVE_MP,
        )

        exclusive_badge_label = ChatPresentationVocabularyService.hierarchy_tree_text(
            "exclusiveMpBadgeLabel",
            default="Exclusiva",
        )

        def item_to_tree_node(item: dict) -> dict:
            child_nodes = [
                item_to_tree_node(child)
                for child in children_by_parent.get(item["code"], [])
            ]
            node = cls._serialize_tree_node(
                item["code"],
                item["description"],
                item["item_type"],
                item["unit"],
                item["quantity"],
                children=child_nodes or None,
            )

            if item.get("is_exclusive"):
                node["emphasis"] = ROW_EMPHASIS_EXCLUSIVE_MP
                node["emphasisLabel"] = exclusive_badge_label

            return node

        root_children = [
            item_to_tree_node(item)
            for item in children_by_parent.get(product_code, [])
        ]

        del source_path  # título alinhado à rota /structure

        return {
            "type": "tree",
            "title": f"Estrutura do produto {product_code}",
            "root": cls._serialize_tree_node(
                product_code,
                str(product.get("description") or "").strip(),
                str(product.get("product_type") or product.get("type") or "PA").strip(),
                str(product.get("unit") or "").strip(),
                None,
                children=root_children or None,
            ),
        }

    @classmethod
    def _normalize_exclusivity_item(cls, raw: dict) -> dict | None:
        from app.domain.services.chat_presentation_vocabulary_service import (
            ChatPresentationVocabularyService,
        )
        from app.domain.services.external_actions.presenters.product_operational_table_row_enrichment import (
            is_exclusive_raw_material_item,
        )

        code = str(raw.get("component_code") or raw.get("product_code") or "").strip()

        if not code:
            return None

        description = str(
            raw.get("component_description") or raw.get("description") or ""
        ).strip()
        item_type = str(raw.get("component_type") or raw.get("type") or "").strip()
        unit = str(raw.get("component_unit") or raw.get("unit") or "").strip()
        quantity = cls._parse_qty(
            raw.get("accumulated_quantity")
            or raw.get("quantity_per")
            or raw.get("quantity")
        )
        exclusive = is_exclusive_raw_material_item(raw)
        exclusive_label = str(raw.get("exclusive_raw_material_label") or "").strip()

        if not exclusive_label and raw.get("exclusive_raw_material") not in (None, ""):
            raw_flag = raw.get("exclusive_raw_material")

            if isinstance(raw_flag, bool):
                exclusive_label = ChatPresentationVocabularyService.boolean_label(yes=raw_flag)
            else:
                exclusive_label = ChatPresentationVocabularyService.boolean_label(yes=exclusive)
        elif exclusive and not exclusive_label:
            exclusive_label = ChatPresentationVocabularyService.boolean_label(yes=True)

        parent = str(raw.get("parent_code") or "").strip()

        if not parent:
            parent = cls._parent_code_from_structure_path(raw.get("path"), code)

        level = raw.get("level")

        try:
            level_int = int(level) if level is not None and level != "" else None
        except (TypeError, ValueError):
            level_int = None

        return {
            "code": code,
            "description": description,
            "item_type": item_type,
            "unit": unit,
            "quantity": quantity,
            "exclusive_label": exclusive_label,
            "is_exclusive": exclusive,
            "parent": parent,
            "level": level_int,
            "path": str(raw.get("path") or "").strip(),
        }

    @classmethod
    def _parent_code_from_structure_path(cls, path, code: str) -> str:
        segments = [
            segment.strip()
            for segment in str(path or "").split(">")
            if str(segment).strip()
        ]

        if not segments:
            return ""

        normalized_code = str(code).strip()

        if segments[-1] != normalized_code:
            for index, segment in enumerate(segments):
                if segment == normalized_code and index > 0:
                    return segments[index - 1]

            return ""

        if len(segments) < 2:
            return ""

        return segments[-2]

    @classmethod
    def _resolve_exclusivity_parent(
        cls,
        item: dict,
        *,
        product_code: str,
        items_by_level: dict[int, list[dict]],
    ) -> str:
        parent = str(item.get("parent") or "").strip()

        if parent:
            return parent

        level = item.get("level")

        if level == 1:
            return product_code

        if isinstance(level, int) and level > 1:
            candidates = items_by_level.get(level - 1) or []

            if len(candidates) == 1:
                return str(candidates[0].get("code") or "").strip() or product_code

            path = str(item.get("path") or "").strip()

            for candidate in candidates:
                candidate_path = str(candidate.get("path") or "").strip()

                if path and candidate_path and path.startswith(candidate_path):
                    return str(candidate.get("code") or "").strip() or product_code

        return product_code

    @classmethod
    def _normalize_parents_payload(cls, root_dict: dict) -> dict | None:
        """Aceita respostas com `root`+`items` ou legado `product`+`parents`."""
        if not isinstance(root_dict, dict):
            return None

        if isinstance(root_dict.get("root"), dict) and isinstance(root_dict.get("items"), list):
            return root_dict

        product = root_dict.get("product")
        parents = root_dict.get("parents")

        if not isinstance(product, dict) or not isinstance(parents, list) or not parents:
            return None

        code = str(product.get("code") or "").strip()

        if not code:
            return None

        return {
            "root": {
                "code": code,
                "description": product.get("description"),
                "type": product.get("type") or product.get("item_type"),
                "unit": product.get("unit"),
                "quantity": product.get("quantity", 1),
            },
            "items": [
                {
                    "code": parent.get("code"),
                    "description": parent.get("description"),
                    "type": parent.get("type"),
                    "unit": parent.get("unit"),
                    "quantity": parent.get("quantity", 1),
                    "parents": parent.get("parents") or [],
                }
                for parent in parents
                if isinstance(parent, dict)
            ],
            "total": root_dict.get("total") if root_dict.get("total") is not None else len(parents),
        }

    @classmethod
    def _build_parents_tree(cls, root_dict: dict, *, source_path: str | None) -> dict | None:
        root_node = root_dict.get("root")
        items = root_dict.get("items")

        if not isinstance(root_node, dict) or not isinstance(items, list):
            return None

        code = str(root_node.get("code") or "").strip()

        if not code:
            return None

        children = [
            cls._parents_node_to_tree(item)
            for item in items
            if isinstance(item, dict)
        ]

        return {
            "type": "tree",
            "title": f"Onde é usado o produto {code}",
            "root": cls._serialize_tree_node(
                code,
                str(root_node.get("description") or "").strip(),
                str(root_node.get("type") or "").strip(),
                str(root_node.get("unit") or "").strip(),
                cls._parse_qty(root_node.get("quantity")),
                children=children or None,
            ),
        }

    @classmethod
    def _structure_node_to_tree(cls, node: StructureNode) -> dict:
        children = [cls._structure_node_to_tree(child) for child in node.components]

        return cls._serialize_tree_node(
            node.code,
            node.description,
            node.item_type,
            node.unit,
            node.quantity,
            children=children or None,
        )

    @classmethod
    def _parents_node_to_tree(cls, raw: dict) -> dict:
        parents_raw = raw.get("parents") or []
        children = [
            cls._parents_node_to_tree(parent)
            for parent in parents_raw
            if isinstance(parent, dict)
        ]

        return cls._serialize_tree_node(
            str(raw.get("code") or "").strip(),
            str(raw.get("description") or "").strip(),
            str(raw.get("type") or "").strip(),
            str(raw.get("unit") or "").strip(),
            cls._parse_qty(raw.get("quantity")),
            children=children or None,
        )

    @classmethod
    def _serialize_tree_node(
        cls,
        code: str,
        description: str,
        item_type: str,
        unit: str,
        quantity: float | None,
        *,
        children: list[dict] | None = None,
    ) -> dict:
        node: dict = {
            "id": code or "unknown",
            "label": code or "—",
        }

        subtitle = str(description or "").strip()

        if subtitle:
            node["subtitle"] = subtitle

        badge = str(item_type or "").strip()

        if badge:
            node["badge"] = badge

        meta: dict[str, str | float | int] = {}

        if unit:
            meta["unit"] = unit

        if quantity is not None:
            meta["quantity"] = quantity

        if meta:
            node["meta"] = meta

        if children:
            node["children"] = children

        return node
