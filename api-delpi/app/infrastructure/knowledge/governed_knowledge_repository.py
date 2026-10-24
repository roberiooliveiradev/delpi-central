from __future__ import annotations

from pathlib import Path

from app.application.use_cases.read_governed_technical_knowledge_use_case import KnowledgeReadError
from scripts.davi_governed_knowledge_bundle_lib import BundleError, read_published_corpus


class GovernedKnowledgeRepository:
    def __init__(self, *, api_root: Path | None = None):
        self._root = api_root or Path(__file__).resolve().parents[3]

    def load(self, corpus_version: int = 1) -> tuple[dict, dict, dict[str, bytes]]:
        try:
            return read_published_corpus(api_root=self._root, corpus_version=corpus_version)
        except (BundleError, OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
            raise KnowledgeReadError("CORPUS_UNAVAILABLE", 503) from exc
