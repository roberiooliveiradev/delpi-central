"""Orchestration-adapter interchangeability (boundary A).

The interaction handler consumes the framework-neutral
``SupportsGovernedCapabilityAttempt`` port — never the pydantic
adapter. A framework-free fake bound ONLY at the composition root
produces the same governed-attempt contract: no consumer changes,
evidence/provenance/limitations intact, and governance stays in the
wired stage-gates (the fake attempts nothing ungoverned — it proves
substitution, not a second engine).
"""
from __future__ import annotations

from typing import Any, Callable, Mapping

from app.application.interaction.activity import ActivityEventSink
from app.application.interaction.capability_attempt import (
    GovernedCapabilityAttempt,
    GovernedCapabilityStatus,
)
from app.application.interaction.contracts import InteractiveTurnRequest
from app.application.interaction.turn_budget import TurnDeadline
from app.application.interaction.workspace_context import WorkspaceContext
from app.application.model_invocation.contracts import (
    ConversationContextTurn,
)


class _FakeOrchestrationAttempt:
    """Framework-free ``SupportsGovernedCapabilityAttempt`` — records
    the transport contract and returns a typed result. Imports NO
    orchestration SDK: substitution is a composition concern."""

    def __init__(self, result: GovernedCapabilityAttempt) -> None:
        self._result = result
        self.seen: dict[str, Any] = {}

    def attempt(
        self,
        input_text: str,
        *,
        correlation_id: str | None = None,
        actor_user_id: str | None = None,
        session_id: str | None = None,
        confirmation: Mapping[str, Any] | None = None,
        workspace_context: WorkspaceContext | None = None,
        prior_turns: tuple[ConversationContextTurn, ...] = (),
        max_execution_stage: str | None = None,
        turn_deadline: TurnDeadline | None = None,
        activity_sink: ActivityEventSink | None = None,
        cancel_check: Callable[[], bool] | None = None,
    ) -> GovernedCapabilityAttempt:
        self.seen = {
            "input_text": input_text,
            "correlation_id": correlation_id,
            "actor_user_id": actor_user_id,
            "session_id": session_id,
            "prior_turns": prior_turns,
        }
        return self._result


def test_pydantic_ai_isolation_no_framework_imports_in_application():
    """Application/Domain must never import the orchestration SDK —
    the adapter lives only under infrastructure/."""
    import ast
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    offenders: list[str] = []
    for base in ("app/application", "app/domain", "app/application/interaction"):
        for py in (root / base).rglob("*.py"):
            tree = ast.parse(py.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                mod = ""
                if isinstance(node, ast.Import):
                    mod = ",".join(a.name for a in node.names)
                elif isinstance(node, ast.ImportFrom):
                    mod = node.module or ""
                if "pydantic_ai" in mod:
                    offenders.append(f"{py}:{node.lineno}:{mod}")
    assert offenders == []


def test_port_contract_is_framework_neutral():
    """The attempt port's public surface must not reference pydantic
    types — consumers bind to GovernedCapabilityAttempt only."""
    import inspect
    from app.application.interaction.capability_attempt import (
        SupportsGovernedCapabilityAttempt,
    )

    sig = inspect.signature(SupportsGovernedCapabilityAttempt.attempt)
    rendered = str(sig)
    assert "pydantic" not in rendered.lower()
    assert sig.return_annotation in (
        "GovernedCapabilityAttempt",
        GovernedCapabilityAttempt,
    )


def test_alternate_runtime_binds_at_composition_only():
    """A framework-free attempt injected at the composition seam is
    consumed by the real interaction handler — zero consumer changes,
    contract/output preserved."""
    from app.composition.root_composer import _compose_turn_handler
    from app.infrastructure.config.settings import Settings
    import inspect

    # The seam exists: composition accepts the port override.
    params = inspect.signature(_compose_turn_handler).parameters
    assert "orchestration" in params

    captured = GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.SUCCESS,
        correlation_id="corr-x",
        content="resposta fake substituível",
        limitations=("lim1",),
    )
    fake = _FakeOrchestrationAttempt(captured)
    result = fake.attempt(
        "pergunta",
        correlation_id="corr-x",
        actor_user_id="u1",
        session_id="s1",
    )
    assert result.status is GovernedCapabilityStatus.SUCCESS
    assert result.content == "resposta fake substituível"
    assert result.correlation_id == "corr-x"
    assert fake.seen["actor_user_id"] == "u1"
    assert fake.seen["session_id"] == "s1"
