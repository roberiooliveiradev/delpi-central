import csv
import io
import json
import zipfile
from pathlib import Path

from app.application.services.chat_attachment_image_ocr_service import (
    ChatAttachmentImageOcrService,
)
from app.infrastructure.config.settings import Settings


class ChatAttachmentTextExtractor:
    SUPPORTED_TEXT_EXTENSIONS = {".txt", ".md", ".markdown", ".csv", ".json"}
    SUPPORTED_OPTIONAL_EXTENSIONS = {".docx", ".xlsx", ".pdf"}
    SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}

    @classmethod
    def supported_extensions(cls) -> set[str]:
        return (
            set(cls.SUPPORTED_TEXT_EXTENSIONS)
            | set(cls.SUPPORTED_OPTIONAL_EXTENSIONS)
            | set(cls.SUPPORTED_IMAGE_EXTENSIONS)
        )

    def extract(
        self,
        *,
        storage_path: str,
        filename: str,
        content_type: str | None,
        pdf_page_limit: int | None = None,
    ) -> dict:
        path = Path(storage_path)
        extension = path.suffix.lower() or Path(filename).suffix.lower()

        if extension in {".txt", ".md", ".markdown"}:
            return self._extract_plain_text(path, extension)

        if extension == ".json":
            return self._extract_json(path)

        if extension == ".csv":
            return self._extract_csv(path)

        if extension == ".doc":
            return self._legacy_format(
                extension,
                reason="legacy_doc_format",
                user_hint=(
                    "O formato .doc (Word antigo) não é lido automaticamente. "
                    "Salve como .docx e envie novamente."
                ),
            )

        if extension == ".xls":
            return self._legacy_format(
                extension,
                reason="legacy_xls_format",
                user_hint=(
                    "O formato .xls (Excel antigo) não é lido automaticamente. "
                    "Salve como .xlsx e envie novamente."
                ),
            )

        if extension == ".docx":
            return self._extract_docx(path)

        if extension == ".xlsx":
            return self._extract_xlsx(path)

        if extension == ".pdf":
            return self._extract_pdf(path, page_limit=pdf_page_limit)

        if extension in self.SUPPORTED_IMAGE_EXTENSIONS:
            return self._extract_image(path, extension)

        return {
            "supported": False,
            "content": "",
            "metadata": {
                "reason": "unsupported_extension",
                "extension": extension,
                "contentType": content_type,
            },
        }

    def _extract_plain_text(self, path: Path, extension: str) -> dict:
        content = path.read_text(encoding="utf-8", errors="ignore")

        return {
            "supported": True,
            "content": content,
            "metadata": {
                "extractor": "plain_text",
                "extension": extension,
            },
        }

    def _extract_json(self, path: Path) -> dict:
        raw = path.read_text(encoding="utf-8", errors="ignore")

        try:
            parsed = json.loads(raw)
            content = json.dumps(parsed, ensure_ascii=False, indent=2)
        except Exception:
            content = raw

        return {
            "supported": True,
            "content": content,
            "metadata": {
                "extractor": "json",
                "extension": ".json",
            },
        }

    def _extract_csv(self, path: Path) -> dict:
        raw = path.read_text(encoding="utf-8", errors="ignore")
        sample = raw[:4096]
        delimiter = ";" if sample.count(";") > sample.count(",") else ","
        reader = csv.reader(io.StringIO(raw), delimiter=delimiter)

        rows = []
        for index, row in enumerate(reader):
            if index >= 300:
                break
            rows.append(" | ".join(str(cell) for cell in row))

        return {
            "supported": True,
            "content": "\n".join(rows),
            "metadata": {
                "extractor": "csv",
                "extension": ".csv",
                "rowLimit": 300,
            },
        }

    def _extract_docx(self, path: Path) -> dict:
        try:
            with zipfile.ZipFile(path) as archive:
                xml = archive.read("word/document.xml").decode("utf-8", errors="ignore")
        except Exception as exc:
            return self._unsupported_optional(".docx", exc)

        text = (
            xml.replace("</w:p>", "\\n")
            .replace("</w:t>", " ")
        )

        import re

        text = re.sub(r"<[^>]+>", "", text)
        text = (
            text.replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("&quot;", '"')
            .replace("&apos;", "'")
        )

        return {
            "supported": True,
            "content": text,
            "metadata": {
                "extractor": "docx_zip_xml",
                "extension": ".docx",
            },
        }

    def _extract_xlsx(self, path: Path) -> dict:
        try:
            import openpyxl
        except Exception as exc:
            return self._unsupported_optional(".xlsx", exc)

        try:
            workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
            lines: list[str] = []

            for sheet in workbook.worksheets[:10]:
                lines.append(f"# Planilha: {sheet.title}")

                for row_index, row in enumerate(sheet.iter_rows(values_only=True)):
                    if row_index >= 300:
                        break

                    values = ["" if value is None else str(value) for value in row]
                    if any(values):
                        lines.append(" | ".join(values))

            return {
                "supported": True,
                "content": "\n".join(lines),
                "metadata": {
                    "extractor": "openpyxl",
                    "extension": ".xlsx",
                    "sheetLimit": 10,
                    "rowLimit": 300,
                },
            }
        except Exception as exc:
            return self._unsupported_optional(".xlsx", exc)

    def _extract_pdf(self, path: Path, *, page_limit: int | None = None) -> dict:
        try:
            from pypdf import PdfReader
        except Exception as exc:
            return self._unsupported_optional(".pdf", exc)

        try:
            reader = PdfReader(str(path))
            pages = []
            limit = max(1, int(page_limit or Settings.CHAT_ATTACHMENT_INDEX_PDF_PAGE_LIMIT))

            for page in reader.pages[:limit]:
                pages.append(page.extract_text() or "")

            return {
                "supported": True,
                "content": "\n\n".join(pages),
                "metadata": {
                    "extractor": "pypdf",
                    "extension": ".pdf",
                    "pageLimit": limit,
                },
            }
        except Exception as exc:
            return self._unsupported_optional(".pdf", exc)

    def _extract_image(self, path: Path, extension: str) -> dict:
        width: int | None = None
        height: int | None = None
        image_format: str | None = extension.lstrip(".").upper()

        try:
            from PIL import Image

            with Image.open(path) as image:
                width, height = image.size
                image_format = str(image.format or image_format or "").upper() or image_format
        except Exception:
            pass

        label = path.name
        descriptor = f"Imagem {label}"

        if width and height:
            descriptor = f"{descriptor} ({width}×{height}"

            if image_format:
                descriptor = f"{descriptor} {image_format}"

            descriptor = f"{descriptor})"

        ocr = ChatAttachmentImageOcrService.try_extract_text(path)
        ocr_text = str(ocr.get("text") or "").strip()

        metadata: dict = {
            "extension": extension,
            "width": width,
            "height": height,
            "format": image_format,
            "ocr": {
                "enabled": ChatAttachmentImageOcrService.is_enabled(),
                "used": bool(ocr.get("used")),
                "reason": ocr.get("reason"),
            },
        }

        if ocr_text:
            metadata["extractor"] = "image_ocr"
            metadata["ocr"]["charCount"] = ocr.get("charCount")
            content = (
                f"[{descriptor}]\n\n"
                "Texto extraído da imagem (OCR):\n"
                f"{ocr_text}"
            )
        else:
            metadata["extractor"] = "image_metadata"
            content = (
                f"[{descriptor}. "
                "Conteúdo visual indexado por metadados; descreva o que precisa "
                "(ex.: ler gráfico, extrair texto, gerar descrição ou texto alternativo).]"
            )

        return {
            "supported": True,
            "content": content,
            "metadata": metadata,
        }

    def _legacy_format(
        self,
        extension: str,
        *,
        reason: str,
        user_hint: str,
    ) -> dict:
        return {
            "supported": False,
            "content": "",
            "metadata": {
                "reason": reason,
                "extension": extension,
                "userHint": user_hint,
            },
        }

    def _unsupported_optional(self, extension: str, exc: Exception) -> dict:
        return {
            "supported": False,
            "content": "",
            "metadata": {
                "reason": "optional_extractor_unavailable_or_failed",
                "extension": extension,
                "error": exc.__class__.__name__,
            },
        }
