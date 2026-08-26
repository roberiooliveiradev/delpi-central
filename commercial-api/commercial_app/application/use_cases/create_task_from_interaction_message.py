"""Cria tarefa do Meu Dia a partir de mensagem da sala de interação."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from commercial_app.application.services.attachment_storage import AttachmentStorage
from commercial_app.application.use_cases.manage_interaction_messages import (
    ManageInteractionMessagesUseCase,
    PostInteractionMessageInput,
)
from commercial_app.application.use_cases.manage_worklist import (
    CreateTaskInput,
    ManageWorklistUseCase,
)
from commercial_app.domain.entities.interaction_room import InteractionMessage
from commercial_app.domain.entities.task import CommercialTask
from commercial_app.domain.ports.attachment_repository_port import AttachmentRepositoryPort
from commercial_app.domain.ports.interaction_message_repository_port import (
    InteractionMessageRepositoryPort,
)
from commercial_app.domain.ports.interaction_room_repository_port import (
    InteractionRoomRepositoryPort,
)
from commercial_app.domain.ports.task_repository_port import TaskRepositoryPort
from commercial_app.domain.services.interaction_message_markdown_attachments_service import (
    InteractionMessageMarkdownAttachmentsService,
)
from commercial_app.domain.services.interaction_room_access_service import (
    InteractionRoomAccessService,
)
from commercial_app.domain.services.interaction_room_content_service import (
    InteractionRoomContentService,
)


@dataclass(frozen=True)
class CreateTaskFromInteractionMessageInput:
    room_id: UUID
    message_id: UUID
    actor_user_id: str
    description: str | None = None
    assignee_user_id: str | None = None
    assignee_user_ids: tuple[str, ...] | None = None
    priority: str = "normal"
    task_type: str = "follow_up"


@dataclass(frozen=True)
class CreateTaskFromInteractionMessageResult:
    task: CommercialTask
    task_ref_message: InteractionMessage


class CreateTaskFromInteractionMessageUseCase:
    """Create_task + mensagem task_ref na sala (acesso global na borda)."""

    def __init__(
        self,
        *,
        rooms: InteractionRoomRepositoryPort,
        messages: InteractionMessageRepositoryPort,
        worklist: ManageWorklistUseCase,
        interaction_messages: ManageInteractionMessagesUseCase,
        attachments: AttachmentRepositoryPort,
        attachment_storage: AttachmentStorage,
        tasks: TaskRepositoryPort,
    ) -> None:
        self._rooms = rooms
        self._messages = messages
        self._worklist = worklist
        self._interaction_messages = interaction_messages
        self._attachments = attachments
        self._attachment_storage = attachment_storage
        self._tasks = tasks
        self._access = InteractionRoomAccessService(rooms)

    def _clone_message_attachments_to_task(
        self,
        *,
        message_id: UUID,
        task_id: UUID,
        actor_user_id: str,
        body_text: str,
    ) -> str:
        records = list(
            self._attachments.list_for_owner(
                owner_type="room_message",
                owner_id=str(message_id),
            )
        )
        if not records:
            return body_text
        id_map: dict[str, str] = {}
        for record in records:
            stored = self._attachment_storage.copy_to_owner(
                source_storage_key=record.storage_key,
                owner_type="task",
                owner_id=str(task_id),
                original_name=record.file_name,
                content_type=record.content_type,
            )
            cloned = self._attachments.create(
                owner_type="task",
                owner_id=str(task_id),
                file_name=stored.file_name,
                storage_key=stored.storage_key,
                content_type=record.content_type,
                byte_size=stored.byte_size,
                uploaded_by_user_id=actor_user_id,
            )
            id_map[str(record.id)] = str(cloned.id)
        return InteractionMessageMarkdownAttachmentsService.rewrite_attachment_ids(
            body_text,
            id_map,
        )

    def execute(
        self,
        request: CreateTaskFromInteractionMessageInput,
        *,
        actor_is_portfolio_manager: bool = False,
    ) -> CreateTaskFromInteractionMessageResult:
        actor = (request.actor_user_id or "").strip()
        if not actor:
            raise ValueError(InteractionRoomContentService.error("userIdRequired"))
        self._access.require_room_exists(request.room_id)

        message = self._messages.get_by_id(request.message_id)
        if message is None:
            raise LookupError(InteractionRoomContentService.error("messageNotFound"))
        if message.room_id != request.room_id:
            raise ValueError(InteractionRoomContentService.error("messageNotInRoom"))
        if message.deleted_at is not None:
            raise ValueError(InteractionRoomContentService.error("messageDeletedForTask"))

        title = InteractionRoomContentService.task_title_from_message_body(
            message.body_text
        )
        override = (request.description or "").strip()
        body = (message.body_text or "").strip()
        description = override or body or None
        task = self._worklist.create_task(
            user_id=actor,
            data=CreateTaskInput(
                title=title,
                description=description,
                task_type=request.task_type,
                priority=request.priority,
                assignee_user_id=request.assignee_user_id,
                assignee_user_ids=request.assignee_user_ids,
                related_entity_type=InteractionRoomContentService.related_entity_type_room(),
                related_entity_id=str(request.room_id),
                source_interaction_message_id=request.message_id,
            ),
            actor_is_portfolio_manager=actor_is_portfolio_manager,
        )
        if description:
            rewritten = self._clone_message_attachments_to_task(
                message_id=request.message_id,
                task_id=task.id,
                actor_user_id=actor,
                body_text=description,
            )
            if rewritten != description:
                updated = self._tasks.update_description(
                    task_id=task.id,
                    description=rewritten,
                )
                if updated is not None:
                    task = updated
        mention_kind = InteractionRoomContentService.task_mention_kind()
        task_ref_message = self._interaction_messages.post(
            PostInteractionMessageInput(
                room_id=request.room_id,
                actor_user_id=actor,
                body_text=InteractionRoomContentService.task_ref_body(title=task.title),
                message_kind=InteractionRoomContentService.task_ref_message_kind(),
                mentions=(
                    (
                        mention_kind,
                        {"task_id": str(task.id)},
                        task.title,
                    ),
                ),
            )
        )
        return CreateTaskFromInteractionMessageResult(
            task=task,
            task_ref_message=task_ref_message,
        )
