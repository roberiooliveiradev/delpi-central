"""Volume persistente das micrografias metalográficas.

Metadado fica no PostgreSQL; o binário fica neste diretório montado no host.
"""

from __future__ import annotations

import hashlib
import re
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

from app.config import settings
from app.domain.engineering.metallographic_report import (
    IMAGE_SLOTS,
    ImageStorageError,
    ImageTooLargeError,
    InvalidImageError,
    UnsupportedImageError,
    validate_slot,
)

MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_EDGE_PX = 6000
_STORED_NAME = re.compile(r"^[a-f0-9]{32}\.(jpg|png)$")
_JPEG = {b"\xff\xd8\xff"}
_PNG = b"\x89PNG\r\n\x1a\n"


class MetallographicImageStorage:
    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir or settings.METALLOGRAPHIC_IMAGE_UPLOAD_DIR)

    def ensure_base(self) -> None:
        try:
            self.base_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise ImageStorageError("Armazenamento de imagens indisponível.") from exc

    def validate_and_normalize(
        self,
        content: bytes,
        *,
        declared_type: str | None,
    ) -> dict[str, object]:
        if not content:
            raise InvalidImageError("Arquivo de imagem vazio.")
        if len(content) > MAX_IMAGE_BYTES:
            raise ImageTooLargeError("A imagem excede o limite de 8 MB.")
        detected = _detect_type(content)
        declared = (declared_type or "").split(";", 1)[0].strip().lower()
        if declared in {"image/jpg", "image/pjpeg"}:
            declared = "image/jpeg"
        if declared and declared != detected:
            raise UnsupportedImageError("O tipo declarado não corresponde ao arquivo.")
        if detected not in {"image/jpeg", "image/png"}:
            raise UnsupportedImageError("Use imagem JPEG ou PNG.")
        try:
            probe = Image.open(BytesIO(content))
            probe.verify()
            image = ImageOps.exif_transpose(Image.open(BytesIO(content)))
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            raise InvalidImageError("A imagem está corrompida ou não é um arquivo válido.") from exc
        width, height = image.size
        if width < 1 or height < 1 or width > MAX_EDGE_PX or height > MAX_EDGE_PX:
            raise ImageTooLargeError(
                "A imagem deve ter entre 1 e 6000 pixels em cada lado."
            )
        if detected == "image/jpeg":
            if image.mode != "RGB":
                image = image.convert("RGB")
            out = BytesIO()
            image.save(out, format="JPEG", quality=90, optimize=True)
            extension = "jpg"
            content_type = "image/jpeg"
        else:
            if image.mode not in {"RGB", "RGBA", "L"}:
                image = image.convert("RGBA")
            out = BytesIO()
            image.save(out, format="PNG", optimize=True)
            extension = "png"
            content_type = "image/png"
        normalized = out.getvalue()
        if len(normalized) > MAX_IMAGE_BYTES:
            raise ImageTooLargeError("A imagem excede o limite de 8 MB.")
        return {
            "content": normalized,
            "content_type": content_type,
            "extension": extension,
            "size_bytes": len(normalized),
            "width": width,
            "height": height,
            "sha256": hashlib.sha256(normalized).hexdigest(),
        }

    def save(self, *, report_id: str, stored_name: str, content: bytes) -> None:
        self.ensure_base()
        path = self._path(report_id, stored_name)
        temporary = path.with_suffix(path.suffix + ".part")
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary.write_bytes(content)
            temporary.replace(path)
        except OSError as exc:
            temporary.unlink(missing_ok=True)
            raise ImageStorageError("Falha ao gravar a imagem.") from exc

    def read(self, *, report_id: str, stored_name: str) -> bytes:
        path = self._path(report_id, stored_name)
        if not path.is_file():
            raise ImageStorageError("Arquivo de imagem não encontrado.")
        try:
            return path.read_bytes()
        except OSError as exc:
            raise ImageStorageError("Falha ao ler a imagem.") from exc

    def delete(self, *, report_id: str, stored_name: str | None) -> None:
        if not stored_name:
            return
        try:
            path = self._path(report_id, stored_name)
        except ImageStorageError:
            return
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            raise ImageStorageError("Falha ao remover arquivo de imagem.") from exc

    def drop_unreferenced(self, *, report_id: str, referenced: set[str]) -> list[str]:
        folder = self._report_dir(report_id)
        if not folder.is_dir():
            return []
        removed: list[str] = []
        for path in folder.iterdir():
            if not path.is_file():
                continue
            if path.name.endswith(".part") or path.name not in referenced:
                try:
                    path.unlink(missing_ok=True)
                except OSError as exc:
                    raise ImageStorageError("Falha ao limpar arquivo órfão.") from exc
                removed.append(path.name)
        return removed

    def _report_dir(self, report_id: str) -> Path:
        token = str(report_id).strip().lower()
        if not re.fullmatch(r"[0-9a-f-]{36}", token):
            raise ImageStorageError("Identificador de relatório inválido.")
        base = self.base_dir.resolve()
        folder = (self.base_dir / token).resolve()
        if not str(folder).startswith(str(base)):
            raise ImageStorageError("Caminho de arquivo inválido.")
        return folder

    def _path(self, report_id: str, stored_name: str) -> Path:
        name = (stored_name or "").strip().lower()
        if _STORED_NAME.fullmatch(name) is None:
            raise ImageStorageError("Nome de arquivo inválido.")
        return self._report_dir(report_id) / name


def new_stored_name(extension: str) -> str:
    from uuid import uuid4

    ext = "jpg" if extension == "jpg" else "png"
    return f"{uuid4().hex}.{ext}"


def _detect_type(content: bytes) -> str:
    if content.startswith(_PNG):
        return "image/png"
    if any(content.startswith(prefix) for prefix in _JPEG):
        return "image/jpeg"
    raise UnsupportedImageError("Use imagem JPEG ou PNG.")


def assert_known_slot(slot: str) -> str:
    if slot not in IMAGE_SLOTS:
        return validate_slot(slot)
    return slot
