from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.domain.services.chat_drawing_library_service import ChatDrawingLibraryService


@pytest.fixture()
def library_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DELPI_API_URL", "http://api-delpi.test")
    monkeypatch.setenv("CHAT_ATTACHMENT_STORAGE_PATH", str(tmp_path))


def test_fetch_pdf_downloads_and_caches(library_env, tmp_path: Path) -> None:
    pdf_bytes = b"%PDF-1.4 library-test"

    metadata_response = MagicMock()
    metadata_response.status_code = 200
    metadata_response.headers = {"content-type": "application/json"}
    metadata_response.json.return_value = {
        "data": {
            "product_code": "90262957",
            "filename": "90262957.pdf",
            "found": True,
        }
    }

    pdf_response = MagicMock()
    pdf_response.status_code = 200
    pdf_response.content = pdf_bytes

    with patch(
        "app.domain.services.chat_drawing_library_service.requests.get",
        side_effect=[metadata_response, pdf_response],
    ) as get_mock:
        result = ChatDrawingLibraryService.fetch_pdf(
            product_code="90262957",
            access_token="token-123",
        )

    assert result is not None
    assert result.filename == "90262957.pdf"
    assert Path(result.storage_path).read_bytes() == pdf_bytes
    assert get_mock.call_count == 2
    assert get_mock.call_args_list[1].kwargs["headers"]["Accept"] == "application/pdf"


def test_fetch_pdf_returns_none_when_metadata_missing(library_env) -> None:
    metadata_response = MagicMock()
    metadata_response.status_code = 404

    with patch(
        "app.domain.services.chat_drawing_library_service.requests.get",
        return_value=metadata_response,
    ):
        result = ChatDrawingLibraryService.fetch_pdf(product_code="99999999")

    assert result is None


def test_fetch_pdf_falls_back_to_service_token_on_user_auth_failure(
    library_env, tmp_path: Path
) -> None:
    pdf_bytes = b"%PDF-1.4 library-fallback"

    denied = MagicMock()
    denied.status_code = 403

    metadata_response = MagicMock()
    metadata_response.status_code = 200
    metadata_response.headers = {"content-type": "application/json"}
    metadata_response.json.return_value = {
        "data": {
            "product_code": "90263396",
            "filename": "90263396.pdf",
            "found": True,
        }
    }

    pdf_response = MagicMock()
    pdf_response.status_code = 200
    pdf_response.content = pdf_bytes

    with patch(
        "app.domain.services.chat_drawing_library_service.requests.get",
        side_effect=[denied, metadata_response, pdf_response],
    ) as get_mock:
        result = ChatDrawingLibraryService.fetch_pdf(
            product_code="90263396",
            access_token="user-token-denied",
        )

    assert result is not None
    assert result.product_code == "90263396"
    assert get_mock.call_count == 3
