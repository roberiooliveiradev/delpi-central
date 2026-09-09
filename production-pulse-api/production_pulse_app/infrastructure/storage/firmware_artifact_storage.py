"""Persistent storage for OTA firmware binaries (metadata lives in Postgres)."""

from __future__ import annotations

import hashlib
import re
import uuid
from dataclasses import dataclass
from pathlib import Path

from production_pulse_app.config import settings

_SAFE_SEGMENT_RE = re.compile(r"[^a-zA-Z0-9._-]+")


class FirmwareArtifactStorageError(ValueError):
    """Invalid or missing firmware artifact on disk."""


@dataclass(frozen=True)
class SavedFirmwareArtifact:
    relative_path: str
    sha256: str
    size_bytes: int


def _safe_segment(value: str, *, max_len: int = 64) -> str:
    cleaned = _SAFE_SEGMENT_RE.sub("-", (value or "").strip()).strip("-._")
    if not cleaned:
        cleaned = "unknown"
    return cleaned[:max_len]


class FirmwareArtifactStorage:
    def __init__(self, base_dir: str | None = None, max_bytes: int | None = None) -> None:
        self._base_dir_override = base_dir
        self._max_bytes_override = max_bytes

    @property
    def base_dir(self) -> Path:
        return Path(self._base_dir_override or settings.PP_FIRMWARE_UPLOAD_DIR)

    @property
    def max_bytes(self) -> int:
        if self._max_bytes_override is not None:
            return self._max_bytes_override
        return settings.PP_FIRMWARE_MAX_BYTES

    def save(
        self,
        *,
        firmware_key: str,
        version: str,
        raw: bytes,
        filename_hint: str | None = None,
    ) -> SavedFirmwareArtifact:
        if not raw:
            raise FirmwareArtifactStorageError("empty_artifact")
        if len(raw) > self.max_bytes:
            raise FirmwareArtifactStorageError("artifact_too_large")

        sha256 = hashlib.sha256(raw).hexdigest()
        folder = self.base_dir / _safe_segment(firmware_key) / _safe_segment(version)
        folder.mkdir(parents=True, exist_ok=True)

        suffix = ""
        if filename_hint:
            suffix = Path(filename_hint).suffix.lower()
            if suffix and not re.fullmatch(r"\.[a-z0-9]{1,8}", suffix):
                suffix = ""
        if suffix and suffix not in {".bin"}:
            raise FirmwareArtifactStorageError("artifact_bad_extension")
        name = f"{uuid.uuid4().hex}{suffix or '.bin'}"
        path = folder / name
        path.write_bytes(raw)
        relative = str(path.relative_to(self.base_dir)).replace("\\", "/")
        return SavedFirmwareArtifact(
            relative_path=relative,
            sha256=sha256,
            size_bytes=len(raw),
        )

    def delete_relative(self, relative_path: str) -> None:
        try:
            file_path = self.absolute_path(relative_path)
        except FirmwareArtifactStorageError:
            return
        if file_path.is_file():
            file_path.unlink(missing_ok=True)

    def absolute_path(self, relative_path: str) -> Path:
        base = self.base_dir.resolve()
        file_path = (self.base_dir / relative_path).resolve()
        try:
            file_path.relative_to(base)
        except ValueError as exc:
            raise FirmwareArtifactStorageError("invalid_artifact_path") from exc
        return file_path

    def read(self, relative_path: str) -> bytes:
        file_path = self.absolute_path(relative_path)
        if not file_path.is_file():
            raise FirmwareArtifactStorageError("artifact_not_found")
        return file_path.read_bytes()

    def open_path(self, relative_path: str) -> Path:
        file_path = self.absolute_path(relative_path)
        if not file_path.is_file():
            raise FirmwareArtifactStorageError("artifact_not_found")
        return file_path
