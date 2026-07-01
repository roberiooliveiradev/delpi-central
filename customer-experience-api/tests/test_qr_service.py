import pytest

pytest.importorskip("qrcode")

from cx_app.application.services.qr_service import (  # noqa: E402
    QrService,
    build_feedback_url,
    build_public_url,
)


def test_generate_persists_png(tmp_path):
    service = QrService(base_dir=str(tmp_path))
    filename = service.generate(token="abc123")
    assert filename == "abc123.png"
    content = service.read(filename)
    assert content is not None
    assert content[:8] == b"\x89PNG\r\n\x1a\n"


def test_generate_feedback_uses_distinct_filename(tmp_path):
    service = QrService(base_dir=str(tmp_path))
    thanks = service.generate(token="abc123")
    feedback = service.generate_feedback(token="abc123")
    assert thanks == "abc123.png"
    assert feedback == "abc123-feedback.png"
    assert thanks != feedback
    assert service.read(feedback) is not None


def test_build_public_url_uses_welcome_path(monkeypatch):
    from cx_app import config

    monkeypatch.setattr(config.settings, "PUBLIC_BASE_URL", "https://minhadelpi.com.br/")
    monkeypatch.setattr(config.settings, "CX_PUBLIC_WELCOME_PATH", "/welcome")
    assert build_public_url("tok") == "https://minhadelpi.com.br/welcome/tok"


def test_build_feedback_url_uses_feedback_path(monkeypatch):
    from cx_app import config

    monkeypatch.setattr(config.settings, "PUBLIC_BASE_URL", "https://minhadelpi.com.br")
    monkeypatch.setattr(
        config.settings, "CX_PUBLIC_FEEDBACK_PATH", "/p/customer-experience/feedback"
    )
    assert (
        build_feedback_url("tok")
        == "https://minhadelpi.com.br/p/customer-experience/feedback/tok"
    )
