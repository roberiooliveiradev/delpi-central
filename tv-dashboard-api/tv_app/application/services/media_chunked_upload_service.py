from __future__ import annotations

import json
import shutil
import uuid
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from tv_app.application.services.media_storage_service import (
    MediaStorageService,
    MediaValidationError,
)
from tv_app.application.services.tv_dashboard_content_service import media_setting_int
from tv_app.config import settings

_META_NAME = "meta.json"
_DEFAULT_EDGE_CHUNK_BYTES = 90 * 1024 * 1024


class MediaChunkedUploadError(ValueError):
    """Sessão de upload em chunks inválida ou incompleta."""


class MediaChunkedUploadService:
    """
    Upload multipart em partes para contornar limite de body na borda (Cloudflare ~100 MB).

    Sessão em disco sob `{media_dir}/.uploads/{upload_id}/` — metadado + chunk_NNNNN.part.
    """

    def __init__(self, storage: MediaStorageService | None = None) -> None:
        self._storage = storage or MediaStorageService()
        self._uploads_root = Path(settings.TV_DASHBOARD_MEDIA_UPLOAD_DIR) / ".uploads"

    def edge_chunk_bytes(self) -> int:
        configured = media_setting_int("maxEdgeChunkBytes", _DEFAULT_EDGE_CHUNK_BYTES)
        return max(1 * 1024 * 1024, min(configured, 95 * 1024 * 1024))

    def _session_dir(self, upload_id: str) -> Path:
        return self._uploads_root / upload_id

    def _meta_path(self, upload_id: str) -> Path:
        return self._session_dir(upload_id) / _META_NAME

    def _chunk_path(self, upload_id: str, index: int) -> Path:
        return self._session_dir(upload_id) / f"chunk_{index:05d}.part"

    def _read_meta(self, upload_id: str) -> dict[str, Any]:
        path = self._meta_path(upload_id)
        if not path.is_file():
            raise MediaChunkedUploadError("Sessão de upload não encontrada.")
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise MediaChunkedUploadError("Metadados da sessão inválidos.") from exc
        if not isinstance(raw, dict):
            raise MediaChunkedUploadError("Metadados da sessão inválidos.")
        return raw

    def _write_meta(self, upload_id: str, meta: dict[str, Any]) -> None:
        path = self._meta_path(upload_id)
        path.write_text(json.dumps(meta, ensure_ascii=True, separators=(",", ":")), encoding="utf-8")

    def create_session(
        self,
        *,
        playlist_id: str,
        original_name: str | None,
        mime_type: str | None,
        size_bytes: int,
    ) -> dict[str, Any]:
        kind, normalized = self._storage.validate_kind_and_mime(mime_type)
        max_bytes = self._storage._max_bytes(kind)
        if size_bytes <= 0:
            raise MediaValidationError("Arquivo vazio.")
        if size_bytes > max_bytes:
            limit_mb = max(1, max_bytes // (1024 * 1024))
            raise MediaValidationError(f"Arquivo acima do limite de {limit_mb} MB.")

        chunk_size = self.edge_chunk_bytes()
        chunk_count = (size_bytes + chunk_size - 1) // chunk_size
        upload_id = uuid.uuid4().hex
        session_dir = self._session_dir(upload_id)
        session_dir.mkdir(parents=True, exist_ok=False)
        meta = {
            "uploadId": upload_id,
            "playlistId": playlist_id,
            "originalName": original_name,
            "mimeType": normalized,
            "mediaKind": kind,
            "sizeBytes": size_bytes,
            "chunkSizeBytes": chunk_size,
            "chunkCount": chunk_count,
            "received": [],
        }
        self._write_meta(upload_id, meta)
        return {
            "uploadId": upload_id,
            "chunkSizeBytes": chunk_size,
            "chunkCount": chunk_count,
            "sizeBytes": size_bytes,
        }

    async def save_chunk(
        self,
        *,
        upload_id: str,
        playlist_id: str,
        chunk_index: int,
        chunks: AsyncIterator[bytes],
    ) -> dict[str, Any]:
        meta = self._read_meta(upload_id)
        if str(meta.get("playlistId")) != playlist_id:
            raise MediaChunkedUploadError("Sessão de upload não pertence a esta playlist.")
        chunk_count = int(meta["chunkCount"])
        chunk_size = int(meta["chunkSizeBytes"])
        if chunk_index < 0 or chunk_index >= chunk_count:
            raise MediaChunkedUploadError("Índice de parte inválido.")

        expected_total = int(meta["sizeBytes"])
        expected_chunk = min(chunk_size, expected_total - chunk_index * chunk_size)
        if expected_chunk <= 0:
            raise MediaChunkedUploadError("Índice de parte inválido.")
        target = self._chunk_path(upload_id, chunk_index)
        temp = self._session_dir(upload_id) / f".chunk_{chunk_index:05d}.writing"
        size = 0
        try:
            with temp.open("wb") as out:
                async for piece in chunks:
                    if not piece:
                        continue
                    size += len(piece)
                    if size > expected_chunk:
                        raise MediaChunkedUploadError(
                            f"Parte excede o tamanho esperado ({expected_chunk} bytes)."
                        )
                    out.write(piece)
            if size != expected_chunk:
                raise MediaChunkedUploadError("Parte com tamanho inesperado.")
            temp.replace(target)
        except Exception:
            if temp.exists():
                temp.unlink(missing_ok=True)
            raise

        received = set(int(i) for i in (meta.get("received") or []) if isinstance(i, int) or str(i).isdigit())
        received.add(chunk_index)
        meta["received"] = sorted(received)
        self._write_meta(upload_id, meta)
        return {
            "uploadId": upload_id,
            "chunkIndex": chunk_index,
            "receivedCount": len(received),
            "chunkCount": chunk_count,
        }

    async def complete(
        self,
        *,
        upload_id: str,
        playlist_id: str,
    ) -> tuple[str, str, str, int, str | None]:
        """
        Concatena partes e grava no storage final.
        Retorna (stored_name, mime, kind, size_bytes, original_name).
        """
        meta = self._read_meta(upload_id)
        if str(meta.get("playlistId")) != playlist_id:
            raise MediaChunkedUploadError("Sessão de upload não pertence a esta playlist.")

        chunk_count = int(meta["chunkCount"])
        expected_size = int(meta["sizeBytes"])
        mime_type = str(meta["mimeType"])
        original_name = meta.get("originalName")
        if isinstance(original_name, str):
            original_name_out: str | None = original_name
        else:
            original_name_out = None

        received = set(int(i) for i in (meta.get("received") or []))
        missing = [i for i in range(chunk_count) if i not in received]
        if missing:
            raise MediaChunkedUploadError(
                f"Upload incompleto: faltam {len(missing)} parte(s)."
            )

        async def iter_parts() -> AsyncIterator[bytes]:
            for index in range(chunk_count):
                path = self._chunk_path(upload_id, index)
                if not path.is_file():
                    raise MediaChunkedUploadError(f"Parte {index} ausente no disco.")
                with path.open("rb") as handle:
                    while True:
                        block = handle.read(1024 * 1024)
                        if not block:
                            break
                        yield block

        try:
            stored_name, mime, kind, size_bytes = await self._storage.save_stream(
                chunks=iter_parts(),
                mime_type=mime_type,
                expected_size=expected_size,
            )
        except MediaValidationError:
            raise
        finally:
            self.abort(upload_id=upload_id, playlist_id=playlist_id, ignore_missing=True)

        if size_bytes != expected_size:
            self._storage.delete(stored_name)
            raise MediaChunkedUploadError("Tamanho final diverge do anunciado no início do upload.")
        return stored_name, mime, kind, size_bytes, original_name_out

    def abort(self, *, upload_id: str, playlist_id: str, ignore_missing: bool = False) -> None:
        try:
            meta = self._read_meta(upload_id)
        except MediaChunkedUploadError:
            if ignore_missing:
                return
            raise
        if str(meta.get("playlistId")) != playlist_id:
            raise MediaChunkedUploadError("Sessão de upload não pertence a esta playlist.")
        session_dir = self._session_dir(upload_id)
        if session_dir.is_dir():
            shutil.rmtree(session_dir, ignore_errors=True)
