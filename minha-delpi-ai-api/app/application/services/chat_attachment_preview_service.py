"""Preview de anexos indexados para welcome e metadata (Playbook 07)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_attachment_content_service import (
    ChatAttachmentContentService,
)


class ChatAttachmentPreviewService:
    @classmethod
    def build_from_extracted(cls, extracted: dict, *, filename: str) -> dict[str, Any]:
        extension = Path(filename).suffix.lower()
        metadata = extracted.get("metadata") or {}
        content = str(extracted.get("content") or "").strip()
        preview: dict[str, Any] = {
            "extension": extension or metadata.get("extension"),
            "extractor": metadata.get("extractor"),
        }

        if extension in {".csv", ".xlsx", ".xls"}:
            columns = cls._columns_from_tabular_content(content)

            if columns:
                preview["kind"] = "spreadsheet"
                preview["columns"] = columns

                sheet_title = cls._first_sheet_title(content)

                if sheet_title:
                    preview["sheetTitle"] = sheet_title

        elif extension == ".pdf":
            pages = metadata.get("pageLimit")

            if pages:
                preview["kind"] = "document"
                preview["pageLimit"] = pages

            if content:
                preview["charCount"] = len(content)

        elif extension in {".txt", ".md", ".markdown", ".json", ".docx"}:
            preview["kind"] = "text"

            if content:
                preview["charCount"] = len(content)

        elif extension in {".png", ".jpg", ".jpeg", ".webp"}:
            preview["kind"] = "image"
            width = metadata.get("width")
            height = metadata.get("height")

            if width and height:
                preview["width"] = width
                preview["height"] = height

            if metadata.get("format"):
                preview["format"] = metadata.get("format")

            ocr_meta = metadata.get("ocr") if isinstance(metadata.get("ocr"), dict) else {}

            if metadata.get("extractor") == "image_ocr" or ocr_meta.get("charCount"):
                preview["ocr"] = True
                char_count = ocr_meta.get("charCount")

                if isinstance(char_count, int) and char_count > 0:
                    preview["ocrCharCount"] = char_count

                if content:
                    ocr_prefix = ChatAssistantContentService.get(
                        "attachments",
                        "preview",
                        "ocrContentPrefix",
                        default="Texto extraído da imagem (OCR):",
                    )
                    excerpt = content.replace(ocr_prefix, "").strip()

                    if excerpt:
                        preview["ocrExcerpt"] = excerpt[:160]

        return preview

    @classmethod
    def reading_status_from_index_reason(cls, index_reason: Any) -> str | None:
        if not isinstance(index_reason, dict):
            return None

        reason = str(index_reason.get("reason") or "").strip()
        configured = ChatAttachmentContentService.index_reason_label(reason)

        if configured:
            return configured

        hint = str(index_reason.get("userHint") or "").strip()

        if hint:
            return hint[:120]

        return None

    @classmethod
    def reading_status_label(
        cls,
        *,
        status: str | None,
        parsed: bool | None = None,
        index_reason: Any = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        legacy = cls.reading_status_from_index_reason(index_reason)

        if legacy:
            return legacy

        normalized = str(status or "").strip().lower()

        if parsed or normalized == "indexed":
            base = ChatAttachmentContentService.reading_status_label("indexed")
        else:
            base = ChatAttachmentContentService.reading_status_label(normalized)

        document_vision = (metadata or {}).get("documentVision")

        if isinstance(document_vision, dict) and document_vision:
            return cls.apply_document_vision_to_reading_status(
                base_label=base,
                status=status,
                parsed=parsed,
                document_vision=document_vision,
            )

        return base

    @classmethod
    def apply_document_vision_to_reading_status(
        cls,
        *,
        base_label: str,
        status: str | None,
        parsed: bool | None,
        document_vision: dict[str, Any],
    ) -> str:
        legible = document_vision.get("legible")
        engine = str(document_vision.get("engine") or "").strip()
        normalized = str(status or "").strip().lower()

        if legible is False:
            suffix = ChatAttachmentContentService.reading_status_format(
                "lowLegibilitySuffix",
            )
            return f"{base_label}{suffix}" if suffix else base_label

        if legible is True:
            if normalized in {"index_failed", "unsupported"}:
                if engine:
                    return ChatAttachmentContentService.reading_status_format(
                        "visionReadableEngine",
                        engine=engine,
                    )
                return ChatAttachmentContentService.reading_status_format("visionReadable")

            if parsed or normalized == "indexed":
                if engine:
                    return ChatAttachmentContentService.reading_status_format(
                        "indexedVisionEngine",
                        engine=engine,
                    )

        return base_label

    @classmethod
    def document_vision_summary(cls, document_vision: dict[str, Any]) -> dict[str, Any]:
        return {
            "engine": document_vision.get("engine"),
            "legible": document_vision.get("legible"),
            "legibilityScore": document_vision.get("legibilityScore"),
            "bomRowCount": document_vision.get("bomRowCount"),
            "hasTitleBlock": document_vision.get("hasTitleBlock"),
            "tableCount": document_vision.get("tableCount"),
            "stages": document_vision.get("stages") or [],
        }

    @classmethod
    def merge_tool_context_vision_into_attachments(
        cls,
        attachments: list[dict] | None,
        tool_context: dict | None,
    ) -> list[dict]:
        if not attachments:
            return []

        vision: dict[str, Any] | None = None
        summary_legible = None

        if isinstance(tool_context, dict):
            summary = tool_context.get("drawingPdfExtractSummary")

            if isinstance(summary, dict):
                summary_legible = summary.get("legible")
                summary_vision = summary.get("documentVision")

                if isinstance(summary_vision, dict) and summary_vision:
                    vision = dict(summary_vision)

                    if summary_legible is not None and vision.get("legible") is None:
                        vision["legible"] = summary_legible

            if not vision:
                tool_vision = tool_context.get("documentVision")

                if isinstance(tool_vision, dict) and tool_vision:
                    vision = dict(tool_vision)

        if not vision:
            return [dict(item) for item in attachments if isinstance(item, dict)]

        merged: list[dict] = []

        for item in attachments:
            if not isinstance(item, dict):
                continue

            meta = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
            existing = (
                meta.get("documentVision")
                if isinstance(meta.get("documentVision"), dict)
                else {}
            )
            next_vision = {**existing, **vision}

            if summary_legible is not None and next_vision.get("legible") is None:
                next_vision["legible"] = summary_legible

            merged.append(
                {
                    **item,
                    "metadata": {
                        **meta,
                        "documentVision": next_vision,
                    },
                }
            )

        return merged

    @classmethod
    def enrich_message_attachment_snapshots(
        cls,
        attachments: list[dict] | None,
    ) -> list[dict[str, Any]]:
        snapshots: list[dict[str, Any]] = []

        for item in attachments or []:
            if not isinstance(item, dict):
                continue

            name = str(
                item.get("original_filename") or item.get("filename") or ""
            ).strip()
            status = str(item.get("status") or "uploaded").strip()
            meta = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
            preview = meta.get("preview") if isinstance(meta.get("preview"), dict) else None
            indexed = bool(meta.get("indexed")) or status == "indexed"
            parsed = indexed and preview is not None

            entry: dict[str, Any] = {
                "id": str(item.get("id") or "").strip() or None,
                "filename": item.get("filename"),
                "original_filename": name or item.get("original_filename"),
                "content_type": item.get("content_type"),
                "size_bytes": item.get("size_bytes"),
                "status": status,
                "parsed": parsed,
                "readingStatus": cls.reading_status_label(
                    status=status,
                    parsed=parsed,
                    index_reason=meta.get("indexReason"),
                    metadata=meta,
                ),
            }

            document_vision = meta.get("documentVision")

            if isinstance(document_vision, dict) and document_vision:
                entry["documentVision"] = cls.document_vision_summary(document_vision)

            if preview:
                entry["preview"] = preview

            snapshots.append(entry)

        return snapshots

    @classmethod
    def summarize_attachments(cls, attachments: list[dict] | None) -> list[dict[str, Any]]:
        summaries: list[dict[str, Any]] = []

        for item in attachments or []:
            if not isinstance(item, dict):
                continue

            name = str(
                item.get("original_filename") or item.get("filename") or ""
            ).strip()
            status = str(item.get("status") or "uploaded").strip()
            meta = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
            preview = meta.get("preview") if isinstance(meta.get("preview"), dict) else None
            indexed = bool(meta.get("indexed")) or status == "indexed"

            parsed = indexed and preview is not None

            entry: dict[str, Any] = {
                "filename": name,
                "status": status,
                "parsed": parsed,
                "readingStatus": cls.reading_status_label(
                    status=status,
                    parsed=parsed,
                    index_reason=meta.get("indexReason"),
                    metadata=meta,
                ),
            }

            if preview:
                entry["preview"] = preview

            if not indexed and status in {"unsupported", "index_failed"}:
                entry["parsed"] = False
                reason = meta.get("indexReason") or meta.get("extractor")

                if reason:
                    entry["indexReason"] = reason

            summaries.append(entry)

        return summaries

    @classmethod
    def format_reading_lines(cls, attachments: list[dict] | None) -> str:
        summaries = cls.summarize_attachments(attachments)

        if not summaries:
            return ""

        lines: list[str] = []
        default_name = ChatAssistantContentService.get(
            "attachments",
            "preview",
            "defaultFilename",
            default="arquivo",
        )
        columns_ellipsis = ChatAssistantContentService.get(
            "attachments",
            "preview",
            "columnsEllipsis",
            default=", …",
        )

        for summary in summaries[:3]:
            name = summary.get("filename") or default_name
            status = str(summary.get("status") or "")
            preview = summary.get("preview") if isinstance(summary.get("preview"), dict) else None

            if summary.get("parsed") and preview:
                if preview.get("kind") == "spreadsheet" and preview.get("columns"):
                    cols = ", ".join(str(c) for c in preview["columns"][:12])

                    if len(preview["columns"]) > 12:
                        cols += columns_ellipsis

                    sheet = preview.get("sheetTitle")

                    if sheet:
                        lines.append(
                            ChatAttachmentContentService.preview_line(
                                "spreadsheetWithSheet",
                                name=name,
                                sheet=sheet,
                                columns=cols,
                            )
                        )
                    else:
                        lines.append(
                            ChatAttachmentContentService.preview_line(
                                "spreadsheet",
                                name=name,
                                columns=cols,
                            )
                        )
                elif preview.get("kind") == "document":
                    char_suffix = (
                        ChatAttachmentContentService.preview_line(
                            "documentCharSuffix",
                            charCount=preview["charCount"],
                        )
                        if preview.get("charCount")
                        else ChatAssistantContentService.get(
                            "attachments",
                            "preview",
                            "lines",
                            "documentNoCharSuffix",
                            default=".",
                        )
                    )
                    lines.append(
                        ChatAttachmentContentService.preview_line(
                            "document",
                            name=name,
                            charSuffix=char_suffix,
                        )
                    )
                elif preview.get("kind") == "image":
                    size = ""

                    if preview.get("width") and preview.get("height"):
                        image_format = preview.get("format") or ChatAssistantContentService.get(
                            "attachments",
                            "preview",
                            "lines",
                            "imageDefaultFormat",
                            default="imagem",
                        )
                        size = ChatAttachmentContentService.preview_line(
                            "imageSize",
                            width=preview["width"],
                            height=preview["height"],
                            format=image_format,
                        )

                    if preview.get("ocr") and preview.get("ocrExcerpt"):
                        excerpt = str(preview["ocrExcerpt"]).strip()
                        lines.append(
                            ChatAttachmentContentService.preview_line(
                                "imageOcr",
                                name=name,
                                size=size,
                                excerpt=excerpt,
                            )
                        )
                    else:
                        lines.append(
                            ChatAttachmentContentService.preview_line(
                                "imageGeneric",
                                name=name,
                                size=size,
                            )
                        )
                else:
                    lines.append(
                        ChatAttachmentContentService.preview_line(
                            "textIndexed",
                            name=name,
                        )
                    )
            elif status == "indexed":
                lines.append(
                    ChatAttachmentContentService.preview_line(
                        "indexedRag",
                        name=name,
                    )
                )
            elif status in {"unsupported", "index_failed"}:
                lines.append(
                    ChatAttachmentContentService.preview_line(
                        "limitedReading",
                        name=name,
                        status=status,
                        hint=ChatAssistantContentService.get(
                            "attachments",
                            "preview",
                            "lines",
                            "limitedReadingHint",
                        ),
                    )
                )
            else:
                lines.append(
                    ChatAttachmentContentService.preview_line(
                        "processing",
                        name=name,
                    )
                )

        if not lines:
            return ""

        section_title = ChatAssistantContentService.get(
            "attachments",
            "preview",
            "readingSectionTitle",
            default="Leitura do arquivo:",
        )

        return f"\n\n**{section_title}**\n" + "\n".join(lines)

    @classmethod
    def _first_sheet_title(cls, content: str) -> str | None:
        prefix = ChatAssistantContentService.get(
            "attachments",
            "preview",
            "spreadsheetSheetPrefix",
            default="# Planilha:",
        )

        for line in content.splitlines():
            stripped = line.strip()

            if stripped.startswith(prefix):
                return stripped.split(":", 1)[-1].strip() or None

        return None

    @classmethod
    def _columns_from_tabular_content(cls, content: str) -> list[str]:
        sheet_prefix = ChatAssistantContentService.get(
            "attachments",
            "preview",
            "spreadsheetSheetPrefix",
            default="# Planilha:",
        )

        for line in content.splitlines():
            stripped = line.strip()

            if not stripped or stripped.startswith(sheet_prefix):
                continue

            parts = [part.strip() for part in stripped.split("|") if part.strip()]

            if len(parts) >= 2:
                return parts[:20]

        return []
