"""Testes de storage — Guias e Procedimentos (mídias/anexos)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import Request

from app.application.services.guias_procedimentos.guide_media_file_response import (
    build_file_response,
)
from app.application.services.guias_procedimentos.guide_media_storage import (
    GuiasMediaStorageError,
    GuiasProcedimentosMediaStorage,
    validate_external_video_url,
)


def test_save_and_resolve_image(tmp_path: Path) -> None:
    storage = GuiasProcedimentosMediaStorage(base_dir=str(tmp_path))
    saved = storage.save(
        procedure_id="proc-1",
        kind="image",
        original_name="foto.PNG",
        content=b"png-bytes",
        mime_type="image/png",
    )
    assert saved["storage_subdir"] == "images"
    path = storage.resolve_file(
        procedure_id="proc-1",
        storage_subdir="images",
        stored_name=str(saved["stored_name"]),
    )
    assert path.read_bytes() == b"png-bytes"
    assert (tmp_path / "procedures" / "proc-1" / "images").is_dir()


def test_reject_invalid_image_mime(tmp_path: Path) -> None:
    storage = GuiasProcedimentosMediaStorage(base_dir=str(tmp_path))
    with pytest.raises(GuiasMediaStorageError, match="Formato de imagem"):
        storage.save(
            procedure_id="proc-1",
            kind="image",
            original_name="x.pdf",
            content=b"%PDF",
            mime_type="application/pdf",
        )


def test_reject_invalid_extension(tmp_path: Path) -> None:
    storage = GuiasProcedimentosMediaStorage(base_dir=str(tmp_path))
    with pytest.raises(GuiasMediaStorageError, match="Extensão"):
        storage.save(
            procedure_id="proc-1",
            kind="image",
            original_name="x.exe",
            content=b"abc",
            mime_type="image/png",
        )


def test_reject_oversized_attachment(tmp_path: Path) -> None:
    storage = GuiasProcedimentosMediaStorage(base_dir=str(tmp_path))
    with pytest.raises(GuiasMediaStorageError, match="20 MB"):
        storage.validate_upload(
            kind="attachment",
            mime_type="application/pdf",
            size_bytes=21 * 1024 * 1024,
            original_name="a.pdf",
        )


def test_path_traversal_rejected(tmp_path: Path) -> None:
    storage = GuiasProcedimentosMediaStorage(base_dir=str(tmp_path))
    saved = storage.save(
        procedure_id="proc-1",
        kind="attachment",
        original_name="doc.pdf",
        content=b"%PDF-1.4",
        mime_type="application/pdf",
    )
    with pytest.raises(GuiasMediaStorageError, match="inválido"):
        storage.resolve_file(
            procedure_id="proc-1",
            storage_subdir="attachments",
            stored_name=f"../{saved['stored_name']}",
        )


def test_external_video_youtube_and_vimeo() -> None:
    url, provider = validate_external_video_url(
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )
    assert provider == "youtube"
    assert url.startswith("https://")
    _, provider2 = validate_external_video_url("https://vimeo.com/123456")
    assert provider2 == "vimeo"


def test_external_video_google_drive_normalizes_public_link() -> None:
    file_id = "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
    normalized, provider = validate_external_video_url(
        f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"
    )
    assert provider == "google_drive"
    assert normalized == f"https://drive.google.com/file/d/{file_id}/view"

    normalized2, provider2 = validate_external_video_url(
        f"https://drive.google.com/open?id={file_id}"
    )
    assert provider2 == "google_drive"
    assert normalized2 == f"https://drive.google.com/file/d/{file_id}/view"


def test_external_video_rejects_google_drive_folder_or_home() -> None:
    with pytest.raises(GuiasMediaStorageError, match="Google Drive"):
        validate_external_video_url("https://drive.google.com/drive/folders/abc")
    with pytest.raises(GuiasMediaStorageError, match="Google Drive"):
        validate_external_video_url("https://drive.google.com/")


def test_external_video_rejects_http_and_unknown() -> None:
    with pytest.raises(GuiasMediaStorageError, match="HTTPS"):
        validate_external_video_url("http://www.youtube.com/watch?v=x")
    with pytest.raises(GuiasMediaStorageError, match="não permitido"):
        validate_external_video_url("https://example.com/video.mp4")


def test_range_partial_content(tmp_path: Path) -> None:
    file_path = tmp_path / "clip.mp4"
    file_path.write_bytes(b"0123456789ABCDEF")
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/file",
        "raw_path": b"/file",
        "query_string": b"",
        "headers": [(b"range", b"bytes=0-3")],
        "client": ("127.0.0.1", 123),
        "server": ("test", 80),
    }
    request = Request(scope)
    response = build_file_response(
        path=file_path,
        request=request,
        media_type="video/mp4",
        filename="clip.mp4",
        enable_range=True,
    )
    assert response.status_code == 206
    assert response.headers["Content-Range"] == "bytes 0-3/16"
    assert response.headers["Content-Length"] == "4"
    assert response.headers["Accept-Ranges"] == "bytes"
