# Doc 55 — EVA MCP Semântico (6 tools): Execução do Plano Mestre 54

Status: `CODE_READY_DEV` — DEV homologado com OAuth MCP real; deploy produtivo condicionado a autorização operacional e aprovação de mudança de superfície pública MCP.
Owner: `engineering-api` (bounded context Engenharia).
Data: 2026-10-30. SHA testado: `8da7d0727c`.

## 1. Resumo

A superfície MCP da Engineering API passou de 23 tools técnicas por rota para **6 tools semânticas + 23 tools legacy mantidas em modo deprecated** (compatibilidade total — nenhum consumer quebrado). Dispatch semântico tipado (`ENTITY + ACTION + SCHEMA + AUTHZ + HANDLER + OUTCOME`) via `SEMANTIC_REGISTRY`, com allowlists explícitas — a EVA nunca envia URLs, métodos HTTP, SQL ou nomes de função.

## 2. As seis tools

| Tool | Classe | Responsabilidade |
| --- | --- | --- |
| `get_context` | READ/DISCOVERY | Catálogo de entidades/ações, authz, act_enabled, planned capabilities, limites de contexto |
| `read` | READ | Todas as consultas (17 intents legacy: catalog, directives, eva_context, engineering overview, 8 LMP, product structure, NC search/detail/history/indicators/tags/context/export) |
| `analyze` | ANALYSIS | Análises fundamentadas sobre dados oficiais (`nc.recurrence`, `lmp.idd`, `lmp.nc_streak`) com `data_class` CALCULATED + coverage |
| `knowledge` | READ | Guias técnicos versionados (`nc.guide`); tópicos planejados → `not_implemented` honesto |
| `execute` | ACT | CREATE/UPDATE diretos (baixo risco) + `mode=prepare`/`mode=commit` com proposta selada (alto risco) |
| `delete` | ACT | Exclusão governada exclusivamente por proposta selada |

## 3. Gates G0–G8

- **G0 — inventário real**: 23 tools legadas mapeadas 1:1 para ações semânticas em `SEMANTIC_REGISTRY`; zero intents perdidas.
- **G1 — contratos semânticos**: schemas versionados por operação (campos, limites, authz, risco, confirmação) no registry — catálogo declara `catalog_version`, `schema_version`, `act_enabled`.
- **G2 — get_context/read**: descoberta sob demanda (`entity`+`action`→schema detalhado) + todas as consultas delegadas aos handlers oficiais; resultados reempacotados com envelope `entity`/`action`.
- **G3 — analyze/knowledge**: `nc.recurrence` agrega indicadores por tags/período com cobertura explícita; `lmp.idd` e `lmp.nc_streak` delegam aos facts TOTVS; `nc.guide` serve corpus versionado (`eva_engineering_knowledge.json`, owner engineering-api, sources rastreáveis). Tudo declarado CALCULATED ou com fonte; nada inventado.
- **G4 — execute/delete**: create/update diretos com validação de schema, ETag e merge full-replace; delete e operações destrutivas exigem proposta selada HMAC (`proposal_ref` opaco, ator-vinculado, TTL 300s, single-use, forge → `proposal_not_found`, replay → 404). `ENG_EVA_ACT_ENABLED` fail-closed em prod.
- **G5 — orquestração**: `mode=prepare` + `mode=commit` no `execute`; import NC expõe `prepare` (dry-run) antes de commit; `delete` é sempre prepare→commit (2 chamadas explícitas). Orquestração real = sequência determinística governada, não promessa de atomicidade global.
- **G6 — compatibilidade**: legacy mantido como `LEGACY_TOOLS` com `_meta["delpi/deprecated"]=true`, `readOnlyHint`/`destructiveHint` por classe; consumer migration = janela de depreciação aberta até observação de adoção semântica.
- **G7 — homologação**: 44 testes semânticos (dispatch, registry, proposal lifecycle, knowledge grounding, analyze, authz, act_disabled, envelope) + 480 total engineering-api verdes; **E2E OAuth MCP real** (Keycloak `mcp-engineering`, JWT) comprova initialize→tools/list→get_context→read→analyze→knowledge→execute create/update/idempotent/409→delete prepare/commit/replay→import prepare.
- **G8 — readiness**: este documento; rollback = `git revert` dos commits do refactor (superfície volta a 23 tools puras) ou deploy do SHA anterior.

## 4. Mapa intents → semântica (ledger de paridade)

17 READ legacy → `read` com `entity`+`action` correspondentes. `get_engineering_capabilities` → `get_context` (catalog). `get_agent_directives`/`get_eva_context`/`get_engineering_overview`/`export_nc`/`list_lmps`/`lmp_summary`/`lmp_detail`/`lmp_history`/`lmp_goal_context`/`lmp_department_idd`/`lmp_nc_streak`/`product_structure`/`search_nc`/`get_nc`/`get_nc_history`/`get_nc_indicators`/`get_nc_tags`/`get_nc_context` → ações `read.*` correspondentes. `prepare_nonconformity_mutation` → `execute(mode=prepare)`. `create/update/import_nc` → `execute` (create/update direto; import via prepare→commit). `delete_nc` → `delete` (prepare→commit obrigatório). 23/23 preservadas.

## 5. Segurança e autoridade

- AuthZ inalterada: `_require_engineering_human` (`engineering.access`, human-only, superadmin igual às rotas) e `_require_eva_act` (`ENG_EVA_ACT_ENABLED` fail-closed) reusados sem alteração.
- Proposta selada: `minted` opaco HMAC SHA-256, vinculada a `actor_id`, `capability`, `target` (nonconformity_id), `version` (expected_updated_at), `payload`, `expires_at`; servidor resolve — modelo não forja.
- Sem SQL/URL/função livre; sem tokens em args; sem acesso direto ao DB (arch test preservado).
- `delete` nunca executa sem proposta válida e nunca aceita `confirmed=true` solto — prova de confirmação é a posse do `proposal_ref` mintado em prepare.

## 6. Evidência DEV (OAuth MCP real — 2026-10-30, container `delpi-engineering-api`)

- `tools/list`: 29 tools = 6 semânticas + 23 deprecated (`delpi/deprecated: true`).
- `get_context`: catalog_version 1.0, act_enabled=true (dev), entidades+ações por entidade.
- `read nc.search`: total=3, envelope `entity`/`action`; `engineering.overview`: `unavailable` honesto (facts S2S não provisionado no container dev — degradação conhecida; em prod provisionado desde G4.A.R2).
- `analyze nc.recurrence`: `data_class=CALCULATED`, coverage `analyzed=3/3 complete=true`.
- `knowledge nc.guide`: version 1.0, sources declaradas; tópico planejado → `not_implemented` 501.
- `execute nc.create` direto: NC criada, postcondition `verified:true` (read-back), replay com mesma `idempotency_key` → mesmo `record_id`.
- `execute nc.update` direto: merge full-replace preserva campos; `expected_updated_at` defasado → `409 concurrency_conflict`.
- `read nc.history`: 2 eventos com `actor=Rober Dev` (humano propagado).
- `delete` sem `proposal_ref` → `400 proposal_required`; `mode=prepare` → `proposal_ref` opaco + impacto; ref forjado → `proposal_not_found`; commit válido → deletada + postcondition `read_back_gone verified:true`; replay do mesmo ref → `404` (consumed); read após delete → `404`.
- `execute nc.import mode=prepare` → proposta selada + `dry_run_report` (sem efeito colateral).

## 7. Produção — condições de deploy

- Deploy via procedimento canônico SSH do repositório, somente após: (a) autorização operacional para mudança de superfície MCP pública; (b) decisão sobre retirada ou coexistência das tools deprecated em prod; (c) `mcp-engineering` client provisionado no realm prod (PENDING_ADMIN, doc 28).
- `ENG_EVA_ACT_ENABLED` permanece **desabilitado em prod** até autorização específica — publicar superfície não-destrutiva primeiro é o caminho seguro (get_context/read/analyze/knowledge funcionam sem ACT).
- Nunca declarar superfície produtiva como "somente 6 tools" enquanto as 23 legacy permanecerem expostas.
- Rollback: `git revert` dos commits do refactor ou redeploy do SHA `4a0f33f13d`/anterior (superfície 23-tools pura, sem `delpi/deprecated`).

## 8. Residuais

- Retirada efetiva das 23 legacy exige prova de consumo semântico (telemetria) + aprovação — gate de consumer migration.
- `lmp.idd`/`lmp.nc_streak` no `analyze` delegam aos mesmos facts TOTVS — análise calculada fica para iteração futura se facts expuserem séries; por ora são READ classificados.
- Orquestração multi-ação numa única chamada MCP (plano G5 pleno) é sequência explícita do modelo por enquanto — suportada, sem atomicidade global; um agregador `plan`/`steps` pode vir depois com schema próprio.
- `ENG_EVA_ACT_ENABLED` wiring prod pendente de autorização (intencional).
- `knowledge` cobre apenas `nc.guide` — desenhos, BOM, roteiros, matérias-primas, especificações e inspeções permanecem `not_implemented` até fontes oficiais.

## 9. Commits

- `60c2c8d706` — refactor semântico completo (registry, proposal_store, knowledge, bridge, server, constants, branding, directives, testes 44+).
- `4a0f33f13d` — merge com `origin/main` (docs concorrentes).
- `8da7d0727c` — fix envelope `structured_content` + merge (CLARA semantic plan concorrente).

Generated by Devin — EVA.MCP.SEMANTIC.R1.
