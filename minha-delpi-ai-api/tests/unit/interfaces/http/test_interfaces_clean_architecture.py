import ast
from pathlib import Path


def _scan_interfaces_forbidden_patterns() -> list[str]:
    base = Path("app/interfaces")
    violations: list[str] = []

    for path in sorted(base.rglob("*.py")):
        source = path.read_text(encoding="utf-8")

        if "Postgres" in source and "Repository" in source:
            violations.append(f"{path}: Postgres*Repository")

        if "make_postgres_" in source:
            violations.append(f"{path}: make_postgres_")

        tree = ast.parse(source)
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue

            module = node.module or ""
            for alias in node.names:
                name = alias.name or ""
                if "Postgres" in name and "Repository" in name:
                    violations.append(f"{path}: import {name} from {module}")
                if name.startswith("make_postgres_"):
                    violations.append(f"{path}: import {name} from {module}")

    return violations


def test_interfaces_have_no_postgres_repository_usage():
    violations = _scan_interfaces_forbidden_patterns()
    assert violations == []
