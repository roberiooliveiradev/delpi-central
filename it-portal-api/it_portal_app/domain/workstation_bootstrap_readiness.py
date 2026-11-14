"""G2-S4-S2b: static fail-closed gate before workstation bootstrap exists.

This OFFLINE check does not provision, issue secrets, authorize enrollment,
or validate a live Keycloak/Windows device. A green CI means only that the
currently unapproved activation surfaces stay absent and fail-closed.
"""
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

FLAGS = (
    "IT_PORTAL_WORKSTATION_INGEST_ENABLED",
    "IT_PORTAL_WORKSTATION_DB_BINDINGS_ENABLED",
    "IT_PORTAL_WORKSTATION_REVOKE_ENABLED",
    "IT_PORTAL_WORKSTATION_PROVISIONING_ENABLED",
)
FILES = {
    "compose": "infra/docker-compose.yml",
    "keycloak": "it-portal-api/it_portal_app/infrastructure/gateways/keycloak_workstation_provisioner.py",
    "identity": "it-portal-api/it_portal_app/application/workstation_identity_service.py",
    "migration": "it-portal-api/migrations/V013__workstation_dynamic_binding_revocation.sql",
    "installer": "it-portal-api/collectors/windows_workstation/Install-ItPortalWorkstationAgent.ps1",
}
ROUTES = "it-portal-api/it_portal_app/interface/http/routes"


@dataclass(frozen=True)
class BootstrapPreflight:
    status: str
    errors: tuple[str, ...]
    warnings: tuple[str, ...]

    @property
    def ci_pass(self) -> bool:
        return self.status == "BLOCKED" and not self.errors

    @property
    def bootstrap_authorized(self) -> bool:
        # Public source and CI can never approve live enrollment.
        return False


def _read(root: Path, relative: str, errors: list[str]) -> str:
    try:
        path = root / relative
        if not path.is_file() or path.stat().st_size > 1_000_000:
            raise OSError("file missing or oversize")
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        errors.append(f"Arquivo obrigatorio indisponivel: {relative}.")
        return ""


def evaluate(root: Path) -> BootstrapPreflight:
    """Inspect versioned source only; never touch Keycloak, DB, OS or network."""
    errors: list[str] = []
    data = {key: _read(root, rel, errors) for key, rel in FILES.items()}
    compose = data["compose"]
    for flag in FLAGS:
        escaped = re.escape(flag)
        declared = re.findall(rf"(?m)^\s*{escaped}:\s*\$\{{{escaped}:-([^}}]+)\}}\s*$", compose)
        if declared != ["false"]:
            errors.append(f"Compose precisa de uma unica flag OFF por padrao: {flag}.")
    if re.search(r"(?m)^\s*IT_PORTAL_WORKSTATION_BOOTSTRAP_ENABLED:\s*\S+", compose):
        errors.append("Nao introduzir flag operacional de bootstrap antes do gate privado.")

    keycloak = data["keycloak"]
    for token in (
        '"enabled": False', '"publicClient": False',
        '"fullScopeAllowed": False', '"defaultClientScopes": []',
        '"optionalClientScopes": []',
        'observed.get("enabled") is not False',
    ):
        if token not in keycloak:
            errors.append("Client Keycloak nao comprova estado DISABLED e sem grants.")
            break
    if re.search(r'"enabled"\s*:\s*True\b', keycloak):
        errors.append("Ativacao Keycloak nao autorizada no provisionador G2-S4.")

    migration = data["migration"]
    if not re.search(r"ADD\s+COLUMN\s+ingest_authorized\s+BOOLEAN\s+NOT\s+NULL\s+DEFAULT\s+FALSE\b", migration, re.I):
        errors.append("V013 deve criar ingest_authorized DEFAULT FALSE.")
    if re.search(r"UPDATE\s+\S+\s+SET\s+ingest_authorized\s*=\s*TRUE\b", migration, re.I):
        errors.append("Migration historica nao pode conceder ingestao.")

    identity = data["identity"]
    if ('"credentials_issued": False' not in identity
            or '"remote_access_enabled": False' not in identity):
        errors.append("Status da identidade nao pode anunciar credencial/remoto ativos.")
    revocation = identity.find("self.store.request_revocation(")
    disable = identity.find("self.provisioner.disable_client(")
    if revocation < 0 or disable < 0 or revocation >= disable:
        errors.append("Revogacao deve bloquear no DB antes de desabilitar Keycloak.")

    installer = data["installer"]
    for marker in (
        "if (-not $Activate) { return }", "New-ScheduledTaskSettingsSet -Disable",
        "-LogonType Interactive", "ConvertFrom-SecureString",
    ):
        if marker not in installer:
            errors.append("Instalador Windows deve permanecer PLAN / disabled / DPAPI.")
            break

    routes = root / ROUTES
    if not routes.is_dir():
        errors.append("Diretorio de rotas HTTP ausente.")
    else:
        for path in routes.glob("*workstation*.py"):
            if any(part in path.name.lower() for part in ("bootstrap", "enroll", "activation")):
                errors.append("Nova rota de bootstrap sem revisao formal.")
                break
            try:
                source = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                errors.append("Rota workstation nao pode ser inspecionada.")
                continue
            # Deliberately inspect route declarations, not free-form documentation.
            declarations = re.findall(
                r'@router\.(?:post|get|put|patch|delete)\(\s*["\']([^"\']+)', source
            )
            if any(re.search(r"/(?:bootstrap|enroll|activate|credentials|token)(?:/|$)", url, re.I)
                   for url in declarations):
                errors.append("Endpoint de emissao/ativacao do agente introduzido antes de HML.")
                break

    return BootstrapPreflight(
        status="INVALID" if errors else "BLOCKED",
        errors=tuple(dict.fromkeys(errors)),
        warnings=("Gate offline; ambiente HML e Windows real NAO avaliados.",),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="G2-S4-S2b preflight offline (esperado: BLOCKED)")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    result = evaluate(args.repo_root.resolve())
    print(f"G2-S4-S2b {result.status}: {len(result.errors)} erro(s). Ativacao NAO autorizada.")
    for err in result.errors:
        print(f"ERRO: {err}")
    return 0 if result.ci_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
