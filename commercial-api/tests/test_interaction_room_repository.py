from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from commercial_app.domain.ports.interaction_message_repository_port import (
    InteractionMessageRepositoryPort,
)
from commercial_app.domain.ports.interaction_room_repository_port import (
    InteractionRoomRepositoryPort,
)
from commercial_app.infrastructure.persistence.repositories.postgres_interaction_message_repository import (
    PostgresInteractionMessageRepository,
)
from commercial_app.infrastructure.persistence.repositories.postgres_interaction_room_repository import (
    PostgresInteractionRoomRepository,
)


ROOM_SRC = (
    Path(__file__).resolve().parents[1]
    / "commercial_app"
    / "infrastructure"
    / "persistence"
    / "repositories"
    / "postgres_interaction_room_repository.py"
).read_text(encoding="utf-8")

MESSAGE_SRC = (
    Path(__file__).resolve().parents[1]
    / "commercial_app"
    / "infrastructure"
    / "persistence"
    / "repositories"
    / "postgres_interaction_message_repository.py"
).read_text(encoding="utf-8")


def test_postgres_repos_implement_ports() -> None:
    assert issubclass(PostgresInteractionRoomRepository, InteractionRoomRepositoryPort)
    assert issubclass(
        PostgresInteractionMessageRepository,
        InteractionMessageRepositoryPort,
    )


def test_room_repo_sql_targets_interaction_tables() -> None:
    assert "commercial.interaction_rooms" in ROOM_SRC
    assert "commercial.interaction_room_members" in ROOM_SRC
    assert "find_entity_room" in ROOM_SRC
    assert "ON CONFLICT (room_id, user_id)" in ROOM_SRC


def test_message_repo_sql_targets_messages_mentions_reactions() -> None:
    assert "commercial.interaction_messages" in MESSAGE_SRC
    assert "commercial.interaction_mentions" in MESSAGE_SRC
    assert "commercial.interaction_reactions" in MESSAGE_SRC
    assert "commercial.interaction_pins" in MESSAGE_SRC
    assert "%s::jsonb" in MESSAGE_SRC


def test_composer_wires_interaction_repo_builders() -> None:
    composer = (
        Path(__file__).resolve().parents[1]
        / "commercial_app"
        / "composition"
        / "commercial_composer.py"
    ).read_text(encoding="utf-8")
    assert "def build_interaction_room_repository" in composer
    assert "def build_interaction_message_repository" in composer
    assert "PostgresInteractionRoomRepository" in composer
    assert "PostgresInteractionMessageRepository" in composer


def test_room_repo_maps_find_entity_stub() -> None:
    now = datetime.now(timezone.utc)
    room_id = uuid4()
    repo = PostgresInteractionRoomRepository()

    def fake_fetch_one(query: str, params=None):  # noqa: ANN001
        assert "kind = 'entity'" in query
        return {
            "id": room_id,
            "kind": "entity",
            "entity_type": params[0],
            "entity_key": params[1],
            "group_id": None,
            "title": "Pedido",
            "created_by_user_id": "u1",
            "created_at": now,
            "updated_at": now,
            "deleted_at": None,
        }

    repo.fetch_one = fake_fetch_one  # type: ignore[method-assign]
    room = repo.find_entity_room(entity_type="order", entity_key="01|1")
    assert room is not None
    assert room.id == room_id
    assert room.entity_key == "01|1"
