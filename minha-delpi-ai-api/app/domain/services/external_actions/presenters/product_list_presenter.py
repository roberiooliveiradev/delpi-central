"""Listas e tabelas de produto do ExternalActionResultPresenter — Fase 3A lote 3."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )


class ExternalActionProductListPresenter:
    def __init__(self, host: ExternalActionResultPresenter) -> None:
        self._host = host

    def _infer_items_title(self, items: list, path: str) -> str | None:
        from app.domain.services.chat_assistant_content_service import (
            ChatAssistantContentService,
        )

        bundle = "presenter_content"
        title = ChatAssistantContentService.title_for_path(
            bundle,
            path,
            path_key="titlesByPathFragment",
        )

        if title:
            return title

        if items and isinstance(items[0], dict):
            first = items[0]

            if ("level" in first or "quantity" in first) and "code" in first:
                return ChatAssistantContentService.get(
                    bundle,
                    "titlesByItemShape",
                    "structure",
                )

            if "branch" in first or "warehouse" in first:
                return ChatAssistantContentService.get(
                    bundle,
                    "titlesByItemShape",
                    "stock",
                )

            if "eficiencia_percentual" in first and (
                "tempo_real_horas" in first or "centro_trabalho" in first
            ):
                return ChatAssistantContentService.get(
                    bundle,
                    "titlesByItemShape",
                    "efficiency",
                )

        return None

    def _present_path_routed_items(self, root: dict, path: str) -> dict | None:
        items = root.get("items") if isinstance(root, dict) else None

        if not isinstance(items, list) or not items:
            return None

        lowered_path = str(path or "").lower()
        title = self._infer_items_title(items, path)
        first_item = items[0] if isinstance(items[0], dict) else {}

        if "/guide" in lowered_path:
            return self._present_product_guide(items, path=path, title=title)

        if "/inspection" in lowered_path or self._host._looks_like_inspection_item(first_item):
            return self._present_product_inspection(items, path=path, title=title)

        if "/stock" in lowered_path or self._host._is_stock_data(first_item):
            return self._present_product_stock(items, path=path, title=title, root=root)

        return None

    def _present_lmp_page(self, root: dict) -> dict | None:
        items = root.get("items")

        if not isinstance(items, list):
            return None

        if items and isinstance(items[0], dict) and "sale_number" not in items[0] and "saleNumber" not in items[0]:
            return None

        if not items:
            return None

        total = root.get("total")
        linhas = []

        for item in items[:12]:
            if not isinstance(item, dict):
                continue

            ov = item.get("sale_number") or item.get("saleNumber")
            desc = item.get("sale_description") or item.get("saleDescription") or ""
            status = item.get("status") or item.get("engineering_status") or ""
            kind = item.get("listing_kind") or item.get("listingKind") or ""
            branch = item.get("branch") or ""

            parts = [str(part) for part in [ov, kind, status, branch] if part]
            separator = self._host._route_presentation("lmp", "headerSeparator")
            header = (
                separator.join(parts)
                if parts
                else self._host._route_presentation("lmp", "pageHeaderFallback")
            )
            line = self._host._route_presentation(
                "lmp",
                "pageLine",
                header=header,
                description=str(desc).strip(),
            ).strip(": ")

            if line:
                linhas.append(line.rstrip(": "))

        if total is not None:
            linhas.append(
                self._host._presenter_text(
                    "pagination",
                    "lmpPageTotal",
                    total=str(total),
                    page=str(root.get("page", 1)),
                )
            )

        return {
            "titulo": self._host._presenter_text("pagination", "lmpTitle"),
            "linhas": linhas
            or [self._host._presenter_text("pagination", "lmpEmptyPage")],
            "dados": {"total": total, "items": items[:12]},
        }

    def _present_lmp_detail(self, root: dict) -> dict | None:
        sale_number = root.get("sale_number") or root.get("saleNumber")

        if not sale_number:
            return None

        desc = root.get("sale_description") or root.get("saleDescription") or ""
        status = root.get("engineering_status") or root.get("status") or ""
        kind = root.get("listing_kind") or root.get("listingKind") or ""
        branch = root.get("branch") or ""
        customer = root.get("costumer_name") or root.get("customer_name") or ""
        seller = root.get("seller_name") or ""
        qtd_pi = root.get("qtd_pi")

        linhas = [
            self._host._route_presentation(
                "lmp",
                "ovHeader",
                sale_number=str(sale_number),
                desc=str(desc).strip(": "),
            ).strip(": "),
        ]

        if kind:
            linhas.append(self._host._route_presentation("lmp", "kind", kind=str(kind)))

        if branch:
            linhas.append(self._host._route_presentation("lmp", "branch", branch=str(branch)))

        if status:
            linhas.append(self._host._route_presentation("lmp", "status", status=str(status)))

        if customer:
            linhas.append(
                self._host._route_presentation("lmp", "customer", customer=str(customer))
            )

        if seller:
            linhas.append(self._host._route_presentation("lmp", "seller", seller=str(seller)))

        if qtd_pi is not None:
            linhas.append(self._host._route_presentation("lmp", "piQuantity", qtd=str(qtd_pi)))

        products = root.get("list_products") or root.get("listProducts") or []

        if isinstance(products, list):
            linhas.append(
                self._host._route_presentation(
                    "lmp", "productsCount", count=str(len(products))
                )
            )

        return {
            "titulo": self._host._route_presentation(
                "lmp", "detailTitle", sale_number=str(sale_number)
            ),
            "linhas": [line for line in linhas if line],
            "dados": root,
        }

    def _present_product_search(self, root: dict, items: list, *, title: str | None = None) -> dict:
        titulo = title or self._host._route_presentation("productSearch", "defaultTitle")
        total = root.get("total")
        is_hierarchy = titulo and ("pai" in titulo.lower() or "estrutura" in titulo.lower())

        if not items:
            return {
                "titulo": titulo,
                "linhas": [self._host._route_presentation("productSearch", "emptySearch")],
                "dados": root,
            }

        linhas = []

        for item in items:
            if not isinstance(item, dict):
                continue

            code = item.get("code") or "?"
            desc = item.get("description") or ""
            tipo = item.get("type") or ""
            unit = item.get("unit") or ""
            qty = item.get("quantity")
            level = item.get("level")

            line = self._host._format_product_search_line(
                code=str(code),
                description=str(desc),
                item_type=str(tipo),
                unit=str(unit),
                quantity=qty,
                level=level,
                is_hierarchy=is_hierarchy,
            )

            if line:
                linhas.append(line)

        if total is not None and total > len(items):
            linhas.append(
                self._host._route_presentation(
                    "productSearch", "totalFound", total=str(total)
                )
            )

        return {
            "titulo": titulo,
            "linhas": linhas or [self._host._route_presentation("productSearch", "empty")],
            "dados": {"total": total, "items": [{"code": i.get("code"), "description": i.get("description"), "type": i.get("type"), "unit": i.get("unit")} for i in items]},
        }

    def _present_sale_orders(self, root: dict, items: list) -> dict:
        total = root.get("total")

        if not items:
            return {
                "titulo": self._host._route_presentation("saleOrders", "title"),
                "linhas": [self._host._route_presentation("saleOrders", "emptyPeriod")],
                "dados": root,
            }

        linhas = []

        for item in items[:12]:
            if not isinstance(item, dict):
                continue

            order = item.get("order_number") or "?"
            desc = item.get("description") or ""
            branch = item.get("branch") or ""
            date = item.get("date") or ""
            stage = item.get("stage") or ""

            parts = [
                self._host._route_presentation("saleOrders", "orderPart", order=str(order))
            ]

            if branch:
                parts.append(
                    self._host._route_presentation(
                        "saleOrders",
                        "branchPart",
                        branch=str(branch),
                    )
                )

            if date:
                parts.append(str(date))

            if stage:
                parts.append(str(stage))

            header = self._host._route_presentation("lmp", "headerSeparator").join(parts)
            line = (
                self._host._route_presentation(
                    "saleOrders",
                    "composedLine",
                    header=header,
                    description=str(desc).strip(),
                ).rstrip(": ")
                if desc
                else header
            )
            linhas.append(line)

        if total is not None:
            linhas.append(
                self._host._presenter_text(
                    "pagination",
                    "saleOrdersPageTotal",
                    total=str(total),
                    page=str(root.get("page", 1)),
                )
            )

        return {
            "titulo": self._host._route_presentation("saleOrders", "title"),
            "linhas": linhas or [self._host._route_presentation("saleOrders", "empty")],
            "dados": {"total": total, "items": items[:12]},
        }

    def _present_product_guide(
        self,
        items: list,
        *,
        path: str = "",
        title: str | None = None,
    ) -> dict:
        titulo = (
            title
            or self._infer_items_title(items, path)
            or self._host._route_presentation("guide", "defaultTitle")
        )
        product_code = self._host._extract_product_code_from_path(path)

        main_ops: list[tuple[str, str, str | None]] = []
        component_products: set[str] = set()

        for item in items:
            if not isinstance(item, dict):
                continue

            level = item.get("bom_level", 0)
            op_desc = str(item.get("operation_description") or "").strip()
            op_code = str(item.get("operation_code") or "").strip()
            prod = str(item.get("product_code") or "").strip()
            work_center = str(item.get("work_center") or "").strip() or None

            if not product_code and level == 0 and prod:
                product_code = prod

            if level == 0 and op_desc:
                main_ops.append((op_code, op_desc, work_center))
            elif level and prod:
                component_products.add(prod)

        linhas: list[str] = []

        if product_code and main_ops:
            ops_preview = ", ".join(
                self._host._route_presentation(
                    "guide",
                    "opsPreviewWithCode",
                    code=code,
                    description=desc,
                )
                if code
                else self._host._route_presentation(
                    "guide",
                    "opsPreviewDescriptionOnly",
                    description=desc,
                )
                for code, desc, _ in main_ops
            )
            linhas.append(
                self._host._route_presentation(
                    "guide",
                    "mainOps",
                    code=product_code,
                    count=str(len(main_ops)),
                    preview=ops_preview,
                )
            )
        elif product_code:
            linhas.append(
                self._host._route_presentation(
                    "guide",
                    "queryOnly",
                    code=product_code,
                    count=str(len(items)),
                )
            )

        if component_products:
            preview_codes = ", ".join(sorted(component_products)[:5])
            suffix = "…" if len(component_products) > 5 else ""
            linhas.append(
                self._host._route_presentation(
                    "guide",
                    "bomComponents",
                    count=str(len(component_products)),
                    preview=preview_codes,
                    suffix=suffix,
                )
            )

        for op_code, op_desc, work_center in main_ops:
            center_part = (
                self._host._route_presentation(
                    "guide", "workCenterSuffix", center=str(work_center)
                )
                if work_center
                else ""
            )
            label = (
                self._host._route_presentation("guide", "operationWithCode", code=op_code)
                if op_code
                else self._host._route_presentation("guide", "operationGeneric")
            )
            linhas.append(
                self._host._route_presentation(
                    "guide",
                    "operationLine",
                    label=label,
                    desc=op_desc,
                    center=center_part,
                )
            )

        if not linhas:
            linhas = [
                self._host._route_presentation(
                    "guide", "apiFallback", count=str(len(items))
                )
            ]

        return {
            "titulo": titulo,
            "linhas": linhas,
            "dados": {
                "items": items,
                "product_code": product_code,
                "total": len(items),
            },
        }

    def _present_product_inspection(
        self,
        items: list,
        *,
        path: str = "",
        title: str | None = None,
    ) -> dict:
        titulo = (
            title
            or self._infer_items_title(items, path)
            or self._host._route_presentation("inspection", "defaultTitle")
        )
        product_code = self._host._extract_product_code_from_path(path)
        linhas: list[str] = []

        if items and isinstance(items[0], dict) and "has_inspection" in items[0]:
            with_plan = [item for item in items if item.get("has_inspection")]
            without_plan = len(items) - len(with_plan)

            if product_code:
                linhas.append(
                    self._host._route_presentation(
                        "inspection",
                        "planWithProduct",
                        code=product_code,
                        count=str(len(items)),
                    )
                )
            else:
                linhas.append(
                    self._host._route_presentation(
                        "inspection",
                        "planGeneric",
                        count=str(len(items)),
                    )
                )

            linhas.append(
                self._host._route_presentation(
                    "inspection", "withPlanCount", count=str(len(with_plan))
                )
            )

            if without_plan:
                linhas.append(
                    self._host._route_presentation(
                        "inspection", "withoutPlanCount", count=str(without_plan)
                    )
                )

            for item in with_plan:
                if not isinstance(item, dict):
                    continue

                item_code = str(item.get("product_code") or "?").strip()
                header = item.get("header") if isinstance(item.get("header"), dict) else {}
                header_desc = str(header.get("description") or "").strip()
                measurable = item.get("measurable_tests") or []
                textual = item.get("textual_tests") or []
                measurable_count = len(measurable) if isinstance(measurable, list) else 0
                textual_count = len(textual) if isinstance(textual, list) else 0

                from app.domain.services.chat_product_operational_content_service import (
                    ChatProductOperationalContentService,
                )

                summary = header_desc or ChatProductOperationalContentService.get(
                    "presenter",
                    "inspection",
                    "summaryFallback",
                )
                linhas.append(
                    self._host._route_presentation(
                        "inspection",
                        "itemLine",
                        code=item_code,
                        summary=summary,
                        measurable=str(measurable_count),
                        textual=str(textual_count),
                    )
                )

                if isinstance(measurable, list):
                    for test in measurable[:3]:
                        if not isinstance(test, dict):
                            continue

                        specs = self._host._format_measurable_test_specs(test)

                        if specs:
                            label = (
                                test.get("test_code")
                                or test.get("sequence")
                                or self._host._route_presentation(
                                    "inspection",
                                    "testLabelFallback",
                                )
                            )
                            linhas.append(
                                self._host._route_presentation(
                                    "inspection",
                                    "testLimits",
                                    label=str(label),
                                    specs=specs,
                                )
                            )

            if len(with_plan) > 8:
                linhas.append(
                    self._host._presenter_text(
                        "pagination",
                        "moreInspectionItems",
                        count=str(len(with_plan) - 8),
                    )
                )

            return {
                "titulo": titulo,
                "linhas": linhas,
                "dados": {
                    "items": items,
                    "product_code": product_code,
                    "total": len(items),
                },
            }

        linhas.append(
            self._host._route_presentation(
                "inspection", "characteristicsPlan", count=str(len(items))
            )
        )

        for item in items[:10]:
            if not isinstance(item, dict):
                continue

            line = self._host._format_inspection_characteristic_line(item)

            if line:
                linhas.append(line)

        if len(items) > 10:
            linhas.append(
                self._host._presenter_text(
                    "pagination",
                    "moreCharacteristics",
                    count=str(len(items) - 10),
                )
            )

        return {
            "titulo": titulo,
            "linhas": linhas,
            "dados": {
                "items": items,
                "product_code": product_code,
                "total": len(items),
            },
        }

    def _present_product_stock(
        self,
        items: list,
        *,
        path: str = "",
        title: str | None = None,
        root: dict | None = None,
    ) -> dict:
        return self._host._present_product_stock(
            items,
            path=path,
            title=title,
            root=root,
        )

    def _present_items(self, items: list, *, title: str | None = None) -> dict:
        from app.domain.services.chat_product_operational_content_service import (
            ChatProductOperationalContentService,
        )

        titulo = title or ChatProductOperationalContentService.get(
            "presenter",
            "items",
            "defaultTitle",
        )
        linhas = [
            ChatProductOperationalContentService.format(
                "presenter",
                "items",
                "apiReturned",
                count=len(items),
            )
        ]

        detail_lines = []
        for item in items[:10]:
            if not isinstance(item, dict):
                continue

            if "warehouse" in item and "available_quantity" in item:
                if not title:
                    titulo = ChatProductOperationalContentService.get(
                        "presenter",
                        "stock",
                        "titleDefault",
                    )
                detail_lines.append(
                    ChatProductOperationalContentService.format(
                        "presenter",
                        "stock",
                        "detailLine",
                        branch=item.get("branch"),
                        warehouse=item.get("warehouse"),
                        current=item.get("current_quantity"),
                        available=item.get("available_quantity"),
                        committed=item.get("committed_quantity"),
                        location=item.get("physical_location")
                        or ChatProductOperationalContentService.get(
                            "presenter",
                            "stock",
                            "locationFallback",
                        ),
                    )
                )
            elif "supplier_name" in item or "supplier_code" in item:
                name = item.get("supplier_name") or item.get("supplier_code") or "?"
                lead = item.get("registered_lead_time_days") or item.get("real_avg_lead_time_days")
                price = item.get("last_price")
                parts = [
                    self._host._presenter_text(
                        "itemsListPreview",
                        "entityNameBold",
                        name=str(name),
                    )
                ]
                if lead is not None:
                    parts.append(
                        self._host._presenter_text(
                            "itemsListPreview",
                            "supplierLeadTime",
                            days=str(lead),
                        )
                    )
                if price is not None:
                    parts.append(
                        self._host._presenter_text(
                            "itemsListPreview",
                            "supplierLastPrice",
                            price=self._host._format_currency(price),
                        )
                    )
                detail_lines.append(" | ".join(parts))
            elif "customer_name" in item or "customer_code" in item:
                name = item.get("customer_name") or item.get("customer_code") or "?"
                detail_lines.append(
                    self._host._presenter_text(
                        "itemsListPreview",
                        "entityNameBold",
                        name=str(name),
                    )
                )
            else:
                label_keys = ["name", "description", "supplier_name", "customer_name", "code", "number"]
                label = next((str(item[k]) for k in label_keys if item.get(k)), None)
                if label:
                    detail_lines.append(label)

        if detail_lines:
            linhas = detail_lines

        return {
            "titulo": titulo,
            "linhas": linhas,
            "dados": {
                "items": items[:15],
            },
        }

    def _build_lmp_table(self, items: list, root: dict) -> dict:
        from app.domain.services.chat_presentation_operational_table_service import (
            ChatPresentationOperationalTableService as OpsTable,
        )
        from app.domain.services.external_actions.presenters.product_operational_table_row_enrichment import (
            normalize_lmp_items,
        )

        dict_items = normalize_lmp_items(
            [item for item in items if isinstance(item, dict)]
        )
        title = self._host._route_presentation(
            "tableTitles",
            "lmps",
            total=str(root.get("total", len(dict_items))),
        )
        table = OpsTable.build_items_table(
            self._host.column_label_context,
            dict_items,
            profile_name="lmpList",
            title=title,
            role="lmp",
            path="/lmp",
        )

        if table:
            return table

        return {
            "type": "table",
            "title": title,
            "columns": [],
            "rows": [],
        }

    def _build_items_table(
        self,
        items: list,
        title: str | None = None,
        *,
        path: str = "",
        profile_name: str | None = None,
        entity: str | None = None,
        role: str = "generic",
    ) -> dict | None:
        from app.domain.services.chat_presentation_operational_table_service import (
            ChatPresentationOperationalTableService as OpsTable,
        )
        from app.domain.services.chat_presentation_table_profile_inference_service import (
            ChatPresentationTableProfileInferenceService,
        )

        if not items:
            return None

        dict_items = [item for item in items if isinstance(item, dict)]

        if not dict_items:
            return None

        effective_path = self._host._effective_presentation_path(path)

        if not title:
            title = self._host._presenter_text("generic", "itemsTableDefaultTitle")

        resolved_profile = profile_name or ChatPresentationTableProfileInferenceService.infer_profile_name(
            path=effective_path,
            entity=entity,
            sample_row=dict_items[0],
            column_labels=self._host._column_labels,
        )

        return OpsTable.build_items_table(
            self._host.column_label_context,
            dict_items,
            title=title,
            role=role,
            path=effective_path,
            profile_name=resolved_profile,
        )

    def _present_product_structure(self, root: dict, path: str) -> dict | None:
        root_node = root.get("root")

        if not isinstance(root_node, dict):
            return None

        items = root.get("items")

        if not isinstance(items, list):
            return None

        code = str(root_node.get("code") or "").strip()
        description = str(root_node.get("description") or "").strip()
        total = root.get("total")
        level1_count = len(items)

        description = (
            str(description or "").strip()
            or self._host._route_presentation("structureItems", "noDescription")
        )
        linhas: list[str] = [
            self._host._route_presentation(
                "structureItems",
                "productLine",
                code=code,
                description=description,
            ),
        ]

        if total is not None:
            linhas.append(
                self._host._route_presentation(
                    "structureItems", "totalFromApi", total=str(total)
                )
            )
        elif level1_count:
            linhas.append(
                self._host._route_presentation(
                    "structureItems", "countFromItems", count=str(level1_count)
                )
            )

        mp_codes: set[str] = set()

        for item in items[:10]:
            if not isinstance(item, dict):
                continue

            item_code = str(item.get("code") or "?").strip()
            item_desc = str(item.get("description") or "").strip()
            item_type = str(item.get("type") or "").strip()
            quantity = item.get("quantity")

            if str(item_type).upper() == "MP":
                mp_codes.add(item_code)

            line = self._host._format_structure_component_line(
                item_code,
                item_desc,
                item_type,
                quantity,
            )

            if line:
                linhas.append(line)

        if level1_count > 10:
            linhas.append(
                self._host._presenter_text(
                    "pagination",
                    "moreStructureComponents",
                    count=str(level1_count - 10),
                )
            )

        if mp_codes:
            preview = ", ".join(sorted(mp_codes)[:6])
            suffix = "…" if len(mp_codes) > 6 else ""
            linhas.append(
                self._host._route_presentation(
                    "structureItems",
                    "rawMaterials",
                    count=str(len(mp_codes)),
                    preview=preview,
                    suffix=suffix,
                )
            )

        return {
            "titulo": (
                self._host._route_presentation("structureItems", "titleWithCode", code=code)
                if code
                else self._host._route_presentation("structureItems", "titleGeneric")
            ),
            "linhas": linhas,
            "dados": root,
            "sourcePath": path,
        }

    def _present_product_factory_status(self, root: dict, path: str) -> dict:
        product = root.get("product") if isinstance(root.get("product"), dict) else {}
        code = str(
            product.get("product_code") or product.get("code") or self._host._extract_product_code_from_path(path)
        ).strip()
        description = str(product.get("description") or "").strip()
        status = str(root.get("factory_status") or "").strip()
        linhas: list[str] = []

        if status:
            linhas.append(
                self._host._route_presentation(
                    "factoryStatus",
                    "statusLine",
                    status=status,
                )
            )

        if description:
            linhas.append(
                self._host._route_presentation(
                    "factoryStatus",
                    "productWithDescription",
                    code=code,
                    description=description,
                )
            )
        elif code:
            linhas.append(
                self._host._route_presentation(
                    "factoryStatus",
                    "productCodeOnly",
                    code=code,
                )
            )

        indicators = root.get("indicators") if isinstance(root.get("indicators"), dict) else {}

        for key, value in list(indicators.items())[:6]:
            linhas.append(
                f"{self._host._humanize_key(str(key))}: {self._host._format_field_value(str(key), value)}"
            )

        structure_summary = (root.get("structure") or {}).get("summary") if isinstance(root.get("structure"), dict) else None

        if isinstance(structure_summary, dict):
            exclusive = structure_summary.get("total_exclusive_raw_materials")

            if exclusive is not None:
                linhas.append(
                    self._host._route_presentation(
                        "factoryStatus",
                        "exclusiveRawMaterials",
                        exclusive=str(exclusive),
                    )
                )

        return {
            "titulo": (
                self._host._route_presentation("factoryStatus", "titleWithCode", code=code)
                if code
                else self._host._route_presentation("factoryStatus", "titleGeneric")
            ),
            "linhas": linhas or [self._host._presenter_text("generic", "apiAuthorized")],
            "dados": root,
            "sourcePath": path,
        }
