from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from cipa_app.infrastructure.persistence.repositories.meeting_minute_repository import (
    MeetingMinuteRepository,
)


def test_resolve_actor_snapshot_guarda_id_nome_e_email():
    user_id = str(uuid4())
    user = SimpleNamespace(id=user_id, name="Robério Oliveira", email="roberio@delpi.com.br")
    with patch(
        "cipa_app.infrastructure.persistence.repositories.meeting_minute_repository.get_current_user",
        return_value=user,
    ):
        snapshot = MeetingMinuteRepository._resolve_actor_snapshot(user_id)

    assert str(snapshot["user_id"]) == user_id
    assert snapshot["name"] == "Robério Oliveira"
    assert snapshot["email"] == "roberio@delpi.com.br"


def test_resolve_actor_snapshot_ignora_usuario_diferente_da_request():
    with patch(
        "cipa_app.infrastructure.persistence.repositories.meeting_minute_repository.get_current_user",
        return_value=SimpleNamespace(
            id=str(uuid4()), name="Outro", email="outro@delpi.com.br"
        ),
    ):
        snapshot = MeetingMinuteRepository._resolve_actor_snapshot(str(uuid4()))

    assert snapshot["user_id"] is not None
    assert snapshot["name"] is None
    assert snapshot["email"] is None


def test_resolve_actor_snapshot_sem_usuario_autenticado():
    with patch(
        "cipa_app.infrastructure.persistence.repositories.meeting_minute_repository.get_current_user",
        return_value=None,
    ):
        snapshot = MeetingMinuteRepository._resolve_actor_snapshot(str(uuid4()))

    assert snapshot["name"] is None
    assert snapshot["email"] is None
