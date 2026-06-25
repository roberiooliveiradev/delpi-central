"""Loader canônico de bundles em ``app/content/pt-BR/labels/*.json``."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, ClassVar


class ChatLabelContentService:
    _loader: ClassVar[Callable[[str], dict[str, Any]] | None] = None

    @classmethod
    def configure(cls, loader: Callable[[str], dict[str, Any]]) -> None:
        cls._loader = loader

    @classmethod
    def load(cls, bundle: str) -> dict[str, Any]:
        if cls._loader is None:
            raise RuntimeError(
                "ChatLabelContentService não configurado — "
                "chame configure_domain_infrastructure_ports()"
            )

        return cls._loader(str(bundle or "").strip().removesuffix(".json"))
