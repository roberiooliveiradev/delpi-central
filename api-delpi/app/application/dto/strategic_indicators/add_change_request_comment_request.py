from dataclasses import dataclass


@dataclass
class AddStrategicIndicatorsChangeRequestCommentRequest:
    change_request_id: str
    comment_text: str
    actor_user_id: str | None = None
    actor_email: str | None = None