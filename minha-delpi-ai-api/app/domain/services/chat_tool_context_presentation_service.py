"""Apresentação rica e respostas autorizadas do turno de tools — Fase 3C lote 9."""

from __future__ import annotations

from app.application.services.chat_tool_context_content_service import (
    ChatToolContextContentService,
)


class ChatToolContextPresentationService:
        @classmethod
        def _rich_presentation_from_metadata(cls, metadata: dict) -> dict | None:
            tree_presentation = metadata.get("treePresentation")

            if isinstance(tree_presentation, dict) and str(tree_presentation.get("type") or "") == "tree":
                return tree_presentation

            presentation = metadata.get("presentation")

            if isinstance(presentation, dict):
                presentation_type = str(presentation.get("type") or "").strip().lower()

                if presentation_type in {"tree", "table", "chart", "kpi"}:
                    return presentation

            for key in ("tablePresentation", "chartPresentation"):
                nested = metadata.get(key)

                if isinstance(nested, dict):
                    nested_type = str(nested.get("type") or "").strip().lower()

                    if nested_type in {"table", "chart", "kpi"}:
                        return nested

            return None

        @classmethod
        def _external_action_tool_calls(cls, safe_tool_calls: list[dict]) -> list[dict]:
            return [
                tool_call
                for tool_call in safe_tool_calls
                if str(tool_call.get("name") or "") == "execute_external_action"
            ]

        @classmethod
        def _successful_external_action_tool_calls(cls, safe_tool_calls: list[dict]) -> list[dict]:
            successful: list[dict] = []

            for tool_call in cls._external_action_tool_calls(safe_tool_calls):
                metadata = tool_call.get("metadata")

                if not isinstance(metadata, dict):
                    continue

                if not metadata.get("ok"):
                    continue

                successful.append(tool_call)

            return successful

        @classmethod
        def should_answer_with_presentation_only(cls, safe_tool_calls: list[dict]) -> bool:
            external_calls = cls._external_action_tool_calls(safe_tool_calls)

            if not external_calls:
                return False

            if len(cls._successful_external_action_tool_calls(safe_tool_calls)) != len(
                external_calls
            ):
                return False

            return cls._has_rich_presentation(safe_tool_calls)

        @classmethod
        def prefer_presentation_direct_answer(
            cls,
            direct_answer: str | None,
            safe_tool_calls: list[dict],
            *,
            message: str | None = None,
        ) -> str | None:
            """Resposta curta quando a UI rica já exibe tabela/gráfico/KPI (11.4.1)."""

            from app.domain.services.chat_drawing_intent_service import (
                ChatDrawingIntentService,
            )
            from app.domain.services.chat_product_overview_intent_service import (
                ChatProductOverviewIntentService,
            )

            if ChatDrawingIntentService.blocks_presentation_only_shortcut(message):
                return direct_answer

            if ChatProductOverviewIntentService.blocks_presentation_only_shortcut(message):
                return direct_answer

            if not cls.should_answer_with_presentation_only(safe_tool_calls):
                return direct_answer

            presentation = cls.resolve_presentation_only_answer(safe_tool_calls)

            if not presentation:
                return direct_answer

            continuation = cls._extract_pagination_continuation_suffix(direct_answer)

            if continuation:
                return f"{presentation}\n\n{continuation}".strip()

            normalized = str(direct_answer or "").strip()

            if normalized and normalized != presentation:
                looks_tabular = "|" in normalized or normalized.count("\n") > 6

                if not looks_tabular and (
                    "\n" in normalized or len(normalized) > len(presentation) + 30
                ):
                    return normalized

            return presentation

        @classmethod
        def _extract_pagination_continuation_suffix(cls, direct_answer: str | None) -> str | None:
            if not direct_answer:
                return None

            marker = "**Deseja que eu continue buscando?**"

            if marker not in direct_answer:
                return None

            start = direct_answer.rfind("Consolidei", 0, direct_answer.index(marker))

            if start >= 0:
                return direct_answer[start:].strip()

            return direct_answer[direct_answer.index(marker) :].strip()

        @classmethod
        def resolve_presentation_only_answer(cls, safe_tool_calls: list[dict]) -> str | None:
            if not cls.should_answer_with_presentation_only(safe_tool_calls):
                return None

            titles = cls._presentation_titles(safe_tool_calls)

            if not titles:
                return ChatToolContextContentService.get("presentation", "queryCompleted")

            if len(titles) == 1:
                return titles[0]

            return "\n".join(f"- {title}" for title in titles)

        @classmethod
        def _authorized_body_from_metadata(cls, metadata: dict) -> str | None:
            text_presentation = metadata.get("textPresentation")

            if isinstance(text_presentation, dict):
                markdown = str(text_presentation.get("markdown") or "").strip()

                if markdown:
                    return markdown

            humanized = metadata.get("humanizedSummary")

            if isinstance(humanized, dict):
                linhas = [
                    str(line).strip()
                    for line in (humanized.get("linhas") or [])
                    if str(line or "").strip()
                ]

                if not linhas:
                    return None

                titulo = str(humanized.get("titulo") or "").strip()
                body = "\n".join(linhas)

                if titulo:
                    return f"### {titulo}\n\n{body}"

                return body

            return None

        @classmethod
        def build_authorized_answer_from_tool_calls(
            cls,
            safe_tool_calls: list[dict],
        ) -> str | None:
            """Markdown autorizado (textPresentation / humanizedSummary) para persistir no chat."""

            bodies: list[str] = []

            for tool_call in cls._successful_external_action_tool_calls(safe_tool_calls):
                metadata = tool_call.get("metadata")

                if not isinstance(metadata, dict):
                    continue

                body = cls._authorized_body_from_metadata(metadata)

                if body and body not in bodies:
                    bodies.append(body)

            if not bodies:
                return None

            return "\n\n".join(bodies).strip()

        @classmethod
        def should_persist_authorized_tool_answer(
            cls,
            safe_tool_calls: list[dict],
            *,
            message: str | None = None,
        ) -> bool:
            del message

            if not cls.build_authorized_answer_from_tool_calls(safe_tool_calls):
                return False

            from app.domain.services.chat_rich_presentation_text_service import (
                ChatRichPresentationTextService,
            )

            for tool_call in cls._successful_external_action_tool_calls(safe_tool_calls):
                metadata = tool_call.get("metadata")

                if not isinstance(metadata, dict):
                    continue

                if ChatRichPresentationTextService.should_prefer_authorized_answer_over_llm(
                    [tool_call],
                ):
                    return True

            return cls._has_rich_presentation(safe_tool_calls)

        @classmethod
        def resolve_authorized_persisted_answer(
            cls,
            answer: str | None,
            safe_tool_calls: list[dict],
            *,
            message: str | None = None,
            skip_replacement: bool = False,
        ) -> str:
            """Substitui texto livre do LLM pelo markdown autorizado da ferramenta quando aplicável."""

            if skip_replacement:
                return str(answer or "").strip()

            if not cls.should_persist_authorized_tool_answer(safe_tool_calls, message=message):
                return str(answer or "").strip()

            authorized = cls.build_authorized_answer_from_tool_calls(safe_tool_calls)

            if not authorized:
                return str(answer or "").strip()

            continuation = cls._extract_pagination_continuation_suffix(answer)

            if continuation and continuation not in authorized:
                return f"{authorized}\n\n{continuation}".strip()

            return authorized

        @classmethod
        def _has_rich_presentation(cls, safe_tool_calls: list[dict]) -> bool:
            for tool_call in safe_tool_calls:
                if str(tool_call.get("name") or "") != "execute_external_action":
                    continue

                metadata = tool_call.get("metadata")

                if not isinstance(metadata, dict):
                    continue

                if cls._rich_presentation_from_metadata(metadata):
                    return True

            return False

        @classmethod
        def _presentation_titles(cls, safe_tool_calls: list[dict]) -> list[str]:
            titles: list[str] = []

            for tool_call in safe_tool_calls:
                if str(tool_call.get("name") or "") != "execute_external_action":
                    continue

                metadata = tool_call.get("metadata")

                if not isinstance(metadata, dict):
                    continue

                presentation = cls._rich_presentation_from_metadata(metadata)

                if not presentation:
                    continue

                title = str(presentation.get("title") or "").strip()

                if title and title not in titles:
                    titles.append(title)

            return titles

        @classmethod
        def _compact_direct_answer_for_rich_presentation(
            cls,
            direct_answer: str | None,
            safe_tool_calls: list[dict],
        ) -> str | None:
            """Evita repetir em markdown o mesmo conteúdo já exibido em tabela/gráfico/KPI."""

            if not direct_answer or not cls._has_rich_presentation(safe_tool_calls):
                return direct_answer

            normalized = str(direct_answer).strip()

            if not normalized:
                return None

            if (
                len(normalized) <= 180
                and "|" not in normalized
                and normalized.count("\n") <= 3
            ):
                return normalized

            titles = cls._presentation_titles(safe_tool_calls)

            if titles:
                if len(titles) == 1:
                    return titles[0]

                return "\n".join(f"- {title}" for title in titles)

            return None

        @classmethod
        def _suppress_redundant_structure_presentations(cls, safe_tool_calls: list[dict]) -> None:
            """Árvore e tabela plana da mesma hierarquia não coexistem no mesmo turno."""

            from app.domain.services.chat_presentation_structure_dedup_service import (
                ChatPresentationStructureDedupService,
            )

            for tool_call in safe_tool_calls:
                if str(tool_call.get("name") or "") != "execute_external_action":
                    continue

                metadata = tool_call.get("metadata")

                if not isinstance(metadata, dict):
                    continue

                ChatPresentationStructureDedupService.dedupe_metadata(metadata)
