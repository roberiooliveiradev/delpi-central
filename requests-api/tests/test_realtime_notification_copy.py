from requests_app.application.services.realtime_notification_copy import (
    build_realtime_transition_notification,
)


def test_realtime_transition_notification_is_friendly():
    notice = build_realtime_transition_notification(
        workflow={
            "initialStatus": "submitted",
            "journeyProgress": {
                "stages": [
                    {"id": "intake", "statuses": ["submitted"]},
                    {"id": "service", "statuses": ["in_progress"]},
                ]
            },
        },
        to_status="in_progress",
        request_number="REQ-1",
        actor_name="Ana",
    )
    assert "in_progress" not in notice["message"]
    assert "→" not in notice["message"]
    assert "REQ-1" in notice["message"]
    assert notice["title"]
