"""Apresentação do relatório de validação de desenho — consolidação e rótulos."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_drawing_inspection_validation_service import (
    ChatDrawingInspectionValidationService,
)
from app.domain.services.chat_drawing_validation_content_service import (
    ChatDrawingValidationContentService,
)

_CODE_TOKEN = re.compile(r"^\d{5,9}$")


class ChatDrawingValidationPresentationService:
    @classmethod
    def status_label(cls, status: str) -> str:
        node = ChatDrawingValidationContentService.get_node(
            "statusPresentation",
            str(status or "").strip(),
        )

        if isinstance(node, dict) and node.get("label"):
            return str(node["label"])

        return str(status or "—")

    @classmethod
    def status_symbol(cls, status: str) -> str:
        node = ChatDrawingValidationContentService.get_node(
            "statusPresentation",
            str(status or "").strip(),
        )

        if isinstance(node, dict) and node.get("symbol"):
            return str(node["symbol"])

        return "—"

    @classmethod
    def status_display(cls, status: str) -> str:
        symbol = cls.status_symbol(status).strip()
        label = cls.status_label(status).strip()

        if symbol and symbol != "—":
            return f"{symbol} {label}"

        return label

    @classmethod
    def status_labels_map(cls) -> dict[str, str]:
        node = ChatDrawingValidationContentService.get_node("statusPresentation") or {}

        if not isinstance(node, dict):
            return {}

        return {
            str(key): str(value.get("label") or key)
            for key, value in node.items()
            if isinstance(value, dict)
        }

    @classmethod
    def divergence_statuses(cls) -> tuple[str, ...]:
        items = ChatDrawingValidationContentService.list_values(
            "presentation",
            "divergenceStatuses",
        )

        return tuple(str(item).strip() for item in items if str(item).strip())

    @classmethod
    def divergence_items(cls, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        allowed = set(cls.divergence_statuses())

        return [
            item
            for item in items
            if isinstance(item, dict) and str(item.get("status") or "") in allowed
        ]

    @classmethod
    def nonconformity_items(cls, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            item
            for item in items
            if isinstance(item, dict) and str(item.get("status") or "") != "ok"
        ]

    @classmethod
    def format_code(cls, value: Any) -> str:
        token = str(value or "").strip()

        if not token or token == "—":
            return token

        if _CODE_TOKEN.match(token):
            return f"`{token}`"

        return token

    @classmethod
    def format_code_list(cls, value: Any) -> str:
        raw = str(value or "").strip()

        if not raw or raw == "—":
            return raw

        delimiter = ChatDrawingValidationContentService.get(
            "presentation",
            "codeListDelimiter",
            default=", ",
        )
        parts = [part.strip() for part in raw.split(delimiter) if part.strip()]

        if not parts:
            return raw

        return delimiter.join(cls.format_code(part) for part in parts)

    @classmethod
    def format_evidence_cell(cls, value: Any) -> str:
        raw = str(value or "").strip()

        if not raw or raw == "—":
            return raw

        delimiter = ChatDrawingValidationContentService.get(
            "presentation",
            "codeListDelimiter",
            default=", ",
        )

        if delimiter in raw:
            return cls.format_code_list(raw)

        return cls.format_code(raw)

    @classmethod
    def resolve_pdf_product_code(
        cls,
        *,
        pdf_product_code: Any,
        resolved_product_code: Any,
    ) -> str:
        pdf_code = str(pdf_product_code or "").strip()
        resolved = str(resolved_product_code or "").strip()

        if pdf_code:
            return pdf_code

        return resolved

    @classmethod
    def prepare_display_items(cls, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        enriched: list[dict[str, Any]] = []

        for item in items:
            if not isinstance(item, dict):
                continue

            copy = dict(item)
            scope = str(copy.get("pdfScope") or "").strip()

            if scope:
                evidence = str(copy.get("pdfEvidence") or "").strip()
                scope_suffix = ChatDrawingValidationContentService.format(
                    "evidenceFormats",
                    "pdfScopePrefix",
                    scope=scope,
                )

                if evidence and evidence != ChatDrawingValidationContentService.evidence("dash"):
                    copy["pdfEvidence"] = f"{evidence}{scope_suffix}"
                else:
                    copy["pdfEvidence"] = scope

            enriched.append(copy)

        return cls.consolidate_items(cls.expand_items(enriched))

    @classmethod
    def expand_items(cls, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        expand_keys = {
            str(key).strip()
            for key in ChatDrawingValidationContentService.list_values(
                "presentation",
                "expandTemplateKeys",
            )
            if str(key).strip()
        }
        suffix = str(
            ChatDrawingValidationContentService.get(
                "presentation",
                "expandItemTemplateSuffix",
                default="_item",
            )
        ).strip()
        delimiter = ChatDrawingValidationContentService.get(
            "presentation",
            "codeListDelimiter",
            default=", ",
        )
        pdf_keys = {
            str(key).strip()
            for key in ChatDrawingValidationContentService.list_values(
                "presentation",
                "expandPdfEvidenceKeys",
            )
            if str(key).strip()
        }
        api_keys = {
            str(key).strip()
            for key in ChatDrawingValidationContentService.list_values(
                "presentation",
                "expandApiEvidenceKeys",
            )
            if str(key).strip()
        }

        if not expand_keys:
            return [item for item in items if isinstance(item, dict)]

        result: list[dict[str, Any]] = []

        for item in items:
            if not isinstance(item, dict):
                continue

            template_key = str(item.get("templateKey") or "").strip()

            if template_key not in expand_keys:
                result.append(item)
                continue

            evidence_field = (
                "pdfEvidence"
                if template_key in pdf_keys
                else "apiEvidence"
                if template_key in api_keys
                else None
            )

            if not evidence_field:
                result.append(item)
                continue

            codes = [
                part.strip()
                for part in str(item.get(evidence_field) or "").split(delimiter)
                if part.strip() and part.strip() != "—"
            ]

            if len(codes) <= 1:
                result.append(item)
                continue

            item_template = f"{template_key}{suffix}"

            for code in codes:
                pdf_evidence = (
                    code
                    if evidence_field == "pdfEvidence"
                    else str(item.get("pdfEvidence") or ChatDrawingValidationContentService.evidence("dash"))
                )
                api_evidence = (
                    code
                    if evidence_field == "apiEvidence"
                    else str(item.get("apiEvidence") or ChatDrawingValidationContentService.evidence("dash"))
                )

                result.append(
                    ChatDrawingValidationContentService.item_from_template(
                        item_template,
                        status=str(item.get("status") or "pending"),
                        pdf_evidence=pdf_evidence,
                        api_evidence=api_evidence,
                        item_values={"code": code},
                    )
                )

        return result

    @classmethod
    def format_analyser_detail_sections(cls, root: Any) -> list[str]:
        if not isinstance(root, dict) or not root:
            return []

        from app.domain.services.chat_presentation_tree_markdown_service import (
            ChatPresentationTreeMarkdownService,
        )
        from app.domain.services.external_actions.external_action_result_presenter import (
            ExternalActionResultPresenter,
        )

        lines: list[str] = []
        presenter = ExternalActionResultPresenter()
        structure = root.get("structure") if isinstance(root.get("structure"), dict) else {}
        structure_items = (
            structure.get("items") if isinstance(structure.get("items"), list) else []
        )

        if structure_items:
            lines.extend(
                ["", ChatDrawingValidationContentService.get("report", "sections", "structure")]
            )
            tree = presenter.build_tree_presentation(root, path="/products/0/analyser")
            outline = (
                ChatPresentationTreeMarkdownService.build_outline_section(tree)
                if isinstance(tree, dict)
                else ""
            )

            if outline:
                lines.append(outline)
            else:
                lines.extend(cls._format_structure_fallback_table(structure_items))

            structure_total = structure.get("total")

            if isinstance(structure_total, int) and structure_total > len(structure_items):
                lines.append(
                    ChatDrawingValidationContentService.format(
                        "evidenceFormats",
                        "structureItemCount",
                        count=str(structure_total),
                    )
                )

        guide_lines = cls._format_guide_section(root, presenter)

        if guide_lines:
            lines.extend(guide_lines)

        inspection_lines = cls._format_inspection_section(root)

        if inspection_lines:
            lines.extend(inspection_lines)

        return lines

    @classmethod
    def _format_structure_fallback_table(cls, structure_items: list[Any]) -> list[str]:
        lines = [
            "| Código | Descrição | Qtd | Unid. | Tipo |",
            "|---|---|---:|---:|---|",
        ]
        dash = ChatDrawingValidationContentService.evidence("dash")

        for row in structure_items[:24]:
            if not isinstance(row, dict):
                continue

            code = cls.format_code(row.get("code") or dash)
            lines.append(
                "| {code} | {description} | {quantity} | {unit} | {type} |".format(
                    code=code,
                    description=str(row.get("description") or dash)[:48],
                    quantity=row.get("quantity") if row.get("quantity") is not None else dash,
                    unit=cls._resolve_structure_unit(row),
                    type=row.get("type") or dash,
                )
            )

        if len(structure_items) > 24:
            lines.append(
                ChatDrawingValidationContentService.format(
                    "report",
                    "truncatedRows",
                    count=str(len(structure_items) - 24),
                )
            )

        return lines

    @classmethod
    def _format_guide_section(cls, root: dict, presenter: Any) -> list[str]:
        guide = root.get("guide") if isinstance(root.get("guide"), dict) else {}
        guide_items = guide.get("items") if isinstance(guide.get("items"), list) else []

        if not guide_items:
            return []

        flattened = presenter._analyser()._flatten_analyser_guide_rows(guide_items)
        rows = flattened if flattened else guide_items

        lines = [
            "",
            ChatDrawingValidationContentService.get("report", "sections", "guide"),
            "| Produto | Nível | Operação | Centro | Descrição |",
            "|---|---:|---|---|---|",
        ]
        dash = ChatDrawingValidationContentService.evidence("dash")
        max_rows = int(
            ChatDrawingValidationContentService.get(
                "presentation",
                "maxGuideRows",
                default="80",
            )
            or 80
        )

        for row in rows[:max_rows]:
            if not isinstance(row, dict):
                continue

            lines.append(
                "| {product} | {level} | {op} | {center} | {description} |".format(
                    product=cls.format_code(row.get("product_code") or row.get("product") or dash),
                    level=row.get("bom_level") if row.get("bom_level") is not None else row.get("level") or dash,
                    op=cls.format_code(row.get("operation_code") or row.get("operation") or dash),
                    center=str(row.get("work_center") or row.get("center") or row.get("resource_code") or dash),
                    description=str(
                        row.get("operation_description") or row.get("description") or dash
                    )[:40],
                )
            )

        return lines

    @classmethod
    def _format_inspection_count(cls, count: int | None, *, dash: str) -> int | str:
        if count is None:
            return dash

        return count

    @classmethod
    def _format_inspection_section(cls, root: dict) -> list[str]:
        inspection = root.get("inspection") if isinstance(root.get("inspection"), dict) else {}
        inspection_items = (
            inspection.get("items") if isinstance(inspection.get("items"), list) else []
        )

        if not ChatDrawingInspectionValidationService.has_inspection_plan(inspection):
            return []

        lines = [
            "",
            ChatDrawingValidationContentService.get("report", "sections", "inspection"),
            "| Produto | Nível | QP6 | QP7 | QP8 |",
            "|---|---:|---:|---:|---:|",
        ]
        dash = ChatDrawingValidationContentService.evidence("dash")
        rendered_rows = 0

        for row in inspection_items[:12]:
            if not isinstance(row, dict):
                continue

            if not ChatDrawingInspectionValidationService.row_has_inspection_data(row):
                continue

            qp6_count, qp7_count, qp8_count = (
                ChatDrawingInspectionValidationService.row_plan_counts(row)
            )
            level = ChatDrawingInspectionValidationService.row_level(row)

            lines.append(
                "| {product} | {level} | {qp6} | {qp7} | {qp8} |".format(
                    product=cls.format_code(
                        ChatDrawingInspectionValidationService.row_product_code(row) or dash
                    ),
                    level=level if level is not None else dash,
                    qp6=cls._format_inspection_count(qp6_count, dash=dash),
                    qp7=cls._format_inspection_count(qp7_count, dash=dash),
                    qp8=cls._format_inspection_count(qp8_count, dash=dash),
                )
            )
            rendered_rows += 1

        if rendered_rows == 0:
            return []

        return lines

    @classmethod
    def consolidate_items(cls, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        consolidate_keys = {
            str(key).strip()
            for key in ChatDrawingValidationContentService.list_values(
                "presentation",
                "consolidateTemplateKeys",
            )
            if str(key).strip()
        }
        normalized = [item for item in items if isinstance(item, dict)]

        if not consolidate_keys:
            return normalized

        joiner = ChatDrawingValidationContentService.get(
            "presentation",
            "evidenceJoiner",
            default="; ",
        )
        consolidated_template = str(
            ChatDrawingValidationContentService.get(
                "presentation",
                "consolidatedTemplateKey",
                default="segment_lengths_consolidated",
            )
        ).strip()
        buckets: dict[tuple[str, str], list[dict[str, Any]]] = {}

        for item in normalized:
            template_key = str(item.get("templateKey") or "").strip()
            section = str(item.get("section") or "")

            if template_key in consolidate_keys:
                buckets.setdefault((section, template_key), []).append(item)

        result: list[dict[str, Any]] = []
        emitted: set[tuple[str, str]] = set()

        for item in normalized:
            template_key = str(item.get("templateKey") or "").strip()
            section = str(item.get("section") or "")

            if template_key not in consolidate_keys:
                result.append(item)
                continue

            bucket_key = (section, template_key)

            if bucket_key in emitted:
                continue

            emitted.add(bucket_key)
            bucket_items = buckets.get(bucket_key) or []

            if len(bucket_items) <= 1:
                result.extend(bucket_items)
                continue

            pdf_values = [
                str(row.get("pdfEvidence") or "").strip()
                for row in bucket_items
                if str(row.get("pdfEvidence") or "").strip()
            ]
            api_values = [
                str(row.get("apiEvidence") or "").strip()
                for row in bucket_items
                if str(row.get("apiEvidence") or "").strip()
            ]

            result.append(
                ChatDrawingValidationContentService.item_from_template(
                    consolidated_template,
                    status=cls._worst_status(row.get("status") for row in bucket_items),
                    pdf_evidence=joiner.join(dict.fromkeys(pdf_values)),
                    api_evidence=joiner.join(dict.fromkeys(api_values)),
                )
            )

        return result

    @classmethod
    def _worst_status(cls, statuses: Any) -> str:
        ranking = {
            "critical_error": 4,
            "error": 3,
            "pending": 2,
            "ok": 1,
            "not_applicable": 0,
        }
        best = "pending"

        for status in statuses:
            key = str(status or "").strip()

            if ranking.get(key, 0) >= ranking.get(best, 0):
                best = key

        return best

    @classmethod
    def build_export_tables(cls, package: dict[str, Any]) -> list[dict[str, Any]]:
        if not isinstance(package, dict):
            return []

        analysis = package.get("drawingAnalysis") if isinstance(package.get("drawingAnalysis"), dict) else {}
        product = package.get("productSummary") if isinstance(package.get("productSummary"), dict) else {}
        root = package.get("analyserRoot") if isinstance(package.get("analyserRoot"), dict) else {}
        raw_items = analysis.get("items") if isinstance(analysis.get("items"), list) else []
        display_items = cls.prepare_display_items(raw_items)
        pdf_fields = ChatDrawingValidationContentService.get_node("reportFields", "pdf") or {}
        api_fields = ChatDrawingValidationContentService.get_node("reportFields", "api") or {}
        dash = ChatDrawingValidationContentService.evidence("dash")

        pdf_code = cls.resolve_pdf_product_code(
            pdf_product_code=analysis.get("pdfProductCode"),
            resolved_product_code=product.get("code") or analysis.get("productCode"),
        )

        tables: list[dict[str, Any]] = [
            cls._build_export_table(
                "pdfData",
                column_keys=["field", "value"],
                column_labels=cls._export_column_labels("keyValue"),
                rows=[
                    {
                        "field": str(pdf_fields.get("code", "Código")),
                        "value": cls.format_code(pdf_code) if pdf_code else dash,
                    },
                    {
                        "field": str(pdf_fields.get("revision", "Revisão (PDF)")),
                        "value": str(analysis.get("revisionPdf") or dash),
                    },
                    {
                        "field": str(pdf_fields.get("attached", "PDF anexado")),
                        "value": (
                            str(pdf_fields.get("attachedYes", "Sim"))
                            if analysis.get("hasPdfAttachment")
                            else str(pdf_fields.get("attachedNo", "Não"))
                        ),
                    },
                ],
            ),
            cls._build_export_table(
                "apiData",
                column_keys=["field", "value"],
                column_labels=cls._export_column_labels("keyValue"),
                rows=[
                    {
                        "field": str(api_fields.get("code", "Código")),
                        "value": cls.format_code(
                            product.get("code") or analysis.get("productCode") or dash
                        ),
                    },
                    {
                        "field": str(api_fields.get("description", "Descrição")),
                        "value": str(product.get("description") or dash),
                    },
                    {
                        "field": str(api_fields.get("revision", "Revisão (API)")),
                        "value": str(product.get("last_revision_date") or dash),
                    },
                ],
            ),
        ]

        structure_rows = cls._export_structure_rows(root)

        if structure_rows:
            tables.append(
                cls._build_export_table(
                    "structure",
                    column_keys=["code", "description", "quantity", "unit", "type", "level"],
                    column_labels=cls._export_column_labels("structure"),
                    rows=structure_rows,
                )
            )

        guide_rows = cls._export_guide_rows(root)

        if guide_rows:
            tables.append(
                cls._build_export_table(
                    "guide",
                    column_keys=["product", "level", "operation", "center", "description"],
                    column_labels=cls._export_column_labels("guide"),
                    rows=guide_rows,
                )
            )

        inspection_rows = cls._export_inspection_rows(root)

        if inspection_rows:
            tables.append(
                cls._build_export_table(
                    "inspection",
                    column_keys=["product", "level", "qp6", "qp7", "qp8"],
                    column_labels=cls._export_column_labels("inspection"),
                    rows=inspection_rows,
                )
            )

        nonconformity_rows = [
            {
                "section": str(item.get("section") or ""),
                "item": str(item.get("item") or ""),
                "status": cls.status_label(str(item.get("status") or "")),
                "pdfEvidence": str(item.get("pdfEvidence") or ""),
                "apiEvidence": str(item.get("apiEvidence") or ""),
                "recommendation": str(item.get("recommendation") or ""),
            }
            for item in cls.nonconformity_items(display_items)
        ]

        if nonconformity_rows:
            tables.append(
                cls._build_export_table(
                    "nonconformities",
                    column_keys=[
                        "section",
                        "item",
                        "status",
                        "pdfEvidence",
                        "apiEvidence",
                        "recommendation",
                    ],
                    column_labels=cls._export_spreadsheet_headers(),
                    rows=nonconformity_rows,
                )
            )

        checklist_rows = [
            {
                "section": str(item.get("section") or ""),
                "item": str(item.get("item") or ""),
                "status": cls.status_label(str(item.get("status") or "")),
                "observation": str(item.get("recommendation") or ""),
            }
            for item in display_items
        ]

        if checklist_rows:
            tables.append(
                cls._build_export_table(
                    "checklist",
                    column_keys=["section", "item", "status", "observation"],
                    column_labels=[
                        "Seção",
                        "Item",
                        "Status",
                        "Observação",
                    ],
                    rows=checklist_rows,
                )
            )

        return [table for table in tables if table.get("rows")]

    @classmethod
    def _export_column_labels(cls, key: str) -> list[str]:
        labels = ChatDrawingValidationContentService.list_values(
            "export",
            "columnLabels",
            key,
        )

        return [str(label) for label in labels if str(label).strip()]

    @classmethod
    def _export_spreadsheet_headers(cls) -> list[str]:
        headers = ChatDrawingValidationContentService.list_values(
            "export",
            "spreadsheetHeaders",
        )

        if headers:
            return [str(header) for header in headers]

        return [
            "Seção",
            "Item",
            "Status",
            "Evidência PDF",
            "Evidência API",
            "Recomendação",
        ]

    @classmethod
    def _build_export_table(
        cls,
        key: str,
        *,
        column_keys: list[str],
        column_labels: list[str],
        rows: list[dict[str, Any]],
    ) -> dict[str, Any]:
        labels = column_labels or column_keys
        columns = [
            {"key": column_keys[index], "label": labels[index]}
            for index in range(len(column_keys))
            if index < len(labels)
        ]

        return {
            "key": key,
            "title": ChatDrawingValidationContentService.get("export", "tableTitles", key)
            or key,
            "sheetName": ChatDrawingValidationContentService.get("export", "sheetNames", key)
            or key[:31],
            "columns": columns,
            "rows": rows,
        }

    @classmethod
    def _resolve_structure_unit(cls, row: dict[str, Any]) -> str:
        dash = ChatDrawingValidationContentService.evidence("dash")

        for key in ("unit", "component_unit", "parent_unit", "unidade"):
            value = row.get(key)

            if value is not None and str(value).strip():
                return str(value).strip()

        return dash

    @classmethod
    def _export_structure_rows(cls, root: dict[str, Any]) -> list[dict[str, str]]:
        structure = root.get("structure") if isinstance(root.get("structure"), dict) else {}
        structure_items = (
            structure.get("items") if isinstance(structure.get("items"), list) else []
        )

        if not structure_items:
            return []

        dash = ChatDrawingValidationContentService.evidence("dash")
        rows: list[dict[str, str]] = []

        def _walk(items: list[Any], level: int = 0) -> None:
            for row in items:
                if not isinstance(row, dict):
                    continue

                rows.append(
                    {
                        "code": cls.format_code(row.get("code") or dash),
                        "description": str(row.get("description") or dash),
                        "quantity": str(
                            row.get("quantity") if row.get("quantity") is not None else dash
                        ),
                        "unit": cls._resolve_structure_unit(row),
                        "type": str(row.get("type") or dash),
                        "level": str(level),
                    }
                )

                components = row.get("components")

                if isinstance(components, list) and components:
                    _walk(components, level + 1)

        _walk(structure_items)
        return rows

    @classmethod
    def _export_guide_rows(cls, root: dict[str, Any]) -> list[dict[str, str]]:
        guide = root.get("guide") if isinstance(root.get("guide"), dict) else {}
        guide_items = guide.get("items") if isinstance(guide.get("items"), list) else []

        if not guide_items:
            return []

        from app.domain.services.external_actions.external_action_result_presenter import (
            ExternalActionResultPresenter,
        )

        presenter = ExternalActionResultPresenter()
        flattened = presenter._analyser()._flatten_analyser_guide_rows(guide_items)
        rows_source = flattened if flattened else guide_items
        dash = ChatDrawingValidationContentService.evidence("dash")
        max_rows = int(
            ChatDrawingValidationContentService.get(
                "presentation",
                "maxGuideRows",
                default="80",
            )
            or 80
        )
        rows: list[dict[str, str]] = []

        for row in rows_source[:max_rows]:
            if not isinstance(row, dict):
                continue

            rows.append(
                {
                    "product": cls.format_code(
                        row.get("product_code") or row.get("product") or dash
                    ),
                    "level": str(
                        row.get("bom_level")
                        if row.get("bom_level") is not None
                        else row.get("level") or dash
                    ),
                    "operation": cls.format_code(
                        row.get("operation_code") or row.get("operation") or dash
                    ),
                    "center": str(
                        row.get("work_center")
                        or row.get("center")
                        or row.get("resource_code")
                        or dash
                    ),
                    "description": str(
                        row.get("operation_description") or row.get("description") or dash
                    ),
                }
            )

        return rows

    @classmethod
    def _export_inspection_rows(cls, root: dict[str, Any]) -> list[dict[str, str]]:
        inspection = root.get("inspection") if isinstance(root.get("inspection"), dict) else {}
        inspection_items = (
            inspection.get("items") if isinstance(inspection.get("items"), list) else []
        )

        if not ChatDrawingInspectionValidationService.has_inspection_plan(inspection):
            return []

        dash = ChatDrawingValidationContentService.evidence("dash")
        rows: list[dict[str, str]] = []

        for row in inspection_items:
            if not isinstance(row, dict):
                continue

            if not ChatDrawingInspectionValidationService.row_has_inspection_data(row):
                continue

            qp6_count, qp7_count, qp8_count = (
                ChatDrawingInspectionValidationService.row_plan_counts(row)
            )
            level = ChatDrawingInspectionValidationService.row_level(row)

            rows.append(
                {
                    "product": cls.format_code(
                        ChatDrawingInspectionValidationService.row_product_code(row) or dash
                    ),
                    "level": str(level if level is not None else dash),
                    "qp6": str(cls._format_inspection_count(qp6_count, dash=dash)),
                    "qp7": str(cls._format_inspection_count(qp7_count, dash=dash)),
                    "qp8": str(cls._format_inspection_count(qp8_count, dash=dash)),
                }
            )

        return rows
