from types import SimpleNamespace

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
