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
    "lxml",
    "xmlschema",
}
FORBIDDEN_SOURCE_MARKERS = {
    "flowchart_v1",
    "react flow",
    "reactflow",
    "mermaid",
    "bpmn-js",
    "bpmn-moddle",
    "parsed_bpmn",
    "bpmn_graph",
    "visual_json",
    "normalized_xml",
    "validated_artifact",
}


def _layer_python_files(*layers: str) -> list[Path]:
    files: list[Path] = []
    for layer in layers:
        files.extend((PACKAGE_ROOT / layer).rglob("*.py"))
    return sorted(files)


def _imported_modules(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.append("." * node.level + (node.module or ""))
    return modules


def test_domain_and_application_do_not_import_infrastructure_dependencies() -> None:
    violations: list[str] = []

    for path in _layer_python_files("domain", "application"):
        for module in _imported_modules(path):
            root = module.lstrip(".").split(".", 1)[0]
            if root in FORBIDDEN_IMPORT_ROOTS:
                violations.append(f"{path}: {module}")

    assert violations == []


def test_domain_and_application_do_not_reference_legacy_or_parallel_models() -> None:
    violations: list[str] = []

    for path in _layer_python_files("domain", "application"):
        source = path.read_text(encoding="utf-8").lower()
        for marker in FORBIDDEN_SOURCE_MARKERS:
            if marker in source:
                violations.append(f"{path}: {marker}")

    assert violations == []


def test_domain_does_not_depend_on_application() -> None:
    violations: list[str] = []

    for path in _layer_python_files("domain"):
        for module in _imported_modules(path):
            normalized = module.lstrip(".")
            if normalized == "application" or normalized.startswith("application."):
                violations.append(f"{path}: {module}")
            if normalized == "bpmn_modeler.application" or normalized.startswith(
                "bpmn_modeler.application."
            ):
                violations.append(f"{path}: {module}")

    assert violations == []
