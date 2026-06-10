"""Árvore operacional como outline ASCII/markdown no modo Texto — Playbook 12 R14."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_api_delpi_response_profile_service import (
    ChatApiDelpiResponseProfileService,
)
from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)
from app.domain.services.chat_rich_presentation_text_service import (
    ChatRichPresentationTextService,
)

_MAX_OUTLINE_NODES = 120


class ChatPresentationTreeMarkdownService:
    @classmethod
    def embed_outline_in_text_presentation(cls, metadata: dict[str, Any]) -> None:
        if not isinstance(metadata, dict):
            return

        if metadata.get("ok") is False:
            return

        if not cls._should_embed_outline(metadata):
            return

        tree = cls._resolve_tree_presentation(metadata)

        if not tree:
            return

        text_presentation = metadata.get("textPresentation")

        if not isinstance(text_presentation, dict):
            return

        markdown = str(text_presentation.get("markdown") or "").strip()

        if not markdown:
            return

        section = cls.build_outline_section(tree)

        if not section:
            return

        if section in markdown:
            return

        text_presentation["markdown"] = f"{markdown}\n\n{section}".strip()

    @classmethod
    def build_outline_section(cls, presentation: dict[str, Any]) -> str:
        outline = cls.outline_markdown(presentation)

        if not outline:
            return ""

        header = ChatAssistantContentService.get(
            "presenter_content",
            "generic",
            "treeOutlineHeader",
            default="**Composição**",
        )

        return f"{header}\n\n```text\n{outline}\n```".strip()

    @classmethod
    def outline_markdown(cls, presentation: dict[str, Any]) -> str:
        root = presentation.get("root")

        if not isinstance(root, dict):
            return ""

        lines = [cls._format_node_line(root)]
        lines.extend(cls._walk_children(root.get("children") or [], prefix=""))
        return "\n".join(lines).strip()

    @classmethod
    def _should_embed_outline(cls, metadata: dict[str, Any]) -> bool:
        if ChatRichPresentationTextService.is_stack_layout(metadata):
            return False

        path = str(metadata.get("path") or "").strip()
        entity = cls._resolve_entity(path)
        profile = ChatPresentationProfileService.resolve_profile(path, entity)
        embed_enabled = profile.get("textEmbedTreeOutline") is True

        if (
            ChatRichPresentationTextService._uses_humanized_stack_sections(metadata)
            and not embed_enabled
        ):
            return False

        if not cls._is_text_selected(metadata):
            return False

        return embed_enabled

    @classmethod
    def _is_text_selected(cls, metadata: dict[str, Any]) -> bool:
        decision = metadata.get("presentationDecision")

        if isinstance(decision, dict):
            selected = str(decision.get("selected") or "").strip().lower()

            if selected in {"text", "topics"}:
                return True

            if selected and selected not in {"", "auto"}:
                return False

        explicit = str(metadata.get("explicitSessionFormat") or "").strip().lower()

        if explicit in {"text", "topics"}:
            return True

        preferred = str(metadata.get("preferredFormat") or "").strip().lower()

        if preferred in {"text", "topics"}:
            return True

        primary = metadata.get("presentation")

        if isinstance(primary, dict):
            primary_type = str(primary.get("type") or "").strip().lower()

            if primary_type in {"markdown", "text"}:
                return True

        text_presentation = metadata.get("textPresentation")

        if isinstance(text_presentation, dict):
            text_type = str(text_presentation.get("type") or "").strip().lower()

            if text_type in {"markdown", "text"} and primary is None:
                return True

        return False

    @classmethod
    def _resolve_entity(cls, path: str) -> str | None:
        entity = str(
            ChatApiDelpiResponseProfileService.resolve({}, path=path).entity or ""
        ).strip()

        return entity or None

    @classmethod
    def _resolve_tree_presentation(cls, metadata: dict[str, Any]) -> dict[str, Any] | None:
        for key in ("treePresentation", "presentation"):
            presentation = metadata.get(key)

            if ChatRichPresentationTextService._is_tree_presentation(presentation):
                return presentation

        return None

    @classmethod
    def _format_node_line(cls, node: dict[str, Any]) -> str:
        label = str(node.get("label") or node.get("id") or "").strip()
        subtitle = str(node.get("subtitle") or "").strip()
        badge = str(node.get("badge") or "").strip()
        meta_caption = str(node.get("metaCaption") or "").strip()

        parts = [part for part in (label, badge, meta_caption) if part]
        line = " ".join(parts)

        if subtitle:
            line = f"{line} — {subtitle}" if line else subtitle

        return line or "—"

    @classmethod
    def _walk_children(
        cls,
        children: list[Any],
        *,
        prefix: str,
        rendered: list[int] | None = None,
    ) -> list[str]:
        if rendered is None:
            rendered = [0]

        lines: list[str] = []
        valid_children = [child for child in children if isinstance(child, dict)]

        for index, child in enumerate(valid_children):
            if rendered[0] >= _MAX_OUTLINE_NODES:
                remaining = cls._count_tree_nodes(valid_children[index:])
                truncated = ChatAssistantContentService.format(
                    "presenter_content",
                    "generic",
                    "treeOutlineTruncated",
                    remaining=str(remaining),
                    default=f"… e mais {remaining} componente(s).",
                )

                if truncated:
                    lines.append(f"{prefix}… {truncated}")

                break

            is_last = index == len(valid_children) - 1
            branch = "└── " if is_last else "├── "
            extension = "    " if is_last else "│   "
            lines.append(f"{prefix}{branch}{cls._format_node_line(child)}")
            rendered[0] += 1

            sub_children = child.get("children") or []

            if isinstance(sub_children, list) and sub_children:
                lines.extend(
                    cls._walk_children(
                        sub_children,
                        prefix=f"{prefix}{extension}",
                        rendered=rendered,
                    )
                )

        return lines

    @classmethod
    def _count_tree_nodes(cls, nodes: list[Any]) -> int:
        total = 0

        for node in nodes:
            if not isinstance(node, dict):
                continue

            total += 1

            children = node.get("children") or []

            if isinstance(children, list) and children:
                total += cls._count_tree_nodes(children)

        return total
