# app/application/services/bom_tree_builder.py

from app.domain.entities.product.bom_node import BomNode


class BomTreeBuilder:

    @staticmethod
    def build(rows, root_code: str):

        items = {}

        for r in rows:

            conversion_factor = r.get("component_conversion_factor")

            try:
                parsed_conversion_factor = (
                    float(conversion_factor) if conversion_factor not in (None, "") else None
                )
            except (TypeError, ValueError):
                parsed_conversion_factor = None

            if parsed_conversion_factor is not None and parsed_conversion_factor <= 0:
                parsed_conversion_factor = None

            component = BomNode(
                code=r["component_code"],
                description=r["component_description"],
                type=r["component_type"],
                unit=r["component_unit"],
                quantity=float(r["quantity"]) if r["quantity"] else 0,
                secondary_unit=r.get("component_secondary_unit") or None,
                conversion_factor=parsed_conversion_factor,
                conversion_type=r.get("component_conversion_type") or None,
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