"""Validação BOM, 50xx e cotas (PDF × estrutura API) — Onda 12.3."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_drawing_tolerance_service import ChatDrawingToleranceService
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)

_INTERMEDIATE_CODE_RE = re.compile(r"\b(50\d{6})\b")


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
        api_codes = cls._collect_api_component_codes(root, product_code)
        pdf_codes = set(pdf_extract.get("componentCodes") or [])

        missing_in_pdf = sorted(api_codes - pdf_codes)
        extra_in_pdf = sorted(
            code for code in (pdf_codes - api_codes) if code != product_code
        )

        if missing_in_pdf:
            items.append(
                cls._item(
                    section="BOM",
                    item="Componente ausente no PDF",
                    status="critical_error",
                    pdf_evidence="—",
                    api_evidence=", ".join(missing_in_pdf[:5]),
                    rule="Todo componente SG1010 deve aparecer no desenho",
                    recommendation="Incluir componente na tabela de materiais",
                )
            )

        if extra_in_pdf:
            items.append(
                cls._item(
                    section="BOM",
                    item="Componente extra no PDF",
                    status="critical_error",
                    pdf_evidence=", ".join(extra_in_pdf[:5]),
                    api_evidence="—",
                    rule="Componente do PDF deve existir na estrutura",
                    recommendation="Remover item extra ou atualizar estrutura Protheus",
                )
            )

        if api_codes and pdf_codes and not missing_in_pdf and not extra_in_pdf:
            items.append(
                cls._item(
                    section="BOM",
                    item="Conjunto de componentes",
                    status="ok",
                    pdf_evidence=f"{len(pdf_codes)} código(s)",
                    api_evidence=f"{len(api_codes)} código(s)",
                    rule="PDF × SG1010",
                    recommendation="—",
                )
            )

        items.extend(cls._intermediate_code_items(root, pdf_extract, product_code))
        items.extend(cls._dimension_items(root, pdf_extract))

        return items

    @classmethod
    def _collect_api_component_codes(cls, root: dict, product_code: str) -> set[str]:
        codes: set[str] = set()
        root_code = ChatProductQueryIntentService.normalize_product_code(product_code)

        structure = root.get("structure") if isinstance(root.get("structure"), dict) else {}

        for item in structure.get("items") or []:
            if not isinstance(item, dict):
                continue

            code = ChatProductQueryIntentService.normalize_product_code(
                str(item.get("code") or "")
            )

            if code and code != root_code:
                codes.add(code)

        guide = root.get("guide") if isinstance(root.get("guide"), dict) else {}

        for item in guide.get("items") or []:
            if not isinstance(item, dict):
                continue

            code = ChatProductQueryIntentService.normalize_product_code(
                str(item.get("product_code") or "")
            )

            if code and code != root_code and int(item.get("bom_level") or 0) > 0:
                codes.add(code)

        return codes

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

        if missing and pdf_intermediate:
            items.append(
                cls._item(
                    section="Código 50xx",
                    item="Intermediário ausente no PDF",
                    status="error",
                    pdf_evidence="—",
                    api_evidence=", ".join(missing[:5]),
                    rule="Intermediários da estrutura",
                    recommendation="Conferir códigos 50xx no desenho",
                )
            )

        if pdf_intermediate and not missing:
            items.append(
                cls._item(
                    section="Código 50xx",
                    item="Intermediários",
                    status="ok",
                    pdf_evidence=", ".join(sorted(pdf_intermediate)[:5]),
                    api_evidence=", ".join(sorted(api_intermediate)[:5]) or "—",
                    rule="PDF × estrutura",
                    recommendation="—",
                )
            )

        return items

    @classmethod
    def _collect_api_intermediate_codes(cls, root: dict, product_code: str) -> set[str]:
        codes: set[str] = set()

        for code in cls._collect_api_component_codes(root, product_code):
            if str(code).startswith("50"):
                codes.add(code)

        return codes

    @classmethod
    def _dimension_items(cls, root: dict, pdf_extract: dict) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        dimensions = pdf_extract.get("dimensions") if isinstance(
            pdf_extract.get("dimensions"), dict
        ) else {}

        total_length = dimensions.get("totalLengthMm")
        left_decape = dimensions.get("leftDecapeMm")
        right_decape = dimensions.get("rightDecapeMm")

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
            decape_status = "ok" if left_decape is not None and right_decape is not None else "pending"
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

        if not items:
            return None

        quantities = [
            float(item.get("quantity"))
            for item in items
            if isinstance(item, dict) and item.get("quantity") is not None
        ]

        if not quantities:
            return None

        return max(quantities)

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
