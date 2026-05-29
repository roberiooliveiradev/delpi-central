"""Normalização de nomes de arquivos de conhecimento do agente (RAG + importação)."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

# Mapeamento explícito (nome original ou stem) → nome canônico para busca RAG.
_CANONICAL_BY_ORIGINAL: dict[str, str] = {
    "api-delpi-rotas-agente.md": "api-delpi-rotas-agente.md",
    "data_sql_api_instructions.md": "sql-data-api-instructions.md",
    "product_api_instructions.md": "api-product-instructions.md",
    "system_api_instructions.md": "api-system-instructions.md",
    "drawing_analyser_instructions.md": "drawing-analyser-instructions.md",
    "drawing_rules_delpi.md": "drawing-rules-delpi.md",
    "drawing_requirements_delpi.md": "drawing-requirements-delpi.md",
    "validation_rules_delpi.md": "drawing-validation-rules-delpi.md",
    "diretrizes_criacao_de_descricao.md": "produto-diretrizes-criacao-descricao.md",
    "understanding delpi intermediate product codes.md": "engenharia-codigos-intermediarios-delpi.md",
    "analista sql delpi — produção, suprimentos e perdas.txt": "sql-playbook-producao-suprimentos-perdas.txt",
    "analista sql delpi — oportunidades, processos e estagios lmp.txt": "sql-playbook-lmp-oportunidades-processos.txt",
    # Variantes geradas pelo sync GPT_instructions
    "gpt-data-sql-api-instructions.md": "sql-data-api-instructions.md",
    "gpt-product-api-instructions.md": "api-product-instructions.md",
    "gpt-system-api-instructions.md": "api-system-instructions.md",
    "gpt-drawing-analyser-instructions.md": "drawing-analyser-instructions.md",
    "gpt-drawing-rules-delpi.md": "drawing-rules-delpi.md",
    "gpt-drawing-requirements-delpi.md": "drawing-requirements-delpi.md",
    "gpt-validation-rules-delpi.md": "drawing-validation-rules-delpi.md",
    "gpt-diretrizes-criacao-de-descricao.md": "produto-diretrizes-criacao-descricao.md",
    "gpt-understanding-delpi-intermediate-product-codes.md": "engenharia-codigos-intermediarios-delpi.md",
}


class AgentKnowledgeFilenameService:
    _CANONICAL_LOOKUP: dict[str, str] | None = None

    @classmethod
    def _canonical_lookup(cls) -> dict[str, str]:
        if cls._CANONICAL_LOOKUP is None:
            cls._CANONICAL_LOOKUP = {
                cls._normalize_lookup_key(key): value for key, value in _CANONICAL_BY_ORIGINAL.items()
            }
        return cls._CANONICAL_LOOKUP

    @classmethod
    def normalize(cls, original_filename: str | None, *, title: str | None = None) -> str:
        raw = str(original_filename or title or "documento").strip()
        if not raw:
            raw = "documento"

        lookup = cls._canonical_lookup()
        lookup_key = cls._normalize_lookup_key(raw)
        if lookup_key in lookup:
            return lookup[lookup_key]

        stem_lookup = cls._normalize_lookup_key(Path(raw).stem)
        if stem_lookup in lookup:
            ext = Path(raw).suffix.lower() or ".md"
            canonical = lookup[stem_lookup]
            if not Path(canonical).suffix:
                return f"{canonical}{ext}"
            return canonical

        return cls._slugify_filename(raw)

    @classmethod
    def _normalize_lookup_key(cls, value: str) -> str:
        text = unicodedata.normalize("NFKD", value)
        text = "".join(ch for ch in text if not unicodedata.combining(ch))
        return re.sub(r"\s+", " ", text).strip().lower()

    @classmethod
    def _slugify_filename(cls, value: str) -> str:
        path = Path(value)
        ext = path.suffix.lower() or ".md"
        stem = path.stem

        text = unicodedata.normalize("NFKD", stem)
        text = "".join(ch for ch in text if not unicodedata.combining(ch))
        text = text.lower()
        text = re.sub(r"[^a-z0-9]+", "-", text)
        text = re.sub(r"-{2,}", "-", text).strip("-")

        if not text:
            text = "documento"

        return f"{text}{ext}"
