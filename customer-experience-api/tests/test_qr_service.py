import pytest

pytest.importorskip("qrcode")

from cx_app.application.services.qr_service import (  # noqa: E402
    QrService,
    build_public_url,
)


def test_generate_persists_png(tmp_path):
    service = QrService(base_dir=str(tmp_path))
    filename = service.generate(token="abc123")
    assert filename == "abc123.png"
    content = service.read(filename)
    assert content is not None
    assert content[:8] == b"\x89PNG\r\n\x1a\n"


def test_build_public_url_uses_welcome_path(monkeypatch):
    from cx_app import config

    monkeypatch.setattr(config.settings, "PUBLIC_BASE_URL", "https://minhadelpi.com.br/")
    monkeypatch.setattr(config.settings, "CX_PUBLIC_WELCOME_PATH", "/welcome")
    assert build_public_url("tok") == "https://minhadelpi.com.br/welcome/tok"
