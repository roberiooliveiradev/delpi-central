"""Apresentação humanizada — GET /products/directives/{identifier}."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.domain.services.chat_presentation_operational_table_service import (
    ChatPresentationOperationalTableService as _OpsTable,
)

if TYPE_CHECKING:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )


class ExternalActionProductDirectivesPresenter:
    def __init__(self, host: ExternalActionResultPresenter) -> None:
        self._host = host

    def _route(self, route: str, key: str, **values: str) -> str:
        return self._host._route_presentation(route, key, **values)

    def _product_code(self, root: dict, path: str) -> str:
        resolution = root.get("resolution") if isinstance(root.get("resolution"), dict) else {}
        product = root.get("product") if isinstance(root.get("product"), dict) else {}

        return str(
            resolution.get("delpi_code")
            or product.get("product_code")
            or product.get("code")
            or self._host._extract_product_code_from_path(path)
            or ""
        ).strip()

    def present(self, root: dict, path: str) -> dict:
        resolution = root.get("resolution") if isinstance(root.get("resolution"), dict) else {}
        product = root.get("product") if isinstance(root.get("product"), dict) else {}
        summary = root.get("summary") if isinstance(root.get("summary"), dict) else {}
        code = self._product_code(root, path)
        description = str(product.get("description") or "").strip()
        customer_reference = str(
            resolution.get("customer_reference") or product.get("customer_reference") or ""
        ).strip()
        identifier = str(resolution.get("identifier") or "").strip()

        linhas: list[str] = []

        if identifier and identifier != code:
            linhas.append(
                self._route(
                    "directives",
                    "resolutionLine",
                    identifier=identifier,
                    code=code or "—",
                    customer_reference=customer_reference or "—",
                )
            )
        elif description:
            linhas.append(
                self._route(
                    "directives",
                    "introWithDescription",
                    code=code,
                    description=description,
                )
            )
        elif code:
            linhas.append(self._route("directives", "introCodeOnly", code=code))

        if summary:
            linhas.append(
                self._route(
                    "directives",
                    "summaryLine",
                    raw_materials=str(summary.get("total_raw_material_entries") or 0),
                    suppliers=str(summary.get("total_supplier_links") or 0),
                    with_purchase=str(summary.get("raw_materials_with_last_purchase") or 0),
                    without_purchase=str(summary.get("raw_materials_without_last_purchase") or 0),
                )
            )

        tables = self.build_all_table_presentations(root, path=path)

        return {
            "titulo": (
                self._route("directives", "titleWithCode", code=code)
                if code
                else self._route("directives", "titleGeneric")
            ),
            "linhas": [line for line in linhas if line],
            "dados": root,
            "sourcePath": path,
            "tables": tables,
        }

    def build_all_table_presentations(self, root: dict, *, path: str = "") -> list[dict]:
        tables: list[dict] = []

        for builder in (
            self.build_structure_table,
            self.build_suppliers_table,
            self.build_last_purchase_table,
        ):
            table = builder(root, path=path)

            if isinstance(table, dict):
                tables.append(table)

        return tables

    def build_structure_table(self, root: dict, *, path: str = "") -> dict | None:
        raw_materials = root.get("raw_materials")

        if not isinstance(raw_materials, list) or not raw_materials:
            return None

        rows: list[dict[str, Any]] = []

        for item in raw_materials:
            if not isinstance(item, dict):
                continue

            rows.append(
                {
                    "raw_material_code": str(
                        item.get("raw_material_code") or item.get("component_code") or ""
                    ).strip(),
                    "description": str(
                        item.get("description") or item.get("component_description") or ""
                    ).strip(),
                    "unit": str(item.get("unit") or item.get("component_unit") or "").strip(),
                    "level": item.get("level"),
                    "quantity_per": item.get("quantity_per"),
                    "accumulated_quantity": item.get("accumulated_quantity"),
                }
            )

        if not rows:
            return None

        return _OpsTable.build_items_table(
            self._host.column_label_context,
            rows,
            title=self._route("directives", "structureTableTitle"),
            role="structure",
            path=path,
            profile_name="directivesRawMaterials",
        )

    def build_suppliers_table(self, root: dict, *, path: str = "") -> dict | None:
        raw_materials = root.get("raw_materials")

        if not isinstance(raw_materials, list) or not raw_materials:
            return None

        rows: list[dict[str, Any]] = []

        for item in raw_materials:
            if not isinstance(item, dict):
                continue

            mp_code = str(item.get("raw_material_code") or item.get("component_code") or "").strip()
            mp_description = str(
                item.get("description") or item.get("component_description") or ""
            ).strip()
            suppliers = item.get("suppliers") if isinstance(item.get("suppliers"), list) else []

            for supplier in suppliers:
                if not isinstance(supplier, dict):
                    continue

                rows.append(
                    {
                        "raw_material_code": mp_code,
                        "raw_material_description": mp_description,
                        "supplier_code": str(supplier.get("supplier_code") or "").strip(),
                        "supplier_store": str(supplier.get("supplier_store") or "").strip(),
                        "supplier_name": str(supplier.get("supplier_name") or "").strip(),
                        "supplier_part_number": str(
                            supplier.get("supplier_part_number") or ""
                        ).strip(),
                        "last_price": supplier.get("last_price"),
                        "last_price_date": str(supplier.get("last_price_date") or "").strip(),
                        "registered_lead_time_days": supplier.get("registered_lead_time_days"),
                    }
                )

        if not rows:
            return None

        return _OpsTable.build_items_table(
            self._host.column_label_context,
            rows,
            title=self._route("directives", "suppliersTableTitle"),
            role="list",
            path=path,
            profile_name="directivesSuppliers",
        )

    def build_last_purchase_table(self, root: dict, *, path: str = "") -> dict | None:
        raw_materials = root.get("raw_materials")

        if not isinstance(raw_materials, list) or not raw_materials:
            return None

        rows: list[dict[str, Any]] = []

        for item in raw_materials:
            if not isinstance(item, dict):
                continue

            last_purchase = (
                item.get("last_purchase") if isinstance(item.get("last_purchase"), dict) else {}
            )

            if not last_purchase:
                continue

            rows.append(
                {
                    "raw_material_code": str(
                        item.get("raw_material_code") or item.get("component_code") or ""
                    ).strip(),
                    "description": str(
                        item.get("description") or item.get("component_description") or ""
                    ).strip(),
                    "branch": str(last_purchase.get("branch") or "").strip(),
                    "invoice_number": str(last_purchase.get("invoice_number") or "").strip(),
                    "invoice_series": str(last_purchase.get("invoice_series") or "").strip(),
                    "issue_date": str(last_purchase.get("issue_date") or "").strip(),
                    "entry_date": str(last_purchase.get("entry_date") or "").strip(),
                    "supplier_code": str(last_purchase.get("supplier_code") or "").strip(),
                    "supplier_name": str(last_purchase.get("supplier_name") or "").strip(),
                    "supplier_part_number": str(
                        last_purchase.get("supplier_part_number") or ""
                    ).strip(),
                    "quantity": last_purchase.get("quantity"),
                    "unit_price": last_purchase.get("unit_price"),
                    "total_value": last_purchase.get("total_value"),
                    "icms_rate": last_purchase.get("icms_rate"),
                    "purchase_order": str(last_purchase.get("purchase_order") or "").strip(),
                }
            )

        if not rows:
            return None

        return _OpsTable.build_items_table(
            self._host.column_label_context,
            rows,
            title=self._route("directives", "lastPurchaseTableTitle"),
            role="list",
            path=path,
            profile_name="directivesLastPurchase",
        )

    def build_raw_materials_table(self, root: dict, *, path: str = "") -> dict | None:
        """Compatibilidade — retorna a primeira tabela disponível."""
        tables = self.build_all_table_presentations(root, path=path)

        return tables[0] if tables else None
