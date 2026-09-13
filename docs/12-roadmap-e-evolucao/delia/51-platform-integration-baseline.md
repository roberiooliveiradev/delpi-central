# DÉLIA — Baseline de Integração com a Plataforma

**Status:** `CANONICAL_BASELINE` de evidências para integração  
**Escopo:** fatos `PROVEN` + gaps `TO_INVENTORY` + decisões `PLANNED` + arquitetura `TARGET`  
**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Evidence snapshot inicial desta revisão:** `dc1d96f787cca66116e328c32c5a9124d31664df`

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
| Core API repository | `PROVEN` | diretório raiz `core-api/` no snapshot | serviço/repositório existe | todos os endpoints/semânticas exigidos pela DÉLIA |
| Gateway repository | `PROVEN` | diretório raiz `gateway/` no snapshot | owner físico de gateway existe | rota/config final da DÉLIA |
| Infra repository | `PROVEN` | diretório raiz `infra/` no snapshot | infraestrutura versionada existe | storage/network/deploy adequados a cada capability futura |
| API DELPI repository | `PROVEN` | diretório raiz `api-delpi/` no snapshot | componente existe | manifesto/OpenAPI/ownership funcional específico sem inspeção adicional |
| APIs dedicadas | `PROVEN` | múltiplos diretórios de APIs no snapshot raiz | padrão de serviços independentes existe no monorepo | que uma estrutura específica seja automaticamente correta para a DÉLIA |
| DÉLIA runtime | `TO_INVENTORY` quanto a qualquer implementação; programa `PLANNED / NOT_STARTED` | ledger + placeholder documental | não há prova documental de runtime entregue | qualquer API/MFE/DB/deploy da DÉLIA |

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

Endpoints concretos e semantics Core necessários à DÉLIA permanecem `TO_INVENTORY` até C0.S0 seguir producer/consumer/contract reais.

## 5. Module Federation / plugin-ui — PROVEN no escopo atual

`plugins/vite/federation.shared.ts` comprova configuração compartilhada de federation, remote de `@delpi/plugin-ui`, React singleton e helpers atuais.

**TARGET:** MFE da DÉLIA reutiliza foundation neutra confirmada, sem source-import de Portal/Chat. Qualquer nova abstração compartilhada passa Abstraction Gate e exige 2+ consumers reais, owner, contrato pequeno e testes.

## 6. Core API — owner normativo; implementação detalhada TO_INVENTORY

`core-api/` existe no HEAD. Pelas autoridades oficiais, Core permanece owner de apps/rotas/RBAC/governança.

`C0.S0` deve provar:

```text
endpoints efetivamente usados
request/response/error contracts
operationIds/OpenAPI quando aplicável
permission resolution
service identity/background patterns
manifest/app registration
idempotency/audit where relevant
consumers reais
```

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

`gateway/` e `infra/` existem no HEAD. Rotas, Compose, network, secrets, storage, health, deployment e rollback específicos da DÉLIA permanecem `TO_INVENTORY` até C0/C1.

**PLANNED:** runtime da DÉLIA terá deploy/rollback próprios e nenhuma dependência operacional do Chat.

## 10. SSO/autorização DÉLIA — TARGET derivado das authorities, não runtime provado

```text
Keycloak
→ Portal/session context
→ DÉLIA MFE host contract
→ Gateway
→ DÉLIA API JWT validation
→ Core permission context
→ Domain API final business authorization
```

Background/service identity específico para continuous/autonomous operations é `TO_INVENTORY`.

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

## 12. Notifications / sockets / workers / schedulers — escopo misto

`PROVEN`: o Portal possui código de notifications/socket e o monorepo contém padrões de execução assíncrona em partes da plataforma.

`TO_INVENTORY`: owner transversal, broker/queue standard, durable workflow platform, scheduler governance, worker/service identity, delivery semantics e suitability para DÉLIA.

Nada disso prova, isoladamente, Event Bus corporativo, Automation Hub reutilizável, Process Mining platform ou AI Control Tower.

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

## 23. Automation / RPA / Automation Hub — TO_INVENTORY de implementação

A autoridade semântica já está definida:

```text
DÉLIA = inteligência + Policy + Decision + Work/orquestração + Outcome coordination
Automation Hub = execução técnica
```

O que C0 ainda precisa provar é **implementação física/owner técnico/contrato/reuse** do Automation Hub e executors existentes. Ausência de runtime comprovado não reabre a autoridade acima.

C0 mapeia:

```text
vendors/tools/licenses/orchestrators
bots/packages
desktop/web automations
queues/workers/heartbeats/leases
VDI/session environments
service accounts
credential injection
package/version/deploy/rollback
retry/idempotency
screenshots/artifacts/logs/retention
support/SLA/kill switches
```

Nenhum vendor é selecionado por suposição.

## 24. Scripts / Functions / Jobs — TO_INVENTORY

Mapear scheduled scripts/functions/cron/jobs/browser automations com owner, trigger, contract, credential model, authority, idempotency, observability e support. Script existente não vira executor da DÉLIA automaticamente.

## 25. Background execution / service identity — TO_INVENTORY

Provar queue/broker standard, worker lease/heartbeat, service identities, cancellation/draining, priority/concurrency e environment isolation. Worker identity != business actor.

## 26. Rule / Decision / BPM engines — TO_INVENTORY

Inventariar regras/engines/BPM/process validators existentes. Se readiness autoritativo já existir em Domain API, consumir contrato em vez de duplicar.

## 27. Business postcondition / Outcome sources — TO_INVENTORY BY DOMAIN

Mapear fonte autoritativa de verificação para invoice, maintenance request, message delivery, production report, records committed etc. Technical executor success != business completion.

## 28. Notification / Escalation channels — TO_INVENTORY além do Portal

Portal notifications são `PROVEN` no escopo de presença/uso client-side. Canais externos, owner/contracts, dedupe/ack/SLA/escalation permanecem `TO_INVENTORY`.

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
Portal AppHost/federated mount artifacts
Portal AuthContext Keycloak/Core client integration
shared federation/plugin-ui configuration artifact
presence of Core API, Gateway, Infra, api-delpi and multiple dedicated API repositories
```

### TO_INVENTORY antes de declarar reusable/runtime-ready

```text
contratos completos e consumers de Core/Domain APIs
Gateway/Compose/storage/secrets/network readiness para DÉLIA
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
