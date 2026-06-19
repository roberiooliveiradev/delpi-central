import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.application.services.drawings.drawing_pdf_library_storage import (
    DrawingPdfLibraryStorage,
    DrawingPdfLibraryStorageError,
    DrawingPdfMatch,
)
from app.interface.http.routes.product_drawing_routes import (
    get_product_drawing_metadata,
    get_product_drawing_pdf,
    list_product_drawings,
)


@pytest.fixture()
def sample_match(tmp_path: Path) -> DrawingPdfMatch:
    pdf_path = tmp_path / "90262957.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 route-test")
    stat = pdf_path.stat()
    from datetime import datetime, timezone

    return DrawingPdfMatch(
        product_code="90262957",
        filename="90262957.pdf",
        path=pdf_path,
        size_bytes=stat.st_size,
        modified_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
        revision=None,
        variant_suffix=None,
    )


@patch("app.interface.http.routes.product_drawing_routes.build_get_product_drawing_metadata_use_case")
def test_get_product_drawing_metadata_returns_meta(mock_build_use_case, sample_match) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = sample_match.to_metadata_dict()
    mock_build_use_case.return_value = use_case

    response = get_product_drawing_metadata("90262957")
    body = json.loads(response.body.decode())

    assert body["meta"]["operationId"] == "get_product_drawing"
    assert body["meta"]["entity"] == "product_drawing"
    assert body["meta"]["shape"] == "scalar"
    assert body["data"]["filename"] == "90262957.pdf"
    assert body["data"]["found"] is True


@patch("app.interface.http.routes.product_drawing_routes.build_get_product_drawing_metadata_use_case")
def test_get_product_drawing_metadata_not_found(mock_build_use_case) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "found": False,
        "product_code": "99999999",
        "message": "Desenho PDF não encontrado para o produto informado.",
    }
    mock_build_use_case.return_value = use_case

    response = get_product_drawing_metadata("99999999")
    assert response.status_code == 404


@patch("app.interface.http.routes.product_drawing_routes.build_get_product_drawing_pdf_use_case")
def test_get_product_drawing_pdf_returns_file(mock_build_use_case, sample_match) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = (sample_match.path, sample_match.filename)
    mock_build_use_case.return_value = use_case

    response = get_product_drawing_pdf("90262957")

    assert response.status_code == 200
    assert response.media_type == "application/pdf"
    assert sample_match.path.read_bytes().startswith(b"%PDF")
    assert response.headers["content-disposition"] == 'inline; filename="90262957.pdf"'


@patch("app.interface.http.routes.product_drawing_routes.build_get_product_drawing_pdf_use_case")
def test_get_product_drawing_pdf_not_found(mock_build_use_case) -> None:
    use_case = MagicMock()
    use_case.execute.side_effect = DrawingPdfLibraryStorageError(
        "Desenho PDF não encontrado para o produto informado."
    )
    mock_build_use_case.return_value = use_case

    response = get_product_drawing_pdf("99999999")
    assert response.status_code == 404


@patch("app.interface.http.routes.product_drawing_routes.build_list_product_drawings_use_case")
def test_list_product_drawings_returns_meta(mock_build_use_case) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "items": [
            {
                "product_code": "90262957",
                "filename": "90262957.pdf",
                "file_kind": "exact",
                "revision": None,
                "variant_suffix": None,
                "size_bytes": 100,
                "modified_at": "2026-01-01T00:00:00+00:00",
                "media_type": "application/pdf",
                "drawing_metadata_path": "/products/90262957/drawing",
                "drawing_pdf_path": "/products/90262957/drawing/pdf",
            }
        ],
        "page": 1,
        "page_size": 50,
        "total": 1,
        "total_pages": 1,
        "summary": {
            "library_available": True,
            "library_dir": "/drawing-pdfs",
            "scanned_files": 1,
            "matched_files": 1,
            "filters_applied": {},
        },
    }
    mock_build_use_case.return_value = use_case

    response = list_product_drawings()
    body = json.loads(response.body.decode())

    assert body["meta"]["operationId"] == "list_product_drawings"
    assert body["meta"]["entity"] == "product_drawing_catalog"
    assert body["meta"]["shape"] == "paged_list"
    assert body["meta"]["pagination"]["total"] == 1
    assert body["data"]["items"][0]["product_code"] == "90262957"
