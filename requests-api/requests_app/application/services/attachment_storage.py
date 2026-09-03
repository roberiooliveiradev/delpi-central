from __future__ import annotations

import hashlib
import json
import mimetypes
import re
import uuid
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from requests_app.config import settings

_CONTENT_ROOT = Path(__file__).resolve().parents[2] / "content" / "pt-BR"
_SAFE_PART = re.compile(r"[^A-Za-z0-9._-]+")


@lru_cache(maxsize=1)
def _storage_bundle() -> dict:
    return json.loads((_CONTENT_ROOT / "storage.json").read_text(encoding="utf-8"))


def storage_error(code: str, **kwargs: str) -> str:
    template = str((_storage_bundle().get("errors") or {}).get(code) or code)
    return template.format(**kwargs) if kwargs else template


class StorageError(ValueError):
    def __init__(self, code: str, **kwargs: str) -> None:
        self.code = code
        super().__init__(storage_error(code, **kwargs))


@dataclass(frozen=True, slots=True)
class StoredFile:
    original_name: str
    stored_name: str
    storage_key: str
    mime_type: str
    size_bytes: int
    checksum_sha256: str


class _BaseFileStorage:
    kind: str = "attachment"

    def __init__(self, base_dir: str | None = None) -> None:
        cfg = _storage_bundle().get(self.kind) or {}
        self.max_bytes = int(cfg.get("maxBytes") or 25 * 1024 * 1024)
        self.allowed_mimes = {
            str(item).lower() for item in (cfg.get("allowedMimeTypes") or [])
        }
        self.base_dir = Path(base_dir or self._default_dir())
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _default_dir(self) -> str:
        raise NotImplementedError

    def validate_upload(self, *, mime_type: str | None, size_bytes: int) -> None:
        if size_bytes <= 0:
            raise StorageError("emptyFile")
        if size_bytes > self.max_bytes:
            max_mb = max(1, self.max_bytes // (1024 * 1024))
            raise StorageError("tooLarge", maxMb=str(max_mb))
        normalized = (mime_type or "").lower().split(";")[0].strip()
        if normalized not in self.allowed_mimes:
            raise StorageError("invalidMime")

    def save(
        self,
        *,
        request_id: str,
        original_name: str,
        content: bytes,
        mime_type: str | None,
        artifact_kind: str | None = None,
    ) -> StoredFile:
        self.validate_upload(mime_type=mime_type, size_bytes=len(content))
        extension = Path(original_name).suffix.lower()
        if not extension:
            extension = (
                mimetypes.guess_extension((mime_type or "").split(";")[0].strip())
                or ".bin"
            )
        if extension == ".jpe":
            extension = ".jpg"
        display_name = Path(original_name).name.strip() or f"file{extension}"
        display_name = _SAFE_PART.sub("_", display_name) or f"file{extension}"
        stored_name = f"{uuid.uuid4().hex}{extension}"
        safe_request = _SAFE_PART.sub("_", (request_id or "").strip()) or "request"
        if self.kind == "artifact":
            kind = _SAFE_PART.sub("_", (artifact_kind or "generic").strip()) or "generic"
            rel_dir = f"{safe_request}/artifacts/{kind}"
        else:
            rel_dir = safe_request
        target_dir = self.base_dir / rel_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / stored_name
        target_path.write_bytes(content)
        checksum = hashlib.sha256(content).hexdigest()
        return StoredFile(
            original_name=display_name,
            stored_name=stored_name,
            storage_key=f"{rel_dir}/{stored_name}",
            mime_type=(mime_type or "application/octet-stream").split(";")[0].strip(),
            size_bytes=len(content),
            checksum_sha256=checksum,
        )

    def resolve_file(self, *, storage_key: str) -> Path:
        base = self.base_dir.resolve()
        normalized_key = storage_key.strip().lstrip("/")
        if not normalized_key or ".." in normalized_key.split("/"):
            raise StorageError("invalidPath")
        path = (self.base_dir / normalized_key).resolve()
        if not str(path).startswith(str(base)):
            raise StorageError("invalidPath")
        if not path.is_file():
            raise StorageError("notFound")
        return path


class AttachmentStorage(_BaseFileStorage):
    kind = "attachment"

    def _default_dir(self) -> str:
        return settings.MY_REQUESTS_ATTACHMENT_UPLOAD_DIR


class ArtifactStorage(_BaseFileStorage):
    kind = "artifact"

    def _default_dir(self) -> str:
        return settings.MY_REQUESTS_ARTIFACT_UPLOAD_DIR
