import re

from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService


class ChatConversationContextService:
    """Monta contexto textual a partir do histórico (incluindo resultados de ferramentas)."""

    _STRUCTURE_PATH_HINT = re.compile(r"/products/[^/]+/structure", re.IGNORECASE)

    @classmethod
    def _message_field(cls, message, name: str, default: str = "") -> str:
        if isinstance(message, dict):
            return str(message.get(name) or default).strip()

        return str(getattr(message, name, default) or default).strip()

    @classmethod
    def _message_metadata(cls, message) -> dict:
        if isinstance(message, dict):
            metadata = message.get("metadata")
            return metadata if isinstance(metadata, dict) else {}

        metadata = getattr(message, "metadata", None)

        return metadata if isinstance(metadata, dict) else {}

    @classmethod
    def build_text_context(cls, previous_messages, *, limit: int = 8) -> str:
        parts: list[str] = []

        for item in previous_messages[-limit:]:
            role = cls._message_field(item, "role", "user") or "user"
            content = cls._message_field(item, "content")

            if content:
                parts.append(f"{role}: {content}")

            snippet = cls._tool_calls_snippet(item, max_preview_chars=1500)

            if snippet:
                parts.append(snippet)

        return "\n".join(parts)

    @classmethod
    def has_recent_tool_data(cls, previous_messages, *, limit: int = 10) -> bool:
        return ChatAnalysisIntentService._has_recent_successful_tool_data(
            previous_messages or [],
            limit=limit,
        )

    @classmethod
    def build_analysis_context(
        cls,
        previous_messages,
        *,
        message: str | None = None,
        limit: int = 12,
    ) -> str:
        blocks: list[str] = []
        preview_texts: list[str] = []

        for item in previous_messages[-limit:]:
            role = cls._message_field(item, "role", "user") or "user"
            content = cls._message_field(item, "content")
            tool_blocks = list(cls._iter_tool_data_blocks(item, max_preview_chars=6000))

            assistant_content = cls._assistant_content_for_analysis(
                content,
                has_tool_data=bool(tool_blocks),
            )

            if assistant_content:
                blocks.append(f"[{role}]\n{assistant_content}")

            for block in tool_blocks:
                blocks.append(block)
                preview_texts.append(block)

        if not blocks:
            return ""

        codes = ChatAnalysisIntentService.extract_all_product_codes(
            *preview_texts,
            *[cls._message_field(m, "content") for m in previous_messages[-limit:]],
        )

        is_interpretation = ChatAnalysisIntentService.is_data_interpretation_request(
            str(message or ""),
            previous_messages,
        )

        if is_interpretation:
            header = (
                "Contexto para interpretar os dados já obtidos nesta conversa "
                "(não repita consultas idênticas; ignore perfil/permissões do usuário):\n"
            )
        else:
            header = (
                "Contexto para análise comparativa (dados já obtidos nesta conversa; "
                "não repita consultas idênticas):\n"
            )

        if codes:
            header += f"Códigos de produto identificados no histórico: {', '.join(codes)}\n"

        if is_interpretation and not preview_texts:
            header += (
                "Nenhum dado operacional detalhado foi encontrado no histórico recente. "
                "Peça ao usuário para fazer uma consulta primeiro (ex.: estoque, roteiro, estrutura).\n"
            )

        return f"{header}\n" + "\n\n".join(blocks)

    @classmethod
    def _format_humanized_summary(cls, tool_meta: dict) -> str:
        humanized = tool_meta.get("humanizedSummary")

        if not isinstance(humanized, dict):
            return ""

        title = str(humanized.get("titulo") or "").strip()
        lines = [
            str(line).strip()
            for line in (humanized.get("linhas") or [])
            if str(line or "").strip()
        ]

        if not title and not lines:
            return ""

        parts: list[str] = []

        if title:
            parts.append(title)

        parts.extend(lines)

        return "\n".join(parts)

    @classmethod
    def _assistant_content_for_analysis(cls, content: str, *, has_tool_data: bool) -> str:
        normalized = str(content or "").strip()

        if not normalized:
            return ""

        generic = (
            "visualização dos dados",
            "visualizacao dos dados",
            "resultado da api",
            "a api retornou",
        )

        if normalized.lower() in generic:
            return ""

        if has_tool_data and len(normalized) < 24:
            return ""

        return normalized

    @classmethod
    def _is_weak_humanized_summary(cls, humanized_text: str, tool_meta: dict) -> bool:
        if not humanized_text:
            return True

        title = str((tool_meta.get("humanizedSummary") or {}).get("titulo") or "").lower()

        if title in {"consulta sql", "resultado da api", "consulta"}:
            return True

        lowered = humanized_text.lower()

        return lowered.startswith("a consulta retornou") and "registro" in lowered

    @classmethod
    def _rehydrate_tool_summary(cls, tool_meta: dict) -> dict | None:
        from app.application.services.chat_data_interpretation_answer_service import (
            ChatDataInterpretationAnswerService,
        )

        return ChatDataInterpretationAnswerService._resolve_tool_summary(tool_meta)

    @classmethod
    def _tool_calls_snippet(cls, message, *, max_preview_chars: int) -> str:
        blocks = list(cls._iter_tool_data_blocks(message, max_preview_chars=max_preview_chars))

        if not blocks:
            return ""

        return "\n".join(blocks)

    @classmethod
    def _iter_tool_data_blocks(cls, message, *, max_preview_chars: int):
        metadata = cls._message_metadata(message)
        tool_calls = metadata.get("toolCalls") or []

        if not isinstance(tool_calls, list):
            return

        for index, tool_call in enumerate(tool_calls):
            if not isinstance(tool_call, dict):
                continue

            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            tool_meta = tool_call.get("metadata")

            if not isinstance(tool_meta, dict) or not tool_meta.get("ok"):
                continue

            path = str(tool_meta.get("path") or "").strip()
            action_id = str(tool_meta.get("actionId") or "").strip()
            preview = str(tool_meta.get("responsePreview") or "").strip()
            humanized_text = cls._format_humanized_summary(tool_meta)

            if cls._is_weak_humanized_summary(humanized_text, tool_meta):
                humanized_text = ""
                rehydrated = cls._rehydrate_tool_summary(tool_meta)

                if rehydrated:
                    humanized_text = "\n".join(
                        [rehydrated["titulo"], *rehydrated["linhas"]]
                    )

            if humanized_text:
                preview = humanized_text if not preview else f"{humanized_text}\n\n{preview}"

            if max_preview_chars > 0 and len(preview) > max_preview_chars:
                preview = f"{preview[:max_preview_chars]}\n…"

            label_parts = []

            if path:
                label_parts.append(f"path={path}")

            if action_id:
                label_parts.append(f"action={action_id}")

            product_code = ChatAnalysisIntentService.extract_product_code_from_tool_path(path)

            if product_code:
                label_parts.append(f"produto={product_code}")

            label = ", ".join(label_parts) if label_parts else f"ferramenta #{index + 1}"

            if preview:
                yield f"[dados da ferramenta — {label}]\n{preview}"
            elif cls._STRUCTURE_PATH_HINT.search(path):
                yield f"[consulta de estrutura registrada — {label}; sem preview armazenado]"

    @classmethod
    def apply_analysis_mode(
        cls,
        message: str,
        previous_messages,
        tool_context: dict,
    ) -> tuple[bool, dict]:
        from app.domain.services.chat_analysis_intent_service import (
            ChatAnalysisIntentService,
        )

        if not (
            ChatAnalysisIntentService.is_comparison_or_insight_request(message)
            or ChatAnalysisIntentService.is_data_interpretation_request(
                message,
                previous_messages,
            )
        ):
            return False, tool_context

        updated = dict(tool_context or {})
        updated.pop("directAnswer", None)

        existing = str(updated.get("context") or "").strip()
        analysis_block = cls.build_analysis_context(
            previous_messages,
            message=message,
        )

        if analysis_block:
            updated["context"] = (
                f"{existing}\n\n{analysis_block}".strip() if existing else analysis_block
            )

        updated["analysisMode"] = True

        return True, updated
