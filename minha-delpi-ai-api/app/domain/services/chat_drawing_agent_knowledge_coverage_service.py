"""Fontes RAG do agente de desenho — catálogo canônico para sync/ingest."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService


@dataclass(frozen=True)
class DrawingAgentKnowledgeEntry:
    source_file: str
    title: str
    tags: tuple[str, ...]
    notes: str = ""


class ChatDrawingAgentKnowledgeCoverageService:
    _BUNDLE = "drawing_query_intent"

    @classmethod
    def entries(cls) -> tuple[DrawingAgentKnowledgeEntry, ...]:
        configured = ChatAssistantContentService.get_node(
            cls._BUNDLE,
            "agentKnowledgeSources",
        )

        if configured:
            parsed: list[DrawingAgentKnowledgeEntry] = []

            for item in configured:
                if not isinstance(item, dict):
                    continue

                source_file = str(item.get("sourceFile") or "").strip()

                if not source_file:
                    continue

                tags_raw = item.get("tags") or []
                tags = tuple(
                    str(tag).strip()
                    for tag in tags_raw
                    if isinstance(tags_raw, list) and str(tag).strip()
                )

                parsed.append(
                    DrawingAgentKnowledgeEntry(
                        source_file=source_file,
                        title=str(item.get("title") or source_file).strip(),
                        tags=tags or ("desenho", "engenharia"),
                        notes=str(item.get("notes") or "").strip(),
                    )
                )

            if parsed:
                return tuple(parsed)

        rag_source = str(
            ChatAssistantContentService.get(cls._BUNDLE, "unitConversion", "ragSource")
            or "produto-conversao-unidades-protheus.txt"
        ).strip()

        return (
            DrawingAgentKnowledgeEntry(
                rag_source,
                "Tutorial — Conversão correta de unidades no Protheus DELPI",
                ("produto", "engenharia", "desenho", "unidades"),
                "RAG desenho MI/MT/BOM — unitConversion.ragSource",
            ),
        )

    @classmethod
    def ingest_sources(cls) -> tuple[DrawingAgentKnowledgeEntry, ...]:
        return cls.entries()
