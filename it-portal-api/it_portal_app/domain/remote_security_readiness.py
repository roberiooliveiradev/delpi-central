"""G0-SEC: preflight offline de seguranca do futuro acesso remoto Delpi.

Nao e uma autorizacao de deploy. Nao cria sessoes, tokens, rotas, permissao ou
integra com MeshCentral. CI deve passar somente quando o recurso continua BLOQUEADO
sem exposicoes acidentais e o registro de evidencias e consistente.
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path

REQUIRED_CHECKS = (
    "human_security_approval",
    "engine_release_and_vulnerability_review",
    "engine_license_and_supply_chain",
    "network_isolation_and_tls",
    "keycloak_mfa_fresh_rbac",
    "device_operator_allowlist",
    "one_time_session_and_revocation",
    "audit_and_retention",
    "employee_notice_and_lgpd",
    "backup_restore_and_kill_switch",
    "safe_browser_embedding",
    "windows_lab_pilot_and_rollback",
)
ALLOWED_STATES = frozenset({"pending", "in_review", "documented"})
REGISTRY_PATH = Path(
    "docs/12-roadmap-e-evolucao/it-portal/delpi-remote/G0-SEC-CHECKPOINTS.json"
)


@dataclass(frozen=True)
class Preflight:
    status: str
    pending: tuple[str, ...]
    documented: tuple[str, ...]
    errors: tuple[str, ...]
    warnings: tuple[str, ...]

    @property
    def safe_to_continue_offline(self) -> bool:
        return not self.errors and self.status == "BLOCKED"

    @property
    def remote_access_authorized(self) -> bool:
        # Revisao documental em GitHub publico NAO concede direito de acesso.
        # A autorizacao formal exige processo privado e controles em runtime.
        return False


def _read_text(root: Path, relative: str) -> str:
    path = root / relative
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return ""


def evaluate(root: Path, registry: object) -> Preflight:
    """Verifica formato do registro e regressao estatica sobre arquivos criticos."""
    errors: list[str] = []
    warnings: list[str] = []
    documented: list[str] = []
    pending: list[str] = []

    if not isinstance(registry, dict):
        return Preflight("INVALID", (), (), ("Registro de G0-SEC nao e objeto JSON.",), ())
    if set(registry) != {"schema_version", "scope", "checkpoints"}:
        errors.append("Registro G0-SEC possui chaves ausentes ou inesperadas.")
    if registry.get("schema_version") != 1 or registry.get("scope") != "delpi-remote":
        errors.append("Schema ou escopo G0-SEC invalido.")
    checkpoints = registry.get("checkpoints")
    if not isinstance(checkpoints, list):
        return Preflight("INVALID", (), (), ("Checkpoints devem ser uma lista.",), ())
    seen: set[str] = set()
    for row in checkpoints:
        if not isinstance(row, dict) or set(row) != {"id", "state", "public_reference"}:
            errors.append("Checkpoint com estrutura invalida.")
            continue
        name, state, reference = row["id"], row["state"], row["public_reference"]
        if not isinstance(name, str) or name not in REQUIRED_CHECKS or name in seen:
            errors.append("Checkpoint duplicado ou nao previsto.")
            continue
        seen.add(name)
        if state not in ALLOWED_STATES:
            errors.append(f"Estado invalido para {name}.")
            continue
        if reference is not None and (
            not isinstance(reference, str)
            or len(reference) > 400
            or not reference.startswith("https://")
            or any(char.isspace() for char in reference)
        ):
            errors.append(f"Referencia publica invalida em {name}.")
            continue
        if state == "documented":
            if reference is None:
                errors.append(f"{name}: evidencia publica necessaria.")
            else:
                documented.append(name)
        else:
            pending.append(name)
            if state == "in_review" and reference is None:
                warnings.append(f"{name}: revisao iniciada sem referencia publica.")
    if seen != set(REQUIRED_CHECKS):
        errors.append("Faltam checkpoints obrigatorios do gate G0-SEC.")

    main = _read_text(root, "it-portal-api/it_portal_app/main.py")
    compose = _read_text(root, "infra/docker-compose.yml")
    manifest_text = _read_text(root, "plugins/it-portal/it-portal.manifest.json")
    if not main or not compose or not manifest_text:
        errors.append("Arquivos de seguranca esperados nao encontrados.")
    if re.search(
        r"app\.include_router\(\s*[A-Za-z_]*(?:remote|meshcentral|broker)[A-Za-z_]*",
        main, re.IGNORECASE,
    ):
        errors.append("Rota de controle remoto detectada antes da aprovacao G0-SEC.")
    if re.search(r"(?m)^  (?:meshcentral|remote-broker|remote-gateway):\s*$", compose):
        errors.append("Servico remoto detectado no Compose antes de G0-SEC.")
    if re.search(r"(?im)^\s*IT_PORTAL_REMOTE_(?:ENABLED|CONTROL_ENABLED):\s*(?:true|1|yes)\s*$", compose):
        errors.append("Flag de acesso remoto habilitada por padrao.")
    try:
        manifest = json.loads(manifest_text)
        grants = [p.get("code", "") for p in manifest.get("permissions", [])]
        if any(isinstance(p, str) and p.startswith("it-portal.remote.") for p in grants):
            errors.append("Permissao de controle remoto registrada antes de G0-SEC.")
    except (TypeError, ValueError, AttributeError):
        errors.append("Manifesto do Portal nao pode ser auditado.")
    routes = root / "it-portal-api/it_portal_app/interface/http/routes"
    if not routes.is_dir():
        errors.append("Pasta de rotas de API nao encontrada.")
    elif any(
        ("remote" in file.name.lower() or "meshcentral" in file.name.lower())
        for file in routes.glob("*.py")
    ):
        errors.append("Arquivo de rota remota presente antes de G0-SEC.")

    if not errors:
        warnings.append("Este preflight NAO substitui aceite de seguranca, MFA, teste ou homologacao.")
    return Preflight(
        status="INVALID" if errors else "BLOCKED",
        pending=tuple(pending), documented=tuple(documented),
        errors=tuple(errors), warnings=tuple(warnings),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Preflight G0-SEC sem efeitos colaterais")
    parser.add_argument(
        "--repo-root", type=Path,
        default=Path(__file__).resolve().parents[3],
    )
    args = parser.parse_args()
    root = args.repo_root.resolve()
    try:
        registry = json.loads((root / REGISTRY_PATH).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        print("G0-SEC INVALID: manifesto nao localizado ou malformado.")
        return 1

    result = evaluate(root, registry)
    print(
        f"G0-SEC {result.status}: {len(result.pending)} pendente(s); "
        f"{len(result.documented)} documentado(s); "
        f"{len(result.errors)} erro(s) de seguranca."
    )
    for item in result.errors:
        print(f"ERRO: {item}")
    for item in result.warnings:
        print(f"NOTA: {item}")
    # CI verde significa que o BLOQUEIO continua seguro, NUNCA que o motor foi aprovado.
    return 0 if result.safe_to_continue_offline else 1


if __name__ == "__main__":
    raise SystemExit(main())
