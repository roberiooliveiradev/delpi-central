# SURI-MCP-SUPPLIERS-DEPLOY-001 — Aceite de Deploy (2026-10-30)

Publicação da SURI MCP **V3** em produção: tool semântica `execute`
(suppliers create/update governados) com paridade de AuthZ, idempotência
durável, auditoria e rastreabilidade. OAuth/Keycloak/RBAC **inalterados**.

## Fonte

| Item | Valor |
|---|---|
| Repo | `roberiooliveiradev/delpi-central` |
| Impl V3 | `db8475454b` (WRITE-001) |
| Idempotência durável | `cbe02f655e` + fix `297068f1b7` (payload_hash VARCHAR) |
| Source SHA | `297068f1b745a2bc9ba41cf4b34b6a54540e3f5c` |
| Prod repo | `/home/operador/projetos/delpi-central` @ `297068f1b7` (clean) |

## Gates

| Gate | Resultado | Evidência |
|---|---|---|
| D0 REBASELINE | PASS | `db8475454b` ancestor de HEAD e origin/main; commits concorrentes (controllership/docs) fora do escopo; working tree conhecida |
| D1 WRITE SAFETY | PASS | Store durável `supplies.suri_execute_operations` (V005): claim atômico `INSERT … ON CONFLICT` por (actor, entity, action, idempotency_key) + `payload_hash`; `in_progress`/`completed`/`conflict`/`replayed`; fail-closed sem store. pg real (container postgres): **3/3** — replay mesmo payload → replay, payload divergente → conflict, claim concorrente → in_progress, escopo por ator/ação. Bug real corrigido: `CHAR(64)` padding divergia fingerprint → `VARCHAR(64)` + strip defensivo (`297068f1b7`). Negativos não alcançam REST real (registry fechado + schema `extra=forbid` + allowlists). Zero escrita de teste em fornecedores reais |
| D2 AUTHZ/CONTRACT | PASS | `can_use_operations` re-derivado por chamada (Core `supplies.access`, escopo de unidade); anônimo → 401; audience errada → 401; allowlists `POST/PUT_SUPPLIER_FIELDS`; update exige código+loja inequívocos; contrato V2 das 4 tools preservado (regressão verde) |
| D3 TESTS/BUILD | PASS | Suíte completa supplies-api: **786 coletados, todos PASS** (pg real incluído). Focados: **105 PASS** (suri_mcp + durable repo + migrations). Docker build prod OK; imagem inspecionada: `CATALOG_VERSION=3`, `tools/list` = 5 tools, `supplier_execute` importável; `docker compose` recreate bem-sucedido |
| D4 DEPLOY PREP | PASS | Imagens pré registradas; rollback = imagem anterior retida + compose recreate; V005 aditiva (V2 ignora a tabela); script/compose revalidados; conjunto mínimo = apenas `supplies-mcp` (BFF não requerida: refactor compatível + migration aplicada via runner canônico dentro do container MCP) |
| D5 PRODUCTION DEPLOY | PASS | `docker compose build supplies-mcp` → `up -d --no-deps supplies-mcp`; apenas `delpi-supplies-mcp` recriado; `migrations_runner up` aplicou V005; healthy, sem restart loop; gateway inalterado |
| D6 MCP/OAUTH SMOKE | PASS (público) / PENDENTE (autenticado usuário) | Metadata 200; challenge 401 + `WWW-Authenticate` correto; aud errada → 401 (`RESOURCE_AUDIENCE_MISMATCH` no log); service token → 401; `/healthz` 200; BFF `/health` 200; `initialize` sem Bearer → 401; container em execução lista 5 tools; `execute` ACT + `idempotentHint=true` + `mcp:tools`. Autenticado user-delegated: `mcp-supplies` não permite direct grants (por design) — exige fluxo OAuth browser do usuário |
| D7 CHATGPT COMPATIBILITY | PENDENTE (parcial) | `SERVER_TOOLS_LIST=PASS`; `CHATGPT_TOOL_DISCOVERY=PENDING`; `CHATGPT_AUTHENTICATED_CALL=PENDING`. OAuth/client/scopes inalterados; 4 tools V2 preservadas. Passo manual: o usuário deve atualizar/recarregar o conector SURI no ChatGPT para redescobrir tools; **não** reinstalar/alterar credenciais |
| D8 DOCUMENTATION | PASS | Este documento; matriz preserva status PROVEN das capacidades já evidenciadas; V2 histórico intacto |

## Imagens e containers

| Item | Valor |
|---|---|
| PREVIOUS MCP IMAGE | `infra-supplies-mcp` `7ec1ad6ea9d7` (2026-10-30 11:29 UTC) |
| NEW MCP IMAGE | `infra-supplies-mcp` `c622ed1b33de` (2026-10-30 14:13 UTC) |
| PREVIOUS BFF IMAGE | `infra-supplies-api` `8c87aefe1e66` (inalterada) |
| NEW BFF IMAGE | — (não rebuildada; não exigida pelo escopo) |
| CONTAINERS CHANGED | `delpi-supplies-mcp` apenas |

## Evidência de runtime

```text
delpi-supplies-mcp  → infra-supplies-mcp c622ed1b33de · Up (healthy) · /healthz 200
tools/list (container em execução) → ['get_context','read','analyze','knowledge','execute']
execute annotations → delpi/toolClass=ACT, idempotentHint=true, securitySchemes mcp:tools
GET  .well-known/oauth-protected-resource → 200 (resource=mcp, as=keycloak/delpi, scopes incl. mcp:tools)
GET/POST /mcp sem Bearer → 401 + WWW-Authenticate (realm=suri-mcp, resource_metadata correto)
Token KC client_credentials (aud=[delpi-central,realm-management,account]) → 401 RESOURCE_AUDIENCE_MISMATCH
GET /apps/supplies-api/health → 200 (BFF Flask preservada)
V005 suri_execute_operations → APLICADA (migrations_runner canônico)
```

## Rollback

1. `cd infra && docker tag c622ed1b33de …` não necessário — imagem anterior `7ec1ad6ea9d7` retida.
2. `git checkout <sha-anterior>` + `docker compose build supplies-mcp && up -d --no-deps supplies-mcp`, ou recriar apontando para a imagem retida.
3. V005 é aditiva: V2 não lê `suri_execute_operations`; tabela pode permanecer (ou `DROP TABLE supplies.suri_execute_operations` se revert permanente).
4. Keycloak/RBAC/gateway: nenhuma alteração feita — nada a reverter.
5. Sem compensação automática de escritas ERP (nenhuma escrita real foi executada neste deploy).

## Resíduos / próxima etapa

- `CHATGPT_TOOL_DISCOVERY` e `CHATGPT_AUTHENTICATED_CALL`: PENDING — exigem
  OAuth user-delegated via browser/ChatGPT (direct grants desabilitados por
  design; sem service-account de teste autorizado). Homologação de escrita real
  requer caso de negócio autorizado e rastreável — **não** inferida por este
  deploy (publicação do catálogo ≠ persistência ERP via ChatGPT).
- `SERVER_TOOLS_LIST = PASS` provado no container em execução.
- KC admin em `.env` permanece como recomendação anterior de rotação
  (fora do escopo desta missão).

## Status

```text
SURI_V3_SOURCE_IN_MAIN     PASS (297068f1b7)
SURI_WRITE_SAFETY_GATE     PASS (idempotência durável atômica, pg-proven)
SUPPLIES_MCP_DEPLOY        PASS
SUPPLIES_API_REGRESSION    PASS (786 testes)
SURI_MCP_HEALTH            PASS
OAUTH_DISCOVERY            PASS
OAUTH_AUDIENCE_ISOLATION   PASS
SURI_TOOL_COUNT            5
SURI_EXECUTE_DISCOVERY     PASS
SURI_EXECUTE_AUTHZ         PASS (401 anônimo/aud errada; unit-scope nos testes)
SUPPLIER_WRITE_CONTRACT    PASS
SURI_V2_REGRESSION         PASS
PRODUCTION_EVIDENCE        DOCUMENTED

STATUS: ACCEPT_WITH_RESIDUAL
```
