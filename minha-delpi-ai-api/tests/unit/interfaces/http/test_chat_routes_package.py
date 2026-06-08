import ast
from pathlib import Path


def test_chat_routes_split_modules_exist():
    base = Path("app/interfaces/http/routes/chat")
    expected = {
        "shared.py",
        "deps.py",
        "meta_routes.py",
        "agent_routes.py",
        "project_routes.py",
        "attachment_routes.py",
        "session_routes.py",
        "message_routes.py",
    }
    assert expected.issubset({path.name for path in base.glob("*.py")})


def test_chat_routes_facade_reexports_blueprint():
    facade = Path("app/interfaces/http/routes/chat_routes.py").read_text()
    assert "from app.interfaces.http.routes.chat import chat_bp" in facade


def test_chat_route_modules_have_no_postgres_repository_imports():
    base = Path("app/interfaces/http/routes/chat")
    for path in base.glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    assert "Postgres" not in alias.name
                    assert "postgres_" not in (alias.name or "")
