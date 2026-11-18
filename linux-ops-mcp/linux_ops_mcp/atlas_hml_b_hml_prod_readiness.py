"""HML pilot and PROD validation readiness matrices (source-only, blocked).

Codifies inventory, stop criteria, install plan placeholders and PROD gate
checklist without authorizing host mutation. Completeness never enables
PREPARE/ACT or replaces owner operational authorization.
"""
from __future__ import annotations

from dataclasses import dataclass

_HML_ARTIFACTS = (
    "linux-ops-mcp/candidate-units/*.candidate",
    "linux-ops-mcp/packaging-review/*",
    "linux-ops-mcp/linux_ops_mcp/atlas_hml_b_stage75_boot_activation_gate.py",
    "linux-ops-mcp/linux_ops_mcp/atlas_hml_b_runtime_packaging.py",
    "linux-ops-mcp/linux_ops_mcp/atlas_hml_b_signed_pipeline_runtime.py",
    "linux-ops-mcp/linux_ops_mcp/atlas_hml_b_glpi_key_registry.py",
)
_STOP = (
    "CI_OR_VERIFIER_NOT_ACCEPT",
    "DIRECTORY_DAC_DRIFT",
    "DOCKER_ENGINE_IMPACT",
    "NON_ATLAS_SERVICE_IMPACT",
    "SIGNER_PEER_AUTH_FAILURE",
    "CONTINUITY_REGRESSION",
    "OWNER_WINDOW_MISSING",
)
_PROD_GATES = (
    "HML_PILOT_EVIDENCE_BOUND_TO_SHA",
    "READ_ONLY_PROD_OBSERVATION_FIRST",
    "PREPARE_REMAINS_OFF",
    "ACT_REMAINS_OFF",
    "SEC_01_TO_10_HUMAN_APPROVAL",
    "ROLLBACK_AND_ROLLFORWARD_DOCUMENTED",
    "HML_PROD_ISOLATION_VERIFIED",
)
_BLOCKS = (
    "READINESS_MATRIX_NOT_AUTHORIZATION",
    "HOST_INSTALL_NOT_EXECUTED",
    "SEC_01_TO_10_PENDING",
    "PREPARE_DISABLED",
    "ACT_DISABLED",
)


@dataclass(frozen=True, slots=True)
class HMLReadinessMatrix:
    artifacts: tuple[str, ...]
    stop_conditions: tuple[str, ...]
    prod_gates: tuple[str, ...]
    status: str = "blocked"
    hml_pilot_authorized: bool = False
    prod_validation_authorized: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False
    blocks: tuple[str, ...] = _BLOCKS


def build_readiness_matrix() -> HMLReadinessMatrix:
    return HMLReadinessMatrix(
        artifacts=_HML_ARTIFACTS,
        stop_conditions=_STOP,
        prod_gates=_PROD_GATES,
    )



def build_hml_preflight_procedure() -> dict[str, object]:
    """Technical package for a future authorized HML window (always blocked)."""
    return {
        "schema": "atlas.hml.b.hml-preflight-procedure.v1",
        "status": "blocked",
        "prepare_eligible": False,
        "can_execute": False,
        "read_only_steps": [
            "stage74_tmpfiles_audit_fixture_then_host_readonly",
            "stage75_boot_activation_gate_post_create",
            "stage71_identity_and_directory_observation",
            "stage73_package_and_identity_review",
            "docker_endpoint_and_fd_observation",
            "signer_bridge_isolation_candidate_review",
        ],
        "stop_conditions": list(_STOP),
        "acceptance_criteria": [
            "NO_CRITICAL_TMPFILES_CONFLICT",
            "POST_CREATE_DAC_POLICY_MATCH",
            "ATLAS_UNITS_ABSENT_UNTIL_AUTHORIZED",
            "SIGNER_BRIDGE_CANDIDATES_NON_INSTALLABLE",
            "MCP_READ_TOOLS_EQUAL_4",
            "OWNER_WINDOW_DOCUMENTED",
        ],
        "prod_baseline": [
            "record_prod_service_health_before",
            "record_prod_service_health_after_read_only_observation",
            "forbid_prod_mutation_from_hml_window",
        ],
        "rollback": [
            "remove_only_atlas_only_components",
            "never_touch_shared_docker_or_non_atlas_units",
        ],
        "blocks": list(_BLOCKS),
        "installation_authorized": False,
    }
