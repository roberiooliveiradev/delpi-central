# Minha DELPI — Homologação na VM srv-api — registro de continuidade

> **Atualizado:** 12/11/2026 · **Estado:** HTTP LAN configurado; **Keycloak HML ativo** + bootstrap mínimo; gateway/apps **não** iniciados.  
> **Repositório:** `roberiooliveiradev/delpi-central`.  
> **TASK_ID:** `HML-HTTP-KEYCLOAK-01`.  
> **BASE_HEAD:** `98e7657d4c311d14d7b1d3978d6b8930e98729b4`.  
> **MAIN_INTEGRATED_SHA:** `5c20be0311be9e1226a0cff082442b09ccdb5f73` (fix bootstrap); compose HTTP em `24beeff429`.

## 1. Objetivo e regras congeladas

Ambiente de homologação independente na mesma VM `srv-api`, sem interferir em produção.

- Produção: `/home/operador/projetos/delpi-central`.
- Homologação: `/home/operador/projetos-teste/delpi-central`.
- Git: commit/push só no computador local; VM apenas `git pull --ff-only`.
- **Executado nesta rodada:** inventário de portas; HTTP LAN `http://192.168.1.237:18080`; publish; `up --scenario keycloak`; bootstrap realm/client/usuário de teste.
- **Ainda proibido:** gateway HML, Portal, Core API, Production Control, restore, HTTPS público, exposição internet.

## 2. Inventário de portas (12/11/2026)

IP LAN: **192.168.1.237/24** (`ens192`). Porta **18080 livre** (bind OK em 127.0.0.1 / 192.168.1.237 / 0.0.0.0).

| Bind | Porta | Responsável | Finalidade |
|---|---|---|---|
| 0.0.0.0/:: | 80 | `delpi-gateway` + nginx host | Produção HTTP |
| 0.0.0.0 | 443/8443 | nginx host | Produção TLS |
| 0.0.0.0 | 22 | sshd | Admin |
| 0.0.0.0 | 5432 | Postgres host | Externo/local (não HML) |
| 0.0.0.0 | 8080 | GLPI | Inventário TI |
| 0.0.0.0 | 8082/8083/8085 | PAC / Evolution | Outros |
| 0.0.0.0 | 11434 | Ollama | LLM |
| 127.0.0.1 | 18088 | controle-mp-front | Controles MP |
| — | **18080** | **livre / reservada HML** | Entrada única HTTP HML |

**Decisão:** sem HTTPS nesta fase. Entrada única planejada `http://192.168.1.237:18080`. Sem publicar Postgres/Keycloak/APIs HML no host.

## 3. OIDC / Keycloak HML

| Item | Valor |
|---|---|
| Imagem | `quay.io/keycloak/keycloak@sha256:f8ade94c1d0ad2f2fa7734a455fee5392764f402c43ca35e9af6bf63a2541dc9` |
| Container | `delpi-hml-keycloak` (healthy), rede `delpi-hml-network` |
| DB | `delpi-hml-keycloak-db` exclusivo |
| Issuer | `http://192.168.1.237:18080/auth/realms/delpi` |
| Realm | `delpi` (`sslRequired=none`) |
| Client | `delpi-central` público, standard flow, **sem** direct grants |
| Redirect/WebOrigin | `http://192.168.1.237:18080/*` / `http://192.168.1.237:18080` |
| Usuário teste | `hml-tester` (sem roles admin) |
| Features | `token-exchange`, `admin-fine-grained-authz` |

Gateway HML **não iniciado** → login browser/Portal = **PENDING**.

## 4. Evidências runtime

| Teste | Resultado |
|---|---|
| Inventário portas / 18080 livre | **PASS** |
| `hml-compose.sh validate` | **PASS** |
| `up --scenario keycloak` (`--no-deps`) | **PASS** |
| Discovery OIDC + JWKS + issuer | **PASS** (interno via rede HML) |
| Bootstrap realm/client/user | **PASS** |
| Client isolation (sem prod / sem direct grants) | **PASS** |
| IDs produtivos inalterados | **PASS** |
| nginx -t isolado (sem rede Compose) | **INCONCLUSIVE** (upstream DNS) |
| Login Portal/browser em `:18080` | **PENDING** (gateway off) |
| Apps HML | **TEST_NOT_RUN** / bloqueado |

Containers HML ativos: `postgres-core`, `keycloak-db`, `postgres-plugins`, `keycloak`. Sem portas host.

## 5. REUSE GATE

| Capacidade | Decisão |
|---|---|
| Compose extends + profiles | **EXTEND** (`keycloak`) |
| Admin REST de `keycloak-dev-bootstrap.sh` | **EXTEND** → `keycloak-hml-bootstrap.sh` |
| Deploy paralelo | **NEW rejeitado** |

## 6. Drift / pendências

- Commit `5c20be0311` também integrou artefatos DÉLIA que estavam staged por trabalho concorrente no momento do fix do bootstrap — registrar e não expandir.
- Próxima etapa autorizável: **gateway HML** em `192.168.1.237:18080` + validação browser do fluxo OIDC (ainda sem apps completas se desejado smoke-only).

## 7. Referências

- `infra/docker-compose.hml.yml`, `infra/env.hml.example`
- `infra/scripts/hml-compose.sh`, `infra/scripts/keycloak-hml-bootstrap.sh`
- `gateway/nginx.hml.conf`
