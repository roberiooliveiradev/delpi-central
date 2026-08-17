from types import SimpleNamespace
from pathlib import Path

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
        self.invalidated_signer_ids: list[str] = []

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

    def get_signature(self, _minute_id, signature_id):
        return next((s for s in self.signatures if s["id"] == signature_id), None)

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

    def invalidate_open_invites(self, *, signer_id: str) -> int:
        self.invalidated_signer_ids.append(signer_id)
        return 1

    def create_invite(self, **kwargs):
        return {"id": "inv1", "consumed_at": None, **kwargs}

    def get_invite_by_token_hash(self, _token_hash):
        return None

    def consume_invite(self, invite_id):
        return {"id": invite_id, "consumed_at": "now"}

    def get_signer(self, signer_id):
        return next((s for s in self.signers if s["id"] == signer_id), None)


def test_create_send_sign_happy_path_and_invalid_finalize():
    repo = FakeRepo()
    service = MeetingMinutesService(repo)
    service.notifications = SimpleNamespace(
        notify_sign_pending=lambda **_: True,
        notify_minute_signed=lambda **_: True,
        notify_minute_refused=lambda **_: True,
    )
    service.sign_pending_mail = SimpleNamespace(notify_signers=lambda **_: 1)
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
    assert repo.invalidated_signer_ids == ["s1"]
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


def test_sign_only_can_pending_detail_and_signature_image(tmp_path):
    from tm_app.application.security import transformometro_permissions as perms

    repo = FakeRepo()
    repo.minute = {
        "id": "m1",
        "minute_number": "2026/001",
        "status": "awaiting_signatures",
        "current_version_id": "v1",
        "unit_code": "01",
        "title": "Kickoff",
        "meeting_type": "ordinary",
        "meeting_date": "2026-07-28",
    }
    repo.version = {"id": "v1", "version_number": 1, "content_hash": "abc", "title": "Kickoff"}
    repo.signers = [
        {"id": "s1", "user_id": "signer-1", "status": "pending", "display_name": "Ana"},
    ]
    image_path = tmp_path / "sig.png"
    image_path.write_bytes(b"\x89PNG")
    repo.signatures = [{"id": "sig1", "image_path": str(image_path)}]
    repo.list_minutes = lambda **_: ([{"id": "m1"}], 1)

    service = MeetingMinutesService(repo)
    service.signature_storage = SimpleNamespace(read=lambda path: Path(path).read_bytes())
    signer = SimpleNamespace(
        id="signer-1",
        is_superadmin=False,
        permissions=[perms.TRANSFORMOMETRO_ATAS_SIGN],
    )

    pending = service.pending_signatures(signer)
    assert pending["total"] == 1
    detail = service.get_detail(signer, "m1")
    assert detail["viewer"]["is_signer"] is True
    assert service.signature_image(signer, "m1", "sig1").startswith(b"\x89PNG")

    with pytest.raises(PermissionError, match="consultar atas"):
        service.list_minutes(signer, {"limit": 10, "offset": 0})


def test_sign_only_cannot_manage():
    from tm_app.application.security import transformometro_permissions as perms

    repo = FakeRepo()
    repo.minute = {
        "id": "m1",
        "minute_number": "2026/001",
        "status": "draft",
        "current_version_id": "v1",
        "unit_code": "01",
        "title": "Kickoff",
    }
    service = MeetingMinutesService(repo)
    signer = SimpleNamespace(
        id="signer-1",
        is_superadmin=False,
        permissions=[perms.TRANSFORMOMETRO_ATAS_SIGN],
    )
    with pytest.raises(PermissionError, match="Sem permissão"):
        service.send_for_signature(signer, "m1")
