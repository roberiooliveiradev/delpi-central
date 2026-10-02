"""Architecture / Abstraction Gate tests for C3-T8 interaction domain."""

from __future__ import annotations

import ast
from dataclasses import fields
from pathlib import Path

from app.domain.interaction.model import (
    InteractionSession,
    InteractionTurn,
    SessionContext,
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
    "chromadb",
    "faiss",
    "langchain",
    "pinecone",
    "qdrant",
    "pgvector",
    "kafka",
    "celery",
    "minha_delpi",
    "minha-delpi",
)

FORBIDDEN_TYPE_NAMES = (
    "ConversationEngine",
    "ChatEngine",
    "UniversalChatRuntime",
    "GenericAssistantRuntime",
    "AgentSessionManager",
    "ContextEngine",
    "MemoryEngine",
    "InteractionOrchestrator",
    "ConversationBus",
    "ChatBus",
    "MessageBus",
    "ConversationRepository",
    "SessionRepository",
    "MessageRepository",
    "ConversationService",
    "SessionManager",
    "KnowledgeRetrievalPort",
    "ConversationModelPort",
    "ChatModelPort",
    "AssistantModelPort",
    "VectorStore",
    "RAGService",
    "ModelRouter",
    "ConversationUser",
    "ChatUser",
    "SessionPrincipal",
    "ChatCorrelationId",
    "ConversationTraceId",
    "ConversationEvidenceRef",
    "TurnEvidenceRef",
    "ChatSourceRef",
    "SessionSourceRef",
    "ConversationPlan",
    "ChatPlan",
    "AssistantPlan",
    "ConversationMode",
    "ChatReasoningMode",
    "ThinkingMode",
    "AssistantMode",
)

FORBIDDEN_FIELD_NAMES = {
    "is_authorized",
    "can_execute",
    "user_allowed",
    "rbac_granted",
    "permission_granted",
    "act_approved",
    "http_method",
    "http_path",
    "endpoint",
    "url",
    "selector",
    "tool_call",
    "function_call",
    "access_token",
    "refresh_token",
    "api_key",
    "password",
    "client_secret",
    "credential",
    "chain_of_thought",
    "cot",
    "private_reasoning",
    "hidden_reasoning",
    "reasoning_trace",
    "scratchpad",
}

APP_ROOT = Path(__file__).resolve().parents[1] / "app"


def _python_files(*relative: str) -> list[Path]:
    root = APP_ROOT.joinpath(*relative)
    return [path for path in root.rglob("*.py") if path.name != "__pycache__"]


def test_interaction_domain_has_no_provider_or_runtime_imports():
    for path in _python_files("domain", "interaction"):
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


def test_no_speculative_conversation_or_runtime_abstractions():
    for path in APP_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                assert node.name not in FORBIDDEN_TYPE_NAMES, path


def test_no_duplicate_canonical_primitives():
    canonical = {
        "EvidenceRef": "domain/evidence/model.py",
        "SourceRef": "domain/evidence/model.py",
        "EntityRef": "domain/evidence/model.py",
        "UserRef": "domain/evidence/model.py",
        "EpistemicClass": "domain/evidence/model.py",
        "DecisionPath": "domain/decision_path/model.py",
        "PlanCandidate": "domain/planning/model.py",
        "PlanStep": "domain/planning/model.py",
    }
    found: dict[str, list[str]] = {name: [] for name in canonical}
    for path in APP_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name in found:
                found[node.name].append(str(path.relative_to(APP_ROOT)))
    for name, expected_path in canonical.items():
        assert found[name] == [expected_path]


def test_session_turn_context_have_no_auth_secret_cot_or_mechanics_fields():
    for model in (InteractionSession, InteractionTurn, SessionContext):
        names = {field.name.lower() for field in fields(model)}
        assert names.isdisjoint(FORBIDDEN_FIELD_NAMES), (
            f"{model.__name__} exposes forbidden field"
        )


def test_interaction_application_layer_stays_bounded():
    """C3-INTERACTION-RUNTIME-01 introduced `application/interaction`.

    The slice may contain exactly one request-scoped use case. No
    conversation/session/chat engines, repositories, or new ports may
    appear.
    """
    interaction_dir = APP_ROOT / "application" / "interaction"
    assert interaction_dir.exists()
    module_files = sorted(
        p.name for p in interaction_dir.rglob("*.py") if p.name != "__init__.py"
    )
    # C4-MCP-GOVERNED-READS-01/02 add the shared capability-neutral
    # governed-read semantics (governed_read.py: statuses, attempt,
    # binding, combiner, direct-invocation edge) plus two static
    # bindings — governed_product_read.py (DAVI candidate flow) and
    # governed_teo_analyze.py (TÉO direct call). No engine, router,
    # registry, repository, or new port is introduced.
    assert module_files == [
        "contracts.py",
        "errors.py",
        "governed_product_read.py",
        "governed_read.py",
        "governed_teo_analyze.py",
        "handle_interactive_turn.py",
        "instruction.py",
    ]
    for package in ("conversation", "session", "chat"):
        assert not (APP_ROOT / "application" / package).exists()
    ports = APP_ROOT / "application" / "ports"
    if ports.exists():
        for path in ports.rglob("*.py"):
            lowered = path.name.lower()
            for forbidden in (
                "conversation",
                "session",
                "chat",
                "retrieval",
                "memory",
            ):
                assert forbidden not in lowered
