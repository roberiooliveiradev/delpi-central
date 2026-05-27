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
