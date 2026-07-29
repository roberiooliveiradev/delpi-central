from types import SimpleNamespace

import pytest

from tm_app.application.services.content_hash_service import ContentHashService
from tm_app.application.services.meeting_minutes_service import MeetingMinutesService


class FakeRepo:
    def __init__(self):
        self.minute = None
        self.version = None
        self.signers = []
        self.signatures = []
        self.participants = []

    def create_minute(self, **data):
        self.minute = {
            "id": "m1",
            "minute_number": "2026/001",
            "status": "draft",
            "current_version_id": "v1",
            "unit_code": data.get("unit_code", "01"),
            **data,
        }
        self.version = {"id": "v1", "version_number": 1, "content_hash": data.get("content_hash"), **data}
        return self.minute

    def get_minute(self, _):
        return self.minute

    def get_version(self, _, version_id=None):
        return self.version

    def list_participants(self, _):
        return self.participants

    def list_versions(self, _):
        return [self.version] if self.version else []

    def list_signers(self, _):
        return self.signers

    def list_signatures(self, _):
        return self.signatures

    def replace_participants(self, minute_id, unit_code, participants, actor_user_id):
        self.participants = list(participants)
        return self.participants

    def replace_signers(self, **kwargs):
        self.signers = [
            {"id": f"s{index}", "status": "pending", **item}
            for index, item in enumerate(kwargs["signers"], start=1)
        ]
        return self.signers

    def get_signer_for_user(self, _, user_id):
        return next((s for s in self.signers if s["user_id"] == user_id), None)

    def mark_signer_viewed(self, signer_id):
        for signer in self.signers:
            if signer["id"] == signer_id and signer["status"] == "pending":
                signer["status"] = "viewed"
                return signer
        return next((s for s in self.signers if s["id"] == signer_id), None)

    def set_status(self, *, status, **_):
        self.minute["status"] = status
        return self.minute

    def register_signature(self, **kwargs):
        signature = {"id": "sig1", **kwargs}
        self.signatures.append(signature)
        self.signers[0]["status"] = "signed"
        return {
            "signature": signature,
            "duplicate": False,
            "signed_count": 1,
            "required_count": 1,
        }


def test_create_send_sign_happy_path_and_invalid_finalize():
    repo = FakeRepo()
    service = MeetingMinutesService(repo)
    service.notifications = SimpleNamespace(send=lambda **_: True)
    service.signature_storage = SimpleNamespace(save_png=lambda **_: "/tmp/signature.png")
    user = SimpleNamespace(id="u1", is_superadmin=True, permissions=[])
    created = service.create(
        user,
        {
            "unit_code": "01",
            "title": "Kickoff",
            "meeting_date": "2026-07-28",
            "participants": [
                {
                    "user_id": "u1",
                    "display_name": "Ana",
                    "must_sign": True,
                    "role_in_meeting": "chair",
                }
            ],
        },
    )
    assert created["minute"]["status"] == "draft"
    assert len(repo.signers) == 1
    service.send_for_signature(user, "m1")
    assert repo.minute["status"] == "awaiting_signatures"
    signed = service.sign(
        user,
        "m1",
        png_bytes=b"png",
        display_name_confirmed="Ana",
        terms_accepted=True,
        client_ip=None,
        user_agent=None,
        session_id=None,
        idempotency_key=None,
    )
    assert signed["minute"]["status"] == "signed"
    repo.minute["status"] = "draft"
    with pytest.raises(ValueError, match="Transição inválida"):
        service.finalize(user, "m1")


def test_content_hash_is_stable():
    payload = ContentHashService.build_version_payload(
        title="Ata",
        meeting_type="ordinary",
        meeting_date="2026-07-28",
        start_time=None,
        end_time=None,
        location="Sala A",
        agenda_html="<p>Pauta</p>",
        body_html="",
        decisions_html="",
        pending_html="",
        observations_html="",
    )
    first = ContentHashService.hash_version_payload(payload)
    second = ContentHashService.hash_version_payload(payload)
    assert first == second
    assert len(first) == 64
