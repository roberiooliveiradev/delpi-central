"""Architecture / Abstraction Gate tests for C3-T7."""

from __future__ import annotations

import ast
from dataclasses import fields
from pathlib import Path

from app.domain.decision_path.model import (
    DecisionPath,
    DecisionPathInput,
    DecisionPathResult,
)
from app.domain.planning.model import PlanCandidate, PlanStep


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
)

FORBIDDEN_TYPE_NAMES = (
    "PlannerEngine",
    "PlannerRegistry",
    "GenericPlanner",
    "UniversalPlanner",
    "AgentPlanner",
    "GenericAgent",
    "AgentRuntime",
    "ToolPlanner",
    "ToolDispatcher",
    "RoutingEngine",
    "ModelRouter",
    "LLMRouter",
    "ProviderRouter",
    "AIOrchestrator",
    "UniversalTaskGraph",
    "GenericWorkflowEngine",
    "PlanRepository",
    "PlannerRepository",
    "PlanningStore",
    "PlannerPort",
    "RoutingPort",
    "PlanExecutionPort",
    "CapabilityExecutionPort",
    "PlannerModelPort",
    "RouterModelPort",
    "ReasoningModelPort",
    "PlannerService",
    "PlannerPolicyEngine",
    "PlannerDecisionEngine",
    "KnowledgeRetrievalPort",
    "KnowledgeRepository",
    "KnowledgeService",
    "KnowledgeManager",
    "RetrievalEngine",
    "VectorStore",
    "RAGService",
    "EventEnvelope2",
    "PlannerEvent",
    "DecisionEvent",
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
    "reasoning_trace",
    "scratchpad",
}

APP_ROOT = Path(__file__).resolve().parents[1] / "app"


def _python_files(*relative: str) -> list[Path]:
    root = APP_ROOT.joinpath(*relative)
    return [path for path in root.rglob("*.py") if path.name != "__pycache__"]


def test_decision_path_planning_no_provider_sdk_or_runtime_imports():
    paths = [
        *_python_files("domain", "decision_path"),
        *_python_files("domain", "planning"),
    ]
    for path in paths:
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


def test_no_speculative_planner_or_routing_abstractions():
    for path in APP_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                assert node.name not in FORBIDDEN_TYPE_NAMES, path


def test_no_duplicate_canonical_primitives():
    canonical = {
        "EvidenceRef": "domain/evidence/model.py",
        "SourceRef": "domain/evidence/model.py",
        "CapabilityProjection": "domain/capability_catalog/model.py",
        "OperationCharacter": "domain/capability_catalog/model.py",
        "DecisionPath": "domain/decision_path/model.py",
    }
    found: dict[str, list[str]] = {name: [] for name in canonical}
    for path in APP_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name in found:
                found[node.name].append(str(path.relative_to(APP_ROOT)))
    for name, expected_path in canonical.items():
        assert found[name] == [expected_path]


def test_decision_path_values_are_exactly_three_paths():
    assert {item.name for item in DecisionPath} == {
        "FAST",
        "OPERATIONAL",
        "REASONING",
    }


def test_routing_and_planning_have_no_authority_or_mechanics_fields():
    for model in (DecisionPathInput, DecisionPathResult, PlanCandidate, PlanStep):
        names = {field.name.lower() for field in fields(model)}
        assert names.isdisjoint(FORBIDDEN_FIELD_NAMES), (
            f"{model.__name__} exposes forbidden field"
        )


def test_planner_reuses_canonical_capability_and_evidence_types():
    planning_model = (APP_ROOT / "domain" / "planning" / "model.py").read_text()
    assert (
        "from app.domain.capability_catalog.model import OperationCharacter"
        in planning_model
    )
    assert "from app.domain.evidence.model import" in planning_model
    assert "class PlannerCapability" not in planning_model
    assert "class PlannerEvidenceRef" not in planning_model
    assert "class PlannerSourceRef" not in planning_model


def test_no_application_planner_or_routing_layer():
    for package in ("decision_path", "planning", "planner", "routing"):
        assert not (APP_ROOT / "application" / package).exists()
    ports = APP_ROOT / "application" / "ports"
    if ports.exists():
        for path in ports.rglob("*.py"):
            lowered = path.name.lower()
            for forbidden in ("planner", "routing", "retrieval"):
                assert forbidden not in lowered
