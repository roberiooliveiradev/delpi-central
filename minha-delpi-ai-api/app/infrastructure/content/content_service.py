from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


class ContentService:
    """Carrega textos da API a partir de arquivos JSON/MD em app/content/."""

    CONTENT_DIR = Path(__file__).resolve().parents[2] / "content"
    DEFAULT_LOCALE = "pt-BR"

    @classmethod
    def locale(cls, value: str | None = None) -> str:
        normalized = str(value or cls.DEFAULT_LOCALE).strip()
        return normalized or cls.DEFAULT_LOCALE

    @classmethod
    @lru_cache(maxsize=64)
    def load_json(cls, relative_path: str, *, locale: str | None = None) -> dict[str, Any]:
        path = cls._resolve_path(relative_path, locale=locale, extension=".json")

        try:
            raw = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise FileNotFoundError(f"Conteúdo não encontrado: {relative_path}") from exc

        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError(f"JSON inválido (esperado objeto): {relative_path}")

        return data

    @classmethod
    @lru_cache(maxsize=64)
    def load_text(cls, relative_path: str, *, locale: str | None = None) -> str:
        path = cls._resolve_path(relative_path, locale=locale, extension=None)

        try:
            return path.read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise FileNotFoundError(f"Conteúdo não encontrado: {relative_path}") from exc

    @classmethod
    def get(cls, relative_path: str, key: str, *, locale: str | None = None, default: str = "") -> str:
        data = cls.load_json(relative_path, locale=locale)
        value = data.get(key, default)
        return str(value if value is not None else default)

    @classmethod
    @lru_cache(maxsize=1)
    def stream(cls, *, locale: str | None = None) -> dict[str, Any]:
        return cls.load_json("assistant/stream", locale=locale)

    @classmethod
    @lru_cache(maxsize=1)
    def skills_catalog(cls, *, locale: str | None = None) -> dict[str, Any]:
        return cls.load_json("skills/catalog", locale=locale)

    @classmethod
    def clear_cache(cls) -> None:
        cls.load_json.cache_clear()
        cls.load_text.cache_clear()
        cls.stream.cache_clear()
        cls.skills_catalog.cache_clear()

    @classmethod
    def _resolve_path(cls, relative_path: str, *, locale: str | None, extension: str | None) -> Path:
        normalized = relative_path.strip().lstrip("/")
        if extension and not normalized.endswith(extension):
            normalized = f"{normalized}{extension}"

        return cls.CONTENT_DIR / cls.locale(locale) / normalized
