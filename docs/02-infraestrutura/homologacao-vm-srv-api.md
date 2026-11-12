# Minha DELPI — Homologação na VM srv-api — registro de continuidade

> **Atualizado:** 12/11/2026 · **Estado:** Gateway HTTP HML ativo em `192.168.1.237:18080`; Keycloak acessível; Portal/apps **não** iniciados.  
> **Repositório:** `roberiooliveiradev/delpi-central`.  
> **TASK_ID:** `HML-HTTP-GATEWAY-01`.  
> **BASE_HEAD:** `af5e5d06225770a69d7259e8d76a9dad8110c0d4`.  
> **MAIN_INTEGRATED_SHA:** `836ddf3c6d788b439bc05861daf5ab6227b53fcd` (gateway); docs/bootstrap follow-up em SHA posterior se aplicável.

## 1. Objetivo e regras congeladas

Ambiente de homologação independente na mesma VM `srv-api`.

- Produção: `/home/operador/projetos/delpi-central`.
- Homologação: `/home/operador/projetos-teste/delpi-central`.
- Git: commit/push só no computador local; VM apenas `git pull --ff-only`.
- **Executado:** gateway HML isolado + validação pública `/auth` + fluxo PKCE do `hml-tester`.
- **Ainda proibido:** Portal, Core API, API DELPI, Redis, Plugin UI, Production Control, restore, migrations de apps, exposição internet.

## 2. Causa raiz e correção (gateway)

**Causa:** `proxy_pass` estático para `portal`/`core-api`/`api-delpi` fazia o Nginx falhar no start quando os nomes não existiam na rede Docker; `depends_on` + healthcheck exigiam APIs.

**Correção (REUSE/EXTEND):**

| Capacidade | Decisão |
|---|---|
| `nginx.hml.conf` + resolver Docker | **EXTEND** — `set $upstream_*` + `error_page 502/504 → 503` controlado |
| `healthcheck.sh` produtivo | **REUSE** com `GATEWAY_HEALTHCHECK_PATHS=/auth/realms/master` |
| `hml-compose.sh` | **EXTEND** — `up --scenario gateway` (build + `--no-deps`) |
| Compose HML gateway | **EXTEND** — `depends_on: {}`, profile `gateway` |

## 3. Endpoint e OIDC

| Item | Valor |
|---|---|
| Entrada | `http://192.168.1.237:18080` (bind LAN; não `0.0.0.0`) |
| Keycloak | `http://192.168.1.237:18080/auth/` |
| Issuer | `http://192.168.1.237:18080/auth/realms/delpi` |
| Client | `delpi-central` (PKCE S256; sem direct grants) |
| Usuário | `hml-tester` |

## 4. Evidências runtime

| Teste | Resultado |
|---|---|
| `hml-compose.sh validate` + `nginx -t` | **PASS** |
| `up --scenario gateway` | **PASS** |
| `/auth/realms/master` / discovery / JWKS públicos | **PASS** |
| Issuer exato + sem `minhadelpi.com.br` | **PASS** |
| `/`, `/core-api/health`, `/apps/api-delpi/health` → 503 controlado | **PASS** |
| Direct grant desabilitado | **PASS** |
| PKCE + login `hml-tester` → authorization code (redirect HML) | **PASS** |
| Login completo no Portal Minha DELPI | **PENDING** (Portal off) |
| IDs produtivos inalterados | **PASS** |

Containers HML: `postgres-core`, `keycloak-db`, `postgres-plugins`, `keycloak`, `gateway` (healthy). Porta prod 80 intacta.

## 5. Drift / pendências

- Drift anterior `5c20be0311` (artefatos DÉLIA) permanece para revisão do owner DÉLIA — não alterado nesta tarefa.
- Bootstrap HML deve sincronizar perfil do `hml-tester` e desabilitar `VERIFY_PROFILE` default para evitar required-action no primeiro login.
- Próxima etapa: Portal/Core (ou smoke Portal-only) sob autorização explícita.

## 6. Referências

- `gateway/nginx.hml.conf`, `gateway/Dockerfile.hml`
- `infra/docker-compose.hml.yml`, `infra/scripts/hml-compose.sh`
- `infra/scripts/keycloak-hml-bootstrap.sh`
