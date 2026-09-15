import asyncio
import tempfile
from pathlib import Path

import pytest

from tv_app.application.services.media_chunked_upload_service import (
    MediaChunkedUploadError,
    MediaChunkedUploadService,
)
from tv_app.application.services.media_storage_service import MediaStorageService, MediaValidationError


async def _chunks(data: bytes, size: int = 8):
    for i in range(0, len(data), size):
        yield data[i : i + size]


def test_chunked_upload_completes_across_parts(monkeypatch):
    async def run() -> None:
        with tempfile.TemporaryDirectory() as tmp:
            monkeypatch.setenv("TV_DASHBOARD_MEDIA_UPLOAD_DIR", tmp)
            from tv_app.config import settings

            settings.TV_DASHBOARD_MEDIA_UPLOAD_DIR = tmp
            storage = MediaStorageService(base_dir=tmp)
            service = MediaChunkedUploadService(storage=storage)
            monkeypatch.setattr(service, "edge_chunk_bytes", lambda: 10)

            payload = b"0123456789ABCDEFGHIJ"  # 20 bytes → 2 chunks
            session = service.create_session(
                playlist_id="pl-1",
                original_name="clip.mp4",
                mime_type="video/mp4",
                size_bytes=len(payload),
            )
            assert session["chunkCount"] == 2
            assert session["chunkSizeBytes"] == 10

            await service.save_chunk(
                upload_id=session["uploadId"],
                playlist_id="pl-1",
                chunk_index=0,
                chunks=_chunks(payload[:10]),
            )
            await service.save_chunk(
                upload_id=session["uploadId"],
                playlist_id="pl-1",
                chunk_index=1,
                chunks=_chunks(payload[10:]),
            )
            stored, mime, kind, size, original = await service.complete(
                upload_id=session["uploadId"],
                playlist_id="pl-1",
            )
            assert kind == "video"
            assert mime == "video/mp4"
            assert size == 20
            assert original == "clip.mp4"
            assert storage.read(stored) == payload
            assert not (Path(tmp) / ".uploads" / session["uploadId"]).exists()

    asyncio.run(run())


def test_chunked_upload_rejects_oversize_session(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setenv("TV_DASHBOARD_MEDIA_UPLOAD_DIR", tmp)
        from tv_app.config import settings

        settings.TV_DASHBOARD_MEDIA_UPLOAD_DIR = tmp
        storage = MediaStorageService(base_dir=tmp)
        service = MediaChunkedUploadService(storage=storage)
        monkeypatch.setattr(storage, "_max_bytes", lambda kind: 10 if kind == "video" else 10)
        with pytest.raises(MediaValidationError, match="limite"):
            service.create_session(
                playlist_id="pl-1",
                original_name="big.mp4",
                mime_type="video/mp4",
                size_bytes=11,
            )


def test_chunked_upload_rejects_incomplete(monkeypatch):
    async def run() -> None:
        with tempfile.TemporaryDirectory() as tmp:
            monkeypatch.setenv("TV_DASHBOARD_MEDIA_UPLOAD_DIR", tmp)
            from tv_app.config import settings

            settings.TV_DASHBOARD_MEDIA_UPLOAD_DIR = tmp
            storage = MediaStorageService(base_dir=tmp)
            service = MediaChunkedUploadService(storage=storage)
            monkeypatch.setattr(service, "edge_chunk_bytes", lambda: 10)
            session = service.create_session(
                playlist_id="pl-1",
                original_name="clip.mp4",
                mime_type="video/mp4",
                size_bytes=20,
            )
            await service.save_chunk(
                upload_id=session["uploadId"],
                playlist_id="pl-1",
                chunk_index=0,
                chunks=_chunks(b"0123456789"),
            )
            with pytest.raises(MediaChunkedUploadError, match="incompleto"):
                await service.complete(upload_id=session["uploadId"], playlist_id="pl-1")

    asyncio.run(run())
