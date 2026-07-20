from types import SimpleNamespace
import io
import zipfile

import pytest

from cipa_app.application.use_cases.meeting_minutes_service import MeetingMinutesService


class _Repo:
    def __init__(self):
        self.participants = None

    def create_minute(self, **_kwargs):
        return {"id": "00000000-0000-0000-0000-000000000001", "unit_code": "01"}

    def replace_participants(self, minute_id, unit_code, participants, actor_user_id):
        self.participants = {
            "minute_id": minute_id,
            "unit_code": unit_code,
            "participants": participants,
            "actor_user_id": actor_user_id,
        }


def test_create_persists_participants_in_initial_transaction_flow():
    service = MeetingMinutesService.__new__(MeetingMinutesService)
    service.repo = _Repo()
    service._assert = lambda *_args: None
    service.get_detail = lambda _user, minute_id: {"minute": {"id": minute_id}}
    user = SimpleNamespace(id="00000000-0000-0000-0000-000000000010")
    participants = [
        {
            "user_id": "00000000-0000-0000-0000-000000000011",
            "display_name": "Pessoa CIPA",
            "role_in_meeting": "president",
            "presence": "present",
            "is_external": False,
            "must_sign": True,
        }
    ]

    service.create(
        user,
        {
            "unit_code": "01",
            "title": "Ata ordinária",
            "meeting_type": "ordinary",
            "meeting_date": "2026-07-16",
            "start_time": "09:00",
            "end_time": "10:00",
            "location": "Sala CIPA",
            "participants": participants,
        },
    )

    assert service.repo.participants["participants"] == participants
    assert service.repo.participants["unit_code"] == "01"


def test_finalize_renders_pdf_with_validation_code_before_persisting(monkeypatch):
    captured = {}

    class Repo:
        def get_version(self, _minute_id):
            return {"content_hash": "hash-final"}

        def set_status(self, **kwargs):
            captured["status"] = kwargs
            return {"id": kwargs["minute_id"], "status": kwargs["status"]}

    class PdfStorage:
        def save(self, **kwargs):
            captured["pdf_storage"] = kwargs
            return "/data/final.pdf"

    service = MeetingMinutesService.__new__(MeetingMinutesService)
    service.repo = Repo()
    service.pdf_storage = PdfStorage()
    service._load_authorized = lambda *_args: {
        "id": "minute-1",
        "unit_code": "01",
        "status": "signed",
    }

    def render_pdf(minute, _version):
        captured["minute_pdf"] = minute
        return b"pdf"

    service._render_pdf = render_pdf
    monkeypatch.setattr("secrets.token_urlsafe", lambda _length: "VALIDA-123")

    service.finalize(SimpleNamespace(id="actor-1"), "minute-1")

    assert captured["minute_pdf"]["validation_code"] == "VALIDA-123"
    assert captured["minute_pdf"]["final_content_hash"] == "hash-final"
    assert captured["status"]["extra"]["validation_code"] == "VALIDA-123"


def test_signature_image_checks_minute_and_reads_current_signature(monkeypatch):
    class Repo:
        def get_minute(self, _minute_id):
            return {"id": "minute-1", "unit_code": "01"}

        def get_signature(self, minute_id, signature_id):
            assert minute_id == "minute-1"
            assert signature_id == "signature-1"
            return {"image_path": "/data/signature.png"}

    class Storage:
        def read(self, path):
            assert path == "/data/signature.png"
            return b"\x89PNG\r\n\x1a\n"

    service = MeetingMinutesService.__new__(MeetingMinutesService)
    service.repo = Repo()
    service.signature_storage = Storage()
    monkeypatch.setattr(
        "cipa_app.application.use_cases.meeting_minutes_service.perms.has_unit_read_access",
        lambda _user, unit_code: unit_code == "01",
    )

    raw = service.signature_image(SimpleNamespace(id="reader"), "minute-1", "signature-1")

    assert raw.startswith(b"\x89PNG")


def test_soft_delete_allows_partially_signed_and_keeps_repository_history():
    class Repo:
        def soft_delete(self, minute_id, actor_user_id):
            return {
                "id": minute_id,
                "status": "partially_signed",
                "deleted_at": "2026-07-16T18:00:00+00:00",
                "actor_user_id": actor_user_id,
            }

    service = MeetingMinutesService.__new__(MeetingMinutesService)
    service.repo = Repo()
    service._load_authorized = lambda *_args: {
        "id": "minute-1",
        "unit_code": "01",
        "status": "partially_signed",
    }

    result = service.soft_delete(SimpleNamespace(id="actor-1"), "minute-1")

    assert result["minute"]["deleted_at"] is not None
    assert result["minute"]["actor_user_id"] == "actor-1"


def test_create_version_with_none_content_preserves_current_version():
    """Regressão: reabrir ata (payload só com change_reason e campos None) não pode zerar o conteúdo."""
    captured = {}

    class Repo:
        def get_version(self, _minute_id):
            return {
                "agenda_html": "<p>Pauta original</p>",
                "body_html": "<p>Texto original da ata</p>",
                "decisions_html": "<p>Decisões</p>",
                "pending_html": "<p>Pendências</p>",
                "observations_html": "<p>Observações</p>",
            }

        def create_new_version(self, **kwargs):
            captured.update(kwargs)
            return {"minute": {"id": kwargs["minute_id"]}, "version": {"id": "v2"}}

    service = MeetingMinutesService.__new__(MeetingMinutesService)
    service.repo = Repo()
    service._load_authorized = lambda *_args: {
        "id": "minute-1",
        "unit_code": "01",
        "status": "partially_signed",
        "title": "Ata",
        "meeting_type": "ordinary",
        "meeting_date": "2026-07-16",
        "start_time": None,
        "end_time": None,
        "location": None,
    }

    payload = {
        "change_reason": "Ata reaberta para edição pelo gestor.",
        "agenda_html": None,
        "body_html": None,
        "decisions_html": None,
        "pending_html": None,
        "observations_html": None,
    }
    service.create_version(SimpleNamespace(id="actor-1"), "minute-1", payload)

    assert "Texto original da ata" in captured["body_html"]
    assert "Pauta original" in captured["agenda_html"]
    assert "Decisões" in captured["decisions_html"]
    assert "Pendências" in captured["pending_html"]
    assert "Observações" in captured["observations_html"]


def _viewer(minute_status: str, signer: dict | None):
    service = MeetingMinutesService.__new__(MeetingMinutesService)
    minute = {"id": "minute-1", "status": minute_status}
    signers = [signer] if signer else []
    return service._build_viewer_context(
        SimpleNamespace(id="user-1"), minute, signers
    )


def test_viewer_context_can_sign_only_while_pending():
    viewer = _viewer(
        "partially_signed", {"user_id": "user-1", "status": "pending"}
    )
    assert viewer["is_signer"] is True
    assert viewer["has_signed"] is False
    assert viewer["can_sign_now"] is True


def test_viewer_context_blocks_after_signed():
    viewer = _viewer(
        "partially_signed", {"user_id": "user-1", "status": "signed"}
    )
    assert viewer["has_signed"] is True
    assert viewer["can_sign_now"] is False


def test_viewer_context_blocks_non_signer_and_non_signable_status():
    assert _viewer("partially_signed", {"user_id": "other", "status": "pending"})[
        "can_sign_now"
    ] is False
    assert _viewer("draft", {"user_id": "user-1", "status": "pending"})[
        "can_sign_now"
    ] is False


def test_export_filtered_pdfs_builds_zip_with_unique_names():
    class Repo:
        pass

    service = MeetingMinutesService.__new__(MeetingMinutesService)
    service.repo = Repo()
    service._assert = lambda *_args: None
    service.list_minutes = lambda _user, _filters: {
        "items": [
            {"id": "minute-1", "minute_number": "2026/001"},
            {"id": "minute-2", "minute_number": "2026/001"},
        ]
    }
    calls = []

    def export_pdf(_user, minute_id):
        calls.append(minute_id)
        return b"%PDF-" + minute_id.encode(), "ata-cipa-2026-001.pdf"

    service.export_pdf = export_pdf

    raw, filename = service.export_filtered_pdfs(
        SimpleNamespace(id="actor-1"),
        {"unit_code": "01", "status": "partially_signed"},
    )

    assert filename.startswith("atas-cipa-01-")
    assert filename.endswith(".zip")
    assert calls == ["minute-1", "minute-2"]
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = archive.namelist()
    assert names == ["ata-cipa-2026-001.pdf", "ata-cipa-2026-001-2.pdf"]


def test_export_filtered_pdfs_requires_unit_and_non_empty_result():
    service = MeetingMinutesService.__new__(MeetingMinutesService)
    service._assert = lambda *_args: None
    service.list_minutes = lambda *_args: {"items": []}

    with pytest.raises(ValueError, match="unidade"):
        service.export_filtered_pdfs(SimpleNamespace(id="actor-1"), {})

    with pytest.raises(LookupError, match="Nenhuma ata"):
        service.export_filtered_pdfs(
            SimpleNamespace(id="actor-1"), {"unit_code": "01"}
        )


@pytest.mark.parametrize("status", ["signed", "finalized"])
def test_soft_delete_rejects_signed_or_finalized(status):
    service = MeetingMinutesService.__new__(MeetingMinutesService)
    service._load_authorized = lambda *_args: {
        "id": "minute-1",
        "unit_code": "01",
        "status": status,
    }

    with pytest.raises(ValueError, match="assinadas ou finalizadas"):
        service.soft_delete(SimpleNamespace(id="actor-1"), "minute-1")
