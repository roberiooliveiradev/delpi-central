"""Architecture / Abstraction Gate tests for C3-T6."""

from __future__ import annotations

import ast
from pathlib import Path


FORBIDDEN_IMPORT_FRAGMENTS = (
    "openai",
    "anthropic",
    "gemini",
    "google.generativeai",
    "azure",
    "ollama",
    "openrouter",
    "flask",
    "fastapi",
    "sqlalchemy",
    "httpx",
    "requests",
    "chromadb",
    "faiss",
    "langchain",
    "pinecone",
    "qdrant",
    "pgvector",
)

FORBIDDEN_TYPE_NAMES = (
    "ExpertiseRegistry",
    "PlaybookRegistry",
    "KnowledgeRepository",
    "KnowledgeStore",
    "KnowledgeService",
    "KnowledgeEngine",
    "KnowledgeGraph",
    "RAGService",
    "VectorStore",
    "EmbeddingService",
    "AgentRegistry",
    "Marketplace",
    "KnowledgeOrchestrator",
    "UniversalKnowledgeObject",
    "GenericKnowledgeItem",
    "KnowledgeRetrievalPort",
    "RetrievalPort",
)

APP_ROOT = Path(__file__).resolve().parents[1] / "app"


def _python_files(*relative: str) -> list[Path]:
    root = APP_ROOT.joinpath(*relative)
    return [path for path in root.rglob("*.py") if path.name != "__pycache__"]


def test_knowledge_expertise_domain_no_provider_sdk_or_vector_runtime():
    paths = [
        *_python_files("domain", "expertise"),
        *_python_files("domain", "knowledge"),
    ]
    for path in paths:
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name.lower() for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [(node.module or "").lower()]
            else:
                continue
            joined = " ".join(names)
            for fragment in FORBIDDEN_IMPORT_FRAGMENTS:
                assert fragment not in joined, f"{path} imports {fragment}"


def test_no_speculative_knowledge_abstractions():
    for path in APP_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                assert node.name not in FORBIDDEN_TYPE_NAMES, path


def test_no_second_evidence_or_source_ref_primitives():
    found_evidence = []
    found_source = []
    for path in APP_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "EvidenceRef":
                found_evidence.append(str(path.relative_to(APP_ROOT)))
            if isinstance(node, ast.ClassDef) and node.name == "SourceRef":
                found_source.append(str(path.relative_to(APP_ROOT)))
    assert found_evidence == ["domain/evidence/model.py"]
    assert found_source == ["domain/evidence/model.py"]


def test_knowledge_reuses_evidence_source_refs():
    source = (APP_ROOT / "domain" / "knowledge" / "model.py").read_text()
    assert "from app.domain.evidence.model import EvidenceRef, SourceRef" in source
    assert "class KnowledgeEvidenceRef" not in source
    assert "class KnowledgeSourceRef" not in source


def test_no_application_knowledge_manager_or_retrieval_port():
    app_knowledge = APP_ROOT / "application" / "knowledge"
    assert not app_knowledge.exists()
    ports = APP_ROOT / "application" / "ports"
    if ports.exists():
        for path in ports.rglob("*.py"):
            text = path.read_text().lower()
            assert "knowledgeretrievalport" not in text.replace("_", "")
            assert "retrievalport" not in path.name.lower() or "model" in path.name.lower()
