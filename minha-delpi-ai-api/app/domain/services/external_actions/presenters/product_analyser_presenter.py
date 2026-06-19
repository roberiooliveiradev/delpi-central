"""Product analyser do ExternalActionResultPresenter — Fase 3A lote 2."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )


class ExternalActionProductAnalyserPresenter:
    def __init__(self, host: ExternalActionResultPresenter) -> None:
        self._host = host

    def _presentation_path(self, path: str = "") -> str:
        from app.domain.services.chat_operational_response_profile_service import (
            ChatOperationalResponseProfileService,
        )

        return ChatOperationalResponseProfileService.presentation_path(
            path=self._host._effective_presentation_path(path),
            entity="product_analyser",
        )

    def _normalize_analyser_root(self, root: dict) -> dict:
        normalized = dict(root)

        for key in (
            "product",
            "guide",
            "inspection",
            "structure",
            "customers",
            "suppliers",
        ):
            value = normalized.get(key)

            if isinstance(value, dict):
                normalized[key] = self._host._normalize_api_section(value)

        return normalized

    def _present_product_analyser(self, root: dict, product: dict, path: str) -> dict:
        code = str(product.get("code") or "").strip()
        title = (
            self._host._presenter_text(
                "productPresentationTitles",
                "analyserWithCode",
                code=code,
            )
            if code
            else self._host._presenter_text(
                "productPresentationTitles",
                "analyserGeneric",
            )
        )

        linhas = self._build_product_analyser_body_lines(root, product)

        structure = root.get("structure")
        structure_table = self._build_analyser_structure_components_table(structure)
        structure_tree = self._host.build_tree_presentation(root, path=path)

        return {
            "titulo": title,
            "linhas": linhas,
            "campos": self._host._alias_dict(self._product_analyser_summary(product)),
            "dados": {
                "product": self._product_analyser_summary(product),
                "guideTotal": self._host._total(root.get("guide")),
                "inspectionTotal": self._host._total(root.get("inspection")),
                "structureTotal": self._host._total(structure if isinstance(structure, dict) else None),
            },
            "apresentacao": structure_tree or structure_table,
        }

    def _product_analyser_summary(self, product: dict) -> dict:
        return {
            "code": product.get("code"),
            "description": product.get("description"),
            "type": product.get("type"),
            "unit": product.get("unit"),
            "groupCode": product.get("group_code"),
            "active": product.get("active"),
            "blocked": product.get("blocked"),
            "defaultWarehouse": product.get("default_warehouse"),
            "customerReference": product.get("customer_reference"),
            "lastPurchasePrice": product.get("last_purchase_price"),
            "standardCost": product.get("standard_cost"),
            "lastRevisionDate": product.get("last_revision_date"),
            "ncm": product.get("ncm_ipi_position"),
        }

    def _build_product_analyser_profile_lines(self, product: dict) -> list[str]:
        code = str(product.get("code") or "")
        desc = str(product.get("description") or "")
        purchase_fallback = self._host._presenter_text("analyserProfile", "purchaseFallback")
        last_purchase = product.get("last_purchase_price")

        if last_purchase not in (None, ""):
            last_purchase_display = self._host._format_currency(last_purchase)
        else:
            last_purchase_display = purchase_fallback

        lines = [
            self._host._presenter_text(
                "analyserProfile",
                "introLine",
                code=code,
                description=desc,
            ),
            self._host._presenter_text(
                "analyserProfile",
                "typeLine",
                type=str(product.get("type") or ""),
                unit=str(product.get("unit") or ""),
                group_code=str(product.get("group_code") or ""),
            ),
            self._host._presenter_text(
                "analyserProfile",
                "statusLine",
                active=str(product.get("active") or ""),
                default_warehouse=str(product.get("default_warehouse") or ""),
            ),
        ]

        blocked = str(product.get("blocked") or "").strip()

        if blocked:
            lines.append(
                self._host._presenter_text("analyserProfile", "blockedLine", blocked=blocked)
            )

        customer_reference = str(product.get("customer_reference") or "").strip()

        if customer_reference:
            lines.append(
                self._host._presenter_text(
                    "analyserProfile",
                    "customerRefLine",
                    customer_reference=customer_reference,
                )
            )

        lines.append(
            self._host._presenter_text(
                "analyserProfile",
                "purchaseCostLine",
                last_purchase_price=last_purchase_display,
                standard_cost=self._host._format_currency(product.get("standard_cost")),
            )
        )
        lines.append(
            self._host._presenter_text(
                "analyserProfile",
                "revisionNcmLine",
                last_revision_date=str(product.get("last_revision_date") or ""),
                ncm_ipi_position=str(product.get("ncm_ipi_position") or ""),
            )
        )

        drawing_code = str(product.get("drawing_code") or "").strip()

        if drawing_code:
            lines.append(
                self._host._presenter_text(
                    "analyserProfile",
                    "drawingLine",
                    drawing_code=drawing_code,
                )
            )

        barcode = str(product.get("barcode") or "").strip()

        if barcode:
            lines.append(
                self._host._presenter_text(
                    "analyserProfile",
                    "barcodeLine",
                    barcode=barcode,
                )
            )

        return lines

    def _escape_markdown_table_cell(self, value) -> str:
        text = str(value if value is not None else "").strip()
        return text.replace("|", "\\|").replace("\n", " ")

    def _markdown_table(self, columns: list[tuple[str, str]], rows: list[dict]) -> list[str]:
        if not rows:
            return []

        header = "| " + " | ".join(label for _, label in columns) + " |"
        separator = "| " + " | ".join("---" for _ in columns) + " |"
        body = [
            "| "
            + " | ".join(
                self._escape_markdown_table_cell(row.get(key))
                for key, _ in columns
            )
            + " |"
            for row in rows
        ]

        return [header, separator, *body]

    def _analyser_has_rich_collections(self, root: dict) -> bool:
        for key in ("guide", "inspection", "structure"):
            value = root.get(key)

            if isinstance(value, dict) and (value.get("items") or value.get("total")):
                return True

        return False

    def _build_product_analyser_profile_markdown(self, product: dict) -> list[str]:
        table_rows: list[dict] = []

        for key in self._host._column_labels.product_profile_field_keys(extended=True):
            value = product.get(key)

            if value in (None, ""):
                continue

            if key == "last_purchase_price":
                value = self._host._format_currency(value)
            elif key == "standard_cost":
                value = f"R$ {self._host._format_currency(value)}"

            table_rows.append(
                {
                    "campo": self._host._humanize_key(key),
                    "valor": value,
                }
            )

        if not table_rows:
            return []

        kv_columns = self._host._column_labels.kv_table_column_defs()

        return [
            "",
            *self._markdown_table(
                [(column["key"], column["label"]) for column in kv_columns],
                table_rows,
            ),
        ]

    def _flatten_analyser_guide_rows(self, guide_items: list) -> list[dict]:
        rows: list[dict] = []

        for item in guide_items:
            if not isinstance(item, dict):
                continue

            product_code = str(item.get("product_code") or "?").strip()
            bom_level = item.get("bom_level", 0)
            operations = item.get("operations")

            if not isinstance(operations, list) or not operations:
                op_desc = str(item.get("operation_description") or "").strip()

                if not op_desc:
                    continue

                rows.append(
                    {
                        "product_code": product_code,
                        "bom_level": bom_level,
                        "operation_code": item.get("operation_code") or "",
                        "operation_description": op_desc,
                        "work_center": item.get("work_center") or "",
                    }
                )
                continue

            for operation in operations:
                if not isinstance(operation, dict):
                    continue

                op_desc = str(operation.get("operation_description") or "").strip()

                if not op_desc:
                    continue

                rows.append(
                    {
                        "product_code": product_code,
                        "bom_level": bom_level,
                        "operation_code": operation.get("operation_code") or "",
                        "operation_description": op_desc,
                        "work_center": operation.get("work_center") or "",
                    }
                )

        return rows

    def _build_product_analyser_guide_markdown(self, guide_items: list) -> list[str]:
        rows = self._flatten_analyser_guide_rows(guide_items)

        if not rows:
            return []

        return [
            "",
            self._host._presenter_text("analyserGuideMarkdown", "header"),
            "",
            *self._markdown_table(
                self._host._markdown_column_pairs_for_items(
                    rows,
                    profile_name="analyserGuide",
                    path=self._presentation_path(),
                ),
                rows,
            ),
        ]

    def _build_product_analyser_guide_table(self, root: dict) -> dict | None:
        guide = root.get("guide")

        if not isinstance(guide, dict):
            return None

        guide_items = guide.get("items") or []
        rows = self._flatten_analyser_guide_rows(guide_items)

        if not rows:
            return None

        product = root.get("product") if isinstance(root.get("product"), dict) else {}
        product_code = str(product.get("code") or rows[0].get("product_code") or "").strip()

        return self._host._build_profile_items_table(
            rows,
            profile_name="analyserGuide",
            title=self._analyser_table_title("guide", product_code),
            role="guide",
            path=self._presentation_path(),
        )

    def _flatten_analyser_inspection_rows(self, inspection_items: list) -> list[dict]:
        rows: list[dict] = []

        for item in inspection_items:
            if not isinstance(item, dict):
                continue

            product_code = str(
                item.get("product")
                or item.get("product_code")
                or "?"
            ).strip()
            level = item.get("level", item.get("bom_level", ""))

            if self._has_protheus_inspection_blocks(item):
                qp7 = self._inspection_list(item, "QP7", "qp7")

                for test in qp7:
                    if not isinstance(test, dict):
                        continue

                    rows.append(
                        {
                            "product_code": product_code,
                            "level": level,
                            "section": self._host._presenter_text(
                                "inspectionSections",
                                "dimensional",
                            ),
                            "operation": test.get("QP7_OPERAC") or "",
                            "test": test.get("QP7_ENSAIO") or "",
                            "lab": test.get("QP7_LABOR") or "",
                            "nominal": test.get("QP7_NOMINA") or "",
                            "lower": test.get("QP7_LIE") or test.get("QP7_LIC") or "",
                            "upper": test.get("QP7_LSE") or test.get("QP7_LSC") or "",
                            "unit": test.get("QP7_UNIMED") or "",
                            "detail": "",
                        }
                    )

                qp8 = self._inspection_list(item, "QP8", "qp8")

                for test in qp8:
                    if not isinstance(test, dict):
                        continue

                    rows.append(
                        {
                            "product_code": product_code,
                            "level": level,
                            "section": self._host._presenter_text(
                                "inspectionSections",
                                "textual",
                            ),
                            "operation": test.get("QP8_OPERAC") or "",
                            "test": test.get("QP8_ENSAIO") or "",
                            "lab": "",
                            "nominal": "",
                            "lower": "",
                            "upper": "",
                            "unit": "",
                            "detail": test.get("QP8_TEXTO") or "",
                        }
                    )
                continue

            parent_code = str(
                item.get("parentCode")
                or item.get("parentcode")
                or item.get("Parentcode")
                or ""
            ).strip()

            rows.append(
                {
                    "product_code": product_code,
                    "level": level,
                    "section": self._host._presenter_text(
                        "inspectionSections",
                        "reference",
                    ),
                    "operation": "",
                    "test": "",
                    "lab": "",
                    "nominal": "",
                    "lower": "",
                    "upper": "",
                    "unit": "",
                    "detail": parent_code
                    or self._host._presenter_text("generic", "emptyDetail"),
                }
            )

        return rows

    def _build_product_analyser_inspection_table(self, root: dict) -> dict | None:
        inspection = root.get("inspection")

        if not isinstance(inspection, dict):
            return None

        inspection_items = inspection.get("items") or []
        rows = self._flatten_analyser_inspection_rows(inspection_items)

        if not rows:
            return None

        product = root.get("product") if isinstance(root.get("product"), dict) else {}
        product_code = str(product.get("code") or "").strip()

        return self._host._build_profile_items_table(
            rows,
            profile_name="analyserInspection",
            title=self._analyser_table_title("inspection", product_code),
            role="inspection",
            path=self._presentation_path(),
        )

    def _build_inspection_items_table(
        self,
        items: list,
        *,
        path: str = "",
    ) -> dict | None:
        rows = self._flatten_analyser_inspection_rows(items)

        if not rows:
            return None

        product_code = self._host._extract_product_code_from_path(path)
        title = (
            self._analyser_table_title("inspection", product_code)
            if product_code
            else self._host._infer_items_title(items, path)
            or self._host._presenter_text("analyserTableTitles", "inspectionGeneric")
        )

        return self._host._build_profile_items_table(
            rows,
            profile_name="analyserInspection",
            title=title,
            role="inspection",
            path=path or self._presentation_path(),
        )

    def _has_protheus_inspection_blocks(self, item: dict) -> bool:
        return any(
            key in item
            for key in ("QP6", "QP7", "QP8", "qp6", "qp7", "qp8")
        )

    def _inspection_list(self, item: dict, *keys: str) -> list:
        for key in keys:
            value = item.get(key)

            if isinstance(value, list):
                return value

        return []

    def build_analyser_auxiliary_table_presentations(self, root: dict) -> list[dict]:
        """Tabelas nativas do analyser: ficha, roteiro, inspeção (ordem de leitura no chat)."""
        tables: list[dict] = []
        product = root.get("product")

        if isinstance(product, dict):
            profile_table = self._build_product_analyser_profile_table(product, root)

            if profile_table:
                tables.append(profile_table)

        guide_table = self._build_product_analyser_guide_table(root)

        if guide_table:
            tables.append(guide_table)

        inspection_table = self._build_product_analyser_inspection_table(root)

        if inspection_table:
            tables.append(inspection_table)

        structure_table = self._build_analyser_structure_components_table(root.get("structure"))

        if structure_table:
            tables.append(structure_table)

        return tables

    def _build_product_analyser_inspection_markdown(self, inspection_items: list) -> list[str]:
        if not inspection_items:
            return []

        detailed = [
            item
            for item in inspection_items
            if isinstance(item, dict) and self._has_protheus_inspection_blocks(item)
        ]
        shallow = [
            item
            for item in inspection_items
            if isinstance(item, dict) and not self._has_protheus_inspection_blocks(item)
        ]

        sections: list[str] = [
            "",
            self._host._presenter_text("analyserInspectionMarkdown", "header"),
            "",
        ]

        for item in detailed[:6]:
            product_code = str(
                item.get("product")
                or item.get("product_code")
                or "?"
            ).strip()
            level = item.get("level", item.get("bom_level", 0))
            qp6 = self._inspection_list(item, "QP6", "qp6")
            header_desc = ""

            if qp6 and isinstance(qp6[0], dict):
                header_desc = str(qp6[0].get("QP6_DESCPO") or "").strip()

            sections.append("")
            sections.append(
                self._host._presenter_text(
                    "analyserInspectionMarkdown",
                    "productLine",
                    code=product_code,
                    level=str(level),
                )
            )

            if header_desc:
                sections.append(f"*{header_desc}*")

            qp7 = self._inspection_list(item, "QP7", "qp7")

            if qp7:
                dim_rows = []

                for test in qp7:
                    if not isinstance(test, dict):
                        continue

                    dim_rows.append(
                        {
                            "operation": test.get("QP7_OPERAC") or "",
                            "test": test.get("QP7_ENSAIO") or "",
                            "lab": test.get("QP7_LABOR") or "",
                            "nominal": test.get("QP7_NOMINA") or "",
                            "lower": test.get("QP7_LIE") or test.get("QP7_LIC") or "",
                            "upper": test.get("QP7_LSE") or test.get("QP7_LSC") or "",
                            "unit": test.get("QP7_UNIMED") or "",
                        }
                    )

                if dim_rows:
                    sections.append("")
                    sections.append(
                        self._host._presenter_text(
                            "analyserInspectionMarkdown",
                            "dimensionalSubtitle",
                        )
                    )
                    sections.extend(
                        self._markdown_table(
                            self._host._markdown_column_pairs_for_items(
                                dim_rows,
                                profile_name="analyserInspectionDimensionalMarkdown",
                                path=self._presentation_path(),
                            ),
                            dim_rows,
                        )
                    )

            qp8 = self._inspection_list(item, "QP8", "qp8")

            if qp8:
                text_rows = []

                for test in qp8:
                    if not isinstance(test, dict):
                        continue

                    text_rows.append(
                        {
                            "operation": test.get("QP8_OPERAC") or "",
                            "test": test.get("QP8_ENSAIO") or "",
                            "text": test.get("QP8_TEXTO") or "",
                        }
                    )

                if text_rows:
                    sections.append("")
                    sections.append(
                        self._host._presenter_text(
                            "analyserInspectionMarkdown",
                            "textualSubtitle",
                        )
                    )
                    sections.extend(
                        self._markdown_table(
                            self._host._markdown_column_pairs_for_items(
                                text_rows,
                                profile_name="analyserInspectionTextualMarkdown",
                                path=self._presentation_path(),
                            ),
                            text_rows,
                        )
                    )

        if shallow:
            shallow_rows = []

            for item in shallow[:20]:
                product_code = str(
                    item.get("product")
                    or item.get("product_code")
                    or item.get("Product")
                    or "?"
                ).strip()
                parent_code = str(
                    item.get("parentCode")
                    or item.get("parentcode")
                    or item.get("Parentcode")
                    or ""
                ).strip()
                level = item.get("level", item.get("Nível", item.get("bom_level", "")))

                shallow_rows.append(
                    {
                        "product_code": product_code,
                        "parent_code": parent_code or "—",
                        "level": level,
                        "plan": self._host._presenter_text("generic", "emptyPlan"),
                    }
                )

            if shallow_rows:
                sections.append("")
                sections.append(
                    self._host._presenter_text(
                        "analyserInspectionMarkdown",
                        "shallowSubtitle",
                    )
                )
                sections.extend(
                    self._markdown_table(
                        self._host._markdown_column_pairs_for_items(
                            shallow_rows,
                            profile_name="analyserInspectionShallowMarkdown",
                            path=self._presentation_path(),
                        ),
                        shallow_rows,
                    )
                )

            if len(shallow) > 20:
                sections.append(
                    self._host._presenter_text(
                        "pagination",
                        "moreComponents",
                        count=str(len(shallow) - 20),
                    )
                )

        if len(detailed) > 6:
            sections.append(
                self._host._presenter_text(
                    "pagination",
                    "moreDetailedProducts",
                    count=str(len(detailed) - 6),
                )
            )

        return sections

    def _build_product_analyser_collection_sections(self, root: dict) -> list[str]:
        sections: list[str] = []

        guide = root.get("guide")

        if isinstance(guide, dict):
            guide_items = guide.get("items") or []

            if guide_items:
                if not self._build_product_analyser_guide_table(root):
                    sections.extend(self._build_product_analyser_guide_markdown(guide_items))
            else:
                sections.append(
                    self._host._presenter_text("analyserCollections", "guideEmpty")
                )

        inspection = root.get("inspection")

        if isinstance(inspection, dict):
            inspection_items = inspection.get("items") or []

            if inspection_items:
                if not self._build_product_analyser_inspection_table(root):
                    sections.extend(
                        self._build_product_analyser_inspection_markdown(inspection_items)
                    )
            else:
                sections.append(
                    self._host._presenter_text("analyserCollections", "inspectionEmpty")
                )

        return sections

    def _build_product_analyser_body_lines(
        self,
        root: dict,
        product: dict,
        *,
        compact_for_rich_ui: bool = False,
    ) -> list[str]:
        from app.domain.services.chat_product_analyser_divergence_service import (
            ChatProductAnalyserDivergenceService,
        )

        lines: list[str] = []

        if not compact_for_rich_ui:
            opening = ChatProductAnalyserDivergenceService.build_opening_narrative(
                root,
                product,
            )

            if opening:
                lines.extend(["", opening, ""])

            lines.extend(self._build_product_analyser_profile_lines(product))
            collection_lines = self._build_product_analyser_collection_sections(root)
            lines.extend(collection_lines)

            if not collection_lines and not self._analyser_has_rich_collections(root):
                lines.extend(self._build_product_analyser_profile_markdown(product))

        insights = self._build_product_analyser_insights(root, product)

        if compact_for_rich_ui:
            code = str(product.get("code") or "").strip()
            description = str(product.get("description") or "").strip()

            if code and description:
                lines.append(
                    self._host._presenter_text(
                        "analyserCompact",
                        "productSummary",
                        code=code,
                        description=description,
                    )
                )

            from app.domain.services.chat_presentation_section_availability_service import (
                ChatPresentationSectionAvailabilityService,
            )

            insights = ChatPresentationSectionAvailabilityService.filter_analyser_highlights(
                insights,
            )

        if insights:
            lines.extend(["", self._host._analyser_markdown("highlightsHeader"), ""])
            lines.extend(f"- {line}" for line in insights)

        attention = ChatProductAnalyserDivergenceService.build_attention_points(
            root,
            product,
        )

        if attention:
            lines.extend(["", self._host._analyser_markdown("attentionHeader"), ""])
            lines.extend(
                f"{index}. {point}"
                for index, point in enumerate(attention, start=1)
            )

        structure = root.get("structure")

        if (
            not compact_for_rich_ui
            and isinstance(structure, dict)
            and (structure.get("items") or structure.get("total"))
        ):
            lines.extend(
                [
                    "",
                    self._host._presenter_text(
                        "analyserCollections", "structureVisualizationHint"
                    ),
                ]
            )

        return [line for line in lines if line is not None]

    def _format_collection_item_lines(self, items: list) -> list[str]:
        lines: list[str] = []

        for item in items[:12]:
            if not isinstance(item, dict):
                continue

            if self._has_protheus_inspection_blocks(item):
                lines.extend(self._build_product_analyser_inspection_markdown([item]))
                continue

            formatted = self._format_guide_like_item(item)

            if formatted:
                lines.append(formatted)
                continue

            preview = ", ".join(
                self._host._presenter_text(
                    "generic",
                    "collectionPreviewPair",
                    label=self._host._humanize_key(key),
                    value=str(value),
                )
                for key, value in list(item.items())[:6]
                if value not in (None, "", [], {})
            )
            lines.append(
                self._host._presenter_text(
                    "generic",
                    "collectionPreviewLine",
                    preview=preview,
                )
            )

        if len(items) > 12:
            lines.append(
                self._host._presenter_text(
                    "pagination",
                    "moreRecords",
                    count=str(len(items) - 12),
                )
            )

        return lines

    def _format_guide_like_item(self, item: dict) -> str | None:
        operations = item.get("operations")

        if not isinstance(operations, list) or not operations:
            op_desc = str(item.get("operation_description") or "").strip()

            if op_desc:
                product_code = str(item.get("product_code") or "?").strip()
                level = item.get("bom_level", 0)
                op_code = str(item.get("operation_code") or "").strip()
                center = str(item.get("work_center") or "").strip()
                label = (
                    self._host._presenter_text(
                        "guideItemNarrative",
                        "operationWithCode",
                        operation_code=op_code,
                    )
                    if op_code
                    else self._host._presenter_text(
                        "guideItemNarrative",
                        "operationGeneric",
                    )
                )
                center_part = (
                    self._host._presenter_text(
                        "guideItemNarrative",
                        "centerPart",
                        work_center=center,
                    )
                    if center
                    else ""
                )

                return self._host._presenter_text(
                    "guideItemNarrative",
                    "singleOperation",
                    product_code=product_code,
                    level=str(level),
                    operation_label=label,
                    operation_description=op_desc,
                    center_part=center_part,
                )

            return None

        product_code = str(item.get("product_code") or "?").strip()
        level = item.get("bom_level", 0)
        op_parts: list[str] = []

        for operation in operations[:6]:
            if not isinstance(operation, dict):
                continue

            op_desc = str(operation.get("operation_description") or "").strip()

            if not op_desc:
                continue

            op_code = str(operation.get("operation_code") or "").strip()
            center = str(operation.get("work_center") or "").strip()
            if op_code:
                label = self._host._presenter_text(
                    "guideItemNarrative",
                    "operationLabelWithCode",
                    operation_code=op_code,
                    operation_description=op_desc,
                )
            else:
                label = self._host._presenter_text(
                    "guideItemNarrative",
                    "operationLabelDescriptionOnly",
                    operation_description=op_desc,
                )

            if center:
                label = self._host._presenter_text(
                    "guideItemNarrative",
                    "operationLabelWithCenter",
                    label=label,
                    work_center=center,
                )

            op_parts.append(label)

        if not op_parts:
            return None

        joined = "; ".join(op_parts)

        return self._host._presenter_text(
            "guideItemNarrative",
            "multiOperations",
            product_code=product_code,
            level=str(level),
            operations_joined=joined,
        )

    def _build_product_analyser_insights(self, root: dict, product: dict) -> list[str]:
        insights: list[str] = []
        code = str(product.get("code") or "").strip()
        product_type = str(product.get("type") or "").strip()
        structure = root.get("structure") if isinstance(root.get("structure"), dict) else {}
        items = structure.get("items") if isinstance(structure.get("items"), list) else []

        mp_codes: set[str] = set()
        mp_usage: dict[str, set[str]] = {}

        for item in items:
            if not isinstance(item, dict):
                continue

            parent_code = str(item.get("code") or "").strip()

            for component in item.get("components") or []:
                if not isinstance(component, dict):
                    continue

                component_code = str(component.get("code") or "").strip()

                if not component_code:
                    continue

                if str(component.get("type") or "").upper() == "MP":
                    mp_codes.add(component_code)

                mp_usage.setdefault(component_code, set()).add(parent_code)

        if items:
            insights.append(
                self._host._presenter_text(
                    "analyserInsights",
                    "structureSummary",
                    level1_count=str(len(items)),
                    mp_count=str(len(mp_codes)),
                )
            )

        shared_components = sorted(
            code
            for code, parents in mp_usage.items()
            if len({parent for parent in parents if parent}) > 1
        )

        if shared_components:
            insights.append(
                self._host._analyser_markdown(
                    "sharedComponents",
                    sample=", ".join(shared_components),
                )
            )

        last_purchase_price = product.get("last_purchase_price")
        last_purchase_date = str(product.get("last_purchase_date") or "").strip()

        if last_purchase_price in (0, 0.0, None) and not last_purchase_date:
            insights.append(self._host._analyser_markdown("noRecentPurchaseProduct"))

        standard_cost = product.get("standard_cost")

        if standard_cost not in (None, ""):
            insights.append(
                self._host._analyser_markdown(
                    "standardCost",
                    cost=self._host._format_currency(standard_cost),
                )
            )

        if self._host._collection_is_empty(root.get("guide")):
            insights.append(self._host._presenter_text("analyserInsights", "guideEmpty"))

        if self._host._collection_is_empty(root.get("inspection")):
            insights.append(
                self._host._presenter_text("analyserInsights", "inspectionEmpty")
            )

        blocked = str(product.get("blocked") or "").strip()

        if blocked and blocked not in {"N", "0"}:
            insights.append(
                self._host._presenter_text(
                    "analyserInsights",
                    "blockedInsight",
                    blocked=blocked,
                )
            )

        return insights

    def _flatten_analyser_structure_rows(self, structure: dict | None) -> list[dict]:
        from app.domain.services.chat_drawing_structure_index_service import (
            ChatDrawingStructureIndexService,
        )

        return ChatDrawingStructureIndexService.flatten_component_rows(structure)

    def _build_analyser_structure_components_table(
        self,
        structure: dict | None,
    ) -> dict | None:
        rows = self._flatten_analyser_structure_rows(structure)

        if not rows:
            return None

        product_code = ""

        if isinstance(structure, dict) and isinstance(structure.get("root"), dict):
            product_code = str(structure["root"].get("code") or "").strip()

        title = (
            self._host._presenter_text(
                "structureComponents",
                "titleWithCode",
                code=product_code,
            )
            if product_code
            else self._host._presenter_text("structureComponents", "titleGeneric")
        )

        return self._host._build_profile_items_table(
            rows,
            profile_name="analyserStructureComponents",
            title=title,
            role="structure",
            path=self._presentation_path(),
        )

    def _build_product_analyser_profile_table(
        self,
        product: dict,
        root: dict,
        *,
        path: str = "",
    ) -> dict:
        effective_path = self._presentation_path(path)
        columns = self._host._column_labels.kv_table_column_defs()
        rows = self._host._column_labels.build_kv_profile_rows(
            product,
            extended=True,
            schema_labels=self._host._active_schema_labels,
            path=effective_path,
            profile_name="productProfileExtended",
        )

        for key in ("guide", "inspection", "structure"):
            value = root.get(key)

            if isinstance(value, dict) and value.get("total") is not None:
                rows.append(
                    {
                        "campo": self._host._label_collection(key),
                        "valor": self._host._column_labels.format_collection_total(value["total"]),
                    }
                )

        code = str(product.get("code") or "").strip()

        return {
            "type": "table",
            "title": self._host._presenter_root_format("productProfileTableTitle", code=code),
            "columns": columns,
            "rows": rows,
        }

    def _build_product_analyser_text_presentation(
        self,
        root: dict,
        product: dict,
        path: str,
    ) -> dict | None:
        from app.domain.services.chat_product_operational_content_service import (
            ChatProductOperationalContentService,
        )

        code = str(product.get("code") or "").strip()
        title = (
            ChatProductOperationalContentService.format(
                "presenter",
                "analyser",
                "titleWithCode",
                code=code,
            )
            if code
            else ChatProductOperationalContentService.get(
                "presenter",
                "analyser",
                "titleGeneric",
            )
        )
        from app.domain.services.chat_rich_presentation_text_service import (
            ChatRichPresentationTextService,
        )

        auxiliary_tables = self.build_analyser_auxiliary_table_presentations(root)
        compact_for_rich_ui = ChatRichPresentationTextService.should_compact_narrative(
            table_presentations=auxiliary_tables,
            tree_presentation=self._host.build_tree_presentation(root, path=path),
        )

        body_parts = self._build_product_analyser_body_lines(
            root,
            product,
            compact_for_rich_ui=compact_for_rich_ui,
        )
        markdown_parts = [f"### {title}", ""]

        if not compact_for_rich_ui:
            scope_line = ChatProductOperationalContentService.get(
                "presenter",
                "analyser",
                "scopeIntro",
            )
            markdown_parts.extend([scope_line, ""])

        markdown_parts.extend(body_parts)

        return {
            "type": "markdown",
            "title": title,
            "markdown": "\n".join(markdown_parts).strip(),
        }

    def _analyser_table_title(self, kind: str, product_code: str) -> str:
        if product_code:
            return self._host._presenter_text(
                "analyserTableTitles",
                f"{kind}WithCode",
                code=product_code,
            )

        return self._host._presenter_text("analyserTableTitles", f"{kind}Generic")

    def build_analyser_tree_presentation(self, root: dict, path: str) -> dict | None:
        return self._host.build_tree_presentation(root, path=path)

    def build_analyser_chart_presentation(self, root: dict, path: str) -> dict | None:
        return self._host.build_chart_presentation(root, path=path, force=True)

    def build_analyser_kpi_presentation(self, root: dict, path: str) -> dict | None:
        return None

    def build_analyser_dashboard_presentation(
        self,
        root: dict,
        path: str,
        **_: object,
    ) -> dict | None:
        return self._host.build_dashboard_presentation(root, path=path)
