"""Architecture / import-boundary tests for C3-T4 Structured Understanding."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

from app.application.structured_understanding.understand_structured_input import (
    UnderstandStructuredInput,
)
from app.create_app import create_app


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
)

FORBIDDEN_TYPE_NAMES = (
    "UniversalUnderstanding",
    "GenericSemanticGraph",
    "UniversalClaim",
    "GenericKnowledgeObject",
    "AIUnderstandingEngine",
    "UnderstandingRegistry",
    "SemanticOntologyEngine",
    "EvalPlatform",
    "EvalEngine",
    "EvalService",
    "ProviderRegistry",
    "ModelRouter",
    "PromptRegistry",
)

APP_ROOT = Path(__file__).resolve().parents[1] / "app"


def _python_files(*relative: str) -> list[Path]:
    root = APP_ROOT.joinpath(*relative)
    return [path for path in root.rglob("*.py") if path.name != "__pycache__"]


def test_structured_understanding_domain_application_no_provider_sdk():
    paths = [
        *_python_files("domain", "structured_understanding"),
        *_python_files("application", "structured_understanding"),
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


def test_no_speculative_understanding_abstractions():
    for path in APP_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                assert node.name not in FORBIDDEN_TYPE_NAMES


def test_single_model_invocation_port_reuse():
    found = []
    for path in APP_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "ModelInvocationPort":
                found.append(str(path.relative_to(APP_ROOT)))
    assert found == ["application/ports/model_invocation_port.py"]


def test_understand_use_case_reuses_invoke_model_and_does_not_fabricate_eval_pass():
    source = inspect.getsource(UnderstandStructuredInput)
    assert "InvokeModel" in source
    assert "EvalResult(" not in source
    assert "EvalOutcome.PASS" not in source
    assert "declared_result_epistemic_class" not in source
    assert "confidence" not in source


def test_no_caller_epistemic_selector_or_confidence_contract():
    from app.application.structured_understanding.contracts import (
        StructuredUnderstandingRequest,
        StructuredUnderstandingResult,
    )
    from app.domain.structured_understanding.model import StructuredObservation
    from dataclasses import fields

    assert "declared_result_epistemic_class" not in {
        f.name for f in fields(StructuredUnderstandingRequest)
    }
    assert "confidence" not in {f.name for f in fields(StructuredUnderstandingResult)}
    assert "evidence_refs" not in {f.name for f in fields(StructuredObservation)}


def test_composition_root_does_not_wire_structured_understanding():
    from app.composition import root_composer

    source = inspect.getsource(root_composer)
    assert "UnderstandStructuredInput" not in source
    app = create_app(testing=True)
    assert "STRUCTURED_UNDERSTANDING" not in app.config


def test_no_duplicate_evidence_or_model_ref():
    for type_name, expected in (
        ("EvidenceRef", ["domain/evidence/model.py"]),
        ("SourceRef", ["domain/evidence/model.py"]),
        ("ModelRef", ["domain/evidence/model.py"]),
    ):
        found = []
        for path in APP_ROOT.rglob("*.py"):
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == type_name:
                    found.append(str(path.relative_to(APP_ROOT)))
        assert found == expected, f"{type_name}: {found}"
