"""Texto embutido em PDF — página nativa, anotações CAD/ODA e metadados (chat base)."""

from __future__ import annotations

from pathlib import Path
from typing import Any


class ChatPdfEmbeddedTextService:
    @classmethod
    def extract(
        cls,
        storage_path: str,
        *,
        page_limit: int | None = None,
    ) -> dict[str, Any]:
        path = Path(storage_path)

        if not path.is_file():
            return cls._empty(reason="file_not_found")

        try:
            import fitz
        except ImportError as exc:
            return cls._empty(reason=f"dependencies_unavailable:{exc.__class__.__name__}")

        try:
            document = fitz.open(str(path))
        except Exception as exc:
            return cls._empty(reason=f"pdf_open_failed:{exc.__class__.__name__}")

        limit = max(1, int(page_limit or 10))
        native_chunks: list[str] = []
        annotation_lines: list[str] = []
        annotations: list[dict[str, Any]] = []
        annotation_count = 0
        page_count = 0

        try:
            for index, page in enumerate(document):
                if index >= limit:
                    break

                page_count += 1
                page_text = str(page.get_text("text") or "").strip()

                if page_text:
                    native_chunks.append(page_text)

                for annot in page.annots() or []:
                    content = str(annot.info.get("content") or "").strip()

                    if not content:
                        continue

                    annotation_count += 1
                    annotation_lines.append(content)

                    rect = annot.rect
                    annotations.append(
                        {
                            "page": index + 1,
                            "content": content,
                            "bbox": [
                                round(float(rect.x0), 2),
                                round(float(rect.y0), 2),
                                round(float(rect.x1), 2),
                                round(float(rect.y1), 2),
                            ],
                            "type": str(annot.type[1] if annot.type else "").strip() or None,
                        }
                    )

            pdf_metadata = {
                key: str(value).strip()
                for key, value in (document.metadata or {}).items()
                if value not in (None, "")
            }
        finally:
            document.close()

        native_text = "\n\n".join(native_chunks).strip()
        annotation_text = "\n".join(annotation_lines).strip()
        combined_parts = [part for part in (native_text, annotation_text) if part]
        combined_text = "\n\n".join(combined_parts).strip()

        if not combined_text:
            return cls._empty(
                reason="no_embedded_text",
                pdf_metadata=pdf_metadata if "pdf_metadata" in locals() else {},
                page_count=page_count,
                annotations=annotations,
            )

        return {
            "supported": True,
            "nativeText": native_text,
            "annotationText": annotation_text,
            "combinedText": combined_text,
            "charCount": len(combined_text),
            "annotationCount": annotation_count,
            "annotations": annotations,
            "pdfMetadata": pdf_metadata if "pdf_metadata" in locals() else {},
            "extractor": "fitz_embedded",
            "pageLimit": limit,
            "pageCount": page_count,
        }

    @classmethod
    def _empty(
        cls,
        *,
        reason: str,
        pdf_metadata: dict[str, str] | None = None,
        page_count: int = 0,
        annotations: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        return {
            "supported": False,
            "nativeText": "",
            "annotationText": "",
            "combinedText": "",
            "charCount": 0,
            "annotationCount": 0,
            "annotations": annotations or [],
            "pdfMetadata": pdf_metadata or {},
            "extractor": "fitz_embedded",
            "pageCount": page_count,
            "reason": reason,
        }
