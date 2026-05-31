"""Preview de anexos indexados para welcome e metadata (Playbook 07)."""

from __future__ import annotations

from pathlib import Path
from typing import Any


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
                    excerpt = content.replace("Texto extraído da imagem (OCR):", "").strip()

                    if excerpt:
                        preview["ocrExcerpt"] = excerpt[:160]

        return preview

    @classmethod
    def reading_status_from_index_reason(cls, index_reason: Any) -> str | None:
        if not isinstance(index_reason, dict):
            return None

        reason = str(index_reason.get("reason") or "").strip()

        if reason == "legacy_doc_format":
            return "DOC legado — salve como DOCX"

        if reason == "legacy_xls_format":
            return "XLS legado — salve como XLSX"

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
    ) -> str:
        legacy = cls.reading_status_from_index_reason(index_reason)

        if legacy:
            return legacy

        normalized = str(status or "").strip().lower()

        if parsed or normalized == "indexed":
            return "Indexado"

        if normalized in {"uploaded", "uploading"}:
            return "Processando leitura"

        if normalized == "unsupported":
            return "Leitura limitada"

        if normalized == "index_failed":
            return "Falha na leitura"

        return "Aguardando envio"

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

        for summary in summaries[:3]:
            name = summary.get("filename") or "arquivo"
            status = str(summary.get("status") or "")
            preview = summary.get("preview") if isinstance(summary.get("preview"), dict) else None

            if summary.get("parsed") and preview:
                if preview.get("kind") == "spreadsheet" and preview.get("columns"):
                    cols = ", ".join(str(c) for c in preview["columns"][:12])

                    if len(preview["columns"]) > 12:
                        cols += ", …"

                    sheet = preview.get("sheetTitle")

                    if sheet:
                        lines.append(
                            f"- **{name}:** planilha indexada (*{sheet}*). Colunas: {cols}."
                        )
                    else:
                        lines.append(
                            f"- **{name}:** planilha indexada. Colunas: {cols}."
                        )
                elif preview.get("kind") == "document":
                    lines.append(
                        f"- **{name}:** documento indexado"
                        + (
                            f" (~{preview['charCount']} caracteres extraídos)."
                            if preview.get("charCount")
                            else "."
                        )
                    )
                elif preview.get("kind") == "image":
                    size = ""

                    if preview.get("width") and preview.get("height"):
                        fmt = preview.get("format") or "imagem"
                        size = f" ({preview['width']}×{preview['height']} {fmt})"

                    if preview.get("ocr") and preview.get("ocrExcerpt"):
                        excerpt = str(preview["ocrExcerpt"]).strip()
                        lines.append(
                            f"- **{name}:** imagem com OCR{size} — «{excerpt}»"
                        )
                    else:
                        lines.append(
                            f"- **{name}:** imagem indexada{size} — descreva o que analisar no visual."
                        )
                else:
                    lines.append(f"- **{name}:** conteúdo indexado para consulta no chat.")
            elif status == "indexed":
                lines.append(f"- **{name}:** indexado para RAG nesta sessão.")
            elif status in {"unsupported", "index_failed"}:
                lines.append(
                    f"- **{name}:** leitura automática limitada ({status}). "
                    "Ainda posso ajudar se você descrever o que precisa."
                )
            else:
                lines.append(f"- **{name}:** recebido; processamento em andamento.")

        if not lines:
            return ""

        return "\n\n**Leitura do arquivo:**\n" + "\n".join(lines)

    @staticmethod
    def _first_sheet_title(content: str) -> str | None:
        for line in content.splitlines():
            stripped = line.strip()

            if stripped.startswith("# Planilha:"):
                return stripped.split(":", 1)[-1].strip() or None

        return None

    @staticmethod
    def _columns_from_tabular_content(content: str) -> list[str]:
        for line in content.splitlines():
            stripped = line.strip()

            if not stripped or stripped.startswith("# Planilha:"):
                continue

            parts = [part.strip() for part in stripped.split("|") if part.strip()]

            if len(parts) >= 2:
                return parts[:20]

        return []
