# Minha DELPI Copilot — Baseline de Integração com a Plataforma

**Status:** `CANONICAL_BASELINE` de evidências para integração  
**Escopo:** fatos comprovados + gaps `TO_INVENTORY` para capabilities `53–66`  
**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)

## 1. Objetivo

Separar **fatos já comprovados no repositório** de targets e itens `TO_INVENTORY`. Este arquivo não substitui C0.S0: tudo é revalidado no HEAD de execução.

## 2. Portal — PROVEN

Portal React/Vite funciona como Shell/Host. `AuthContext` integra Keycloak/Core, carrega usuário/apps/rotas e fornece `getAccessToken`.

## 3. AppHost / Module Federation — PROVEN

Portal suporta `embedded`, `external` e `federated`; federated resolve remote/share scope/mount + host props. Copilot MFE seguirá esse padrão.

## 4. AppLauncher / Core-driven menu — PROVEN

Apps/rotas vêm do Core/AuthContext. Não criar catálogo manual app→URL.

## 5. Manifest / plugin-ui — PROVEN

Manifest v2 e `@delpi/plugin-ui` são padrões compartilhados. Copilot terá manifesto próprio e reutilizará design system/federation.

## 6. Core API — PROVEN

Core segue Clean Architecture e permanece authority de users/context, apps/routes, RBAC/permissions, manifest registration e shared governance.

## 7. APIs dedicadas — PROVEN

Monorepo possui vários serviços independentes; Copilot API dedicada é coerente com a plataforma.

## 8. api-delpi / Domain APIs — PROVEN

`api-delpi` é backend-only e owner de integrações DELPI/TOTVS já expostas. Copilot consome contracts. Domain APIs permanecem business authorities e são preferidas como executor quando oferecem action contract adequado.

## 9. Gateway / Compose — PROVEN

Gateway roteia Core/apps por paths; Compose organiza serviços/profiles independentes. Copilot terá rotas/services próprios e nenhuma dependência operacional do Chat.

## 10. SSO/autorização alvo — DERIVED FROM PROVEN PLATFORM

```text
Keycloak
→ Portal token
→ Copilot MFE getAccessToken
→ Gateway
→ Copilot API JWT validation
→ Core context/RBAC
→ Domain API final authorization
```

Background/service identity específico para autonomous operations continua `TO_INVENTORY`.

## 11. OpenAPI Business Action integration — TARGET

```text
OpenAPI/contract
→ Copilot discovery/index
→ Capability Projection
→ planner
→ Policy/Decision
→ generic executor
```

No endpoint-specific planner teaching.

## 12. Existing notifications/events/rooms/workers — PARTIAL PROVEN / TO_INVENTORY

Core/Portal possuem notifications/socket patterns; alguns serviços possuem workers/schedulers; Portal Comercial expõe Interaction Rooms.

Isso **não prova** event bus, workflow platform, RPA orchestrator ou Control Tower transversal.

## 13. Copilot surfaces — TARGET

```text
GLOBAL
WORKSPACE
MEETING
FRONTLINE
FUTURE TEAMS SURFACE
BACKGROUND WATCH/WORKFLOW
ADMIN GOVERNANCE SURFACES
```

Mesmo Copilot API/policy/work runtime.

## 14. Media / Realtime — TO_INVENTORY

Não considerar comprovados: corporate STT/TTS/Vision provider, WebRTC/realtime standard, recording/transcription infra, media store, browser abstraction, quotas/cost/latency or retention policy.

## 15. Devices / Frontline — TO_INVENTORY

Não considerar comprovados: standardized tablets/kiosks, production-station mic/camera, device identity service, shared-terminal policy, factory network or production-terminal contracts.

## 16. Biometric Identity — TO_INVENTORY

Enrollment/photo/voice/template/liveness/providers/thresholds/governance owners ainda precisam evidence. Core identity remains authority regardless.

## 17. Internet Research / Egress — TO_INVENTORY

Approved search provider, shared search API, safe-fetch component, outbound proxy/allowlist, protected-destination blocking, malware/content policy, browser automation and research cache are not yet proven.

## 18. OAuth / Secret Management — TO_INVENTORY

Reusable OAuth callback framework, state/nonce/PKCE conventions, token vault, rotation/revocation, connection ownership/admin consent/provider scopes need evidence.

Credentials elsewhere are not automatically reusable.

## 19. Microsoft 365 / Teams — TO_INVENTORY IN REPO

Need factual evidence for Entra/Graph registrations, delegated/application/resource consent, Outlook/Teams/SharePoint/OneDrive integrations, messages/meetings/transcripts/recordings/change notifications, app/tab/bot and owners.

Raw realtime bot is not base requirement.

## 20. Google Workspace / Gmail — TO_INVENTORY IN REPO

Need evidence for OAuth app, Gmail/Calendar/Drive, scopes, push/PubSub, token lifecycle and owner.

## 21. WhatsApp / Other Connectors — TO_INVENTORY

Map official supported WhatsApp Business integration and Slack/GitHub/CRMs/service desks only with real evidence. Personal WhatsApp Web scraping is not target default.

## 22. Provider/domain events — TO_INVENTORY

Map event/webhook authenticity, EventEnvelope compatibility, dedupe/order, renewal/reconciliation, polling fallback, domain owners, replay/freshness. Do not invent event platform before gap proof.

## 23. Automation / RPA platform — TO_INVENTORY

No current baseline evidence is sufficient to claim a reusable corporate RPA Hub.

C0 maps:

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

No vendor selection by assumption.

## 24. Scripts / Functions / Jobs — TO_INVENTORY

Map scheduled scripts/functions/cron/jobs/browser automations with owner, trigger, contract, credential model, authority, idempotency, observability and support. Existing script is not automatically Copilot executor.

## 25. Background execution / service identity — TO_INVENTORY

Need evidence for queue/broker standard, worker lease/heartbeat, service identities, cancellation/draining, priority/concurrency and environment isolation.

Worker identity != business actor.

## 26. Rule / Decision / BPM engines — TO_INVENTORY

Search existing deterministic rules/engines/BPM/process validators. If authoritative readiness already exists in Domain API, consume it instead of rebuilding.

## 27. Business postcondition / Outcome sources — TO_INVENTORY BY DOMAIN

Map authoritative verification sources for invoice, maintenance request, message delivery, production report changes, records committed, etc. Technical executor success alone is insufficient.

## 28. Notification / Escalation channels — PARTIAL PROVEN / TO_INVENTORY

Core/Portal notifications partially proven. External channels depend on connectors. Need owner/contracts for dedupe/ack/SLA/escalation.

## 29. Process Intelligence / Process Mining — TO_INVENTORY

No current baseline proof of a transversal Process Mining platform.

C0 must map:

```text
event logs/audit trails
case/business keys
activity/timestamps/statuses
BPMN/process documentation
process owners
process KPIs
historical completeness/data quality
task-mining/desktop telemetry products
privacy/employee-monitoring policies
```

Do not infer that audit logs are sufficient for mining until case/activity semantics are proven.

## 30. AI Control Tower — TO_INVENTORY

No current baseline proof of a central AI Control Tower.

Map:

```text
AI/model/automation inventories
asset owners
risk/compliance classifications
eval registries
provider/model usage and cost telemetry
feature flags/kill switches
AI incidents/change management
dependency/deployment inventories
```

Existing dashboards do not automatically constitute Control Tower.

## 31. MCP / A2A / Agent interoperability — TO_INVENTORY

Need evidence for:

```text
MCP servers/clients
agent frameworks/protocols
tool registries
approved external agents
service/delegation identities
credential exchange/scoping
network boundaries
protocol versions/security policy
```

Market support for MCP/A2A != existing DELPI infrastructure.

## 32. Personal Memory / Personalization — TO_INVENTORY

Core user/profile/favorites may provide some facts, but C0 must map actual preference/recent-usage/memory-like stores, privacy/retention/delete/export owners, notification preferences and shared-device behavior.

No existing profile field is automatically approved as AI memory.

## 33. Semantic Business Layer — TO_INVENTORY

Need inventory of:

```text
Power BI/BI semantic models if any
KPI formulas in APIs/frontends/spreadsheets
business glossary
warehouse/lake/SQL definitions
metric/dimension owners
grain/freshness/security
conflicting definitions
```

Business Graph target does not prove a semantic metric layer exists.

## 34. Analysis Sandbox — TO_INVENTORY

Need evidence for Python/Jupyter/code execution, isolated containers, query engines, package policies, object/temp storage, file scanning, quotas, egress controls and reproducibility infrastructure.

Local developer Python availability is **not** production sandbox evidence.

## 35. Artifact generation/workspace — TO_INVENTORY

Need evidence for document/spreadsheet/presentation/PDF/chart generation, object storage, versioning/collaboration, comments/review, export/share and retention/ACL owners.

Existing file generation in isolated plugins is not yet a shared Artifact Workspace.

## 36. Predictive / Prescriptive Intelligence — TO_INVENTORY

Need factual inventory of forecasting/anomaly/classification/optimization models, datasets, ground truth, evals, model owners, deployment runtime and current analytical models.

No prediction capability should be inferred from generic LLM availability.

## 37. Operational / Digital Twin — TO_INVENTORY

Need evidence for simulation/twin tools, MES/IoT/historian state, capacity/planning models, solvers, scenario spreadsheets/models and state-update frequency.

Business Graph != Operational Twin.

## 38. Edge / Offline Industrial — TO_INVENTORY

Need evidence for:

```text
factory network reliability
Edge platforms/gateways
production PCs/tablets/kiosks
MDM/device management
GPU/NPU/CPU/local storage
local inference runtimes/models
time sync
procedure/drawing distribution
offline continuity requirements
OT segmentation/firewalls
```

Desktop PCs in factory do not automatically prove governed Edge runtime.

## 39. AI Model Lifecycle / MLOps — TO_INVENTORY

Need evidence for model providers/accounts, local ML models, model registry, CI/CD/deployment, datasets/eval suites, drift monitoring, rollback, provider/model ownership and Edge model distribution.

Model Router target does not prove governed model lifecycle infrastructure exists.

## 40. Capability Marketplace / Supply Chain — TO_INVENTORY

Need evidence for existing plugin/template/catalog mechanisms reusable for AI assets, package signing/integrity, dependency/license/vulnerability checks, publisher ownership and lifecycle.

Plugin manifest system is a useful reference but does not automatically equal AI Marketplace.

## 41. Personal vs organizational data / privacy — TO_INVENTORY

Need policies for delegated accounts, shared resources, personal memory, Process/Task Mining, artifacts, model datasets/evals, Edge caches, sandbox temp data, AI asset metadata and organizational Knowledge promotion.

## 42. Operational context — TO_INVENTORY BY DOMAIN

WorkspaceContext + EntityRef is target; C0 proves real owners/IDs/contracts for OP/operation/machine/workstation/product/revision/lot/material/tool.

## 43. Industrial/OT — TO_INVENTORY / NO-ACTUATION DEFAULT

Do not assume protocols/SCADA/MES/telemetry/command APIs/network reachability/safety architecture. Even if command interface exists, it does not authorize Copilot/Edge/RPA actuation.

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

**PROVEN platform foundations:**

```text
Keycloak → SSO
Core API → governance/RBAC/apps/routes
Portal → Shell/host/context/navigation
Gateway → routing
plugin-ui → design system
Module Federation → MFE integration
Domain APIs → business data/rules
Infra → deploy/network/storage foundations
```

**PARTIAL PROVEN:** notifications/socket/worker/scheduler patterns in parts of platform; they do not yet prove transversal event/automation/process/AI-governance foundations.

**NOT YET PROVEN for Copilot:** specific implementations for media/biometric/Internet/OAuth/connectors/Teams/RPA/event bus/background identity/Process Mining/Control Tower/MCP-A2A/Personal Memory/Semantic Layer/Sandbox/Artifact Workspace/Predictive/Twin/Edge/MLOps/Marketplace/OT privacy and safety.

Therefore C0.S0 must inventory and freeze all these boundaries before runtime implementation.
