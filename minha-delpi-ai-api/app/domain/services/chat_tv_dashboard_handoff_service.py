"""Handoff TV Dashboard → especialista VISTA (sem tool de mutação no Chat)."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)

_BUNDLE = "tv_dashboard_handoff"
TV_DASHBOARD_SURFACE = "tv-dashboard"
# Legacy skill flag — stripped if present in workspace (never re-enabled).
_LEGACY_SKILL_FLAG = "tvDashboardCopilot"


class ChatTvDashboardHandoffService:
    """Detecta pedido/surface TV e orienta handoff VISTA; nunca emite tool calls."""

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
    def redirect_to_vista_message(cls) -> str:
        return cls._text(
            "redirectToVista",
            default=(
                "Alterações de programação e slides TV são feitas pelo especialista "
                "VISTA (Custom GPT Actions), não por este Chat."
            ),
        )

    @classmethod
    def selection_reason(cls) -> str:
        return cls._text(
            "selectionReason",
            default="Pedido de mutação no editor TV Dashboard.",
        )

    @classmethod
    def path_failed_message(cls) -> str:
        return cls._text(
            "copilotPathFailed",
            default=(
                "O copiloto TV interno foi retirado. Use o especialista VISTA "
                "para alterar a programação."
            ),
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
    def matches_explicit_phrase(cls, message: str | None) -> bool:
        """Frases TV fortes (slide/playlist) — sem markers fracos (tabela+monte)."""
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        if not normalized or len(normalized) < 4:
            return False
        return any(
            phrase and phrase in normalized for phrase in cls._normalized_phrases()
        )

    @classmethod
    def matches(cls, message: str | None) -> bool:
        """Heurística leve de surface (frases/markers)."""
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        if not normalized or len(normalized) < 4:
            return False

        if cls.matches_explicit_phrase(message):
            return True

        markers = cls._list("markers")
        actions = cls._list("mutationActionTerms")
        has_marker = any(marker in normalized for marker in markers if marker)
        has_action = any(action in normalized for action in actions if action)
        return bool(has_marker and has_action)

    @classmethod
    def has_mutation_verb(cls, message: str | None) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        if not normalized:
            return False
        return any(
            term and term in normalized for term in cls._list("mutationActionTerms")
        )

    @classmethod
    def has_selection_focus(cls, host_context: dict | None) -> bool:
        if not isinstance(host_context, dict):
            return False
        if str(host_context.get("slideId") or host_context.get("slide_id") or "").strip():
            return True
        selected = host_context.get("selectedBlockIds") or host_context.get(
            "selectedBlockId"
        )
        if isinstance(selected, list) and any(str(item or "").strip() for item in selected):
            return True
        if str(selected or "").strip():
            return True
        return False

    @classmethod
    def is_tv_mutation_turn(
        cls,
        message: str | None,
        host_context: dict | None = None,
        *,
        has_suggested_ops: bool = False,
    ) -> bool:
        """Surface TV + (match leve OU seleção+verbo)."""
        del has_suggested_ops
        if not cls.is_tv_surface(host_context):
            return False
        if cls.matches(message):
            return True
        if cls.has_selection_focus(host_context) and cls.has_mutation_verb(message):
            return True
        return False

    @classmethod
    def is_tv_handoff_turn(
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
        selected_block_ids = host_context.get("selectedBlockIds")
        selected_normalized: list[str] | None = None
        if isinstance(selected_block_ids, list):
            selected_normalized = [
                str(item).strip() for item in selected_block_ids if str(item or "").strip()
            ]
        elif host_context.get("selectedBlockId"):
            single = str(host_context.get("selectedBlockId") or "").strip()
            selected_normalized = [single] if single else None

        if not surface and not playlist_id and not slide_id and not selected_normalized:
            return None

        result: dict[str, Any] = {
            "surface": surface or TV_DASHBOARD_SURFACE,
            "playlistId": playlist_id,
            "slideId": slide_id,
        }
        if selected_normalized:
            result["selectedBlockIds"] = selected_normalized

        for camel, snake in (
            ("operationId", "operation_id"),
            ("dataSourceId", "data_source_id"),
            ("presetKey", "preset_key"),
            ("focusBlockId", "focus_block_id"),
            ("focusBlockType", "focus_block_type"),
            ("selectedDataSourceId", "selected_data_source_id"),
            ("selectedVisualId", "selected_visual_id"),
        ):
            value = str(host_context.get(camel) or host_context.get(snake) or "").strip()
            if value:
                result[camel] = value

        selected_block_types = host_context.get("selectedBlockTypes")
        if isinstance(selected_block_types, list):
            types_normalized = [
                str(item).strip()
                for item in selected_block_types
                if str(item or "").strip()
            ]
            if types_normalized:
                result["selectedBlockTypes"] = types_normalized

        raw_sources = host_context.get("dataSources")
        if isinstance(raw_sources, list):
            sources_out: list[dict[str, str]] = []
            for item in raw_sources:
                if not isinstance(item, dict):
                    continue
                sid = str(item.get("id") or "").strip()
                op_id = str(item.get("operationId") or item.get("operation_id") or "").strip()
                if not sid or not op_id:
                    continue
                label = str(item.get("label") or "").strip() or op_id
                sources_out.append({"id": sid, "operationId": op_id, "label": label})
            if sources_out:
                result["dataSources"] = sources_out

        if bool(
            host_context.get("hasLocalDraft") or host_context.get("localDraftDirty")
        ):
            result["hasLocalDraft"] = True

        return result

    @classmethod
    def build_host_prompt_section(
        cls,
        host_context: dict | None,
        *,
        catalog: dict | None = None,
    ) -> str:
        del catalog
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
    def enrich_workspace(
        cls,
        workspace_context: dict | None,
        *,
        message: str | None,
        host_context: dict | None = None,
    ) -> dict:
        """Propagates host context; strips legacy skill flag if present."""
        del message
        workspace = dict(workspace_context or {})
        skills = (
            dict(workspace.get("skills") or {})
            if isinstance(workspace.get("skills"), dict)
            else {}
        )
        normalized_host = cls.normalize_host_context(host_context)
        skills.pop(_LEGACY_SKILL_FLAG, None)
        workspace["skills"] = skills
        if normalized_host:
            workspace["tvDashboardHostContext"] = normalized_host
        return workspace
