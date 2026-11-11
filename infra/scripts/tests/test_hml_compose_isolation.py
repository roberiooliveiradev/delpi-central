#!/usr/bin/env python3
"""Inspeção estática do Compose de homologação.

Não executa up, build, pull, down, restart, stop ou rm.
`docker compose config` só renderiza YAML.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
INFRA = REPO / "infra"
GATEWAY = REPO / "gateway"
COMPOSE_FILE = INFRA / "docker-compose.hml.yml"
PROD_COMPOSE = INFRA / "docker-compose.yml"
ENV_EXAMPLE = INFRA / "env.hml.example"
NGINX_HML = GATEWAY / "nginx.hml.conf"
PROD_NGINX = GATEWAY / "nginx.conf"
HML_SCRIPT = INFRA / "scripts" / "hml-compose.sh"

DATABASES = {
    "postgres-core",
    "keycloak-db",
    "postgres-plugins",
}
BASELINE = {
    "postgres-core",
    "keycloak-db",
    "postgres-plugins",
    "delpi-redis",
    "keycloak",
    "core-api",
    "api-delpi",
    "portal",
    "plugin-ui",
    "production-control",
    "production-control-api",
    "gateway",
}
PLATFORM = BASELINE - {"production-control", "production-control-api"}
UPSTREAM_IMAGES = {
    "postgres:15",
    "pgvector/pgvector:pg15",
    "redis:7-alpine",
    "quay.io/keycloak/keycloak:24.0",
}
PROD_DATA_MARKERS = (
    "/var/lib/delpi",
    "/mnt/fileserver",
    "/home/michael",
    "/home/operador/projetos/delpi-central",
    "minhadelpi.com.br",
    "infra-production-control-api",
    "inventario-ti-glpi",
)
SOURCE_DENY = PROD_DATA_MARKERS + (
    "network_mode:",
    '"80:80"',
    "'80:80'",
    "11434:11434",
)


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def clean_env() -> dict[str, str]:
    kept = {}
    for key in ("PATH", "HOME", "DOCKER_HOST", "DOCKER_CONTEXT"):
        if os.environ.get(key):
            kept[key] = os.environ[key]
    kept["COMPOSE_PROJECT_NAME"] = "delpi-hml"
    return kept


def compose_config(profile: str | None) -> dict:
    cmd = [
        "docker",
        "compose",
        "--project-name",
        "delpi-hml",
        "--project-directory",
        str(INFRA),
        "-f",
        COMPOSE_FILE.name,
        "--env-file",
        ENV_EXAMPLE.name,
    ]
    if profile:
        cmd.extend(["--profile", profile])
    cmd.extend(["config", "--format", "json"])
    proc = subprocess.run(
        cmd,
        cwd=INFRA,
        env=clean_env(),
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-20:]
        fail("docker compose config falhou:\n" + "\n".join(tail))
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        fail(f"config JSON inválido: {exc}")


def prod_container_names() -> set[str]:
    text = PROD_COMPOSE.read_text(encoding="utf-8")
    return set(re.findall(r"container_name:\s*(\S+)", text))


def strip_hash_comments(text: str) -> str:
    lines = []
    for line in text.splitlines():
        if line.lstrip().startswith("#"):
            continue
        if " #" in line:
            line = line.split(" #", 1)[0]
        lines.append(line)
    return "\n".join(lines)


def assert_source_files() -> None:
    hml = COMPOSE_FILE.read_text(encoding="utf-8")
    nginx = NGINX_HML.read_text(encoding="utf-8")
    example = ENV_EXAMPLE.read_text(encoding="utf-8")
    script = HML_SCRIPT.read_text(encoding="utf-8")
    for label, text in (
        ("compose", strip_hash_comments(hml)),
        ("nginx", strip_hash_comments(nginx)),
        ("env", strip_hash_comments(example)),
    ):
        for marker in SOURCE_DENY:
            if marker in text:
                fail(f"{label} contém marcador produtivo: {marker}")
    if "name: delpi-hml" not in hml:
        fail("projeto Compose não é delpi-hml")
    if "name: delpi-hml-network" not in hml:
        fail("rede explícita delpi-hml-network ausente")
    if "profiles: [databases" not in hml and "profiles: [databases," not in hml:
        # tolerate whitespace variants
        if "databases" not in hml or "postgres-core" not in hml:
            fail("profile databases ausente no Compose")
    if re.search(r"set \$service delpi-", nginx):
        fail("nginx de homologação ainda roteia MFE para container delpi-*")
    if "listen 443" in nginx or "server_name minhadelpi.com.br" in nginx:
        fail("nginx de homologação publica produção")
    if "proxy_pass http://portal:80" not in nginx:
        fail("nginx de homologação não encaminha o portal")
    if "production-control-api:8000" not in nginx:
        fail("nginx de homologação não encaminha production-control-api")
    if PROD_NGINX.read_text(encoding="utf-8").find("server_name minhadelpi.com.br") < 0:
        fail("nginx de produção foi alterado e perdeu o server_name vigente")
    if "KEYCLOAK_ISSUER=http://127.0.0.1" in example or "KC_HOSTNAME=127.0.0.1" in example:
        fail("env.hml.example fixa 127.0.0.1 como issuer/hostname permanente")
    if "DELPI_HML_PUBLIC_HOST=" not in example or "hml.delpi.invalid" not in example:
        fail("origem pública parametrizada ausente no env de homologação")
    if "quay.io/keycloak/keycloak:24.0" not in hml:
        fail("Keycloak HML sem pin de versão 24.0 alinhado à produção")
    if "up --scenario databases" not in script:
        fail("script sem caminho autorizado de up databases")
    if "HOMOLOGATION_DATABASES_ONLY_AUTHORIZED" not in script:
        fail("script sem marcador de autorização databases-only")


def published_ports(service: dict) -> list[dict]:
    ports = service.get("ports") or []
    found = []
    for port in ports:
        if isinstance(port, dict):
            found.append(port)
        else:
            fail(f"porta em formato inesperado: {port!r}")
    return found


def bind_sources(service: dict) -> list[str]:
    sources = []
    for volume in service.get("volumes") or []:
        if not isinstance(volume, dict):
            fail(f"volume em formato inesperado: {volume!r}")
        if volume.get("type") == "bind":
            sources.append(str(volume.get("source") or ""))
    return sources


def assert_rendered(profile: str | None, expected: set[str]) -> dict:
    rendered = compose_config(profile)
    if rendered.get("name") != "delpi-hml":
        fail(f"nome renderizado {rendered.get('name')!r}")
    services = rendered.get("services") or {}
    names = set(services)
    if names != expected:
        fail(f"profile={profile!r} serviços {sorted(names)} != {sorted(expected)}")
    return rendered


def assert_isolation(rendered: dict, prod_names: set[str], *, require_gateway: bool) -> None:
    services = rendered["services"]
    networks = rendered.get("networks") or {}
    volumes = rendered.get("volumes") or {}
    if set(networks) != {"delpi-hml"}:
        fail(f"redes renderizadas: {sorted(networks)}")
    network = networks["delpi-hml"]
    if network.get("name") != "delpi-hml-network":
        fail(f"nome da rede {network.get('name')!r}")
    if str(network.get("driver") or "bridge") != "bridge":
        fail("rede de homologação não é bridge")
    for key, spec in volumes.items():
        explicit = (spec or {}).get("name") or key
        if not str(explicit).startswith("delpi-hml-"):
            fail(f"volume sem nome exclusivo: {explicit}")
        if explicit in {"postgres_core_data", "keycloak_data", "postgres_plugins_data", "ollama_data"}:
            fail(f"volume produtivo reutilizado: {explicit}")

    for name, service in services.items():
        if service.get("network_mode"):
            fail(f"{name} usa network_mode")
        if service.get("extra_hosts"):
            fail(f"{name} declara extra_hosts")
        if service.get("links"):
            fail(f"{name} declara links")
        container = service.get("container_name") or ""
        if not container.startswith("delpi-hml-"):
            fail(f"{name} container_name {container!r}")
        if container in prod_names:
            fail(f"{name} colide com container produtivo {container}")
        image = service.get("image") or ""
        if image in UPSTREAM_IMAGES:
            pass
        elif image.startswith("delpi-hml/") and image.endswith(":local"):
            pass
        else:
            fail(f"{name} imagem mutável ou inesperada: {image}")
        if "infra-production-control-api" in image:
            fail(f"{name} reutiliza tag de build da produção")
        labels = service.get("labels") or {}
        if labels.get("delpi.environment") != "homologation":
            fail(f"{name} sem label de homologação")
        attached = set((service.get("networks") or {}))
        if attached != {"delpi-hml"}:
            fail(f"{name} redes {sorted(attached)}")
        for port in published_ports(service):
            host_ip = str(port.get("host_ip") or "")
            published = str(port.get("published") or "")
            if host_ip != "127.0.0.1":
                fail(f"{name} publica em {host_ip or '0.0.0.0'}:{published}")
            if published in {"80", "443", "11434"}:
                fail(f"{name} publica porta ocupada pela produção: {published}")
        for source in bind_sources(service):
            resolved = Path(source).resolve()
            if not str(resolved).startswith(str(REPO.resolve())):
                fail(f"{name} bind fora do checkout: {source}")
            for marker in PROD_DATA_MARKERS:
                if marker in source:
                    fail(f"{name} bind produtivo: {source}")
        env = service.get("environment") or {}
        if isinstance(env, list):
            env = dict(item.split("=", 1) for item in env if "=" in item)
        blob = json.dumps(env)
        for marker in (
            "minhadelpi.com.br",
            "delpi-api-delpi",
            "delpi-minha-delpi-ai-api",
            "delpi-tv-dashboard-api",
            "delpi-production-pulse-api",
            "/var/lib/delpi",
            "/mnt/fileserver",
        ):
            if marker in blob:
                fail(f"{name} ambiente referencia {marker}")
        # Resource ceilings must exist for activated/planned services.
        if not (service.get("mem_limit") or (service.get("deploy") or {}).get("resources")):
            # compose config may normalize mem_limit into deploy; accept either
            fail(f"{name} sem limite de memória renderizado")

    if not require_gateway:
        for name in services:
            if published_ports(services[name]):
                fail(f"{name} não deveria publicar porta no profile databases")
        return

    api = services["api-delpi"]["environment"]
    if isinstance(api, list):
        api = dict(item.split("=", 1) for item in api if "=" in item)
    if api.get("DB_HOST") != "totvs-disabled.hml.invalid":
        fail("api-delpi não está presa ao host TOTVS desabilitado")
    if api.get("DB_DATABASE") != "DISABLED":
        fail("api-delpi não está com database TOTVS desabilitado")
    for key in (
        "OPENAPI_CONSUMER_NOTIFY_ENABLED",
        "PROTHEUS_SUPPLIER_CREATE_ENABLED",
        "PROTHEUS_SUPPLIER_UPDATE_ENABLED",
        "NOTIFICATIONS_DISPATCH_SCHEDULER_ENABLED",
    ):
        owner = services["api-delpi"]["environment"] if key != "NOTIFICATIONS_DISPATCH_SCHEDULER_ENABLED" else services["core-api"]["environment"]
        if isinstance(owner, list):
            owner = dict(item.split("=", 1) for item in owner if "=" in item)
        if key == "NOTIFICATIONS_DISPATCH_SCHEDULER_ENABLED":
            if str(owner.get(key)).lower() != "false":
                fail("scheduler de notificação do core não está desligado")
        elif str(owner.get(key)).lower() not in {"false", ""}:
            fail(f"{key} não está desligado")
    pc = services["production-control-api"]["environment"]
    if isinstance(pc, list):
        pc = dict(item.split("=", 1) for item in pc if "=" in item)
    if str(pc.get("PC_MES_CT_AUTONOMOUS_ENABLED")).lower() != "false":
        fail("monitoramento autônomo do PCP não está desligado")
    if pc.get("DELPI_API_URL") != "http://api-delpi:8000":
        fail("PCP não aponta para a api-delpi da rede de homologação")
    if pc.get("PRODUCTION_PULSE_API_URL") not in ("", None):
        fail("PCP ainda aponta para production-pulse")
    depends = services["production-control-api"].get("depends_on") or {}
    if "requests-api" in depends or "transformometro-api" in (services["api-delpi"].get("depends_on") or {}):
        fail("dependência de plugin fora do cenário permaneceu")
    gateway_ports = published_ports(services["gateway"])
    if len(gateway_ports) != 1 or str(gateway_ports[0].get("published")) != "18080":
        fail(f"gateway deveria publicar só 18080, veio {gateway_ports}")
    for name, service in services.items():
        if name != "gateway" and published_ports(service):
            fail(f"{name} não deveria publicar porta no host")


def assert_prod_source_unchanged() -> None:
    proc = subprocess.run(
        [
            "git",
            "diff",
            "--exit-code",
            "--",
            "infra/docker-compose.yml",
            "infra/docker-compose.dev.yml",
            "infra/docker-compose.minimal.yml",
            "infra/docker-compose.qa-override.yml",
            "infra/scripts/up-prod-sequential.sh",
            "infra/scripts/up-dev-sequential.sh",
            "gateway/nginx.conf",
            "gateway/Dockerfile.prod",
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        fail("arquivo de produção/dev foi modificado:\n" + (proc.stdout or proc.stderr))


def assert_databases_no_implicit_deps(rendered: dict) -> None:
    for name, service in rendered["services"].items():
        depends = service.get("depends_on") or {}
        if depends:
            fail(f"{name} no profile databases possui depends_on {sorted(depends)}")


def main() -> None:
    assert_prod_source_unchanged()
    assert_source_files()
    prod_names = prod_container_names()
    if "delpi-gateway" not in prod_names or "delpi-production-control-api" not in prod_names:
        fail("inventário de containers produtivos incompleto")
    empty = assert_rendered(None, set())
    if empty.get("services"):
        fail("config sem profile ainda publica serviços")
    databases = assert_rendered("databases", DATABASES)
    assert_isolation(databases, prod_names, require_gateway=False)
    assert_databases_no_implicit_deps(databases)
    platform = assert_rendered("platform", PLATFORM)
    if "production-control" in platform["services"]:
        fail("profile platform inclui Production Control")
    baseline = assert_rendered("baseline", BASELINE)
    assert_isolation(baseline, prod_names, require_gateway=True)
    print("HML_COMPOSE_ISOLATION=PASS")
    print(
        f"services_baseline={len(BASELINE)} services_databases={len(DATABASES)} "
        "network=delpi-hml-network port=127.0.0.1:18080"
    )


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 — relatório único de falha do ensaio
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
