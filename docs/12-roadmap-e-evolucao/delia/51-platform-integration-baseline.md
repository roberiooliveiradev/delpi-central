# DÉLIA — Baseline de Integração com a Plataforma

**Status:** `CANONICAL_BASELINE` de evidências para integração  
**Escopo:** fatos `PROVEN` + gaps `TO_INVENTORY` + decisões `PLANNED` + arquitetura `TARGET`  
**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Evidence snapshot inicial desta revisão:** `dc1d96f787cca66116e328c32c5a9124d31664df`  
**C0.S0-B revalidation HEAD:** `5deb7fc2c2f1683ebc3f7224e8f6fba99e35854d`  
**C0.S0-C identity/AuthZ HEAD:** `90730043c79cbb984a42db6bbbc615c03091094b`  
**C0.S0-D automation/workers/schedulers HEAD:** `566def330798b6fefe1eda37b3eebd3e46686aba`  
**C0.S0-B scope:** Portal host/auth, Core `/me` `/me/apps`, `/me/routes` resolution, Gateway/Compose declarations, `shared/delpi_auth`, federation/`plugin-ui`, representative Domain OpenAPI. Thematic inventories in later sections remain `TO_INVENTORY` unless revalidated here.  
**C0.S0-C scope:** Keycloak/OIDC Portal client path, Core JWT + user resolution, `authenticate()` vs `PermissionResolver`, `/me` `/me/apps` AuthZ projection, shared FastAPI/Flask auth, Domain AuthZ samples, Chat legacy auth refs.  
**C0.S0-D scope:** Automation Hub physical status, in-process schedulers/workers/outbox, Redis-as-cache vs queue, RPA/computer-use, Domain report schedules, notification/email execution, idempotency/retry samples, Chat tools as reference-only.

## 1. Objetivo

Separar **fatos comprovados no repositório** de targets e itens ainda sujeitos a inventário. Este arquivo não substitui `C0.S0`: toda evidência precisa ser revalidada no HEAD de execução antes de desbloquear qualquer gate.

Taxonomia obrigatória neste baseline:

```text
PROVEN        evidência direta no HEAD, com path/contrato/símbolo identificável
TO_INVENTORY  existência, comportamento, owner, contrato ou readiness ainda não provados
PLANNED       decisão de execução já ordenada pelo Plano Mestre, ainda sem runtime entregue
TARGET        arquitetura/capability desejada, sem implicar implementação
```

Não usar `PARTIAL PROVEN`, `DERIVED FROM PROVEN PLATFORM`, `NOT YET PROVEN` ou equivalentes como substitutos ambíguos. Quando somente uma parte estiver comprovada, registrar explicitamente **o escopo exato do `PROVEN`** e deixar o restante `TO_INVENTORY`.

## 2. Evidências âncora do HEAD

| Área | Estado | Evidência âncora | O que a evidência prova | O que ainda não prova |
|---|---|---|---|---|
| Portal host | `PROVEN` | `portal/src/ui/AppHost.tsx` blob `b981a7d7ab5ba37194b957e10a9b57a677c66a65` | existe host React com flows embedded/external/federated | compatibilidade futura da DÉLIA sem contract test |
| Federated mount | `PROVEN` | `portal/src/ui/AppHost.tsx` | `container.get`, `mount()`, `unmount()`, host props e share scope existem | contrato congelado para DÉLIA |
| Portal auth/context | `PROVEN` | `portal/src/state/AuthContext.tsx` blob `be12e8b7bf10f8017ed1c14fb39e09ee2f8ee1e1` | integração client-side com Keycloak/Core, `getAccessToken`, apps/routes e state de usuário existem | autorização final de cada Domain API |
| Shared federation | `PROVEN` | `plugins/vite/federation.shared.ts` blob `37f87c8998f3b11ab37e1e514cab623c746c8da2` | config compartilhada, `@delpi/plugin-ui`, React singleton e helpers existem | que toda futura surface da DÉLIA deva usar exatamente a mesma shape sem revalidação |
| Core API repository | `PROVEN` | diretório raiz `core-api/` no HEAD `5deb7fc2c` | serviço/repositório existe | todos os endpoints/semânticas exigidos pela DÉLIA |
| Core `/me` | `PROVEN` no escopo HTTP+payload+auth boundary | `core-api/app/interfaces/http/me_controller.py` `get_me`; `auth_middleware.authenticate` blob `2cdbcf06da86261fa2e66c2e5dad2e1bfe93861c`; consumer `portal/src/data/coreApi.ts` `getMe()` → `/core-api/me` | GET autenticado devolve id/name/email/roles/groups/permissions/is_superadmin (+ `consent_pending` opcional); `permissions` vêm de Core persistence via `list_permission_codes_by_user` (**sem** user overrides; superadmin **não** expande para todos os codes) | OpenAPI Core; paridade com `PermissionResolver` |
| Core `/me/apps` | `PROVEN` no escopo HTTP+filter+consumer | `ListUserAppsUseCase` + `AppAuthorizationService.filter_apps` usando `g.current_user.permissions` do `authenticate()`; Portal deriva `routes` de `apps[].routes` | navegação/apresentação filtrada por permission codes + bypass superadmin | **não** é autorização de negócio Domain; herda gap de overrides do `authenticate()` |
| Core JWT validation | `PROVEN` | `shared/delpi_auth/jwt_validator.py` blob `cc04efdce0663ef9d752b9f38fb01c4c9b0a2cde` usado por Core `authenticate()` | fail-closed: exige `KEYCLOAK_AUDIENCE` + `KEYCLOAK_ISSUER`; JWKS + RS256; refresh JWKS em falha de decode | valores runtime de issuer/audience (env); realm export deployado |
| Core user resolution | `PROVEN` | `auth_middleware.authenticate` | `sub`→UUID; lookup by id/email; auto-create; sync name/email; `last_login`; roles/groups/permissions via `rbac_queries` | disabled/inactive user path (não evidenciado) |
| `PermissionResolver` | `PROVEN` | `core-api/app/domain/services/permission_resolver.py` blob `74b89c56552c1c21b6a3f32395550aac4ae92330` | direct∪group + allow/deny overrides; superadmin → `list_all_permission_codes`; cache | **não** usado por `authenticate()` / `/me` / `/me/apps` |
| Permission semantic parity | `SEMANTICALLY_DIFFERENT` | `authenticate`→`list_permission_codes_by_user` vs `PermissionResolver.resolve` | consumers de Resolver: access-profile, export, IAM sync, notifications eligibility, admin explorers, RBAC delta, replace roles/groups | Canonical effective-permission path for `/me` requires Core owner decision |
| Portal OIDC | `PROVEN` path / `CONFIGURED_BY_ENV` values | `portal/src/data/keycloakClient.ts` blob `c432c01e7468cb4f2e203c10c6f1486006def6be`; `AuthContext` refresh/logout | `check-sso` + PKCE S256; `updateToken(60)`; token in memory/`tokenRef`; logout Keycloak + `DELPI_GLOBAL_LOGOUT` | realm/client/issuer values reais = env (`VITE_KC_*`); sem realm JSON no repo |
| Shared FastAPI auth | `PROVEN` | `shared/delpi_auth/middleware/fastapi_auth.py` blob `7fd11c8b76944af4ed3eb81b7653c441e6b9452e` | JWT validate → `GET Core /me` reload RBAC; fallback claims com `permissions=[]` + `rbac_unavailable` | herda semantics de `/me` (sem overrides) |
| Shared Flask auth | `DEAD_CODE_CANDIDATE` | `shared/delpi_auth/middleware/flask_auth.py` blob `ec5a2bf96e1a243881724e7a84910e19913b5742` | lê `permissions`/`roles`/`groups`/`is_superadmin` **direto do JWT** | **zero** imports de produção encontrados; se ativado = `SECURITY_DRIFT` potencial |
| Domain AuthZ samples | `PROVEN` (amostra, não universal) | `api-delpi` `BranchAccessGate` + `delpi_auth`; `transformometro-api` `FilialAccessScopeService` | platform permission codes + regras de escopo de filial Domain | demais APIs = `TO_INVENTORY` |
| Core `/me/routes` | **não é contrato vigente** | nenhum `@route("/me/routes")` em `core-api/app`; teste órfão `test_get_me_routes_endpoint`; Chat `CoreApiHttpGateway.get_routes` chama `me/routes` sem outro consumidor; Project Instructions ainda citam o path | ausência do producer no HEAD | não inventar a rota |
| Gateway repository | `PROVEN` | `gateway/nginx.conf` + `gateway/nginx.dev.conf` | `/core-api/`, `/apps/<service>-api/`, generic `/apps/([^/]+)/assets/remoteEntry.js` → `delpi-$1`; Chat `/apps/minha-delpi-ai/api/` | rota/config final da DÉLIA; JWT no gateway (não evidenciado) |
| Infra repository | `PROVEN` | diretório raiz `infra/` no snapshot | infraestrutura versionada existe | storage/network/deploy adequados a cada capability futura |
| API DELPI repository | `PROVEN` | diretório raiz `api-delpi/` no snapshot | componente existe | manifesto/OpenAPI/ownership funcional específico sem inspeção adicional |
| APIs dedicadas | `PROVEN` | múltiplos diretórios de APIs no snapshot raiz | padrão de serviços independentes existe no monorepo | que uma estrutura específica seja automaticamente correta para a DÉLIA |
| DÉLIA runtime | `TO_INVENTORY` quanto a qualquer implementação; programa `PLANNED / NOT_STARTED` | ledger + placeholder documental | não há prova documental de runtime entregue | qualquer API/MFE/DB/deploy da DÉLIA |
| Automation Hub physical | `NOT_PROVEN_AS_PHYSICAL_SERVICE` | nenhum serviço/compose/gateway `automation-hub`; `52` cita `automation_hub/` só como adapter futuro | autoridade semântica permanece TARGET | runtime Hub |
| Platform schedulers | `PROVEN` como loops in-process **por serviço**, não scheduler corporativo | Core `notification_dispatch_scheduler` + `usage_session_flush_scheduler`; commercial `integration_jobs_scheduler`; requests `outbox_worker`; Pulse `DevicePollSchedulerService`; SI `period_scores_scheduler`; TM/CIPA mail-trace loops; purchase-requests pollers | timer técnico Domain/Core | Recurring Governed Work; timezone/DST/misfire corporativos |
| Queues/brokers | `PROVEN` cache Redis opcional; `NOT_PROVEN` job broker | `api-delpi` `RedisQueryCache`; Compose `REDIS_URL` env; sem RabbitMQ/Kafka/NATS/Celery no HEAD | Redis ≠ fila de jobs | Event Bus / worker pool |
| RPA / computer-use | `NOT_PROVEN` como business RPA | Playwright em `portal/scripts/test-launcher-routes-alignment.mjs` = TEST_AUTOMATION | nenhum UiPath/Selenium/Robocorp runtime | Automation Hub RPA |
| Recurring user intent | `PARTIAL` Domain-only | api-delpi `reports.report_schedules` + personal subscription + `process-pending-report-schedules.sh` (cron **host**, não Compose) | agenda de relatório + e-mail Graph | Recurring Governed Work first-class DÉLIA |

A presença de arquivo/diretório não prova uso, readiness, contrato completo, produção, segurança ou compatibilidade. `C0.S0` deve seguir producers/consumers e contratos reais.

## 3. Portal / AppHost — PROVEN no escopo acima

O HEAD comprova que `AppHost` suporta caminhos `embedded`, `external` e `federated`. No flow federado atual ele resolve entry, inicializa share scope, busca exposed module, exige `mount()` e fornece props como:

```text
getAccessToken
basePath
pathname
search
alternateEntry
appRoutes
routeLabel
permissions
isSuperadmin
```

Também existe cleanup por `unmount()` quando disponibilizado pelo remote.

**Decisão para DÉLIA:** `PLANNED` reutilizar contrato de host da plataforma em vez de criar host paralelo. A compatibilidade exata e qualquer extensão necessária são `TO_INVENTORY`/contract-first em C0/C1.

## 4. Auth / Core-driven app context — PROVEN no Portal

`AuthContext` atual comprova client integration com Keycloak/Core e mantém `user`, `apps`, `routes`, favorites/notifications e `getAccessToken`.

Isso **não** transforma Portal state nem props como `permissions` em authority final de escrita. Invariante:

```text
JWT/Portal context = identidade/contexto
Core/permission resolver = authority de plataforma
Domain API = regra/autorização final de negócio
DÉLIA = não amplia permission
```

C0.S0-B seguiu producer/consumer no HEAD `5deb7fc2c`:

```text
Portal keycloak-js (VITE_KC_URL/REALM/CLIENT_ID, PKCE S256)
→ access token em tokenRef / getAccessToken
→ GET /core-api/me
→ GET /core-api/me/apps
→ AuthContext.user / apps / routes derivadas de apps[].routes
→ AppHost federated props (inclui permissions/isSuperadmin como contexto de host)
```

`GET /me/routes` **não existe** no Core neste HEAD. Rotas autorizadas vivem em `/me/apps` (`apps[].routes`). Referências restantes (Project Instructions, docs históricos, teste órfão, Chat `get_routes`) são `STALE_DOCUMENTATION` / `STALE_TEST` / `LEGACY_REFERENCE`.

Campos de contrato ainda `TO_INVENTORY`: catálogo completo de erros, limits, idempotency de writes de favorites, observability, OpenAPI do Core, paridade `PermissionResolver` (inclui overrides) vs `rbac_queries.list_permission_codes_by_user` usado em `authenticate()` (roles diretas ∪ grupos, sem overrides no SQL inspecionado).

## 5. Module Federation / plugin-ui — PROVEN no escopo atual

`plugins/vite/federation.shared.ts` comprova configuração compartilhada de federation, remote de `@delpi/plugin-ui`, React singleton e helpers atuais.

**TARGET:** MFE da DÉLIA reutiliza foundation neutra confirmada, sem source-import de Portal/Chat. Qualquer nova abstração compartilhada passa Abstraction Gate e exige 2+ consumers reais, owner, contrato pequeno e testes.

C0.S0-B: `plugins/commercial/vite.config.ts` consome `pluginUiRemote()` + `FEDERATION_SHARED_WITH_DIAGRAM`; `commercial.manifest.json` usa `schemaVersion 1.0.0`, `type: microfrontend`, `entry: /apps/commercial/assets/remoteEntry.js`. `shared/delpi_auth` valida JWT (AuthN) e, no middleware FastAPI, busca RBAC em Core `GET /me`. O helper Flask `shared/delpi_auth/middleware/flask_auth.py` lê `permissions` do JWT e **não teve consumidores** neste HEAD — não classificar como reuse seguro.

## 6. Core API — owner normativo; implementação detalhada TO_INVENTORY

`core-api/` existe no HEAD. Pelas autoridades oficiais, Core permanece owner de apps/rotas/RBAC/governança.

C0.S0-B provou, no HEAD `5deb7fc2c`, estes endpoints efetivamente usados pelo Portal:

```text
GET /me
GET /me/apps
```

JWT é validado por `delpi_auth.jwt_validator.validate_token` (issuer/audience obrigatórios). Permissões efetivas em `/me` vêm do Postgres Core via `authenticate()`, não do JWT. Domain APIs FastAPI (`shared/delpi_auth/middleware/fastapi_auth.py`) recarregam RBAC com `GET {CORE_API_URL}/me`.

Ainda `TO_INVENTORY`: OpenAPI/operationIds do Core; service identity/background além de `CORE_API_INTEGRATIONS_SERVICE_TOKEN`; catálogo de erros; paridade PermissionResolver vs query do middleware; consumers além de Portal e `delpi_auth` FastAPI.

Não inferir contrato a partir do nome do serviço.

## 7. APIs dedicadas — PROVEN como padrão físico; reuso específico TO_INVENTORY

O monorepo contém múltiplos serviços independentes. Isso comprova que serviço dedicado é um padrão existente, mas **não** prova naming, skeleton, dependency set ou deployment contract da DÉLIA.

A criação física da DÉLIA continua `PLANNED` após Foundation Freeze, conforme `16/52`.

## 8. api-delpi / Domain APIs — presença PROVEN; contratos TO_INVENTORY

`api-delpi/` existe no HEAD. Domain APIs permanecem authorities de dados/regras de seus domínios por decisão arquitetural.

Antes de declarar qualquer action/read reutilizável pela DÉLIA, C0 precisa provar por API:

```text
owner
OpenAPI/operationId
request/response/errors
AuthN/AuthZ
idempotency
limits/retries
observability
data/business authority
postcondition source
```

DÉLIA consome contratos aprovados; não replica business rule nem integração proprietária apenas por conveniência.

## 9. Gateway / Infra — presença PROVEN; readiness DÉLIA TO_INVENTORY

`gateway/` e `infra/` existem no HEAD. C0.S0-B inspecionou **declarações** (não prova de processo em execução):

```text
location ^~ /core-api/     → core-api:8000
location ^~ /apps/<name>-api/  → delpi-<name>-api (padrão BFF)
location ~ ^/apps/([^/]+)/assets/remoteEntry.js$ → http://delpi-$1/assets/remoteEntry.js
location ^~ /apps/minha-delpi-ai/api/ → Chat (vizinho)
/apps/minha-delpi-copilot-api/  AUSENTE
Compose: keycloak, core-api, portal, gateway, minha-delpi-ai-api, minha-delpi-chat, Domain APIs
```

Rotas, Compose, network, secrets, storage, health, deployment e rollback específicos da DÉLIA permanecem `TO_INVENTORY` até C0/C1.

**PLANNED:** runtime da DÉLIA terá deploy/rollback próprios e nenhuma dependência operacional do Chat.

## 10. SSO/autorização — baseline factual (C0.S0-C) + TARGET DÉLIA

### 10.1 Authority boundary — `PROVEN` no HEAD atual

```text
Keycloak = AuthN / SSO identity (JWT)
Core = platform AuthZ (RBAC persistence + /me projection)
Domain API = final business/domain AuthZ (revalida codes + regras de domínio)
Portal = apresenta context (token + /me + /me/apps); não é autoridade
DÉLIA = consumidor futuro; não é authority
```

### 10.2 Cadeia factual atual

```text
Keycloak-js (Portal)
→ Bearer JWT
→ Core authenticate(): validate_token + user resolve + list_permission_codes_by_user
→ GET /me | GET /me/apps (permissions sem overrides)
→ Domain FastAPI jwt_middleware: validate_token + reload Core /me
→ Domain helpers (has_permission / BranchAccessGate / FilialAccessScope…)
```

### 10.3 Drift material — permission dual path

| Path | Overrides | Superadmin permissions list |
|---|---|---|
| `authenticate()` / `/me` / `/me/apps` / Domain reload via `/me` | **não** | flags `is_superadmin`; lista = só roles∪groups |
| `PermissionResolver` (`/me/access-profile`, admin/export/notif…) | allow/deny | **todos** os codes |

Classificação: `SEMANTICALLY_DIFFERENT` + `IMPLEMENTATION_DRIFT` (+ `SECURITY_DRIFT` se deny-override existir em dados reais).  
`ARCHITECTURE_DECISION_REQUIRED` (owner Core): qual path é canônico para projeção efetiva em `/me`.

### 10.4 Docs vs código

`docs/03-autenticacao-autorizacao/jwt.md` ainda descreve dívida P0 (`verify_aud` condicional / issuer não passado). Código atual de `jwt_validator.py` **exige** issuer+audience fail-closed → `DOCUMENTATION_DRIFT`.

### 10.5 TARGET DÉLIA (não runtime)

```text
Keycloak → Portal/session → DÉLIA MFE → Gateway → DÉLIA API JWT → Core permission context → Domain final AuthZ
```

Background/service identity para continuous/autonomous operations permanece `TO_INVENTORY`.

## 11. OpenAPI Business Action integration — TARGET

```text
OpenAPI/contract
→ DÉLIA discovery/index
→ Capability Projection
→ planner
→ Policy/Decision
→ Work/orchestration
→ Automation Hub / Domain API / approved executor contract
→ authoritative Outcome verification
```

Sem endpoint-specific planner teaching. Provider/executor metadata nunca concede permission.

## 12. Notifications / sockets / workers / schedulers — C0.S0-D factual

### 12.1 Notifications — `PROVEN` (execução técnica fragmentada)

```text
Domain/Core decide criar notificação
→ Core persistência + dispatch pending (DB poll)
→ Core notification_dispatch_scheduler (socketio background, poll ~60s)
→ in-app Portal/socket
→ e-mail Graph opcional (CORE_NOTIFICATION_MAIL_ENABLED)
```

Outbox Domain (commercial/requests) publica no Core via HTTP; retry/backoff é **por serviço**.  
Graph `send_mail_to` = aceite do provider (HTTP), **não** outcome de negócio (leitura/entrega).

### 12.2 Workers / schedulers — `PROVEN` in-process; sem worker platform

Não há Celery/RQ/Dramatiq/APScheduler/Temporal/Airflow/K8s CronJob/GitHub `schedule:` no HEAD.

Mecanismos físicos: loops `asyncio`/`threading`/`socketio.start_background_task` **dentro** do processo da API dona. Realtime hubs (commercial/TM/Pulse/requests/TV) são **pub/sub in-memory**, não fila.

### 12.3 O que isso **não** prova

Event Bus corporativo, Automation Hub, Recurring Governed Work, Process Mining worker, AI Control Tower.

## 13. DÉLIA surfaces — TARGET

```text
GLOBAL
WORKSPACE
MEETING
FRONTLINE
FUTURE TEAMS SURFACE
BACKGROUND WATCH/WORKFLOW
ADMIN GOVERNANCE SURFACES
```

Mesma identidade de produto e mesma authority de Policy/Decision/Work. Surface não cria segundo planner/runtime.

## 14. Media / Realtime — TO_INVENTORY

Não considerar comprovados: corporate STT/TTS/Vision provider, WebRTC/realtime standard, recording/transcription infra, media store, browser abstraction, quotas/cost/latency ou retention policy.

## 15. Devices / Frontline — TO_INVENTORY

Não considerar comprovados: standardized tablets/kiosks, production-station mic/camera, device identity service, shared-terminal policy, factory network ou production-terminal contracts.

## 16. Biometric Identity — TO_INVENTORY

Enrollment/photo/voice/template/liveness/providers/thresholds/governance owners precisam evidence. Keycloak/Core identity authority permanece independente de biometria.

## 17. Internet Research / Egress — TO_INVENTORY

Approved search provider, shared search API, safe-fetch component, outbound proxy/allowlist, protected-destination blocking, malware/content policy, browser automation e research cache ainda não estão provados neste baseline.

## 18. OAuth / Secret Management — TO_INVENTORY

Reusable OAuth callback framework, state/nonce/PKCE conventions, token vault, rotation/revocation, connection ownership/admin consent/provider scopes exigem evidência. Credenciais existentes em outro app não são automaticamente reutilizáveis.

## 19. Microsoft 365 / Teams — TO_INVENTORY

Inventariar Entra/Graph registrations, delegated/application/resource consent, Outlook/Teams/SharePoint/OneDrive integrations, messages/meetings/transcripts/recordings/change notifications, app/tab/bot e owners.

Raw realtime media bot não é requisito do conector base.

## 20. Google Workspace / Gmail — TO_INVENTORY

Inventariar OAuth app, Gmail/Calendar/Drive, scopes, push/PubSub, token lifecycle e owner.

## 21. WhatsApp / Other Connectors — TO_INVENTORY

Mapear integrações oficiais suportadas e Slack/GitHub/CRMs/service desks somente com evidência real. Personal WhatsApp Web scraping não é target default.

## 22. Provider/domain events — TO_INVENTORY

Mapear event/webhook authenticity, EventEnvelope compatibility, dedupe/order, renewal/reconciliation, polling fallback, domain owners, replay/freshness. Não inventar event platform antes de gap proof.

## 23. Automation / RPA / Automation Hub — C0.S0-D

Autoridade semântica (TARGET, inalterada):

```text
DÉLIA = inteligência + Policy + Decision + Work/orquestração + Outcome coordination
Automation Hub = execução técnica
Domain API = autoridade de negócio + postcondition
```

Implementação física do Hub: `NOT_PROVEN_AS_PHYSICAL_SERVICE`.  
RPA/computer-use de negócio: `NOT_PROVEN`. Playwright = TEST_AUTOMATION.

Execução técnica **hoje** = HTTP nas Domain APIs + loops in-process + Graph mail + Core notify. Não é Hub.

Residual `TO_INVENTORY`: vendors/licenças RPA, VDI, worker leases, kill-switch corporativo.

## 24. Scripts / Functions / Jobs — C0.S0-D

`PROVEN`: `api-delpi/scripts/process-pending-report-schedules.sh` (cron host documentado; dispara HTTP S2S). Chat attachment indexer = thread daemon (CHAT_ONLY). CLI/scripts de CI = CI, não executor de negócio.

Script existente **não** é executor da DÉLIA.

## 25. Background execution / service identity — C0.S0-D

`PROVEN`: tokens S2S (`X-Delpi-Service-Token` / `CORE_API_INTEGRATIONS_SERVICE_TOKEN`) em jobs de reports/notificações.  
`TO_INVENTORY`: identidade de background auditável unificada, lease/heartbeat, drain, isolation.

Worker identity != business actor permanece invariante.

## 26. Rule / Decision / BPM engines — TO_INVENTORY

Sem engine BPM corporativo evidenciado neste passo. Regras Domain (ex. filial) permanecem na API dona.

## 27. Business postcondition / Outcome sources — C0.S0-D amostra

Padrão atual: HTTP 2xx / Graph accepted / outbox `published` = sucesso **técnico**.  
Postcondition de negócio (invoice existe, destinatário leu) **não** é verificada de forma uniforme → `TO_INVENTORY BY DOMAIN`.  
Idempotência: `PROVEN` em requests-api `idempotency_keys`; `PARTIAL` via `dedupeKey` de notificação; `ABSENT` como contrato transversal.

## 28. Notification / Escalation channels — C0.S0-D

Portal in-app + Core dispatch: `PROVEN`.  
E-mail Graph: `PROVEN` como provider técnico (Core, api-delpi reports, atas TM/CIPA/CEC).  
Teams/WhatsApp Business como canal de execução: `TO_INVENTORY`.  
Escalation/SLA unificado: `TO_INVENTORY`.

## 29. Process Intelligence / Process Mining — TO_INVENTORY

Nenhuma plataforma transversal deve ser presumida. C0 mapeia event logs/audit trails, case/business keys, activity/timestamps/statuses, BPMN/process docs, process owners/KPIs, historical completeness/data quality e task-mining/privacy.

Audit log ≠ event log de processo adequado sem semântica de case/activity comprovada.

## 30. AI Control Tower — TO_INVENTORY

Inventariar AI/model/automation assets, owners, risk/compliance, eval registries, usage/cost telemetry, flags/kill switches, incidents/change management e deployment dependencies.

Dashboard existente ≠ Control Tower automaticamente.

## 31. MCP / A2A / Agent interoperability — TO_INVENTORY

Inventariar servers/clients, agent frameworks/protocols, tool registries, approved agents, delegation identities, credentials/scoping, network boundaries e protocol/security versions.

Market support ≠ DELPI infrastructure.

## 32. Personal Memory / Personalization — TO_INVENTORY

Core profile/favorites podem fornecer fatos, mas C0 deve mapear stores, privacy/retention/delete/export owners, notification preferences e shared-device behavior. Profile field ≠ approved AI memory.

## 33. Semantic Business Layer — TO_INVENTORY

Inventariar BI semantic models, KPI formulas em APIs/frontends/spreadsheets, glossary, warehouse/lake/SQL definitions, metric/dimension owners, grain/freshness/security e conflicts.

Business Graph ≠ Semantic Layer.

## 34. Analysis Sandbox — TO_INVENTORY

Provar Python/Jupyter/code execution, isolated runtimes, query engines, package policies, object/temp storage, file scanning, quotas, egress controls e reproducibility. Developer machine Python ≠ production sandbox.

## 35. Artifact generation/workspace — TO_INVENTORY

Inventariar document/spreadsheet/presentation/PDF/chart generation, storage, versioning/collaboration, comments/review, export/share e retention/ACL owners. Geração isolada em plugin ≠ shared Artifact Workspace.

## 36. Predictive / Prescriptive Intelligence — TO_INVENTORY

Inventariar forecasting/anomaly/classification/optimization models, datasets, ground truth, evals, owners, deployment runtime e analytical models. LLM availability ≠ predictive capability.

## 37. Operational / Digital Twin — TO_INVENTORY

Inventariar simulation/twin tools, MES/IoT/historian state, capacity/planning models, solvers, scenario models e update frequency. Business Graph ≠ Operational Twin.

## 38. Edge / Offline Industrial — TO_INVENTORY

Inventariar factory network reliability, Edge platforms/gateways, PCs/tablets/kiosks, MDM, GPU/NPU/CPU/storage, local inference, time sync, procedure/drawing distribution, offline requirements e OT segmentation.

Factory PC ≠ governed Edge runtime.

## 39. AI Model Lifecycle / MLOps — TO_INVENTORY

Inventariar providers/accounts, local ML models, model registry, CI/CD/deployment, datasets/eval suites, drift monitoring, rollback, ownership e Edge distribution. Model Router target ≠ model lifecycle infrastructure.

## 40. Capability Marketplace / Supply Chain — TO_INVENTORY

Inventariar reusable catalog/plugin mechanisms, package signing/integrity, dependency/license/vulnerability controls, publisher ownership e lifecycle. Plugin manifest system ≠ AI Marketplace automaticamente.

## 41. Personal vs organizational data / privacy — TO_INVENTORY

Inventariar policies de delegated accounts/shared resources, Personal Memory, Process/Task Mining, artifacts, model datasets/evals, Edge caches, sandbox temp data, AI asset metadata e Organizational Knowledge promotion.

## 42. Operational context — TO_INVENTORY BY DOMAIN

`WorkspaceContext + EntityRef` é TARGET. C0 prova owners/IDs/contracts reais para OP/operation/machine/workstation/product/revision/lot/material/tool antes de estabilizar schema.

## 43. Industrial/OT — TO_INVENTORY / no-actuation invariant

Protocolos/SCADA/MES/telemetry/command APIs/network reachability/safety architecture não são presumidos. Mesmo que command interface exista, isso não autoriza DÉLIA/Edge/RPA a atuar fisicamente.

## 44. Mandatory C0.S0 inventory summary

```text
platform/API/MFE/infra
media/device/biometric/privacy
Internet/OAuth/connectors/Teams
events/RPA/automation/workers/service identity/outcome
process logs/process owners/task mining
AI assets/Control Tower/model lifecycle/evals/cost/incidents
MCP/A2A/tools/agents
personal memory/preferences/privacy
semantic metrics/glossary/BI models
sandbox/query/file/artifact infrastructure
predictive/optimization/simulation/twin
Edge/offline devices/network/MDM/local inference
marketplace/package/supply-chain
OT safety
```

## 45. Baseline conclusion

### PROVEN neste snapshot, no escopo explicitamente observado

```text
Portal AppHost/federated mount artifacts (blob inalterado vs snapshot inicial)
Portal AuthContext Keycloak/Core client integration (blob inalterado)
shared federation/plugin-ui configuration artifact (blob inalterado)
presence of Core API, Gateway, Infra, api-delpi and multiple dedicated API repositories
GET /me and GET /me/apps producer + Portal consumer + FastAPI delpi_auth RBAC lookup
Portal derives navigation routes from /me/apps[].routes
GET /me/routes producer absent
Gateway path patterns for Core, Domain *-api, generic MFE remoteEntry; Chat neighbor; no DÉLIA locations
Compose service declarations for Keycloak/Core/Portal/Gateway/Chat/Domain APIs (not runtime proof)
api-delpi OpenAPI served at /openapi.json with BearerAuth + x-delpi extensions; baseline JSON versionado
transformometro-api FastAPI + delpi_auth JWT middleware (BFF sample; GPT Actions OpenAPI is a facade)
```

### TO_INVENTORY antes de declarar reusable/runtime-ready

```text
OpenAPI/error catalog/limits/observability do Core
paridade PermissionResolver (overrides) vs list_permission_codes_by_user no authenticate()
consumers Domain API além da amostra FastAPI/api-delpi/transformometro
Gateway/Compose/storage/secrets/network readiness para DÉLIA (declaração ≠ processo running)
background identity/workers/events
media/biometric/Internet/OAuth/connectors/Teams
Automation Hub/RPA executors
Process Intelligence/Control Tower/MCP-A2A
Personal Memory/Semantic Layer/Sandbox/Artifacts
Predictive/Twin/Edge/MLOps/Marketplace
OT privacy/safety implementation details
```

### PLANNED / TARGET

DÉLIA permanece `PLANNED / NOT_STARTED`; sua aplicação standalone, contracts e capabilities são target/plan até evidência válida para o SHA/config executado.

Portanto `C0.S0` continua obrigatório e nenhuma capability, integração ou foundation é promovida a `PASS` apenas por esta documentação.
