# app/application/services/bom_tree_builder.py

from app.domain.entities.product.bom_node import BomNode


class BomTreeBuilder:

    @staticmethod
    def _parse_positive_float(raw) -> float | None:
        try:
            value = float(raw) if raw not in (None, "") else None
        except (TypeError, ValueError):
            return None

        if value is None or value <= 0:
            return None

        return value

    @staticmethod
    def build(rows, root_code: str):

        items = {}

        for r in rows:

            parsed_conversion_factor = BomTreeBuilder._parse_positive_float(
                r.get("component_conversion_factor")
            )
            parsed_third_conversion_factor = BomTreeBuilder._parse_positive_float(
                r.get("component_third_conversion_factor")
            )

            component = BomNode(
                code=r["component_code"],
                description=r["component_description"],
                type=r["component_type"],
                unit=r["component_unit"],
                quantity=float(r["quantity"]) if r["quantity"] else 0,
                secondary_unit=r.get("component_secondary_unit") or None,
                conversion_factor=parsed_conversion_factor,
                conversion_type=r.get("component_conversion_type") or None,
                third_unit=r.get("component_third_unit") or None,
                third_conversion_factor=parsed_third_conversion_factor,
            )

            parent_code = r["parent_code"]

            if parent_code not in items:
                items[parent_code] = BomNode(
                    code=parent_code,
                    description=r["parent_description"],
                    type=r["parent_type"],
                    unit=r["parent_unit"],
                    quantity=1
                )

            items[parent_code].components.append(component)
            items[component.code] = component

        return items.get(root_code)