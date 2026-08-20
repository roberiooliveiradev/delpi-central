from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from commercial_app.application.services.attachment_storage import AttachmentStorage
from commercial_app.application.use_cases.manage_attachments import ManageAttachmentsUseCase
from commercial_app.domain.entities.attachment import CommercialAttachment
from commercial_app.domain.entities.task import CommercialTask
from commercial_app.domain.services.interaction_room_content_service import (
    InteractionRoomContentService,
)
from tests.test_interaction_message_use_case import (
    InMemoryInteractionMessageRepo,
    _open_room,
)
from tests.test_interaction_room_membership_use_case import InMemoryInteractionRoomRepo


class _MemoryTasks:
    def __init__(self, task: CommercialTask) -> None:
        self.task = task

    def list_for_assignee(self, **_kwargs):
        return [self.task]

    def list_for_assignees(self, **_kwargs):
        return [self.task]

    def list_by_status(self, **_kwargs):
        return [self.task]

    def get_by_id(self, task_id):
        return self.task if self.task.id == task_id else None

    def create(self, **_kwargs):
        raise NotImplementedError

    def complete(self, **_kwargs):
        raise NotImplementedError

    def update_due_at(self, **_kwargs):
        raise NotImplementedError

    def reassign(self, **_kwargs):
        raise NotImplementedError


class _MemoryAttachments:
    def __init__(self) -> None:
        self.items: list[CommercialAttachment] = []

    def list_for_owner(self, *, owner_type: str, owner_id: str, limit: int = 50):
        return [
            item
            for item in self.items
            if item.owner_type == owner_type and item.owner_id == owner_id
        ][:limit]

    def count_for_owners(self, *, owner_type: str, owner_ids):
        counts: dict[str, int] = {}
        for item in self.items:
            if item.owner_type != owner_type or item.owner_id not in owner_ids:
                continue
            counts[item.owner_id] = counts.get(item.owner_id, 0) + 1
        return counts

    def get_by_id(self, attachment_id):
        for item in self.items:
            if item.id == attachment_id:
                return item
        return None

    def create(self, **kwargs):
        record = CommercialAttachment(
            id=uuid4(),
            owner_type=kwargs["owner_type"],
            owner_id=kwargs["owner_id"],
            file_name=kwargs["file_name"],
            storage_key=kwargs["storage_key"],
            content_type=kwargs["content_type"],
            byte_size=kwargs["byte_size"],
            uploaded_by_user_id=kwargs["uploaded_by_user_id"],
            created_at=datetime.now(timezone.utc),
        )
        self.items.append(record)
        return record

    def delete(self, attachment_id):
        for index, item in enumerate(self.items):
            if item.id == attachment_id:
                return self.items.pop(index)
        return None


def _task(
    *,
    assignee: str = "u1",
    created_by: str | None = None,
    assignee_user_ids: tuple[str, ...] = (),
) -> CommercialTask:
    now = datetime.now(timezone.utc)
    primary = assignee_user_ids[0] if assignee_user_ids else assignee
    return CommercialTask(
        id=uuid4(),
        title="Follow-up",
        description=None,
        task_type="follow_up",
        status="open",
        priority="normal",
        due_at=now,
        completed_at=None,
        assignee_user_id=primary,
        created_by_user_id=created_by or primary,
        customer_code="0001",
        customer_store="01",
        created_at=now,
        updated_at=now,
        assignee_user_ids=assignee_user_ids,
    )


def test_upload_list_download_delete_attachment(tmp_path: Path) -> None:
    task = _task()
    repo = _MemoryAttachments()
    storage = AttachmentStorage(base_dir=str(tmp_path))
    uc = ManageAttachmentsUseCase(
        repository=repo,
        storage=storage,
        task_repository=_MemoryTasks(task),
    )

    uploaded = uc.upload(
        owner_type="task",
        owner_id=str(task.id),
        original_name="nota.pdf",
        content=b"%PDF-1.4 demo",
        mime_type="application/pdf",
        uploaded_by_user_id="u1",
    )
    assert uploaded.file_name.endswith("nota.pdf") or "nota" in uploaded.file_name
    assert (tmp_path / uploaded.storage_key).is_file()

    listed = uc.list(
        owner_type="task",
        owner_id=str(task.id),
        actor_user_id="u1",
    )
    assert len(listed) == 1
    assert listed[0].id == uploaded.id

    file_info = uc.get_file(attachment_id=uploaded.id, actor_user_id="u1")
    assert file_info.path.read_bytes().startswith(b"%PDF")

    deleted = uc.delete(attachment_id=uploaded.id, actor_user_id="u1")
    assert deleted["deleted"] is True
    assert uc.list(owner_type="task", owner_id=str(task.id), actor_user_id="u1") == []


def test_attachment_forbidden_for_other_user(tmp_path: Path) -> None:
    task = _task(assignee="u1")
    uc = ManageAttachmentsUseCase(
        repository=_MemoryAttachments(),
        storage=AttachmentStorage(base_dir=str(tmp_path)),
        task_repository=_MemoryTasks(task),
    )
    try:
        uc.upload(
            owner_type="task",
            owner_id=str(task.id),
            original_name="x.pdf",
            content=b"%PDF-1.4",
            mime_type="application/pdf",
            uploaded_by_user_id="u2",
        )
        assert False, "expected PermissionError"
    except PermissionError:
        pass


def test_secondary_assignee_can_list_attachments(tmp_path: Path) -> None:
    """Regressão: multi-responsável — só o primary estava autorizado (403 na fila)."""
    task = _task(
        assignee="u-primary",
        created_by="u-creator",
        assignee_user_ids=("u-primary", "u-secondary"),
    )
    repo = _MemoryAttachments()
    uc = ManageAttachmentsUseCase(
        repository=repo,
        storage=AttachmentStorage(base_dir=str(tmp_path)),
        task_repository=_MemoryTasks(task),
    )
    uploaded = uc.upload(
        owner_type="task",
        owner_id=str(task.id),
        original_name="nota.pdf",
        content=b"%PDF-1.4 demo",
        mime_type="application/pdf",
        uploaded_by_user_id="u-creator",
    )
    listed = uc.list(
        owner_type="task",
        owner_id=str(task.id),
        actor_user_id="u-secondary",
    )
    assert len(listed) == 1
    assert listed[0].id == uploaded.id


def test_rejects_unsupported_mime(tmp_path: Path) -> None:
    task = _task()
    uc = ManageAttachmentsUseCase(
        repository=_MemoryAttachments(),
        storage=AttachmentStorage(base_dir=str(tmp_path)),
        task_repository=_MemoryTasks(task),
    )
    try:
        uc.upload(
            owner_type="task",
            owner_id=str(task.id),
            original_name="x.exe",
            content=b"MZ",
            mime_type="application/x-msdownload",
            uploaded_by_user_id="u1",
        )
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_room_message_upload_uses_disk_subdir(tmp_path: Path) -> None:
    rooms = InMemoryInteractionRoomRepo()
    messages = InMemoryInteractionMessageRepo()
    room = _open_room(rooms)
    posted = messages.create_message(
        room_id=room.id,
        author_user_id="u1",
        message_kind="text",
        body_text="anexo",
    )
    repo = _MemoryAttachments()
    storage = AttachmentStorage(base_dir=str(tmp_path))
    uc = ManageAttachmentsUseCase(
        repository=repo,
        storage=storage,
        task_repository=_MemoryTasks(_task()),
        rooms=rooms,
        messages=messages,
    )
    uploaded = uc.upload(
        owner_type="room_message",
        owner_id=str(posted.id),
        original_name="proposta.pdf",
        content=b"%PDF-1.4 sala",
        mime_type="application/pdf",
        uploaded_by_user_id="u1",
    )
    assert uploaded.owner_type == "room_message"
    assert uploaded.storage_key.startswith(f"room_message/{posted.id}/")
    assert (tmp_path / uploaded.storage_key).is_file()
    listed = uc.list(
        owner_type="room_message",
        owner_id=str(posted.id),
        actor_user_id="u1",
    )
    assert [item.id for item in listed] == [uploaded.id]


def test_room_message_rejects_eleventh_attachment(tmp_path: Path) -> None:
    rooms = InMemoryInteractionRoomRepo()
    messages = InMemoryInteractionMessageRepo()
    room = _open_room(rooms)
    posted = messages.create_message(
        room_id=room.id,
        author_user_id="u1",
        message_kind="text",
        body_text="anexo",
    )
    repo = _MemoryAttachments()
    uc = ManageAttachmentsUseCase(
        repository=repo,
        storage=AttachmentStorage(base_dir=str(tmp_path)),
        task_repository=_MemoryTasks(_task()),
        rooms=rooms,
        messages=messages,
    )
    for index in range(10):
        uc.upload(
            owner_type="room_message",
            owner_id=str(posted.id),
            original_name=f"f{index}.pdf",
            content=b"%PDF",
            mime_type="application/pdf",
            uploaded_by_user_id="u1",
        )
    with pytest.raises(ValueError) as exc:
        uc.upload(
            owner_type="room_message",
            owner_id=str(posted.id),
            original_name="extra.pdf",
            content=b"%PDF",
            mime_type="application/pdf",
            uploaded_by_user_id="u1",
        )
    assert "10" in str(exc.value)


def test_room_message_rejects_invalid_owner_id(tmp_path: Path) -> None:
    uc = ManageAttachmentsUseCase(
        repository=_MemoryAttachments(),
        storage=AttachmentStorage(base_dir=str(tmp_path)),
        task_repository=_MemoryTasks(_task()),
    )
    try:
        uc.upload(
            owner_type="room_message",
            owner_id="not-a-uuid",
            original_name="x.pdf",
            content=b"%PDF-1.4",
            mime_type="application/pdf",
            uploaded_by_user_id="u1",
        )
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_room_message_allows_non_member(tmp_path: Path) -> None:
    rooms = InMemoryInteractionRoomRepo()
    messages = InMemoryInteractionMessageRepo()
    room = _open_room(rooms)
    posted = messages.create_message(
        room_id=room.id,
        author_user_id="u1",
        message_kind="text",
        body_text="anexo",
    )
    uc = ManageAttachmentsUseCase(
        repository=_MemoryAttachments(),
        storage=AttachmentStorage(base_dir=str(tmp_path)),
        task_repository=_MemoryTasks(_task()),
        rooms=rooms,
        messages=messages,
    )
    attachment = uc.upload(
        owner_type="room_message",
        owner_id=str(posted.id),
        original_name="x.pdf",
        content=b"%PDF-1.4",
        mime_type="application/pdf",
        uploaded_by_user_id="u2",
    )
    assert attachment.owner_type == "room_message"
