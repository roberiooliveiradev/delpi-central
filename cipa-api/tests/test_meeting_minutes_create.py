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
