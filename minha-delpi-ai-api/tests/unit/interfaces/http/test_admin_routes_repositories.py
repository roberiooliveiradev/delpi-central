import ast
from pathlib import Path


def test_admin_routes_use_repository_composer_aliases():
    tree = ast.parse(Path("app/interfaces/http/routes/admin_routes.py").read_text())
    imports: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "app.composition.repository_composer":
            for alias in node.names:
                imports.add(alias.name)

    assert "make_audit_repository" in imports
    assert "make_chat_quality_report_repository" in imports
    assert "make_postgres_audit_repository" not in imports
    assert "make_postgres_chat_quality_report_repository" not in imports

    source = Path("app/interfaces/http/routes/admin_routes.py").read_text()
    assert "make_postgres_" not in source
