# F0 — Readiness de Implementação — EVA / Portal Engenharia DELPI

> **Documento:** `04-f0-implementation-readiness.md`
> **Fase:** F0 — reconciliação de requisitos e preparação; nenhum item marcado `IMPLEMENTED`
> **Regra:** nenhuma etapa é autorização automática — cada F* exige pedido explícito + revalidação (`plan-execution.mdc`, `IMPLEMENTATION-PLAN.md`)

---

## 1. Reconciliação RQ/AC

> Fonte dos RQ/AC: `01-foundation-engineering-api-eva-mcp-portal-inicio.md` (linhas 108–114). Estado factual por item: `F0_STATUS` = readiness de início; nada aqui é `IMPLEMENTED`.

### RQ-ENG-001 — Foundation `engineering-api`

| Campo | Valor |
|---|---|
| Objetivo | serviço inicializável, health/readiness, config, erros, observabilidade, testes; sem bypass de Domain APIs |
| Owner | `engineering-api` (novo bounded context de composição Portal) |
| Dependências | ADR-REQ-05 (naming/estrutura), ADR-REQ-10 (gateway/compose); `delpi_auth` pronto |
| Fontes | `commercial-api`, `requests-api`, `delia-api` (Flask bootstrap), `api-delpi` (FastAPI, para contraste) |
| Contrato | OpenAPI-first; envelope/erros canônicos |
| AuthN/Z | `delpi_auth.middleware` + Core `/me`; `engineering.access` (code `PLANNED`) |
| AC | AC-ENG-001 |
| Testes | startup smoke, health público sem JWT, JWT fail-closed, Core `me` mock (positive/negative), observabilidade correlation id, boundaries audit |
| Outcome | container sobe, `/health` responde, nenhuma rota de negócio ainda |
| Gaps | decisão de framework Flask confirmada por precedência (commercial/requests/delia/transformometro/tv-dashboard são Flask; api-delpi é FastAPI outlier) — **precisa confirmação ADR-REQ-05**; DB/migrations fora do bootstrap |
| Próximo step | scaffold mínimo `engineering-api` |

### RQ-ENG-002 — Contrato composição Início (`GET /v1/home`)

| Campo | Valor |
|---|---|
| Objetivo | resposta read-only com provenance + degradação parcial; AuthZ +/−; downstream fake |
| Owner | `engineering-api` |
| Dependências | RQ-ENG-001; ADR-REQ-04 (contratos downstream exatos) |
| Fontes | api-delpi `/engineering/*` summary candidato; SI indicators confirmados; requests/transformometro `TO_INVENTORY` |
| Contrato | `GET /v1/home` → blocos `{status, provenance{source,version_hint,observed_at}, data}` |
| AuthN/Z | `engineering.access` positive; negative 401/403 |
| AC | AC-ENG-002 |
| Testes | happy path; schema/normalização; 401/403; timeout; 5xx; malformed; partial composition; nenhum acesso direto MFE→provider (teste estrutural) |
| Outcome | Home consome contrato real; partial/fail honesto |
| Gaps | catálogo P0 de blocos: somente blocos com fonte autorizada entram (não inventar contadores/tarefas — P-06, P-15) |
| Próximo step | definir contrato `GET /v1/home` + contract tests com fakes |

### RQ-EVA-001 — Fronteira EVA/MCP

| Campo | Valor |
|---|---|
| Objetivo | Domain/Application independentes de MCP/LLM/provider; adapter com catálogo mínimo e contrato explícito |
| Owner | EVA specialist (novo) + `mcp-engineering` (adapter) |
| Dependências | **Abstraction Gate** (`openai-plugin-mcp-integration.mdc`): consumer real, owner, capability, contrato — `NOT_READY` |
| Fontes | `shared/delpi_mcp` (transporte neutro), `api-delpi/app/interface/mcp/` (DAVI), TÉO/VISTA, `delia-api` (forma Domain/Application/ports) |
| Contrato | MCP streamable-http `/mcp`; tool catalog mínimo; OAuth/resource metadata |
| AuthN/Z | Bearer + resource audience + scopes de transporte (`delpi_mcp.auth`); business AuthZ app-owned; service tokens internos rejeitados em user-data paths |
| AC | AC-EVA-001 |
| Testes | `delpi_mcp` conformance + `no_domain_imports`-like test garantindo adapter sem domain import; authz positive/negative; transport audience/scope tests |
| Outcome | fronteira declarada e testável |
| Gaps | consumer real do MCP não identificado em F0 — `ARCHITECTURE_DECISION_REQUIRED` |
| Próximo step | documentar consumer/capability/contrato do gate; só depois scaffold adapter |

### RQ-EVA-002 — Primeira análise assistida

| Campo | Valor |
|---|---|
| Objetivo | grounded output com source/revision/limitations; fail-closed; testes/evals; sem claim não suportado |
| Owner | EVA specialist |
| Dependências | RQ-EVA-001; provider LLM contratado ou `deterministic_test_adapter`-like (TEST_ONLY); dados autorizados (LMP candidata — não decisão) |
| Fontes | `delia-api` `ModelInvocationPort`/`InvokeModel`/`governed_retries`/`context_budget` (forma); `ai-intelligence-evaluation.mdc` (evals); `ai-external-tools-security.mdc` |
| Contrato | resposta com `{answer, sources[{source, id, revision}], limitations[]}`; recusa fail-closed quando sem grounding |
| AuthN/Z | user parity — token do usuário; nunca service account substituindo RBAC |
| AC | AC-EVA-002 |
| Testes/evals | unit (grounding presente), negative (sem fonte → recusa), eval baseline/candidate com corpus fixo, lineage/eval identity (padrão `delia-api`) |
| Outcome | primeira capability de leitura/análise com evidência rastreável |
| Gaps | provider real não existe nem em `delia-api` — primeiro release pode ser TEST_ONLY/determinístico |
| Próximo step | definir capability candidata (LMP read/analysis) + contrato de saída grounded |

### RQ-PORTAL-001 — MFE federado

| Campo | Valor |
|---|---|
| Objetivo | manifest + registro Core/Portal + basePath/deep links + kit-first + sem api-delpi direto |
| Owner | `plugins/engineering` |
| Dependências | ADR-REQ-02 (permissions), ADR-REQ-10 (gateway); Core seed |
| Fontes | `commercial.manifest.json` (template PROVEN), `consumo-de-plugins.md`, `novo-plugin-mfe-checklist.md` |
| Contrato | manifest schemaVersion 1.0.0; `basePath: /apps/engineering`; `entry: /apps/engineering/assets/remoteEntry.js` |
| AuthN/Z | route permission via `ProtectedRoute` + Core `/me/apps` |
| AC | AC-PORTAL-001 |
| Testes | manifest schema test; deep link F5/back-forward; audit estrutural `plugins/engineering` não contém `api-delpi` base URL |
| Outcome | `/apps/engineering` monta via remoteEntry com rotas registradas |
| Gaps | Core app/route seed `TO_INVENTORY`; codes `engineering.*` finais pendentes |
| Próximo step | scaffold MFE + manifest draft → Core registration |

### RQ-PORTAL-002 — Página Início

| Campo | Valor |
|---|---|
| Objetivo | kit components, disponibilidade real, loading/empty/error/forbidden/partial, responsivo/acessível |
| Owner | `plugins/engineering` |
| Dependências | RQ-PORTAL-001, RQ-ENG-002 |
| Fontes | `plugin-ui` components confirmados (TopBar, PageHero, NavigationCard, AlertQueue, WorklistItem, ScreenLoading, EmptyState/EmptyGuidance, ScopeChipBar, MetricStrip, RecentAccessStrip, EventsSection, HelpTooltip); `commercial` HomePage como referência de composição |
| Contrato | consome `GET /v1/home`; render-only dos status por bloco |
| AuthN/Z | render por bloco conforme `forbidden`/`unavailable` — nunca esconder erro |
| AC | AC-PORTAL-002 |
| Testes | loading/empty/error/forbidden/partial; responsividade; acessibilidade keyboard; `audit_mfe_plugin_ui_css` compliance; sem `.delpi-ui-*` recriado |
| Outcome | Início real com estados honestos |
| Gaps | blocos sem fonte autorizada exibem `TO_INVENTORY`-style estado (não inventar) |
| Próximo step | mapear blocos Início → componentes kit → fonte contratual |

### RQ-INT-001 — Fluxo integrado

| Campo | Valor |
|---|---|
| Objetivo | contrato/auth/observability testados ponta a ponta; testes vinculados a SHA; outcome evidence |
| Owner | transversal |
| Dependências | RQ-ENG-001/002 + RQ-PORTAL-001/002 mínimos |
| Contrato | `MFE → engineering-api → downstream` com envelope/erros canônicos |
| AuthN/Z | positive/sibling/negative em todas as camadas |
| AC | AC-INT-001 |
| Testes | e2e contract tests; correlation id propagado; SHA pin em evidência |
| Outcome | fluxo provado, não documentado-apenas |
| Gaps | — |
| Próximo step | definir harness e2e + evidence format |

---

## 2. Dependências e ordem recomendada

```text
F0 (este) ── concluído documentalmente
   │
   ▼
F1 — BOOTSTRAP engineering-api (RQ-ENG-001)
   │   desbloqueia: ADR-REQ-05 (naming), ADR-REQ-10 (gateway/compose), Core registration draft
   │
   ├──► F2a — Contrato Início (RQ-ENG-002)  [precisa ADR-REQ-04]
   │      └──► F3a — MFE + Início (RQ-PORTAL-001/002)
   │
   └──► F2b — EVA boundary + gate (RQ-EVA-001)  [precisa ADR-REQ-03]
          └──► F3b — Primeira capability assistida (RQ-EVA-002)

RQ-INT-001 transversal — avaliado quando F2a+F3a existirem
```

Ordem alinhada a `IMPLEMENTATION-PLAN.md` (E0→E1→E2→E3, com E10 por contrato) e à decisão do usuário de Início-first.

---

## 3. Arquivos/serviços a criar ou modificar (por fase — PLANNED)

### F1 — `engineering-api` scaffold

- **Criar** `engineering-api/` (estrutura a decidir: `app/` vs `engineering_app/` — ADR-REQ-05)
- Referências a espelhar: `delia-api/app/main.py` (lifecycle), `delia-api/app/interfaces/http/{health_routes,auth_middleware,error_handlers,request_logging}.py`, `commercial-api/commercial_app/` (escala madura)
- Dependência: `shared/delpi_auth` (editable `-e ../shared`)
- `Dockerfile.dev`, `Dockerfile.prod`, `requirements.txt`, `pytest.ini`, `env.example`, `README.md`
- **Modificar** `gateway/nginx.dev.conf` + conf prod: location `/apps/engineering-api/` (verificar padrão `/apps/<svc>-api/`)
- **Modificar** docker-compose (dev/prod) — container `delpi-engineering-api`
- **Verificar** cobertura de `architecture-enforcement.yml` (paths já `**/*` — provavelmente sem mudança)

### F2a — `/v1/home` contract

- `engineering-api`: route `/v1/home`, composition service, anti-corruption DTOs, adapters/gateways para downstreams autorizados
- Contract tests com downstream fake (AC-ENG-002)

### F3a — `plugins/engineering` scaffold + Início

- **Criar** `plugins/engineering/`: `delpi.manifest.json` (base `/apps/engineering`), `package.json`, `vite` federation config, `src/features/home/HomePage.tsx`, `src/api/engineeringApi.ts` (base `/apps/engineering-api` — **nunca** `/apps/api-delpi`)
- `plugins/vite/federationShareScope.ts` `preparePluginUiRemote()` no bootstrap
- **Modificar** Core seed/registration (app + rotas + permissions) — `TO_INVENTORY` mecanismo exato
- **Modificar** `gateway/nginx.*.conf`: `/apps/engineering/` → container `delpi-engineering`
- imports `@delpi/plugin-ui` apenas; CSS estrutural no kit

### F2b/F3b — EVA

- **Criar** specialist standalone (forma `delia-api`): `app/{domain,application,infrastructure,interfaces,composition}` — naming a alinhar
- `ModelInvocationPort`-like + deterministic adapter (TEST_ONLY) até provider real
- **Criar** `mcp-engineering/` **somente após** Abstraction Gate documentado
- Reusar `shared/delpi_mcp` (transporte/conformance), `delpi_auth`

---

## 4. Testes e evals por gate

| Gate | Testes mínimos |
|---|---|
| F1 | startup smoke; `/health` público; JWT 401; Core `/me` mock ±; correlation id; `audit_backend_boundaries` limpo |
| F2a | contract tests `GET /v1/home`: happy, schema, 401/403, timeout, 5xx, malformed, partial; provenance por bloco; fan-out budget |
| F3a | manifest schema; deep link F5/back-forward; estados loading/empty/error/forbidden/partial; audit MFE→api-delpi negativo; `audit_mfe_plugin_ui_css`; acessibilidade |
| F2b | `delpi_mcp` conformance; `no_domain_imports` equivalente; transport auth ± (Bearer, audience, scopes, service-token rejection) |
| F3b | grounding unit tests; recusa sem fonte; eval baseline/candidate corpus fixo + lineage (`delia-api` `scripts/*eval*` como referência de formato) |
| RQ-INT-001 | e2e MFE→BFF→downstream fake; correlation id; SHA pin |

---

## 5. Gates de segurança

- JWT Keycloak fail-closed; Core `/me` effective RBAC; `force_refresh` em writes sensíveis
- `engineering.*` permission codes revalidados contra catálogo Core antes do seed (não usar draft como autoridade)
- Nenhum service token em MCP user-data paths; business AuthZ app-owned
- Nenhum path arbitrário de FILESERVER aceito como autoridade; `library_id` + raiz allowlisted server-side (P-12)
- Nenhum payload TOTVS cru repassado; anti-corruption DTOs
- Sem secrets em código/log; `credential_guard`
- Erros sem stack/SQL/hostname/path físico
- MFE sem `api-delpi` base URL (teste estrutural negativo)

---

## 6. Critérios de início F1/F2/F3

### F1 pode iniciar quando:

- [ ] ADR-REQ-05 resolvido (naming `app/` vs `engineering_app/`; Flask confirmado)
- [ ] ADR-REQ-10 resolvido (gateway path, container name, compose)
- [ ] permission `engineering.access` code confirmado no catálogo Core (ou stub `TO_INVENTORY` documentado)
- [ ] pedido explícito do PO para F1 (ver `IMPLEMENTATION-PLAN.md`: "nenhuma etapa futura é autorização automática")

### F2a pode iniciar quando:

- [ ] F1 `PASS` (health + auth + observabilidade provados)
- [ ] ADR-REQ-04: contratos downstream exatos inventariados (OpenAPI vigente)
- [ ] catálogo de blocos Início com fonte autorizada aprovado (nada inventado)

### F3a pode iniciar quando:

- [ ] F2a `PASS` (contrato `/v1/home` + contract tests)
- [ ] ADR-REQ-02 resolvido (permissions + manifest final)
- [ ] Core registration mechanism identificado

### F2b pode iniciar quando:

- [ ] **Abstraction Gate satisfeito**: consumer real + owner + capability + contrato + benefício vs HTTP documentado
- [ ] forma EVA standalone decidida (ADR-REQ-09)

### F3b pode iniciar quando:

- [ ] F2b `PASS`; capability candidata contratada; corpus de eval baseline fixo

---

## 7. Itens bloqueados (NOT_READY — não escolher silenciosamente)

| Item | Bloqueia | Decisor |
|---|---|---|
| Consumer/contrato `mcp-engineering` | todo código MCP | Arquitetura |
| Persistência `engineering-api` (DB, runner) | Sala/settings | Arquitetura |
| Sala: P-01..P-05 (salas por contexto, membership, retenção, storage anexos, realtime Flask) | Sala produtiva | PO + Arquitetura |
| Minhas tarefas: P-06/P-07 (fontes P0, allowed_actions) | worklist/actions reais | PO + owners |
| Unit scope P-08 | RBAC operacional | PO + Arquitetura |
| Custos P-10 (`engineering.costs.view`?) | dados sensíveis | PO + RBAC |
| FILESERVER libs P-12/P-13 | documentos genéricos/preview | PO + Arquitetura |
| Overview operacionais P-15/P-16 | cards extras | PO |
| NC rota global P-17 | paridade/cutover | Arquitetura |
| Cutover P-20 | redirect legados | PO |
| EVA forma standalone (ADR-REQ-09) | scaffold EVA | Arquitetura |
| Naming serviço (ADR-REQ-05) | scaffold F1 | Arquitetura |

---

## 8. Próximo bounded step

**Único próximo passo tecnicamente desbloqueado sem decisão arquitetural prévia adicional:** resolver `ADR-REQ-05` + `ADR-REQ-10` (naming + gateway/compose) — decisão pequena, documental — e então executar **F1** (`engineering-api` scaffold mínimo: health + JWT + Core `/me` + observabilidade + boundaries test), **somente** após pedido explícito.

Nada em F0 autoriza F1/F2/F3 automaticamente. Este documento deve ser revalidado contra `origin/main` vigente antes de cada execução (`plan-execution.mdc`).

---

## 9. Residual search — inconsistências registradas

| Achado | Tipo | Ação |
|---|---|---|
| `105118dd` baseline ≠ HEAD real | divergência de baseline | registrada; inspeção em `23613bd1f1`, entrega em `b886664da` |
| Legados `dashboard-*` → `/apps/api-delpi` direto | anti-padrão vigente | registrado; target proíbe — não "consertar" legado em F0 |
| `delia-api` `interfaces/` vs. maioria `interface/` | inconsistência naming | registrada (ADR-REQ-05) |
| `minha-delpi-copilot/` README-only | doc que parece runtime | classificado `HISTORICAL` pelo próprio README |
| Drafts de permissions/rotas Engineering | `PLANNED`, não `PROVEN` | manter separação de status em todos os docs |
| Nenhum provider LLM real no repo | gap de dependência EVA | primeiro release pode ser TEST_ONLY — documentar |
| `docs/12-roadmap-e-evolucao/engineering/` já tem arquitetura/alvo | risco de duplicação | F0 referencia docs existentes, não copia conteúdo |
