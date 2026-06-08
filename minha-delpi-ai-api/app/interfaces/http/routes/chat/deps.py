"""Imports comuns das rotas HTTP de chat (evita duplicação entre módulos)."""

from __future__ import annotations

from dataclasses import asdict
from uuid import UUID

from flask import g, jsonify, request, send_file
from sqlalchemy.exc import IntegrityError

from app.application.security.chat_permissions import (
    CHAT_ACCESS_PERMISSION,
    CHAT_ADMIN_PERMISSION,
    CHAT_ASK_PERMISSION,
    CHAT_HISTORY_VIEW_PERMISSION,
    CHAT_KNOWLEDGE_MANAGE_PERMISSION,
    CHAT_TOOLS_MANAGE_PERMISSION,
    CHAT_TOOLS_USE_PERMISSION,
)
from app.application.dto.create_chat_artifact_request import CreateChatArtifactRequest
from app.application.dto.create_chat_attachment_request import CreateChatAttachmentRequest
from app.application.dto.create_chat_agent_request import CreateChatAgentRequest
from app.application.dto.create_chat_project_request import CreateChatProjectRequest
from app.application.dto.create_chat_session_request import CreateChatSessionRequest
from app.application.dto.share_chat_agent_request import ShareChatAgentRequest
from app.application.dto.share_chat_project_request import ShareChatProjectRequest
from app.application.dto.switch_chat_branch_request import SwitchChatBranchRequest
from app.application.dto.update_chat_agent_request import UpdateChatAgentRequest
from app.application.dto.update_chat_artifact_request import UpdateChatArtifactRequest
from app.application.dto.update_chat_project_request import UpdateChatProjectRequest
from app.application.dto.upsert_chat_agent_action_request import UpsertChatAgentActionRequest
from app.application.dto.upsert_chat_agent_skill_request import UpsertChatAgentSkillRequest
from app.application.use_cases.chat_agents_use_cases import (
    ChatAgentKeyConflictError,
    ChatAgentPermissionDeniedError,
)
from app.application.use_cases.get_chat_status_use_case import GetChatStatusUseCase
from app.application.use_cases.rename_chat_session_use_case import RenameChatSessionRequest
from app.application.use_cases.set_chat_session_state_use_case import SetChatSessionStateRequest
from app.application.use_cases.update_chat_message_use_case import UpdateChatMessageRequest
from app.composition.chat_composer import (
    make_cancel_chat_stream_use_case,
    make_clear_chat_session_memory_use_case,
    make_create_agent_source_use_case,
    make_create_chat_agent_use_case,
    make_create_chat_artifact_use_case,
    make_create_chat_attachment_use_case,
    make_create_chat_project_use_case,
    make_create_chat_session_use_case,
    make_create_project_source_use_case,
    make_delete_chat_agent_action_provider_use_case,
    make_delete_chat_agent_action_use_case,
    make_delete_chat_agent_use_case,
    make_delete_chat_artifact_use_case,
    make_delete_chat_attachment_use_case,
    make_delete_chat_project_use_case,
    make_delete_chat_session_use_case,
    make_delete_chat_source_use_case,
    make_download_chat_attachment_use_case,
    make_download_chat_source_use_case,
    make_duplicate_chat_agent_use_case,
    make_export_chat_agent_use_case,
    make_get_chat_agent_stats_use_case,
    make_get_chat_agent_use_case,
    make_get_chat_history_use_case,
    make_import_chat_agent_use_case,
    make_list_agent_sources_use_case,
    make_list_chat_agent_action_providers_use_case,
    make_list_chat_agent_actions_use_case,
    make_list_chat_agent_shares_use_case,
    make_list_chat_agent_skills_use_case,
    make_list_chat_agent_versions_use_case,
    make_list_chat_agents_use_case,
    make_list_chat_artifacts_use_case,
    make_list_chat_attachments_use_case,
    make_list_chat_project_shares_use_case,
    make_list_chat_projects_use_case,
    make_list_chat_sessions_use_case,
    make_list_chat_skill_catalog_use_case,
    make_list_project_sources_use_case,
    make_preview_chat_agent_use_case,
    make_publish_chat_agent_use_case,
    make_rename_chat_session_use_case,
    make_revoke_chat_agent_share_use_case,
    make_revoke_chat_project_share_use_case,
    make_search_chat_directory_users_use_case,
    make_send_chat_message_use_case,
    make_set_chat_session_archived_use_case,
    make_set_chat_session_pinned_use_case,
    make_share_chat_agent_use_case,
    make_share_chat_project_use_case,
    make_switch_chat_branch_use_case,
    make_transfer_chat_agent_ownership_use_case,
    make_update_chat_agent_use_case,
    make_update_chat_artifact_use_case,
    make_update_chat_message_use_case,
    make_update_chat_project_use_case,
    make_upsert_chat_agent_action_provider_use_case,
    make_upsert_chat_agent_action_use_case,
    make_upsert_chat_agent_skill_use_case,
    make_upsert_chat_message_feedback_use_case,
    make_chat_session_memory_pins_use_case,
)
from app.composition.repository_composer import (
    make_audit_repository,
    make_chat_agent_repository,
    make_external_action_repository,
    make_list_external_action_providers_use_case,
    make_list_external_actions_use_case,
)
from app.domain.exceptions.chat_exceptions import (
    ChatMessageNotFoundError,
    ChatSessionAccessDeniedError,
    ChatSessionNotFoundError,
    InvalidChatSessionInputError,
)
from app.extensions.db import db
from app.infrastructure.config.settings import Settings
from app.infrastructure.content.content_service import ContentService
from app.infrastructure.external_actions.external_action_test_executor import (
    ExternalActionTestExecutor,
)
from app.interfaces.http.auth_decorators import require_permission
from app.interfaces.http.rate_limit_decorators import rate_limit
from app.interfaces.http.routes.chat.shared import (
    _PRIVACY_NOTICE,
    _build_send_chat_message_request,
    _can_manage_agent_configuration,
    _can_use_admin_debug,
    _create_source_from_request,
    _find_linked_agent_provider,
    _get_chat_capabilities_from_request,
    _not_found_response,
    _parse_optional_bool,
    _stream_chat_response,
    chat_bp,
    chat_forbidden,
)
from app.interfaces.http.utils.errors import bad_request, conflict, forbidden

# `from deps import *` ignora nomes com `_` salvo se estiverem em `__all__`.
__all__ = [name for name in globals() if not name.startswith("__")]
