from __future__ import annotations

import ast
from pathlib import Path

PACKAGE_ROOT = Path(__file__).parents[1] / "bpmn_modeler"
FORBIDDEN_IMPORT_ROOTS = {
    "fastapi",
    "flask",
    "sqlalchemy",
    "psycopg",
    "redis",
    "boto3",
    "keycloak",
    "transformometro",
}
FORBIDDEN_SOURCE_MARKERS = {
    "flowchart_v1",
    "react flow",
    "reactflow",
    "mermaid",
    "bpmn-js",
    "bpmn-moddle",
}


def _python_files() -> list[Path]:
    return sorted(PACKAGE_ROOT.rglob("*.py"))


def test_domain_and_application_do_not_import_infrastructure_dependencies() -> None:
    violations: list[str] = []

    for path in _python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".", 1)[0]
                    if root in FORBIDDEN_IMPORT_ROOTS:
                        violations.append(f"{path}: import {alias.name}")
            elif isinstance(node, ast.ImportFrom) and node.module:
                root = node.module.split(".", 1)[0]
                if root in FORBIDDEN_IMPORT_ROOTS:
                    violations.append(f"{path}: from {node.module} import ...")

    assert violations == []


def test_domain_and_application_do_not_reference_legacy_modeling_stacks() -> None:
    violations: list[str] = []

    for path in _python_files():
        source = path.read_text(encoding="utf-8").lower()
        for marker in FORBIDDEN_SOURCE_MARKERS:
            if marker in source:
                violations.append(f"{path}: {marker}")

    assert violations == []
