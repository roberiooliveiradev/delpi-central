"""G0-SEC-S1: offline, fail-closed admission review of a REMOTE ENGINE CANDIDATE.

This is NOT a remote runtime, MeshCentral deployment, signature verifier,
security attestation, release downloader, nor authority to grant remote access.
CI success means the risk register is structurally sound while the engine is
BLOCKED. Formal acceptance belongs to humans using a PRIVATE process.
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

MANIFEST_PATH = Path(
    "docs/12-roadmap-e-evolucao/it-portal/delpi-remote/G3-LAB-CANDIDATE.json"
)
SOURCE_REPO = "https://github.com/Ylianst/MeshCentral"
OFFICIAL_TAG_COMMITS = {"1.3.1": "f436143527458d56da0336ea3047c006703fb4e4"}
ALLOWED_ENVIRONMENT = {
    "network_isolation": "separate_lab_only",
    "inbound_from_internet": False,
    "production_credentials": False,
    "production_devices_enrolled": False,
    "remote_engine_installed": False,
    "remote_sessions_enabled": False,
}
REQUIRED_RISK_IDS = {
    "upstream_emergency_security_notice",
    "windows_agent_desktop_regression",
    "supply_chain_artifact_verification",
    "sso_mfa_revocation_validation",
    "private_network_and_recovery",
}
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
TAG = re.compile(r"^[1-9][0-9]*\.[0-9]+\.[0-9]+$")
ISSUE_URL = re.compile(r"^https://github\.com/Ylianst/MeshCentral/(?:releases/tag|issues|security/advisories)/[A-Za-z0-9._-]+$")


@dataclass(frozen=True)
class Review:
    status: str
    errors: tuple[str, ...]
    pending: tuple[str, ...]
    warnings: tuple[str, ...]

    @property
    def ci_pass(self) -> bool:
        # The gate only passes if this is correctly marked blocked.
        return self.status == "BLOCKED" and not self.errors

    @property
    def engine_install_authorized(self) -> bool:
        # A public JSON file cannot authorize an installation or lab deployment.
        return False


def _exact_dict(value: object, keys: set[str], label: str, errors: list[str]) -> dict:
    if not isinstance(value, dict) or set(value) != keys:
        errors.append(f"{label}: estrutura invalida.")
        return {}
    return value


def assess(candidate: object, *, today: date | None = None) -> Review:
    """Validate public admission evidence. Never accept declarations of APPROVED."""
    errors: list[str] = []
    pending: list[str] = []
    warnings: list[str] = []
    if not isinstance(candidate, dict):
        return Review("INVALID", ("Manifesto nao e JSON objeto.",), (), ())
    data = _exact_dict(candidate, {
        "schema_version", "purpose", "engine", "source", "environment", "risks",
    }, "manifesto", errors)
    if data.get("schema_version") != 1 or data.get("purpose") != "offline_review_only" \
            or data.get("engine") != "meshcentral":
        errors.append("Versao, engine ou proposito nao permitido.")
    source = _exact_dict(data.get("source"), {
        "repository", "tag", "tag_commit_sha", "artifact_sha256",
        "verified_on",
    }, "source", errors)
    if source:
        if source["repository"] != SOURCE_REPO:
            errors.append("Origem de codigo nao e o repositorio oficial.")
        tag = source["tag"]
        if not isinstance(tag, str) or not TAG.fullmatch(tag):
            errors.append("Release precisa de versao x.y.z fixa.")
        sha = source["tag_commit_sha"]
        if not isinstance(sha, str) or not SHA40.fullmatch(sha):
            errors.append("Commit de release precisa de SHA Git completo.")
        if isinstance(tag, str) and tag not in OFFICIAL_TAG_COMMITS:
            errors.append("Nova release nao foi revisada/pinada no codigo.")
        elif isinstance(tag, str) and sha != OFFICIAL_TAG_COMMITS[tag]:
            errors.append("Versao e commit nao correspondem a release verificada.")
        digest = source["artifact_sha256"]
        if digest is not None and (
            not isinstance(digest, str) or not SHA256.fullmatch(digest)
        ):
            errors.append("Digest SHA-256 deve ser 64 hex, nunca placeholder.")
        if digest is None:
            pending.append("artifact_sha256: artefato ainda nao verificado")
        try:
            reviewed = date.fromisoformat(source["verified_on"])
            now = today or date.today()
            if reviewed > now:
                errors.append("Data de verificacao futura.")
            elif (now - reviewed).days > 7:
                warnings.append("Verificacao upstream antiga; reconferir antes de qualquer piloto.")
        except (TypeError, ValueError):
            errors.append("Data de verificacao upstream invalida.")
    environment = _exact_dict(
        data.get("environment"), set(ALLOWED_ENVIRONMENT), "environment", errors
    )
    if environment:
        for key, required in ALLOWED_ENVIRONMENT.items():
            value = environment[key]
            if type(value) is not type(required) or value != required:
                errors.append(f"Ambiente viola limite: {key}.")
    risks = data.get("risks")
    if not isinstance(risks, list):
        errors.append("Lista de riscos ausente.")
    else:
        seen: set[str] = set()
        for row in risks:
            r = _exact_dict(row, {"id", "state", "public_reference"}, "risk", errors)
            if not r:
                continue
            name, state, url = r["id"], r["state"], r["public_reference"]
            if not isinstance(name, str) or name not in REQUIRED_RISK_IDS or name in seen:
                errors.append("Risco duplicado, ausente ou desconhecido.")
                continue
            seen.add(name)
            if state not in ("open", "in_review"):
                errors.append(f"Estado indevido para risco {name}; nao aprovar no repo.")
            if not isinstance(url, str) or not ISSUE_URL.fullmatch(url):
                errors.append(f"URL de referencia oficial invalida: {name}.")
            pending.append(name)
        if seen != REQUIRED_RISK_IDS:
            errors.append("Nem todos os riscos obrigatorios foram declarados.")
    if not errors:
        warnings.append("CI verde somente significa riscos declarados e engine nao liberado.")
    return Review(
        status="INVALID" if errors else "BLOCKED",
        errors=tuple(errors), pending=tuple(pending), warnings=tuple(warnings),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Intake G3 de laboratorio (offline)")
    parser.add_argument(
        "--repo-root", type=Path, default=Path(__file__).resolve().parents[3]
    )
    args = parser.parse_args()
    path = args.repo_root.resolve() / MANIFEST_PATH
    try:
        if path.stat().st_size > 16_384:
            print("G3-LAB INVALID: manifesto excede limite.")
            return 1
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        print("G3-LAB INVALID: manifesto ausente ou JSON malformado.")
        return 1
    result = assess(record)
    print(f"G3-LAB {result.status}: {len(result.pending)} pendencia(s), {len(result.errors)} erro(s).")
    for err in result.errors:
        print(f"ERRO: {err}")
    for warning in result.warnings:
        print(f"NOTA: {warning}")
    print("Nenhuma instalacao, uso de credenciais ou sessao remota autorizados.")
    return 0 if result.ci_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
