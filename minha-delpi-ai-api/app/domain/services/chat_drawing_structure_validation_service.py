"""Validação BOM, 50xx e cotas (PDF × estrutura API) — Onda 12.3+."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_drawing_bom_comparison_service import (
    ChatDrawingBomComparisonService,
)
from app.domain.services.chat_drawing_intermediate_semantics_service import (
    ChatDrawingIntermediateSemanticsService,
)
from app.domain.services.chat_drawing_tolerance_service import ChatDrawingToleranceService
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)


class ChatDrawingStructureValidationService:
    @classmethod
    def build_check_items(
        cls,
        *,
        root: dict,
        pdf_extract: dict,
        product_code: str,
    ) -> list[dict[str, Any]]:
        if not isinstance(pdf_extract, dict) or not pdf_extract.get("legible"):
            return []

        items: list[dict[str, Any]] = []
        comparison = ChatDrawingBomComparisonService.compare(
            root=root,
            pdf_extract=pdf_extract,
            product_code=product_code,
        )

        if comparison.missing_in_pdf:
            items.append(
                cls._item(
                    section="BOM",
                    item="Componente ausente no PDF",
                    status="critical_error",
                    pdf_evidence="—",
                    api_evidence=", ".join(comparison.missing_in_pdf[:5]),
                    rule="Todo item de 1º nível da SG1010 deve constar na BOM do desenho",
                    recommendation="Incluir componente na tabela de materiais",
                )
            )

        if comparison.extra_in_pdf:
            items.append(
                cls._item(
                    section="BOM",
                    item="Componente extra no PDF",
                    status="critical_error",
                    pdf_evidence=", ".join(comparison.extra_in_pdf[:5]),
                    api_evidence="—",
                    rule="Item do PDF deve existir na estrutura de 1º nível",
                    recommendation="Remover item extra ou atualizar estrutura Protheus",
                )
            )

        if comparison.api_codes and comparison.reconciled_pdf_codes and not (
            comparison.missing_in_pdf or comparison.extra_in_pdf
        ):
            items.append(
                cls._item(
                    section="BOM",
                    item="Conjunto de componentes",
                    status="ok",
                    pdf_evidence=f"{len(comparison.reconciled_pdf_codes)} código(s)",
                    api_evidence=f"{len(comparison.api_codes)} código(s)",
                    rule="PDF × SG1010 (1º nível)",
                    recommendation="—",
                )
            )

        items.extend(cls._intermediate_code_items(root, pdf_extract, product_code))
        items.extend(cls._intermediate_dimension_items(root, pdf_extract))
        items.extend(cls._dimension_items(root, pdf_extract))

        return items

    @classmethod
    def _intermediate_code_items(
        cls,
        root: dict,
        pdf_extract: dict,
        product_code: str,
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        pdf_intermediate = set(pdf_extract.get("intermediateCodes") or [])
        api_intermediate = cls._collect_api_intermediate_codes(root, product_code)

        malformed = [
            code
            for code in pdf_intermediate
            if code and not str(code).startswith("50")
        ]

        if malformed:
            items.append(
                cls._item(
                    section="Código 50xx",
                    item="Formato intermediário",
                    status="critical_error",
                    pdf_evidence=", ".join(malformed[:3]),
                    api_evidence="—",
                    rule="Família 50xx",
                    recommendation="Corrigir código intermediário no desenho",
                )
            )

        missing = sorted(api_intermediate - pdf_intermediate)

        if missing:
            items.append(
                cls._item(
                    section="Código 50xx",
                    item="Intermediário ausente no PDF",
                    status="error" if pdf_intermediate else "critical_error",
                    pdf_evidence="—",
                    api_evidence=", ".join(missing[:5]),
                    rule="Intermediários cadastrados na SG1010",
                    recommendation="Incluir códigos 50xx na BOM do desenho",
                )
            )

        extra_intermediate = sorted(
            code for code in (pdf_intermediate - api_intermediate) if code.startswith("50")
        )

        if extra_intermediate:
            items.append(
                cls._item(
                    section="Código 50xx",
                    item="Intermediário extra no PDF",
                    status="critical_error",
                    pdf_evidence=", ".join(extra_intermediate[:5]),
                    api_evidence="—",
                    rule="Intermediário do PDF deve existir na SG1010",
                    recommendation="Remover intermediário obsoleto ou atualizar estrutura",
                )
            )

        if pdf_intermediate and api_intermediate and not missing and not extra_intermediate:
            items.append(
                cls._item(
                    section="Código 50xx",
                    item="Intermediários",
                    status="ok",
                    pdf_evidence=", ".join(sorted(pdf_intermediate)[:5]),
                    api_evidence=", ".join(sorted(api_intermediate)[:5]),
                    rule="PDF × SG1010",
                    recommendation="—",
                )
            )

        return items

    @classmethod
    def _collect_api_intermediate_codes(cls, root: dict, product_code: str) -> set[str]:
        codes: set[str] = set()

        for code in ChatDrawingBomComparisonService.collect_structure_bom_codes(
            root,
            product_code,
        ):
            if str(code).startswith("50"):
                codes.add(code)

        return codes

    @classmethod
    def _intermediate_dimension_items(
        cls,
        root: dict,
        pdf_extract: dict,
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []

        for row in ChatDrawingIntermediateSemanticsService.collect_structure_intermediates(root):
            code = str(row.get("code") or "")
            length = row.get("lengthMm")
            cable_qty = row.get("cableQuantityMm")

            if length is None or cable_qty is None:
                continue

            within = ChatDrawingToleranceService.lengths_within_tolerance(length, cable_qty)

            if within is False:
                items.append(
                    cls._item(
                        section="Código 50xx",
                        item=f"Comprimento {code}",
                        status="critical_error",
                        pdf_evidence=f"{length} mm (descrição)",
                        api_evidence=f"{cable_qty} mm (SG1010)",
                        rule="Comprimento do intermediário × quantidade do cabo filho",
                        recommendation="Alinhar descrição 50xx com estrutura SG1010",
                    )
                )

        dimensions = pdf_extract.get("dimensions") if isinstance(
            pdf_extract.get("dimensions"), dict
        ) else {}
        pdf_decape = dimensions.get("leftDecapeMm")

        if pdf_decape is None:
            return items

        for row in ChatDrawingIntermediateSemanticsService.collect_structure_intermediates(root):
            left = row.get("leftDecapeMm")
            right = row.get("rightDecapeMm")
            code = str(row.get("code") or "")

            if left is None and right is None:
                continue

            for label, expected in (("esquerdo", left), ("direito", right)):
                if expected is None:
                    continue

                within = ChatDrawingToleranceService.decape_within_tolerance(
                    pdf_decape,
                    expected,
                )

                if within is False:
                    items.append(
                        cls._item(
                            section="Cotas",
                            item=f"Decape {label} × {code}",
                            status="error",
                            pdf_evidence=f"{pdf_decape} mm",
                            api_evidence=f"{expected} mm (código 50xx)",
                            rule="Decape ±1 mm (intermediário)",
                            recommendation="Conferir decape no desenho e na descrição 50xx",
                        )
                    )

        return items

    @classmethod
    def _dimension_items(cls, root: dict, pdf_extract: dict) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        dimensions = pdf_extract.get("dimensions") if isinstance(
            pdf_extract.get("dimensions"), dict
        ) else {}

        total_length = dimensions.get("totalLengthMm")
        left_decape = dimensions.get("leftDecapeMm")
        right_decape = dimensions.get("rightDecapeMm")
        segment_lengths = dimensions.get("segmentLengthsMm") or []

        if segment_lengths:
            api_lengths = [
                row.get("lengthMm")
                for row in ChatDrawingIntermediateSemanticsService.collect_structure_intermediates(
                    root
                )
                if row.get("lengthMm") is not None
            ]

            for segment in segment_lengths[:6]:
                if not api_lengths:
                    break

                matched = any(
                    ChatDrawingToleranceService.lengths_within_tolerance(segment, api_len)
                    is True
                    for api_len in api_lengths
                )

                if matched is False:
                    items.append(
                        cls._item(
                            section="Cotas",
                            item="Comprimento de trecho",
                            status="pending",
                            pdf_evidence=f"{segment} mm",
                            api_evidence=", ".join(str(v) for v in api_lengths[:4]),
                            rule="Cota de trecho × comprimento 50xx (±5%)",
                            recommendation="Conferir cotas do desenho com intermediários",
                        )
                    )

        api_quantity = cls._root_structure_quantity(root)

        if total_length is not None and api_quantity is not None:
            within = ChatDrawingToleranceService.lengths_within_tolerance(
                total_length,
                api_quantity,
            )

            if within is True:
                status = "ok"
                recommendation = "—"
            elif within is False:
                status = "critical_error"
                recommendation = "Corrigir cota principal ou quantidade na estrutura"
            else:
                status = "pending"
                recommendation = "Conferir unidade e cota manualmente"

            items.append(
                cls._item(
                    section="Cotas",
                    item="Comprimento total",
                    status=status,
                    pdf_evidence=f"{total_length} mm",
                    api_evidence=f"{api_quantity}",
                    rule="Tolerância ±5% (validation_rules)",
                    recommendation=recommendation,
                )
            )

        if left_decape is not None or right_decape is not None:
            decape_status = (
                "ok" if left_decape is not None and right_decape is not None else "pending"
            )
            items.append(
                cls._item(
                    section="Cotas",
                    item="Decapes E/D",
                    status=decape_status,
                    pdf_evidence=(
                        f"E={left_decape or '—'} mm; D={right_decape or '—'} mm"
                    ),
                    api_evidence="Conferir intermediário 50xx",
                    rule="Decape ±1 mm quando referência disponível",
                    recommendation=(
                        "—"
                        if decape_status == "ok"
                        else "Informar decapes no PDF ou validar código 50xx"
                    ),
                )
            )

        return items

    @classmethod
    def _root_structure_quantity(cls, root: dict) -> float | None:
        structure = root.get("structure") if isinstance(root.get("structure"), dict) else {}
        items = structure.get("items") or []

        if len(items) != 1:
            return None

        item = items[0]

        if not isinstance(item, dict):
            return None

        quantity = item.get("quantity")

        if quantity is None:
            return None

        try:
            value = float(quantity)
        except (TypeError, ValueError):
            return None

        if value <= 0 or value > 1000:
            return None

        return value

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
