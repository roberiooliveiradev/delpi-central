"""Armazenamento persistente de mídias/anexos — Guias e Procedimentos.

Layout em disco (volume Docker)::

    {base}/procedures/{procedure_uuid}/images|videos|attachments/{uuid}{ext}

Referência de segurança: PacEvidenceStorage (path traversal, UUID no nome).
"""

from __future__ import annotations

import mimetypes
import re
from pathlib import Path
from typing import Literal
from uuid import uuid4
from urllib.parse import ParseResult, parse_qs, urlparse

from app.config import settings

MediaKind = Literal["image", "video_file", "attachment"]
StorageSubdir = Literal["images", "videos", "attachments"]

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

VIDEO_MIME_TYPES = frozenset(
    {
        "video/mp4",
        "video/webm",
        "video/quicktime",
    }
)
VIDEO_EXTENSIONS = frozenset({".mp4", ".webm", ".mov"})

ATTACHMENT_MIME_TYPES = frozenset(
    {
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/plain",
        "text/csv",
        "image/jpeg",
        "image/png",
        "image/webp",
    }
)
ATTACHMENT_EXTENSIONS = frozenset(
    {
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".txt",
        ".csv",
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
    }
)

# Alinhado ao client_max_body_size do gateway (20m).
MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_VIDEO_BYTES = 20 * 1024 * 1024
MAX_ATTACHMENT_BYTES = 20 * 1024 * 1024

_SAFE_NAME_RE = re.compile(r"^[\w.\-]+$")

# Provedores controlados (sem iframe HTML arbitrário no backend).
_EXTERNAL_VIDEO_HOSTS: dict[str, tuple[str, ...]] = {
    "youtube": ("www.youtube.com", "youtube.com", "youtu.be", "m.youtube.com"),
    "vimeo": ("vimeo.com", "www.vimeo.com", "player.vimeo.com"),
    "google_drive": ("drive.google.com", "www.drive.google.com"),
}

# IDs de arquivo do Google Drive (links públicos de compartilhamento).
_GOOGLE_DRIVE_FILE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{10,128}$")


class GuiasMediaStorageError(ValueError):
    pass


class GuiasProcedimentosMediaStorage:
    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(
            base_dir or settings.GUIAS_PROCEDIMENTOS_UPLOAD_DIR
        )
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def validate_upload(
        self,
        *,
        kind: MediaKind,
        mime_type: str | None,
        size_bytes: int,
        original_name: str,
    ) -> None:
        if size_bytes <= 0:
            raise GuiasMediaStorageError("Arquivo vazio.")

        extension = Path(original_name or "").suffix.lower()
        normalized_mime = (mime_type or "").lower().strip()

        if kind == "image":
            if size_bytes > MAX_IMAGE_BYTES:
                raise GuiasMediaStorageError("Imagem excede o limite de 5 MB.")
            if normalized_mime not in IMAGE_MIME_TYPES:
                raise GuiasMediaStorageError(
                    "Formato de imagem inválido. Use JPEG, PNG, WebP ou GIF."
                )
            if extension and extension not in IMAGE_EXTENSIONS:
                raise GuiasMediaStorageError(
                    "Extensão de imagem inválida. Use .jpg, .jpeg, .png, .webp ou .gif."
                )
            return

        if kind == "video_file":
            if size_bytes > MAX_VIDEO_BYTES:
                raise GuiasMediaStorageError("Vídeo excede o limite de 20 MB.")
            if normalized_mime not in VIDEO_MIME_TYPES:
                raise GuiasMediaStorageError(
                    "Formato de vídeo inválido. Use MP4, WebM ou QuickTime."
                )
            if extension and extension not in VIDEO_EXTENSIONS:
                raise GuiasMediaStorageError(
                    "Extensão de vídeo inválida. Use .mp4, .webm ou .mov."
                )
            return

        if kind == "attachment":
            if size_bytes > MAX_ATTACHMENT_BYTES:
                raise GuiasMediaStorageError("Anexo excede o limite de 20 MB.")
            if normalized_mime not in ATTACHMENT_MIME_TYPES:
                raise GuiasMediaStorageError(
                    "Formato de anexo inválido. Use PDF, Office, texto ou imagem."
                )
            if extension and extension not in ATTACHMENT_EXTENSIONS:
                raise GuiasMediaStorageError(
                    "Extensão de anexo inválida."
                )
            return

        raise GuiasMediaStorageError("Tipo de mídia inválido.")

    @staticmethod
    def subdir_for(kind: MediaKind) -> StorageSubdir:
        if kind == "image":
            return "images"
        if kind == "video_file":
            return "videos"
        return "attachments"

    def save(
        self,
        *,
        procedure_id: str,
        kind: MediaKind,
        original_name: str,
        content: bytes,
        mime_type: str | None,
    ) -> dict[str, str | int]:
        self.validate_upload(
            kind=kind,
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
        subdir = self.subdir_for(kind)
        target_dir = (
            self.base_dir / "procedures" / procedure_id.strip() / subdir
        )
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = (target_dir / stored_name).resolve()
        base = self.base_dir.resolve()
        if not str(target_path).startswith(str(base)):
            raise GuiasMediaStorageError("Caminho de arquivo inválido.")

        target_path.write_bytes(content)
        return {
            "stored_name": stored_name,
            "storage_subdir": subdir,
            "size_bytes": len(content),
            "mime_type": (mime_type or "application/octet-stream").lower(),
        }

    def resolve_file(
        self,
        *,
        procedure_id: str,
        storage_subdir: str,
        stored_name: str,
    ) -> Path:
        procedure_key = (procedure_id or "").strip()
        subdir = (storage_subdir or "").strip()
        name = (stored_name or "").strip()
        if not procedure_key or not subdir or not name:
            raise GuiasMediaStorageError("Arquivo não encontrado.")
        if subdir not in {"images", "videos", "attachments"}:
            raise GuiasMediaStorageError("Caminho de arquivo inválido.")
        if "/" in name or "\\" in name or not _SAFE_NAME_RE.match(name):
            raise GuiasMediaStorageError("Caminho de arquivo inválido.")

        base = self.base_dir.resolve()
        path = (
            self.base_dir / "procedures" / procedure_key / subdir / name
        ).resolve()
        if not str(path).startswith(str(base)):
            raise GuiasMediaStorageError("Caminho de arquivo inválido.")
        if not path.is_file():
            raise GuiasMediaStorageError("Arquivo não encontrado.")
        return path

    def delete_file(
        self,
        *,
        procedure_id: str,
        storage_subdir: str,
        stored_name: str,
    ) -> None:
        path = self.resolve_file(
            procedure_id=procedure_id,
            storage_subdir=storage_subdir,
            stored_name=stored_name,
        )
        path.unlink(missing_ok=True)


def _extract_google_drive_file_id(parsed: ParseResult) -> str | None:
    """Extrai file id de links públicos do Google Drive."""
    parts = [part for part in (parsed.path or "").split("/") if part]
    if len(parts) >= 3 and parts[0] == "file" and parts[1] == "d":
        candidate = parts[2]
        if _GOOGLE_DRIVE_FILE_ID_RE.fullmatch(candidate):
            return candidate

    query = parse_qs(parsed.query or "")
    for key in ("id", "fileId"):
        values = query.get(key) or []
        if values and _GOOGLE_DRIVE_FILE_ID_RE.fullmatch(values[0]):
            return values[0]
    return None


def validate_external_video_url(url: str) -> tuple[str, str]:
    """Valida URL controlada de vídeo externo.

    Returns:
        (normalized_url, provider) onde provider ∈
        {youtube, vimeo, google_drive}.
    """
    raw = (url or "").strip()
    if not raw:
        raise GuiasMediaStorageError("URL do vídeo é obrigatória.")
    if len(raw) > 2000:
        raise GuiasMediaStorageError("URL do vídeo é muito longa.")

    parsed = urlparse(raw)
    if parsed.scheme != "https":
        raise GuiasMediaStorageError("URL do vídeo deve usar HTTPS.")
    host = (parsed.hostname or "").lower()
    if not host:
        raise GuiasMediaStorageError("URL do vídeo inválida.")

    for provider, hosts in _EXTERNAL_VIDEO_HOSTS.items():
        if host not in hosts:
            continue
        if provider == "google_drive":
            file_id = _extract_google_drive_file_id(parsed)
            if not file_id:
                raise GuiasMediaStorageError(
                    "URL do Google Drive inválida. Use um link público "
                    "do arquivo (ex.: /file/d/.../view ou open?id=...)."
                )
            normalized = f"https://drive.google.com/file/d/{file_id}/view"
            return normalized, provider
        return raw, provider

    raise GuiasMediaStorageError(
        "Provedor de vídeo não permitido. Use YouTube, Vimeo ou Google Drive."
    )
