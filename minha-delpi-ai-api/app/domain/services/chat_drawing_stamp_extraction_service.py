"""Parse hierárquico de carimbo/título de desenho DELPI — Onda 14.3."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_drawing_region_service import ChatDrawingRegionService
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)

_BUNDLE = "drawing_stamp"
_CODE_TOKEN_RE = re.compile(
    r"\b(90\d{6}|50\d{6}|10\d{6}|100\d{5})\b",
    re.IGNORECASE,
)
_OCR_SPACED_CODE_RE = re.compile(
    r"(90|50|10)\s*(\d{3})\s*(\d{3})",
    re.IGNORECASE,
)
_REV_RE = re.compile(
    r"REV(?:\.|IS[ÃA]O)?\s*[:.]?\s*(\d{1,3})",
    re.IGNORECASE,
)


class ChatDrawingStampExtractionService:
    @classmethod
    def extract(
        cls,
        *,
        stamp_text: str = "",
        title_text: str = "",
        message_code: str | None = None,
        filename_code: str | None = None,
    ) -> dict[str, Any]:
        stamp = str(stamp_text or "").strip()
        title = str(title_text or "").strip()
        combined = "\n".join(part for part in (stamp, title) if part).strip()

        candidates: list[dict[str, Any]] = []
        conflicts: list[dict[str, Any]] = []

        labeled_code, labeled_source = cls._extract_labeled_product_code(stamp or combined)

        if labeled_code:
            candidates.append(
                cls._candidate(labeled_code, labeled_source, 0.92),
            )

        title_code = cls._extract_title_pattern_code(combined)

        if title_code:
            candidates.append(cls._candidate(title_code, "title_pattern", 0.88))

        if stamp:
            for code in cls._scan_codes_excluding_customer_fields(stamp):
                if cls._candidate_exists(candidates, code):
                    continue

                candidates.append(cls._candidate(code, "stamp_context", 0.55))

        intermediate_codes = sorted(
            {
                ChatProductQueryIntentService.normalize_product_code(match)
                for match in _CODE_TOKEN_RE.findall(combined)
                if match.startswith("50")
            }
        )

        product_code, product_source = cls._resolve_candidates(candidates)

        if message_code and product_code and message_code != product_code:
            conflicts.append(
                {
                    "type": "stamp_vs_message",
                    "severity": "critical",
                    "messageCode": message_code,
                    "stampCode": product_code,
                }
            )
            product_code = message_code
            product_source = "user_message"

        if filename_code and product_code and filename_code != product_code:
            conflicts.append(
                {
                    "type": "stamp_vs_filename",
                    "severity": "pending",
                    "filenameCode": filename_code,
                    "stampCode": product_code,
                }
            )

        revision = cls._extract_revision(combined)
        customer_code, customer_description = cls._extract_customer_fields(combined)
        description = cls._extract_description(combined)

        if not product_code and not candidates and combined:
            if cls._looks_unresolvable(combined):
                product_source = "unresolved"

        return {
            "schemaVersion": "2.0",
            "productCode": product_code,
            "productCodeSource": product_source,
            "productCodeCandidates": candidates,
            "revision": revision,
            "customerCode": customer_code,
            "customerDescription": customer_description,
            "description": description,
            "intermediateCodes": intermediate_codes,
            "conflicts": conflicts,
        }

    @classmethod
    def build_title_block(
        cls,
        extract: dict[str, Any] | None,
        *,
        raw_text: str = "",
    ) -> dict[str, Any] | None:
        payload = extract if isinstance(extract, dict) else {}
        code = str(payload.get("productCode") or "").strip()
        rev = str(payload.get("revision") or "").strip()
        raw = str(raw_text or "").strip()

        if not code and not rev and not raw:
            return None

        fields: dict[str, str] = {}

        if code:
            fields["code"] = ChatProductQueryIntentService.normalize_product_code(code)

        if rev:
            fields["rev"] = rev.zfill(2) if rev.isdigit() else rev

        if payload.get("customerCode"):
            fields["customerCode"] = str(payload["customerCode"])

        if payload.get("description"):
            fields["description"] = str(payload["description"])[:120]

        return {
            "rawText": raw[:800],
            "bbox": list(ChatDrawingRegionService.stamp_bbox()),
            "fields": fields,
        }

    @classmethod
    def _extract_labeled_product_code(cls, text: str) -> tuple[str | None, str | None]:
        masked = cls._mask_customer_fields(text)
        labels = ChatAssistantContentService.list(_BUNDLE, "stampFieldLabels", "productCode")

        for label in labels:
            pattern = (
                rf"{re.escape(label)}\s*[:.]?\s*"
                rf"((?:90|50|10)\s*\d{{3}}\s*\d{{3}}|(?:90|50|10)\d{{6}}|100\d{{5}})"
            )

            match = re.search(pattern, masked, re.IGNORECASE)

            if not match:
                continue

            code = cls._normalize_ocr_code(match.group(1))

            if code and cls._is_drawing_product_code(code):
                return code, "stamp_labeled"

        return None, None

    @classmethod
    def _extract_title_pattern_code(cls, text: str) -> str | None:
        masked = cls._mask_customer_fields(text)
        prefixes = ChatAssistantContentService.list(_BUNDLE, "titlePatterns", "chicotePrefixes")

        for prefix in prefixes:
            normalized_prefix = cls._normalize_token(prefix)
            idx = cls._fold_ascii(masked).find(normalized_prefix)

            if idx < 0:
                continue

            tail = masked[idx + len(normalized_prefix) :].lstrip()
            chunk = re.sub(r"^[/|·\-]+\s*", "", tail).split("\n", 1)[0].strip()
            if not chunk:
                continue

            code = cls._normalize_ocr_code(chunk)

            if code and cls._is_drawing_product_code(code) and not code.startswith("10"):
                return code

        return None

    @classmethod
    def _scan_codes_excluding_customer_fields(cls, text: str) -> list[str]:
        masked = cls._mask_customer_fields(text)
        found: list[str] = []

        for match in _CODE_TOKEN_RE.finditer(masked):
            code = ChatProductQueryIntentService.normalize_product_code(match.group(1))

            if not code or not cls._is_drawing_product_code(code):
                continue

            if code.startswith(("10", "50")):
                continue

            if code not in found:
                found.append(code)

        for match in _OCR_SPACED_CODE_RE.finditer(masked):
            code = cls._normalize_ocr_code("".join(match.groups()))

            if not code or code.startswith("50"):
                continue

            if code not in found:
                found.append(code)

        return found

    @classmethod
    def _mask_customer_fields(cls, text: str) -> str:
        lines = str(text or "").splitlines()
        prefixes = ChatAssistantContentService.list(_BUNDLE, "customerExclusionPrefixes")
        masked_lines: list[str] = []

        for line in lines:
            upper = line.upper()
            masked_line = line

            for prefix in prefixes:
                idx = upper.find(prefix.upper())

                if idx >= 0:
                    masked_line = line[: idx + len(prefix)] + " " * max(0, len(line) - idx - len(prefix))
                    break

            masked_lines.append(masked_line)

        return "\n".join(masked_lines)

    @classmethod
    def _extract_revision(cls, text: str) -> str | None:
        match = _REV_RE.search(text)

        if match:
            return match.group(1).zfill(2)

        return None

    @classmethod
    def _extract_customer_fields(cls, text: str) -> tuple[str | None, str | None]:
        customer_code = None
        customer_description = None

        code_match = re.search(
            r"(?:COD\.?\s*CLIENTE|C[ÓO]D\.?\s*CLIENTE)\s*[:.]?\s*(\d{4,12})",
            text,
            re.IGNORECASE,
        )

        if not code_match:
            code_match = re.search(
                r"(?:^|\n)\s*COD\s*:\s*(\d{4,12})",
                text,
                re.IGNORECASE,
            )

        if code_match:
            customer_code = code_match.group(1).strip()

        des_match = re.search(
            r"(?:DES\.?\s*CLIENTE|DES\.?)\s*[:.]?\s*(\d{4,14})",
            text,
            re.IGNORECASE,
        )

        if des_match:
            customer_description = des_match.group(1).strip()

        return customer_code, customer_description

    @classmethod
    def _extract_description(cls, text: str) -> str | None:
        title_code = cls._extract_title_pattern_code(text)

        if title_code:
            return "CHICOTE DE LIGACAO"

        for prefix in ChatAssistantContentService.list(_BUNDLE, "titlePatterns", "chicotePrefixes"):
            if cls._normalize_token(prefix) in cls._normalize_token(text):
                return prefix.split("/")[0].strip()

        return None

    @classmethod
    def _resolve_candidates(
        cls,
        candidates: list[dict[str, Any]],
    ) -> tuple[str | None, str | None]:
        if not candidates:
            return None, None

        ranked = sorted(
            candidates,
            key=lambda item: float(item.get("confidence") or 0),
            reverse=True,
        )
        top = ranked[0]
        code = ChatProductQueryIntentService.normalize_product_code(str(top.get("code") or ""))

        if not code:
            return None, None

        high_conf = [
            item
            for item in ranked
            if float(item.get("confidence") or 0) >= 0.85
            and str(item.get("code")) != code
        ]

        if high_conf:
            return None, "unresolved"

        return code, str(top.get("source") or "stamp_labeled")

    @classmethod
    def _candidate(cls, code: str, source: str, confidence: float) -> dict[str, Any]:
        normalized = ChatProductQueryIntentService.normalize_product_code(code)

        return {
            "code": normalized,
            "source": source,
            "confidence": confidence,
        }

    @classmethod
    def _candidate_exists(cls, candidates: list[dict[str, Any]], code: str) -> bool:
        normalized = ChatProductQueryIntentService.normalize_product_code(code)

        return any(str(item.get("code")) == normalized for item in candidates)

    @classmethod
    def _normalize_ocr_code(cls, raw: str) -> str | None:
        compact = re.sub(r"\s+", "", str(raw or ""))

        if not compact:
            return None

        return ChatProductQueryIntentService.normalize_product_code(compact)

    @classmethod
    def _normalize_token(cls, value: str) -> str:
        import unicodedata

        folded = unicodedata.normalize("NFKD", str(value or ""))
        ascii_only = folded.encode("ascii", "ignore").decode("ascii")

        return re.sub(r"\s+", " ", ascii_only).strip().upper()

    @classmethod
    def _fold_ascii(cls, value: str) -> str:
        import unicodedata

        folded = unicodedata.normalize("NFKD", str(value or ""))

        return folded.encode("ascii", "ignore").decode("ascii").upper()

    @classmethod
    def _looks_unresolvable(cls, text: str) -> bool:
        return not bool(_CODE_TOKEN_RE.search(cls._mask_customer_fields(text)))

    @classmethod
    def _is_drawing_product_code(cls, code: str | None) -> bool:
        normalized = ChatProductQueryIntentService.normalize_product_code(code or "")

        if not normalized or not ChatProductQueryIntentService.is_plausible_product_code(normalized):
            return False

        return bool(re.match(r"^(90\d{6}|50\d{6})$", normalized))
