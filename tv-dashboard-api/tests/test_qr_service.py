from tv_app.application.services.qr_service import build_public_presentation_url, render_qr_png


def test_render_qr_png():
    png = render_qr_png("http://localhost/p/tv-dashboard/present/test-token")
    assert png[:8] == b"\x89PNG\r\n\x1a\n"


def test_build_public_url():
    url = build_public_presentation_url("abc123")
    assert "/p/tv-dashboard/present/abc123" in url
