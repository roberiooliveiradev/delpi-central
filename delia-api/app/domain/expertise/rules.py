"""Deterministic Expertise / Playbook governance rules for C3-T6."""

from __future__ import annotations

from app.domain.expertise.model import DomainPlaybook, ExpertisePack


def expertise_grants_no_permission(expertise: ExpertisePack) -> None:
    if expertise.grants_authorization() or expertise.grants_rbac() or expertise.grants_act():
        raise ValueError("Expertise must not grant authorization")


def playbook_grants_no_permission(playbook: DomainPlaybook) -> None:
    if (
        playbook.grants_authorization()
        or playbook.grants_act()
        or playbook.executes_side_effect()
        or playbook.executes_capability()
    ):
        raise ValueError("Playbook must not grant authorization or execute side effects")


def capability_reference_does_not_authorize_act(playbook: DomainPlaybook) -> None:
    """C3-T5 CapabilityProjection refs on a Playbook remain projection-only."""
    if playbook.capability_ids and playbook.grants_act():
        raise ValueError("CapabilityProjection reference must not authorize ACT")
    for step in playbook.steps:
        if step.capability_id and step.grants_act():
            raise ValueError("Playbook step capability reference must not authorize ACT")
