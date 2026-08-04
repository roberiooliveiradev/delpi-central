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
    def is_create_slide_request(cls, message: str | None) -> bool:
        """Pedido de novo slide/tela (não playlist genérica nem bind de fonte)."""
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        if not normalized or len(normalized) < 4:
            return False

        slide_markers = cls._list("createSlideMarkers") or ("slide", "slides", "tela", "telas")
        for phrase in cls._normalized_phrases():
            if phrase and phrase in normalized and any(m in phrase for m in slide_markers):
                return True

        has_marker = any(marker in normalized for marker in slide_markers if marker)
        has_action = any(
            action in normalized for action in cls._list("createActionTerms") if action
        )
        return bool(has_marker and has_action)

    @classmethod
    def build_create_slide_tool_call(cls, message: str | None) -> dict | None:
        if not cls.is_create_slide_request(message):
            return None

        preset = cls._text("defaultCreatePresetKey", default="preset_comunicado") or "preset_comunicado"
        reason = cls._text(
            "selectionReason",
            default="Pedido de slide no editor TV Dashboard.",
        )
        return {
            "name": "tv_dashboard_copilot",
            "arguments": {
                "mode": "preview",
                "ops": [{"op": "add_slide_from_preset", "presetKey": preset}],
            },
            "reason": reason,
        }

    @classmethod
    def build_apply_tool_call_from_history(
        cls,
        previous_messages: list | None,
    ) -> dict | None:
        """Reusa ops do último preview bem-sucedido de ``tv_dashboard_copilot``."""

        def _role(item: object) -> str:
            if isinstance(item, dict):
                return str(item.get("role") or "").lower()
            return str(getattr(item, "role", "") or "").lower()

        def _metadata(item: object) -> dict:
            if isinstance(item, dict):
                meta = item.get("metadata")
            else:
                meta = getattr(item, "metadata", None)
            return meta if isinstance(meta, dict) else {}

        for message in reversed(list(previous_messages or [])):
            if _role(message) != "assistant":
                continue
            tool_calls = _metadata(message).get("toolCalls")
            if not isinstance(tool_calls, list):
                continue
            for call in reversed(tool_calls):
                if not isinstance(call, dict):
                    continue
                if str(call.get("name") or "") != "tv_dashboard_copilot":
                    continue
                call_meta = call.get("metadata") if isinstance(call.get("metadata"), dict) else {}
                if call_meta.get("ok") is False or call_meta.get("blocked"):
                    continue
                arguments = call.get("arguments") if isinstance(call.get("arguments"), dict) else {}
                mode = str(arguments.get("mode") or call_meta.get("mode") or "preview").lower()
                if mode == "apply":
                    continue
                ops = arguments.get("ops")
                if not isinstance(ops, list) or not ops:
                    continue
                target = arguments.get("target")
                return {
                    "name": "tv_dashboard_copilot",
                    "arguments": {
                        "mode": "apply",
                        "ops": list(ops),
                        "target": dict(target) if isinstance(target, dict) else {},
                    },
                    "reason": cls._text(
                        "applySelectionReason",
                        default="Confirmação — apply do patch TV Dashboard.",
                    ),
                }
        return None

    @classmethod
    def format_direct_answer(
        cls,
        *,
        data: dict | None,
        metadata: dict | None,
    ) -> str | None:
        meta = metadata if isinstance(metadata, dict) else {}
        payload = data if isinstance(data, dict) else {}
        if not payload and isinstance(meta.get("data"), dict):
            payload = meta["data"]

        if meta.get("blocked") or meta.get("blockReason") == "confirmation_required":
            return cls._text("directAnswer", "blocked", default="")

        mode = str(meta.get("mode") or "").lower()
        ok = meta.get("ok") is not False

        if mode == "apply":
            key = "applyOk" if ok else "applyFailed"
            return cls._text("directAnswer", key, default="") or None

        side = payload.get("sideEffects") if isinstance(payload.get("sideEffects"), dict) else {}
        slides = side.get("slides") if isinstance(side.get("slides"), list) else []
        first = slides[0] if slides and isinstance(slides[0], dict) else {}
        title = str(first.get("title") or "").strip() or "Slide"
        preset = str(first.get("presetKey") or "").strip()
        if preset:
            return cls._text(
                "directAnswer",
                "previewSlide",
                default="",
            ).format(title=title, presetKey=preset) or None

        ops = payload.get("appliedOps") if isinstance(payload.get("appliedOps"), list) else []
        return cls._text(
            "directAnswer",
            "previewGeneric",
            default="",
        ).format(opsCount=str(len(ops) or 1)) or None
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
