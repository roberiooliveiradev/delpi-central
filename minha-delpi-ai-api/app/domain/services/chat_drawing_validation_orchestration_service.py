"""Merge payload `/analyser` com contexto de análise de desenho — Onda 12 MVP."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_drawing_inspection_validation_service import (
    ChatDrawingInspectionValidationService,
)
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
        pdf_extract = cls._apply_bom_vision_refinement(
            pdf_extract,
            product_code=code,
            analyser_root=root,
        )

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
            items, extraction_confidence = cls._apply_validation_layers(
                items,
                pdf_extract=pdf_extract,
            )
            return cls._package(
                product_code=code,
                items=items,
                has_pdf_attachment=has_pdf_attachment,
                product=product,
                pdf_extract=pdf_extract,
                analyser_root=root,
                extraction_confidence=extraction_confidence,
            )

        items.append(
            cls._item_from_template(
                "product_found",
                status=cls._STATUS_OK,
                pdf_evidence=cls._evidence("dash"),
                api_evidence=str(product.get("code") or code),
            )
        )

        delpi_revision = str(
            product.get("current_revision")
            or product.get("last_revision_date")
            or product.get("revision")
            or ""
        ).strip()
        items.append(
            cls._item_from_template(
                "revision_api",
                status=cls._STATUS_OK if delpi_revision else cls._STATUS_PENDING,
                pdf_evidence=(
                    cls._evidence("pendingPdf")
                    if not has_pdf_attachment
                    else cls._evidence("dash")
                ),
                api_evidence=delpi_revision or cls._evidence("dash"),
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

        if has_guide:
            from app.domain.services.chat_drawing_guide_structure_consistency_service import (
                ChatDrawingGuideStructureConsistencyService,
            )
            from app.domain.services.chat_drawing_validation_rule_registry_service import (
                ChatDrawingValidationRuleRegistryService,
            )

            product = root.get("product") if isinstance(root.get("product"), dict) else {}
            group_code = str(product.get("group_code") or "").strip() or None

            if ChatDrawingValidationRuleRegistryService.is_enabled(
                "guide_structure",
                code,
                group_code=group_code,
            ):
                items.extend(
                    ChatDrawingGuideStructureConsistencyService.build_check_items(
                        root=root,
                        product_code=code,
                    )
                )

            from app.domain.services.chat_drawing_guide_component_consistency_service import (
                ChatDrawingGuideComponentConsistencyService,
            )

            if ChatDrawingValidationRuleRegistryService.is_enabled(
                "guide_component",
                code,
                group_code=group_code,
            ):
                items.extend(
                    ChatDrawingGuideComponentConsistencyService.build_check_items(
                        root=root,
                        product_code=code,
                    )
                )

        inspection = root.get("inspection") if isinstance(root.get("inspection"), dict) else {}
        has_qp = ChatDrawingInspectionValidationService.has_inspection_plan(inspection)

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

            items.extend(cls._pdf_cross_check_items(
                product,
                code,
                pdf_meta,
                structure=root.get("structure") if isinstance(root.get("structure"), dict) else {},
            ))

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

        from app.domain.services.chat_drawing_validation_rule_registry_service import (
            ChatDrawingValidationRuleRegistryService,
        )

        product = root.get("product") if isinstance(root.get("product"), dict) else {}
        group_code = str(product.get("group_code") or "").strip() or None
        items = ChatDrawingValidationRuleRegistryService.filter_items(
            items,
            code,
            group_code=group_code,
        )

        items, extraction_confidence = cls._apply_validation_layers(
            items,
            pdf_extract=pdf_extract,
        )
        return cls._package(
            product_code=code,
            items=items,
            has_pdf_attachment=has_pdf_attachment,
            product=product,
            pdf_extract=pdf_extract,
            analyser_root=root,
            extraction_confidence=extraction_confidence,
        )

    @classmethod
    def _apply_bom_vision_refinement(
        cls,
        pdf_extract: dict[str, Any] | None,
        *,
        product_code: str,
        analyser_root: dict[str, Any],
    ) -> dict[str, Any] | None:
        if not isinstance(pdf_extract, dict) or not pdf_extract:
            return pdf_extract

        from app.domain.services.chat_drawing_bom_vision_refinement_service import (
            ChatDrawingBomVisionRefinementService,
        )

        source_meta = pdf_extract.get("sourceMetadata")

        if not isinstance(source_meta, dict):
            source_meta = {}

        storage_path = str(source_meta.get("storagePath") or "").strip()

        return ChatDrawingBomVisionRefinementService.refine_if_needed(
            pdf_extract,
            storage_path=storage_path,
            analyser_root=analyser_root,
            product_code=product_code,
        )

    @classmethod
    def _apply_validation_layers(
        cls,
        items: list[dict[str, Any]],
        *,
        pdf_extract: dict[str, Any] | None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
        from app.domain.services.chat_drawing_validation_assertion_service import (
            ChatDrawingValidationAssertionService,
        )

        adjusted, confidence = ChatDrawingValidationAssertionService.apply(
            items=items,
            pdf_extract=pdf_extract,
        )

        return adjusted, confidence.to_metadata() if confidence else None

    @classmethod
    def format_report_markdown(cls, package: dict[str, Any]) -> str:
        analysis = package.get("drawingAnalysis") or {}
        product = package.get("productSummary") or {}
        raw_items = analysis.get("items") or []
        display_items = ChatDrawingValidationPresentationService.prepare_display_items(
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

        pdf_code = ChatDrawingValidationPresentationService.resolve_pdf_product_code(
            pdf_product_code=analysis.get("pdfProductCode"),
            resolved_product_code=product.get("code") or analysis.get("productCode"),
        )

        lines = [
            cls._content("report", "title"),
            "",
            cls._content("report", "sections", "overall"),
            str(analysis.get("overallLabel") or cls._evidence("dash")),
        ]

        executive_summary = (
            ChatDrawingValidationPresentationService.build_executive_summary(
                analysis,
                product if isinstance(product, dict) else {},
            )
        )

        if executive_summary:
            lines.extend(["", executive_summary])

        lines.extend(
            [
                "",
                cls._content("report", "sections", "pdfData"),
                table_header,
                table_separator,
                f"| {pdf_fields.get('code', 'Código')} | {ChatDrawingValidationPresentationService.format_code(pdf_code) if pdf_code else cls._evidence('dash')} |",
                f"| {pdf_fields.get('customerReference', 'Referência do cliente (PDF)')} | {analysis.get('customerReferencePdf') or cls._evidence('dash')} |",
                f"| {pdf_fields.get('revision', 'Revisão do cliente (PDF)')} | {analysis.get('revisionPdf') or cls._evidence('dash')} |",
                f"| {pdf_fields.get('attached', 'PDF anexado')} | {pdf_fields.get('attachedYes', 'Sim') if analysis.get('hasPdfAttachment') else pdf_fields.get('attachedNo', 'Não')} |",
                "",
                cls._content("report", "sections", "apiData"),
                table_header,
                table_separator,
                f"| {api_fields.get('code', 'Código')} | {ChatDrawingValidationPresentationService.format_code(product.get('code') or analysis.get('productCode') or cls._evidence('dash'))} |",
                f"| {api_fields.get('description', 'Descrição')} | {product.get('description') or cls._evidence('dash')} |",
                f"| {api_fields.get('customerReference', 'Referência do cliente (B1_REFEREN)')} | {product.get('customer_reference') or analysis.get('customerReferenceApi') or cls._evidence('dash')} |",
                f"| {api_fields.get('revision', 'Revisão Delpi (cadastro)')} | {product.get('current_revision') or product.get('last_revision_date') or cls._evidence('dash')} |",
            ]
        )

        lines.extend(
            ChatDrawingValidationPresentationService.format_analyser_detail_sections(
                package.get("analyserRoot")
            )
        )

        lines.extend(
            ChatDrawingValidationPresentationService.format_dimensions_comparison_section(
                package
            )
        )

        lines.extend(
            [
                "",
                cls._content("report", "sections", "critical"),
                "| Seção | Item | Status | PDF | API | Ação |",
                "|---|---|---|---|---|---|",
            ]
        )

        divergences = ChatDrawingValidationPresentationService.divergence_items(
            display_items
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
                        pdf=ChatDrawingValidationPresentationService.format_evidence_cell(
                            item.get("pdfEvidence") or cls._evidence("dash")
                        ),
                        api=ChatDrawingValidationPresentationService.format_evidence_cell(
                            item.get("apiEvidence") or cls._evidence("dash")
                        ),
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
                        pdf=ChatDrawingValidationPresentationService.format_evidence_cell(
                            item.get("pdfEvidence") or cls._evidence("dash")
                        ),
                        api=ChatDrawingValidationPresentationService.format_evidence_cell(
                            item.get("apiEvidence") or cls._evidence("dash")
                        ),
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
        return cls.format_report_markdown(package).strip()

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
        *,
        structure: dict | None = None,
    ) -> list[dict[str, Any]]:
        from app.domain.services.chat_drawing_validation_rule_registry_service import (
            ChatDrawingValidationRuleRegistryService,
        )

        items: list[dict[str, Any]] = []
        group_code = str(product.get("group_code") or "").strip() or None
        pdf_code = str(pdf_extract.get("productCode") or "").strip()
        api_product_code = str(product.get("code") or api_code or "").strip()

        if ChatDrawingValidationRuleRegistryService.is_enabled(
            "product_code_cross_check",
            api_code,
            group_code=group_code,
        ):
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

        if ChatDrawingValidationRuleRegistryService.is_enabled(
            "customer_reference_cross_check",
            api_code,
            group_code=group_code,
        ):
            from app.domain.services.chat_drawing_customer_reference_cross_check_service import (
                ChatDrawingCustomerReferenceCrossCheckService,
            )

            customer_ref_item = ChatDrawingCustomerReferenceCrossCheckService.build_check_item(
                pdf_reference=ChatDrawingCustomerReferenceCrossCheckService.resolve_pdf_reference(
                    pdf_extract
                ),
                api_reference=ChatDrawingCustomerReferenceCrossCheckService.resolve_api_reference(
                    product
                ),
            )

            if customer_ref_item:
                items.append(customer_ref_item)

        if ChatDrawingValidationRuleRegistryService.is_enabled(
            "revision_cross_check",
            api_code,
            group_code=group_code,
        ):
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
                pdf_extract=pdf_extract,
            )

            if revision_item:
                items.append(revision_item)

        from app.domain.services.chat_drawing_structure_validity_notice_service import (
            ChatDrawingStructureValidityNoticeService,
        )

        if ChatDrawingValidationRuleRegistryService.is_enabled(
            "structure_bom_validity",
            api_code,
            group_code=group_code,
        ):
            items.extend(
                ChatDrawingStructureValidityNoticeService.build_check_items(
                    product=product,
                    pdf_extract=pdf_extract,
                    structure=structure if isinstance(structure, dict) else {},
                )
            )

        return items

    @classmethod
    def _build_revision_cross_check_item(
        cls,
        *,
        pdf_revision: str,
        pdf_internal_revision: str,
        api_current_revision: str,
        api_revision_date: str,
        pdf_extract: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Exibe revisões sem cruzar PDF × B1_REVATU.

        A REV. no desenho é sempre a do **cliente**. A revisão Delpi
        (``current_revision`` / B1_REVATU) existe só no TOTVS — não aparece
        no PDF. Divergência entre elas **nunca** é crítico nem pendente.
        """
        del pdf_internal_revision, pdf_extract  # OCR de “interna” no carimbo ≠ B1_REVATU

        api_evidence = str(api_current_revision or api_revision_date or "").strip()
        client_revision = cls._normalize_revision_number(pdf_revision)
        content = ChatDrawingValidationContentService

        if not client_revision and not api_evidence:
            return None

        if client_revision and api_evidence:
            return cls._item_from_template(
                "revision_client_not_comparable",
                status=cls._STATUS_OK,
                pdf_evidence=content.evidence_format(
                    "revisionClientOnly",
                    revision=pdf_revision or client_revision,
                ),
                api_evidence=api_evidence,
            )

        if client_revision:
            return cls._item_from_template(
                "revision_client_not_comparable",
                status=cls._STATUS_OK,
                pdf_evidence=content.evidence_format(
                    "revisionClientOnly",
                    revision=pdf_revision or client_revision,
                ),
                api_evidence=content.evidence("dash"),
            )

        return None

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
    def _package(
        cls,
        *,
        product_code: str,
        items: list[dict[str, Any]],
        has_pdf_attachment: bool,
        product: dict,
        pdf_extract: dict[str, Any] | None = None,
        analyser_root: dict | None = None,
        extraction_confidence: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        critical = sum(1 for i in items if i.get("status") == cls._STATUS_CRITICAL)
        errors = sum(1 for i in items if i.get("status") == cls._STATUS_ERROR)
        pending = sum(1 for i in items if i.get("status") == cls._STATUS_PENDING)

        pdf_meta = pdf_extract if isinstance(pdf_extract, dict) else {}
        validation_scopes = pdf_meta.get("validationScopes")

        if not isinstance(validation_scopes, dict):
            validation_scopes = {}

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
            conclusion = ChatDrawingValidationPresentationService.build_analysis_conclusion(
                items,
                has_pdf=has_pdf_attachment,
            )
        else:
            overall = "approved"
            overall_label = cls._content("overallLabels", "approved")
            conclusion = cls._content("conclusions", "approved")

        from app.domain.services.chat_drawing_multipage_coverage_service import (
            ChatDrawingMultipageCoverageService,
        )

        multipage_coverage = ChatDrawingMultipageCoverageService.resolve_metadata_from_items(
            items
        )

        return {
            "drawingAnalysis": {
                "status": overall,
                "overallLabel": overall_label,
                "productCode": product_code,
                "revisionPdf": pdf_meta.get("revision"),
                "revisionPdfInternal": pdf_meta.get("internalRevision"),
                "customerReferencePdf": pdf_meta.get("customerReference"),
                "customerReferenceApi": product.get("customer_reference"),
                "revisionApi": product.get("current_revision")
                or product.get("last_revision_date"),
                "pdfProductCode": pdf_meta.get("productCode") or product_code,
                "hasPdfAttachment": has_pdf_attachment,
                "pdfLegible": pdf_meta.get("legible"),
                "criticalErrors": critical,
                "errors": errors,
                "warnings": pending,
                "items": items,
                "conclusion": conclusion,
                "validationScopes": validation_scopes,
                **(
                    {"multipageCoverage": multipage_coverage}
                    if multipage_coverage
                    else {}
                ),
                **(
                    {"validationLayers": {"extractionConfidence": extraction_confidence}}
                    if extraction_confidence
                    else {}
                ),
                **(
                    {"visionRefinement": cls._vision_refinement_metadata(pdf_meta)}
                    if cls._vision_refinement_metadata(pdf_meta)
                    else {}
                ),
            },
            "productSummary": {
                "code": product.get("code"),
                "description": product.get("description"),
                "last_revision_date": product.get("last_revision_date"),
            },
            "analyserRoot": analyser_root if isinstance(analyser_root, dict) else {},
        }

    @classmethod
    def reconcile_analysis_summary(cls, analysis: dict[str, Any]) -> dict[str, Any]:
        items = analysis.get("items") if isinstance(analysis.get("items"), list) else []
        has_pdf_attachment = bool(analysis.get("hasPdfAttachment"))
        pdf_legible = analysis.get("pdfLegible")

        critical = sum(1 for item in items if item.get("status") == cls._STATUS_CRITICAL)
        errors = sum(1 for item in items if item.get("status") == cls._STATUS_ERROR)
        pending = sum(1 for item in items if item.get("status") == cls._STATUS_PENDING)

        if critical:
            overall = "rejected"
            overall_label = cls._content("overallLabels", "rejected")
            conclusion = cls._content("conclusions", "rejected")
        elif has_pdf_attachment and pdf_legible is False:
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
            conclusion = ChatDrawingValidationPresentationService.build_analysis_conclusion(
                items,
                has_pdf=has_pdf_attachment,
            )
        else:
            overall = "approved"
            overall_label = cls._content("overallLabels", "approved")
            conclusion = cls._content("conclusions", "approved")

        merged = dict(analysis)
        merged.update(
            {
                "status": overall,
                "overallLabel": overall_label,
                "criticalErrors": critical,
                "errors": errors,
                "warnings": pending,
                "conclusion": conclusion,
            }
        )
        return merged

    @classmethod
    def repackage_with_overrides(
        cls,
        analysis: dict[str, Any],
        overrides: list[dict[str, Any]],
        *,
        base_package: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        from app.domain.services.chat_drawing_report_adjustment_service import (
            ChatDrawingReportAdjustmentService,
        )
        from app.domain.services.chat_drawing_validation_package_service import (
            ChatDrawingValidationPackageService,
        )

        updated = ChatDrawingReportAdjustmentService.apply_overrides(analysis, overrides)

        if isinstance(base_package, dict) and base_package.get("drawingAnalysis"):
            return ChatDrawingValidationPackageService.merge_with_analysis(
                base_package,
                updated,
            )

        return {"drawingAnalysis": updated}

    @classmethod
    def _vision_refinement_metadata(cls, pdf_meta: dict[str, Any]) -> dict[str, Any] | None:
        refinement = pdf_meta.get("bomVisionRefinement")

        if not isinstance(refinement, dict) or not refinement:
            return None

        attempts = refinement.get("attempts") if isinstance(refinement.get("attempts"), list) else []
        codes_refined = (
            refinement.get("codesRefined")
            if isinstance(refinement.get("codesRefined"), list)
            else []
        )

        return {
            "attempted": bool(refinement.get("triggered")),
            "resolved": len(codes_refined),
            "tableCount": refinement.get("tableCount"),
            "columnRowCount": refinement.get("columnRowCount"),
            "attemptCount": int(refinement.get("attemptCount") or len(attempts)),
            "codesRefined": codes_refined,
            "stoppedReason": refinement.get("stoppedReason"),
        }

    @classmethod
    def _status_label(cls, status: str) -> str:
        return ChatDrawingValidationPresentationService.status_display(status)

    @classmethod
    def _status_symbol(cls, status: str) -> str:
        return ChatDrawingValidationPresentationService.status_symbol(status)
