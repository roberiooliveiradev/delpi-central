"""Merge payload `/analyser` com contexto de análise de desenho — Onda 12 MVP."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService
from app.domain.services.chat_drawing_validation_content_service import (
    ChatDrawingValidationContentService,
)
from app.domain.services.chat_drawing_validation_presentation_service import (
    ChatDrawingValidationPresentationService,
)


class ChatDrawingValidationOrchestrationService:
    """Gera relatório estruturado e metadata `drawingAnalysis` a partir da API."""

    _STATUS_OK = "ok"
    _STATUS_PENDING = "pending"
    _STATUS_ERROR = "error"
    _STATUS_CRITICAL = "critical_error"
    _STATUS_NA = "not_applicable"

    @classmethod
    def _content(cls, *path: str, default: str = "", **values: str) -> str:
        if values:
            return ChatDrawingValidationContentService.format(
                *path,
                default=default,
                **values,
            )

        return ChatDrawingValidationContentService.get(*path, default=default)

    @classmethod
    def _evidence(cls, key: str) -> str:
        return ChatDrawingValidationContentService.evidence(key)

    @classmethod
    def _item_from_template(
        cls,
        template_key: str,
        *,
        status: str,
        pdf_evidence: str,
        api_evidence: str,
        recommendation: str | None = None,
        recommendation_field: str = "recommendation",
        item_values: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        return ChatDrawingValidationContentService.item_from_template(
            template_key,
            status=status,
            pdf_evidence=pdf_evidence,
            api_evidence=api_evidence,
            recommendation=recommendation,
            recommendation_field=recommendation_field,
            item_values=item_values,
        )

    @classmethod
    def build_from_analyser_payload(
        cls,
        *,
        product_code: str,
        payload: dict | None,
        has_pdf_attachment: bool = False,
        api_ok: bool = True,
        api_status_code: int | None = None,
        pdf_extract: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        code = str(product_code or "").strip()
        root = payload if isinstance(payload, dict) else {}
        product = root.get("product") if isinstance(root.get("product"), dict) else {}

        items: list[dict[str, Any]] = []

        if not api_ok or api_status_code == 404 or not product:
            items.append(
                cls._item_from_template(
                    "product_not_found",
                    status=cls._STATUS_CRITICAL,
                    pdf_evidence=cls._evidence("dash"),
                    api_evidence=cls._evidence("notFound"),
                )
            )
            return cls._package(
                product_code=code,
                items=items,
                has_pdf_attachment=has_pdf_attachment,
                product=product,
                pdf_extract=pdf_extract,
                analyser_root=root,
            )

        items.append(
            cls._item_from_template(
                "product_found",
                status=cls._STATUS_OK,
                pdf_evidence=cls._evidence("dash"),
                api_evidence=str(product.get("code") or code),
            )
        )

        revision = str(product.get("last_revision_date") or product.get("revision") or "").strip()
        items.append(
            cls._item_from_template(
                "revision_api",
                status=cls._STATUS_OK if revision else cls._STATUS_PENDING,
                pdf_evidence=(
                    cls._evidence("pendingPdf")
                    if not has_pdf_attachment
                    else cls._evidence("dash")
                ),
                api_evidence=revision or cls._evidence("dash"),
                recommendation_field=(
                    "recommendationWithPdf"
                    if has_pdf_attachment
                    else "recommendationNoPdf"
                ),
            )
        )

        guide = root.get("guide") if isinstance(root.get("guide"), dict) else {}
        guide_items = guide.get("items") if isinstance(guide.get("items"), list) else []
        has_guide = bool(guide_items)

        items.append(
            cls._item_from_template(
                "guide",
                status=cls._STATUS_OK if has_guide else cls._STATUS_CRITICAL,
                pdf_evidence=cls._evidence("dash"),
                api_evidence=(
                    ChatDrawingValidationContentService.evidence_format(
                        "guideOperationCount",
                        count=str(len(guide_items)),
                    )
                    if has_guide
                    else cls._evidence("absent")
                ),
                recommendation_field=(
                    "recommendationOk" if has_guide else "recommendationMissing"
                ),
            )
        )

        has_ct99 = cls._root_guide_has_ct99(root, code)

        items.append(
            cls._item_from_template(
                "guide_ct99",
                status=cls._STATUS_OK if has_ct99 else cls._STATUS_ERROR,
                pdf_evidence=cls._evidence("dash"),
                api_evidence=(
                    cls._evidence("linked") if has_ct99 else cls._evidence("absent")
                ),
                recommendation_field=(
                    "recommendationOk" if has_ct99 else "recommendationMissing"
                ),
            )
        )

        inspection = root.get("inspection") if isinstance(root.get("inspection"), dict) else {}
        inspection_items = (
            inspection.get("items") if isinstance(inspection.get("items"), list) else []
        )
        has_qp = False

        for row in inspection_items:
            if not isinstance(row, dict):
                continue

            if row.get("QP6") or row.get("QP7") or row.get("QP8"):
                has_qp = True
                break

        items.append(
            cls._item_from_template(
                "inspection_qp",
                status=cls._STATUS_OK if has_qp else cls._STATUS_CRITICAL,
                pdf_evidence=cls._evidence("dash"),
                api_evidence=(
                    cls._evidence("linked") if has_qp else cls._evidence("absent")
                ),
                recommendation_field=(
                    "recommendationOk" if has_qp else "recommendationMissing"
                ),
            )
        )

        if not has_pdf_attachment:
            items.append(
                cls._item_from_template(
                    "pdf_missing",
                    status=cls._STATUS_PENDING,
                    pdf_evidence=cls._evidence("noAttachment"),
                    api_evidence=cls._evidence("dash"),
                )
            )
            items.append(
                cls._item_from_template(
                    "bom_pending",
                    status=cls._STATUS_PENDING,
                    pdf_evidence=cls._evidence("dash"),
                    api_evidence=ChatDrawingValidationContentService.evidence_format(
                        "structureItemCount",
                        count=str(guide.get("total", len(guide_items))),
                    ),
                )
            )
        else:
            pdf_meta = pdf_extract if isinstance(pdf_extract, dict) else {}
            legible = bool(pdf_meta.get("legible"))

            items.append(
                cls._item_from_template(
                    "pdf_attached",
                    status=cls._STATUS_OK if legible else cls._STATUS_PENDING,
                    pdf_evidence=ChatDrawingValidationContentService.get(
                        "itemTemplates",
                        "pdf_attached",
                        "pdfEvidenceLegible" if legible else "pdfEvidenceIllegible",
                    ),
                    api_evidence=cls._evidence("dash"),
                    recommendation_field=(
                        "recommendationLegible"
                        if legible
                        else "recommendationIllegible"
                    ),
                )
            )

            items.extend(cls._pdf_cross_check_items(product, code, pdf_meta))

            from app.domain.services.chat_drawing_structure_validation_service import (
                ChatDrawingStructureValidationService,
            )

            items.extend(
                ChatDrawingStructureValidationService.build_check_items(
                    root=root,
                    pdf_extract=pdf_meta,
                    product_code=code,
                )
            )

        return cls._package(
            product_code=code,
            items=items,
            has_pdf_attachment=has_pdf_attachment,
            product=product,
            pdf_extract=pdf_extract,
            analyser_root=root,
        )

    @classmethod
    def format_report_markdown(cls, package: dict[str, Any]) -> str:
        analysis = package.get("drawingAnalysis") or {}
        product = package.get("productSummary") or {}
        raw_items = analysis.get("items") or []
        display_items = ChatDrawingValidationPresentationService.consolidate_items(
            raw_items if isinstance(raw_items, list) else []
        )
        pdf_fields = ChatDrawingValidationContentService.get_node("reportFields", "pdf") or {}
        api_fields = ChatDrawingValidationContentService.get_node("reportFields", "api") or {}
        table_header = cls._content("reportFields", "tableHeader", default="| Campo | Valor |")
        table_separator = cls._content(
            "reportFields",
            "tableSeparator",
            default="|---|---|",
        )

        lines = [
            cls._content("report", "title"),
            "",
            cls._content("report", "sections", "overall"),
            str(analysis.get("overallLabel") or cls._evidence("dash")),
            "",
            cls._content("report", "sections", "pdfData"),
            table_header,
            table_separator,
            f"| {pdf_fields.get('code', 'Código')} | {analysis.get('pdfProductCode') or cls._evidence('dash')} |",
            f"| {pdf_fields.get('revision', 'Revisão (PDF)')} | {analysis.get('revisionPdf') or cls._evidence('dash')} |",
            f"| {pdf_fields.get('attached', 'PDF anexado')} | {pdf_fields.get('attachedYes', 'Sim') if analysis.get('hasPdfAttachment') else pdf_fields.get('attachedNo', 'Não')} |",
            "",
            cls._content("report", "sections", "apiData"),
            table_header,
            table_separator,
            f"| {api_fields.get('code', 'Código')} | {product.get('code') or analysis.get('productCode') or cls._evidence('dash')} |",
            f"| {api_fields.get('description', 'Descrição')} | {product.get('description') or cls._evidence('dash')} |",
            f"| {api_fields.get('revision', 'Revisão (API)')} | {product.get('last_revision_date') or cls._evidence('dash')} |",
        ]

        lines.extend(cls._format_analyser_detail_sections(package.get("analyserRoot")))

        lines.extend(
            [
                "",
                cls._content("report", "sections", "critical"),
                "| Seção | Item | Status | PDF | API | Ação |",
                "|---|---|---|---|---|---|",
            ]
        )

        divergences = ChatDrawingValidationPresentationService.divergence_items(
            raw_items if isinstance(raw_items, list) else []
        )

        if not divergences:
            lines.append(cls._content("report", "noCriticalRow"))
        else:
            row_tpl = cls._content("report", "criticalRow")
            for item in divergences:
                lines.append(
                    row_tpl.format(
                        section=item.get("section") or cls._evidence("dash"),
                        item=item.get("item") or cls._evidence("dash"),
                        status=ChatDrawingValidationPresentationService.status_display(
                            str(item.get("status") or "")
                        ),
                        pdf=item.get("pdfEvidence") or cls._evidence("dash"),
                        api=item.get("apiEvidence") or cls._evidence("dash"),
                        rec=item.get("recommendation") or cls._evidence("dash"),
                    )
                )

        lines.extend(
            [
                "",
                cls._content("report", "sections", "checklist"),
                "| Seção | Item | Status | Observação |",
                "|---|---|---|---|",
            ]
        )

        checklist_tpl = cls._content("report", "checklistRow")
        for item in display_items:
            lines.append(
                checklist_tpl.format(
                    section=item.get("section") or cls._evidence("dash"),
                    item=item.get("item") or cls._evidence("dash"),
                    status=ChatDrawingValidationPresentationService.status_display(
                        str(item.get("status") or "")
                    ),
                    rec=item.get("recommendation") or cls._evidence("dash"),
                )
            )

        lines.extend(
            [
                "",
                cls._content("report", "sections", "conclusion"),
                str(analysis.get("conclusion") or cls._evidence("dash")),
            ]
        )

        return "\n".join(lines)

    @classmethod
    def format_critical_only_markdown(cls, analysis: dict[str, Any]) -> str:
        product_code = str(analysis.get("productCode") or "—")
        lines = [
            cls._content("criticalReport", "title"),
            "",
            cls._content("report", "productLine", code=product_code),
            cls._content(
                "report",
                "statusLine",
                label=str(analysis.get("overallLabel") or cls._evidence("dash")),
            ),
            "",
            "| Seção | Item | PDF | API | Ação |",
            "|---|---|---|---|---|",
        ]

        critical = ChatDrawingValidationPresentationService.divergence_items(
            analysis.get("items") if isinstance(analysis.get("items"), list) else []
        )
        critical_only = [
            item
            for item in critical
            if str(item.get("status") or "") == cls._STATUS_CRITICAL
        ]

        if not critical_only:
            lines.append(cls._content("criticalReport", "noCriticalRow"))
        else:
            row_tpl = cls._content("criticalReport", "criticalRow")
            for item in critical_only:
                lines.append(
                    row_tpl.format(
                        section=item.get("section") or cls._evidence("dash"),
                        item=item.get("item") or cls._evidence("dash"),
                        pdf=item.get("pdfEvidence") or cls._evidence("dash"),
                        api=item.get("apiEvidence") or cls._evidence("dash"),
                        rec=item.get("recommendation") or cls._evidence("dash"),
                    )
                )

        return "\n".join(lines)

    @classmethod
    def format_section_filter_markdown(
        cls,
        analysis: dict[str, Any],
        *,
        section_keywords: tuple[str, ...],
        title: str,
    ) -> str:
        product_code = str(analysis.get("productCode") or "—")
        lowered = tuple(keyword.casefold() for keyword in section_keywords)

        filtered = [
            item
            for item in (analysis.get("items") or [])
            if any(
                keyword in str(item.get("section") or "").casefold()
                or keyword in str(item.get("item") or "").casefold()
                for keyword in lowered
            )
        ]

        lines = [
            f"# {title}",
            "",
            f"**Produto:** {product_code}",
            "",
            "| Seção | Item | Status | Observação |",
            "|---|---|---|---|",
        ]

        if not filtered:
            lines.append("| — | Nenhum item nesta seção | — | — |")
        else:
            for item in filtered:
                lines.append(
                    "| {section} | {item} | {status} | {rec} |".format(
                        section=item.get("section") or "—",
                        item=item.get("item") or "—",
                        status=ChatDrawingValidationPresentationService.status_display(
                            str(item.get("status") or "")
                        ),
                        rec=item.get("recommendation") or "—",
                    )
                )

        return "\n".join(lines)

    @classmethod
    def wrap_direct_answer(
        cls,
        direct_answer: str,
        *,
        package: dict[str, Any],
    ) -> str:
        report = cls.format_report_markdown(package).strip()
        body = str(direct_answer or "").strip()

        if not body:
            return report

        return f"{report}\n\n---\n\n## Dados operacionais (API DELPI)\n\n{body}"

    @classmethod
    def _item(
        cls,
        *,
        section: str,
        item: str,
        status: str,
        pdf_evidence: str,
        api_evidence: str,
        rule: str,
        recommendation: str,
    ) -> dict[str, Any]:
        return {
            "section": section,
            "item": item,
            "status": status,
            "pdfEvidence": pdf_evidence,
            "apiEvidence": api_evidence,
            "rule": rule,
            "recommendation": recommendation,
        }

    @classmethod
    def _pdf_cross_check_items(
        cls,
        product: dict,
        api_code: str,
        pdf_extract: dict,
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        pdf_code = str(pdf_extract.get("productCode") or "").strip()
        api_product_code = str(product.get("code") or api_code or "").strip()

        if pdf_code and api_product_code and pdf_code != api_product_code:
            items.append(
                cls._item_from_template(
                    "product_code_mismatch",
                    status=cls._STATUS_CRITICAL,
                    pdf_evidence=pdf_code,
                    api_evidence=api_product_code,
                )
            )
        elif pdf_code and api_product_code:
            items.append(
                cls._item_from_template(
                    "product_code_ok",
                    status=cls._STATUS_OK,
                    pdf_evidence=pdf_code,
                    api_evidence=api_product_code,
                )
            )

        pdf_revision = str(pdf_extract.get("revision") or "").strip()
        pdf_internal_revision = str(pdf_extract.get("internalRevision") or "").strip()
        api_current_revision = str(product.get("current_revision") or "").strip()
        api_revision_date = str(
            product.get("last_revision_date") or product.get("revision") or ""
        ).strip()

        revision_item = cls._build_revision_cross_check_item(
            pdf_revision=pdf_revision,
            pdf_internal_revision=pdf_internal_revision,
            api_current_revision=api_current_revision,
            api_revision_date=api_revision_date,
        )

        if revision_item:
            items.append(revision_item)

        return items

    @classmethod
    def _build_revision_cross_check_item(
        cls,
        *,
        pdf_revision: str,
        pdf_internal_revision: str,
        api_current_revision: str,
        api_revision_date: str,
    ) -> dict[str, Any] | None:
        api_compare = cls._resolve_api_revision_for_compare(
            api_current_revision,
            api_revision_date,
        )
        pdf_compare = cls._normalize_revision_number(
            pdf_internal_revision or pdf_revision
        )

        if not pdf_compare or not api_compare:
            return None

        content = ChatDrawingValidationContentService
        pdf_evidence = (
            content.evidence_format("revisionInternalTable", revision=pdf_internal_revision)
            if pdf_internal_revision
            else content.evidence_format("revisionTitle", revision=pdf_revision)
        )

        if pdf_compare == api_compare:
            return cls._item_from_template(
                "revision_cross_ok",
                status=cls._STATUS_OK,
                pdf_evidence=pdf_evidence,
                api_evidence=api_current_revision or api_revision_date,
            )

        client_revision = cls._normalize_revision_number(pdf_revision)

        if (
            pdf_internal_revision
            and client_revision
            and client_revision != pdf_compare
            and pdf_compare == api_compare
        ):
            return cls._item_from_template(
                "revision_client_ok",
                status=cls._STATUS_OK,
                pdf_evidence=content.evidence_format(
                    "revisionClientPair",
                    internal=pdf_internal_revision,
                    client=client_revision,
                ),
                api_evidence=api_current_revision or api_revision_date,
            )

        if len(api_revision_date) > 4 and not pdf_internal_revision:
            return cls._item_from_template(
                "revision_manual_pending",
                status=cls._STATUS_PENDING,
                pdf_evidence=content.evidence_format(
                    "revisionTitle",
                    revision=pdf_revision,
                ),
                api_evidence=api_revision_date,
            )

        return cls._item_from_template(
            "revision_critical",
            status=cls._STATUS_CRITICAL,
            pdf_evidence=pdf_evidence,
            api_evidence=api_current_revision or api_revision_date,
        )

    @classmethod
    def _resolve_api_revision_for_compare(
        cls,
        current_revision: str,
        revision_date: str,
    ) -> str:
        if current_revision:
            return cls._normalize_revision_number(current_revision)

        date_value = str(revision_date or "").strip()

        if date_value.isdigit() and len(date_value) == 8:
            return ""

        return cls._normalize_revision_number(date_value)

    @classmethod
    def _normalize_revision_number(cls, raw: str) -> str:
        value = str(raw or "").strip()

        if not value:
            return ""

        digits = "".join(char for char in value if char.isdigit())

        if not digits:
            return ""

        try:
            return str(int(digits)).zfill(2)
        except ValueError:
            return digits[-2:].zfill(2)

    @classmethod
    def _root_guide_has_ct99(cls, root: dict, product_code: str) -> bool:
        guide = root.get("guide") if isinstance(root.get("guide"), dict) else {}
        root_code = str(product_code or "").strip()

        for row in guide.get("items") or []:
            if not isinstance(row, dict):
                continue

            if str(row.get("product_code") or "").strip() != root_code:
                continue

            for field in ("work_center", "resource_code"):
                marker = str(row.get(field) or "").strip().upper()

                prefix = ChatDrawingPatternsService.final_inspection_work_center_prefix().upper()

                if marker.startswith(prefix):
                    return True

        return False

    @classmethod
    def _format_analyser_detail_sections(cls, root: Any) -> list[str]:
        if not isinstance(root, dict) or not root:
            return []

        lines: list[str] = []
        structure = root.get("structure") if isinstance(root.get("structure"), dict) else {}
        structure_items = (
            structure.get("items") if isinstance(structure.get("items"), list) else []
        )

        if structure_items:
            lines.extend(["", cls._content("report", "sections", "structure")])
            lines.append("| Código | Descrição | Qtd | Tipo |")
            lines.append("|---|---|---:|---|")

            for row in structure_items[:12]:
                if not isinstance(row, dict):
                    continue

                lines.append(
                    "| {code} | {description} | {quantity} | {type} |".format(
                        code=row.get("code") or cls._evidence("dash"),
                        description=str(row.get("description") or cls._evidence("dash"))[:48],
                        quantity=row.get("quantity") if row.get("quantity") is not None else cls._evidence("dash"),
                        type=row.get("type") or cls._evidence("dash"),
                    )
                )

            if len(structure_items) > 12:
                lines.append(
                    cls._content(
                        "report",
                        "truncatedRows",
                        count=len(structure_items) - 12,
                    )
                )

        guide = root.get("guide") if isinstance(root.get("guide"), dict) else {}
        guide_items = guide.get("items") if isinstance(guide.get("items"), list) else []

        if guide_items:
            lines.extend(["", cls._content("report", "sections", "guide")])
            lines.append("| Produto | Nível | Operação | Centro | Descrição |")
            lines.append("|---|---:|---|---|---|")

            for row in guide_items[:16]:
                if not isinstance(row, dict):
                    continue

                operations = (
                    row.get("operations") if isinstance(row.get("operations"), list) else []
                )

                if not operations:
                    lines.append(
                        "| {product} | {level} | — | — | — |".format(
                            product=row.get("product_code") or cls._evidence("dash"),
                            level=row.get("bom_level") if row.get("bom_level") is not None else cls._evidence("dash"),
                        )
                    )
                    continue

                for operation in operations[:3]:
                    if not isinstance(operation, dict):
                        continue

                    lines.append(
                        "| {product} | {level} | {op} | {center} | {description} |".format(
                            product=row.get("product_code") or cls._evidence("dash"),
                            level=row.get("bom_level") if row.get("bom_level") is not None else cls._evidence("dash"),
                            op=operation.get("operation_code") or cls._evidence("dash"),
                            center=operation.get("work_center") or cls._evidence("dash"),
                            description=str(operation.get("operation_description") or cls._evidence("dash"))[:40],
                        )
                    )

        inspection = root.get("inspection") if isinstance(root.get("inspection"), dict) else {}
        inspection_items = (
            inspection.get("items") if isinstance(inspection.get("items"), list) else []
        )

        if inspection_items:
            lines.extend(["", cls._content("report", "sections", "inspection")])
            lines.append("| Produto | Nível | QP6 | QP7 | QP8 |")
            lines.append("|---|---:|---:|---:|---:|")

            for row in inspection_items[:12]:
                if not isinstance(row, dict):
                    continue

                qp6 = row.get("QP6") if isinstance(row.get("QP6"), list) else []
                qp7 = row.get("QP7") if isinstance(row.get("QP7"), list) else []
                qp8 = row.get("QP8") if isinstance(row.get("QP8"), list) else []

                lines.append(
                    "| {product} | {level} | {qp6} | {qp7} | {qp8} |".format(
                        product=row.get("product") or row.get("product_code") or cls._evidence("dash"),
                        level=row.get("level") if row.get("level") is not None else cls._evidence("dash"),
                        qp6=len(qp6) if qp6 else cls._evidence("dash"),
                        qp7=len(qp7) if qp7 else cls._evidence("dash"),
                        qp8=len(qp8) if qp8 else cls._evidence("dash"),
                    )
                )

        return lines

    @classmethod
    def _package(
        cls,
        *,
        product_code: str,
        items: list[dict[str, Any]],
        has_pdf_attachment: bool,
        product: dict,
        pdf_extract: dict[str, Any] | None = None,
        analyser_root: dict | None = None,
    ) -> dict[str, Any]:
        critical = sum(1 for i in items if i.get("status") == cls._STATUS_CRITICAL)
        errors = sum(1 for i in items if i.get("status") == cls._STATUS_ERROR)
        pending = sum(1 for i in items if i.get("status") == cls._STATUS_PENDING)

        pdf_meta = pdf_extract if isinstance(pdf_extract, dict) else {}

        if critical:
            overall = "rejected"
            overall_label = cls._content("overallLabels", "rejected")
            conclusion = cls._content("conclusions", "rejected")
        elif has_pdf_attachment and pdf_meta and not pdf_meta.get("legible"):
            overall = "incomplete"
            overall_label = cls._content("overallLabels", "incomplete")
            conclusion = cls._content("conclusions", "illegiblePdf")
        elif pending and not has_pdf_attachment:
            overall = "incomplete"
            overall_label = cls._content("overallLabels", "incomplete")
            conclusion = cls._content("conclusions", "noPdf")
        elif errors or pending:
            overall = "approved_with_notes"
            overall_label = cls._content("overallLabels", "approvedWithNotes")
            conclusion = cls._content("conclusions", "pendingWithPdf")
        else:
            overall = "approved"
            overall_label = cls._content("overallLabels", "approved")
            conclusion = cls._content("conclusions", "approved")

        return {
            "drawingAnalysis": {
                "status": overall,
                "overallLabel": overall_label,
                "productCode": product_code,
                "revisionPdf": pdf_meta.get("revision"),
                "revisionApi": product.get("last_revision_date"),
                "pdfProductCode": pdf_meta.get("productCode"),
                "hasPdfAttachment": has_pdf_attachment,
                "pdfLegible": pdf_meta.get("legible"),
                "criticalErrors": critical,
                "errors": errors,
                "warnings": pending,
                "items": items,
                "conclusion": conclusion,
            },
            "productSummary": {
                "code": product.get("code"),
                "description": product.get("description"),
                "last_revision_date": product.get("last_revision_date"),
            },
            "analyserRoot": analyser_root if isinstance(analyser_root, dict) else {},
        }

    @classmethod
    def _status_label(cls, status: str) -> str:
        return ChatDrawingValidationPresentationService.status_display(status)

    @classmethod
    def _status_symbol(cls, status: str) -> str:
        return ChatDrawingValidationPresentationService.status_symbol(status)
