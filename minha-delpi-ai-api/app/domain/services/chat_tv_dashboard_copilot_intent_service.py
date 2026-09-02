"""Intenção do Copiloto TV Dashboard — surface/confirmação (ops vêm do BFF)."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)

_BUNDLE = "tv_dashboard_copilot_intent"
TV_DASHBOARD_SURFACE = "tv-dashboard"
TV_DASHBOARD_COPILOT_SKILL_FLAG = "tvDashboardCopilot"


class ChatTvDashboardCopilotIntentService:
    """Detecta surface/pedido TV leve; ops tipadas vêm do BFF (suggest-ops)."""

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
    def selection_reason(cls) -> str:
        return cls._text(
            "selectionReason",
            default="Pedido de mutação no editor TV Dashboard.",
        )

    @classmethod
    def catalog_unavailable_message(cls) -> str:
        return cls._text(
            "catalogUnavailable",
            default="Catálogo do TV Dashboard indisponível no momento.",
        )

    @classmethod
    def copilot_path_failed_message(cls) -> str:
        return cls._text(
            "copilotPathFailed",
            default=(
                "Falhei ao preparar a alteração no TV Dashboard e nada foi alterado "
                "na programação."
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
        """Frases TV fortes (slide/playlist/copiloto) — sem markers fracos (tabela+monte)."""
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        if not normalized or len(normalized) < 4:
            return False
        return any(
            phrase and phrase in normalized for phrase in cls._normalized_phrases()
        )

    @classmethod
    def matches(cls, message: str | None) -> bool:
        """Heurística leve de surface (frases/markers) — não lista ops do BFF."""
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
        """Surface TV + (match leve OU seleção+verbo OU suggest-ops já resolveu ops)."""
        if not cls.is_tv_surface(host_context):
            return False
        if has_suggested_ops:
            return True
        if cls.matches(message):
            return True
        if cls.has_selection_focus(host_context) and cls.has_mutation_verb(message):
            return True
        return False

    @classmethod
    def last_tool_call_in_history(cls, previous_messages: list | None) -> dict | None:
        """Último ``tv_dashboard_copilot`` do histórico, em qualquer estado."""

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
                if str(call.get("name") or "") == "tv_dashboard_copilot":
                    return call
        return None

    @classmethod
    def build_apply_tool_call_from_history(
        cls,
        previous_messages: list | None,
    ) -> dict | None:
        """Reusa ops do **último** preview bem-sucedido de ``tv_dashboard_copilot``.

        A confirmação vale para a prévia mais recente. Preview que falhou, foi
        bloqueado ou já virou apply não é reaproveitado — o chamador responde
        que não há prévia pendente em vez de gravar um patch antigo.
        """
        call = cls.last_tool_call_in_history(previous_messages)
        if not isinstance(call, dict):
            return None

        call_meta = call.get("metadata") if isinstance(call.get("metadata"), dict) else {}
        if call_meta.get("ok") is False or call_meta.get("blocked"):
            return None

        arguments = call.get("arguments") if isinstance(call.get("arguments"), dict) else {}
        mode = str(arguments.get("mode") or call_meta.get("mode") or "preview").lower()
        if mode == "apply":
            return None

        ops = arguments.get("ops")
        if not isinstance(ops, list) or not ops:
            return None

        target = arguments.get("target")
        confirmation_policy = str(
            arguments.get("confirmationPolicy") or "confirm"
        ).strip().lower()
        if confirmation_policy != "confirm":
            return None
        return {
            "name": "tv_dashboard_copilot",
            "arguments": {
                "mode": "apply",
                "ops": list(ops),
                "target": dict(target) if isinstance(target, dict) else {},
                "confirmationPolicy": "confirm",
                "risk": str(arguments.get("risk") or "destructive"),
            },
            "reason": cls._text(
                "applySelectionReason",
                default="Confirmação — apply do patch TV Dashboard.",
            ),
        }

    @classmethod
    def requires_confirmation(cls, arguments: dict | None) -> bool:
        args = arguments if isinstance(arguments, dict) else {}
        mode = str(args.get("mode") or "preview").strip().lower()
        policy = str(args.get("confirmationPolicy") or "confirm").strip().lower()
        return mode == "apply" and policy != "direct"

    @classmethod
    def no_pending_preview_message(cls) -> str:
        return cls._text(
            "directAnswer",
            "noPendingPreview",
            default="Não há prévia pendente para gravar no TV Dashboard.",
        )

    @classmethod
    def _apply_failure_message(cls, payload: dict, metadata: dict) -> str | None:
        """Falha sem mensagem amigável: mostrar o motivo técnico em vez de só «não deu»."""
        reason = str(payload.get("detail") or "").strip()
        if not reason:
            status = metadata.get("httpStatus")
            reason = f"HTTP {status}" if status else ""
        if reason:
            template = cls._text("directAnswer", "applyFailedWithReason", default="")
            if template:
                return template.format(reason=reason)
        return cls._text("directAnswer", "applyFailed", default="") or None

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
        nested_data = payload.get("data")
        nested_message = (
            str(nested_data.get("message") or "").strip()
            if isinstance(nested_data, dict)
            else ""
        )
        factual_message = str(payload.get("message") or nested_message).strip()

        if mode == "apply":
            if not ok:
                return factual_message or cls._apply_failure_message(payload, meta)
            side = (
                payload.get("sideEffects")
                if isinstance(payload.get("sideEffects"), dict)
                else {}
            )
            slides = side.get("slides") if isinstance(side.get("slides"), list) else []
            key = "applySlideOk" if slides else "applyOk"
            return cls._text("directAnswer", key, default="") or None

        if not ok:
            if factual_message:
                return factual_message
            # Preview que falhou não pode anunciar «prévia gerada»: o usuário
            # confirmaria um patch inexistente.
            return cls._text("directAnswer", "previewFailed", default="") or None

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

        operation_id = str(
            host_context.get("operationId") or host_context.get("operation_id") or ""
        ).strip()
        if operation_id:
            result["operationId"] = operation_id

        data_source_id = str(
            host_context.get("dataSourceId") or host_context.get("data_source_id") or ""
        ).strip()
        if data_source_id:
            result["dataSourceId"] = data_source_id

        preset_key = str(
            host_context.get("presetKey") or host_context.get("preset_key") or ""
        ).strip()
        if preset_key:
            result["presetKey"] = preset_key

        selected_block_types = host_context.get("selectedBlockTypes")
        if isinstance(selected_block_types, list):
            types_normalized = [
                str(item).strip()
                for item in selected_block_types
                if str(item or "").strip()
            ]
            if types_normalized:
                result["selectedBlockTypes"] = types_normalized

        focus_block_id = str(
            host_context.get("focusBlockId") or host_context.get("focus_block_id") or ""
        ).strip()
        if focus_block_id:
            result["focusBlockId"] = focus_block_id

        focus_block_type = str(
            host_context.get("focusBlockType") or host_context.get("focus_block_type") or ""
        ).strip()
        if focus_block_type:
            result["focusBlockType"] = focus_block_type

        selected_data_source_id = str(
            host_context.get("selectedDataSourceId")
            or host_context.get("selected_data_source_id")
            or ""
        ).strip()
        if selected_data_source_id:
            result["selectedDataSourceId"] = selected_data_source_id

        selected_visual_id = str(
            host_context.get("selectedVisualId")
            or host_context.get("selected_visual_id")
            or ""
        ).strip()
        if selected_visual_id:
            result["selectedVisualId"] = selected_visual_id

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
                sources_out.append(
                    {"id": sid, "operationId": op_id, "label": label}
                )
            if sources_out:
                result["dataSources"] = sources_out

        if bool(
            host_context.get("hasLocalDraft")
            or host_context.get("localDraftDirty")
        ):
            result["hasLocalDraft"] = True

        return result

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
    def build_host_prompt_section(
        cls,
        host_context: dict | None,
        *,
        catalog: dict | None = None,
    ) -> str:
        normalized = cls.normalize_host_context(host_context)
        if not normalized and not catalog:
            return ""

        lines = [cls._text("hostPrompt", "title", default="Contexto do editor TV Dashboard")]
        if normalized:
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

        summaries = cls.format_catalog_when_to_use(catalog)
        if summaries:
            title = cls._text(
                "hostPrompt",
                "catalogSectionTitle",
                default="Capabilities do host (catálogo BFF):",
            )
            lines.append(title)
            lines.append(summaries)

        return "\n".join(lines).strip()

    @classmethod
    def format_catalog_when_to_use(
        cls,
        catalog: dict | None,
        *,
        max_items: int = 12,
        max_chars: int = 900,
    ) -> str:
        if not isinstance(catalog, dict):
            return ""
        capabilities = catalog.get("capabilities")
        if not isinstance(capabilities, list):
            return ""

        lines: list[str] = []
        for item in capabilities:
            if not isinstance(item, dict):
                continue
            when = str(item.get("whenToUse") or "").strip()
            op = str(item.get("op") or item.get("key") or "").strip()
            if not when:
                continue
            lines.append(f"- `{op}`: {when}" if op else f"- {when}")
            if len(lines) >= max(1, max_items):
                break

        text = "\n".join(lines).strip()
        if len(text) > max_chars:
            return text[: max(0, max_chars - 1)].rstrip() + "…"
        return text
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
