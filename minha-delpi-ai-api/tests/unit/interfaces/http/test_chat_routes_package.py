import ast
from pathlib import Path


def test_chat_routes_split_modules_exist():
    base = Path("app/interfaces/http/routes/chat")
    expected = {
        "shared.py",
        "deps.py",
        "meta_routes.py",
        "agent_routes.py",
        "agent_provider_routes.py",
        "agent_skill_routes.py",
        "project_routes.py",
        "attachment_routes.py",
        "session_routes.py",
        "message_routes.py",
    }
    assert expected.issubset({path.name for path in base.glob("*.py")})


def test_chat_routes_facade_reexports_blueprint():
    facade = Path("app/interfaces/http/routes/chat_routes.py").read_text()
    assert "from app.interfaces.http.routes.chat import chat_bp" in facade


def test_deps_exports_private_helpers_for_wildcard_import():
    deps_source = Path("app/interfaces/http/routes/chat/deps.py").read_text()
    shared_source = Path("app/interfaces/http/routes/chat/shared.py").read_text()

    assert "__all__ = [name for name in globals() if not name.startswith(\"__\")]" in deps_source
    for helper in (
        "_PRIVACY_NOTICE",
        "_get_chat_capabilities_from_request",
        "_not_found_response",
        "_stream_chat_response",
    ):
        assert helper in deps_source
    assert "_PRIVACY_NOTICE" in shared_source
    assert "_PRIVACY_NOTICE" not in Path(
        "app/interfaces/http/routes/chat/attachment_routes.py"
    ).read_text()


def test_chat_route_modules_have_no_postgres_repository_imports():
    base = Path("app/interfaces/http/routes/chat")
    for path in base.glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    assert "Postgres" not in alias.name
                    assert "postgres_" not in (alias.name or "")
