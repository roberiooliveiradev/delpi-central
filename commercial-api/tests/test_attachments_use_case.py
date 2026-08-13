from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from commercial_app.application.services.attachment_storage import AttachmentStorage
from commercial_app.application.use_cases.manage_attachments import ManageAttachmentsUseCase
from commercial_app.domain.entities.attachment import CommercialAttachment
from commercial_app.domain.entities.task import CommercialTask


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


def _task(*, assignee: str = "u1") -> CommercialTask:
    now = datetime.now(timezone.utc)
    return CommercialTask(
        id=uuid4(),
        title="Follow-up",
        description=None,
        task_type="follow_up",
        status="open",
        priority="normal",
        due_at=now,
        completed_at=None,
        assignee_user_id=assignee,
        created_by_user_id=assignee,
        customer_code="0001",
        customer_store="01",
        created_at=now,
        updated_at=now,
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
