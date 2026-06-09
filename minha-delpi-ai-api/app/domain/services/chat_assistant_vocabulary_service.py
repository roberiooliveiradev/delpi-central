"""API canônica para dicionários PT em ``assistant/*_vocabulary.json``.

Vários serviços de domínio compartilham o mesmo bundle JSON — uma única fonte
de termos, frases e templates, carregada via ``ChatAssistantContentService``.
"""

from __future__ import annotations

from typing import Any, ClassVar

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService


class ChatAssistantVocabularyService:
    """Classe base — subclasses definem ``BUNDLE`` (nome do arquivo sem .json)."""

    BUNDLE: ClassVar[str] = ""

    @classmethod
    def _require_bundle(cls) -> str:
        bundle = str(cls.BUNDLE or "").strip()

        if not bundle:
            raise RuntimeError(
                f"{cls.__name__} exige BUNDLE — defina o nome do JSON de vocabulário"
            )

        return bundle

    @classmethod
    def terms(cls, *path: str) -> tuple[str, ...]:
        return tuple(
            ChatAssistantContentService.list(cls._require_bundle(), *path)
        )

    @classmethod
    def merge_terms(cls, *paths: tuple[str, ...]) -> tuple[str, ...]:
        """Une listas de termos de vários caminhos do mesmo bundle, sem duplicar."""
        seen: set[str] = set()
        merged: list[str] = []

        for path in paths:
            for item in cls.terms(*path):
                if item not in seen:
                    seen.add(item)
                    merged.append(item)

        return tuple(merged)

    @classmethod
    def text(cls, *path: str, default: str = "", **values: str) -> str:
        template = ChatAssistantContentService.get(
            cls._require_bundle(),
            *path,
            default=default,
        )

        if not template:
            return default

        try:
            return template.format(**values)
        except KeyError:
            return template

    @classmethod
    def format(cls, *path: str, default: str = "", **values: str) -> str:
        return ChatAssistantContentService.format(
            cls._require_bundle(),
            *path,
            default=default,
            **values,
        )

    @classmethod
    def node(cls, *path: str) -> Any:
        return ChatAssistantContentService.get_node(cls._require_bundle(), *path)

    @classmethod
    def mapping(cls, *path: str) -> dict[str, str]:
        return ChatAssistantContentService.get_mapping(cls._require_bundle(), *path)

    @classmethod
    def synonym_map(cls, *path: str) -> dict[str, tuple[str, ...]]:
        raw = cls.node(*path)

        if not isinstance(raw, dict):
            return {}

        resolved: dict[str, tuple[str, ...]] = {}

        for key, value in raw.items():
            if isinstance(value, list):
                resolved[str(key)] = tuple(
                    str(item) for item in value if str(item).strip()
                )

        return resolved
