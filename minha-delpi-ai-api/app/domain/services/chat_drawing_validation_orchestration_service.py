"""Merge payload `/analyser` com contexto de análise de desenho — Onda 12 MVP."""

from __future__ import annotations

from typing import Any


class ChatDrawingValidationOrchestrationService:
    """Gera relatório estruturado e metadata `drawingAnalysis` a partir da API."""

    _STATUS_OK = "ok"
    _STATUS_PENDING = "pending"
    _STATUS_ERROR = "error"
    _STATUS_CRITICAL = "critical_error"
    _STATUS_NA = "not_applicable"

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
                cls._item(
                    section="API DELPI",
                    item="Cadastro do produto",
                    status=cls._STATUS_CRITICAL,
                    pdf_evidence="—",
                    api_evidence="Não encontrado",
                    rule="Produto deve existir em SB1010",
                    recommendation="Verificar código ou cadastro no Protheus",
                )
            )
            return cls._package(
                product_code=code,
                items=items,
                has_pdf_attachment=has_pdf_attachment,
                product=product,
                pdf_extract=pdf_extract,
            )

        items.append(
            cls._item(
                section="API DELPI",
                item="Cadastro do produto",
                status=cls._STATUS_OK,
                pdf_evidence="—",
                api_evidence=str(product.get("code") or code),
                rule="Produto localizado na API",
                recommendation="—",
            )
        )

        revision = str(product.get("last_revision_date") or product.get("revision") or "").strip()
        items.append(
            cls._item(
                section="Cabeçalho",
                item="Revisão (API)",
                status=cls._STATUS_OK if revision else cls._STATUS_PENDING,
                pdf_evidence="Pendente leitura do PDF" if not has_pdf_attachment else "—",
                api_evidence=revision or "—",
                rule="Revisão deve bater com carimbo do PDF",
                recommendation="Conferir REV. no carimbo" if has_pdf_attachment else "Anexe o PDF",
            )
        )

        guide = root.get("guide") if isinstance(root.get("guide"), dict) else {}
        guide_items = guide.get("items") if isinstance(guide.get("items"), list) else []
        has_guide = bool(guide_items)

        items.append(
            cls._item(
                section="Roteiro",
                item="Roteiro de produção (SG2010)",
                status=cls._STATUS_OK if has_guide else cls._STATUS_CRITICAL,
                pdf_evidence="—",
                api_evidence=f"{len(guide_items)} operação(ões)" if has_guide else "Ausente",
                rule="Roteiro obrigatório para liberação",
                recommendation="Cadastrar roteiro" if not has_guide else "—",
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
            cls._item(
                section="Inspeção",
                item="QP6 / QP7 / QP8",
                status=cls._STATUS_OK if has_qp else cls._STATUS_CRITICAL,
                pdf_evidence="—",
                api_evidence="Vinculado" if has_qp else "Ausente",
                rule="Inspeção obrigatória quando aplicável",
                recommendation="Cadastrar plano de inspeção" if not has_qp else "—",
            )
        )

        if not has_pdf_attachment:
            items.append(
                cls._item(
                    section="PDF",
                    item="Documento anexado",
                    status=cls._STATUS_PENDING,
                    pdf_evidence="Sem anexo",
                    api_evidence="—",
                    rule="PDF necessário para BOM, cotas e carimbo",
                    recommendation="Anexe o PDF do desenho",
                )
            )
            items.append(
                cls._item(
                    section="BOM",
                    item="Tabela de materiais (PDF × SG1010)",
                    status=cls._STATUS_PENDING,
                    pdf_evidence="—",
                    api_evidence=f"{guide.get('total', len(guide_items))} item(ns) na estrutura",
                    rule="Comparar PDF com SG1010",
                    recommendation="Anexe o PDF para conferência completa",
                )
            )
        else:
            pdf_meta = pdf_extract if isinstance(pdf_extract, dict) else {}
            legible = bool(pdf_meta.get("legible"))

            items.append(
                cls._item(
                    section="PDF",
                    item="Documento anexado",
                    status=cls._STATUS_OK if legible else cls._STATUS_PENDING,
                    pdf_evidence="PDF na sessão" if legible else "Texto insuficiente/ilegível",
                    api_evidence="—",
                    rule="Extrair carimho, BOM e cotas do anexo",
                    recommendation=(
                        "Conferir divergências item a item no relatório"
                        if legible
                        else "Regerar PDF com melhor qualidade ou informar código na mensagem"
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
        )

    @classmethod
    def format_report_markdown(cls, package: dict[str, Any]) -> str:
        analysis = package.get("drawingAnalysis") or {}
        product = package.get("productSummary") or {}
        lines = [
            "# Relatório de Análise de Desenho DELPI",
            "",
            "## 1. Status geral",
            str(analysis.get("overallLabel") or "—"),
            "",
            "## 2. Dados identificados no PDF",
            "| Campo | Valor |",
            "|---|---|",
            f"| Código | {analysis.get('productCode') or '—'} |",
            f"| Revisão (PDF) | {analysis.get('revisionPdf') or '—'} |",
            f"| PDF anexado | {'Sim' if analysis.get('hasPdfAttachment') else 'Não'} |",
            "",
            "## 3. Dados retornados pela API",
            "| Campo | Valor |",
            "|---|---|",
            f"| Código | {product.get('code') or '—'} |",
            f"| Descrição | {product.get('description') or '—'} |",
            f"| Revisão (API) | {product.get('last_revision_date') or '—'} |",
            "",
            "## 4. Divergências críticas",
            "| Seção | Item | Status | PDF | API | Ação |",
            "|---|---|---|---|---|---|",
        ]

        critical = [
            item
            for item in (analysis.get("items") or [])
            if str(item.get("status") or "") == cls._STATUS_CRITICAL
        ]

        if not critical:
            lines.append("| — | Nenhuma divergência crítica automática | OK | — | — | — |")
        else:
            for item in critical:
                lines.append(
                    "| {section} | {item} | Erro crítico | {pdf} | {api} | {rec} |".format(
                        section=item.get("section") or "—",
                        item=item.get("item") or "—",
                        pdf=item.get("pdfEvidence") or "—",
                        api=item.get("apiEvidence") or "—",
                        rec=item.get("recommendation") or "—",
                    )
                )

        lines.extend(
            [
                "",
                "## 5. Checklist completo",
                "| Seção | Item | Status | Observação |",
                "|---|---|---|---|",
            ]
        )

        for item in analysis.get("items") or []:
            lines.append(
                "| {section} | {item} | {status} | {rec} |".format(
                    section=item.get("section") or "—",
                    item=item.get("item") or "—",
                    status=cls._status_label(str(item.get("status") or "")),
                    rec=item.get("recommendation") or "—",
                )
            )

        lines.extend(
            [
                "",
                "## 6. Conclusão",
                str(analysis.get("conclusion") or "—"),
            ]
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
                cls._item(
                    section="Cabeçalho",
                    item="Código DELPI",
                    status=cls._STATUS_CRITICAL,
                    pdf_evidence=pdf_code,
                    api_evidence=api_product_code,
                    rule="Código do PDF deve bater com SB1010",
                    recommendation="Corrigir código no desenho ou no cadastro",
                )
            )
        elif pdf_code and api_product_code:
            items.append(
                cls._item(
                    section="Cabeçalho",
                    item="Código DELPI",
                    status=cls._STATUS_OK,
                    pdf_evidence=pdf_code,
                    api_evidence=api_product_code,
                    rule="Código PDF × API",
                    recommendation="—",
                )
            )

        pdf_revision = str(pdf_extract.get("revision") or "").strip()
        api_revision = str(
            product.get("last_revision_date") or product.get("revision") or ""
        ).strip()

        if pdf_revision and api_revision:
            api_short = api_revision[-2:] if len(api_revision) >= 8 else api_revision

            if len(api_revision) <= 4 and pdf_revision != api_short.zfill(2):
                items.append(
                    cls._item(
                        section="Cabeçalho",
                        item="Revisão",
                        status=cls._STATUS_CRITICAL,
                        pdf_evidence=f"REV.{pdf_revision}",
                        api_evidence=api_revision,
                        rule="Revisão do carimbo × cadastro",
                        recommendation="Atualizar revisão do PDF ou cadastro Protheus",
                    )
                )
            elif len(api_revision) > 4:
                items.append(
                    cls._item(
                        section="Cabeçalho",
                        item="Revisão",
                        status=cls._STATUS_PENDING,
                        pdf_evidence=f"REV.{pdf_revision}",
                        api_evidence=api_revision,
                        rule="Conferência manual (API em data, PDF em REV.)",
                        recommendation="Validar revisão no carimbo com SB1010",
                    )
                )

        return items

    @classmethod
    def _package(
        cls,
        *,
        product_code: str,
        items: list[dict[str, Any]],
        has_pdf_attachment: bool,
        product: dict,
        pdf_extract: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        critical = sum(1 for i in items if i.get("status") == cls._STATUS_CRITICAL)
        errors = sum(1 for i in items if i.get("status") == cls._STATUS_ERROR)
        pending = sum(1 for i in items if i.get("status") == cls._STATUS_PENDING)

        pdf_meta = pdf_extract if isinstance(pdf_extract, dict) else {}

        if critical:
            overall = "rejected"
            overall_label = "Reprovado"
            conclusion = "O desenho não pode ser liberado enquanto houver erro crítico."
        elif has_pdf_attachment and pdf_meta and not pdf_meta.get("legible"):
            overall = "incomplete"
            overall_label = "Análise incompleta"
            conclusion = (
                "O PDF está ilegível ou sem texto extraível suficiente. "
                "Informe o código na mensagem ou regenere o PDF."
            )
        elif pending and not has_pdf_attachment:
            overall = "incomplete"
            overall_label = "Análise incompleta"
            conclusion = (
                "Anexe o PDF para validar carimho, BOM e cotas. "
                "A API já foi consultada para cadastro, roteiro e inspeção."
            )
        elif errors or pending:
            overall = "approved_with_notes"
            overall_label = "Aprovado com ressalvas"
            conclusion = "Revise os itens pendentes ou com erro antes da liberação."
        else:
            overall = "approved"
            overall_label = "Aprovado"
            conclusion = "Nenhuma divergência crítica detectada na validação automática da API."

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
        }

    @classmethod
    def _status_label(cls, status: str) -> str:
        symbol = cls._status_symbol(status)
        label = {
            cls._STATUS_OK: "OK",
            cls._STATUS_PENDING: "Pendente",
            cls._STATUS_ERROR: "Erro",
            cls._STATUS_CRITICAL: "Erro crítico",
            cls._STATUS_NA: "Não aplicável",
        }.get(status, status)

        return f"{symbol} {label}"

    @classmethod
    def _status_symbol(cls, status: str) -> str:
        return {
            cls._STATUS_OK: "✅",
            cls._STATUS_PENDING: "⚠️",
            cls._STATUS_ERROR: "❌",
            cls._STATUS_CRITICAL: "❌",
            cls._STATUS_NA: "—",
        }.get(status, "—")
