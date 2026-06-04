"""Cruza roteiro, inspeção e estrutura do analyser — pontos de atenção confiáveis."""

from __future__ import annotations

from typing import Any


class ChatProductAnalyserDivergenceService:
    @classmethod
    def build_attention_points(cls, root: dict | None, product: dict | None) -> list[str]:
        if not isinstance(root, dict):
            return []

        product = product if isinstance(product, dict) else {}
        points: list[str] = []

        guide_points = cls._guide_attention(root)
        inspection_points = cls._inspection_attention(root)
        cross_points = cls._cross_collection_attention(root)
        cadastral_points = cls._cadastral_attention(product)

        for block in (guide_points, inspection_points, cross_points, cadastral_points):
            for item in block:
                token = str(item or "").strip()

                if token and token not in points:
                    points.append(token)

        return points

    @classmethod
    def build_opening_narrative(cls, root: dict | None, product: dict | None) -> str | None:
        if not isinstance(root, dict) or not isinstance(product, dict):
            return None

        code = str(product.get("code") or "").strip()
        description = str(product.get("description") or "").strip()
        product_type = str(product.get("type") or "").strip()
        group_code = str(product.get("group_code") or "").strip()

        if not code:
            return None

        parts = [
            f"O produto **{code}**",
        ]

        if description:
            parts[0] += f" — {description}"

        meta_bits: list[str] = []

        if product_type:
            meta_bits.append(f"tipo **{product_type}**")

        if group_code:
            meta_bits.append(f"grupo **{group_code}**")

        if meta_bits:
            parts.append(f"({' , '.join(meta_bits)})")

        composition = cls._structure_component_labels(root)

        if composition:
            parts.append(
                "A estrutura de nível 1 inclui: "
                + ", ".join(composition[:8])
                + ("…" if len(composition) > 8 else "")
                + "."
            )

        guide_total = cls._collection_total(root.get("guide"))
        inspection_total = cls._collection_total(root.get("inspection"))
        structure_total = cls._collection_total(root.get("structure"))

        availability: list[str] = []

        if guide_total and int(guide_total) > 0:
            availability.append(f"roteiro ({guide_total} registro(s))")
        else:
            availability.append("roteiro sem operações retornadas")

        if inspection_total and int(inspection_total) > 0:
            availability.append(f"inspeção ({inspection_total} registro(s))")
        else:
            availability.append("inspeção não cadastrada")

        if structure_total and int(structure_total) > 0:
            availability.append(f"estrutura ({structure_total} item(ns) nível 1)")
        else:
            availability.append("estrutura vazia na API")

        parts.append(
            "Fontes cruzadas nesta consulta: " + "; ".join(availability) + "."
        )

        return " ".join(parts)

    @classmethod
    def _guide_attention(cls, root: dict) -> list[str]:
        guide = root.get("guide")

        if not isinstance(guide, dict):
            return []

        items = [item for item in (guide.get("items") or []) if isinstance(item, dict)]
        total = cls._collection_total(guide)

        if total == 0 or not items:
            return [
                "Roteiro não retornado: não há operações registradas na rota analisada."
            ]

        without_operations = [
            str(item.get("product_code") or item.get("product") or "?").strip()
            for item in items
            if not cls._guide_item_has_operations(item)
        ]

        if without_operations and len(without_operations) == len(items):
            return [
                "Roteiro retornou itens, mas nenhum traz operações preenchidas — "
                "confirme no ERP se o roteiro está incompleto ou se a API filtrou o detalhe."
            ]

        return []

    @classmethod
    def _inspection_attention(cls, root: dict) -> list[str]:
        inspection = root.get("inspection")

        if not isinstance(inspection, dict):
            return []

        items = [item for item in (inspection.get("items") or []) if isinstance(item, dict)]
        total = cls._collection_total(inspection)

        if total == 0 or not items:
            return []

        empty_qp: list[str] = []
        missing_blocks: list[str] = []

        for item in items:
            code = str(
                item.get("product")
                or item.get("product_code")
                or "?"
            ).strip()

            if not cls._has_qp_blocks(item):
                missing_blocks.append(code)
                continue

            if cls._qp_blocks_empty(item):
                empty_qp.append(code)

        points: list[str] = []

        if empty_qp:
            sample = ", ".join(empty_qp[:5])
            suffix = f" e mais {len(empty_qp) - 5}" if len(empty_qp) > 5 else ""
            points.append(
                "Inspeções com blocos QP6/QP7/QP8 vazios nos itens: "
                f"{sample}{suffix}."
            )

        if missing_blocks:
            sample = ", ".join(missing_blocks[:5])
            points.append(
                "Registros de inspeção sem blocos QP6/QP7/QP8 estruturados: "
                f"{sample}."
            )

        return points

    @classmethod
    def _cross_collection_attention(cls, root: dict) -> list[str]:
        structure_codes = cls._structure_component_codes(root)
        inspection_codes = cls._inspection_product_codes(root)
        points: list[str] = []

        only_inspection = sorted(inspection_codes - structure_codes)
        only_structure = sorted(structure_codes - inspection_codes)

        for code in only_inspection[:6]:
            points.append(
                f"Componente **{code}** aparece na inspeção, mas não consta na estrutura "
                "retornada — vale conferir desenho, cadastro técnico ou divergência entre bases."
            )

        if len(only_inspection) > 6:
            points.append(
                f"Há mais {len(only_inspection) - 6} código(s) só na inspeção "
                "(não listados acima)."
            )

        if only_structure and inspection_codes:
            sample = ", ".join(only_structure[:4])
            points.append(
                "Na estrutura há componente(s) sem espelho explícito na inspeção retornada: "
                f"{sample}."
            )

        return points

    @classmethod
    def _cadastral_attention(cls, product: dict) -> list[str]:
        points: list[str] = []
        blocked = str(product.get("blocked") or "").strip()

        if blocked and blocked not in {"N", "0", ""}:
            points.append(
                f"Cadastro com indicador de bloqueio «{blocked}» — valide liberacão comercial/produção."
            )

        if product.get("last_purchase_price") in (0, 0.0, None) and not str(
            product.get("last_purchase_date") or ""
        ).strip():
            points.append(
                "Sem histórico recente de compra no cadastro — pode ser item fabricado ou sem movimentação."
            )

        drawing = str(product.get("drawing_code") or "").strip()
        customer_ref = str(product.get("customer_reference") or "").strip()

        if drawing and customer_ref and drawing != customer_ref:
            points.append(
                f"Referências distintas no cadastro: desenho **{drawing}** "
                f"× ref. cliente **{customer_ref}**."
            )

        return points

    @classmethod
    def _structure_component_codes(cls, root: dict) -> set[str]:
        structure = root.get("structure")

        if not isinstance(structure, dict):
            return set()

        codes: set[str] = set()

        for item in structure.get("items") or []:
            if not isinstance(item, dict):
                continue

            for component in item.get("components") or []:
                if not isinstance(component, dict):
                    continue

                code = str(component.get("code") or "").strip()

                if code:
                    codes.add(code)

            code = str(item.get("code") or "").strip()

            if code and not item.get("components"):
                codes.add(code)

        return codes

    @classmethod
    def _inspection_product_codes(cls, root: dict) -> set[str]:
        inspection = root.get("inspection")

        if not isinstance(inspection, dict):
            return set()

        codes: set[str] = set()

        for item in inspection.get("items") or []:
            if not isinstance(item, dict):
                continue

            code = str(
                item.get("product")
                or item.get("product_code")
                or ""
            ).strip()

            if code:
                codes.add(code)

        return codes

    @classmethod
    def _structure_component_labels(cls, root: dict) -> list[str]:
        structure = root.get("structure")

        if not isinstance(structure, dict):
            return []

        labels: list[str] = []

        for item in structure.get("items") or []:
            if not isinstance(item, dict):
                continue

            for component in item.get("components") or []:
                if not isinstance(component, dict):
                    continue

                desc = str(component.get("description") or "").strip()
                code = str(component.get("code") or "").strip()
                comp_type = str(component.get("type") or "").strip()

                if desc:
                    label = desc

                    if code:
                        label = f"{desc} ({code})"

                    if comp_type:
                        label = f"{label} [{comp_type}]"

                    labels.append(label)

        return labels

    @classmethod
    def _collection_total(cls, value: Any) -> int | None:
        if isinstance(value, dict):
            total = value.get("total")

            if total is not None:
                try:
                    return int(total)
                except (TypeError, ValueError):
                    return None

        return None

    @classmethod
    def _guide_item_has_operations(cls, item: dict) -> bool:
        operations = item.get("operations")

        if isinstance(operations, list) and operations:
            return True

        return bool(str(item.get("operation_description") or "").strip())

    @classmethod
    def _has_qp_blocks(cls, item: dict) -> bool:
        return any(key in item for key in ("QP6", "QP7", "QP8", "qp6", "qp7", "qp8"))

    @classmethod
    def _qp_blocks_empty(cls, item: dict) -> bool:
        if not cls._has_qp_blocks(item):
            return True

        for key in ("QP6", "QP7", "QP8", "qp6", "qp7", "qp8"):
            value = item.get(key)

            if isinstance(value, list) and value:
                return False

        return True
