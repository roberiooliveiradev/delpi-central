from __future__ import annotations

import ast
from pathlib import Path

from app.domain.capability_catalog.model import OperationCharacter


APP_ROOT = Path(__file__).resolve().parents[1] / "app"
FORBIDDEN_TYPE_NAMES = {
    "UniversalTool",
    "GenericAction",
    "GenericEndpoint",
    "UniversalCapability",
    "GenericApiAction",
    "ToolRegistryGodObject",
    "GlobalActionRouter",
    "CatalogRepository",
    "CapabilityRegistry",
    "OpenAPIService",
    "SchemaRegistry",
}
FORBIDDEN_DOMAIN_IMPORTS = {
    "flask",
    "fastapi",
    "requests",
    "httpx",
    "sqlalchemy",
    "openapi",
    "swagger",
}


def test_only_canonical_operation_characters_exist():
    assert {item.value for item in OperationCharacter} == {
        "READ", "ADVISE", "PREPARE", "ACT", "VERIFY", "SIGNAL"
    }


def test_single_capability_projection_primitive():
    found = []
    for path in APP_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "CapabilityProjection":
                found.append(str(path.relative_to(APP_ROOT)))
    assert found == ["domain/capability_catalog/model.py"]


def test_domain_does_not_import_openapi_or_framework_dependencies():
    for path in (APP_ROOT / "domain" / "capability_catalog").rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules = [alias.name.lower() for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                modules = [(node.module or "").lower()]
            else:
                continue
            joined = " ".join(modules)
            assert all(fragment not in joined for fragment in FORBIDDEN_DOMAIN_IMPORTS)


def test_no_speculative_or_generic_action_abstractions():
    for path in APP_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                assert node.name not in FORBIDDEN_TYPE_NAMES


def test_no_planner_executor_model_or_automation_hub_dependency():
    paths = [
        *(APP_ROOT / "domain" / "capability_catalog").rglob("*.py"),
        *(APP_ROOT / "infrastructure" / "openapi").rglob("*.py"),
    ]
    combined = "\n".join(path.read_text().lower() for path in paths)
    for forbidden in (
        "tool_dispatcher",
        "planner",
        "automationhub",
        "automation_hub",
        "modelinvocation",
        "model_invocation",
        "vector_store",
        "chromadb",
        "faiss",
        "generic sql",
        "sql execution",
    ):
        assert forbidden not in combined
