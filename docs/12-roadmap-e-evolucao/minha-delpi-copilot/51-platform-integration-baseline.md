# Minha DELPI Copilot — Baseline de Integração com a Plataforma

**Status:** `CANONICAL_BASELINE` de evidências para integração  
**Escopo:** Portal, Core API, Gateway, APIs, MFEs, plugin-ui, infraestrutura e gaps `TO_INVENTORY` para media/biometric/Internet/connectors/Meeting/Frontline/OT  
**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)  
**Biometric/Human Observation:** [`54-biometric-identity-and-human-observation-governance.md`](./54-biometric-identity-and-human-observation-governance.md)  
**Internet/External Connectors:** [`55-internet-research-and-external-connectors.md`](./55-internet-research-and-external-connectors.md)

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

Core segue Clean Architecture e permanece authority de:

- platform users/context;
- apps/routes;
- RBAC/permissions;
- manifest registration;
- notifications/presence/app usage quando aplicável.

## 7. APIs dedicadas — PROVEN

Monorepo possui `api-delpi`, `commercial-api`, `financial-api`, `customer-experience-api` e outros serviços independentes.

Decisão: Copilot API dedicada é coerente com o monorepo e seguirá Clean Architecture/Ports & Adapters.

## 8. api-delpi / Domain APIs — PROVEN

`api-delpi` é backend-only e owner de integrações DELPI/TOTVS já expostas. Copilot consome contracts; não copia regra/integration.

Domain APIs continuam business authorities.

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

## 11. Domain Action integration — TARGET

```text
OpenAPI/contract
→ Copilot discovery/index
→ allowed capability projection
→ planner
→ generic adapter/executor
```

No endpoint-specific planner teaching.

## 12. Existing events/notifications/rooms — PARTIAL PROVEN / TO_INVENTORY

Core/Portal possuem notifications/socket patterns; alguns serviços possuem workers/schedulers; Portal Comercial expõe Interaction Rooms.

C0 precisa mapear owner/contracts antes de decidir reuse/extend/adapter/create.

## 13. Copilot surfaces — TARGET

```text
GLOBAL
WORKSPACE
MEETING
FRONTLINE
```

Mesmo MFE/API/runtime; no separate Meeting/Frontline backend.

## 14. Media/realtime — TO_INVENTORY

Não considerar comprovados sem C0:

- corporate STT/TTS/Vision provider;
- realtime/WebRTC standard;
- recording/transcription infra;
- media/object storage adequado;
- browser media abstraction;
- quotas/cost/latency;
- raw media retention policy;
- meeting-room hardware.

## 15. Devices/Frontline — TO_INVENTORY

Não considerar comprovados:

- tablets/kiosks standardized;
- mic/camera on production stations;
- device identity service;
- shared-terminal policy;
- factory network characteristics;
- current production-terminal contract.

## 16. Biometric Identity — TO_INVENTORY

Não considerar comprovados sem C0:

- approved biometric enrollment process;
- corporate photo source approved for biometric purpose;
- voice enrollment source;
- biometric template storage/key owner;
- face/speaker provider;
- liveness/anti-spoof capability;
- thresholds/correction/revoke policy;
- Human Observation governance owner.

Core user identity remains authority regardless.

## 17. Internet Research / web egress — TO_INVENTORY

Não considerar comprovados sem C0:

- approved web search provider;
- generic search API already shared;
- safe web-fetch component;
- outbound proxy/allowlist policy suitable for Copilot;
- protected/internal destination blocking;
- external content download/malware policy;
- browser automation infrastructure;
- research cache policy.

C0 must prove `PLATFORM_REUSE | NEUTRAL_SHARED_REUSE | COPILOT_IMPLEMENT_NEW | EXTEND_PLATFORM_CONTRACT | NOT_PROVEN`.

## 18. External OAuth / secret management — TO_INVENTORY

Não considerar comprovados sem evidence:

- reusable OAuth authorization/callback framework;
- state/nonce/PKCE conventions;
- provider token vault/secret manager;
- rotation/revocation lifecycle;
- user-delegated connection ownership model;
- org-managed/shared/service connection model;
- admin consent governance;
- provider scope inventory.

Even if env vars or provider credentials exist elsewhere, they are not automatically reusable by Copilot.

## 19. Microsoft 365 / Graph — TO_INVENTORY IN REPO

C0 deve procurar factual evidence de:

- existing Microsoft Graph app registration/config;
- delegated/application permission usage;
- Outlook mail/calendar/file integrations;
- Teams/SharePoint/OneDrive integrations;
- webhook/change-notification subscriptions;
- provider-specific credential owner.

Absence of repo evidence = `NOT_PROVEN`, even though Microsoft Graph is an external platform capability available in the market.

## 20. Google Workspace / Gmail — TO_INVENTORY IN REPO

C0 deve procurar:

- Google OAuth app/config;
- Gmail/Calendar/Drive integration;
- delegated scopes;
- push/Pub/Sub integration;
- token/refresh lifecycle;
- provider credential owner.

No repo evidence = `NOT_PROVEN`.

## 21. WhatsApp — TO_INVENTORY IN REPO

C0 deve mapear somente integrations oficiais existentes. Target architectural default from `55` is WhatsApp Business Platform when applicable.

Não assumir personal WhatsApp Web integration or reusable personal session.

## 22. Other external connectors — TO_INVENTORY

Inventariar Slack, GitHub, CRMs, service desks e outros integrations já existentes apenas com evidence real.

## 23. Provider events/webhooks — TO_INVENTORY

C0 deve mapear:

- webhook ingress conventions;
- authenticity/signature validation;
- EventEnvelope compatibility;
- subscription/watch renewal;
- scheduler/reconciliation capability;
- duplicate/out-of-order handling;
- missed-event recovery.

Não criar event framework antes de provar gaps.

## 24. Personal versus organizational data — TO_INVENTORY

C0 deve identificar owners/policies de:

- personal/delegated account access;
- shared mailbox/resources;
- org-managed service accounts;
- sharing into Case/Room;
- external content retention/cache;
- promotion to organizational Knowledge;
- provider compliance/terms/data classification.

## 25. Operational context — TO_INVENTORY BY DOMAIN

WorkspaceContext + EntityRef is target, but C0 proves real owners/IDs/contracts for OP/operation/machine/workstation/product/revision/lot/material/tool.

## 26. Industrial/OT — TO_INVENTORY / NO-ACTUATION DEFAULT

Do not assume vendors/protocols/SCADA/MES/telemetry/command APIs/network reachability/safety architecture.

Even if command interface exists, it does not authorize Copilot actuation.

## 27. Privacy/retention — TO_INVENTORY

Map owners/policies for:

- audio/video/screen;
- biometric enrollment/template;
- employee/workplace privacy;
- web research/cache;
- user-delegated mailbox/files/messages;
- organizational external resources;
- provider data processing;
- export/delete/anonymize;
- LGPD/data classification.

## 28. Training/procedures — TO_INVENTORY

Map official instructions/procedures/drawings/revisions/videos/qualification owners and freshness. External sources only complement; they do not silently replace official internal operational sources.

## 29. Mandatory C0.S0 complementary inventory

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
webhook/subscription/reconciliation
external privacy/compliance ownership
production context/OT/safety
```

## 30. Baseline conclusion

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

**NOT YET PROVEN for Copilot:** specific media/biometric/search/OAuth/connector/provider-event/factory/OT/privacy implementations.

Therefore C0.S0 must inventory and freeze these boundaries before any external provider code is introduced.
