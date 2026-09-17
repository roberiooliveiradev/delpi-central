# DÉLIA — Baseline de Integração com a Plataforma

**Status:** `CANONICAL_BASELINE` de evidências para integração  
**Escopo:** fatos `PROVEN` + gaps `TO_INVENTORY` + decisões `PLANNED` + arquitetura `TARGET`  
**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Evidence snapshot inicial desta revisão:** `dc1d96f787cca66116e328c32c5a9124d31664df`  
**C0.S0-B revalidation HEAD:** `5deb7fc2c2f1683ebc3f7224e8f6fba99e35854d`  
**C0.S0-C identity/AuthZ HEAD:** `90730043c79cbb984a42db6bbbc615c03091094b`  
**C0.S0-D automation/workers/schedulers HEAD:** `566def330798b6fefe1eda37b3eebd3e46686aba`  
**C0.S0-E events/webhooks/connectors HEAD:** `aa3d93eee710c1c74fe56b9f7a45cd652d19c827` (task start `96d2591cd`; revalidated after unrelated Pulse/TM commits)  
**C0.S0-F OAuth/secrets/vault/egress HEAD:** `c6c9c8370d037edfc3529821b9d63e138b153436` (task start `633d10d2a`; revalidated after unrelated TM GPT specialist commit)  
**C0.S0-G media/device/biometric/frontline HEAD:** `79378e48184a118df060e164111d7a5963c06f34`  
**C0.S0-H Process Intelligence / event-log HEAD:** `79378e48184a118df060e164111d7a5963c06f34`  
**C0.S0-I AI Control Tower / model governance HEAD:** `cd688f2ff0d3829ea20e2c21b140d3378d7cc538` (task start inventory at `aec6f1294`; intermediate `79378e481` docs; HEAD moved via Transformômetro then Pulse — AI conclusions revalidated)  
**C0.S0-J Personal Memory / preferences / privacy HEAD:** `792cc990c27873a688c0f0638cf6292ed8910a8f`  
**C0.S0-K Semantic Business Layer / metrics / Business Graph HEAD:** `792cc990c27873a688c0f0638cf6292ed8910a8f`  
**C0.S0-L Analysis Sandbox / Artifact infrastructure HEAD:** `d3851a5323347aafb7d2a457c1337ba500abdce5` (prior K at `792cc990c`; HEAD moved via Transformômetro docs — sandbox conclusions revalidated)  
**C0.S0-M Predictive / Prescriptive / Operational Twin HEAD:** `8d9fa79679e91b5e65aed3c8b57bb2c240f031d7` (task start `09ea5aa79`; intermediate Transformômetro tests; FINAL revalidated after TÉO Builder docs commit — predictive conclusions unchanged)  
**C0.S0-N Edge / Offline / Industrial residual HEAD:** `6038ec5c841a4f03206b8fa342466dfecb68ef63` (prior M at `8d9fa7967`; HEAD moved via Transformômetro PT-first tests — Edge/OT conclusions revalidated)  
**C0.S0-O AI Model Lifecycle / MLOps / Capability Marketplace HEAD:** `6038ec5c841a4f03206b8fa342466dfecb68ef63` (same HEAD as N; I/M/N residuals revalidated — no material EXECUTION_DRIFT)  
**C0.S0-P Personal vs Organizational Data / Privacy HEAD:** `6038ec5c841a4f03206b8fa342466dfecb68ef63` (same HEAD as O; G/H/J/K/L/M/N/O privacy residuals revalidated)  
**C0.S0-Q Operational Context / EntityRef / Workspace HEAD:** `6038ec5c841a4f03206b8fa342466dfecb68ef63` (same HEAD as P; B/C/K EntityRef and Portal context residuals revalidated)  
**C0.S0-R MCP / A2A / Agent Interoperability residual HEAD:** `10f874c84f4a661b9851a9179be8d1418e029a2a` (prior Q at `6038ec5c8`; HEAD moved via TV Dashboard GPT Actions OAuth façade — MCP/A2A conclusions revalidated; TV GPT Actions = OpenAPI Custom GPT ≠ MCP)  
**C0.S0-S OT Safety / Independent Interlocks / Approval Matrix residual HEAD:** `bcf23241e058c03fae74dc24231adebdf34d297c` (prior R at `10f874c84`; HEAD moved via commercial Fase 1R docs — OT/safety/approval conclusions revalidated; no device actuation)  
**C0.S0-T residual consolidation / readiness HEAD:** `f1cce79b871bf0b5dbd7b8d332ead53e3fb44716` (prior S at `bcf23241e`; HEAD moved via TV GPT Actions 401/policy — consolidation revalidated; DÉLIA_RUNTIME_DIFF still NONE)  
**C0.S0-T canonical reconciliation HEAD:** `68ea41d9b5aac6216b5ab531f7cdccc93d64c3bc` (task start `674670ce7`; HEAD moved via Transformômetro GPT commit — AuthZ/`633d10d2a` revalidated; architecture review EXECUTION_DRIFT on stale docs reconciled — no DÉLIA/Core runtime change in this task)  
**C0.S0-B scope:** Portal host/auth, Core `/me` `/me/apps`, `/me/routes` resolution, Gateway/Compose declarations, `shared/delpi_auth`, federation/`plugin-ui`, representative Domain OpenAPI. Thematic inventories in later sections remain `TO_INVENTORY` unless revalidated here.  
**C0.S0-C scope:** Keycloak/OIDC Portal client path, Core JWT + user resolution, `authenticate()` vs `PermissionResolver`, `/me` `/me/apps` AuthZ projection, shared FastAPI/Flask auth, Domain AuthZ samples, Chat legacy auth refs.  
**C0.S0-D scope:** Automation Hub physical status, in-process schedulers/workers/outbox, Redis-as-cache vs queue, RPA/computer-use, Domain report schedules, notification/email execution, idempotency/retry samples, Chat tools as reference-only.  
**C0.S0-E scope:** signal taxonomy, Core domain EventBus≠broker, inbound/outbound webhooks, Graph mail/trace, Teams/WhatsApp/MCP physical status, Chat web_search, outbox, Pulse device-ota callbacks.  
**C0.S0-F scope:** credential classes, env secret storage, vault status, ExternalConnection status, Keycloak PKCE + Graph client_credentials, revoke/rotation, Chat ExternalProviderUrlPolicy SSRF, token→LLM/MFE boundaries.  
**C0.S0-G scope:** media upload/capture taxonomy, realtime media, camera/mic, transcript/recording, Pulse devices/OTA/commands, frontline surfaces, biometrics/Human Observation, vision/voice, OT/safety linkage, Edge/offline.  
**C0.S0-H scope:** process evidence sources, event-log fitness, case/activity/timestamp/grain, Process Mining/Discovery/Conformance/Variant/Bottleneck runtime status, Task Mining, Human Observation/employment boundaries, BPM/process models.  
**C0.S0-I scope:** AI providers/models, routing/fallback, prompts, evals, Control Tower, model registry, fine-tuning, cost/latency telemetry, kill-switches, Chat-as-reference boundaries.  
**C0.S0-J scope:** Personal Memory physical status, session vs durable context, Core/Chat preferences/profiles, isolation, retention/delete/export, consent, knowledge-candidate lifecycle, semantic personalization, privacy surfaces.  
**C0.S0-K scope:** Semantic Business Layer status, Domain/Chat metrics & glossaries, entity identity, Business Graph status, provenance/versioning, AuthZ boundary, materialization/staleness.  
**C0.S0-L scope:** analysis sandbox status, Python/SQL/notebook execution, isolation/limits/egress/secrets, artifact generators/storage/AuthZ, malware/path controls, Automation Hub overlap.  
**C0.S0-M scope:** predictive/anomaly/forecast mechanisms, prescriptive/recommendation, optimization/simulation, Operational/Digital Twin, prediction≠fact, SIMULATE≠APPLY, OT/AI→machine safety.  
**C0.S0-N scope:** Edge runtime residual, offline/AuthZ, Pulse device identity/OTA/commands, store-and-forward, industrial protocols, MES/historian, safety/AI→machine, fail-closed.  
**C0.S0-O scope:** model lifecycle/registry, training/FT, MLOps tooling, promotion/rollback, capability catalog vs Marketplace, plugin supply-chain, AuthZ boundaries.  
**C0.S0-P scope:** personal vs organizational data classes, owners/subjects/scopes, consent/purpose, retention/delete/export, provider/LLM exposure, Knowledge/Memory boundaries, Human Observation/employment.  
**C0.S0-Q scope:** Operational Context status, Portal/Core/Domain context, EntityRef, Workspace, branch/tenant semantics, context≠AuthZ, TOCTOU.  
**C0.S0-R scope:** MCP/A2A runtime residual, servers/clients/transports/auth, tool discovery vs AuthZ, write governance, agent identity/delegation, Marketplace/Hub/planner boundaries, remote trust/egress.  
**C0.S0-S scope:** OT safety controller/interlocks/e-stop, business vs safety approval, PREPARE/ACT, Pulse command materiality, fail-safe/cloud independence, kill-switch≠e-stop.  
**C0.S0-T scope:** consolidate A–S residuals; classify blockers; gate matrix; C0.S0 readiness for architecture review (not FOUNDATION_FREEZE).

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
| Core `/me` | `PROVEN` no escopo HTTP+payload+auth boundary | `core-api/app/interfaces/http/me_controller.py` `get_me`; `auth_middleware.authenticate` (aligned since `633d10d2a`); consumer `portal/src/data/coreApi.ts` `getMe()` → `/core-api/me` | GET autenticado devolve id/name/email/roles/groups/permissions/is_superadmin (+ `consent_pending` opcional); `permissions` = **effective** via `PermissionResolver` (direct∪group ± overrides; superadmin → all registered codes) | OpenAPI Core; Domain still final business AuthZ |
| Core `/me/apps` | `PROVEN` no escopo HTTP+filter+consumer | `ListUserAppsUseCase` + `AppAuthorizationService.filter_apps` usando `g.current_user.permissions` do `authenticate()`; Portal deriva `routes` de `apps[].routes` | navegação/apresentação filtrada por **effective** permission codes + bypass superadmin | **não** é autorização de negócio Domain |
| Core JWT validation | `PROVEN` | `shared/delpi_auth/jwt_validator.py` blob `cc04efdce0663ef9d752b9f38fb01c4c9b0a2cde` usado por Core `authenticate()` | fail-closed: exige `KEYCLOAK_AUDIENCE` + `KEYCLOAK_ISSUER`; JWKS + RS256; refresh JWKS em falha de decode | valores runtime de issuer/audience (env); realm export deployado |
| Core user resolution | `PROVEN` | `auth_middleware.authenticate` | `sub`→UUID; lookup by id/email; auto-create; sync name/email; `last_login`; roles/groups via `rbac_queries`; permissions via Resolver | disabled/inactive user path (não evidenciado) |
| `PermissionResolver` | `PROVEN` | `core-api/app/domain/services/permission_resolver.py` | direct∪group + allow/deny overrides; superadmin → `list_all_permission_codes`; cache | **used by** `authenticate()` / `/me` / `/me/apps` / request context since `633d10d2a` |
| Permission semantic parity | `ALIGNED` (request context) | `authenticate` → `PermissionResolver.resolve` → `g.current_user.permissions`; `/me`, `/me/apps`, `/me/access-profile` share effective semantics | CARRY_FORWARD: `list_user_ids_by_permission_code` still role∪group only (no overrides); override-mutation cache hygiene; Core suite health INCONCLUSIVE | JWT claims ≠ final AuthZ; Domain = final business rule |
| Portal OIDC | `PROVEN` path / `CONFIGURED_BY_ENV` values | `portal/src/data/keycloakClient.ts` blob `c432c01e7468cb4f2e203c10c6f1486006def6be`; `AuthContext` refresh/logout | `check-sso` + PKCE S256; `updateToken(60)`; token in memory/`tokenRef`; logout Keycloak + `DELPI_GLOBAL_LOGOUT` | realm/client/issuer values reais = env (`VITE_KC_*`); sem realm JSON no repo |
| Shared FastAPI auth | `PROVEN` | `shared/delpi_auth/middleware/fastapi_auth.py` blob `7fd11c8b76944af4ed3eb81b7653c441e6b9452e` | JWT validate → `GET Core /me` reload RBAC; fallback claims com `permissions=[]` + `rbac_unavailable` | herda **effective** semantics de `/me` (Resolver) |
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
| EventEnvelope shared | `TARGET_ONLY` / `NOT_PROVEN` físico | docs DÉLIA (`17`/`21`); Core `DomainEvent`/`AdminChangedEvent` = dataclass local | envelope canônico compartilhado ausente | EventEnvelope runtime |
| Event bus / broker | `NOT_PROVEN` | Core `application/event_bus.py` = dispatcher in-process (RBAC+audit+Socket.IO); sem Kafka/Rabbit/NATS/Redis Streams | bus corporativo | EventEnvelope transport |
| Inbound provider webhooks | `NOT_PROVEN` | nenhum `/webhook` inbound com HMAC/signature no HEAD | authenticity/replay provider | Graph change notifications |
| Outbound webhooks | `PROVEN` (amostra) | api-delpi `CONSOLE_ALERT_WEBHOOK_URL` (POST JSON, debounce in-memory); Chat `CHAT_LEARNING_FINE_TUNING_TRAIN_WEBHOOK_URL` | fire-and-forget técnico | delivery ACK / Outcome |
| Microsoft Graph mail | `PROVEN` WRITE (sendMail) | Core/api-delpi/TM/CIPA/CEC `microsoft_graph_mail_client` + `GRAPH_*` env | client credentials org-managed | Teams APIs |
| Graph message trace | `PROVEN` READ (poll) | TM/CIPA `microsoft_graph_message_trace_client` | delivery status técnico ≠ outcome negócio | Graph subscriptions |
| Teams / WhatsApp connectors | `NOT_PROVEN` runtime | só docs TARGET + perfil `whatsapp_e164` (contato) | conector mensagem | CP-211/223 |
| Chat web_search | `PROVEN` CHAT_ONLY | DuckDuckGo/SearXNG/Tavily/Serper adapters + query security | pesquisa read | platform-neutral search API |
| MCP/A2A | `DOCUMENTATION_ONLY` / `TARGET` / runtime `NOT_PROVEN` (C0.S0-R) | specs `60` + README copilot; zero MCP/A2A SDK deps; Chat OpenAPI Action Catalog ≠ MCP; GPT Actions TM/TV = OpenAPI Custom GPT ≠ MCP | discovery≠approval; tool metadata≠AuthZ | protocol adapters (future) |
| Vault / secret manager | `NOT_PROVEN` | sem HashiCorp/AWS/Azure/K8s Secrets runtime no Compose/código | env + `.env` host | SecretRef/vault port |
| ExternalConnection first-class | `TARGET_ONLY` | `21` candidate schema; sem tabela/API plataforma | Chat `ai_external_action_providers` = CHAT_LOCAL registry | CP-197 lifecycle |
| OAuth user session | `PROVEN` | Portal Keycloak-js PKCE S256; token em memória/`tokenRef` | USER_DELEGATED | provider OAuth connections |
| Graph client credentials | `PROVEN` | env `GRAPH_*` / `GRAPH_REPORTS_*`; token obtido sob demanda (não persistido) | ORG_MANAGED SERVICE_CONNECTION; scope `.default` | least-privilege evidence |
| Chat SSRF guard | `PARTIAL` CHAT_ONLY | `ExternalProviderUrlPolicy` (scheme/host/private IP) | não é safe-fetch plataforma; DNS rebinding/redirect **ABSENT** | CP-195 |

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

Campos de contrato ainda `TO_INVENTORY`: catálogo completo de erros, limits, idempotency de writes de favorites, observability, OpenAPI do Core. Request-context permissions alinhados via `PermissionResolver` desde `633d10d2a`. CARRY_FORWARD: `list_user_ids_by_permission_code` (sem overrides).

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

Ainda `TO_INVENTORY`: OpenAPI/operationIds do Core; service identity/background além de `CORE_API_INTEGRATIONS_SERVICE_TOKEN`; catálogo de erros; consumers além de Portal e `delpi_auth` FastAPI. AuthZ request-context dual-path: **RESOLVED** (`633d10d2a`).

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
/apps/minha-delpi-copilot-api/  AUSENTE (HISTORICAL temporary planned; SUPERSEDED)
/apps/delia-api/               AUSENTE (FROZEN_CANDIDATE C0.S1; not implemented)
/apps/delia                    AUSENTE (FROZEN_CANDIDATE C0.S1; not implemented)
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

### 10.2 Cadeia factual atual (reconciled — Core SHA `633d10d2a`)

```text
Keycloak-js (Portal)
→ Bearer JWT
→ Core authenticate(): validate_token + user resolve + PermissionResolver.resolve
→ g.current_user.permissions = effective (direct∪group ± overrides; superadmin=all codes)
→ GET /me | GET /me/apps | GET /me/access-profile (effective context aligned)
→ Domain FastAPI jwt_middleware: validate_token + reload Core /me
→ Domain helpers (has_permission / BranchAccessGate / FilialAccessScope…)
```

```text
Core = platform RBAC / governance
Domain APIs = final domain authorization
Portal = consumer (not authority)
DÉLIA = not RBAC authority
JWT claims = not final permission authority
```

### 10.3 Core AuthZ residuals (CARRY_FORWARD — not dual-path ADR)

| Residual | Status |
|---|---|
| Request-context `/me` `/me/apps` `/me/access-profile` effective alignment | **RESOLVED** since `633d10d2a` |
| `list_user_ids_by_permission_code` | CARRY_FORWARD — still role∪group union only (**no** user overrides) |
| Override mutation → effective-permission cache invalidate/recalculate | CARRY_FORWARD — must remain explicit for future mutation paths |
| `IamSyncService` resolve→invalidate ordering | CARRY_FORWARD — non-blocking cleanup |
| Broad Core test suite health | INCONCLUSIVE (prior evidence 264 passed / 30 failed — not re-run here) |

`ARCHITECTURE_DECISION_REQUIRED` for dual `/me` vs Resolver path: **CLOSED** (runtime uses Resolver).  
Stale docs claiming SEMANTICALLY_DIFFERENT for request context = **DOCUMENTATION_DRIFT** (fixed in this reconciliation).

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

## 14. Media / Realtime — C0.S0-G

### 14.1 Taxonomia física (HEAD `79378e481`)

| Classe | Status | Evidência |
|---|---|---|
| IMAGE_UPLOAD | `PROVEN` Domain/Chat | Auditoria 5S fotos; TV Dashboard media; Chat attachments; mural/CX/comercial/PO anexos; Transformômetro signature images |
| VIDEO_UPLOAD | `PROVEN` Domain | `tv-dashboard-api` `MediaStorageService` aceita `video/mp4` (playlist/comunicado) |
| AUDIO_UPLOAD | `NOT_PROVEN` | sem endpoint/storage de áudio como mídia contínua |
| CAMERA_CAPTURE | `DOMAIN_LOCAL` snapshot | `capture="environment"` em `plugins/auditoria-5s/.../CriterionPhotoSection.tsx` e travel-expenses — file picker + câmera móvel; **não** MediaStream |
| MIC_CAPTURE | `NOT_PROVEN` | sem `getUserMedia` / MediaRecorder em plugins |
| SCREEN_CAPTURE | `NOT_PROVEN` | |
| FILE_ATTACHMENT | `PROVEN` | Chat attachments; PO Capex; my-requests; guias; CX forms |
| STREAM / REALTIME_MEDIA | `NOT_PROVEN` | zero `WebRTC`/`getUserMedia`/`MediaStream`/`RTSP`/`HLS` no código de produto |
| TRANSCRIPT / RECORDING | `NOT_PROVEN` runtime | Transformômetro tem script isolado `scripts/test_kimi_ata.py` (transcrição→ata via LLM) = **REFERENCE_ONLY / TEST**; sem STT corporativo |
| DEVICE_TELEMETRY | `DOMAIN_LOCAL` | Production Pulse readings/poll (contadores/gauges) — **não** é mídia A/V |

Realtime **não-mídia** (Socket.IO/WS presence/presentation) permanece classificado em C0.S0-E; **≠** realtime media.

### 14.2 Vision / voice (vizinho Chat vs plataforma)

| Capability | Status | Owner |
|---|---|---|
| Document OCR / drawing vision | `CHAT_ONLY` | `minha-delpi-ai-api` tesseract/easyocr + optional `VISION_LLM_*` |
| Corporate STT/TTS | `NOT_PROVEN` | CP-160 LOCKED como requisito futuro; sem adapter runtime |
| Speaker recognition / diarization | `NOT_PROVEN` | |
| Face analysis / biometrics | `NOT_PROVEN` | ver §16 |

Invariantes: PDF/imagem Chat ≠ policy (CP-088); visual finding ≠ decisão oficial qualidade (CP-177).

### 14.3 Privacy / retention media

```text
PROVEN: auth gates Domain/Chat nos uploads; TV media delete route existe
TO_INVENTORY: retention class-specific (CP-175), malware scan unificado, purpose/consent media (CP-157), raw media minimization cross-app
RISK (Chat): attachment bytes → document vision / Vision LLM path (governed by Chat settings; not DÉLIA)
```

## 15. Devices / Frontline — C0.S0-G

### 15.1 Device registry (Production Pulse)

```text
PROVEN DOMAIN_LOCAL: production-pulse-api devices table + drivers catalog
identity: device UUID + branch + controller_code
credential: device_api_token (header X-Device-Token) for OTA/device→API callbacks
protocols PROVEN: http_counter | http_gauge only (migrations CHECK)
modbus/mqtt/plc: TARGET docs / rejected invalid protocol_kind in tests — NOT_PROVEN runtime
commands: typed command_key (increment/reset/set/reboot/…) via DeviceCommandService
OTA: /device-ota/* authenticate_device(token) — device credential ≠ user JWT
offline: connectivity status from last_seen (telemetry), not Edge authority cache
```

### 15.2 Device identity ≠ user identity

| Subject | AuthN | AuthZ |
|---|---|---|
| Human operator/admin | Keycloak JWT → Core permissions (`guard_operator` / admin) | Pulse RBAC + branch guard |
| Physical device | `device_api_token` / `X-Device-Token` | device-scoped OTA/callback only |

```text
device token ≠ Core permission
device token ≠ Domain business authorization
NO SECURITY_DRIFT found equating device id to user id
```

CP-171 LOCKED (device metadata ≠ identity/authorization) — runtime Pulse aligns.

### 15.3 Frontline surfaces

| Surface | Classificação | Evidência |
|---|---|---|
| Pulse `/operator/*` MFE + API | `FRONTLINE_USER_SURFACE` | operator placements/devices/commands; JWT user + `canOperator` |
| Pulse admin devices/drivers/OTA | `DEVICE_ADMIN` | admin permissions |
| TV Dashboard public present | `DEVICE_ADMIN` / display player | public token present WS — **not** shop-floor operator AuthZ |
| Portal responsive MFEs | `BACKOFFICE` / domain | não classificar como frontline só por mobile CSS |
| Standardized kiosk/MDM/shared-terminal policy | `NOT_PROVEN` / TARGET docs | OPERATOR-SURFACES-P2 `?kiosk=1` = P3 spec |

Offline frontline: **NOT_PROVEN** (operator API requires online auth; no offline permission cache evidenced).

## 16. Biometric Identity / Human Observation — C0.S0-G

| Item | Status |
|---|---|
| Face/voice/fingerprint/iris runtime | `NOT_PROVEN` |
| Enrollment / templates / liveness | `NOT_PROVEN` |
| Closed-set matching | `N/A` (no matcher) |
| Open-world identification | `NOT_PROVEN` (and prohibited by CP-176) |
| Biometric → login/RBAC | `NONE` (invariant preserved; CP-183) |
| Purpose/consent biometric | `DOCUMENTATION_ONLY` (`54-*.md` TARGET) |
| Human Observation process facts runtime | `NOT_PROVEN` |
| Collaborative “presence” (editors online) | ≠ Human Observation |
| Meeting attendance fields (CIPA/comite) | meeting roster — **not** biometric observation |
| Prohibited trait inference (emotion/health/personality-of-people) | `NOT_PROVEN` in product code (`personality` Chat = assistant tone playbook) |
| Employment-decision automation | `NOT_PROVEN` / prohibited by CP-189 |

Signature image upload (Transformômetro atas) = **legal ink/signature capture**, **not** biometric face/voice enrollment.

## 17. Internet Research / Egress — C0.S0-F

### 17.1 Egress físico

```text
PROVEN: outbound HTTPS/HTTP direto dos processos (httpx/requests) — Graph, search, webhooks, Domain→Core
NOT_PROVEN: proxy corporativo / egress gateway / service-mesh allowlist unificado
```

### 17.2 Safe-fetch / SSRF

| Camada | Status |
|---|---|
| Platform Safe Web Fetch (CP-195) | `NOT_PROVEN` / `TARGET` |
| Chat `ExternalProviderUrlPolicy` | `CHAT_LOCAL_GUARD` `PARTIAL`: bloqueia scheme inválido, HTTPS para external, hosts internos nomeados, IP private/loopback/link-local literal; **não** resolve DNS antes do check; **sem** revalidação de redirect |
| Chat web_search query security | sanitiza query (não URL fetch SSRF) |
| SearXNG limiter example | `filter_link_local` configurável — infra search, não safe-fetch app |

### 17.3 Trust

Conteúdo externo / tool output = **UNTRUSTED DATA**. Chat `ToolPolicyService.sanitize_for_llm` e `ExternalActionExecutionPolicy` removem chaves `access_token`/`refresh_token`/`client_secret`/… do payload para o LLM.

## 18. OAuth / Secret Management — C0.S0-F factual

### 18.1 Vault

`NOT_PROVEN` como serviço de plataforma. Secrets = **environment variables** via Compose (`CONFIGURATION_ONLY` templates em `infra/env*.example` / README). Sem Docker/K8s Secrets Manager / HashiCorp Vault evidenciado no runtime Compose.

### 18.2 Credential classes (PROVEN amostras)

| Class | Exemplos | Storage | Lifecycle |
|---|---|---|---|
| USER_DELEGATED | Keycloak Portal access token | browser memory (`tokenRef` / keycloak-js) | PKCE init; `updateToken`; logout Keycloak |
| ORG_MANAGED / SERVICE_CONNECTION | Graph client secret; S2S `*_SERVICE_TOKEN`; Keycloak admin client | env → process memory | client_credentials; Graph token **não** persistido; admin token cache in-process |
| DEVICE_CREDENTIAL / SHARED_RESOURCE | Pulse `X-Device-Token` | device config / DB device fields | enable/disable device |
| CHAT_LOCAL | Tavily/Serper keys; LLM API keys; `auth_config` JSONB em `ai_external_action_providers` | env e/ou Postgres Chat | `enabled` flag provider; **não** ExternalConnection plataforma |

### 18.3 ExternalConnection

First-class plataforma: `TARGET_ONLY` (`21` candidate).  
Chat external action providers = **DOMAIN_LOCAL_EQUIVALENT (CHAT_ONLY)** — registry de OpenAPI providers com `auth_mode`/`auth_config`, `enabled`; **não** satisfaz CP-197 (consent/scopes/revoke/reconnect/audit unificado).

### 18.4 OAuth flows

| Flow | Status |
|---|---|
| Portal Keycloak authorization_code + PKCE | `PROVEN` |
| Graph / Keycloak admin client_credentials | `PROVEN` |
| Provider delegated OAuth (Gmail/Teams user connect) | `NOT_PROVEN` |
| Refresh token server-side store | `NOT_PROVEN` (SPA refresh via Keycloak adapter; Graph CC sem refresh) |
| Provider token revoke/unlink API | `ABSENT` / `NOT_PROVEN` |
| Kill-switch | `PARTIAL`: env empty / `enabled=false` / device disable / Core mail flag |

### 18.5 Boundaries

```text
provider scope (.default Graph) != Core RBAC != Domain AuthZ
credential possession != authorization
Portal getAccessToken = session identity context, not provider secret
SECRET/TOKEN must not enter prompts — Chat sanitizers PROVEN for known keys
```

Rotation: JWKS refresh on validate failure (`jwt_validator`); Graph/S2S = **manual** env rotation. Formal rotation audit: `TO_INVENTORY`.

## 19. Microsoft 365 / Teams — C0.S0-E

Graph **mail send** + **message trace read**: `PROVEN` (não é Teams).

Teams chats/channels/meetings/transcripts/change notifications/app/tab/bot: `NOT_PROVEN` no código. Spec `56` = TARGET.  
**Não** confundir `sendMail` com capability Teams.

## 20. Google Workspace / Gmail — `NOT_PROVEN`

Somente Google Fonts em TV dashboard (asset CSS). Sem Gmail/Calendar/Drive OAuth.

## 21. WhatsApp / Other Connectors — C0.S0-E

WhatsApp Business API / Meta / Twilio: `NOT_PROVEN`.  
`whatsapp_e164` em perfil Core/Commercial = campo de contato, **não** conector de mensagem.  
Scraping sessão pessoal: proibido por authority (CP-211). Slack/GitHub CRM connectors: `NOT_PROVEN` neste inventário.

## 22. Provider/domain events — C0.S0-E factual

### 22.1 Taxonomia

| Categoria | Exemplos PROVEN |
|---|---|
| DOMAIN_LOCAL + STREAM | Core `EventBus` → handlers → Socket.IO admin/RBAC notify |
| TECHNICAL_JOB / POLLING | outbox commercial/requests; schedulers C0.S0-D; Graph message-trace poll |
| NOTIFICATION | Core dispatch + Portal socket |
| WEBHOOK (outbound) | console alerts; Chat fine-tune train webhook |
| EXTERNAL_CALLBACK | Pulse `/device-ota/*` (device→API, token device) |
| USER_REQUEST | HTTP APIs; Chat tools |
| REAL_EVENT (provider push) | **NOT_PROVEN** |
| INBOUND WEBHOOK (provider) | **NOT_PROVEN** |

### 22.2 EventEnvelope / bus

```text
EventEnvelope compartilhado = TARGET_ONLY / NOT_PROVEN
Kafka/Rabbit/NATS/Redis Streams = NOT_PROVEN
Core EventBus = in-process dispatcher (não broker)
Outbox Postgres = DOMAIN_LOCAL TECHNICAL_JOB_BUFFER (notify), não EventEnvelope transport
```

### 22.3 Authenticity / replay

Inbound provider webhook authenticity: N/A (ausente).  
Outbound webhooks: sem assinatura evidenciada; debounce in-memory (console).  
Replay store / processed-event: **ABSENT** como plataforma.  
Dedupe: `PARTIAL` (`dedupeKey` notify; outbox row ids).

Não inventar event platform antes de Abstraction Gate.

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

## 26. Rule / Decision / BPM engines — C0.S0-H (parcial)

| Candidate | Status | Nota |
|---|---|---|
| Camunda / Zeebe / Temporal / Airflow BPM | `NOT_PROVEN` | |
| Domain state machines | `DOMAIN_LOCAL` | ex. Transformômetro `MinuteStatusTransitionService`; Capex/request status enums |
| BPMN UI / Mermaid / FlowchartEditor | `DOCUMENTATION` / editor | `@delpi/plugin-ui` BPMN + Transformômetro React Flow — **≠** executable BPM engine |
| Shared Decision/Rule engine | `NOT_PROVEN` | regras permanecem na Domain API dona |

## 27. Business postcondition / Outcome sources — C0.S0-D amostra

Padrão atual: HTTP 2xx / Graph accepted / outbox `published` = sucesso **técnico**.  
Postcondition de negócio (invoice existe, destinatário leu) **não** é verificada de forma uniforme → `TO_INVENTORY BY DOMAIN`.  
Idempotência: `PROVEN` em requests-api `idempotency_keys`; `PARTIAL` via `dedupeKey` de notificação; `ABSENT` como contrato transversal.

## 28. Notification / Escalation channels — C0.S0-D

Portal in-app + Core dispatch: `PROVEN`.  
E-mail Graph: `PROVEN` como provider técnico (Core, api-delpi reports, atas TM/CIPA/CEC).  
Teams/WhatsApp Business como canal de execução: `NOT_PROVEN` (C0.S0-E).  
Escalation/SLA unificado: `TO_INVENTORY`.

## 29. Process Intelligence / Process Mining — C0.S0-H

### 29.1 Runtime status

| Capability | Status |
|---|---|
| Process Mining engine (pm4py/XES/OCEL/miners) | `NOT_PROVEN` / TARGET (`58`) |
| Algorithmic Process Discovery | `NOT_PROVEN` |
| Conformance vs reference process | `NOT_PROVEN` (validação Domain ≠ conformance mining) |
| Variant / bottleneck process analysis | `NOT_PROVEN` |
| Task Mining / desktop telemetry | `NOT_PROVEN` |
| Canonical ProcessEvent / EventLog contract | `NOT_PROVEN` (TARGET CP-250) |
| Shared EventEnvelope process projection | `NOT_PROVEN` (C0.S0-E) |

### 29.2 Candidate process evidence sources (amostra material)

| Source | Owner | Class | Case | Activity | Timestamp | Grain | Fitness |
|---|---|---|---|---|---|---|---|
| `my_requests.request_status_history` | requests-api | AUTHORITATIVE_DOMAIN_RECORD + history | `request_id` | `action` + from/to_status | `created_at` (persist) | one row per status transition | **PARTIAL** → candidate mining input |
| `my_requests.request_events` | requests-api | DOMAIN_EVENT | `request_id` | `event_type` | `created_at` | one row per domain event | **PARTIAL** |
| `my_requests.integration_outbox` | requests-api | OUTBOX | payload-linked | `event_type` | available/published | technical publish attempt | **NOT_READY** (tech grain) |
| `planejamento_orcamentario.capex_plan_history` | api-delpi/PO | AUTHORITATIVE history (append-only) | `plan_id` | `action` + status | `created_at` | one row per workflow action | **PARTIAL** |
| `invoice_issuance.invoice_issuance_history` | api-delpi | AUTHORITATIVE history | `request_id` | `event_type` + status | `created_at` | one row per transition | **PARTIAL** |
| `quality.audit_5s_nc_events` | api-delpi/quality | DOMAIN_EVENT | `nonconformity_id` (+ audit via FK) | `event_type` | `created_at` | one row per NC event | **PARTIAL**; OBJECT_CENTRIC_CANDIDATE (audit↔NC↔response) |
| `quality.quality_audit_log` | quality-action-plans | AUDIT_LOG | plan/entity ids | `event_type` | created | audit grain | **PARTIAL** / may mix audit≠process |
| Pulse `device_hardware_events` / readings | production-pulse-api | TELEMETRY / DEVICE | `device_id` | `event_type` | timestamps | device/telemetry | **NOT_READY** as human process case |
| Transformômetro process diagrams / decomposição / instances | transformometro-api | REFERENCE_MODEL / DOCUMENTATION | process/instance IDs | diagram nodes | model timestamps | design artifact | **NOT_READY** as executed event log |
| TM/CIPA meeting minute audit + status machine | TM/CIPA | DOMAIN_LOCAL lifecycle | `minute_id` | status transitions | created/updated | document workflow | **PARTIAL** |
| commercial/requests outboxes | Domain | OUTBOX | domain keys | event_type | publish times | integration | **NOT_READY** alone |
| Chat `chat_data_anomaly_detection` | Chat | DERIVED_RECORD | N/A | data anomaly types | turn time | API result anomalies | **OUT_OF_SCOPE** for process mining; ≠ fraud |

```text
PROCESS_MINING_READY (platform-complete) = NONE proven
PARTIAL domain histories = best future adapters (ADAPTER_REQUIRED)
Audit log ≠ process event log without case+activity+business time proof
```

### 29.3 Semantics summary

```text
case identity:        Domain-local (request_id, plan_id, NC id, minute_id) — no cross-service case contract
activity:             EXPLICIT in status/history action/event_type columns (Domain)
timestamp:            typically created_at of history row (= persist time); occurred_at business-distinct rarely proven → PARTIAL
ordering:             PARTIAL_ORDER via (case_id, created_at) / UUID; no shared sequence/version contract
dedupe:               Domain-local (outbox dedupe_key; history append-only Capex); no shared event_id process contract
lifecycle:            Domain-specific enums (request/capex/NC/minute) — do not normalize prematurely
cross-service corr.:  ABSENT / PARTIAL (business keys only; no causation_id platform)
retention:            TO_INVENTORY (no universal purge/TTL evidenced on these histories)
privacy:              actor_user_id/name often present → MINIMIZABLE for mining projections
```

### 29.4 Safety / authority

```text
Nonconformity (5S/quality) = process/quality fact — not employee guilt
Chat data anomaly = tool/result anomaly — not fraud fact
Process KPI Domain (OEE/delivery/etc.) = Domain derived metrics — not process-mining truth
Employment decision from process/task metrics = NOT_PROVEN
Prohibited human inference from traces = NOT_PROVEN
Process model / mining output = must not replace Domain authority (no AUTHORITY_DRIFT found)
Task Mining screen/keyboard/desktop agent = NOT_PROVEN
```

### 29.5 Reuse classification (candidates only)

| Mechanism | Classification |
|---|---|
| Domain status/history tables | `ADAPTER_REQUIRED` (export/projection) |
| Transformômetro BPMN-lite diagrams | `REFERENCE_MODEL` / `OUT_OF_SCOPE` as mining log |
| plugin-ui BPMN components | `NEUTRAL_SHARED_REUSE` for documentation UX only |
| Process Mining engine | `COPILOT_IMPLEMENT_NEW` / TARGET |
| ProcessEvent shared contract | `EXTEND_PLATFORM_CONTRACT` / ADR_REQUIRED when prioritized |
| Task Mining | `NOT_PROVEN` / TARGET with privacy gate |

## 30. AI Control Tower / model governance — C0.S0-I

### 30.1 Control Tower physical status

| Item | Status |
|---|---|
| DÉLIA AI Control Tower runtime | `NOT_PROVEN` / TARGET (`59`) |
| Platform AI Asset Registry | `NOT_PROVEN` (CP-257 TARGET) |
| Platform Model Registry | `NOT_PROVEN` (CP-303 TARGET) |
| Chat Admin (metrics/settings/learning/FT) | `CHAT_ONLY` governance-like surface — **≠** Control Tower |
| Second planner via admin/metrics | `NOT_PROVEN` — Chat Admin does not replace Policy/Work planner |

```text
CONTROL TOWER != SECOND PLANNER (invariant; no counterexample)
Chat Admin observe/configure/enable flags ≠ business permission authority
```

### 30.2 Providers / models (physical)

| Provider / stack | Owner | Class | Config |
|---|---|---|---|
| `openai_compatible` (default Kimi/OpenRouter via `KIMI_*` / `LLM_TEXT_*`) | minha-delpi-ai-api | `CHAT_ONLY` | env `LLM_PROVIDER` + model env |
| `ollama` | Chat | `CHAT_ONLY` | env explicit only — **not** automatic fallback |
| Vision LLM (`VISION_LLM_*`, inherits text provider) | Chat | `CHAT_ONLY` | env |
| Embeddings (`EMBEDDING_PROVIDER`) | Chat | `CHAT_ONLY` | env; local tag may force keyword RAG |
| Transformômetro `KimiLlmGateway` (atas) | transformometro-api | `DOMAIN_LOCAL` | `KIMI_*` settings; hardcoded SYSTEM_PROMPT in gateway |
| Anthropic / Gemini / Azure OpenAI first-class | — | `NOT_PROVEN` as primary runtime | |
| DÉLIA model invocation | — | `NOT_PROVEN` | no DÉLIA runtime |

Model version semantics (Chat/TM): **ENV_CONFIGURED** / alias strings (e.g. `moonshotai/kimi-k3`, `qwen2.5:3b`) — changeable without code; not a governed ModelVersion registry.

### 30.3 Routing / fallback

| Mechanism | Status | Nota |
|---|---|---|
| Chat `provider_registry` → ollama \| openai_compatible | `CHAT_ONLY` | factory selection by env |
| Agent-level provider override | `CHAT_ONLY` | documented; turn-scoped |
| `CHAT_LLM_LATENCY_PROFILE` | `CHAT_ONLY` | token/ctx presets — not DÉLIA FAST/OPERATIONAL/REASONING |
| `CHAT_FAST_PATH` / `CHAT_OPERATIONAL_FAST_PATH` | `CHAT_ONLY` | deterministic Chat paths before/around LLM |
| DÉLIA decision-path FAST\|OPERATIONAL\|REASONING (CP-232) | `TARGET` / `NOT_PROVEN` runtime | |
| Automatic provider fallback (e.g. OpenRouter→Ollama) | `ABSENT` (Chat docs: Ollama not fallback) | |
| Domain TM Kimi timeout/error | `DOMAIN_LOCAL` | HTTP gateway errors; no multi-provider chain |

Routing does **not** grant Core/Domain AuthZ (no AUTHORITY_DRIFT found).

### 30.4 Prompts / structured output / tools

| Asset | Status |
|---|---|
| Chat `app/content/pt-BR/assistant/*.json` | `CHAT_ONLY` content layer; git-versioned |
| Hardcoded SYSTEM_PROMPT (TM Kimi gateway) | `DOMAIN_LOCAL` |
| Formal PromptAsset registry / approval workflow | `ABSENT` / TARGET |
| Structured JSON / Pydantic / tool schemas | `CHAT_ONLY` PARTIAL–PROVEN; TM JSON sections PROVEN |
| Tool metadata alone authorizes ACT | `NO` — Chat tools still require AuthZ/policy (reference) |
| Model output grants RBAC/permission | `NO` — no counterexample |

Provider SDK: Chat infra gateways behind ports; TM gateway in infrastructure. Domain TM application uses gateway via composition — **BOUNDARY_OK** for sampled paths. DÉLIA Domain N/A (no runtime).

### 30.5 Evals / telemetry / cost / kill-switch

| Item | Status |
|---|---|
| Chat R1–R11 / intelligence baselines / evidence JSON | `CHAT_ONLY`; many runs record `gitSha` + dataset hash → **PARTIAL**–**STRONG** for Chat programs; ≠ DÉLIA PASS |
| Eval ↔ model ID always bound | `PARTIAL` (offline often `model: n/a`) |
| Production proof from offline green alone | rejected — `eval green != production proof` |
| Admin metrics (latency, audit counts, provider/model labels) | `CHAT_ONLY` PARTIAL telemetry |
| `LlmCostEstimatorService` + admin cost table | `CHAT_ONLY` estimated cost; not org financial budget |
| Latency SLO FAST/OPERATIONAL/REASONING (DÉLIA) | `NOT_PROVEN` |
| Kill-switch / disable | `PARTIAL` Chat: `CHAT_*_ENABLED`, provider `enabled`, vision flags; no platform Control Tower kill matrix |
| Circuit breaker model-specific | `TO_INVENTORY` / mostly HTTP timeouts |

### 30.6 Fine-tuning / datasets

| Item | Status |
|---|---|
| Chat fine-tuning (Ollama create / export_only JSONL) | `CHAT_ONLY` |
| Train webhook optional | `CHAT_ONLY` |
| Platform MLOps / model artifact registry | `NOT_PROVEN` (CP-302 residual) |
| Knowledge corpus ≠ model weights | preserved (RAG/content separate from LLM gateway) |

### 30.7 Reuse classification (candidates only)

| Mechanism | Classification |
|---|---|
| Chat LLM gateway ports / provider_registry | `REFERENCE_ONLY` / `DO_NOT_REUSE` as DÉLIA runtime; possible `ADAPTER_REQUIRED` pattern study |
| Chat Admin metrics/cost | `OUT_OF_SCOPE` as Control Tower |
| TM Kimi gateway | `DOMAIN_LOCAL` |
| Control Tower / ModelRegistry / PromptAsset | `COPILOT_IMPLEMENT_NEW` + `ADR_REQUIRED` |
| FAST/OPERATIONAL/REASONING | `TARGET` (CP-232) |

## 31. MCP / A2A / Agent interoperability — C0.S0-R

### 31.1 Physical status

| Capability | Status | Evidence |
|---|---|---|
| MCP server/client runtime | `NOT_PROVEN` | zero `@modelcontextprotocol` / `mcp` SDK deps; no `mcp.json`; no stdio/SSE/HTTP MCP transport impl |
| A2A agent protocol / Agent Card runtime | `NOT_PROVEN` | no Agent Card endpoint / A2A client/server; CSS/onboarding “agent card” = Chat UI only |
| MCP/A2A shared contracts (`AgentRef`, `Delegation`, `ToolCall`) | `DOCUMENTATION_ONLY` / `TARGET` | `60`, `21` §23 candidates; no runtime tables/APIs |
| Chat OpenAPI Action Catalog + HTTP gateway | `CHAT_ONLY` **≠ MCP** | `OpenApiActionImporter` → Postgres catalog → `execute_external_action` |
| Chat native OpenAI function-calling | `CHAT_ONLY` **≠ MCP** | `openai_compatible_llm_gateway.generate_with_tools` |
| GPT Actions (TM/TV) | `DOMAIN_LOCAL` **≠ MCP** | OpenAPI 3 Custom GPT façades + JWT/RBAC |
| Agent identity / `on_behalf_of` / `delegated_by` | `NOT_PROVEN` | Chat forwards user Bearer; no agent delegation token model |
| Agent registry / Control Tower MCP lifecycle | `NOT_PROVEN` / TARGET (CP-266) | Control Tower still NOT_PROVEN (I) |
| Capability Marketplace MCP/A2A packs | `NOT_PROVEN` / TARGET (CP-305) | Marketplace NOT_PROVEN (O) |
| Automation Hub as MCP executor | `NOT_PROVEN` | Hub physical still NOT_PROVEN (D); boundary `BOUNDARY_OK` (no overlap proven) |

```text
MCP TOOL != AUTHORIZATION
A2A AGENT != USER AUTHORITY
DELEGATION != PERMISSION ELEVATION
TOOL METADATA != POLICY
REMOTE AGENT CONTENT = UNTRUSTED
MCP/A2A != PLANNER
MCP/A2A != AUTOMATION HUB
DISCOVERABLE != AUTHORIZED
Chat Action Catalog != MCP
GPT Actions OpenAPI != MCP
```

### 31.2 Neighbor mechanisms (do not promote to MCP/A2A)

| Mechanism | Owner | Role | AuthZ |
|---|---|---|---|
| OpenAPI Action Catalog | Chat | import operations → allowlist by agent | Core tool permission + Domain Bearer |
| `ExternalProviderUrlPolicy` | Chat | SSRF PARTIAL on provider URLs | ≠ platform safe-fetch (F) |
| Write confirmation | Chat | product gate before write tools | Domain still final |
| GPT Actions OpenAPI | TM/TV Domain | Custom GPT façade | Domain JWT/RBAC |
| web_search adapters | Chat | read search | CHAT_ONLY |

### 31.3 Trust / write / privacy residuals

| Topic | Classification |
|---|---|
| MCP write tools / idempotency / postcondition | `NOT_APPLICABLE` (no MCP runtime) — gates remain LOCKED TARGET (CP-265) |
| Delegation ≤ delegator | `NOT_PROVEN` model; Chat pattern = user token forward (≤ user) when used |
| Remote content → Policy/RBAC | no MCP/A2A path; Chat treats external content as tool/LLM input (not system Policy) |
| Token audience reuse via MCP | `NOT_PROVEN` |
| Dynamic MCP server registration | `NOT_PROVEN` |
| Kill-switch / disable MCP integration | `NOT_PROVEN` (no integration); Chat provider disable = CHAT_ONLY |
| Human Task fallback for MCP failure | `NOT_PROVEN` / TARGET |
| Vendor lock Domain→MCP SDK | `ABSENT` (good) |

### 31.4 Reuse classification (candidates only)

| Mechanism | Classification |
|---|---|
| Chat OpenAPI Action Catalog | `REFERENCE_ONLY` / `DO_NOT_REUSE` as MCP |
| GPT Actions OpenAPI | `REFERENCE_ONLY` Domain façade ≠ MCP adapter |
| Future MCP/A2A adapters | `EXTEND_PLATFORM_CONTRACT` + `ADAPTER_REQUIRED` + `ADR_REQUIRED` when justified |
| AgentRef / Delegation contracts | `ABSTRACTION_CANDIDATE` only with real consumers + owner |
| Marketplace/Control Tower lifecycle | `COPILOT_IMPLEMENT_NEW` / TARGET (O/I) |

## 32. Personal Memory / Personalization — C0.S0-J

### 32.1 DÉLIA vs Chat vs Core

| Capability | Status |
|---|---|
| DÉLIA Personal Memory runtime / contract | `NOT_PROVEN` / TARGET (`61`, CP-268–273) |
| Chat durable user memory (`ai_memory_items`) | `CHAT_ONLY` PROVEN |
| Chat session memory (pins/context-items/response-format) | `CHAT_ONLY` SESSION_CONTEXT |
| Chat conversation/session history | `CHAT_ONLY` CHAT_HISTORY ≠ Personal Memory |
| Core `user_person_profiles` | `PROVEN` platform person profile (job/phone/photo) ≠ AI memory |
| Core notification preferences / favorites / consents | `PROVEN` DURABLE_PREFERENCE / consent flags |
| Semantic user profile / preference embeddings | `NOT_PROVEN` (Chat column `embedding` reserved; unused as active profile) |
| Business Graph / Semantic Layer ← Personal Memory | `NOT_PROVEN` authority effect |

```text
Chat user memory != DÉLIA Personal Memory
Core profile/favorites != approved AI memory
Personal Memory (any) != Core RBAC / Domain AuthZ / Decision Gate
```

### 32.2 Session vs durable taxonomy (amostra)

| Class | Owner | Storage | Notes |
|---|---|---|---|
| TRANSIENT_REQUEST | Chat turn | in-process | |
| SESSION_CONTEXT | Chat | session memory APIs (`/sessions/.../memory/*`) | pins, context-items |
| CHAT_HISTORY | Chat | `ai_chat_sessions` + messages | durable conversation; not PM contract |
| PERSONAL_MEMORY (Chat) | Chat | `ai_memory_items` | preference/profile/correction; `user_id` scoped; flags `CHAT_USER_MEMORY_*` |
| DURABLE_PROFILE | Core | `user_person_profiles` | HR-ish contacts/photo |
| DURABLE_PREFERENCE | Core | `user_notification_preferences`, favorites | UX/notification only |
| KNOWLEDGE_CANDIDATE | Chat | `ai_learning_candidates` | pending→review→promote vocabulary |
| DOMAIN_DATA | Domain APIs | domain DBs | business truth |

### 32.3 Chat memory mechanics (reference-only)

```text
write: SYSTEM_DERIVED from explicit preference/profile regex (ChatUserMemoryDurabilityService)
       + ChatLearningSafetyGuard; gated CHAT_USER_MEMORY_ENABLED/CAPTURE
read:  format_prompt_block_for → turn context (retrieved memory != authority)
index: optional RAG source_type=user_memory (CHAT_USER_MEMORY_RAG_INDEX)
admin: list memory items; session clear/delete pins
user privacy UX (inspect/correct/delete/disable PM): PARTIAL/TO_INVENTORY vs CP-271
retention/export formal policy: TO_INVENTORY
consent dedicated to memory: ABSENT (feature flags ≠ legal consent record)
failure: capture best-effort — does not break turn / does not elevate AuthZ
```

Isolation: lookups keyed by `user_id` (+ project) — **PARTIAL** evidence of isolation design; no cross-user test campaign executed (`TEST_NOT_RUN` penetration).

### 32.4 Preference / profile authority

| Mechanism | Can grant RBAC / Policy / ACT? |
|---|---|
| Core notification prefs / favorites | **NO** (delivery/UX) |
| Core person profile | **NO** (identity extension) |
| Chat user memory / session pins | **NO** (context/personalization only) |
| `/me/access-profile` | RBAC projection — **not** preference |

No AUTHORITY_DRIFT found equating preference/memory with permission.

### 32.5 Knowledge candidate lifecycle (Chat)

| Stage | Status |
|---|---|
| Capture learning candidate | `CHAT_ONLY` PROVEN (`ai_learning_candidates`) |
| Admin review approve/reject | `CHAT_ONLY` PROVEN |
| Promote → vocabulary term (+ eval gate) | `CHAT_ONLY` PARTIAL–PROVEN |
| Auto-promote to org Domain truth | `NOT_PROVEN` / blocked by design (CP-208 reference) |
| DÉLIA KnowledgeCandidate→publish | `TARGET` / `NOT_PROVEN` |

Published Chat glossary/vocabulary = **Chat knowledge context**, not Domain business SoT.

### 32.6 Privacy / training boundary

```text
Core consents: usage_tracking / birthday — PARTIAL platform consent (≠ memory purpose)
Fine-tune export (Chat feedback/JSONL): CHAT_ONLY; memory != training consent
Prohibited sensitive inference as persistent profile: NOT_PROVEN
Secret/token in memory stores: NOT_PROVEN intentional path
```

### 32.7 Reuse classification (candidates only)

| Mechanism | Classification |
|---|---|
| Chat `ai_memory_items` / learning candidates | `DO_NOT_REUSE` as DÉLIA runtime; pattern study only |
| Core prefs/profile/consents | `PLATFORM_REUSE` for identity/notification facts; **not** AI memory |
| DÉLIA PersonalMemory / KnowledgeCandidate contracts | `COPILOT_IMPLEMENT_NEW` + `ADR_REQUIRED` |

## 33. Semantic Business Layer / Business Graph — C0.S0-K

### 33.1 Physical status

| Capability | Status |
|---|---|
| DÉLIA Semantic Business Layer / MetricDefinition registry | `NOT_PROVEN` / TARGET (`62`, CP-274–279) |
| Shared Semantic Query API | `NOT_PROVEN` |
| DELPI Business Graph runtime (Neo4j/graph DB/EntityRef+RelationshipRef store) | `NOT_PROVEN` / TARGET (`35`, CP-090) |
| Shared `EntityRef` / `WorkspaceContext` platform contract | `TARGET` / `PLANNED` (CP-091/159); Pulse local `AdminEntityRef` ≠ platform EntityRef |
| Domain KPI/report endpoints (api-delpi production/commercial/supplies/…) | `DOMAIN_LOCAL` PROVEN derived metrics |
| UI metric label catalogs (ex. commercial `overviewMetricsCatalog`) | `DOMAIN_LOCAL` presentation — **≠** MetricDefinition |
| Chat `ai_vocabulary_terms` / glossary RAG | `CHAT_ONLY` routing/normalization glossary — **≠** business semantic catalog |
| Plugin help glossaries (ex. supplies) | `DOMAIN_LOCAL` / DOCUMENTATION UX |
| Power BI / warehouse semantic model as platform SoT | `NOT_PROVEN` in-repo (TV may iframe external Power BI) |

```text
Semantic Layer != Domain SoT
Business Graph != Domain DB
UI KPI catalog != MetricDefinition
Chat glossary != business glossary
materialized KPI cache != authority
```

### 33.2 Entities / identity (amostra)

| Concept | Owner | ID semantics | Canonical status |
|---|---|---|---|
| User / permissions | Core + Keycloak | UUID / Keycloak sub | PLATFORM_CANONICAL identity |
| Branch/filial | multi-Domain + TOTVS | filial codes | DOMAIN_LOCAL / shared convention |
| Request / Capex plan / Invoice request / NC | Domain APIs | UUID domain-local | DOMAIN_CANONICAL per context |
| Product / OP / stock (TOTVS-backed) | api-delpi | ERP natural keys | DOMAIN_CANONICAL via ERP |
| Pulse device | production-pulse-api | UUID + controller_code | DOMAIN_LOCAL |
| Cross-domain EntityRef | — | — | `NOT_PROVEN` shared |

Cross-service identity: **DOMAIN_LOCAL** / **PARTIAL** (business keys); no stable shared EntityRef registry.

### 33.3 Metrics / formulas / dimensions (amostra)

| Metric family | Owner | Formula locus | Grain / dims | Cache |
|---|---|---|---|---|
| OEE / appointments | api-delpi production | CODE + SQL/TOTVS | period, branch, machine… | `production_kpi_cache` materialization **≠** SoT |
| OTD / delivery | api-delpi / commercial | CODE + SQL | customer/period | cache used |
| ROL / closing rate / portfolio | commercial-api + api-delpi + MFE labels | CODE + SI methods; UI tooltips | unit/segment | Domain-local |
| Efficiency fabril | api-delpi | CODE | day/operator | Domain-local |
| Audit 5S / quality KPIs | quality Domain | CODE/Postgres | audit/branch | Domain-local |
| Chat admin learning KPIs | Chat | CODE | Chat-only | OUT_OF_SCOPE business |

Formula versioning: **git / code** — not MetricDefinition version with effective_date.  
Time semantics: mix of business period vs `created_at` — **PARTIAL**, Domain-specific.  
Units/currency: **PARTIAL** (often implicit in Domain).  
Unknown≠zero: Domain-specific; no shared semantic quality enum.

### 33.4 Catalogs / aliases / search

| Artifact | Class |
|---|---|
| OpenAPI / generated api-delpi catalog | TECHNICAL / API_CATALOG |
| Chat vocabulary + column synonyms | CHAT_ONLY synonym map |
| Commercial OVERVIEW_METRICS | DOMAIN_LOCAL UI catalog |
| Governed MetricDefinition/Glossary store | NOT_PROVEN |
| Semantic/vector search for business concepts | CHAT_ONLY RAG/glossary retrieval; similarity ≠ semantic truth |
| LLM dynamic formula invention as canonical | NOT_PROVEN as SoT (CP-276 forbids for material metrics) |

Alias ≠ permission: **NO AUTHORITY_DRIFT** found.

### 33.5 AuthZ / knowledge / memory / process boundaries

```text
Metric access: Core/Domain permissions on endpoints (e.g. KPI_SUPPLIES_ACCESS) — metadata ≠ AuthZ
Personal Memory → change formula/meaning: NO (C0.S0-J)
Process Intelligence → redefine semantics: NO (C0.S0-H; PI NOT_PROVEN)
Knowledge/Chat glossary → Domain rule: NO auto
Employment/sensitive trait metrics as semantic authority: NOT_PROVEN
```

### 33.6 Graph / materialization / governance

```text
Business Graph writes altering Domain/RBAC: N/A (graph NOT_PROVEN)
KPI cache/materialized rows: PROVEN Domain-local; refresh/staleness PARTIAL/TO_INVENTORY per endpoint
Semantic publication lifecycle (draft→approved→published): NOT_PROVEN platform
Definition conflict governance UX (CP-278): TARGET
```

### 33.7 Reuse classification (candidates only)

| Mechanism | Classification |
|---|---|
| Domain KPI use cases / SQL | `ADAPTER_REQUIRED` for future MetricDefinition projection |
| UI metric catalogs | `OUT_OF_SCOPE` as semantic registry |
| Chat vocabulary | `DO_NOT_REUSE` as business glossary |
| MetricDefinition / Semantic Query / Business Graph | `COPILOT_IMPLEMENT_NEW` + `ADR_REQUIRED` |
| EntityRef shared | `EXTEND_PLATFORM_CONTRACT` when C0 freezes |

## 34. Analysis Sandbox — C0.S0-L

### 34.1 Physical status

| Capability | Status |
|---|---|
| Governed Analysis Sandbox (CP-281 isolation) | `NOT_PROVEN` / TARGET (`63`) |
| Jupyter / notebook runtime product | `NOT_PROVEN` (dev/CI only if any) |
| User/LLM arbitrary Python `exec` sandbox | `NOT_PROVEN` |
| Chat “sandbox” admin simulate UI | `CHAT_ONLY` / DOCUMENTATION — **≠** execution sandbox |
| iframe `sandbox=` (TV presentation) | browser attribute — **≠** analysis sandbox |
| Chat OCR child process (`multiprocessing` + timeout) | `CHAT_ONLY` PARTIAL_SANDBOX (process spawn + tempfile; not full quota/network/secret isolation) |
| Chat attachment text extraction `subprocess` | `CHAT_ONLY` STATIC_INTERNAL_COMMAND + timeout |
| TV Power Query / AST transform evaluator | `DOMAIN_LOCAL` safe AST subset — deterministic analysis, not general code sandbox |
| api-delpi `POST /data/sql` | `DOMAIN_LOCAL` READ_ONLY_DYNAMIC_SQL (SELECT + permission `DATA_SQL_ACCESS` + table allowlist) — **≠** sandbox |
| CI/scripts `subprocess` | `CI_ONLY` / `OPS_ONLY` |
| Automation Hub execution plane | `NOT_PROVEN` (C0.S0-D); no overlap with missing sandbox |

```text
Python scripts in repo / OCR subprocess != governed Analysis Sandbox
SQL allowlisted Domain endpoint != sandbox
Sandbox != Automation Hub
```

### 34.2 Isolation / limits / egress / secrets

| Control | Evidence |
|---|---|
| Container/cgroup/seccomp sandbox product | `NOT_PROVEN` |
| Per-user/job workspace product | `NOT_PROVEN` |
| Resource quotas (CPU/RAM/disk product) | `NOT_PROVEN` (OCR timeout PARTIAL) |
| Package install at runtime (`pip`/`npm`) | `NOT_PROVEN` / image build-time only |
| Shared object store (S3/MinIO) platform | `NOT_PROVEN` |
| Network: Chat OCR/subprocess | inherits Chat process env → `SHARED_PROCESS_SECRETS` risk class for Chat host; not isolated sandbox |
| SSRF | Chat ExternalProviderUrlPolicy PARTIAL (C0.S0-F); not sandbox-specific |
| Generated/user code → ACT | `NOT_PROVEN` path for LLM-exec; Domain SQL is read-only |

## 35. Artifact generation / workspace — C0.S0-L

### 35.1 Infrastructure status

| Capability | Status |
|---|---|
| Shared Artifact Workspace service | `NOT_PROVEN` / TARGET (CP-283/284) |
| Domain file uploads/exports | `DOMAIN_LOCAL` PROVEN (many `*_UPLOAD_DIR` / Storage services) |
| Chat attachments + workspace file extract | `CHAT_ONLY` |
| TV media / deck packages | `DOMAIN_LOCAL` |
| Platform object storage | `NOT_PROVEN` (filesystem volumes per Compose rule) |

### 35.2 Generators / types (amostra)

| Generator | Owner | Types | Class |
|---|---|---|---|
| reportlab minute PDF | CIPA / CEC / Transformômetro | PDF | DOMAIN_LOCAL RUNTIME |
| openpyxl exports | api-delpi (Capex, stock, RNC 8D, returns…), CIPA SIPAT | XLSX | DOMAIN_LOCAL RUNTIME |
| Chat openpyxl/PDF text extract | Chat | parse only | CHAT_ONLY |
| TV media storage | tv-dashboard-api | image/video | DOMAIN_LOCAL |
| Pulse firmware artifacts | production-pulse-api | firmware blobs | DOMAIN_LOCAL |
| Zip packages (TV deck, TM backup, PAC evidence) | Domain | ZIP | DOMAIN_LOCAL; zip-slip controls **PARTIAL** / TO_INVENTORY |

### 35.3 AuthZ / trust / knowledge

```text
Artifact access: Domain JWT + resource AuthZ (paths must not be guessable-public for private files)
Artifact != Domain SoT; report/export is derived representation
Artifact != auto Organizational Knowledge
File content != Policy/RBAC (CP-088 reference for PDF/image)
Malware scanner (ClamAV etc.): NOT_PROVEN
MIME/size/extension validation: PARTIAL Domain-local (varies by upload service)
Retention/delete/version Artifact Workspace: TO_INVENTORY / Domain-specific
Email/share of artifacts: Domain-local ACT when present (Graph mail) — not Artifact Workspace
```

### 35.4 Reuse classification (candidates only)

| Mechanism | Classification |
|---|---|
| Domain PDF/XLSX generators + upload dirs | `ADAPTER_REQUIRED` / Domain-local |
| Chat OCR process isolation pattern | `REFERENCE_ONLY` / `DO_NOT_REUSE` as DÉLIA sandbox |
| Analysis Sandbox / Artifact Workspace | `COPILOT_IMPLEMENT_NEW` + `ADR_REQUIRED` |
| Object store platform | `NOT_PROVEN` / ADR if introduced |
| Overlap Automation Hub | `BOUNDARY_OK` today (neither physical Hub nor sandbox) |

## 36. Predictive / Prescriptive Intelligence — C0.S0-M

### 36.1 Predictive ML / engine status

| Capability | Status |
|---|---|
| Predictive Engine / Model Registry for forecasts | `NOT_PROVEN` / TARGET (`64`) |
| sklearn / xgboost / prophet / torch train artifacts | `NOT_PROVEN` (no deps/artifacts) |
| Torch CUDA cache (Chat OCR) | `CHAT_ONLY` — **≠** business prediction |
| Chat tabular “anomaly” (empty/negative/zero rules) | `CHAT_ONLY` DETERMINISTIC_RULE |
| Chat contextual recommendations | `CHAT_ONLY` RULE + LLM_REASONING — suggestion ≠ ACT |
| SI alert `recommendation` strings | `DOMAIN_LOCAL` RULE_BASED copy on IGD bands |
| OEE/efficiency outlier band (0–199%) | `DOMAIN_LOCAL` threshold — **≠** failure ML |
| Transformômetro ROI/payback/economia | `DOMAIN_LOCAL` DETERMINISTIC KPI from observed inputs |
| Commercial/weekly/OP/headcount “forecast” naming | `DOMAIN_LOCAL` fact aggregation / human input — **≠** predictive model |
| CRM commercial forecast routes | `TARGET` / removed backlog |
| Feature store / drift / calibration / MLflow | `NOT_PROVEN` |
| LLM availability | `CHAT_ONLY` (C0.S0-I) ≠ predictive capability |

```text
Prediction != FACT
Recommendation != authorization
LLM availability != predictive capability
KPI / threshold / named "forecast" != predictive ML
```

### 36.2 Simulation / optimization (prescriptive path)

| Capability | Status |
|---|---|
| OR-Tools / PuLP / Gurobi / CP-SAT | `NOT_PROVEN` |
| api-delpi product cost-impact simulation (GET) | `DOMAIN_LOCAL` PROVEN — arithmetic what-if; **SIMULATE ≠ APPLY** |
| Safety-stock stock projection | `DOMAIN_LOCAL` deterministic ledger projection |
| Transformômetro comparable scenarios + `activate_scenario` | `DOMAIN_LOCAL` — compare = sim; activate = **Domain APPLY** (revision write), not Twin |
| TM flowchart token “simulation” | `DOMAIN_LOCAL` structural graph check ≠ plant twin |
| Chat admin agent simulate | `CHAT_ONLY` / DEV |

### 36.3 Reuse classification (candidates only)

| Mechanism | Classification |
|---|---|
| Domain deterministic what-if / KPI | `ADAPTER_REQUIRED` / Domain-local |
| Chat anomaly/recommendation | `REFERENCE_ONLY` / `DO_NOT_REUSE` as DÉLIA Predictive |
| Predictive/Prescriptive engines | `COPILOT_IMPLEMENT_NEW` + `ADR_REQUIRED` |

## 37. Operational / Digital Twin — C0.S0-M

| Capability | Status |
|---|---|
| Operational / Digital Twin runtime | `NOT_PROVEN` / TARGET (`64`) |
| Twin as source of truth | **forbidden** by authorities; no runtime counterexample |
| MES / historian / plant model adapters | `NOT_PROVEN` |
| Business Graph / Semantic Layer as Twin | **separated** — both NOT_PROVEN (C0.S0-K); ≠ Twin |
| Control Tower as Twin/planner | Tower NOT_PROVEN (C0.S0-I); Twin ≠ planner |
| Pulse ESP HTTP telemetry + device commands | `DOMAIN_LOCAL` device state — **≠** Operational Twin |
| Pulse Modbus/PLC/OPC UA | `NOT_PROVEN` (driver stub/tests only) |
| AI/LLM/Vision → machine command | `NOT_PROVEN` (and forbidden) |
| Twin write-back to Domain/OT | `NOT_PROVEN` |
| Edge Twin / offline prediction | `NOT_PROVEN` (C0.S0-G residual) |

```text
Twin != source of truth
Twin state != Domain state
Business Graph != Operational Twin
Edge != increased authority
DÉLIA != safety controller
Pulse HTTP command != OT/PLC safety override
```

## 38. Edge / Offline Industrial — C0.S0-N

### 38.1 Edge runtime / offline

| Capability | Status |
|---|---|
| Governed Edge runtime / Edge agent / MDM | `NOT_PROVEN` / TARGET (`65`) |
| Pulse BFF poll → ESP HTTP | `DOMAIN_LOCAL` PROVEN — **≠** Edge agent |
| ESP firmware local count/HTTP | `DEVICE_FIRMWARE` DOMAIN_LOCAL |
| Store-and-forward / EventEnvelope buffer | `NOT_PROVEN` |
| Wi‑Fi reconnect backoff on chip | `PROVEN` connectivity only |
| Offline permission cache / OFFLINE_BOUNDED_ACTIONS | `NOT_PROVEN` |
| Offline AuthZ expansion | **NOT_PROVEN** — invariant holds (`EDGE != INCREASED AUTHORITY`) |
| Pulse `offline` / `last_seen` | `DOMAIN_LOCAL` telemetry; UI disables operator pad when offline |
| Shared-device / kiosk MDM sessions | `NOT_PROVEN` (operator JWT surface PROVEN) |
| Edge inference (ONNX/TFLite/local LLM) | `NOT_PROVEN` |
| Factory network OT zoning / firewall | `NOT_PROVEN` (Compose LAN reach PARTIAL; docs VLAN) |
| Time sync / GPU-NPU / procedure offline cache | `TO_INVENTORY` / TARGET residual |

```text
CENTRAL UNAVAILABLE != PERMISSION EXPANSION
device offline status != authorization
Pulse BFF != governed Edge platform
```

### 38.2 Device identity / OTA / commands (Pulse — residual deepen)

| Topic | Evidence |
|---|---|
| Device AuthN | `X-Device-Token` / `device_api_token` — DEVICE_AUTHENTICATION only (`/device-ota/*`) |
| User AuthZ | Keycloak JWT + Pulse permissions + branch — **≠** device token |
| Provisioning | create/enable/disable/soft-delete PROVEN; MDM/PKI NOT_PROVEN |
| OTA | catalog SHA-256 PROVEN; artifact token TTL PROVEN; crypto signature + on-device verify **NOT_PROVEN** |
| OTA AuthZ ≠ generic command | PROVEN (device token OTA channel; JWT for commands) |
| Commands | increment/decrement/reset/set/configure/reboot/factory_reset — JWT; audit `device_commands` |
| Idempotency keys | ABSENT on HTTP command path; OTA reports PARTIAL idempotent |
| Postcondition | HTTP ack + counter readback PARTIAL; ack ≠ physical industrial outcome |
| Fail-closed | command unreachable → success=False; no fail-open AuthZ |
| Kill-switch | device `enabled=false` PROVEN; OT e-stop/interlock NOT_PROVEN |
| Secrets | token in Postgres; Wi‑Fi password not persisted; SECRET_PRESENT metadata only |

### 38.3 Reuse classification (candidates only)

| Mechanism | Classification |
|---|---|
| Pulse HTTP IoT counter/gauge | `ADAPTER_REQUIRED` / Domain-local |
| ESP firmware | `OUT_OF_SCOPE` for DÉLIA ownership |
| Edge/Offline DÉLIA runtime | `COPILOT_IMPLEMENT_NEW` + `ADR_REQUIRED` when prioritized |
| Automation Hub overlap | `BOUNDARY_OK` (Hub NOT_PROVEN; Pulse Domain-local) |

## 39. AI Model Lifecycle / MLOps — C0.S0-O

### 39.1 Lifecycle / registry / MLOps

| Capability | Status |
|---|---|
| Platform Model Registry (CP-303) | `NOT_PROVEN` / TARGET (`66`) |
| Platform MLOps (MLflow/Kubeflow/SageMaker/W&B/DVC) | `NOT_PROVEN` |
| Model weight/ONNX/GGUF artifact store | `NOT_PROVEN` |
| Chat model identity | `CHAT_ONLY` ENV alias strings (`LLM_*` / Ollama tags) — **≠** ModelVersion registry |
| Chat fine-tuning datasets/runs/deploy | `CHAT_ONLY` (Ollama create / export_only); provenance PARTIAL (no gitSha column) |
| Chat R1–R11 evals + evidence `gitSha`/datasetHash | `CHAT_ONLY` PARTIAL–STRONG for Chat programs; **≠** promotion gate formal |
| Chat learning promotion gate | `CHAT_ONLY` vocabulary/candidates — **≠** model DRAFT→DEPLOYED |
| Provider enable / `CHAT_*_ENABLED` kill flags | `CHAT_ONLY` / ENV_ONLY PARTIAL |
| Automatic multi-provider fallback | `ABSENT` (Chat) |
| Drift / calibration monitoring | `NOT_PROVEN` |
| Predictive training runtime | `NOT_PROVEN` (C0.S0-M unchanged) |
| Edge model distribution | `NOT_PROVEN` (C0.S0-N unchanged) |
| Control Tower | `NOT_PROVEN` (C0.S0-I unchanged); Chat Admin ≠ Tower |

```text
MODEL DEPLOYMENT != BUSINESS AUTHORIZATION
eval green != production proof
Chat FT/Admin != platform MLOps / Control Tower
Model Registry != business source of truth
```

### 39.2 Reuse (candidates only)

| Mechanism | Classification |
|---|---|
| Chat provider_registry / FT / R1–R11 | `REFERENCE_ONLY` / `DO_NOT_REUSE` as DÉLIA MLOps |
| Model Registry / MLOps platform | `COPILOT_IMPLEMENT_NEW` + `ADR_REQUIRED` |

## 40. Capability Marketplace / Supply Chain — C0.S0-O

### 40.1 Catalog vs Marketplace

| Mechanism | Class | Role |
|---|---|---|
| Capability Marketplace product (CP-305) | `NOT_PROVEN` / TARGET (`66`) | publication/enable lifecycle |
| Portal/Core plugin manifests + `/me/apps` | `PLATFORM_SHARED` PROVEN | **catalog** discovery; `active` + JWT filter |
| Core register/unregister/activate/rollback plugin | `PLATFORM_SHARED` PROVEN | plugin lifecycle; checksum SHA-256 local |
| Plugin permission sync (definitions only) | `PLATFORM_SHARED` PROVEN | **≠** role grant |
| Chat Action Catalog / OpenAPI tools | `CHAT_ONLY` | tool discovery/planner input; `enabled` ≠ Domain AuthZ |
| MCP/A2A runtime | `NOT_PROVEN` / TARGET (C0.S0-R; was E residual) | Chat OpenAPI≠MCP; GPT Actions≠MCP |
| cosign / SBOM / container SCA workflows | `NOT_PROVEN` | architecture CI ≠ AI supply-chain |
| Pulse firmware SHA-256 | `DOMAIN_LOCAL` | ≠ model package signing |

```text
catalog = discovery/inventory
marketplace = publication/distribution/enablement (TARGET; absent)
capability available/installed/enabled != authorized
CAPABILITY CATALOG != PLANNER
MARKETPLACE INSTALL != PERMISSION
tool metadata != authority
```

### 40.2 Authority / supply-chain

| Check | Result |
|---|---|
| `plugin.active` / action `enabled` grants AuthZ? | **NO** — Core/Domain JWT+RBAC remains |
| Marketplace elevates permission (CP-310)? | runtime N/A; invariant preserved |
| Catalog is planner? | Action Catalog feeds Chat planner only; ≠ business Policy |
| Automation Hub overlap | `BOUNDARY_OK` (Hub NOT_PROVEN) |
| Dynamic Marketplace hot-install | `NOT_PROVEN`; Chat OpenAPI reimport = CHAT_ONLY |

### 40.3 Reuse (candidates only)

| Mechanism | Classification |
|---|---|
| Core plugin catalog + `/me/apps` | `PLATFORM_REUSE` / `EXTEND_PLATFORM_CONTRACT` candidate for discovery patterns |
| Chat Action Catalog | `DO_NOT_REUSE` as DÉLIA Marketplace |
| Capability Marketplace | `COPILOT_IMPLEMENT_NEW` + `ADR_REQUIRED` |

## 41. Personal vs organizational data / privacy — C0.S0-P

### 41.1 Data-class summary (structural; no PII values)

| Class | Kind | Owner | Scope | Notes |
|---|---|---|---|---|
| Identity / profile | PERSONAL | Core + Keycloak | USER | `/me`; Export/Anonymize/Delete use cases PARTIAL cascade |
| Core prefs / favorites / consents | PERSONAL | Core | USER | `user_consents` purposes: data_processing, analytics, ai_context, birthday, usage_tracking |
| Conversation | MIXED | Chat | USER/SESSION | `ai_chat_*`; retention CLI ~365d messages |
| Chat user memory | PERSONAL | Chat | USER | `ai_memory_items` — **≠** DÉLIA Personal Memory |
| DÉLIA Personal Memory | — | — | — | `NOT_PROVEN` / TARGET (`61`) |
| Domain business records | ORGANIZATIONAL (+ MIXED actors) | Domain APIs | BRANCH/DOMAIN | SoT |
| Uploads / Domain artifacts | MIXED | Chat/Domain | SESSION/DOMAIN | Chat session RAG ≠ org Knowledge publish |
| Pulse telemetry | ORGANIZATIONAL (+ TECHNICAL) | Pulse | BRANCH | rawRetentionDays ~90 |
| Process histories | ORGANIZATIONAL (+ MIXED) | Domain | DOMAIN | mining runtime NOT_PROVEN (H) |
| FT / eval datasets | MIXED→TECHNICAL | Chat | CHAT admin | CHAT_ONLY; anonymize flag PARTIAL |
| Embeddings | TECHNICAL | Chat | various | derived; not anonymous by default |
| Learning → vocabulary | ORGANIZATIONAL candidate | Chat | Chat-local | admin promote; **≠** Domain SoT |
| Logs / audit | MIXED | Core/Chat/Domain | various | redaction PARTIAL |
| Secrets / credentials | SECRET | Infra/services | SERVICE | env; vault NOT_PROVEN |

```text
PERSONAL DATA != PERSONAL MEMORY
ORGANIZATIONAL DATA != ORGANIZATIONAL KNOWLEDGE
DATA ACCESS != PERMISSION TO REUSE
LLM INPUT != TRAINING CONSENT
PROCESS DATA != EMPLOYEE SCORE
ARTIFACT != KNOWLEDGE
TENANT/BRANCH FILTER != universal multi-company residency
```

### 41.2 Consent / purpose / reuse

| Mechanism | Status |
|---|---|
| Core consent purposes | `PROVEN` (listed above) |
| Memory / training / embedding consent purpose | `ABSENT` (flags ≠ consent row) |
| `ai_context` consent | gates profile→Chat only — **≠** durable memory/FT |
| Chat memory → Org Knowledge auto | **DISPROVEN** (user-scoped RAG optional; promote is admin) |
| Artifact/session attach → Org Knowledge auto | **DISPROVEN** (`session_source` ≠ publish) |
| Service usage → training consent | **NO** evidenced auto path |
| Personal Memory → AuthZ | **NO** |

### 41.3 Retention / delete / export / isolation

| Topic | Evidence |
|---|---|
| Retention jobs/CLIs | Core/Chat/TM/SI/Pulse code **PROVEN**; prod schedule **TO_INVENTORY** |
| Cross-app erase cascade (Core→Chat) | **OWNER_GAP** / ABSENT |
| Core export/anonymize | `PROVEN` PARTIAL (Core-scoped) |
| Formal data residency gate | `NOT_PROVEN` |
| Cross-user/filial filters | design **PARTIAL PROVEN**; penetration `TEST_NOT_RUN` |
| Prompt/log minimization | **PARTIAL** (FT anonymize, web-search redact, audit redact) |

### 41.4 Human Observation / employment / biometric

| Check | Status |
|---|---|
| Biometric runtime | `NOT_PROVEN` (G unchanged) |
| Hidden productivity/employee AI score | `NOT_PROVEN` |
| Employment automation from observation | `NOT_PROVEN` |
| HR/KPI “desempenho” Domain | ORGANIZATIONAL KPI — **≠** prohibited people scoring |

### 41.5 Reuse classification (candidates only)

| Mechanism | Classification |
|---|---|
| Core consents/export/anonymize | `PLATFORM_REUSE` / `EXTEND_PLATFORM_CONTRACT` for identity privacy |
| Chat memory/learning/RAG | `REFERENCE_ONLY` / `DO_NOT_REUSE` as DÉLIA PM/Knowledge |
| Unified privacy/retention orchestration | `COPILOT_IMPLEMENT_NEW` + `ADR_REQUIRED` if DÉLIA requires cross-app erase |
| DataClassification shared contract | `ABSTRACTION_CANDIDATE` only if multiple owners need common purpose vocabulary |

## 42. Operational context / EntityRef / Workspace — C0.S0-Q

### 42.1 Shared contracts

| Capability | Status |
|---|---|
| Shared `OperationalContext` / `WorkspaceContext` runtime | `NOT_PROVEN` / TARGET (`05`, CP-159) |
| Shared cross-domain `EntityRef` (CP-091) | `NOT_PROVEN` / PLANNED |
| DÉLIA Workspace product | `NOT_PROVEN` |
| Artifact Workspace product | `NOT_PROVEN` / TARGET (L) |
| Pulse `AdminEntityRef` | `DOMAIN_LOCAL` UI hub — **≠** platform EntityRef |
| Chat `ChatWorkspaceContextService` / `TvWorkspaceContext` | `CHAT_ONLY` — **≠** product Workspace |

```text
CONTEXT != AUTHORIZATION
EntityRef != Domain SoT
Portal context != final Domain rule
selected branch != access
Workspace != Work / Memory / Knowledge / Sandbox
```

### 42.2 Portal / Core / Domain context

| Source | Publishes | Authority class |
|---|---|---|
| Keycloak JWT | `sub`, claims | IDENTITY |
| Core `GET /me` | user + **effective permissions** (direct-role ∪ group-role ± user overrides; superadmin = all registered codes) | PLATFORM identity + AuthZ **input** |
| Core `GET /me/apps` | apps + routes filtered by effective request-context permissions | NAVIGATION (≠ Domain AuthZ) |
| Core `GET /me/access-profile` | effective `PermissionResolver` projection | AuthZ projection — **ALIGNED** with `/me` request context since `633d10d2a` |
| Core `GET /me/routes` | **no current producer proven** | `STALE_LEGACY_REFERENCE`; current navigation = `/me/apps → apps[].routes` |
| Portal AppHost props | `getAccessToken`, apps/routes, permissions flags — **no global branch** | DISPLAY/NAVIGATION/IDENTITY |
| Domain URL/query (filial-01/02, `branch=`, Pulse `entity=`) | selected resource/branch | DOMAIN_REFERENCE CONTEXT |
| Domain AuthZ gates | `BranchAccessGate`, `FilialAccessScope`, Pulse `assert_branch_access` | AUTHORIZATION (server) |

### 42.3 Entity identity / Workspace / TOCTOU

| Topic | Evidence |
|---|---|
| Entity IDs | DOMAIN_LOCAL (OP, processo UUID, device UUID, order keys); PLATFORM user UUID |
| Alias mappings | DOMAIN_LOCAL (e.g. api-delpi OP item aliases; filial↔branch labels) |
| Shared EntityRef open protocol (CP-004/009) | NOT_PROVEN; deep-links = path/query DOMAIN_LOCAL |
| Branch switch AuthZ | server revalidation PROVEN pattern; client selection alone ≠ grant |
| RBAC cache residual | FastAPI `/me` cache TTL ~60s — PARTIAL freshness |
| Write TOCTOU | Domain rechecks branch/resource on write — PROVEN pattern |
| Session storage | UX prefs (theme/sidebar/filters); **no** OperationalContext persistence |
| Chat session | CHAT_ONLY conversation state |
| LLM context minimize | CHAT_ONLY PARTIAL (`CHAT_OPERATIONAL_SLIM_USER_CONTEXT`) |

### 42.4 Reuse classification (candidates only)

| Mechanism | Classification |
|---|---|
| Portal AppHost + Core `/me`/`/me/apps` | `PLATFORM_REUSE` host/nav |
| Domain branch gates + local IDs | `ADAPTER_REQUIRED` / Domain-local |
| Pulse AdminEntityRef / Chat workspace | `DO_NOT_REUSE` as shared EntityRef/Workspace |
| Shared EntityRef / WorkspaceContext | `EXTEND_PLATFORM_CONTRACT` + `ADR_REQUIRED` when C0 freezes (CP-091/159) |
| OperationalContext abstraction | `ABSTRACTION_CANDIDATE` only with ≥2 real consumers + owner |

## 43. Industrial/OT safety + approval matrix — C0.S0-S (N residual deepen)

### 43.1 Safety controller / interlocks / e-stop

| Interface | Status | Classificação |
|---|---|---|
| PLC / SCADA / OPC UA / Modbus runtime | `NOT_PROVEN` | catalog rejects non-`http_*`; docs TARGET only |
| MQTT industrial | `NOT_PROVEN` | rejected as invalid `protocolKind` in tests |
| CNC / robot / actuator APIs | `NOT_PROVEN` | work-center “CNC” label ≠ CNC interface |
| MES / historian / industrial TSDB | `NOT_PROVEN` | |
| Safety PLC / SIL / certified safety controller | `NOT_PROVEN` | |
| Independent interlock / e-stop / safe-state runtime | `NOT_PROVEN` | |
| Maintenance / local / key-switch override OT | `NOT_PROVEN` | |
| Pulse HTTP IoT counter/gauge commands | `DOMAIN_LOCAL` | bounded command enum + payload limits; JWT+RBAC; **OPERATIONAL_DEVICE_COMMAND** ≠ SAFETY_IMPACTING |
| Pulse device `enabled=false` | `DOMAIN_LOCAL` | operational disable / poll stop — **≠** industrial safety interlock |
| Vision/voice/LLM/Twin/prediction → machine | `NOT_PROVEN` | CP-178; no Chat→Pulse command wiring |
| Safety owner (expected) | OT / industrial | DÉLIA ≠ safety controller; Hub ≠ safety |
| Safety independence of cloud/LLM/DÉLIA/Hub | architecture intent `YES` | physical proof of factory interlocks **outside monorepo** / `NOT_PROVEN` in-repo |

```text
BUSINESS APPROVAL != SAFETY AUTHORIZATION
USER CONFIRMATION != SAFETY INTERLOCK
POLICY ALLOW != MACHINE SAFE
DOMAIN AUTHZ != SAFETY STATE
AUTOMATION HUB SUCCESS != SAFE PHYSICAL OUTCOME
DÉLIA DECISION != SAFETY DECISION
LLM/MODEL/VISION/VOICE != SAFETY CONTROLLER
HTTP 200 / ACK != physical industrial outcome
device disable != e-stop
kill-switch (software) != emergency stop
SAFETY INTERLOCK MUST REMAIN INDEPENDENT
```

### 43.2 Pulse command materiality (sample)

| Command class | Materiality | Postcondition | Notes |
|---|---|---|---|
| `increment`/`decrement`/`set`/`reset`/`configure` | OPERATIONAL_DEVICE_COMMAND | HTTP response + optional reading persist | Domain IoT UX |
| `reboot`/`factory_reset` | OPERATIONAL_DEVICE_COMMAND (device lifecycle) | ACK-ish; no industrial safety postcondition | still ≠ machine safety |
| gauge commands | empty catalog | — | |
| free-form LLM→command | NOT_PROVEN | — | forbidden (CP-178) |

Owner matrix (Pulse): business=Pulse Domain · AuthZ=Core permission codes + branch · executor=`DeviceCommandService`+HTTP driver · safety=N/A (no OT safety gate) · postcondition=driver HTTP parse (technical ≠ safety).

### 43.3 Approval matrix residual

| Mechanism | Status | Notes |
|---|---|---|
| Shared industrial approval matrix (CP-179) | `NOT_PROVEN` / TARGET | no cross-domain four-eyes for OT actuation |
| Shared ApprovalRequest/ApprovalDecision contracts | `DOCUMENTATION_ONLY` / TARGET | DÉLIA CP-018/107 |
| CAPEX / personnel plan approve | `DOMAIN_LOCAL` | segregação submit≠approve (`CapexApprovalForbiddenError`); version conflict; **≠** OT safety |
| Meeting minutes multi-sign | `DOMAIN_LOCAL` | signer list + invite TTL; signature ≠ industrial approval |
| Scheduling booking approve | `DOMAIN_LOCAL` | **self-approval allowed** (tests); expiry of pending bookings |
| Purchase request approval | `DOMAIN_LOCAL` map | TOTVS status mapped; monorepo does not decide approve |
| Chat write confirmation | `CHAT_ONLY` | UI_CONFIRMATION ≠ Domain AuthZ ≠ safety |
| Chat FT dataset `approved_by` | `CHAT_ONLY` | model-data governance ≠ OT |
| PREPARE vs ACT (DÉLIA) | TARGET | L3 PREPARE / L4 C5 / L5 C7 OFF default |
| Domain dry_run / Chat simulate | `DOMAIN_LOCAL` / `CHAT_ONLY` | ≠ physical ACT |
| Pulse command PREPARE stage | `NOT_PROVEN` | execute is immediate ACT under Domain AuthZ |

```text
approval != permission
permission != approval
business approval != safety authorization
Chat confirm != final AuthZ
DÉLIA Decision != human approver
Policy requires approval != approval granted
```

### 43.4 Autonomy / fail-safe / residual before industrial ACT

| Topic | Status |
|---|---|
| L5 OFF by default | LOCKED requirement (CP-246); runtime DÉLIA NOT_PROVEN |
| Industrial ACT extra gate (CP-179) | PLANNED; physical safety still NOT_PROVEN |
| C6 Watch | OBSERVE/ADVISE/PREPARE; no autonomous ACT |
| Kill-switch software | PARTIAL Domain/Chat flags; Control Tower kill NOT_PROVEN; ≠ e-stop |
| Fail-safe without cloud | architecture intent YES; factory proof NOT_PROVEN in-repo |
| Offline industrial write | NOT_PROVEN (N) |
| MCP/A2A bypass safety | NOT_PROVEN (R); forbidden by invariant |
| Override by approval/DÉLIA/Hub/LLM | NOT_PROVEN paths |

**Antes de qualquer industrial ACT futuro:** OT-owned safety gate + independent interlocks + bounded IndustrialCommand + live AuthZ + business approval se aplicável + authoritative physical postcondition + ADR/risk approval (CP-179). Não atribuir safety ownership à DÉLIA.

### 43.5 Reuse classification (candidates only)

| Mechanism | Classification |
|---|---|
| Pulse HTTP IoT commands / disable | `REFERENCE_ONLY` / `DO_NOT_REUSE` as OT safety |
| Domain Capex/personnel approval | `REFERENCE_ONLY` business four-eyes pattern; ≠ industrial matrix |
| Shared ApprovalPolicy / SafetyGate / IndustrialCommand | `ABSTRACTION_CANDIDATE` only with real OT systems + ≥2 consumers + OT owner |
| CP-179 safety gate | `EXTEND_PLATFORM_CONTRACT` + `ADR_REQUIRED` + industrial owner before any ACT |

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
CARRY_FORWARD Core AuthZ: list_user_ids_by_permission_code (no overrides); override-mutation cache hygiene; IamSyncService cleanup; Core suite health INCONCLUSIVE
consumers Domain API além da amostra FastAPI/api-delpi/transformometro
Gateway/Compose/storage/secrets/network readiness para DÉLIA (declaração ≠ processo running)
background identity/workers/events
Internet/OAuth/connectors/Teams residual (vault/ExternalConnection/safe-fetch platform)
Automation Hub/RPA executors (Hub still NOT_PROVEN)
media retention/consent class-specific (CP-157/175); corporate STT/TTS
Process Intelligence residual: retention/quality completeness per domain; EventLog contract (CP-250); cross-service case correlation
Control Tower / Model Registry / PromptAsset still TARGET; Chat Admin ≠ Tower; CP-256 inventory advanced not PASS
Model Lifecycle / MLOps still TARGET (CP-302 advanced not PASS); Chat FT/evals CHAT_ONLY; no MLflow/weight registry
Capability Marketplace still TARGET (CP-305); Core plugin catalogs PLATFORM_SHARED ≠ Marketplace; cosign/SBOM NOT_PROVEN; enabled≠AuthZ
Personal Memory DÉLIA still TARGET (CP-268); Chat memory CHAT_ONLY; retention/export/consent TO_INVENTORY
Personal vs org privacy inventory advanced (CP-157/175/268 related); unified erase/residency/memory-training consent still OWNER_GAP/TO_INVENTORY; employment/biometric NOT_PROVEN
Operational Context / shared EntityRef / Workspace still TARGET (CP-091/159); Portal+/me PLATFORM_LOCAL; Domain IDs DOMAIN_LOCAL; context≠AuthZ
MCP/A2A runtime still NOT_PROVEN (CP-262 inventory advanced not PASS); Chat OpenAPI≠MCP; GPT Actions≠MCP; adapters TARGET (CP-263–267)
Semantic Layer / Business Graph still TARGET (CP-274); Domain KPIs DOMAIN_LOCAL
Analysis Sandbox / Artifact Workspace still TARGET (CP-280)
Predictive Engine / Operational Twin still TARGET (CP-287)
Edge runtime / store-and-forward / MDM still TARGET gaps (CP-295); Pulse HTTP IoT DOMAIN_LOCAL
OT safety inventory advanced (CP-178/179); safety PLC/interlock/e-stop still NOT_PROVEN; Pulse IoT≠safety; Domain approvals≠OT matrix; factory interlocks outside monorepo
```

### PLANNED / TARGET

DÉLIA permanece `PLANNED / NOT_STARTED`; sua aplicação standalone, contracts e capabilities são target/plan até evidência válida para o SHA/config executado.

Inventários temáticos C0.S0-A–S estão consolidados em C0.S0-T (§46). Isso **não** marca `C0.S0 COMPLETE`, `CP PASS` nem `FOUNDATION_FREEZE`.

```text
C0.S0 = APPROVED
C0.S0_READINESS (historical T) = SUPERSEDED_BY_ACCEPTED_ARCHITECTURE_REVIEW
C0 = NOT_STARTED
C0.S1 = APPROVED
C0.S2 = APPROVED
C0.S3 = APPROVED
C0.S4 = APPROVED
C0.S5 = APPROVED
SHARED_REFERENCE_SEMANTICS = FROZEN_ACCEPTED
ARCHITECTURE_PERSISTENCE_PRIVACY_SAFETY = FROZEN_ACCEPTED
INTEGRATION_CONTRACTS = FROZEN_ACCEPTED
C0.S6 = APPROVED
RED_CONTRACT_CONFORMANCE_PRIVACY_SECURITY_HARNESS = FROZEN_ACCEPTED
C0.S7 = APPROVED
FOUNDATION_FREEZE = APPROVED
C1_AUTHORIZED = YES
C1_STARTED = YES
C1_EXECUTED = NO
NEXT = C1-T2 — JWT + CORE EFFECTIVE ACCESS INTEGRATION
RUNTIME_READINESS = NOT_PROVEN
PRODUCTION_READINESS = NOT_PROVEN
NEW_BEHAVIORAL_TESTS = TEST_NOT_RUN
FUTURE_C1_C7_GREEN_EVIDENCE_REQUIRED = YES
DÉLIA_RUNTIME_DIFF = delia-api skeleton + /health
NEW_RUNTIME_ABSTRACTIONS = NONE
CORE_EFFECTIVE_PERMISSIONS = ALIGNED since 633d10d2a
```

Nenhuma capability, integração ou foundation é promovida a `PASS` apenas por esta documentação.

## 46. C0.S0 residual consolidation / readiness — C0.S0-T

### 46.1 Program / runtime

| Item | Status |
|---|---|
| PROGRAM | `PLANNED / NOT_STARTED` (ledger) |
| C0 | `NOT_STARTED` |
| C0.S0 | `APPROVED` |
| C0.S1 | `APPROVED` |
| C0.S2 | `APPROVED` (`ARCHITECTURE_REVIEW_C0_S2`) |
| C0.S3_AUTHORIZED | `YES` |
| C0.S3 | `APPROVED` (`ARCHITECTURE_REVIEW_C0_S3`; `SHARED_REFERENCE_SEMANTICS=FROZEN_ACCEPTED`; ACCEPT_WITH_RESIDUAL) |
| C0.S4 | `APPROVED` (`ARCHITECTURE_REVIEW_C0_S4`; `ARCHITECTURE_PERSISTENCE_PRIVACY_SAFETY=FROZEN_ACCEPTED`; ACCEPT_WITH_RESIDUAL) |
| C0.S5 | `APPROVED` (`ARCHITECTURE_REVIEW_C0_S5`; `INTEGRATION_CONTRACTS=FROZEN_ACCEPTED`; ACCEPT_WITH_RESIDUAL) |
| C0.S6 | `APPROVED` (`RED_HARNESS=FROZEN_ACCEPTED` in `20`; `ARCHITECTURE_REVIEW_C0_S6`) |
| C0.S7 | `APPROVED` (`FOUNDATION_FREEZE_REVIEW`; `REVIEWED_HEAD=6e10029bcc281c4e0c3575448a1414a157cc3c44`; `VERDICT=APPROVE_WITH_NON_BLOCKING_RESIDUALS`) |
| FOUNDATION_FREEZE | `APPROVED` (does **not** prove runtime/GREEN/production) |
| C1_AUTHORIZED | `YES` |
| C1_STARTED | `NO` |
| C1_EXECUTED | `NO` |
| NEXT | `C1 — STANDALONE APPLICATION BOOTSTRAP` |
| DÉLIA_RUNTIME_DIFF | `NONE` (`minha-delpi-copilot/` = HISTORICAL docs placeholder only; targets = `delia-api/` + `plugins/delia/`) |
| Unauthorized TARGET→PROVEN promotion | NONE found |

### 46.2 A–S task matrix (summary)

| Task | Evidence HEAD | Status | Freshness | Material accepted facts | Residual families |
|---|---|---|---|---|---|
| A | implicit via initial `51` snapshot | PLAN_ONLY | SUPERSEDED_BY_B | initial baseline | no dedicated ledger event |
| B | `5deb7fc2c` | PLAN_ONLY | REVALIDATED | Portal/Core/Gateway anchors | `/me/routes` absent |
| C | `90730043c` inventory; AuthZ runtime reconciled `633d10d2a` | PLAN_ONLY | REVALIDATED | Keycloak+JWT; **effective** permissions via Resolver | CARRY_FORWARD list_user_ids / cache / suite |
| D | `566def330` | PLAN_ONLY | REVALIDATED | Hub NOT_PROVEN; Domain schedulers | Hub physical owner |
| E | `aa3d93eee` | PLAN_ONLY | REVALIDATED | Graph mail; EventEnvelope TARGET | broker/webhooks |
| F | `c6c9c8370` | PLAN_ONLY | REVALIDATED | env secrets; Chat SSRF PARTIAL | vault/ExternalConnection |
| G | `79378e481` | PLAN_ONLY | REVALIDATED | Pulse device DOMAIN_LOCAL | STT/biometric NOT_PROVEN |
| H | `79378e481` | PLAN_ONLY | REVALIDATED | Domain histories PARTIAL | mining NOT_PROVEN |
| I | `cd688f2ff` | PLAN_ONLY | REVALIDATED | Chat LLM CHAT_ONLY | Control Tower NOT_PROVEN |
| J | `792cc990c` | PLAN_ONLY | REVALIDATED | Chat memory ≠ DÉLIA PM | PM TARGET |
| K | `792cc990c` | PLAN_ONLY | REVALIDATED | Domain KPIs DOMAIN_LOCAL | Semantic/Graph TARGET |
| L | `d3851a532` | PLAN_ONLY | REVALIDATED | Domain uploads DOMAIN_LOCAL | sandbox TARGET |
| M | `8d9fa7967` | PLAN_ONLY | REVALIDATED | prediction≠FACT | Twin/engine TARGET |
| N | `6038ec5c8` | PLAN_ONLY | REVALIDATED | Edge NOT_PROVEN; Pulse IoT | MDM/offline |
| O | `6038ec5c8` | PLAN_ONLY | REVALIDATED | catalog≠Marketplace | Registry/MLOps |
| P | `6038ec5c8` | PLAN_ONLY | REVALIDATED | privacy classes | erase/residency OWNER_GAP |
| Q | `6038ec5c8` | PLAN_ONLY | REVALIDATED | context≠AuthZ; EntityRef NOT_PROVEN | freeze EntityRef |
| R | `10f874c84` | PLAN_ONLY | REVALIDATED | MCP/A2A NOT_PROVEN | adapters TARGET |
| S | `bcf23241e` | PLAN_ONLY | REVALIDATED | safety PLC NOT_PROVEN; approve≠safety | CP-179 factory |
| T | `f1cce79b8` | PLAN_ONLY | CURRENT | consolidation | readiness |

### 46.3 Drift audit (A–S accepted findings)

| Drift class | Consolidation |
|---|---|
| AUTHORITY_DRIFT | **NONE** |
| SECURITY_DRIFT | **NONE** as accepted architecture (gaps ≠ accepted fail-open) |
| PRIVACY_DRIFT | **NONE** |
| SAFETY_DRIFT | **NONE** |
| AUTOMATION_BOUNDARY_DRIFT | **NONE** |
| MODEL_GOVERNANCE_DRIFT | **NONE** |
| INTEROPERABILITY_DRIFT | **NONE** |
| DOCUMENTATION_DRIFT | **NONE current-state**; `/me/routes` old refs = `STALE_LEGACY_REFERENCE`; one-CP-per-A–T = `CLOSED_NONISSUE` |

### 46.4 Blocking vs deferred residuals

**BLOCKING_RESIDUALS (for C0.S0 architecture re-review) = NONE**

TARGET runtime absences are **DEFERRED_BY_PHASE** (`16`: C0.S0 = inventory; ownership freeze in C0.S1–S7).

| Residual family | Sources | Class | When |
|---|---|---|---|
| Effective permission dual-path (`authenticate` vs Resolver) | C | **RESOLVED** at `633d10d2a` — CLOSED_AS_NON_ISSUE for S0 ADR | request context aligned |
| `list_user_ids_by_permission_code` / override-cache / IamSync / Core suite | C | CARRY_FORWARD | not dual-path; keep explicit |
| `/me/routes` stale refs | B | STALE_LEGACY_REFERENCE | cleanup anytime; **do not recreate** |
| Automation Hub physical owner | D | DEFERRED_BY_PHASE | C0.S1 ADR |
| EventEnvelope / broker | E | DEFERRED_BY_PHASE | C0.S3–S5 |
| Vault / ExternalConnection / platform safe-fetch | F | DEFERRED_BY_PHASE | before external writes |
| Media retention / STT / biometrics | G/P | DEFERRED_BY_PHASE | capability introduction |
| Process Mining / EventLog | H | DEFERRED_BY_PHASE | C4–C6 |
| Control Tower / Registry / MLOps / Marketplace | I/O | DEFERRED_BY_PHASE | C6–C7 |
| DÉLIA PM / unified erase / residency | J/P | OWNER_GAP + DEFERRED | when PM introduced; erase C0.S4 |
| Semantic / Graph / EntityRef | K/Q | DEFERRED + candidates | C0.S3 |
| Sandbox / Artifact Workspace | L | DEFERRED_BY_PHASE | C4–C5 |
| Predictive / Twin / Edge | M/N | DEFERRED_BY_PHASE | C4/C7 |
| OperationalContext / Workspace | Q | DEFERRED_BY_PHASE | C2 |
| MCP/A2A adapters | R | DEFERRED_BY_PHASE | C3+ |
| OT safety PLC / industrial matrix | S | DEFERRED + invariant frozen | before industrial ACT |
| Domain APIs beyond samples | B/C | EVIDENCE_GAP NON_BLOCKING | expand as needed |
| One CP per A–T subbrief | A–T | CLOSED_AS_NON_ISSUE | thematic CPs + inventory linkage cover S0 |

### 46.5 Owner / SoT matrix (consolidation)

| Concept | Owner | SoT / status |
|---|---|---|
| Identity | Keycloak | PROVEN path |
| Platform RBAC | Core | PROVEN — effective permissions via PermissionResolver (`633d10d2a`) |
| Business rules/data | Domain APIs | PROVEN pattern |
| Portal | Portal | host/nav/context PROVEN |
| DÉLIA | TARGET standalone | NOT_PROVEN runtime |
| Automation Hub | TARGET technical execution | NOT_PROVEN physical |
| OT/safety | Industrial/OT | NOT_PROVEN in-repo; boundary frozen |
| Personal Memory | DÉLIA TARGET; Chat ≠ | Chat CHAT_ONLY |
| Knowledge | org governed TARGET | no auto-promotion proven |
| Business Graph / Semantic | TARGET projection | NOT_PROVEN |
| Model registry / Marketplace | TARGET | NOT_PROVEN; catalog≠Marketplace |
| EntityRef / OperationalContext / Workspace | TARGET | NOT_PROVEN shared |
| MCP/A2A | TARGET adapters | NOT_PROVEN |

### 46.6 Abstraction candidates (hygiene)

Keep as candidates only (no implement): ExternalConnection, EventEnvelope, EntityRef, OperationalContext, Workspace, MetricDefinition, PersonalMemory, KnowledgeCandidate, SandboxPort, ArtifactStore, Prediction/Recommendation/Scenario/Twin, ModelAsset, Capability/MarketplaceEntry, DataPurpose/RetentionPolicy, AgentRef/Delegation, SafetyGate, IndustrialCommand, ApprovalPolicy.

Drop premature: Chat Action Catalog as MCP; Pulse `AdminEntityRef` as platform EntityRef.

### 46.7 Readiness gate matrix

| Gate | Result | Evidence |
|---|---|---|
| authority | PASS | roles documented; no parallel accepted |
| ownership | PASS | boundaries clear; physical Hub/Tower deferred S1 |
| source of truth | PASS | Domain/Core/Keycloak proven; TARGET SoTs not invented |
| security | PASS | no accepted fail-open AuthZ |
| privacy | PASS | classes inventoried; no accepted drift |
| safety | PASS | CP-178/179 boundary frozen |
| contracts | PENDING | TARGET contracts deferred by phase OK for S0 |
| platform integration | PASS | Portal/Core/Gateway/auth inventoried |
| standalone boundary | PASS | Chat≠DÉLIA; copilot docs-only |
| testability | PENDING | mostly TEST_NOT_RUN; inventory-first per 16 |
| traceability | PASS | 25 §14 links thematic CPs to S0 inventory; CP rows remain PLANNED |
| documentation consistency | PASS | current Core AuthZ and `/me/routes` semantics reconciled; historical stale evidence explicitly superseded |

```text
C0.S0_READINESS = CANDIDATE_FOR_ARCHITECTURE_RE_REVIEW
```

Rationale: A–T inventory package present; Core request-context AuthZ reconciled to runtime (`633d10d2a`); `/me/routes` non-contract explicit; TARGET absences deferred; drifts NONE for dual AuthZ ADR. **Not** C0.S0 COMPLETE / FOUNDATION_FREEZE / C0.S1 unlocked.

**Not claimed (historical T package):** C0 COMPLETE · FOUNDATION_FREEZE · CP PASS.  
**Superseded claim:** “C0.S1 not authorized” / “C0.S0 not approved” — replaced by Architecture Review acceptance (see §45 / ledger §6.22). C0.S1 remains **candidate**, not accepted.

### 46.8 Architecture review package

```text
canonical_reconciliation_base = 68ea41d9b5aac6216b5ab531f7cdccc93d64c3bc
authorities = 16, 17, 20, 21, 25, 50, 51, 52, ledger, thematic 53–66 as cited
owner matrix = §46.5
SoT matrix = §46.5
CORE_AUTHZ = RESOLVED at 633d10d2a (request context; revalidated at current canonical branch)
/me/routes = no current producer proven; navigation via /me/apps[].routes; old refs STALE_LEGACY_REFERENCE
BLOCKING_RESIDUALS (for re-review of docs consistency) = NONE after reconciliation
CARRY_FORWARD / DEFERRED = §46.4 / §46.9
next = SUPERSEDED → ARCHITECTURE_REVIEW_C0_S1 (C0.S0 accepted; C0.S1 freeze candidate in C0.S1-T1)
```

### 46.9 Residual classification (post-reconciliation)

```text
RESOLVED_BY_RECONCILIATION
- stale Core dual-path request-context narrative
- stale /me vs /me/access-profile current-state divergence
- missing canonical A–T closeout
- missing final reconciliation/supersession evidence

CARRY_FORWARD
- list_user_ids_by_permission_code (no overrides)
- override mutation → cache invalidate
- IamSyncService cleanup
- Core suite health INCONCLUSIVE
- domain-specific contract gaps beyond S0

DEFERRED_BY_PHASE
- Automation Hub / Model Registry / MLOps / MCP/A2A / Marketplace
- Business Graph / Semantic Layer / Personal Memory / Workspace
- Sandbox / Artifact / Predictive / Twin / Edge / OT / Control Tower

CLOSED_NONISSUE
- absence of future TARGET runtime
- absence of physical shared Automation Hub today
- Chat not being DÉLIA runtime
- lack of one CP per A–T subbrief
```

## 47. C0.S1 naming freeze — factual vs planned

```text
FACTUAL (HEAD): delia-api/ ABSENT; plugins/delia/ ABSENT; gateway routes ABSENT; Compose services ABSENT
HISTORICAL: minha-delpi-copilot/ docs-only placeholder remains; not runtime
PLANNED/FROZEN_CANDIDATE: delia-api + plugins/delia + /apps/delia* + delpi-delia* (see 68)
≠ runtime proof; ≠ FOUNDATION_FREEZE; ≠ C0.S1 APPROVED
```
