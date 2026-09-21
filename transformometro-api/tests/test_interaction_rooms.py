from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from tm_app.application.security.authorization_policy import AuthorizationDenied
from tm_app.application.security.transformometro_permissions import (
    ACCESS_PERMISSION,
    MANAGE_PERMISSION,
)
from tm_app.application.use_cases.manage_interaction_rooms import InteractionRoomUseCases
from tm_app.domain.services.interaction_room_rules import (
    MAX_MESSAGE_LENGTH,
    normalize_message_content,
    normalize_processo_id,
)
from tm_app.infrastructure.persistence.repositories.interaction_room_repository import (
    InMemoryInteractionRoomRepository,
)

USER = "11111111-1111-1111-1111-111111111111"
OTHER = "22222222-2222-2222-2222-222222222222"
PROCESS = "33333333-3333-3333-3333-333333333333"
OTHER_PROCESS = "44444444-4444-4444-4444-444444444444"

# operationIds do baseline: list_transformometro_interaction_rooms
# open_transformometro_interaction_room
# get_transformometro_interaction_room
# list_transformometro_interaction_messages
# post_transformometro_interaction_message
# patch_transformometro_interaction_message
# delete_transformometro_interaction_message
# toggle_transformometro_interaction_reaction
# pin_transformometro_interaction_message
# unpin_transformometro_interaction_message
# mark_transformometro_interaction_room_read
# list_transformometro_interaction_attachments
# upload_transformometro_interaction_attachment
# download_transformometro_interaction_attachment
# delete_transformometro_interaction_attachment


def _user(*, permissions=None, user_id=USER):
    return SimpleNamespace(
        id=user_id,
        permissions=[ACCESS_PERMISSION] if permissions is None else permissions,
        is_superadmin=False,
    )


def _cases() -> tuple[InteractionRoomUseCases, InMemoryInteractionRoomRepository]:
    repo = InMemoryInteractionRoomRepository()
    repo.processes.add(PROCESS)
    return InteractionRoomUseCases(repo), repo


def test_message_rules_reject_blank_and_oversize():
    with pytest.raises(ValueError):
        normalize_message_content("   \n  ")
    with pytest.raises(ValueError):
        normalize_message_content("a" * (MAX_MESSAGE_LENGTH + 1))
    kept = normalize_message_content("  linha\n\nseguinte  ")
    assert kept == "linha\n\nseguinte"
    assert normalize_processo_id(PROCESS) == PROCESS
    with pytest.raises(ValueError):
        normalize_processo_id("nao-uuid")


def test_one_room_per_process_and_missing_context():
    cases, _repo = _cases()
    first = cases.open_for_process(_user(), PROCESS)
    second = cases.open_for_process(_user(), PROCESS)
    assert first.id == second.id
    assert first.processo_id == PROCESS
    with pytest.raises(LookupError):
        cases.open_for_process(_user(), OTHER_PROCESS)


def test_post_then_list_is_authoritative_and_ordered():
    cases, _repo = _cases()
    room = cases.open_for_process(_user(), PROCESS)
    first = cases.post_message(_user(), room.id, "primeira")
    second = cases.post_message(_user(), room.id, "segunda")
    listed = cases.list_messages(_user(), room.id, limit=50)
    assert [item["id"] for item in listed["items"]] == [first.id, second.id]
    assert listed["items"][0]["author_user_id"] == USER
    assert listed["items"][0]["content"] == "primeira"
    assert listed["has_more"] is False
    page = cases.list_messages(_user(), room.id, limit=1)
    assert [item["content"] for item in page["items"]] == ["segunda"]
    assert page["has_more"] is True
    with pytest.raises(LookupError):
        cases.get_room(_user(), "55555555-5555-5555-5555-555555555555")


def test_authz_access_manage_and_anonymous():
    cases, _repo = _cases()
    cases.open_for_process(_user(), PROCESS)
    with pytest.raises(AuthorizationDenied) as missing:
        cases.list_rooms(_user(permissions=[]))
    assert missing.value.status_code == 403
    with pytest.raises(AuthorizationDenied) as manage_only:
        cases.post_message(_user(permissions=[MANAGE_PERMISSION]), "x", "oi")
    assert manage_only.value.status_code == 403
    with pytest.raises(AuthorizationDenied) as anonymous:
        cases.list_rooms(None)
    assert anonymous.value.status_code == 401


def test_http_read_back_and_validation():
    from tm_app.interface.http.routes import interaction_room_routes

    cases, _repo = _cases()
    request = SimpleNamespace(state=SimpleNamespace(user=_user()))
    with patch.object(interaction_room_routes, "_rooms", cases):
        opened = interaction_room_routes.open_interaction_room(
            request,
            interaction_room_routes.OpenInteractionRoomBody(processo_id=PROCESS),
        )
        missing = interaction_room_routes.open_interaction_room(
            request,
            interaction_room_routes.OpenInteractionRoomBody(processo_id=OTHER_PROCESS),
        )
        forbidden = interaction_room_routes.list_interaction_rooms(
            SimpleNamespace(state=SimpleNamespace(user=_user(permissions=[]))),
        )
        manage_only = interaction_room_routes.list_interaction_rooms(
            SimpleNamespace(state=SimpleNamespace(user=_user(permissions=[MANAGE_PERMISSION]))),
        )
        anonymous = interaction_room_routes.list_interaction_rooms(
            SimpleNamespace(state=SimpleNamespace(user=None)),
        )
        room_id = json.loads(opened.body)["data"]["id"]
        posted = interaction_room_routes.post_interaction_message(
            request,
            room_id,
            interaction_room_routes.PostInteractionMessageBody(content="  texto da sala  "),
        )
        listed = interaction_room_routes.list_interaction_messages(request, room_id)
        unknown = interaction_room_routes.get_interaction_room(
            request,
            "55555555-5555-5555-5555-555555555555",
        )
    assert opened.status_code == 200
    assert missing.status_code == 404
    assert forbidden.status_code == 403
    assert manage_only.status_code == 403
    assert anonymous.status_code == 401
    assert posted.status_code == 201
    listed_body = json.loads(listed.body)
    assert listed_body["data"]["items"][0]["content"] == "texto da sala"
    assert listed_body["data"]["items"][0]["author_user_id"] == USER
    assert unknown.status_code == 404
    with pytest.raises(ValidationError):
        interaction_room_routes.PostInteractionMessageBody(content="   ")


def test_reply_mention_reaction_pin_and_author_only_edit():
    cases, _repo = _cases()
    room = cases.open_for_process(_user(), PROCESS)
    root = cases.post_message(_user(), room.id, "raiz")
    with pytest.raises(ValueError):
        cases.post_message(
            _user(),
            room.id,
            "órfã",
            parent_id="55555555-5555-5555-5555-555555555555",
        )
    reply = cases.post_message(
        _user(),
        room.id,
        "resposta",
        parent_id=root.id,
        mentions=[{"user_id": OTHER, "label": "@Ana Silva", "email": "ana@example.com"}],
    )
    assert reply.parent_id == root.id
    assert reply.mentions[0].user_id == OTHER
    assert reply.mentions[0].label == "Ana Silva"
    assert "email" not in reply.to_dict()["mentions"][0]
    reacted = cases.toggle_reaction(_user(), room.id, root.id, "👍")
    assert any(item.code == "👍" and item.user_id == USER for item in reacted.reactions)
    cleared = cases.toggle_reaction(_user(), room.id, root.id, "👍")
    assert not any(item.code == "👍" and item.user_id == USER for item in cleared.reactions)
    pinned = cases.pin_message(_user(), room.id, root.id)
    assert pinned.pinned is True
    still = cases.pin_message(_user(), room.id, root.id)
    assert still.pinned is True
    unpinned = cases.unpin_message(_user(), room.id, root.id)
    assert unpinned.pinned is False
    with pytest.raises(PermissionError):
        cases.edit_message(_user(user_id=OTHER), room.id, root.id, "alheia")
    edited = cases.edit_message(_user(), room.id, root.id, "raiz nova")
    assert edited.content == "raiz nova"
    assert edited.edited_at is not None
    removed = cases.delete_message(_user(), room.id, reply.id)
    assert removed.to_dict()["content"] == ""
    assert removed.deleted_at is not None
    with pytest.raises(ValueError):
        cases.post_message(_user(), room.id, "em cima da removida", parent_id=reply.id)


def test_unread_cursor_and_mention_filter():
    cases, _repo = _cases()
    room = cases.open_for_process(_user(), PROCESS)
    cases.post_message(_user(), room.id, "olá")
    mine = cases.list_rooms(_user(), inbox_filter="unread")
    theirs = cases.list_rooms(_user(user_id=OTHER), inbox_filter="unread")
    assert mine == []
    assert [item.id for item in theirs] == [room.id]
    assert theirs[0].unread_count == 1
    cases.post_message(
        _user(),
        room.id,
        "chama a Ana",
        mentions=[{"user_id": OTHER, "label": "Ana"}],
    )
    mentioned = cases.list_rooms(_user(user_id=OTHER), inbox_filter="mentioned")
    assert [item.id for item in mentioned] == [room.id]
    assert cases.list_rooms(_user(), inbox_filter="mentioned") == []
    cases.mark_read(_user(user_id=OTHER), room.id)
    assert cases.list_rooms(_user(user_id=OTHER), inbox_filter="unread") == []
    assert cases.list_rooms(_user(user_id=OTHER), inbox_filter="mentioned") == []
    with pytest.raises(ValueError):
        cases.list_rooms(_user(), inbox_filter="murais")


def test_attachment_rules_and_author_read_back(tmp_path, monkeypatch):
    from tm_app.infrastructure.storage import interaction_attachment_storage as storage_module

    monkeypatch.setattr(storage_module, "MAX_ATTACHMENT_BYTES", 8)
    storage = storage_module.InteractionAttachmentStorage(str(tmp_path))
    with pytest.raises(ValueError):
        storage.save(room_id="sala", original_name="vazio.png", content=b"", mime_type="image/png")
    with pytest.raises(ValueError):
        storage.save(room_id="sala", original_name="grande.png", content=b"123456789", mime_type="image/png")
    with pytest.raises(ValueError):
        storage.save(room_id="sala", original_name="virus.exe", content=b"1234", mime_type="application/x-msdownload")
    cases, _repo = _cases()
    cases._storage = storage
    room = cases.open_for_process(_user(), PROCESS)
    message = cases.post_message(_user(), room.id, "segue arquivo")
    saved = cases.add_attachment(
        _user(),
        room.id,
        message.id,
        file_name="foto.png",
        content=b"1234",
        mime_type="image/png",
    )
    listed = cases.list_messages(_user(), room.id)
    attachment = listed["items"][0]["attachments"][0]
    assert attachment["id"] == saved.id
    assert attachment["file_name"] == "foto.png"
    assert attachment["byte_size"] == 4
    assert "stored_name" not in attachment
    shared = cases.list_attachments(_user(), room.id)
    assert [item.id for item in shared] == [saved.id]
    path, name, mime = cases.open_attachment(_user(), room.id, saved.id)
    assert path.is_file() and name == "foto.png" and mime == "image/png"
    with pytest.raises(ValueError):
        storage.resolve_file(room_id="..", stored_name="foto.png")
    with pytest.raises(PermissionError):
        cases.delete_attachment(_user(user_id=OTHER), room.id, saved.id)
    cases.delete_attachment(_user(), room.id, saved.id)
    assert cases.list_attachments(_user(), room.id) == []
    assert not path.is_file()


def test_http_capabilities_keep_authz():
    from tm_app.interface.http.routes import interaction_room_routes

    cases, _repo = _cases()
    request = SimpleNamespace(state=SimpleNamespace(user=_user()))
    with patch.object(interaction_room_routes, "_rooms", cases):
        opened = interaction_room_routes.open_interaction_room(
            request,
            interaction_room_routes.OpenInteractionRoomBody(processo_id=PROCESS),
        )
        room_id = json.loads(opened.body)["data"]["id"]
        posted = interaction_room_routes.post_interaction_message(
            request,
            room_id,
            interaction_room_routes.PostInteractionMessageBody(content="texto"),
        )
        message_id = json.loads(posted.body)["data"]["id"]
        edited = interaction_room_routes.patch_interaction_message(
            request,
            room_id,
            message_id,
            interaction_room_routes.EditInteractionMessageBody(content="texto novo"),
        )
        reacted = interaction_room_routes.toggle_interaction_reaction(
            request,
            room_id,
            message_id,
            interaction_room_routes.ReactionBody(code="ok"),
        )
        forbidden = interaction_room_routes.patch_interaction_message(
            SimpleNamespace(state=SimpleNamespace(user=_user(permissions=[MANAGE_PERMISSION]))),
            room_id,
            message_id,
            interaction_room_routes.EditInteractionMessageBody(content="nao"),
        )
        anonymous = interaction_room_routes.download_interaction_attachment(
            SimpleNamespace(state=SimpleNamespace(user=None)),
            room_id,
            "55555555-5555-5555-5555-555555555555",
        )
        unread = interaction_room_routes.list_interaction_rooms(
            SimpleNamespace(state=SimpleNamespace(user=_user(user_id=OTHER))),
            inbox_filter="unread",
        )
    assert edited.status_code == 200
    assert json.loads(edited.body)["data"]["content"] == "texto novo"
    assert reacted.status_code == 200
    assert json.loads(reacted.body)["data"]["reactions"][0]["code"] == "ok"
    assert forbidden.status_code == 403
    assert anonymous.status_code == 401
    assert json.loads(unread.body)["data"]["items"][0]["id"] == room_id
