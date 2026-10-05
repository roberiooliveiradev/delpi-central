"""Architecture / boundary tests for C3-INTERACTION-RUNTIME-01.

Locks the slice to: one Application use case, one HTTP route, the
canonical InteractionSession/InteractionTurn domain, and the existing
ModelInvocationPort — with no engines, repositories, routers, or
provider-specific abstractions.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

from app.application.interaction import (
    contracts,
    errors,
    handle_interactive_turn,
    instruction,
)
from app.application.interaction.handle_interactive_turn import (
    HandleInteractiveConversationTurn,
)


APP_ROOT = Path(__file__).resolve().parents[1] / "app"
INTERACTION_DIR = APP_ROOT / "application" / "interaction"

FORBIDDEN_IMPORT_FRAGMENTS = (
    "flask",
    "fastapi",
    "sqlalchemy",
    "httpx",
    "requests",
    "openai",
    "anthropic",
    "gemini",
    "ollama",
)

FORBIDDEN_TYPE_NAMES = (
    "ConversationEngine",
    "InteractionEngine",
    "ChatEngine",
    "AssistantRuntime",
    "AgentRuntime",
    "ProviderRegistry",
    "ModelRouter",
    "PromptRegistry",
    "SessionRepository",
    "MessageRepository",
    "ConversationRepository",
    "GenericApiClient",
    "UniversalResponse",
    "UniversalMessage",
)


def _tree(path: Path) -> ast.AST:
    return ast.parse(path.read_text())


def test_application_module_has_no_framework_or_provider_imports():
    for path in INTERACTION_DIR.rglob("*.py"):
        for node in ast.walk(_tree(path)):
            if isinstance(node, ast.Import):
                names = " ".join(a.name.lower() for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                names = (node.module or "").lower()
            else:
                continue
            for fragment in FORBIDDEN_IMPORT_FRAGMENTS:
                assert fragment not in names, f"{path} imports {fragment}"


def test_no_forbidden_abstractions_defined_in_app():
    for path in APP_ROOT.rglob("*.py"):
        if "__pycache__" in str(path):
            continue
        for node in ast.walk(_tree(path)):
            if isinstance(node, ast.ClassDef):
                assert node.name not in FORBIDDEN_TYPE_NAMES, (
                    f"{path} defines {node.name}"
                )


def test_use_case_is_application_only():
    source = inspect.getsource(handle_interactive_turn)
    for marker in ("get_json", "Blueprint", "jsonify", "request.headers", "flask."):
        assert marker not in source
    # Authorization is Core-permission based only.
    assert '"delia.access"' in source
    assert "effective_permissions" in source


def test_contracts_carry_no_provider_or_authority_leak():
    fields = {f.name for f in contracts.InteractiveTurnResult.__dataclass_fields__.values()}
    for leaked in (
        "provider_response",
        "credentials",
        "instruction",
        "system_prompt",
        "authority",
        "raw",
    ):
        assert leaked not in fields


def test_instruction_lineage_bound_and_not_user_overridable():
    lineage = instruction.interaction_instruction_lineage()
    assert lineage.instruction_id == "delia.interaction.base"
    assert lineage.version == "3"
    assert len(lineage.content_hash) == 64
    # The request contract exposes no prompt/instruction override fields.
    # ``confirmation`` is a bounded digest-only write payload, never a
    # prompt or authority override (§6.126). ``workspace_context`` is a
    # bounded untrusted client hint (§6.130) — never authority.
    request_fields = {
        f.name for f in contracts.InteractiveTurnRequest.__dataclass_fields__.values()
    }
    assert request_fields == {
        "access_context",
        "input_text",
        "prior_turns",
        "confirmation",
        "workspace_context",
    }


def test_single_http_route_shape():
    from app.interfaces.http import interaction_routes

    source = inspect.getsource(interaction_routes)
    assert source.count("@bp.post(") == 1
    assert '"/interaction/turns"' in source
    assert "@bp.get(" not in source
    assert "delete(" not in source


def test_handle_interactive_turn_is_the_only_use_case_class():
    classes = [
        node.name
        for node in ast.walk(_tree(INTERACTION_DIR / "handle_interactive_turn.py"))
        if isinstance(node, ast.ClassDef)
    ]
    assert classes == ["HandleInteractiveConversationTurn"]
