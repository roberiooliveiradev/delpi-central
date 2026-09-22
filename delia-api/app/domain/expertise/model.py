"""C3-T6 Expertise and Playbook value objects.

Expertise and Playbook are governed, versioned intelligence assets.
They are not authorization, agents, workflows, tools, or ACT grants.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExpertisePack:
    """Versioned Expertise Pack (CP-072 contribution).

    Expertise != authorization / RBAC / Domain permission / ACT.
    """

    expertise_id: str
    version: str
    owner_ref: str
    semantic_purpose: str
    description: str = ""
    applicability: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    knowledge_refs: tuple[str, ...] = ()
    playbook_refs: tuple[str, ...] = ()
    status: str = "DRAFT"

    def __post_init__(self) -> None:
        for name, value in (
            ("expertise_id", self.expertise_id),
            ("version", self.version),
            ("owner_ref", self.owner_ref),
            ("semantic_purpose", self.semantic_purpose),
            ("status", self.status),
        ):
            if not value.strip():
                raise ValueError(f"ExpertisePack.{name} is required")

    def grants_authorization(self) -> bool:
        return False

    def grants_rbac(self) -> bool:
        return False

    def grants_act(self) -> bool:
        return False

    def authorizes_domain_access(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class PlaybookStep:
    """Declarative guidance step. Not executable closure or tool invocation."""

    step_id: str
    guidance: str
    expertise_ref: str | None = None
    knowledge_ref: str | None = None
    capability_id: str | None = None
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.step_id.strip():
            raise ValueError("PlaybookStep.step_id is required")
        if not self.guidance.strip():
            raise ValueError("PlaybookStep.guidance is required")

    def executes_capability(self) -> bool:
        return False

    def grants_act(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class DomainPlaybook:
    """Versioned Domain Playbook (CP-075 contribution).

    Playbook = governed reasoning/work guidance.
    Playbook != Workflow runtime / AutomationExecution / ACT authorization.
    CapabilityProjection reference != execution permission.
    """

    playbook_id: str
    version: str
    owner_ref: str
    purpose: str
    steps: tuple[PlaybookStep, ...] = ()
    applicability: tuple[str, ...] = ()
    capability_ids: tuple[str, ...] = ()
    expertise_refs: tuple[str, ...] = ()
    knowledge_refs: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    status: str = "DRAFT"

    def __post_init__(self) -> None:
        for name, value in (
            ("playbook_id", self.playbook_id),
            ("version", self.version),
            ("owner_ref", self.owner_ref),
            ("purpose", self.purpose),
            ("status", self.status),
        ):
            if not value.strip():
                raise ValueError(f"DomainPlaybook.{name} is required")

    def grants_authorization(self) -> bool:
        return False

    def grants_act(self) -> bool:
        return False

    def executes_side_effect(self) -> bool:
        return False

    def executes_capability(self) -> bool:
        return False
