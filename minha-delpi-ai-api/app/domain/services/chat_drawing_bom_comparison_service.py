"""Comparação hierárquica BOM PDF × SG1010 — ignora cabos-filho de 50xx e ruído de roteiro."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)


@dataclass(frozen=True)
class BomComparisonResult:
    missing_in_pdf: tuple[str, ...]
    extra_in_pdf: tuple[str, ...]
    reconciled_pdf_codes: tuple[str, ...]
    api_codes: tuple[str, ...]


class ChatDrawingBomComparisonService:
    @classmethod
    def compare(
        cls,
        *,
        root: dict,
        pdf_extract: dict,
        product_code: str,
    ) -> BomComparisonResult:
        api_codes = cls.collect_structure_bom_codes(root, product_code)
        known_codes = cls.collect_known_structure_codes(root, product_code)
        raw_pdf_codes = set(pdf_extract.get("componentCodes") or [])
        raw_pdf_codes.update(pdf_extract.get("intermediateCodes") or [])

        reconciled = cls.normalize_pdf_bom_codes(
            raw_pdf_codes,
            known_codes=known_codes,
            child_cable_parents=cls.collect_child_cable_parents(root),
        )

        missing = sorted(api_codes - reconciled)
        extra = sorted(
            code
            for code in (reconciled - api_codes)
            if code != ChatProductQueryIntentService.normalize_product_code(product_code)
        )

        return BomComparisonResult(
            missing_in_pdf=tuple(missing),
            extra_in_pdf=tuple(extra),
            reconciled_pdf_codes=tuple(sorted(reconciled)),
            api_codes=tuple(sorted(api_codes)),
        )

    @classmethod
    def collect_structure_bom_codes(cls, root: dict, product_code: str) -> set[str]:
        root_code = ChatProductQueryIntentService.normalize_product_code(product_code)
        codes: set[str] = set()
        structure = root.get("structure") if isinstance(root.get("structure"), dict) else {}

        for item in structure.get("items") or []:
            if not isinstance(item, dict):
                continue

            code = ChatProductQueryIntentService.normalize_product_code(
                str(item.get("code") or "")
            )

            if code and code != root_code:
                codes.add(code)

        return codes

    @classmethod
    def collect_known_structure_codes(cls, root: dict, product_code: str) -> set[str]:
        known = set(cls.collect_structure_bom_codes(root, product_code))
        structure = root.get("structure") if isinstance(root.get("structure"), dict) else {}

        for item in structure.get("items") or []:
            if not isinstance(item, dict):
                continue

            for child in item.get("components") or []:
                if not isinstance(child, dict):
                    continue

                code = ChatProductQueryIntentService.normalize_product_code(
                    str(child.get("code") or "")
                )

                if code:
                    known.add(code)

        return known

    @classmethod
    def collect_child_cable_parents(cls, root: dict) -> dict[str, set[str]]:
        mapping: dict[str, set[str]] = {}
        structure = root.get("structure") if isinstance(root.get("structure"), dict) else {}

        for item in structure.get("items") or []:
            if not isinstance(item, dict):
                continue

            parent = ChatProductQueryIntentService.normalize_product_code(
                str(item.get("code") or "")
            )

            if not parent:
                continue

            for child in item.get("components") or []:
                if not isinstance(child, dict):
                    continue

                child_code = ChatProductQueryIntentService.normalize_product_code(
                    str(child.get("code") or "")
                )

                if child_code:
                    mapping.setdefault(child_code, set()).add(parent)

        return mapping

    @classmethod
    def normalize_pdf_bom_codes(
        cls,
        pdf_codes: set[str],
        *,
        known_codes: set[str],
        child_cable_parents: dict[str, set[str]],
    ) -> set[str]:
        reconciled: set[str] = set()
        parents_50xx = {code for code in pdf_codes if str(code).startswith("50")}

        for raw_code in pdf_codes:
            code = cls.reconcile_pdf_code(raw_code, known_codes)

            if not code:
                continue

            parent = child_cable_parents.get(code) or set()

            if parent & parents_50xx:
                continue

            reconciled.add(code)

        return reconciled

    @classmethod
    def reconcile_pdf_code(cls, raw_code: str, known_codes: set[str]) -> str | None:
        code = ChatProductQueryIntentService.normalize_product_code(str(raw_code or ""))

        if not code:
            return None

        if code in known_codes:
            return code

        if re.fullmatch(r"40\d{6}", code):
            alt = f"10{code[2:]}"

            if alt in known_codes:
                return alt

        if len(code) == 7 and code.isdigit():
            prefix_matches = sorted(
                candidate
                for candidate in known_codes
                if len(candidate) == 8 and candidate.startswith(code[:5])
            )

            if len(prefix_matches) == 1:
                return prefix_matches[0]

            padded = f"{code[:5]}0{code[5:]}"

            if padded in known_codes:
                return padded

        return code
