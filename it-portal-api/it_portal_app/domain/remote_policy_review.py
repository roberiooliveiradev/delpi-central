"""G0-SEC-S2: validate PUBLIC drafts while all remote capabilities remain blocked.

No network calls, tokens, signatures, runtime configuration, firewall operations
or deployments. A green CI is evidence of an incomplete public *proposal* only;
formal signoff and private security evidence cannot be authored through this file.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

ROOT = "docs/12-roadmap-e-evolucao/it-portal/delpi-remote"
REGISTER = Path(f"{ROOT}/G0-SEC-S2-REVIEW-REGISTER.json")
DOCUMENTS = {
    "policy": f"{ROOT}/G0-SEC-S2-POLICY-PRIVACY.md",
    "network": f"{ROOT}/G0-SEC-S2-NETWORK-ISOLATION.md",
    "recovery": f"{ROOT}/G0-SEC-S2-RECOVERY-AND-REVOCATION.md",
}
CONTROL_OWNERS = {
    "human_security_approval": "ti_security",
    "employee_notice_and_lgpd": "rh_legal",
    "network_isolation_and_tls": "infra_security",
    "keycloak_mfa_fresh_rbac": "ti_security",
    "device_operator_allowlist": "ti_support",
    "one_time_session_and_revocation": "ti_security",
    "audit_and_retention": "rh_legal",
    "backup_restore_and_kill_switch": "infra_security",
    "safe_browser_embedding": "ti_security",
    "windows_lab_pilot_and_rollback": "ti_support",
}
REQUIRED = {
    "schema_version", "scope", "phase", "status",
    "remote_authorized", "lab_install_authorized",
    "unattended_enabled", "screen_recording_enabled",
    "retention_days", "rpo_minutes", "rto_minutes",
    "documents", "checkpoints",
}


@dataclass(frozen=True)
class DraftReview:
    status: str
    errors: tuple[str, ...]
    pending: tuple[str, ...]

    @property
    def ci_pass(self) -> bool:
        return self.status == "BLOCKED" and not self.errors

    @property
    def remote_or_lab_authorized(self) -> bool:
        # The public register cannot authorize operational changes.
        return False


def assess(root: Path, record: object) -> DraftReview:
    errors: list[str] = []
    pending: list[str] = []
    if not isinstance(record, dict) or set(record) != REQUIRED:
        return DraftReview(
            "INVALID", ("Registro de minutas incompleto ou com chaves extras.",), ()
        )
    if (type(record["schema_version"]) is not int
            or record["schema_version"] != 1
            or record["scope"] != "delpi-remote"
            or record["phase"] != "G0-SEC-S2"
            or record["status"] != "draft_requires_private_approval"):
        errors.append("Registro publico so permite minuta pendente de aprovacao privada.")

    for name in (
        "remote_authorized", "lab_install_authorized",
        "unattended_enabled", "screen_recording_enabled",
    ):
        if type(record[name]) is not bool or record[name]:
            errors.append(f"{name}: habilitacao prematura proibida.")
    for name in ("retention_days", "rpo_minutes", "rto_minutes"):
        if record[name] is not None:
            errors.append(f"{name}: valor ainda depende de aprovacao formal e teste.")

    docs = record["documents"]
    if not isinstance(docs, dict) or docs != DOCUMENTS:
        errors.append("Documentos devem ser as tres minutas publicas previstas.")
    else:
        for label, relative in DOCUMENTS.items():
            file = root / relative
            try:
                if file.stat().st_size > 32_768:
                    errors.append(f"{label}: documento excede limite.")
                    continue
                body = file.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                errors.append(f"{label}: documento ausente ou ilegivel.")
                continue
            if (not body.startswith("# G0-SEC-S2")
                    or "**Status:** MINUTA" not in body
                    or "**Gate:** G0-SEC" not in body
                    or "BLOQUEADO" not in body and "NO-GO" not in body):
                errors.append(f"{label}: cabecalho de minuta/gate bloqueado ausente.")

    controls = record["checkpoints"]
    if not isinstance(controls, list):
        errors.append("Checkpoints devem ser uma lista.")
    else:
        seen: set[str] = set()
        for row in controls:
            if not isinstance(row, dict) or set(row) != {
                "id", "owner_role", "review_state", "private_evidence_recorded",
            }:
                errors.append("Checkpoint malformado ou com campos extras.")
                continue
            name = row["id"]
            if not isinstance(name, str) or name not in CONTROL_OWNERS or name in seen:
                errors.append("Checkpoint desconhecido ou duplicado.")
                continue
            seen.add(name)
            if row["owner_role"] != CONTROL_OWNERS[name]:
                errors.append(f"{name}: papel de revisao divergente.")
            if row["review_state"] not in ("pending", "in_review"):
                errors.append(f"{name}: repositorio publico nao registra aprovacao.")
            if type(row["private_evidence_recorded"]) is not bool or row["private_evidence_recorded"]:
                errors.append(f"{name}: evidencia privada nao pode ficar aqui.")
            pending.append(name)
        if seen != set(CONTROL_OWNERS):
            errors.append("Faltam checkpoints de governanca obrigatorios.")

    return DraftReview(
        status="INVALID" if errors else "BLOCKED",
        errors=tuple(errors), pending=tuple(pending),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="G0-SEC-S2: preflight de minuta, sem deploy")
    parser.add_argument(
        "--repo-root", type=Path, default=Path(__file__).resolve().parents[3]
    )
    args = parser.parse_args()
    root = args.repo_root.resolve()
    try:
        path = root / REGISTER
        if path.stat().st_size > 16_384:
            print("G0-SEC-S2 INVALID: registro excede limite.")
            return 1
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        print("G0-SEC-S2 INVALID: registro ausente ou ilegivel.")
        return 1

    result = assess(root, record)
    print(
        f"G0-SEC-S2 {result.status}: {len(result.pending)} "
        f"pendencia(s), {len(result.errors)} erro(s)."
    )
    for err in result.errors:
        print(f"ERRO: {err}")
    print("O registro publico NAO autoriza deploy, MeshCentral, sessoes ou G3.")
    return 0 if result.ci_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
