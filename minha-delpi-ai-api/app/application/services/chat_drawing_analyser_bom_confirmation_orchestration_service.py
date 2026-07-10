"""Orquestra fetch `/analyser` + confirmação BOM ancorada após código resolvido."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_drawing_analyser_anchor_service import (
    AnalyserBomAnchor,
    ChatDrawingAnalyserAnchorService,
)
from app.domain.services.chat_drawing_analyser_fetch_service import (
    ChatDrawingAnalyserFetchService,
)
from app.domain.services.chat_drawing_analyser_parameter_service import (
    ChatDrawingAnalyserParameterService,
)
from app.domain.services.chat_drawing_bom_anchor_confirmation_service import (
    ChatDrawingBomAnchorConfirmationService,
)
from app.domain.services.chat_drawing_extraction_confidence_service import (
    ChatDrawingExtractionConfidenceService,
)


class ChatDrawingAnalyserBomConfirmationOrchestrationService:
    @classmethod
    def try_anchor_after_code_resolution(
        cls,
        *,
        pdf_extract: dict[str, Any] | None,
        product_code: str,
        access_token: str | None,
        storage_path: str = "",
        filename: str = "",
    ) -> dict[str, Any]:
        pdf_meta = pdf_extract if isinstance(pdf_extract, dict) else {}

        if not pdf_meta:
            return pdf_meta

        confidence = ChatDrawingExtractionConfidenceService.evaluate_for_extraction(
            pdf_extract=pdf_meta,
        )

        if not ChatDrawingAnalyserAnchorService.should_anchor_bom(
            pdf_extract=pdf_meta,
            confidence=confidence,
            product_code=product_code,
        ):
            return pdf_meta

        resolved_path = cls._resolve_storage_path(pdf_meta, storage_path=storage_path)

        if not resolved_path:
            return pdf_meta

        analyser_root = ChatDrawingAnalyserFetchService.fetch_root(
            product_code=product_code,
            access_token=access_token,
            view=ChatDrawingAnalyserParameterService.FULL_VIEW,
        )
        anchor = ChatDrawingAnalyserAnchorService.build_anchor(
            analyser_root=analyser_root,
            product_code=product_code,
        )

        if anchor is None:
            return pdf_meta

        improved, run_meta = ChatDrawingBomAnchorConfirmationService.try_improve_with_anchor(
            resolved_path,
            filename=filename or cls._resolve_filename(pdf_meta, product_code),
            pdf_extract=pdf_meta,
            anchor=anchor,
            confidence=confidence,
        )

        if improved is None:
            return pdf_meta

        return cls._attach_anchor_metadata(improved, run_meta=run_meta, anchor=anchor)

    @classmethod
    def _attach_anchor_metadata(
        cls,
        pdf_extract: dict[str, Any],
        *,
        run_meta: dict[str, Any],
        anchor: AnalyserBomAnchor,
    ) -> dict[str, Any]:
        payload = dict(pdf_extract)
        retry = payload.get("extractionQualityRetry")

        if not isinstance(retry, dict):
            retry = {}

        attempts = list(retry.get("confirmationAttempts") or [])
        attempts.append(run_meta)

        payload["extractionQualityRetry"] = {
            **retry,
            "confirmationAttempts": attempts,
            "analyserBomAnchor": {
                **anchor.to_metadata(),
                "applied": True,
            },
        }

        return payload

    @classmethod
    def _resolve_storage_path(
        cls,
        pdf_extract: dict[str, Any],
        *,
        storage_path: str,
    ) -> str:
        explicit = str(storage_path or "").strip()

        if explicit:
            return explicit

        source = pdf_extract.get("sourceMetadata")

        if isinstance(source, dict):
            from_source = str(source.get("storagePath") or "").strip()

            if from_source:
                return from_source

        return ""

    @classmethod
    def _resolve_filename(cls, pdf_extract: dict[str, Any], product_code: str) -> str:
        source = pdf_extract.get("sourceMetadata")

        if isinstance(source, dict):
            filename = str(source.get("filename") or "").strip()

            if filename:
                return filename

        code = str(product_code or "").strip()

        return f"{code}.pdf" if code else "drawing.pdf"
