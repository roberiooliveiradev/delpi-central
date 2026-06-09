"""Vocabulário compartilhado de refinamento de formato — Fase 5 apresentação."""

from __future__ import annotations

from app.domain.services.chat_assistant_vocabulary_service import ChatAssistantVocabularyService


class ChatPresentationFormatVocabularyService(ChatAssistantVocabularyService):
    BUNDLE = "operational_pipeline_vocabulary"
    _ROOT = ("presentationFormatRefinement",)

    @classmethod
    def table_hints(cls, *, include_tool_context: bool = False) -> tuple[str, ...]:
        hints = cls.terms(*cls._ROOT, "tableHints")

        if include_tool_context:
            return cls.merge_terms(
                cls._ROOT + ("tableHints",),
                cls._ROOT + ("toolContextExtras", "tableHints"),
            )

        return hints

    @classmethod
    def chart_hints(cls, *, include_tool_context: bool = False) -> tuple[str, ...]:
        return cls.terms(*cls._ROOT, "chartHints")

    @classmethod
    def text_hints(cls, *, include_tool_context: bool = False) -> tuple[str, ...]:
        hints = cls.terms(*cls._ROOT, "textHints")

        if include_tool_context:
            return cls.merge_terms(
                cls._ROOT + ("textHints",),
                cls._ROOT + ("toolContextExtras", "textHints"),
            )

        return hints

    @classmethod
    def tree_hints(cls, *, include_tool_context: bool = False) -> tuple[str, ...]:
        hints = cls.terms(*cls._ROOT, "treeHints")

        if include_tool_context:
            return cls.merge_terms(
                cls._ROOT + ("treeHints",),
                cls._ROOT + ("toolContextExtras", "treeHints"),
            )

        return hints

    @classmethod
    def reference_hints(cls) -> tuple[str, ...]:
        return cls.terms(*cls._ROOT, "referenceHints")

    @classmethod
    def imperative_verbs(cls) -> tuple[str, ...]:
        return cls.terms(*cls._ROOT, "imperativeVerbs")

    @classmethod
    def last_result_terms(cls) -> tuple[str, ...]:
        return cls.terms(*cls._ROOT, "lastResultTerms")
