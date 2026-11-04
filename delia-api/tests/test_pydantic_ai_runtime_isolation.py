"""Doc 231 — Pydantic AI investigation isolation / LangGraph absence."""

from __future__ import annotations

import ast
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1] / "app"
ADAPTER_PATH = (
    APP_ROOT / "infrastructure" / "orchestration" / "pydantic_ai_investigation.py"
)
LEGACY_LANGGRAPH = (
    APP_ROOT / "infrastructure" / "orchestration" / "langgraph_engine.py"
)
COMPOSER_PATH = APP_ROOT / "composition" / "root_composer.py"
REQ_PATH = Path(__file__).resolve().parents[1] / "requirements.txt"


def test_langgraph_engine_file_removed():
    assert not LEGACY_LANGGRAPH.exists()


def test_investigation_adapter_exists():
    assert ADAPTER_PATH.exists()


def test_application_domain_have_no_pydantic_ai_or_langgraph_imports():
    offenders = []
    for layer in ("application", "domain"):
        root = APP_ROOT / layer
        for path in root.rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                mods = []
                if isinstance(node, ast.Import):
                    mods = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    mods = [node.module]
                for mod in mods:
                    root_name = mod.split(".", 1)[0]
                    if root_name in {
                        "pydantic_ai",
                        "langgraph",
                        "langchain",
                        "langsmith",
                    }:
                        offenders.append(
                            f"{path.relative_to(APP_ROOT)} -> {mod}"
                        )
    assert not offenders, offenders


def test_composer_lazy_imports_investigation_runtime():
    tree = ast.parse(COMPOSER_PATH.read_text(encoding="utf-8"))
    top = {
        a.name
        for n in tree.body
        if isinstance(n, ast.Import)
        for a in n.names
    } | {
        n.module
        for n in tree.body
        if isinstance(n, ast.ImportFrom) and n.module
    }
    assert "pydantic_ai" not in {
        m.split(".", 1)[0] for m in top if m
    }
    src = COMPOSER_PATH.read_text(encoding="utf-8")
    assert "pydantic_ai_investigation" in src
    assert "langgraph_engine" not in src


def test_requirements_have_no_langgraph():
    req = REQ_PATH.read_text().lower()
    # Ignore commentary lines — only package pins matter.
    pins = "\n".join(
        line
        for line in req.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )
    assert "langgraph" not in pins
    assert "langchain" not in pins
    assert "pydantic-ai" in pins
