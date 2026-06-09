"""Resolução canônica do código de produto em turnos de análise de desenho."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from app.domain.services.chat_drawing_pdf_extraction_service import (
    ChatDrawingPdfExtractionService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)

_FILENAME_CODE_RE = re.compile(
    r"^(?:delpi[_-]?)?(90\d{6}|10\d{6}|100\d{5})(?:[_-].*)?$",
    re.IGNORECASE,
)
_PRIMARY_CODE_RE = re.compile(r"^(90\d{6}|50\d{6})$")
_HIGH_CONFIDENCE = 0.85


class ChatDrawingProductCodeResolutionService:
    @classmethod
    def resolve(
        cls,
        *,
        message: str | None,
        has_pdf_attachment: bool,
        pdf_extract: dict[str, Any] | None = None,
        attachment_filename: str | None = None,
        previous_messages: list | None = None,
        user_context_items: list | None = None,
        operational_focus: dict | None = None,
        conversation_context: str | None = None,
    ) -> tuple[str | None, str | None]:
        message_code = ChatProductQueryIntentService.extract_product_code(message or "")

        if message_code:
            return message_code, "message"

        if has_pdf_attachment:
            return cls._resolve_with_pdf_attachment(
                pdf_extract=pdf_extract,
                attachment_filename=attachment_filename,
            )

        code = ChatProductQueryIntentService.resolve_product_code(
            message or "",
            conversation_context,
            previous_messages=previous_messages,
            user_context_items=user_context_items,
            operational_focus=operational_focus,
        )

        return (str(code).strip(), "context") if code else (None, None)

    @classmethod
    def merge_precedence(
        cls,
        *,
        current_code: str | None,
        current_source: str | None,
        resolved_code: str | None,
        resolved_source: str | None,
    ) -> tuple[str | None, str | None]:
        if not resolved_code:
            return current_code, current_source

        if not current_code:
            return resolved_code, resolved_source

        if str(current_code) == str(resolved_code):
            return resolved_code, resolved_source or current_source

        resolved_rank = cls._source_rank(resolved_source)
        current_rank = cls._source_rank(current_source)

        if resolved_rank >= current_rank:
            return resolved_code, resolved_source

        return current_code, current_source

    @classmethod
    def extract_product_code_from_filename(cls, filename: str | None) -> str | None:
        stem = Path(str(filename or "").strip()).stem

        if not stem:
            return None

        match = _FILENAME_CODE_RE.match(stem)

        if not match:
            return None

        return ChatProductQueryIntentService.normalize_product_code(match.group(1))

    @classmethod
    def resolve_attachment_filename(
        cls,
        *,
        user_id: str | None,
        session_id: str | None,
        attachment_ids: list | None,
    ) -> str | None:
        if not attachment_ids:
            return None

        from app.application.services.chat_document_vision_service import (
            ChatDocumentVisionService,
        )

        attachment = ChatDocumentVisionService._resolve_first_document_attachment(
            user_id=user_id,
            session_id=session_id,
            attachment_ids=attachment_ids,
        )

        if not attachment:
            return None

        return str(getattr(attachment, "original_filename", None) or "").strip() or None

    @classmethod
    def pick_from_candidates(
        cls,
        candidates: list[Any] | None,
        *,
        filename_code: str | None = None,
    ) -> tuple[str | None, str | None]:
        ranked = cls._rank_candidates(candidates)

        if not ranked:
            return None, None

        top = ranked[0]
        code = ChatProductQueryIntentService.normalize_product_code(str(top.get("code") or ""))
        source = str(top.get("source") or "stamp_labeled")

        if not code:
            return None, None

        high_conf = [
            item
            for item in ranked
            if float(item.get("confidence") or 0) >= _HIGH_CONFIDENCE
            and str(item.get("code")) != code
        ]

        if high_conf:
            return None, "unresolved"

        if filename_code and code != filename_code:
            if cls._filename_looks_like_primary_product(filename_code):
                if float(top.get("confidence") or 0) < _HIGH_CONFIDENCE:
                    return filename_code, "filename_crosscheck"

        return code, source

    @classmethod
    def ocr_code_likely_filename_drift(cls, extracted_code: str, filename_code: str) -> bool:
        extracted = ChatProductQueryIntentService.normalize_product_code(extracted_code)
        filename = ChatProductQueryIntentService.normalize_product_code(filename_code)

        if not extracted or not filename:
            return False

        if not (extracted.startswith("90") and filename.startswith("90")):
            return False

        if len(extracted) != len(filename):
            return False

        differences = sum(left != right for left, right in zip(extracted, filename))

        return differences == 1

    @classmethod
    def enrich_pdf_extract_conflicts(
        cls,
        pdf_extract: dict[str, Any] | None,
        *,
        attachment_filename: str | None = None,
    ) -> dict[str, Any]:
        meta = dict(pdf_extract) if isinstance(pdf_extract, dict) else {}
        conflicts = list(meta.get("conflicts") or [])
        filename_code = cls.extract_product_code_from_filename(attachment_filename)
        pdf_code = ChatProductQueryIntentService.normalize_product_code(
            str(meta.get("productCode") or "")
        )

        if pdf_code and filename_code and pdf_code != filename_code:
            if cls._looks_like_bom_component(pdf_code) and cls._filename_looks_like_primary_product(
                filename_code
            ):
                conflicts.append(
                    {
                        "type": "bom_code_promoted",
                        "severity": "forbidden",
                        "filenameCode": filename_code,
                        "stampCode": pdf_code,
                    }
                )
                meta["productCode"] = filename_code
                meta["productCodeSource"] = "filename_crosscheck"

        if conflicts:
            meta["conflicts"] = conflicts

        return meta

    @classmethod
    def _resolve_with_pdf_attachment(
        cls,
        *,
        pdf_extract: dict[str, Any] | None,
        attachment_filename: str | None,
    ) -> tuple[str | None, str | None]:
        filename_code = cls.extract_product_code_from_filename(attachment_filename)
        pdf_meta = pdf_extract if isinstance(pdf_extract, dict) else {}
        candidates = pdf_meta.get("productCodeCandidates") if isinstance(
            pdf_meta.get("productCodeCandidates"), list
        ) else []
        pdf_code = str(pdf_meta.get("productCode") or "").strip() or None
        pdf_source = str(
            pdf_meta.get("productCodeSource")
            or ("document_vision" if pdf_meta.get("documentVision") else pdf_meta.get("extractor"))
            or "pdf_extract"
        )

        if pdf_code and cls._looks_like_bom_component(pdf_code):
            if filename_code and cls._filename_looks_like_primary_product(filename_code):
                return filename_code, "filename"

        candidate_code, candidate_source = cls.pick_from_candidates(
            candidates,
            filename_code=filename_code,
        )

        if not pdf_code and candidate_code:
            return candidate_code, candidate_source

        if filename_code and pdf_code and filename_code != pdf_code:
            if cls._filename_looks_like_primary_product(filename_code):
                if cls._looks_like_bom_component(pdf_code):
                    return filename_code, "filename"

                if candidate_code and candidate_code != pdf_code:
                    if float(
                        next(
                            (
                                item.get("confidence")
                                for item in cls._rank_candidates(candidates)
                                if str(item.get("code")) == candidate_code
                            ),
                            0,
                        )
                    ) >= _HIGH_CONFIDENCE:
                        return candidate_code, candidate_source

                return filename_code, "filename"

        if filename_code:
            return filename_code, "filename"

        if pdf_code:
            return pdf_code, pdf_source

        if candidate_code:
            return candidate_code, candidate_source

        return None, None

    @classmethod
    def _rank_candidates(cls, candidates: list[Any] | None) -> list[dict[str, Any]]:
        if not isinstance(candidates, list):
            return []

        ranked: list[dict[str, Any]] = []

        for item in candidates:
            if not isinstance(item, dict):
                continue

            code = ChatProductQueryIntentService.normalize_product_code(str(item.get("code") or ""))

            if not code or cls._looks_like_bom_component(code):
                continue

            ranked.append({**item, "code": code})

        return sorted(
            ranked,
            key=lambda item: float(item.get("confidence") or 0),
            reverse=True,
        )

    @classmethod
    def _filename_looks_like_primary_product(cls, code: str) -> bool:
        normalized = ChatProductQueryIntentService.normalize_product_code(code)

        return bool(normalized and normalized.startswith("90"))

    @classmethod
    def _looks_like_bom_component(cls, code: str | None) -> bool:
        normalized = ChatProductQueryIntentService.normalize_product_code(code or "")

        if not normalized:
            return False

        return normalized.startswith(("10", "100"))

    @classmethod
    def _looks_like_primary_drawing(cls, code: str | None) -> bool:
        normalized = ChatProductQueryIntentService.normalize_product_code(code or "")

        return bool(normalized and _PRIMARY_CODE_RE.match(normalized))

    @classmethod
    def _source_rank(cls, source: str | None) -> int:
        ranking = {
            "message": 50,
            "filename": 40,
            "filename_crosscheck": 39,
            "stamp_labeled": 38,
            "title_pattern": 37,
            "document_vision": 35,
            "title_block": 34,
            "pdf_extract": 30,
            "attachment_context": 28,
            "turn": 20,
            "context": 10,
            "unresolved": 0,
        }

        return ranking.get(str(source or "").strip(), 0)
