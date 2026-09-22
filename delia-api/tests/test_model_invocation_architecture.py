"""Architecture / import-boundary tests for C3-T3 model invocation."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

from app.create_app import create_app
from app.infrastructure.model_invocation.deterministic_test_adapter import (
    DeterministicTestAdapter,
)


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
)

FORBIDDEN_TYPE_NAMES = (
    "ChatCompletion",
    "MessageParam",
    "GenerateContentResponse",
    "UniversalAIClient",
    "GenericAgentRuntime",
    "ProviderRegistry",
    "ModelRouter",
    "PromptRegistry",
    "EvalPlatform",
    "AIControlTower",
)

APP_ROOT = Path(__file__).resolve().parents[1] / "app"


def _python_files(*relative: str) -> list[Path]:
    root = APP_ROOT.joinpath(*relative)
    return [path for path in root.rglob("*.py") if path.name != "__pycache__"]


def _assert_no_forbidden_imports(paths: list[Path]) -> None:
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


def test_domain_and_application_have_no_provider_sdk_imports():
    paths = [
        *_python_files("domain"),
        *_python_files("application"),
    ]
    _assert_no_forbidden_imports(paths)


def test_no_duplicate_model_ref_type():
    found: list[str] = []
    for path in APP_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "ModelRef":
                found.append(str(path.relative_to(APP_ROOT)))
    assert found == ["domain/evidence/model.py"]


def test_forbidden_speculative_abstractions_absent():
    for path in APP_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                assert node.name not in FORBIDDEN_TYPE_NAMES


def test_composition_root_does_not_wire_model_invocation():
    from app.composition import root_composer

    source = inspect.getsource(root_composer)
    assert "InvokeModel" not in source
    assert "DeterministicTestAdapter" not in source
    assert "openai" not in source.lower()
    app = create_app(testing=True)
    assert "MODEL_INVOCATION" not in app.config


def test_test_adapter_is_explicitly_test_only():
    adapter = DeterministicTestAdapter()
    assert adapter.ADAPTER_KIND == "TEST_ONLY"
    source = inspect.getsource(DeterministicTestAdapter)
    assert "openai" not in source.lower()
    assert "anthropic" not in source.lower()


def test_invoke_model_does_not_fabricate_eval_pass():
    invoke_path = APP_ROOT / "application" / "model_invocation" / "invoke_model.py"
    tree = ast.parse(invoke_path.read_text())
    source = invoke_path.read_text()
    assert "_bind_eval(" not in source
    assert "EvalOutcome.PASS" not in source
    assert "EvalResult(" not in source
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "InvokeModel":
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "execute":
                    execute_src = ast.get_source_segment(source, item) or ""
                    assert "EvalResult(" not in execute_src
                    assert "EvalOutcome.PASS" not in execute_src
