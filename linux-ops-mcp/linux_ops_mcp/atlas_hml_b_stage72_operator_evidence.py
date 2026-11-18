"""ATLAS stage 72: explicitly invoked, stdout-only host evidence.

No MCP endpoint, system service, installation, Docker connection, Git command,
subprocess, host mutation or privilege escalation. The result is an untrusted
operator self-observation; it never authorizes operational action or SEC gates.
Run only after explicit operator authorization, with Python -B.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .atlas_hml_b_stage71_readonly_preflight import (
    Stage71ReadOnlyPreflight,
    collect_stage71_readonly,
)

_SCHEMA = "atlas.hml.stage72.readonly-observation.v1"
_BLOCKS = (
    "STAGE72_OPERATOR_OBSERVATION_UNTRUSTED",
    "NOT_INDEPENDENT_HOST_ATTESTATION",
    "DOCKER_ENDPOINTS_AND_CONNECTED_FDS_NOT_ATTESTED",
    "EFFECTIVE_APPARMOR_PROFILE_NOT_ATTESTED",
    "GIT_REMOTE_AND_CHECKOUT_NOT_ATTESTED",
    "PROD_APPLICATION_HEALTH_NOT_ATTESTED",
    "SEC_01_TO_10_PENDING",
    "NO_HOST_MUTATION_AUTHORIZED",
    "PREPARE_DISABLED",
    "ACT_DISABLED",
)


def build_stage72_evidence(probe: Stage71ReadOnlyPreflight) -> dict[str, object]:
    """Render a bounded stable observation without arbitrary host data."""
    if type(probe) is not Stage71ReadOnlyPreflight:
        raise ValueError("STAGE72_OBSERVATION_TYPE_DENIED")
    return {
        "schema": _SCHEMA,
        "environment": "hml",
        "status": "blocked",
        "observation_kind": "operator_self_observation",
        "host_attested": False,
        "can_execute": False,
        "prepare_eligible": False,
        "prepare_enabled": False,
        "act_enabled": False,
        "mcp_tools": [
            "get_deployment_revision",
            "get_host_health",
            "get_service_health",
            "list_managed_services",
        ],
        "identities": [asdict(item) for item in probe.identities],
        "directories": [asdict(item) for item in probe.directories],
        "systemd_unit_names_found": list(probe.systemd_unit_names_found),
        "docker_socket_metadata": {
            "kind": probe.docker_socket_kind,
            "mode": probe.docker_socket_mode,
            "uid": probe.docker_socket_uid,
            "gid": probe.docker_socket_gid,
            "endpoint_connect_attempted": False,
        },
        "apparmor_enabled_flag": probe.apparmor_enabled,
        "findings": list(probe.findings),
        "blocks": list(_BLOCKS),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="ATLAS source-only read-only evidence (never authorizes deployment)",
    )
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument(
        "--fixture-root",
        type=Path, metavar="ABSOLUTE_DIR",
        help="Inspect only an isolated disposable fixture root",
    )
    scope.add_argument(
        "--host-readonly",
        action="store_true",
        help="Explicit host metadata observation (requires prior owner authorization)",
    )
    args = parser.parse_args(argv)
    root = Path("/") if args.host_readonly else args.fixture_root
    if not root.is_absolute() or root.is_symlink() or not root.is_dir():
        parser.error("STAGE72_ROOT_DENIED")
    probe = collect_stage71_readonly(root=root)
    # stdout only: no write to disk, no automatic host persistence or uploads.
    print(json.dumps(build_stage72_evidence(probe), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
