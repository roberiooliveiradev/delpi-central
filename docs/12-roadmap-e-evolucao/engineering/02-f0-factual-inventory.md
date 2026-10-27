# F0 — Inventário Factual — EVA / Portal Engenharia DELPI

> **Documento:** `02-f0-factual-inventory.md`
> **Fase:** F0 — Foundation / Factual Inventory (somente documentação; nenhum serviço, MCP ou frontend foi implementado)
> **Classificação:** `PROVEN | TO_INVENTORY | PLANNED | TARGET` por item
> **Verificação:** `PASS | FAIL | PENDING | INCONCLUSIVE | TEST_NOT_RUN | STALE_EVIDENCE` quando aplicável

---

## 0. Baseline e reancoragem

| Campo | Valor |
|---|---|
| Repositório | `roberiooliveiradev/delpi-central` |
| Baseline solicitada | `105118dd00de593257bc06189ed7869bf535fa68` |
| Divergência | `105118dd` é **ancestral** de `origin/main`; não é o HEAD atual. Divergência registrada, não reconciliada silenciosamente. |
| `BASE_HEAD` de inspeção | `23613bd1f1e43ca9804fa389c7b540b6abc183b5` (= `origin/main` no início da inspeção) |
| HEAD de entrega | `b886664da704ce1c4c63b2e30f4e40636c59b26f` (= `origin/main` no commit; `23613bd1` é seu ancestral direto; delta = apenas `docs/12-roadmap-e-evolucao/controllership-finance/*`, sem impacto no escopo Engineering) |
| Ambiente de inspeção | worktree isolado `.worktrees/eva-f0` (detached) para não tocar o working tree concorrente |
| Estado original do repo | branch `feat/metalography-visual-fidelity` @ `c02bbd8402`, à frente do remoto, com modificações e untracked extensos — **não tocados** |

**Todos os fatos abaixo foram verificados no SHA `23613bd1f1` salvo indicação explícita.**

---

## 1. Veredito de existência (o que já existe vs. o que é plano)

| Componente alvo | Existe no repo? | Evidência | Status |
|---|---|---|---|
| `engineering-api/` | **Não** | `ls engineering-api` → No such file or directory | `PLANNED` |
| `mcp-engineering/` | **Não** | `ls mcp-engineering` → No such file or directory | `PLANNED` |
| `plugins/engineering/` | **Não** | `ls plugins/engineering` → No such file or directory | `PLANNED` |
| Rotas Engineering na `api-delpi` | Sim | `api-delpi/app/interface/http/routes/engineering/` | `PROVEN` |
| MFEs Engineering legados | Sim | `plugins/dashboard-engineering/`, `plugins/dashboard-lmps/` | `PROVEN` (LEGADO) |
| Infra MCP compartilhada | Sim | `shared/delpi_mcp/` | `PROVEN` |
| MCP em produção (api-delpi) | Sim | `api-delpi/app/interface/mcp/` + `app.mount("/mcp", ...)` | `PROVEN` |
| Especialista standalone (referência arquitetural) | Sim | `delia-api/` (bootstrap C1) | `PROVEN` |
| Kit visual federado | Sim | `plugins/plugin-ui/` (`@delpi/plugin-ui`, remote `delpi-plugin-ui`) | `PROVEN` |

> **Regra factual:** `IMPLEMENTATION-PLAN.md` §3 confirma `plugins/engineering` e `engineering-api` como "não existe". O plano Foundation 001 é intenção de implementação, não evidência de runtime.

---

## 2. Inventário — `engineering-api` (futuro BFF)

### 2.1. Rotas Engineering existentes na `api-delpi` (PROVEN)

Arquivos (todos em `api-delpi/app/interface/http/routes/engineering/`):

| Arquivo | Conteúdo | AuthZ observada |
|---|---|---|
| `engineering_router.py` | LMP list/detail/history/flow, TRANSFORMA+ process/summary, Transformômetro series, mini-applicators | `require_any_permission` de `delpi_auth.authorization`; constants `ENGINEERING_LMP_ACCESS`, `ENGINEERING_TRANSFORMOMETRO_ACCESS`, `MINI_APPLICATORS_ACCESS` |
| `lmp_nonconformity_router.py` | não conformidades de LMP | leitura: `ENGINEERING_LMP_ACCESS`; escrita: `ENGINEERING_LMP_NC_WRITE` |
| `lmp_route_helpers.py` | helpers de rota LMP | — |
| `metallographic_reports_router.py` | laudos metalográficos | `METALOGRAPHY_CREATE/VIEW/EDIT/DELETE` |

Convenções comprovadas: respostas via `api_delpi_success` (`api-delpi/app/interface/http/route_response_helpers.py:13`) e `error_response` (`api-delpi/app/core/responses.py`, importado em `engineering_router.py:51`), `operationId` estruturado, OpenAPI metadata por rota.

### 2.2. Composição Engineering existente (PROVEN)

`api-delpi/app/composition/engineering_composer.py` — factories de use cases:

- LMP: list/detail/history/flow + não conformidades;
- TRANSFORMA+: `ListProcessUseCase`, `GetProcessSummaryUseCase` via `TransformometroTransformaMaisGateway`;
- Transformômetro: `GetDashboardEvolucaoUseCase` via `TransformometroDashboardGateway`;
- mini-applicators.

**Limitação arquitetural factual:** o composer acopla use cases de `api-delpi` a gateways de `transformometro-api`. Isso prova o padrão gateway HTTP cross-context, mas **não** é um BFF de Portal — é composição interna da domain API. `engineering-api` deve **consumir** esses contratos via HTTP, não importá-los.

### 2.3. Contratos de Produtos/Desenhos (PROVEN)

`api-delpi/app/interface/http/routes/product_routes.py` — ~40 endpoints, incluindo:

- `/search`, `/{code}` (detalhe), `/{code}/summary`;
- `/{code}/structure`, `/structure/excel`, `/structure/exclusivity`, `/{code}/parents` (onde-usado);
- `/{code}/stock`, `/safety-stock`, `/inventory-blocks`, `/physical-locations`;
- `/{code}/suppliers`, `/purchases`, `/last-purchase`, `/purchase-price-history`, `/purchase-budget-history`, `/pricing`, `/raw-material-price-intelligence`, `/{code}/cost-impact-simulation`;
- `/{code}/production-status`, `/shipping-status`, `/factory-status`, `/customers`, `/sales`, `/raw-material-set-shortages`.

`product_drawing_routes.py`: `/drawings`, `/{code}/drawing`, `/{code}/drawing/pdf` (metadados + PDF — backend-only, FILESERVER por trás).

### 2.4. AuthN/AuthZ provado (PROVEN)

`api-delpi/app/middleware/auth_middleware.py`:

- base: `delpi_auth.middleware.fastapi_auth.jwt_middleware`;
- MCP paths: `delpi_mcp.auth.mcp_transport_auth`;
- service tokens: `delpi_auth.service_token.request_has_valid_internal_service_token`;
- whitelist pública explícita (`/public/quality-labels/`, `/gpt-actions/v1/openapi.json`, etc.);
- root_path stripping (`/apps/api-delpi`).

`shared/delpi_auth/` (PROVEN, reutilizável **como dependência, não como cópia**):

| Arquivo | Papel |
|---|---|
| `jwt_validator.py` | validação JWT Keycloak |
| `middleware/fastapi_auth.py` + `middleware/` Flask | JWT + `GET /me` Core para effective RBAC; cache com TTL normal/stale; `force_refresh=True` desabilita stale fallback em writes sensíveis; falha de lookup Core → erro de autorização (fail-closed) |
| `authorization.py` | `has_permission`, `has_any_permission`, `has_all_permissions`, `require_any_permission`; superadmin como primitiva compartilhada |
| `context_resolver.py` | resolve `g.current_user`/`g.user` (Flask) ou contexto FastAPI |
| `service_token*.py`, `service_identity.py`, `service_contract.py` | identidade de serviço para integração server-to-server |
| `policy_engine.py`, `policy_registry.py` | políticas declarativas |

`core-api/app/interfaces/http/me_controller.py` — endpoint `/me` que fornece effective access (PROVEN).

### 2.5. Bootstrap de APIs maduras (PROVEN — referências)

| Serviço | Framework | Estrutura | Observações |
|---|---|---|---|
| `commercial-api` | Flask | `commercial_app/{application,domain,infrastructure,interface,middleware,composition,startup}` + `migrations/` + `tests/` | Referência madura: interaction rooms, inbox, mentions, pins, shared_items (tests `test_interaction_*` extensos) |
| `requests-api` | Flask | `requests_app/` (mesma família) | dona `raw-material-creation` request type (ver §5) |
| `strategic-indicators-api` | Flask | `si_app/` | possui `si_app/application/services/engineering/engineering_metrics_helpers.py` |
| `transformometro-api` | Flask | `tm_app/` | owner de TRANSFORMA+/Transformômetro |
| `delia-api` | Flask | `app/{domain,application,infrastructure,interfaces,composition}` | **referência arquitetural mais próxima de EVA** (ver §3) |
| `api-delpi` | FastAPI | `app/{interface,application,domain,infrastructure,composition,middleware}` | domain API corporativa/TOTVS |

**Nota de inconsistência factual:** `delia-api` usa `app/interfaces/` (plural); `commercial-api` usa `commercial_app/interface/` (singular). Convenção de naming não é uniforme no repo — registrar, não corrigir.

### 2.6. Gaps do futuro `engineering-api` (TO_INVENTORY/PLANNED)

| Item | Estado |
|---|---|
| health/readiness | padrão existe (commercial/requests/delia têm `/health`); contrato exato a definir em F1 — `PLANNED` |
| observabilidade/correlation | `api-delpi/app/middleware/request_observability_middleware.py` PROVEN como referência; `observability-standards.mdc` canonical — padrão reutilizável, implementação `PLANNED` |
| persistência própria | Sala/settings exigem schema próprio (`DATA-MODEL.md` planeja); migration runner/DB alvo `NOT_READY` (decisão E1) — `TO_INVENTORY` |
| gateway/nginx | padrão `/apps/<svc>-api/` provado; registro exato `engineering-api` `PLANNED` |
| OpenAPI/operationIds | convenção `api-delpi-openapi-route-standards.mdc` canonical; aplicação `PLANNED` |

---

## 3. Inventário — EVA / `mcp-engineering`

### 3.1. Infra MCP compartilhada (PROVEN — `shared/delpi_mcp/`)

Neutra por contrato (`__init__.py` proíbe server factories, domain errors, tool registries e semântica de negócio):

| Módulo | Fato verificado |
|---|---|
| `auth.py` | `McpTransportAuthPolicy`; rejeita service tokens internos em user-data paths; exige `Authorization: Bearer`; valida via `delpi_auth.validate_token`; checa resource audience exata + scopes de transporte; **não** faz business AuthZ (delegada à app) |
| `transport.py` | rewrite interno `/mcp` → `/mcp/` sem redirect 307/308; `combine_lifespan` determinístico; DNS rebinding protection sempre ativa; host/origin allowlists app-owned |
| outros | `conformance` runner, `resource_contract`, `tool_validation`, `identity` bridge, `errors_metadata`, `protocol` minimum checks |
| testes | `test_auth/conformance/errors_metadata/identity/no_domain_imports/protocol/resource_contract/tool_validation/transport` |

**Status:** `REUSE_AS_IS_NEUTRAL` — fundação de transporte conforme `openai-plugin-mcp-integration.mdc`.

### 3.2. MCP existentes (PROVEN — referências)

| Serviço | Local | Padrão |
|---|---|---|
| api-delpi (DAVI) | `api-delpi/app/interface/mcp/` (`server.py`, `routes`, `oauth_contract.py`, `resource_metadata.py`, `schemas`, `asgi`, `transport-spike`) | `app.mount("/mcp", mcp_http_app)` em `app/main.py:382`; `mcp_metadata_router` (:380); `mcp_mount_path_middleware` (:261). Config: `api-delpi/integrations/openai-plugin/mcp.json` → `https://minhadelpi.com.br/apps/api-delpi/mcp` (streamable-http) |
| transformometro-api (TÉO) | `transformometro-api/` (impl/tests/docs) | mesma família `shared/delpi_mcp` |
| tv-dashboard-api (VISTA) | `tv-dashboard-api/` (impl/tests/docs) | mesma família |

`openai-plugin-mcp-integration.mdc` exige **Abstraction Gate** antes de novo MCP: consumer real, owner real, capability real, contrato real, reuso do path application/domain, redução de acoplamento, benefício sobre HTTP/bridge existente. Proibido: SQL/proxy genérico, path/method arbitrário, CRUD mecânico integral, provider metadata como autorização, RBAC duplicado, service account como substituto de user parity.

### 3.3. `delia-api` — referência arquitetural para EVA (PROVEN)

`delia-api/app/` — Flask standalone (não FastAPI), bootstrap C1:

- `main.py`: `create_app()` → `app.run()`, lifecycle logging `delia_api_started/stopped`, signal handlers (PROVEN, `main.py:1-66`);
- `interfaces/http/`: `health_routes`, `auth_middleware` (JWT fail-closed `delpi_auth.jwt_validator` + Core `GET /me`), `interaction_routes`, `dictation_routes`, `error_handlers`, `request_logging`;
- `domain/`: `capability_catalog`, `evidence`, `expertise`, `interaction`, `knowledge`, `decision_path`, `planning`, `specialist_interop`, `media`, `structured_understanding`, `model_invocation` — cada um com `model.py` + `rules.py` (Domain puro, sem provider);
- `application/`: `ports/model_invocation_port.py`, `model_invocation/` (`invoke_model`, `contracts`, `governed_retries`, `context_budget`, `errors`), `interaction/` (`handle_interactive_turn`, `turn_budget`, `pending_proposals`, `presentation`, `activity`, `capability_attempt`, `argument_validation`, `workspace_context`, `turn_observability`), `dictation/`, `specialist_interop/`;
- `infrastructure/model_invocation/`: `deterministic_test_adapter` (TEST_ONLY), `openai_compatible_adapter`, `openai_compatible_transcription_adapter`;
- `composition/root_composer.py`.

README declara: provider-neutral `ModelInvocationPort` + `InvokeModel` + lineage/eval identity; **real provider adapter = NONE**; sem RBAC local, sem business routes ainda. Isso é **evidência documental de escopo**, não de runtime — `CONFIRMADO_EM_DOCUMENTACAO_CANONICA` + código lido.

**Classificação para EVA:** `REFERENCE_ONLY` (padrão domain/application/ports + provider-neutral invocation + governed retries + context/turn budget + evals) — EVA deve seguir a mesma forma, sem runtime dependency em `delia-api`.

### 3.4. `minha-delpi-ai-api` — classificação de ativos (PROVEN para existência)

Estrutura (`app/`): `domain` (entities/exceptions/features/models/ports/prompt_policies/security/services/skills), `application` (dto/security/services incl. `chat_turn`, `external_actions`, use_cases), `infrastructure` (cache/cli/config/content/db/embeddings/external_actions/gateways/llm/openapi/persistence/presentation/tools), `interfaces`, `composition`, `content/pt-BR`, `migrations`.

| Ativo | Classificação | Justificativa |
|---|---|---|
| `infrastructure/external_actions/openapi_action_importer.py` | `EXTRACT_AND_ADAPT` | import OpenAPI → actions reutilizável conceitualmente; acoplamento a chat pipeline exige adaptação |
| `infrastructure/external_actions/http_external_action_gateway.py` | `REFERENCE_ONLY` | padrão de execução HTTP autorizada |
| `external_action_test_executor.py` | `TEST_FIXTURE_REUSE` | harness de actions |
| `infrastructure/llm/llm_gateway_registry.py` + `openai_compatible_*` | `REFERENCE_ONLY` | registry/gateways de provider; `delia-api` `ModelInvocationPort` é referência mais limpa para EVA |
| `infrastructure/tools/{web_search_tool,execute_external_action_tool}.py` | `CHAT_SPECIFIC_DROP` | tools acopladas ao pipeline do chat |
| `domain/skills`, `prompt_policies`, `content/pt-BR/assistant` | `KNOWLEDGE_ASSET_CANDIDATE` | vocabulário/policies a minerar, não importar |
| chat_turn pipeline, intent router, presentation compilers | `CHAT_SPECIFIC_DROP` | pipeline do Chat, não da EVA |
| OpenAPI → Action Catalog → retrieval/planner/validator (conceito) | `SHARED_PRIMITIVE_CANDIDATE` (conceitual) | não extrair sem 2+ consumidores reais (gate `centralized-rules-first`) |

**Proibição registrada:** nenhuma runtime dependency de `mcp-engineering`/`engineering-api` em `minha-delpi-ai-api` (Chat). EVA é specialist standalone como `delia-api`.

### 3.5. Outros

- `minha-delpi-copilot/` — **README-only**, `HISTORICAL/SUPERSEDED` como namespace técnico (`minha-delpi-copilot/README.md`). Não é evidência de runtime.
- `plugins/delia/` — MFE DÉLIA existe (`delpi.manifest.json`), `PROVEN` para existência.
- `docs/12-roadmap-e-evolucao/delia/` — `delia-execution-protocol.mdc` + docs canônicos próprios da DÉLIA.

### 3.6. Gaps EVA/MCP (TO_INVENTORY/PLANNED)

| Item | Estado |
|---|---|
| consumer real do `mcp-engineering` | `NOT_READY` — Abstraction Gate exige consumer/owner/capability/contrato reais antes de implementar |
| primeira capability (LMP read/analysis) | candidata, não decisão — `READY_BOUNDED` condicional |
| provider LLM real | nenhum adaptador real existe nem em `delia-api` — `NOT_READY` (EVA também ficaria `TEST_ONLY` até contrato de provider) |
| MCP catalog mínimo | `PLANNED` — seguir `tool_validation`/`conformance` de `shared/delpi_mcp` |
| evals | `delia-api/scripts/*eval*.py` + `ai-intelligence-evaluation.mdc` como referência — `PLANNED` |

---

## 4. Inventário — Portal / MFE (`plugins/engineering`)

### 4.1. Portal host (PROVEN)

- `portal/src/ui/AppHost.tsx`, `App.tsx`: rotas React dinâmicas por `route.path` com `<ProtectedRoute permission>` (`portal/src/routes/ProtectedRoute.tsx`); wildcard `basePath/*` → `AppHost`;
- `portal/src/state/AuthContext.tsx`: fonte `GET /core-api/me/apps` (`AppItem`: id/name/icon/basePath/type/entryUrl/renderMode/routes[]);
- federated: `import(entryUrl)` → `remoteEntry.js` → `.get()` → mount em `federatedHostRef`; MFE chama `preparePluginUiRemote()` (`plugins/vite/federationShareScope.ts`);
- loading overlay `AppHostLoadingScreen` (delay ~180ms / min ~450ms / fade);
- doc canônico: `docs/06-portal-frontend/consumo-de-plugins.md`.

### 4.2. Manifests maduros (PROVEN — template factual)

`plugins/commercial/commercial.manifest.json` (schemaVersion `1.0.0`):

- `id: "commercial"`, `type: "microfrontend"`, `basePath: "/apps/commercial"`, `entry: "/apps/commercial/assets/remoteEntry.js"`;
- `permissions[]`: `commercial.access`, `commercial.manage`, `commercial.billing.notify` (cada um com code/name/description/module);
- `routes[]`: `{path, label, permission, icon, order, showInMenu}` — base `/apps/commercial` (showInMenu true), `/overview`, `/my-tasks`, etc. (showInMenu false).

Legados Engineering:

- `plugins/dashboard-engineering/dashboard-engineering.manifest.json`: id `dashboard-engineering`, base `/apps/dashboard-engineering`, `dashboard-engineering.view`; rotas dashboard/LMP/TRANSFORMA+;
- `plugins/dashboard-lmps/dash-lmps-microfrontend.manifest.json`: id `dashboard-lmps`, base `/apps/dashboard-lmps`, `dashboard-lmps.view`, `dashboard-lmps.nc.write`.

### 4.3. Violação factual legada — MFE → api-delpi direto (PROVEN, anti-padrão para o target)

| Arquivo | Base URL hardcoded |
|---|---|
| `plugins/dashboard-engineering/src/api/engineeringApi.ts` | `/apps/api-delpi/engineering` |
| `plugins/dashboard-engineering/src/api/departmentIddApi.ts` | `/apps/api-delpi/dashboard` |
| `plugins/dashboard-lmps/src/api/lmpApi.ts` | `/apps/api-delpi/engineering` |
| `plugins/dashboard-lmps/src/api/lmpNonconformityApi.ts` | `/apps/api-delpi/engineering/lmps/nonconformities` |
| `plugins/dashboard-lmps/src/api/productApi.ts` | `/apps/api-delpi/products` |
| `plugins/dashboard-lmps/src/api/departmentIddApi.ts` | `/apps/api-delpi/dashboard` |

`mfe-own-api-no-direct-api-delpi.mdc` proíbe esse padrão para MFE com API própria. Path alvo: `plugins/engineering → engineering-api → api-delpi`. **Fato:** a regra existe e o legado viola-a — não carregar o padrão para o target.

### 4.4. `@delpi/plugin-ui` — componentes confirmados para a página Início (PROVEN)

`plugins/plugin-ui/src/`:

| Bloco da Início | Componente(s) provados | Arquivo |
|---|---|---|
| TopBar | `TopBar`, `createDashboardTopBarFavoritesStrip`, `TopBarUtilityCluster`, `TopBarUserIdentity`, `TopBarSearchTrigger`, `HubChipRow` | `components/layout/TopBar*.tsx`, `HubChipRow.tsx` |
| Hero | `PageHero` | `components/layout/PageHero.tsx` |
| Atalhos/ferramentas | `NavigationCard` | `components/layout/NavigationCard.tsx` |
| Command palette | `CommandPalette` | `components/layout/CommandPalette.tsx` |
| Métricas | `KpiCard`, `DelpiKpiCard`, `MetricStrip`, `ChartCard` | `components/layout/{KpiCard,MetricStrip,ChartCard}.tsx` |
| Atenção/alertas | `AlertQueue`, `InfoStatePanel`, `FloatingNoticeStack`, `LoadingActivityBadge` | `components/feedback/*.tsx` |
| Worklist | `WorklistItem`, `createDashboardWorklistItem` | `components/feedback/WorklistItem.tsx` |
| Escopo | `ScopeChipBar` | `components/feedback/ScopeChipBar.tsx` |
| Loading/Empty/Error | `ScreenLoading`, `EmptyState`, `EmptyGuidance`, `TaskEmptyState`, `PluginErrorBoundary`, `InlineLoadingProgress` | `components/feedback/*.tsx` |
| Recentes | `createDashboardRecentAccessStrip` | `components/layout/RecentAccessStrip.tsx` |
| Eventos | `EventsSection`, `createDashboardEventsSection` | `components/layout/EventsSection.tsx` |
| Ajuda | `HelpTooltip`, `SectionHintLabel`, `FieldLabel`, `UserManual`, `createDashboardUserManual` | `components/help/*`, `components/layout/UserManual` |
| Sala (futura) | `InteractionRoomPage`, `RoomInboxList`, `MessageThread`, `Conversation*` | `components/collaboration/*`, `components/conversation/*` |
| Tarefas (futura) | `TaskWorkspacePage` | `components/tasks/TaskWorkspacePage.tsx` |
| Arquivos | `FilePreviewModal` | `components/preview`/`document` |

Regra: structural CSS `.delpi-ui-*` fica no kit; consumer define tokens/layout escopado (`plugins-visual-design-system.mdc`, `plugins-reusable-components.mdc`). Audits CI: `audit_mfe_plugin_ui_css`, `audit_plugin_ui_duplication`, `audit_plugin_ui_native_form_controls`.

### 4.5. Referência de Home madura (PROVEN — `REFERENCE_ONLY`)

`plugins/commercial/src/features/home/HomePage.tsx` — composição com kit: catálogo de rotas content-driven, favorites, recent views, worklist preview, loading/empty/error. Não é dependência runtime do Engineering.

### 4.6. Gaps MFE (TO_INVENTORY/PLANNED)

| Item | Estado |
|---|---|
| manifest `plugins/engineering` | `MANIFEST-DRAFT.md` existe como draft — `PLANNED`; codes finais a revalidar contra catálogo Core |
| registro Core (app/rotas/permissions) | mecanismo PROVEN (`/core-api/me/apps` + `me_controller`); seed/registro exato `TO_INVENTORY` |
| basePath `/apps/engineering` | `PLANNED` (docs); gateway/nginx entry `TO_INVENTORY` |
| estados forbidden/partial | componentes PROVEN; contrato de provenance/degradation do BFF `PLANNED` (RQ-ENG-002) |

---

## 5. Inventário — Integrações downstream (mapa factual)

| Downstream | Owner | Contrato existente | Consumer atual | AuthZ | Status |
|---|---|---|---|---|---|
| Core API (`/me`, `/me/apps`) | Plataforma | `core-api/app/interfaces/http/me_controller.py` | Portal (`AuthContext`), `delpi_auth` middleware | JWT + effective RBAC | `PROVEN` |
| api-delpi `/engineering/*` | api-delpi (TOTVS) | §2.1–2.3 | dashboards legados (direto — anti-padrão) | `ENGINEERING_*`, `MINI_APPLICATORS_ACCESS`, `METALOGRAPHY_*` | `PROVEN` |
| api-delpi `/products/*`, `/drawings` | api-delpi | §2.3 | dashboard-lmps, outros | product permissions (por rota) | `PROVEN` |
| strategic-indicators-api | SI | `si_app/application/services/engineering/engineering_metrics_helpers.py`; indicators `engineering-projects-on-time`, `engineering-transforma-plus`; `test_engineering_consolidated_branch_view.py` | dashboards legados via api-delpi/dashboard | SI permissions | `PROVEN` |
| requests-api (Controle MP) | Minhas Solicitações | request type `raw-material-creation`; perms `my-requests.raw-material-creation.create`/`.process` (`plugins/my-requests/src/security/requestsAccess.ts:47-48`); `test_raw_material_type_plugability.py` | `plugins/my-requests` | requests-api RBAC | `PROVEN` |
| transformometro-api | Transformômetro | consumido hoje **por api-delpi** via `TransformometroTransformaMaisGateway`/`TransformometroDashboardGateway` | api-delpi engineering_composer | — | `PROVEN` (via api-delpi) |
| FILESERVER/storage | storage corporativo | desenhos via `product_drawing_routes.py` (backend-only) | api-delpi | — | `PROVEN` (desenhos); `NOT_READY` (bibliotecas genéricas — P-12) |
| commercial-api (interaction rooms) | Comercial | tests `test_interaction_*` extensos | `plugins/commercial` | commercial RBAC | `PROVEN` — **não** provider do Engineering (proibição documental); referência de protocolo/UX apenas |

**Não inventar:** contadores, tarefas, indicadores operacionais, mentions ou atividades sem fonte autorizada — `TO_INVENTORY` por owner (P-06, P-15, P-18).

---

## 6. CI/Enforcement provado (PROVEN)

`.github/workflows/architecture-enforcement.yml` + `scripts/ci/`:

- `audit_architecture_phase3.py`, `audit_platform_guardrails.py`, `audit_openapi_contracts.py`, `audit_gpt_actions_openapi.py`, `audit_fastapi_authz.py`, `audit_backend_boundaries.py` (+ `test_*` self-tests);
- MFE: `audit_mfe_plugin_ui_css.py`, `audit_plugin_ui_duplication.py`, `audit_plugin_ui_native_form_controls.py`;
- `shared/delpi_auth` test gate (`pytest shared/delpi_auth/tests/test_jwt_validator.py`);
- workflows separados: `sync-api-delpi-openapi*.yml`, `api-delpi-console.yml`, `bpmn-modeler.yml`, `cursor-rules-governance.yml`.

Implicação F1: `engineering-api`/`plugins/engineering` entram no escopo desses gates (paths `**/*.py`, `**/*.ts*`, etc.) — `PLANNED` verificação de cobertura por path.

---

## 7. Autoridades consultadas

Canônicas (8 responsabilidades + constituição): `AGENTS.md`; `.cursor/rules/`: `development-standards-index`, `evidence-driven-execution`, `centralized-rules-first`, `clean-code-architecture-guardrails`, `english-code-identifiers`, `platform-architecture-boundaries`, `platform-security-identity-authorization`, `platform-api-contracts-integration`, `platform-data-persistence`, `platform-frontend-mfe-experience`, `platform-quality-testing`, `platform-delivery-runtime-operations`, `platform-reliability-observability`, `mfe-own-api-no-direct-api-delpi`, `application-bounded-context-decoupling`, `openai-plugin-mcp-integration`, `openai-workspace-agent-integration`, `architecture-ci-enforcement`, `plan-construction`, `plan-execution`, `contract-evolution-backward-compatibility`, `http-integration-resilience`, `observability-standards`, `new-api-route-checklist`, `openapi-first-universal-tool-routing`, `operational-api-routing`, `ai-intelligence-evaluation`, `ai-external-tools-security`, `ai-context-and-tool-budget`, `custom-gpt-actions-integration`, `delia-execution-protocol`, `plugins-reusable-components`, `plugins-visual-design-system`, `feature-help-sync`, `migrations-immutable-checksum`, `local-first-deploy`, `infra-sequential-container-startup`, `test-and-commit`.

Engineering docs (`docs/12-roadmap-e-evolucao/engineering/`): `01-foundation-*.md` (RQ/AC), `PLAYBOOK-MODULO-ENGENHARIA.md`, `DESIGN-IA-ENGENHARIA.md`, `README.md`, `INVENTARIO-ATIVOS.md`, `SCOPE-OWNERSHIP.md`, `ARCHITECTURE.md`, `API-ROUTES.md`, `PERFIS-E-PERMISSOES.md`, `MANIFEST-DRAFT.md`, `INTEGRACOES.md`, `DATA-MODEL.md`, `ROADMAP.md`, `IMPLEMENTATION-PLAN.md`, `DECISOES-FUNCIONAIS-PENDENTES.md`, `WIREFRAMES.md`, `HELP-AND-ONBOARDING.md`, `KPI-FICHAS.md`, `HOMOLOGACAO-PARIDADE.md`, `CUTOVER-RUNBOOK.md`, `adr/ADR-001-engineering-bounded-context.md`, `ADR-002-fileserver-boundary.md`, `ADR-003-legacy-cutover.md`, `ADR-004-interaction-rooms.md` (adr/ contém também ADR-005..007 e README — não centrais a F0).

Outros: `docs/06-portal-frontend/consumo-de-plugins.md`, `docs/05-plugin-system/*`, `plugins/plugin-ui/docs/{component-catalog,architecture}.md`, `api-delpi/docs/integrations/openai-plugin-mcp.md`, `minha-delpi-copilot/README.md`, `delia-api/README.md`.

---

## 8. Limitações deste inventário

1. Evidência = leitura de código/contrato/testes no SHA `23613bd1f1`; **nenhum runtime foi exercitado** (nenhum serviço subido, nenhum request HTTP). Verificações `TEST_NOT_RUN` por padrão.
2. `plugins/delia` e `minha-delpi-ai-api` foram inspecionados estruturalmente; detalhe de tools/evals não é material a F0.
3. Catálogo Core de permissions vigente não foi consultado em banco — apenas código; codes finais `engineering.*` dependem de revalidação (ver `PERFIS-E-PERMISSOES.md`, que já marca essa pendência).
4. Rotas exatas do gateway nginx para futuros serviços não foram materialmente verificadas — padrão `/apps/<svc>-api/` é PROVEN para serviços existentes; registro novo é `PLANNED`.
5. `strategic-indicators-api` provado por testes + helper de engenharia; contrato HTTP exato do endpoint de indicator detail/score não foi enumerado linha a linha — `TO_INVENTORY` em F1 se material ao Overview (fora do escopo Início).
