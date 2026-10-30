# Documento 123 — CLARA MCP Semântico: execução do plano CLARA-MCP-SEMANTIC-001

**Status:** `ACCEPT_WITH_RESIDUAL` — superfície semântica de seis tools
implantada e verificada em produção; cutover do host ChatGPT depende da
reconexão/atualização do conector (ação do usuário).
**Owner:** controllership-finance-api / Portal Controladoria & Finanças
**Data:** 2026-10-30 · **Executor:** Devin
**Matriz de migração:** `CLARA-MCP-SEMANTIC-001-capability-matrix.md` (mesmo diretório)

## 1. O que mudou

O `tools/list` público do servidor MCP da CLARA passou de 43 tools
por-capacidade para **exatamente seis tools semânticas estáveis**:

| Tool | Classe | Papel |
|---|---|---|
| `get_context` | DISCOVERY | ator + capacidades efetivas, catálogo versionado de `(entity, action)`, schema sob demanda (`topic=schema`), persona/`agent_directives` |
| `read` | READ | as 32 consultas do Portal por `entity`+`action`+`filters` — cada uma invoca a mesma função `tool_*` que chama a rota BFF canônica (`_call_route`) |
| `analyze` | ANALYSIS | `closing_blockers` (FACT vs RECOMMENDATION) |
| `knowledge` | READ | `search`/`get`/`sources` sobre o corpus PROC-0072, com citações |
| `execute` | ACT | toda operação governada não-destrutiva: `phase=prepare` → `confirmation_url` no Portal → `phase=commit` com `proposal_handle`; `batch` cobre o fluxo multi-ação (`prepare`/`confirm`/`execute`) |
| `delete` | ACT | apenas capabilities marcadas `destructive`, mesmo fluxo governado |

O dispatcher (`interface/mcp/semantic_bridge.py`) resolve
`(entity, action)` por registry tipado com allowlist por action —
rejeita `entity`/`action`/filtros desconhecidos com `not_implemented` /
`validation_error`. Nenhuma URL, método HTTP, SQL ou nome de handler é
aceito do modelo. Novas capacidades crescem por entradas no registry,
nunca por novos nomes de tool.

As 43 ferramentas legadas **não foram removidas**: os handlers
`tool_*` seguem em `tool_bridge.py` como alvos do dispatcher e os nomes
permanecem em `LEGACY_TOOL_NAMES` (janela de compatibilidade
documentada); simplesmente não são registrados no `tools/list` — o
único consumer externo (conector ChatGPT) descobre a superfície
dinamicamente a cada sessão, portanto o cutover dele é a
reconexão/atualização do plugin, sem dual surface mascarada.

## 2. Política de risco (G2 — conservadora)

Toda capability do catálogo permanece `GOVERNED_HIGH` ou `DESTRUCTIVE`:
nenhuma foi rebaixada para `LOW_DIRECT`/`MEDIUM_DIRECT`, porque a
política vigente exige PREPARE → consentimento verificável no Portal →
ACT para **toda** escrita MCP (doc 106 §3; mesma constatação da
execução 016). `phase=direct|immediate` é rejeitado com
`consent_required`. `delete` recusa capabilities não-destrutivas.
`confirmed=true` vindo do LLM nunca é consentimento — a prova é a posse
do `proposal_handle` selado + `consent_record` do Portal (ou atestação
de host vinculada ao `plan_hash`, no lote).

## 3. Propriedades preservadas

- AuthZ efetiva por chamada: cada read invoca a rota BFF canônica com a
  request reconstruída (`authorized_user`, bearer delegado, envelope e
  erros tipados idênticos); `manage`/`dre` revalidados no PREPARE e no
  ACT via `identity_provider` — fail-closed sem identidade.
- Snapshots de staleness, `expected_revision`, `idempotency_key`,
  postconditions por read-back e auditoria `mcp/clara` inalterados.
- Batch: `plan_hash`, `depends_on`, `resume`, `PARTIAL` honesto,
  `get_batch_status` via `read(batch.status)`.
- Persona/avatar: `get_context(topic=persona)` entrega
  `agent_directives` completo (`FICTION_IDENTITY_ONLY`,
  `avatar_distribution`).
- `MAX_PAGE_SIZE=200` imposto no adapter; filtros por allowlist.

## 4. Evidências

- **Testes:** `pytest tests/` → **725 passed** não-PG; suíte PG
  (`CF_TEST_PG_*` dedicada + opt-in) → **966 passed** total, 0 falhas.
  Novos: `test_clara_mcp_semantic.py` (34 casos: wire surface=6,
  schemas constructíveis, registry dispatch, schema-on-demand,
  prepare/commit/delete gating, `direct` rejeitado, batch fases,
  unauthenticated 401, fuzz/injection, `page_size` cap).
- **Gates CI:** `audit_architecture_phase3`, `audit_platform_guardrails`,
  `audit_openapi_contracts`, `audit_fastapi_authz`,
  `audit_backend_boundaries` — 0 findings no diff do commit.
- **Deploy:** `up-prod-sequential.sh --pull --build
  controllership-finance-api` via SSH `operador` → container
  `delpi-controllership-finance-api` healthy; runtime `tools: 6`,
  `caps: 48`; edge `/apps/controllership-finance-api/mcp` responde 401 +
  `WWW-Authenticate` RFC 9728 corretos.
- **Rollback:** `git reset --hard <sha-anterior>` +
  `up-prod-sequential.sh --build controllership-finance-api`; imagem
  anterior retida no host; corpus anterior permanece no histórico
  (supersede não destrói); sem migrations no diff.

## 5. FINAL EXECUTION REPORT (modelo do doc 119 §12)

```text
CLARA-MCP-SEMANTIC-001 — FINAL EXECUTION REPORT
BASE HEAD / FINAL HEAD / BRANCH / GIT STATUS:
  base 951926292e (origin/main após fetch) → final 3f36137dc3 (main);
  deploy puxou origin/main = 70e93be21f (inclui 3f36137 + fix EVA
  concorrente). Working tree com alterações alheias (api-delpi,
  delia-api, supplies-api, doc 210, untracked) — preservadas, fora do commit.
AUTHORITIES READ / .CURSOR / CONTRACTS:
  doc 119 integral; docs 94/106 (consentimento), 113, 118, 121;
  .cursor: development-standards-index, centralized-rules-first,
  clean-code-architecture-guardrails, english-code-identifiers,
  custom-gpt-actions-integration; referência estrutural EVA
  (engineering-api/interface/mcp/semantic_bridge.py, doc 55) — sem import.
CURRENT MCP TOOLS/LIST / CATALOG / GOVERNED OPERATIONS:
  antes: 43 tools / get_catalog / 48 caps; depois: 6 tools /
  get_context(topic=catalog) versionado / 48 caps inalteradas.
6 TOOL SCHEMAS AND CATALOG VERSION:
  schemas explícitos por assinatura de função (ver server.py);
  catalog_version = "clara-semantic-v1"; schema por action sob demanda
  via get_context(topic=schema) — nenhum dump em massa.
MIGRATION MATRIX COVERAGE (X/X) AND LOCATION:
  43/43 tools + 48/48 capabilities em
  docs/12-roadmap-e-evolucao/controllership-finance/
  CLARA-MCP-SEMANTIC-001-capability-matrix.md — todas MIGRATED.
CONSUMERS FOUND / CUTOVER STATUS:
  conector ChatGPT (client mcp-controllership-finance, OAuth) —
  discovery dinâmico; nenhum consumer por nome no repo; consumer
  externo não rastreado = INCONCLUSIVE, mitigado por discovery atômico.
RISK POLICY LOW_DIRECT / MEDIUM_DIRECT / HIGH / DESTRUCTIVE:
  READ/ANALYZE imediato; nenhum LOW/MEDIUM_DIRECT concedido (política
  vigente exige consentimento para toda escrita — DECISION_REQUIRED);
  42 caps GOVERNED_HIGH via execute; 6 caps DESTRUCTIVE via delete;
  BLOCKED tipado (validation/forbidden/not_implemented/consent_required).
BACKEND AUTHZ (CORE LIVE) / RESOURCE SCOPE / BUSINESS RULE:
  authorized_user + has_permission por chamada; gates access/manage/
  dre confrontados rota-a-rota; scope/ownership revalidados em ACT;
  sem bypass, sem service token.
CONFIRMATION BOUNDARIES / BATCH / IDEMPOTENCY / POSTCONDITIONS:
  PREPARE selado → confirmation_url Portal → commit por handle exato;
  ator/TTL/single-use/staleness verificados; batch plan_hash vinculado;
  idempotency_key/expected_revision selados no payload; read-back
  pós-condição; UNKNOWN reportado.
FILES/DIFF / TEST COMMANDS+COUNTS / AUDITS / RESIDUAL SEARCH:
  10 arquivos (+1908/−801): semantic_bridge.py (novo), server.py,
  constants.py, branding.py, corpus_manifest.py, 3 testes + suíte
  semântica nova, matriz G1. `pytest tests/` = 725 não-PG + 241 PG
  = 966 passed; 5 audit scripts = 0 findings; residual search: sem
  consumers internos de nomes legados.
SECURITY NEGATIVE TESTS / CLIENT & WIRE CONFORMANCE:
  entity/action malformados, injection-like, handler/path arbitrário,
  payload gigante → erros tipados; sem exceção não capturada; wire
  `delpi/toolClass` + securitySchemes + annotations preservados.
COMMIT SHA / PRODUCTION PREVIOUS SHA & DIGEST / DEPLOYED SHA & DIGEST:
  commit 3f36137dc3; prod anterior 951926292e (imagem pré-existente);
  deploy 70e93be21f, imagem infra-controllership-finance-api
  sha256:996281d9a76eda957b18ae62e025343512b82ebfc76eb2ca6158b2c5fb7e3559.
SSH OPERATOR / RUNBOOK / DEPLOY STEPS / HEALTH / ROLLBACK:
  operador@192.168.1.237, ~/projetos/delpi-central,
  infra/scripts/up-prod-sequential.sh --pull --build
  controllership-finance-api; container healthy em ~30s; rollback por
  git reset + rebuild (seção 4).
LIVE MCP TOOLS/LIST = 6? / CHATGPT PLUGIN TOOLS VISIBLE = 6?:
  sim (runtime: get_context/read/analyze/knowledge/execute/delete) /
  TEST_NOT_RUN — requer reconexão do conector no workspace ChatGPT
  com usuário real (ação do usuário; host pode cachear schemas).
REAL READ/ANALYSIS/KNOWLEDGE / MUTATION-SAFE VALIDATION:
  handlers verificados por testes de paridade (mock-route + PG e2e);
  smoke autenticado = TEST_NOT_RUN; nenhuma mutação produtiva de teste.
AVATAR_DISCOVERY AND OFFICIAL IMAGE FALLBACK:
  get_context(topic=persona) serve agent_directives completo com
  avatar_distribution — inalterado da execução anterior.
FAILURES/REWORK/EXECUTION_DRIFT/DECISION_REQUIRED:
  DECISION_REQUIRED — execução direta de operações classe B
  (LOW/MEDIUM_DIRECT) exige mudança da política de consentimento
  (owner: segurança, doc 106 §3). Drift: WSL caiu durante 1ª chamada
  do deploy — pull não completou; reexecução idempotente concluiu.
FINAL STATUS: ACCEPT_WITH_RESIDUAL
  (superfície 6 PROVEN em serviço; cutover do host ChatGPT pendente
  de ação do usuário — resta TEST_NOT_RUN autenticado)
NEXT STEP / USER ACTION FOR PLUGIN REFRESH:
  no ChatGPT, desconectar/reconectar o conector CLARA (ou editar e
  salvar) para re-descobrir tools/list; verificar que apenas as seis
  tools semânticas aparecem e rodar o roteiro de aceite do doc 107 §3
  com dados de teste.
```
