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
# Profile keycloak inclui keycloak-db só para satisfazer depends_on no config;
# o up operacional usa --no-deps e sobe apenas o serviço keycloak.
KEYCLOAK_ONLY = {"keycloak", "keycloak-db"}
GATEWAY_ONLY = {"gateway"}
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
KEYCLOAK_DIGEST = (
    "quay.io/keycloak/keycloak@sha256:"
    "f8ade94c1d0ad2f2fa7734a455fee5392764f402c43ca35e9af6bf63a2541dc9"
)
UPSTREAM_IMAGES = {
    "postgres:15",
    "pgvector/pgvector:pg15",
    "redis:7-alpine",
    "quay.io/keycloak/keycloak:24.0",
    KEYCLOAK_DIGEST,
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
    if "set $upstream_portal portal:80" not in nginx:
        fail("nginx de homologação não encaminha o portal via upstream dinâmico")
    if "production-control-api:8000" not in nginx:
        fail("nginx de homologação não encaminha production-control-api")
    if PROD_NGINX.read_text(encoding="utf-8").find("server_name minhadelpi.com.br") < 0:
        fail("nginx de produção foi alterado e perdeu o server_name vigente")
    if "KEYCLOAK_ISSUER=http://127.0.0.1" in example or "KC_HOSTNAME=127.0.0.1" in example:
        fail("env.hml.example fixa 127.0.0.1 como issuer/hostname permanente")
    if "https://hml.delpi.invalid" in example or "KEYCLOAK_ISSUER=https://" in example:
        fail("env.hml.example ainda usa HTTPS placeholder nesta fase HTTP")
    if "DELPI_HML_PUBLIC_HOST=" not in example or "DELPI_HML_PUBLIC_ORIGIN=http://" not in example:
        fail("origem pública HTTP parametrizada ausente no env de homologação")
    if "DELPI_HML_BIND_ADDR=" not in example:
        fail("DELPI_HML_BIND_ADDR ausente no env de homologação")
    if KEYCLOAK_DIGEST not in hml and "quay.io/keycloak/keycloak@sha256:f8ade94c1d0ad2f2" not in hml:
        fail("Keycloak HML sem pin por digest alinhado à produção")
    if "profiles: [keycloak" not in hml and "keycloak, baseline" not in hml:
        fail("profile keycloak ausente no Compose")
    if "up --scenario databases" not in script or "up --scenario keycloak" not in script:
        fail("script sem caminhos autorizados databases/keycloak")
    if "up --scenario gateway" not in script:
        fail("script sem caminho autorizado de up gateway")
    if "HOMOLOGATION_DATABASES_KEYCLOAK_AND_GATEWAY_AUTHORIZED" not in script:
        fail("script sem marcador de autorização databases+keycloak+gateway")
    if "X-Forwarded-Port 18080" not in nginx:
        fail("nginx HML não fixa X-Forwarded-Port 18080 para redirects")
    if "set $upstream_keycloak" not in nginx or "set $upstream_portal" not in nginx:
        fail("nginx HML sem proxy_pass dinâmico para keycloak/portal")
    if "set $upstream_core_api" not in nginx or "set $upstream_api_delpi" not in nginx:
        fail("nginx HML sem proxy_pass dinâmico para core-api/api-delpi")
    if "@hml_upstream_unavailable" not in nginx:
        fail("nginx HML sem resposta controlada para upstream ausente")
    # Estáticos literais (sem variável) quebram o start sem o serviço.
    if re.search(r"proxy_pass http://core-api:8000", nginx):
        fail("nginx HML ainda tem proxy_pass estático para core-api")
    if re.search(r"proxy_pass http://portal:80", nginx):
        fail("nginx HML ainda tem proxy_pass estático para portal")
    if re.search(r"proxy_pass http://api-delpi:8000", nginx):
        fail("nginx HML ainda tem proxy_pass estático para api-delpi")
    if re.search(r"proxy_pass http://keycloak:8080", nginx):
        fail("nginx HML ainda tem proxy_pass estático para keycloak")
    if "profiles: [gateway" not in hml and "gateway, baseline" not in hml:
        fail("profile gateway ausente no Compose")
    bootstrap = INFRA / "scripts" / "keycloak-hml-bootstrap.sh"
    if not bootstrap.is_file():
        fail("keycloak-hml-bootstrap.sh ausente")
    boot = bootstrap.read_text(encoding="utf-8")
    if "directAccessGrantsEnabled\": False" not in boot and "directAccessGrantsEnabled\": false" not in boot:
        # script embeds JSON via python with False
        if "directAccessGrantsEnabled" not in boot:
            fail("bootstrap HML não declara política de direct grants")
    # Guardrails negativas (recusa se origem/client apontar produção) são OK.
    if re.search(r'(ORIGIN|URL|ISSUER)=https?://[^\\s]*minhadelpi\\.com\\.br', boot):
        fail("bootstrap HML configura URL produtiva")


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


def assert_isolation(
    rendered: dict,
    prod_names: set[str],
    *,
    require_gateway: bool,
    allow_gateway_port: bool = False,
) -> None:
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
        elif image.startswith("quay.io/keycloak/keycloak@sha256:"):
            if image != KEYCLOAK_DIGEST:
                fail(f"{name} digest Keycloak divergente: {image}")
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
            # Homologação: bind LAN específico (ex. 192.168.1.237) ou loopback.
            # Nunca 0.0.0.0/:: sem necessidade.
            if host_ip in {"", "0.0.0.0", "::", "*"}:
                fail(f"{name} publica em wildcard {host_ip or '0.0.0.0'}:{published}")
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
            ports = published_ports(services[name])
            if not ports:
                continue
            if allow_gateway_port and name == "gateway":
                if len(ports) != 1 or str(ports[0].get("published")) != "18080":
                    fail(f"gateway deveria publicar só 18080, veio {ports}")
                host_ip = str(ports[0].get("host_ip") or "")
                if host_ip in {"", "0.0.0.0", "::", "*"}:
                    fail(f"gateway publica em wildcard {host_ip!r}")
                continue
            fail(f"{name} não deveria publicar porta no profile isolado")
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
    host_ip = str(gateway_ports[0].get("host_ip") or "")
    if host_ip in {"", "0.0.0.0", "::"}:
        fail(f"gateway HML não deve bindar em wildcard ({host_ip!r})")
    gw_deps = services["gateway"].get("depends_on") or {}
    if gw_deps:
        fail(f"gateway HML não deve depender de apps nesta fase: {sorted(gw_deps)}")
    gw_env = services["gateway"].get("environment") or {}
    if isinstance(gw_env, list):
        gw_env = dict(item.split("=", 1) for item in gw_env if "=" in item)
    paths = str(gw_env.get("GATEWAY_HEALTHCHECK_PATHS") or "")
    if "/auth/realms/master" not in paths:
        fail("healthcheck do gateway HML deve focar /auth nesta fase")
    if "/core-api/health" in paths or "/apps/api-delpi/health" in paths:
        fail("healthcheck do gateway HML ainda exige APIs desligadas")
    for name, service in services.items():
        if name != "gateway" and published_ports(service):
            fail(f"{name} não deveria publicar porta no host")
    kc = services["keycloak"]
    kc_image = kc.get("image") or ""
    if KEYCLOAK_DIGEST not in kc_image and not kc_image.endswith(
        "f8ade94c1d0ad2f2fa7734a455fee5392764f402c43ca35e9af6bf63a2541dc9"
    ):
        fail(f"keycloak sem digest produtivo: {kc_image}")


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
    keycloak = assert_rendered("keycloak", KEYCLOAK_ONLY)
    assert_isolation(keycloak, prod_names, require_gateway=False)
    if "gateway" in keycloak["services"] or "core-api" in keycloak["services"] or "portal" in keycloak["services"]:
        fail("profile keycloak puxou apps/gateway")
    if set(keycloak["services"]) - {"keycloak", "keycloak-db"}:
        fail(f"profile keycloak com serviços extras: {sorted(keycloak['services'])}")
    gateway = assert_rendered("gateway", GATEWAY_ONLY)
    assert_isolation(gateway, prod_names, require_gateway=False, allow_gateway_port=True)
    gw = gateway["services"]["gateway"]
    if gw.get("depends_on"):
        fail(f"profile gateway ainda declara depends_on: {gw.get('depends_on')}")
    if set(gateway["services"]) != GATEWAY_ONLY:
        fail(f"profile gateway com serviços extras: {sorted(gateway['services'])}")
    platform = assert_rendered("platform", PLATFORM)
    if "production-control" in platform["services"]:
        fail("profile platform inclui Production Control")
    baseline = assert_rendered("baseline", BASELINE)
    assert_isolation(baseline, prod_names, require_gateway=True)
    print("HML_COMPOSE_ISOLATION=PASS")
    print(
        f"services_baseline={len(BASELINE)} services_databases={len(DATABASES)} "
        f"services_keycloak={len(KEYCLOAK_ONLY)} services_gateway={len(GATEWAY_ONLY)} "
        "network=delpi-hml-network port=${DELPI_HML_BIND_ADDR}:18080"
    )


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 — relatório único de falha do ensaio
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
