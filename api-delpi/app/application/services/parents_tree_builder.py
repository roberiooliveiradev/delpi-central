# app/application/services/parents_tree_builder.py
from app.domain.entities.product.parent_node import ParentNode


class ParentsTreeBuilder:

    @staticmethod
    def build(rows: list[dict], root_code: str):

        items: dict[str, ParentNode] = {}

        for r in rows:

            parent = ParentNode(
                code=r["parent_code"],
                description=r["parent_description"],
                type=r["parent_type"],
                unit=r["parent_unit"],
                quantity=float(r["quantity"] or 0),
                parents=[]
            )

            child_code = r["child_code"]

            if child_code not in items:

                items[child_code] = ParentNode(
                    code=child_code,
                    description=r["child_description"],
                    type=r["child_type"],
                    unit=r["child_unit"],
                    quantity=1,
                    parents=[]
                )

            items[child_code].parents.append(parent)

            items[parent.code] = parent

        return items.get(root_code)