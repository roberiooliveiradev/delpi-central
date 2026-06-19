"""Extração genérica de PDF no chat base — embedded, pypdf, fusão e tabelas por anotação."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.domain.services.chat_document_vision_content_service import (
    ChatDocumentVisionContentService,
)
from app.domain.services.chat_pdf_annotation_table_service import (
    ChatPdfAnnotationTableService,
)
from app.domain.services.chat_pdf_embedded_text_service import ChatPdfEmbeddedTextService
from app.domain.services.chat_pdf_text_fusion_service import ChatPdfTextFusionService
from app.infrastructure.config.settings import Settings


class ChatPdfDocumentExtractionService:
    LAYOUT_GENERIC = "generic"
    LAYOUT_DRAWING_DELPI = "drawing_delpi"

    @classmethod
    def extract_from_storage_path(
        cls,
        storage_path: str,
        *,
        filename: str = "",
        page_limit: int | None = None,
        layout_profile: str = LAYOUT_GENERIC,
        enable_region_ocr: bool | None = None,
    ) -> dict[str, Any]:
        path = Path(storage_path)

        if not path.is_file():
            return cls._unsupported(reason="file_not_found", filename=filename or path.name)

        limit = max(
            1,
            int(
                page_limit
                or Settings.CHAT_ATTACHMENT_INDEX_PDF_PAGE_LIMIT
            ),
        )
        stages: list[str] = []
        warnings: list[str] = []
        fusion_sources: list[dict[str, Any]] = []

        embedded = ChatPdfEmbeddedTextService.extract(str(path), page_limit=limit)

        if embedded.get("supported"):
            stages.append("fitz_embedded")
            fusion_sources.append(
                {
                    "name": "fitz_embedded",
                    "text": embedded.get("combinedText"),
                    "annotationCount": embedded.get("annotationCount"),
                }
            )

            annotation_text = str(embedded.get("annotationText") or "").strip()

            if annotation_text:
                fusion_sources.append(
                    {
                        "name": "fitz_embedded_annotations",
                        "text": annotation_text,
                        "annotationCount": embedded.get("annotationCount"),
                    }
                )

        pypdf = cls._extract_pypdf(path, page_limit=limit)

        if pypdf.get("supported"):
            stages.append("pypdf")
            fusion_sources.append(
                {
                    "name": "pypdf",
                    "text": pypdf.get("content"),
                }
            )

        region_texts: dict[str, str] = {}
        regions: dict[str, Any] = {}

        if cls._should_run_region_ocr(
            layout_profile=layout_profile,
            enable_region_ocr=enable_region_ocr,
            embedded=embedded,
            pypdf=pypdf,
        ):
            region_texts, regions = cls._ocr_layout_regions(str(path), page_limit=limit)
            stages.append("region_ocr")

            for region_name, region_text in region_texts.items():
                normalized = str(region_text or "").strip()

                if not normalized:
                    continue

                fusion_sources.append(
                    {
                        "name": f"{region_name}_region",
                        "text": normalized,
                    }
                )

        min_embedded = ChatDocumentVisionContentService.pdf_fusion_min_embedded_chars()
        fused = ChatPdfTextFusionService.fuse(
            fusion_sources,
            min_embedded_chars=min_embedded,
        )
        full_text = str(fused.get("fullText") or "").strip()

        if not full_text and not fusion_sources:
            reason = str(embedded.get("reason") or pypdf.get("reason") or "no_text")
            return cls._unsupported(reason=reason, filename=filename or path.name)

        annotations = embedded.get("annotations") if isinstance(embedded.get("annotations"), list) else []
        annotation_tables = ChatPdfAnnotationTableService.build_tables(annotations)
        annotation_table_text = ChatPdfAnnotationTableService.table_text(annotation_tables)

        if annotation_table_text and annotation_table_text not in full_text:
            full_text = ChatPdfTextFusionService._merge_texts(full_text, annotation_table_text)

        engine = str(fused.get("primarySource") or (stages[0] if stages else "unknown"))

        parse_metadata: dict[str, Any] = {
            "extractor": engine,
            "filename": filename or path.name,
            "pageLimit": limit,
            "layoutProfile": layout_profile,
            "pdfMetadata": embedded.get("pdfMetadata")
            if isinstance(embedded.get("pdfMetadata"), dict)
            else {},
            "embedded": {
                "nativeCharCount": len(str(embedded.get("nativeText") or "")),
                "annotationCount": int(embedded.get("annotationCount") or 0),
                "annotationCharCount": len(str(embedded.get("annotationText") or "")),
            },
            "annotationText": str(embedded.get("annotationText") or ""),
            "annotationTables": annotation_tables,
            "regionTexts": region_texts,
            "regions": regions,
            "fusionSources": fused.get("sources"),
        }

        if pypdf.get("supported"):
            parse_metadata["pypdfCharCount"] = len(str(pypdf.get("content") or ""))

        if region_texts.get("stamp"):
            parse_metadata["stampText"] = region_texts["stamp"]

        if region_texts.get("bom"):
            parse_metadata["bomText"] = region_texts["bom"]

        if region_texts.get("dimensions"):
            parse_metadata["dimensionsText"] = region_texts["dimensions"]

        cad_reference_text = cls._build_cad_reference_text(
            embedded,
            annotation_tables,
            annotation_text=str(embedded.get("annotationText") or ""),
        )

        if cad_reference_text:
            parse_metadata["cadReferenceText"] = cad_reference_text

        parse_metadata["stages"] = list(stages)

        return {
            "supported": True,
            "fullText": full_text,
            "charCount": len(full_text),
            "engine": engine,
            "stages": stages,
            "warnings": warnings,
            "pageCount": int(embedded.get("pageCount") or pypdf.get("pageCount") or 0),
            "annotations": annotations,
            "annotationTables": annotation_tables,
            "parseMetadata": parse_metadata,
            "filename": filename or path.name,
        }

    @classmethod
    def extract_for_attachment_index(
        cls,
        storage_path: str,
        *,
        filename: str = "",
        page_limit: int | None = None,
    ) -> dict[str, Any]:
        extracted = cls.extract_from_storage_path(
            storage_path,
            filename=filename,
            page_limit=page_limit,
            layout_profile=cls.LAYOUT_GENERIC,
            enable_region_ocr=False,
        )

        if not extracted.get("supported"):
            return {
                "supported": False,
                "content": "",
                "metadata": {
                    "reason": extracted.get("reason") or "unsupported",
                    "extension": ".pdf",
                },
            }

        metadata = dict(extracted.get("parseMetadata") or {})
        metadata["extension"] = ".pdf"
        metadata["annotationTableCount"] = len(extracted.get("annotationTables") or [])

        return {
            "supported": True,
            "content": str(extracted.get("fullText") or ""),
            "metadata": metadata,
        }

    @classmethod
    def _extract_pypdf(cls, path: Path, *, page_limit: int) -> dict[str, Any]:
        try:
            from pypdf import PdfReader
        except Exception as exc:
            return {
                "supported": False,
                "reason": f"dependencies_unavailable:{exc.__class__.__name__}",
            }

        try:
            reader = PdfReader(str(path))
            pages = []

            for page in reader.pages[:page_limit]:
                pages.append(page.extract_text() or "")

            content = "\n\n".join(pages).strip()

            return {
                "supported": bool(content),
                "content": content,
                "pageCount": min(len(reader.pages), page_limit),
            }
        except Exception as exc:
            return {
                "supported": False,
                "reason": f"pypdf_failed:{exc.__class__.__name__}",
            }

    @classmethod
    def _should_run_region_ocr(
        cls,
        *,
        layout_profile: str,
        enable_region_ocr: bool | None,
        embedded: dict[str, Any],
        pypdf: dict[str, Any],
    ) -> bool:
        if enable_region_ocr is False:
            return False

        if enable_region_ocr is True:
            return True

        if layout_profile == cls.LAYOUT_DRAWING_DELPI:
            return True

        if not ChatDocumentVisionContentService.pdf_layout_profile_allows_region_ocr(
            layout_profile
        ):
            return False

        embedded_chars = len(str(embedded.get("combinedText") or ""))
        pypdf_chars = len(str(pypdf.get("content") or ""))
        min_chars = ChatDocumentVisionContentService.pdf_region_ocr_min_chars()

        return max(embedded_chars, pypdf_chars) < min_chars

    @classmethod
    def _build_cad_reference_text(
        cls,
        embedded: dict[str, Any],
        annotation_tables: list[dict[str, Any]],
        *,
        annotation_text: str = "",
    ) -> str:
        parts: list[str] = []
        combined = str(embedded.get("combinedText") or "").strip()

        if combined:
            parts.append(combined)

        table_text = ChatPdfAnnotationTableService.table_text(annotation_tables).strip()

        if table_text and table_text not in combined:
            parts.append(table_text)

        ann = str(annotation_text or "").strip()

        if ann and ann not in "\n".join(parts):
            parts.append(ann)

        return "\n\n".join(parts).strip()

    @classmethod
    def _ocr_layout_regions(
        cls,
        storage_path: str,
        *,
        page_limit: int,
    ) -> tuple[dict[str, str], dict[str, Any]]:
        try:
            import fitz
        except ImportError:
            return {}, {}

        try:
            document = fitz.open(storage_path)
        except Exception:
            return {}, {}

        from app.domain.services.chat_drawing_region_service import ChatDrawingRegionService
        from app.infrastructure.config.settings import Settings as AppSettings
        import os

        lang = os.getenv("CHAT_DOCUMENT_VISION_TESSERACT_LANG", "por+eng").strip() or "por+eng"
        dpi = max(72, int(AppSettings.CHAT_DOCUMENT_VISION_DPI))
        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)

        region_texts: dict[str, str] = {}
        regions: dict[str, Any] = {}

        try:
            page_count = min(document.page_count, page_limit)

            if page_count < 1:
                return {}, {}

            page = document.load_page(0)
            region_texts, regions = ChatDrawingRegionService.ocr_drawing_regions(
                page,
                matrix=matrix,
                lang=lang,
            )
        finally:
            document.close()

        return region_texts, regions

    @classmethod
    def _unsupported(cls, *, reason: str, filename: str) -> dict[str, Any]:
        return {
            "supported": False,
            "fullText": "",
            "charCount": 0,
            "engine": reason,
            "stages": [],
            "warnings": [reason],
            "filename": filename,
            "reason": reason,
        }
