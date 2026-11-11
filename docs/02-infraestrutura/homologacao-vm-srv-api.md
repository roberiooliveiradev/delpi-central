# Minha DELPI — Homologação na VM srv-api — registro de continuidade

> **Atualizado:** 11/11/2026 · **Estado:** Compose HML na `main`; **três PostgreSQL HML ativos** e isolados; apps/Keycloak/gateway **não** iniciados.  
> **Repositório:** `roberiooliveiradev/delpi-central`.  
> **TASK_ID:** `HML-COMPOSE-PUBLISH-AND-DATABASES-01`.  
> **SHA integrado:** `211fa666378f28cb2b020c7af0b27f57bfeb5219` (`main`).  
> **HEAD base observado na reancoragem:** ancestral `a531cba71e5f` confirmado; publicação sobre `b6f3e4e392` → `ab1d59557f` (compose) → `211fa66637` (modo +x do script).

## 1. Objetivo e regras congeladas

Ambiente de homologação independente na mesma VM `srv-api`, sem interferir em produção.

- Produção: `/home/operador/projetos/delpi-central`.
- Homologação: `/home/operador/projetos-teste/delpi-central`.
- Git: commit/push só no computador local; VM apenas `git pull --ff-only`.
- **Autorizado e executado nesta rodada:** somente `postgres-core`, `keycloak-db`, `postgres-plugins` do projeto `delpi-hml`.
- **Ainda proibido:** Keycloak app, Core API, Portal, Production Control, gateway, migrations de apps, restore sanitizado, exposição intranet.

## 2. Situação factual e evidências

| Frente | Estado | Evidência |
|---|---|---|
| VM | **PROVEN** | 16 vCPUs; ~47 GiB RAM; disco `/dev/sda2` ~394G (~227G livres); swap 8G `/dev/sdb` (0B usado antes/depois). |
| Compose HML | **PASS / na main** | `infra/docker-compose.hml.yml` + script/testes/gateway HML + docs. |
| Isolamento estático | **PASS** | `hml-compose.sh validate` local e na VM → `HML_COMPOSE_ISOLATION=PASS`. |
| `.env.hml` | **PASS (não versionado)** | Criado no checkout HML a partir de `env.hml.example`; mode `0600`; placeholders `CHANGE_ME_*` substituídos; **não** copiado de produção. |
| Bancos HML | **PASS / running healthy** | `delpi-hml-postgres-core`, `delpi-hml-keycloak-db`, `delpi-hml-postgres-plugins`. |
| Produção | **PRESERVADA** | IDs/`StartedAt` de `delpi-postgres-core`, `delpi-keycloak-db`, `delpi-postgres-plugins`, `delpi-gateway`, `delpi-core-api` inalterados após o `up` HML. |
| Keycloak HML | **NÃO INICIADO** | Pin `quay.io/keycloak/keycloak:24.0`; digest produtivo observado `sha256:f8ade94c1d0ad2f2fa7734a455fee5392764f402c43ca35e9af6bf63a2541dc9`; issuer placeholder `hml.delpi.invalid` (não `127.0.0.1` permanente). |
| Apps/gateway HML | **NÃO INICIADOS** | Apenas os 3 containers `delpi-hml-*` existem. |

### Recursos criados

| Tipo | Nome |
|---|---|
| Rede | `delpi-hml-network` |
| Volumes | `delpi-hml-postgres-core`, `delpi-hml-keycloak`, `delpi-hml-postgres-plugins` |
| Containers | `delpi-hml-postgres-core` (`postgres:15`), `delpi-hml-keycloak-db` (`postgres:15`), `delpi-hml-postgres-plugins` (`pgvector/pgvector:pg15`) |

Limites aplicados: core/plugins `1g`/1.0 CPU; keycloak-db `768m`/0.5 CPU. Memória observada ~25 MiB por banco HML.

### Isolamento dos bancos

- Rede exclusiva `delpi-hml-network` (sem `infra_delpi-network`).
- Volumes distintos dos produtivos (`infra_postgres_*` / `infra_keycloak_data`).
- Sem portas publicadas no host.
- Conexão interna OK (`psql` via `docker exec`); schemas `public` com **0** tabelas (só init controlado / vazio — sem restore).
- Checkout HML em `211fa66637`.

### REUSE GATE

| Capacidade | Decisão |
|---|---|
| Compose prod via `extends` + `!override` | **REUSE** |
| Subida sequencial `--no-deps` | **EXTEND** em `hml-compose.sh` |
| Novo mecanismo paralelo de deploy | **NEW rejeitado** |

## 3. Próxima fila

| Ordem | Entrega | Estado |
|---|---|---|
| 1 | Publicar Compose + ativar 3 PostgreSQL | **CONCLUÍDO (executor; sem autoaceite)** |
| 2 | Definir hostname HTTPS intranet + clients OIDC HML | **PENDING** |
| 3 | Bootstrap Keycloak HML (sem cadastro produtivo) | **BLOQUEADO até autorização** |
| 4 | Apps/Portal/gateway HML | **BLOQUEADO** |
| 5 | Restore sanitizado de dados | **BLOQUEADO** |

## 4. Protocolo de retomada

1. Reancorar `origin/main` e este documento.
2. Operar só no checkout `projetos-teste` com `hml-compose.sh`.
3. Não iniciar Keycloak/apps sem nova autorização explícita.
4. Não copiar `.env` de produção; não push a partir da VM.

**STOP:** qualquer referência a recurso produtivo; OOM/degradação; `up` fora de `databases`.

## 5. Referências

- [Docker Compose](./docker-compose.md) §5.1
- `infra/README-ambiente.md` (Homologação)
- `.cursor/rules/platform-delivery-runtime-operations.mdc`, `local-first-deploy.mdc`, `infra-sequential-container-startup.mdc`
