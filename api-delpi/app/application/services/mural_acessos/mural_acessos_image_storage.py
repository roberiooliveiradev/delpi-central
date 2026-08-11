"""Armazenamento persistente de ícones do Mural de Acessos.

Layout em disco (volume Docker)::

    {base}/links/{link_uuid}/{uuid}{ext}
"""

from __future__ import annotations

import mimetypes
import re
from pathlib import Path
from uuid import uuid4

from app.config import settings

IMAGE_MIME_TYPES = frozenset(
    {
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/webp",
        "image/gif",
    }
)
IMAGE_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".webp", ".gif"})
MAX_IMAGE_BYTES = 5 * 1024 * 1024
_SAFE_NAME_RE = re.compile(r"^[\w.\-]+$")


class MuralAcessosStorageError(ValueError):
    """Arquivo inválido ou caminho inseguro."""


class MuralAcessosImageStorage:
    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir or settings.MURAL_ACESSOS_UPLOAD_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def validate_upload(
        self,
        *,
        mime_type: str | None,
        size_bytes: int,
        original_name: str,
    ) -> None:
        if size_bytes <= 0:
            raise MuralAcessosStorageError("Arquivo vazio.")
        if size_bytes > MAX_IMAGE_BYTES:
            raise MuralAcessosStorageError("Imagem excede o limite de 5 MB.")

        extension = Path(original_name or "").suffix.lower()
        normalized_mime = (mime_type or "").lower().strip()
        if normalized_mime not in IMAGE_MIME_TYPES:
            raise MuralAcessosStorageError(
                "Formato de imagem inválido. Use JPEG, PNG, WebP ou GIF."
            )
        if extension and extension not in IMAGE_EXTENSIONS:
            raise MuralAcessosStorageError(
                "Extensão de imagem inválida. Use .jpg, .jpeg, .png, .webp ou .gif."
            )

    def save(
        self,
        *,
        link_id: str,
        original_name: str,
        content: bytes,
        mime_type: str | None,
    ) -> dict[str, str | int]:
        self.validate_upload(
            mime_type=mime_type,
            size_bytes=len(content),
            original_name=original_name,
        )

        extension = Path(original_name).suffix.lower()
        if not extension:
            extension = mimetypes.guess_extension(mime_type or "") or ".bin"
            if extension == ".jpe":
                extension = ".jpg"

        stored_name = f"{uuid4().hex}{extension}"
        target_dir = self.base_dir / "links" / link_id.strip()
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = (target_dir / stored_name).resolve()
        base = self.base_dir.resolve()
        if not str(target_path).startswith(str(base)):
            raise MuralAcessosStorageError("Caminho de arquivo inválido.")

        target_path.write_bytes(content)
        return {
            "stored_name": stored_name,
            "size_bytes": len(content),
            "mime_type": (mime_type or "application/octet-stream").lower(),
        }

    def resolve_file(self, *, link_id: str, stored_name: str) -> Path:
        link_key = (link_id or "").strip()
        name = (stored_name or "").strip()
        if not link_key or not name:
            raise MuralAcessosStorageError("Arquivo não encontrado.")
        if "/" in name or "\\" in name or not _SAFE_NAME_RE.match(name):
            raise MuralAcessosStorageError("Caminho de arquivo inválido.")

        base = self.base_dir.resolve()
        path = (self.base_dir / "links" / link_key / name).resolve()
        if not str(path).startswith(str(base)):
            raise MuralAcessosStorageError("Caminho de arquivo inválido.")
        if not path.is_file():
            raise MuralAcessosStorageError("Arquivo não encontrado.")
        return path

    def delete_file(self, *, link_id: str, stored_name: str | None) -> None:
        if not stored_name:
            return
        try:
            path = self.resolve_file(link_id=link_id, stored_name=stored_name)
        except MuralAcessosStorageError:
            return
        path.unlink(missing_ok=True)
        parent = path.parent
        if parent.is_dir() and not any(parent.iterdir()):
            parent.rmdir()
