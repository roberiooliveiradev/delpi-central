"""Storage de ícones/imagens customizadas de categorias CAPEX.

Usa o mesmo volume persistente de `PLANEJAMENTO_ORCAMENTARIO_UPLOAD_DIR`
(subpasta `category-icons/{category_id}/`).
"""

from __future__ import annotations

import mimetypes
from pathlib import Path
from uuid import uuid4

from app.config import settings
from app.domain.services.planejamento_orcamentario.exceptions import (
    BudgetDocumentNotFoundError,
    BudgetDocumentTooLargeError,
    BudgetDocumentTypeNotAllowedError,
)

ALLOWED_ICON_MIME_TYPES = frozenset(
    {
        "image/png",
        "image/jpeg",
        "image/webp",
        "image/gif",
    }
)

ALLOWED_ICON_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".webp", ".gif"})

# Ícones de UI — limite menor que documentos/anexos.
MAX_CATEGORY_ICON_BYTES = 2 * 1024 * 1024


class CategoryIconStorage:
    def __init__(self, base_dir: str | None = None) -> None:
        root = Path(base_dir or settings.PLANEJAMENTO_ORCAMENTARIO_UPLOAD_DIR)
        self.base_dir = root / "category-icons"
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _safe_category_dir(self, category_id: str) -> Path:
        cid = (category_id or "").strip()
        if not cid or "/" in cid or "\\" in cid or cid.startswith("."):
            raise BudgetDocumentTypeNotAllowedError("Identificador de categoria inválido.")
        path = (self.base_dir / cid).resolve()
        base = self.base_dir.resolve()
        if not str(path).startswith(str(base)):
            raise BudgetDocumentTypeNotAllowedError("Caminho de arquivo inválido.")
        return path

    def validate_upload(
        self, *, mime_type: str | None, size_bytes: int, original_name: str
    ) -> str:
        if size_bytes <= 0:
            raise BudgetDocumentTypeNotAllowedError("Arquivo vazio.")
        if size_bytes > MAX_CATEGORY_ICON_BYTES:
            raise BudgetDocumentTooLargeError(
                "Imagem do ícone excede o limite de 2 MB."
            )
        normalized = (mime_type or "").lower().strip()
        if normalized not in ALLOWED_ICON_MIME_TYPES:
            raise BudgetDocumentTypeNotAllowedError(
                "Use PNG, JPEG, WebP ou GIF para o ícone."
            )
        extension = Path(original_name or "").suffix.lower()
        if extension not in ALLOWED_ICON_EXTENSIONS:
            raise BudgetDocumentTypeNotAllowedError(
                "Extensão inválida. Use .png, .jpg, .jpeg, .webp ou .gif."
            )
        return normalized

    def save(
        self,
        *,
        category_id: str,
        original_name: str,
        content: bytes,
        mime_type: str | None,
    ) -> tuple[str, str]:
        mime = self.validate_upload(
            mime_type=mime_type,
            size_bytes=len(content),
            original_name=original_name,
        )
        extension = Path(original_name).suffix.lower() or (
            mimetypes.guess_extension(mime) or ".png"
        )
        if extension == ".jpe":
            extension = ".jpg"
        stored_name = f"{uuid4().hex}{extension}"
        target_dir = self._safe_category_dir(category_id)
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / stored_name
        target_path.write_bytes(content)
        return stored_name, mime

    def resolve_file(self, *, category_id: str, storage_key: str) -> Path:
        key = (storage_key or "").strip()
        if not key or "/" in key or "\\" in key or key.startswith("."):
            raise BudgetDocumentTypeNotAllowedError("Identificador de arquivo inválido.")
        target_dir = self._safe_category_dir(category_id)
        path = (target_dir / key).resolve()
        if not str(path).startswith(str(target_dir.resolve())):
            raise BudgetDocumentTypeNotAllowedError("Caminho de arquivo inválido.")
        if not path.is_file():
            raise BudgetDocumentNotFoundError("Imagem do ícone não encontrada.")
        return path

    def delete_file(self, *, category_id: str, storage_key: str | None) -> None:
        if not storage_key:
            return
        try:
            path = self.resolve_file(category_id=category_id, storage_key=storage_key)
        except (BudgetDocumentNotFoundError, BudgetDocumentTypeNotAllowedError):
            return
        path.unlink(missing_ok=True)
