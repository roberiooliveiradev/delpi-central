# 53 — EVA.ENGINEERING.FULL.CAPABILITY.PARITY: CRUD governado, paridade funcional e homologação MCP

**Status:** IMPLEMENTADO + HOMOLOGADO EM DEV — ACT produtivo permanece gateado (`ENG_EVA_ACT_ENABLED` ausente em produção).
**Missão:** EVA.ENGINEERING.FULL.CAPABILITY.PARITY (P1–P8).
**Baseline:** `origin/main` real — reancorado durante a execução (ver §10 EXECUTION_DRIFT).
**Commits:** `98d746a6b4` (P1–P5 código + testes); wiring prod do flag varreu por commit concorrente `54880eb6e9` (§10).

---

## 1. Inventário completo Engineering API ↔ EVA (P1)

Todas as operações efetivamente registradas na Engineering API no HEAD de baseline foram inventariadas por leitura de rotas — não por roadmap.

### Rotas REST existentes (`/v1`)

| Operação | Método/rota | Contrato | Classe |
|---|---|---|---|
| get_engineering_home | GET `/v1/home` | E-HOME | READ |
| get_engineering_overview | GET `/v1/overview` | E-OV-01 | READ |
| list_lmps | GET `/v1/lmps` | F-LMP-01 | READ |
| get_lmp_summary | GET `/v1/lmps/summary` | F-LMP-KPI | READ |
| get_lmp_goal_context | GET `/v1/lmps/goal-context` | delegação SI | READ |
| get_lmp_department_idd | GET `/v1/lmps/department-idd` | delegação SI | READ |
| get_lmp_nc_streak | GET `/v1/lmps/nonconformities/streak` | delegação NC | READ |
| get_lmp_history_events | GET `/v1/lmps/{sale_number}/history/events` | F-LMP-HIST | READ |
| get_lmp_history_flow | GET `/v1/lmps/{sale_number}/history/flow` | F-LMP-HIST | READ |
| get_lmp_detail | GET `/v1/lmps/{sale_number}` | F-LMP-02 | READ |
| get_product_structure | GET `/v1/products/{code}/structure` | E-PRD-01 delegação | READ |
| list_nonconformities | GET `/v1/nonconformities` | E-NC-01 | READ |
| get_nonconformity | GET `/v1/nonconformities/{id}` | E-NC-02 | READ |
| get_nonconformity_history | GET `.../{id}/history` | E-NC-03 | READ |
| get_nonconformity_indicators | GET `.../indicators` | E-NC-04 | READ |
| list_problem_tags | GET `.../problem-tags` | E-NC-05 | READ |
| export_nonconformities | GET `.../export` | E-NC-06 | READ |
| get_nonconformity_context | GET `.../{id}/context` | E-NC-11 | READ |
| prepare_nonconformity | POST `.../prepare` | E-NC-PREP | PREPARE |
| create_nonconformity | POST `.../` | E-NC-07 | WRITE |
| update_nonconformity | PUT `.../{id}` | E-NC-08 full-replace+ETag | WRITE |
| delete_nonconformity | DELETE `.../{id}` | E-NC-09 cascade | WRITE |
| import_nonconformities | POST `.../import` | E-NC-10 dry_run/confirm_replace | WRITE destrutiva |

### Matriz de paridade funcional (ledger)

`OWNER | CONTRACT | INTENT | TOOL | CLASSE | AUTHZ | RISCO | TESTE | OUTCOME | STATUS`

| Contrato REST | EVA tool | Classe | Confirmação | Idempotência/Concorrência | Postcondition | Status |
|---|---|---|---|---|---|---|
| GET /v1/home | `get_engineering_home` | READ | — | — | — | PROVEN |
| GET /v1/overview | `get_engineering_overview` | READ | — | — | — | PROVEN |
| GET /v1/lmps | `list_lmps` | READ | — | — | — | PROVEN |
| GET /v1/lmps/summary | `get_lmp_summary` | READ | — | — | — | PROVEN |
| GET /v1/lmps/goal-context | `get_lmp_goal_context` | READ | — | — | — | PROVEN |
| GET /v1/lmps/department-idd | `get_lmp_department_idd` | READ | — | — | — | PROVEN |
| GET /v1/lmps/nc-streak | `get_lmp_nc_streak` | READ | — | — | — | PROVEN |
| GET /v1/lmps/{sn}/history/* | `get_lmp_history` (view=events\|flow) | READ | — | — | — | PROVEN |
| GET /v1/lmps/{sn} | `get_lmp_detail` | READ | — | — | — | PROVEN |
| GET /v1/products/{c}/structure | `get_product_structure` | READ | — | — | — | PROVEN |
| GET /v1/nonconformities | `search_nonconformities` | READ | — | — | — | PROVEN |
| GET .../{id} | `get_nonconformity` | READ | — | — | — | PROVEN |
| GET .../{id}/history | `get_nonconformity_history` | READ | — | — | — | PROVEN |
| GET .../indicators | `get_nonconformity_indicators` | READ | — | — | — | PROVEN |
| GET .../problem-tags | `get_nonconformity_tags` | READ | — | — | — | PROVEN |
| GET .../{id}/context | `get_nonconformity_context` | READ | — | — | — | PROVEN |
| GET .../export | `export_nonconformities` | READ | — | — | — | PROVEN |
| POST .../prepare | `prepare_nonconformity_mutation` | PREPARE | n/a (zero efeitos) | — | — | PROVEN |
| POST /v1/nonconformities | `create_nonconformity` | ACT | `confirmed=true` obrigatório | `idempotency_key` (contrato) | read-back GET | PROVEN (dev) |
| PUT .../{id} | `update_nonconformity` | ACT | `confirmed=true` | `expected_updated_at` → 409 | read-back GET | PROVEN (dev) |
| DELETE .../{id} | `delete_nonconformity` | ACT destrutiva | `confirmed=true` reforçada | 404 idempotente | read-back → 404 | PROVEN (dev) |
| POST .../import | `import_nonconformities` | ACT destrutiva | `confirmed=true` + `confirm_replace=true` + `dry_run=false` | relatório por item | relatório de contagem | PROVEN (dev dry-run) |

**Cobertura:** 23/23 intents — 17 READ + 1 PREPARE + 4 ACT + 1 DISCOVERY. Nenhuma rota REST ficou sem intenção EVA correspondente; nenhum WRITE artificial foi criado sobre contrato READ-only.

Capacidades ainda `not_implemented` (catalog `planned_capabilities`): produtos DELPI completos, BOM/roteiros independentes, desenhos/especificações/inspeções — sem contrato oficial; permanecem PLANNED, nunca executáveis.

---

## 2. Contratos ACT governados (P2)

Fluxo canônico implementado:
`USER REQUEST → INTENT → GROUNDING → PREPARE → AUTHZ → CONFIRMATION → ACT → VERIFY → AUDIT → RESPONSE`

- **`confirmed` (bool, obrigatório em toda ACT):** asserção do chamador de que o usuário autorizou explicitamente; `false`/ausente → `confirmation_required` (400, `error_kind=confirmation`). Não é autorização — é política de confirmação; a AuthZ efetiva continua sendo Core live a cada chamada.
- **`ENG_EVA_ACT_ENABLED` (env, fail-closed):** ausente/false → `act_disabled` (403) em toda tool ACT, inclusive dry-run de import. Produção: desabilitado até autorização operacional específica (gate EVA-P8).
- **`NC_WRITABLE_FIELDS`:** espelho dos campos graváveis de `normalize_nc_payload`; UPDATE rejeita chaves fora do contrato em vez de descartar typo do agente.
- **Update merge:** `changes` parcial + registro corrente → payload full-replace completo (nunca apaga campos não informados); `expected_updated_at` do GET alimenta o optimistic lock, ou o caller fornece explicitamente.
- **Postcondition read-back:** create → GET confirma existência; update → GET confirma `updated_at` novo; delete → GET espera 404; import → relatório de contagens é o outcome. Falha de read-back é reportada honestamente (`verified=false`), nunca sucesso afirmado.
- **`DESTRUCTIVE_ACT_TOOLS = {delete_nonconformity, import_nonconformities}`** → `destructiveHint=true` no wire MCP + política `reinforced_explicit_confirmation` no catálogo.
- **Ator:** `nc_actor_from_principal` canonizado em `application/use_cases/nonconformity/actor.py` (fonte única REST+MCP) — o `NcActor` registrado no histórico é sempre o humano autenticado.

## 3. Identidade, segurança e OAuth MCP (P4)

- Transporte inalterado: `TRANSPORT_REQUIRES_OAUTH`, audience exata do resource (`MCP_RESOURCE_URL`), scope `mcp:tools`, service token rejeitado (401) — guardas já existentes no middleware.
- `_require_engineering_human()` idêntico às rotas: `principal_type=="user"` + `has_any_permission(engineering.access)` (ou superadmin) — fail-closed por chamada.
- `_source_context()` propaga o Bearer humano a fontes delegadas (api-delpi facts, SI owner, NC owner) — nenhum service token, nenhuma elevação.
- Provisionamento dev: client `mcp-engineering` criado no realm dev (confidential, standard flow + PKCE S256, direct access apenas dev, escopos default `mcp:tools` + `mcp-audience-engineering` → `http://localhost/apps/engineering-api/mcp` + `audience-delpi`). Produção: doc 28 continua governando — client `mcp-engineering` prod com audience `https://minhadelpi.com.br/apps/engineering-api/mcp` é task administrativa pendente (PENDING_ADMIN), sem direct access.
- Tokens nunca são argumentos de tool, logs ou resultados — identidade vem do contexto validado pelo middleware.

## 4. Homologação (P7)

### Testes automatizados (container delpi-engineering-api)

- `tests/test_eva_mcp.py`: **61/61** — contract freeze (23 nomes, classes, DESTRUCTIVE_ACT_TOOLS), list_tools wire (oauth schemes, annotations readonly/destructive), transport AuthN negativas, catálogo (`act_enabled`, `write_tools`, confirmação), ACT gate/confirm/merge/409/postcondition/not-found/dry-run/unsafe, delegações LMP/produto com `access_token` humano, service-principal rejeitado em todas as tools.
- Suíte completa: **436 passed, 10 skipped** (skips = adapter Postgres exigindo sandbox dedicado, inalterado).
- `test_architecture.py`: sem import cruzado; `mcp`/`delpi_mcp` confinados a `interface/mcp`; `psycopg` confinado a `infrastructure/persistence` — EVA não toca banco.

### E2E OAuth MCP real (dev, dataset sandbox NC)

Token real via Keycloak dev (`mcp-engineering`, password grant do usuário humano) → `POST /apps/engineering-api/mcp`:

| Cenário | Resultado |
|---|---|
| initialize | 200 + instructions EVA novas |
| tools/list | 23 tools, annotations corretas |
| get_catalog | `act_enabled: true`, 4 write_tools |
| search_nonconformities | 2 registros sandbox |
| prepare create | `valid:true`, `side_effects:"none"` |
| create sem confirmed | 400 `confirmation_required` |
| create confirmed + key | id `0aca7cf2…`, `postcondition.verified`, `created_by="Rober Dev"` |
| replay mesma idempotency_key | mesmo id (dedup efetiva) |
| update changes | status in_progress, merge preservou campos, postcondition ok |
| update com etag obsoleto | 409 `concurrency_conflict` |
| get history | eventos created/updated com actor `Rober Dev` (humano) |
| delete sem confirmed | 400 `confirmation_required` |
| delete confirmed | deleted + `read_back_gone` |
| get pós-delete | 404 honesto |
| import dry_run | relatório `would_replace_all`/`would_create`, zero deletes |
| export | `count:2`, `version:1` |
| sem token | 401 |
| token portal (sem aud MCP) | 401 |
| list_lmps | `status: unavailable`/`service_auth_unavailable` — degradação honesta (S2S facts não provisionado neste container dev; não é defeito EVA) |
| get_lmp_nc_streak | `available` |

**Actor audit:** histórico gravou `actor_name="Rober Dev"` — identidade humana do token, não principal de serviço. EVA-FULL-04/13 comprovados.

## 5. Readiness produtiva (P8)

- `ENG_EVA_ACT_ENABLED`: wiring adicionado a `infra/docker-compose.yml` (prod) e `infra/docker-compose.dev.yml`; default vazio = desabilitado. Habilitação prod exige autorização operacional + aprovação owner Engenharia.
- `mcp-engineering` prod: doc 28 (client confidential, redirect URIs do Plugin, audience exata, sem direct access) — PENDING_ADMIN.
- Import destrutiva: mesmo com EVA ACT habilitado, substituição total segue exigindo `confirm_replace` + `ENG_NC_IMPORT_REPLACE_ENABLED` no adapter — dois gates independentes.
- Rollback: desabilitar `ENG_EVA_ACT_ENABLED` ou o client `mcp-engineering` → superfície mutável fail-closed sem impacto em `/v1` REST ou Portal.
- Nenhum ACT produtivo executado; nenhuma importação destrutiva em produção; nenhum grant novo criado — `engineering.access` permanece a única permissão operacional.

## 6. Decisões e residuais

- Confirmação é modelo conversacional (asserção `confirmed=true` + política no contrato/instruções), não selo server-side — padrão suficiente para o risco; evolução para propostas seladas (estilo CLARA `governed_writes`) fica como decisão arquitetural futura se o owner exigir tamper-evidence.
- Auditoria NC registra o ator humano; marcador de canal `mcp/eva` nos eventos não existe (histórico não distingue superfície) — residual registrado, sem mudança de schema.
- `list_lmps` em dev retorna `unavailable` (S2S facts não provisionado no container) — degradação honesta validada; em prod o S2S `engineering-facts.read` já está provisionado (G4.A.R2).
- `engineering.manage` continua restrito a administração — não concede access operacional; nenhuma permissão nova foi criada.

## 10. EXECUTION_DRIFT

1. `origin/main` moveu durante a execução (`f893befd80` → `891aa0483c`, trabalho concorrente supplies/market-intelligence) — reancoragem automática, sem conflito de código.
2. O commit concorrente `54880eb6e9` varreu a adição não commitada de `ENG_EVA_ACT_ENABLED` em `infra/docker-compose.yml` (prod) para seu diff — conteúdo idêntico ao planejado; atribuição de gate registrada aqui.
3. Falhas transitórias WSL durante execução — comandos reexecutados, sem impacto de produto.
