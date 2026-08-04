"""Intenção do Copiloto TV Dashboard — patches tipados (não redação textual)."""

from __future__ import annotations

from functools import lru_cache

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)

_BUNDLE = "tv_dashboard_copilot_intent"
TV_DASHBOARD_SURFACE = "tv-dashboard"
TV_DASHBOARD_COPILOT_SKILL_FLAG = "tvDashboardCopilot"


class ChatTvDashboardCopilotIntentService:
    """Detecta pedidos de slide/playlist/fonte TV e normaliza hostContext."""

    @classmethod
    def _list(cls, *path: str) -> tuple[str, ...]:
        return tuple(ChatAssistantContentService.list(_BUNDLE, *path))

    @classmethod
    def _text(cls, *path: str, default: str = "") -> str:
        return ChatAssistantContentService.get(_BUNDLE, *path, default=default)

    @classmethod
    @lru_cache(maxsize=1)
    def _normalized_phrases(cls) -> tuple[str, ...]:
        return tuple(
            ChatMessageNormalizationService.normalize_for_matching(item)
            for item in cls._list("phrases")
            if str(item).strip()
        )

    @classmethod
    def is_tv_surface(cls, host_context: dict | None) -> bool:
        if not isinstance(host_context, dict):
            return False
        surface = str(host_context.get("surface") or "").strip().lower().replace("_", "-")
        tokens = {
            ChatMessageNormalizationService.normalize_for_matching(item)
            for item in cls._list("surfaceTokens")
        }
        return surface in tokens or surface == TV_DASHBOARD_SURFACE

    @classmethod
    def matches(cls, message: str | None) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        if not normalized or len(normalized) < 4:
            return False

        if any(phrase and phrase in normalized for phrase in cls._normalized_phrases()):
            return True

        markers = cls._list("markers")
        actions = cls._list("createActionTerms")
        has_marker = any(marker in normalized for marker in markers if marker)
        has_action = any(action in normalized for action in actions if action)
        return bool(has_marker and has_action)

    @classmethod
    def is_tv_copilot_turn(
        cls,
        message: str | None,
        *,
        host_context: dict | None = None,
    ) -> bool:
        if cls.is_tv_surface(host_context):
            return True
        return cls.matches(message)

    @classmethod
    def normalize_host_context(cls, host_context: dict | None) -> dict | None:
        if not isinstance(host_context, dict):
            return None

        surface = str(host_context.get("surface") or "").strip() or None
        playlist_id = str(
            host_context.get("playlistId") or host_context.get("playlist_id") or ""
        ).strip() or None
        slide_id = str(
            host_context.get("slideId") or host_context.get("slide_id") or ""
        ).strip() or None

        if not surface and not playlist_id and not slide_id:
            return None

        return {
            "surface": surface or TV_DASHBOARD_SURFACE,
            "playlistId": playlist_id,
            "slideId": slide_id,
        }

    @classmethod
    def should_enable_skill(
        cls,
        message: str | None,
        *,
        host_context: dict | None = None,
        already_enabled: bool = False,
    ) -> bool:
        if already_enabled:
            return True
        return cls.is_tv_copilot_turn(message, host_context=host_context)

    @classmethod
    def build_host_prompt_section(cls, host_context: dict | None) -> str:
        normalized = cls.normalize_host_context(host_context)
        if not normalized:
            return ""

        lines = [cls._text("hostPrompt", "title", default="Contexto do editor TV Dashboard")]
        surface = normalized.get("surface")
        playlist_id = normalized.get("playlistId")
        slide_id = normalized.get("slideId")

        if surface:
            lines.append(
                cls._text("hostPrompt", "surfaceLine", default="surface={surface}").format(
                    surface=surface
                )
            )
        if playlist_id:
            lines.append(
                cls._text(
                    "hostPrompt",
                    "playlistLine",
                    default="playlistId={playlistId}",
                ).format(playlistId=playlist_id)
            )
        if slide_id:
            lines.append(
                cls._text("hostPrompt", "slideLine", default="slideId={slideId}").format(
                    slideId=slide_id
                )
            )

        instruction = cls._text("hostPrompt", "instruction", default="")
        if instruction:
            lines.append(instruction)

        return "\n".join(lines).strip()

    @classmethod
    def merge_target_into_arguments(
        cls,
        arguments: dict | None,
        host_context: dict | None,
    ) -> dict:
        args = dict(arguments or {})
        host = cls.normalize_host_context(host_context) or {}
        target = args.get("target")
        target_dict = dict(target) if isinstance(target, dict) else {}

        if host.get("playlistId") and not str(target_dict.get("playlistId") or "").strip():
            target_dict["playlistId"] = host["playlistId"]
        if host.get("slideId") and not str(target_dict.get("slideId") or "").strip():
            target_dict["slideId"] = host["slideId"]

        if target_dict:
            args["target"] = target_dict
        return args

    @classmethod
    def enrich_workspace_skills(
        cls,
        workspace_context: dict | None,
        *,
        message: str | None,
        host_context: dict | None = None,
    ) -> dict:
        workspace = dict(workspace_context or {})
        skills = dict(workspace.get("skills") or {}) if isinstance(workspace.get("skills"), dict) else {}
        normalized_host = cls.normalize_host_context(host_context)

        if cls.should_enable_skill(
            message,
            host_context=normalized_host,
            already_enabled=bool(skills.get(TV_DASHBOARD_COPILOT_SKILL_FLAG)),
        ):
            skills[TV_DASHBOARD_COPILOT_SKILL_FLAG] = True

        workspace["skills"] = skills
        if normalized_host:
            workspace["tvDashboardHostContext"] = normalized_host
        return workspace
