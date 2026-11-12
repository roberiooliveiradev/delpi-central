# Minha DELPI — Homologação na VM srv-api — registro de continuidade

> **Atualizado:** 12/11/2026 · **Estado:** Portal + Core API + Gateway HML ativos em `http://192.168.1.237:18080`.  
> **Repositório:** `roberiooliveiradev/delpi-central`.  
> **TASK_ID:** `HML-CORE-PORTAL-01`.  
> **BASE_HEAD:** `24a7a8a144f2a009d6eacdc22eb248a7b074abab`.  
> **MAIN_INTEGRATED_SHA:** `86eef5aedc02775a2d1c77876b18bb76897f51d2` (Portal bake `__none__` + revert de plugins acidentais).  
> **SHA funcional Core/Portal auth:** `4f22f6a7b5` (cenários) + `86eef5aedc` (bundle sem URLs produtivas).

## 1. Objetivo e regras congeladas

Ambiente de homologação independente na mesma VM `srv-api`.

- Produção: `/home/operador/projetos/delpi-central`.
- Homologação: `/home/operador/projetos-teste/delpi-central`.
- Git: commit/push só no computador local; VM apenas `git pull --ff-only`.
- **Executado:** DBs → Keycloak → Gateway → **Core API** → **Portal**.
- **Ainda proibido:** Redis, API DELPI, Plugin UI, Production Control, restore produtivo, exposição internet.

## 2. REUSE GATE (Etapa 4)

| Capacidade | Decisão |
|---|---|
| Serviços Compose `core-api` / `portal` | **REUSE** via `extends` + profiles isolados |
| Dockerfiles Core/Portal | **REUSE** (`Dockerfile.prod`); Portal aceita `VITE_FRONT_CHANNEL_LOGOUT_URLS` |
| Migrations Core (Alembic `flask db upgrade`) | **REUSE** no entrypoint — destino só `delpi-hml-postgres-core` |
| `hml-compose.sh` | **EXTEND** — `up --scenario core-api|portal` |
| Bootstrap KC audience `delpi-central` | **EXTEND** — client scope `audience-delpi` |
| Redis | **REUSE** deferido — stores `memory`, `REDIS_URL=""` |
| plugin-ui / MFEs | **REUSE** deferido — shell Portal sem remotes |

## 3. Endpoint e OIDC

| Item | Valor |
|---|---|
| Entrada | `http://192.168.1.237:18080` (bind LAN) |
| Keycloak | `http://192.168.1.237:18080/auth/` |
| Issuer | `http://192.168.1.237:18080/auth/realms/delpi` |
| Audience | `delpi-central` |
| Client | `delpi-central` (PKCE S256) |
| Usuário | `hml-tester` (`hml-tester@hml.invalid`, sem superadmin) |

## 4. Gate A — Core API

- Imagem: `delpi-hml/core-api:local`
- Migrations aplicadas no volume HML: `alembic_version=u7v8w9x0y1` (28 tabelas)
- `/core-api/health` via gateway → **200**
- `/core-api/me` sem token → **401**
- Token HML (PKCE) → **200**, usuário reconhecido, `is_superadmin=false`
- Token com issuer produtivo sintético → **401**
- Rede exclusiva `delpi-hml-network`; Redis **não** iniciado

## 5. Gate B — Portal

- Imagem: `delpi-hml/portal:local` (bake `VITE_KC_*` HML + `VITE_FRONT_CHANNEL_LOGOUT_URLS=__none__`)
- `/` via gateway → **200**
- Bundle sem `minhadelpi.com.br`; contém `192.168.1.237:18080/auth`
- Login PKCE + `/core-api/me` + revoke logout → **PASS**
- MFEs/plugin-ui → **PENDING** (não iniciados)

## 6. Containers HML (7)

`postgres-core`, `keycloak-db`, `postgres-plugins`, `keycloak`, `gateway`, `core-api`, `portal` — todos healthy na rede `delpi-hml-network`.

## 7. Produção

IDs/`StartedAt` de containers críticos **inalterados** após Gate A e Gate B. Portas 80/443 intactas; 18080 só no IP LAN. Swap 0; mem ~14 GiB / 47 GiB.

## 8. Drift / pendências

- Drift `5c20be0311` (DÉLIA) permanece para owner DÉLIA.
- Commit `6e52cf94b3` incluiu paths PRC por engano; corrigido em `86eef5aedc` (revert dos plugins).
- Próxima etapa: Plugin UI / API DELPI / Redis sob autorização explícita.
- Expiração longa de sessão e navegação MFE: **PENDING**.

## 9. Referências

- `infra/docker-compose.hml.yml`, `infra/scripts/hml-compose.sh`
- `infra/scripts/keycloak-hml-bootstrap.sh`
- `portal/Dockerfile.prod`, `portal/src/state/AuthContext.tsx`
