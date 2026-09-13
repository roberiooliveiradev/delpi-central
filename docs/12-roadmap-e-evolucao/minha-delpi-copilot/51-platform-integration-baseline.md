# Minha DELPI Copilot — Baseline de Integração com a Plataforma

**Status:** `CANONICAL_BASELINE` de evidências para integração  
**Escopo:** Portal, Core API, Gateway, APIs, MFEs, plugin-ui, infraestrutura e gaps `TO_INVENTORY` para media/biometric/Internet/connectors/Teams/automation/RPA/Meeting/Frontline/OT  
**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)  
**Biometric/Human Observation:** [`54-biometric-identity-and-human-observation-governance.md`](./54-biometric-identity-and-human-observation-governance.md)  
**Internet/External Connectors:** [`55-internet-research-and-external-connectors.md`](./55-internet-research-and-external-connectors.md)  
**Microsoft Teams:** [`56-microsoft-teams-connector-and-meeting-integration.md`](./56-microsoft-teams-connector-and-meeting-integration.md)  
**Autonomous Operations/Execution Hub:** [`57-event-driven-autonomous-operations-and-automation-execution-hub.md`](./57-event-driven-autonomous-operations-and-automation-execution-hub.md)

## 1. Objetivo

Separar **fatos já comprovados no repositório** de itens ainda `TO_INVENTORY`. Este arquivo não substitui C0.S0: tudo é revalidado no HEAD de execução.

## 2. Portal — PROVEN

Portal React/Vite funciona como Shell/Host. `AuthContext` integra Keycloak/Core, carrega usuário/apps/rotas e fornece `getAccessToken`.

Consequência: Copilot não implementa login/RBAC no frontend.

## 3. AppHost / Module Federation — PROVEN

Portal suporta `embedded`, `external` e `federated`. Para federated resolve `remoteEntry`, share scope, módulo `mount()` e host props.

Decisão: Copilot MFE será `federated` e seguirá federation shared config existente.

## 4. AppLauncher / Core-driven menu — PROVEN

Apps/rotas vêm do Core/AuthContext. Não criar catálogo manual app→URL no Portal/Copilot.

## 5. Manifest / plugin-ui — PROVEN

Manifestos `microfrontend` e `@delpi/plugin-ui` já são padrões compartilhados. Copilot terá manifesto próprio e reutilizará design system/federation.

## 6. Core API — PROVEN

Core segue Clean Architecture e permanece authority de platform users/context, apps/routes, RBAC/permissions, manifest registration e shared notifications/presence/app usage quando aplicável.

## 7. APIs dedicadas — PROVEN

Monorepo possui `api-delpi`, `commercial-api`, `financial-api`, `customer-experience-api` e outros serviços independentes.

Decisão: Copilot API dedicada é coerente com o monorepo e seguirá Clean Architecture/Ports & Adapters.

## 8. api-delpi / Domain APIs — PROVEN

`api-delpi` é backend-only e owner de integrações DELPI/TOTVS já expostas. Copilot consome contracts; não copia regra/integration.

Domain APIs continuam business authorities e devem ser preferidas como executor quando oferecem action contract adequado.

## 9. Gateway / Compose — PROVEN

Gateway Nginx roteia `/core-api/` e `/apps/<service>/...`. Compose organiza serviços/profiles independentes.

Decisão: Copilot API/MFE terão rotas/services próprios e nenhuma dependência operacional do Chat.

## 10. SSO/autorização alvo — DERIVED FROM PROVEN PLATFORM

```text
Keycloak
→ Portal token
→ Copilot MFE getAccessToken
→ Gateway
→ Copilot API JWT validation
→ Core context/RBAC
→ Domain API final business authorization
```

Background/service identity model específico para autonomous operations ainda é `TO_INVENTORY`.

## 11. Domain Action integration — TARGET

```text
OpenAPI/contract
→ Copilot discovery/index
→ allowed capability projection
→ planner
→ generic adapter/executor
```

No endpoint-specific planner teaching. Quando action API oficial existe e atende reliability/authority, ela é preferida antes de RPA.

## 12. Existing events/notifications/rooms — PARTIAL PROVEN / TO_INVENTORY

Core/Portal possuem notifications/socket patterns; alguns serviços possuem workers/schedulers; Portal Comercial expõe Interaction Rooms.

C0 precisa mapear owner/contracts concretos antes de decidir reuse/extend/adapter/create para Event/Signal Plane, Watch delivery ou Automation Hub.

A existência de worker/scheduler isolado não prova um event bus/automation platform transversal.

## 13. Copilot surfaces — TARGET

```text
GLOBAL
WORKSPACE
MEETING
FRONTLINE
FUTURE TEAMS SURFACE
BACKGROUND WATCH/WORKFLOW
```

Mesmo Copilot API/work/policy runtime. Background execution não cria segundo Copilot.

## 14. Media/realtime — TO_INVENTORY

Não considerar comprovados sem C0: corporate STT/TTS/Vision provider, realtime/WebRTC standard, recording/transcription infra, media/object storage, browser media abstraction, quotas/cost/latency, raw-media retention e meeting-room hardware.

## 15. Devices/Frontline — TO_INVENTORY

Não considerar comprovados: tablets/kiosks standardized, mic/camera on production stations, device identity service, shared-terminal policy, factory network characteristics ou current production-terminal contract.

## 16. Biometric Identity — TO_INVENTORY

Não considerar comprovados: biometric enrollment process, approved photo/voice source, template storage/key owner, face/speaker provider, liveness, thresholds/correction/revoke policy ou Human Observation governance owner.

Core user identity remains authority regardless.

## 17. Internet Research / web egress — TO_INVENTORY

Não considerar comprovados: approved search provider, shared search API, safe-fetch component, outbound proxy/allowlist suitable for Copilot, protected destination blocking, malware policy, browser automation infra ou research cache policy.

## 18. External OAuth / secret management — TO_INVENTORY

Não considerar comprovados sem evidence: reusable OAuth callback framework, state/nonce/PKCE conventions, token vault, rotation/revocation, connection ownership model, admin consent governance ou provider-scope inventory.

Credentials elsewhere are not automatically reusable by Copilot.

## 19. Microsoft 365 / Teams — TO_INVENTORY IN REPO

C0 deve procurar factual evidence de Microsoft Graph/Entra configuration, delegated/application/resource-specific scopes, Outlook/Teams/SharePoint/OneDrive integrations, chats/channels/meetings/transcripts/recordings, change notifications, app/tab/bot distribution e credential/admin owner.

No evidence = `NOT_PROVEN`. Base Teams integration does not imply raw realtime media bot.

## 20. Google Workspace / Gmail — TO_INVENTORY IN REPO

C0 deve procurar Google OAuth app/config, Gmail/Calendar/Drive integration, scopes, push/PubSub, token lifecycle e provider credential owner.

## 21. WhatsApp — TO_INVENTORY IN REPO

Mapear integrations oficiais existentes. Default target architecture remains supported WhatsApp Business Platform contracts when applicable, not personal WhatsApp Web sessions.

## 22. Other external connectors — TO_INVENTORY

Inventariar Slack, GitHub, CRMs, service desks e outros integrations apenas com evidence real.

## 23. Provider/domain events — TO_INVENTORY

C0 deve mapear:

- event/webhook ingress conventions;
- authenticity/signature validation;
- EventEnvelope compatibility;
- duplicate/out-of-order handling;
- subscription renewal/reconciliation;
- scheduler/polling fallback;
- domain event owners/topics/sockets;
- event freshness and replay semantics.

Não criar event framework/broker antes de provar gaps.

## 24. Automation / RPA platform — TO_INVENTORY

**Não há, nesta baseline documental, evidence suficiente para afirmar que existe um RPA Hub/orchestrator corporativo reutilizável.** C0.S0 deve procurar factual evidence para:

```text
RPA vendors/tools/platforms/licences
orchestrators/control rooms
bots/robots/packages
existing desktop/web automations
package/version/deploy/rollback
queues/priorities
workers/worker pools/heartbeats
leases/locks/concurrency
desktop/session/VDI environments
service accounts/background identities
credential injection/storage
screenshots/artifacts/logs/retention
retry/idempotency semantics
support/SLA/ownership
kill switches/emergency stop
```

Classify only from evidence:

```text
PLATFORM_REUSE
NEUTRAL_SHARED_REUSE
COPILOT_IMPLEMENT_NEW
EXTEND_PLATFORM_CONTRACT
ADAPTER_REQUIRED
ADR_REQUIRED
NOT_PROVEN
OUT_OF_SCOPE
```

Do not select UiPath/Automation Anywhere/Power Automate or another product by assumption.

## 25. Automation scripts/functions/jobs — TO_INVENTORY

C0 deve mapear scheduled scripts, functions, cron/jobs, browser/desktop automations e existing integrations that already execute operational actions.

For each finding capture:

```text
owner
trigger
input/output contract
credential model
business authority
idempotency/retry
observability
failure/support model
```

Existing script does not automatically become a Copilot executor.

## 26. Queues/workers/background execution — TO_INVENTORY

Não considerar comprovados sem C0:

- general-purpose queue/broker suitable for automation;
- worker lease/heartbeat standard;
- desktop worker pool;
- background service identity standard for Copilot ACT;
- execution cancellation/draining;
- concurrency/priority model;
- worker environment isolation.

Workers are infrastructure identities, not business actors/permission authorities.

## 27. Decision/rule engines — TO_INVENTORY

C0 deve procurar existing deterministic rule/decision engines, BPM/process engines, validation services and domain readiness rules.

If authoritative business readiness already exists in a Domain API/use case, Copilot should consume it rather than recreate it.

No evidence = Copilot may implement its own orchestration Policy/Specification while preserving Domain authority, according to `49/57`.

## 28. Business postcondition / Outcome sources — TO_INVENTORY BY DOMAIN

Autonomous execution requires truthful verification. C0 must map authoritative sources capable of answering postconditions such as:

```text
invoice actually created/valid
maintenance request actually opened
message accepted/delivered state
production report actually changed
business record committed
```

Technical HTTP/RPA success alone is insufficient.

## 29. Notification/escalation channels — PARTIAL PROVEN / TO_INVENTORY

Core/Portal notification infrastructure is partially proven; external channels depend on connector evidence.

C0 maps delivery owner/contract for Minha DELPI, email, Teams, WhatsApp Business and any other approved channel, including dedupe/ack/SLA/escalation capabilities.

## 30. Personal versus organizational data — TO_INVENTORY

Identify policies for delegated accounts, shared resources, org service accounts, Case/Room sharing, cache/retention, Knowledge promotion, provider compliance/terms/data classification.

## 31. Operational context — TO_INVENTORY BY DOMAIN

WorkspaceContext + EntityRef is target, but C0 proves real owners/IDs/contracts for OP/operation/machine/workstation/product/revision/lot/material/tool.

## 32. Industrial/OT — TO_INVENTORY / NO-ACTUATION DEFAULT

Do not assume vendors/protocols/SCADA/MES/telemetry/command APIs/network reachability/safety architecture.

Even if command interface exists, it does not authorize Copilot/RPA/computer-use actuation.

## 33. Privacy/retention — TO_INVENTORY

Map owners/policies for media/biometric/web research/external resources, RPA screenshots/desktop artifacts, automation logs/execution metadata, employee/workplace privacy, export/delete/anonymize and LGPD classification.

## 34. Training/procedures — TO_INVENTORY

Map official instructions/procedures/drawings/revisions/videos/qualification owners and freshness. External sources only complement; they do not replace official internal operational sources.

## 35. Mandatory C0.S0 complementary inventory

```text
all active manifests/APIs/OpenAPIs
representative auth clients/middleware
Gateway dev/prod
Compose/env/storage patterns
Portal/federation/plugin-ui contracts
rooms/cases/requests/events/workers
media/device/biometric sources
outbound egress/search/fetch
OAuth/callback/secret-store
Microsoft/Google/WhatsApp Business/other connectors
Teams Graph/consent/artifacts/events
webhook/subscription/reconciliation
RPA platforms/orchestrators/bots/packages
scripts/functions/jobs
queues/workers/desktop sessions
service/background identities
rule/BPM/process engines
business outcome/postcondition sources
notification/escalation channels
automation governance/kill switches
external privacy/compliance ownership
production context/OT/safety
```

## 36. Baseline conclusion

**PROVEN platform foundations:**

```text
Keycloak       → SSO
Core API       → governance/RBAC/apps/routes
Portal         → Shell/host/context/navigation
Gateway        → routing
plugin-ui      → design system
Module Federation → MFE integration
Domain APIs    → business data/rules
Infra          → deploy/network/storage foundations
```

**PARTIAL PROVEN:** notifications/socket/worker/scheduler patterns exist in parts of the platform, but transversal ownership/contracts for autonomous operations are not yet established.

**NOT YET PROVEN for Copilot:** specific media/biometric/search/OAuth/connectors/Teams/RPA platform/event bus/automation queues/workers/background identities/outcome verifiers/factory/OT/privacy implementations.

Therefore C0.S0 must inventory and freeze these boundaries before any Automation Hub/RPA/Event engine/autonomous ACT implementation.
