"""Cruzamento REF./COD. do cliente no PDF × B1_REFEREN (api-delpi).

Estratégia: ancora no valor da API e procura esse token no PDF
(perto de REF:/COD: ou como token isolado). Não usa razão social (CLIENTE:).
"""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService
from app.domain.services.chat_drawing_validation_content_service import (
    ChatDrawingValidationContentService,
)


class ChatDrawingCustomerReferenceCrossCheckService:
    _STATUS_OK = "ok"
    _STATUS_PENDING = "pending"
    _STATUS_CRITICAL = "critical_error"

    @classmethod
    def build_from_sources(
        cls,
        *,
        product: dict[str, Any] | None,
        pdf_extract: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        api_reference = cls.resolve_api_reference(product)
        haystack = cls.pdf_haystack(pdf_extract)
        extracted = cls.resolve_pdf_reference(pdf_extract)

        if not extracted and haystack:
            extracted = cls.extract_from_text(haystack) or ""

        found_in_pdf = cls.find_reference_in_text(api_reference, haystack) if api_reference else None

        # API manda; se o valor da API aparece no PDF, o cruzamento fecha (OK).
        pdf_reference = found_in_pdf or extracted or ""

        return cls.build_check_item(
            pdf_reference=pdf_reference,
            api_reference=api_reference,
            extracted_pdf_reference=extracted,
            found_api_value_in_pdf=bool(found_in_pdf),
        )

    @classmethod
    def build_check_item(
        cls,
        *,
        pdf_reference: str,
        api_reference: str,
        extracted_pdf_reference: str = "",
        found_api_value_in_pdf: bool | None = None,
    ) -> dict[str, Any] | None:
        pdf_clean = cls.coerce_reference(pdf_reference)
        api_clean = cls.coerce_reference(api_reference)
        extracted_clean = cls.coerce_reference(extracted_pdf_reference)
        pdf_norm = cls.normalize(pdf_clean)
        api_norm = cls.normalize(api_clean)
        extracted_norm = cls.normalize(extracted_clean)
        content = ChatDrawingValidationContentService

        if not pdf_norm and not api_norm:
            return None

        api_found = (
            found_api_value_in_pdf
            if found_api_value_in_pdf is not None
            else bool(api_norm and pdf_norm and api_norm == pdf_norm)
        )

        if api_norm and api_found:
            return content.item_from_template(
                "customer_reference_ok",
                status=cls._STATUS_OK,
                pdf_evidence=pdf_clean or api_clean,
                api_evidence=api_clean or api_norm,
            )

        if api_norm and pdf_norm and api_norm == pdf_norm:
            return content.item_from_template(
                "customer_reference_ok",
                status=cls._STATUS_OK,
                pdf_evidence=pdf_clean or pdf_norm,
                api_evidence=api_clean or api_norm,
            )

        # Só crítico com outra REF/COD *forte* (ex.: dígitos / 3E4270G02).
        # Ruído de descrição (CABO PARA 1002) → pending, não reprova.
        if (
            api_norm
            and extracted_norm
            and extracted_norm != api_norm
            and cls.is_strong_reference_code(extracted_clean)
        ):
            return content.item_from_template(
                "customer_reference_mismatch",
                status=cls._STATUS_CRITICAL,
                pdf_evidence=extracted_clean or extracted_norm,
                api_evidence=api_clean or api_norm,
            )

        if (
            api_norm
            and pdf_norm
            and pdf_norm != api_norm
            and cls.is_strong_reference_code(pdf_clean)
        ):
            return content.item_from_template(
                "customer_reference_mismatch",
                status=cls._STATUS_CRITICAL,
                pdf_evidence=pdf_clean or pdf_norm,
                api_evidence=api_clean or api_norm,
            )

        if api_norm and not pdf_norm:
            return content.item_from_template(
                "customer_reference_pending_pdf",
                status=cls._STATUS_PENDING,
                pdf_evidence=content.evidence("dash"),
                api_evidence=api_clean or api_norm,
            )

        return content.item_from_template(
            "customer_reference_pending_api",
            status=cls._STATUS_PENDING,
            pdf_evidence=pdf_clean or pdf_norm,
            api_evidence=content.evidence("dash"),
        )

    @classmethod
    def pdf_haystack(cls, pdf_extract: dict[str, Any] | None) -> str:
        meta = pdf_extract if isinstance(pdf_extract, dict) else {}
        chunks: list[str] = []

        for key in (
            "fullText",
            "stampText",
            "customerReference",
            "rawText",
        ):
            value = str(meta.get(key) or "").strip()

            if value:
                chunks.append(value)

        title_block = meta.get("titleBlock")

        if isinstance(title_block, dict):
            raw = str(title_block.get("rawText") or "").strip()

            if raw:
                chunks.append(raw)

            fields = title_block.get("fields")

            if isinstance(fields, dict):
                for field_key in ("customerCode", "code", "description"):
                    field_value = str(fields.get(field_key) or "").strip()

                    if field_value:
                        chunks.append(field_value)

        source_meta = meta.get("sourceMetadata")

        if isinstance(source_meta, dict):
            for key in ChatDrawingPatternsService.pdf_haystack_source_metadata_keys():
                value = str(source_meta.get(key) or "").strip()

                if value:
                    chunks.append(value)

            # Compat: chaves legadas além do catálogo JSON
            for key in ("titleText", "fullText", "cadText"):
                value = str(source_meta.get(key) or "").strip()

                if value:
                    chunks.append(value)

        scopes = meta.get("validationScopes")

        if isinstance(scopes, dict):
            for scope in scopes.values():
                if not isinstance(scope, dict):
                    continue

                for key in ("text", "fallbackText"):
                    value = str(scope.get(key) or "").strip()

                    if value:
                        chunks.append(value)

        return "\n".join(chunks)

    @classmethod
    def find_reference_in_text(cls, reference: str, text: str) -> str | None:
        """Localiza o valor da API no PDF (rótulos REF:/COD: ou token isolado)."""
        api_clean = cls.coerce_reference(reference)
        blob = str(text or "")

        if not api_clean or not blob.strip():
            return None

        api_norm = cls.normalize(api_clean)

        if not api_norm:
            return None

        spaced = r"\s*".join(re.escape(ch) for ch in api_norm)
        token_pattern = re.compile(
            rf"(?<![A-Z0-9]){spaced}(?![A-Z0-9])",
            re.IGNORECASE,
        )

        labeled_hit = cls._find_near_labels(blob, token_pattern)

        if labeled_hit:
            return labeled_hit

        match = token_pattern.search(blob)

        if match:
            return cls.coerce_reference(re.sub(r"\s+", "", match.group(0))) or api_clean

        return None

    @classmethod
    def _find_near_labels(cls, text: str, token_pattern: re.Pattern[str]) -> str | None:
        upper = text.upper()
        labels = ChatDrawingPatternsService.customer_reference_labels()

        for label in labels:
            start = 0
            label_upper = label.upper()

            while True:
                idx = upper.find(label_upper, start)

                if idx < 0:
                    break

                window = text[idx : idx + max(80, len(label) + 40)]
                match = token_pattern.search(window)

                if match:
                    return cls.coerce_reference(re.sub(r"\s+", "", match.group(0))) or match.group(0).strip()

                start = idx + len(label)

        return None

    @classmethod
    def looks_like_customer_name(cls, raw: str) -> bool:
        """Razão social (CLIENTE:) não é REF./B1_REFEREN."""
        value = str(raw or "").strip()

        if not value:
            return False

        upper = value.upper()
        markers = ChatDrawingPatternsService.customer_name_noise_markers()

        if any(marker in upper for marker in markers):
            return True

        if ChatDrawingPatternsService.customer_name_noise().search(value):
            return True

        letters = re.sub(r"[^A-Z]", "", upper)
        digits = re.sub(r"[^0-9]", "", upper)
        words = [part for part in re.split(r"[\s\-_/]+", upper) if part]

        if len(words) >= 3 and len(digits) < 4 and len(letters) >= 10:
            return True

        return False

    @classmethod
    def has_description_noise_words(cls, raw: str) -> bool:
        """Trecho de BOM/descrição (ex.: CABO PARA 1002) não é REF do cliente."""
        upper = str(raw or "").upper()

        if not upper.strip():
            return False

        for word in ChatDrawingPatternsService.customer_reference_description_noise_words():
            if not word:
                continue

            if re.search(rf"(?<![A-Z0-9]){re.escape(word)}(?![A-Z0-9])", upper):
                return True

        return False

    @classmethod
    def is_strong_reference_code(cls, raw: str) -> bool:
        """REF tipicamente numérica ou código compacto (ex.: 3E 4270 G02)."""
        value = cls.sanitize_raw(raw)

        if not value or not cls.is_plausible_reference(value):
            return False

        compact = re.sub(r"[^A-Z0-9]", "", value.upper())

        if compact.isdigit():
            return True

        tokens = [part for part in re.split(r"[\s\-_/]+", value.upper()) if part]

        if len(tokens) > 4:
            return False

        if any(len(token) > 10 for token in tokens):
            return False

        return bool(re.search(r"\d", compact))

    @classmethod
    def is_plausible_reference(cls, raw: str) -> bool:
        value = cls.sanitize_raw(raw)

        if not value:
            return False

        if cls.looks_like_customer_name(value):
            return False

        if cls.has_description_noise_words(value):
            return False

        compact = re.sub(r"[^A-Z0-9]", "", value.upper())

        if len(compact) < 4 or len(compact) > 24:
            return False

        if compact.isdigit():
            return 4 <= len(compact) <= 14

        # Código alfanumérico compacto exige ao menos um dígito (evita "CABOPARA").
        if not re.search(r"\d", compact):
            return False

        return bool(re.fullmatch(r"[A-Z0-9]{4,24}", compact))

    @classmethod
    def coerce_reference(cls, raw: str) -> str:
        """Normaliza e descarta captura de nome de cliente."""
        value = cls.sanitize_raw(raw)

        if not value or not cls.is_plausible_reference(value):
            return ""

        return value

    @classmethod
    def normalize(cls, raw: str) -> str:
        value = cls.coerce_reference(raw)

        if not value:
            return ""

        return re.sub(r"[^A-Z0-9]", "", value.upper())

    @classmethod
    def sanitize_raw(cls, raw: str) -> str:
        """Corta ruído OCR após o token REF (CLIENTE, LIBERADO, etc.)."""
        value = str(raw or "").strip()

        if not value:
            return ""

        digit_run = re.match(r"^(\d{4,14})\b", value)

        if digit_run:
            return digit_run.group(1)

        cut = re.split(
            r"\b(?:CLIENTE|LIBERADO|EXECUTADO|REVIS[AÃ]O|REV(?:IS)?\.?|COD(?:IGO)?|DATA|DES(?:CRICAO)?)\b",
            value,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0].strip(" :.|-\t")

        return cut or value

    @classmethod
    def resolve_pdf_reference(cls, pdf_extract: dict[str, Any] | None) -> str:
        meta = pdf_extract if isinstance(pdf_extract, dict) else {}
        direct = cls.coerce_reference(str(meta.get("customerReference") or ""))

        if direct:
            return direct

        title_block = meta.get("titleBlock")

        if isinstance(title_block, dict):
            fields = title_block.get("fields")

            if isinstance(fields, dict):
                from_fields = cls.coerce_reference(str(fields.get("customerCode") or ""))

                if from_fields:
                    return from_fields

        return ""

    @classmethod
    def resolve_api_reference(cls, product: dict[str, Any] | None) -> str:
        row = product if isinstance(product, dict) else {}

        for key in ("customer_reference", "customerReference", "B1_REFEREN"):
            value = cls.coerce_reference(str(row.get(key) or ""))

            if value:
                return value

        return ""

    @classmethod
    def extract_from_text(cls, text: str) -> str | None:
        """Extrai REF/COD plausível do texto do carimbo (nunca razão social)."""
        blob = str(text or "")

        if not blob.strip():
            return None

        for pattern in (
            ChatDrawingPatternsService.customer_code_labeled(),
            ChatDrawingPatternsService.customer_code_inline(),
        ):
            for match in pattern.finditer(blob):
                candidate = cls.coerce_reference(match.group(1))

                if candidate:
                    return candidate

        upper = blob.upper()

        for label in ChatDrawingPatternsService.customer_reference_labels():
            idx = upper.find(label)

            if idx < 0:
                continue

            snippet = blob[idx : idx + 120]
            same_line = snippet.split("\n", 1)[0]
            after_label = same_line[len(label) :] if len(same_line) >= len(label) else same_line
            after_label = after_label.lstrip(" :.|-\t")

            if ":" in same_line[len(label) - 1 :]:
                parts = re.split(r"[:|]", same_line, maxsplit=1)

                if len(parts) >= 2:
                    after_label = parts[1].strip()

            candidate = cls.coerce_reference(after_label.split()[0] if after_label else "")

            if not candidate:
                candidate = cls.coerce_reference(after_label)

            if candidate:
                return candidate

        return None
