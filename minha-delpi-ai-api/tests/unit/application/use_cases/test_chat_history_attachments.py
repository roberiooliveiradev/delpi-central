from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from app.application.use_cases.get_chat_history_use_case import GetChatHistoryUseCase


@dataclass(frozen=True)
class FakeSession:
    id: object
    user_id: object


@dataclass(frozen=True)
class FakeMessage:
    id: object
    session_id: object
    role: str
    content: str
    metadata: dict
    created_at: object


class FakeRepository:
    def __init__(self, user_id, session_id):
        self.user_id = user_id
        self.session_id = session_id

    def get_session_by_id(self, session_id):
        return FakeSession(id=session_id, user_id=self.user_id)

    def list_messages_by_session(self, session_id):
        return [
            FakeMessage(
                id=uuid4(),
                session_id=session_id,
                role="user",
                content="Veja o arquivo",
                metadata={
                    "attachments": [
                        {
                            "id": "att-1",
                            "original_filename": "teste.txt",
                        }
                    ]
                },
                created_at=datetime.now(timezone.utc),
            )
        ]


class FakeFeedbackRepository:
    def list_feedback_by_message_ids(self, *, message_ids, user_id):
        return {}


def test_history_returns_message_attachments_from_metadata():
    user_id = uuid4()
    session_id = uuid4()

    use_case = GetChatHistoryUseCase(
        FakeRepository(user_id, session_id),
        feedback_repository=FakeFeedbackRepository(),
    )

    result = use_case.execute(user_id=str(user_id), session_id=str(session_id))

    assert result[0].metadata["attachments"][0]["original_filename"] == "teste.txt"
