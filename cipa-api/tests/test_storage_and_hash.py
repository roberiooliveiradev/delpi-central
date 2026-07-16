from cipa_app.application.services.content_hash_service import ContentHashService
from cipa_app.application.services.storage_services import (
    CipaStorageError,
    SignatureStorageService,
)


def test_content_hash_stable():
    payload = ContentHashService.build_version_payload(
        title="Ata",
        meeting_type="ordinary",
        meeting_date="2026-07-16",
        start_time=None,
        end_time=None,
        location="Sala",
        agenda_html="<p>a</p>",
        body_html="<p>b</p>",
        decisions_html="",
        pending_html="",
        observations_html="",
    )
    h1 = ContentHashService.hash_version_payload(payload)
    h2 = ContentHashService.hash_version_payload(payload)
    assert h1 == h2
    assert len(h1) == 64


def test_signature_storage_rejects_non_png(tmp_path):
    storage = SignatureStorageService(base_dir=str(tmp_path), max_bytes=1024)
    try:
        storage.save_png(unit_code="01", minute_id="x", raw=b"not-png")
        assert False, "should raise"
    except CipaStorageError:
        pass


def test_signature_storage_accepts_png(tmp_path):
    storage = SignatureStorageService(base_dir=str(tmp_path), max_bytes=1024)
    png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 20
    path = storage.save_png(unit_code="01", minute_id="m1", raw=png)
    assert path.endswith(".png")
