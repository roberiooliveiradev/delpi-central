"""Operator handoff checklist for ATLAS HML pre-activation (source-only).

Produces a structured matrix: developed / CI-proven / host-pending /
authorization-pending / residual risk. Never authorizes installation.
"""
from __future__ import annotations

from dataclasses import dataclass

_BLOCKS = (
    "HANDOFF_CHECKLIST_SOURCE_ONLY",
    "NOT_A_HOST_ATTESTATION",
    "SEC_01_TO_10_PENDING",
    "PREPARE_DISABLED",
    "ACT_DISABLED",
)


@dataclass(frozen=True, slots=True)
class HMLHandoffItem:
    id: str
    category: str
    summary: str
    evidence_class: str


@dataclass(frozen=True, slots=True)
class HMLHandoffChecklist:
    items: tuple[HMLHandoffItem, ...]
    status: str = "blocked"
    progress_percent_reference: int = 60
    prepare_eligible: bool = False
    can_execute: bool = False
    blocks: tuple[str, ...] = _BLOCKS


def build_stage66_69_handoff_checklist() -> HMLHandoffChecklist:
    items = (
        HMLHandoffItem(
            "E66_CHAIN", "developed",
            "Chain claim→bridge→signer-listen→envelope→signed presenter",
            "code+ci_disposable",
        ),
        HMLHandoffItem(
            "E66_SIGNER_SELF_BIND", "ci_proven",
            "Signer binds AF_UNIX after non-root; root-prebound rejected",
            "ci_disposable",
        ),
        HMLHandoffItem(
            "E67_BOOTSTRAP", "developed",
            "Bootstrap dossier requires external anchor; absence≠genesis",
            "code+ci_disposable",
        ),
        HMLHandoffItem(
            "E67_RECOVERY", "developed",
            "Counter recovery never silently regresses generation floor",
            "code+ci_disposable",
        ),
        HMLHandoffItem(
            "E67_KEYS", "developed",
            "Ephemeral key lifecycle + PKCS#8 recovery id ATLAS-HML-ED25519-PRIVATE-V1",
            "code+ci_disposable",
        ),
        HMLHandoffItem(
            "E68_CANDIDATE_UNITS", "developed",
            "candidate-units/*.candidate RefuseManualStart + sentinel + ExecStart false",
            "code+ci_disposable",
        ),
        HMLHandoffItem(
            "E69_PREFLIGHT", "developed",
            "Structured preflight dossier with secret redaction fail-closed",
            "code+ci_disposable",
        ),
        HMLHandoffItem(
            "HOST_USERS_DIRS", "host_pending",
            "Create UIDs/GIDs/dirs/ACLs on srv-api under change-control",
            "requires_operational_auth",
        ),
        HMLHandoffItem(
            "HOST_BOOTSTRAP_GEN1", "authorization_pending",
            "Authorized gen1 checkpoint with external anchor + owner approval",
            "requires_operational_auth",
        ),
        HMLHandoffItem(
            "HOST_KEY_GLPI", "authorization_pending",
            "Operational key + GLPI recovery copy; passphrase segregated",
            "requires_operational_auth",
        ),
        HMLHandoffItem(
            "HOST_SYSTEMD", "authorization_pending",
            "Install reviewed units only after packaging replaces /usr/bin/false",
            "requires_operational_auth",
        ),
        HMLHandoffItem(
            "SEC_01_10", "residual",
            "SEC-01..10 independent review or formal exception still pending",
            "residual_risk",
        ),
        HMLHandoffItem(
            "ROOT_SAME_HOST", "residual",
            "Same-host root can still compromise local private key / forge peers",
            "owner_accepted_residual",
        ),
        HMLHandoffItem(
            "PREPARE_ACT", "invariant",
            "PREPARE/ACT remain OFF; four MCP READ only; can_execute=False",
            "confirmed_in_code",
        ),
    )
    return HMLHandoffChecklist(items=items)
