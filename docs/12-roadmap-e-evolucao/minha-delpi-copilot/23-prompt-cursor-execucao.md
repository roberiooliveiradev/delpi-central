# Prompt mestre — Cursor — Minha DELPI Copilot Standalone

Implemente o **Minha DELPI Copilot como aplicação nova e independente**, do zero até o produto completo. Não evolua nem refatore o Minha DELPI Chat para atingir este objetivo.

A visão alvo inclui **escritório, reuniões, chão de fábrica, fontes externas autorizadas e operações autônomas governadas**, com texto, voz, imagem, câmera, vídeo e documentos quando autorizados. Também inclui **identidade biométrica governada**, **Internet Research**, **External Connectors**, **Microsoft Teams** e **Event-Driven Autonomous Operations + Automation & Execution Hub** conforme `54`, `55`, `56` e `57`.

O Copilot é o cérebro de contexto/decisão/orquestração; executors/API/RPA/computer-use são mecanismos de execução e nunca viram uma segunda inteligência ou authority de regra de negócio.

## 1. Decisão inegociável

```text
Copilot backend  = nova minha-delpi-copilot-api
Copilot frontend = novo plugins/minha-delpi-copilot
Chat backend     = sistema separado
Chat frontend    = sistema separado
```

Proibido:

```text
importar runtime do minha-delpi-ai-api
importar source do plugins/minha-delpi-chat
usar Chat API como proxy/planner/tool/media/biometric/external/automation runtime
usar Chat tables/sessions/agents como Copilot authority
criar teams-copilot-api ou Teams planner separado
criar RPA planner/AI paralelo ao Copilot
alterar Chat para desbloquear Copilot
esperar roadmap/Onda J do Chat
```

O Chat pode ser lido em C0 somente como referência para patterns, lessons learned e anti-patterns.

## 2. North Star de experiência

O mesmo Copilot deve poder se apresentar como:

```text
GLOBAL      → painel contextual no Portal
WORKSPACE   → página completa
MEETING     → reunião assistida multimodal
FRONTLINE   → operador/posto/máquina
TEAMS       → futura surface app/tab/bot do mesmo Copilot
BACKGROUND  → Watches/Workflows governados reagindo a eventos sem user prompt
```

Todas as surfaces e background operations usam:

```text
same Copilot API
same product identity
same Core/RBAC
same Policy/Decision Gate
same Evidence model
same Durable Work runtime
same External Connector governance
same Automation/Outcome governance
```

## 3. Ordem de leitura

1. `docs/11-padroes-de-desenvolvimento/instrucoes-oficiais-gpt-arquiteto-delpi-central.md`
2. `.cursor/rules/development-standards-index.mdc` + regras aplicáveis
3. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/README.md`
4. `.../16-execution-master-plan.md`
5. `.../50-standalone-copilot-application-architecture.md`
6. `.../51-platform-integration-baseline.md`
7. `.../52-standalone-repository-and-bootstrap-plan.md`
8. `.../17-component-and-contract-map.md`
9. `.../49-architecture-and-design-patterns-standard.md`
10. `.../53-multimodal-meeting-frontline-and-industrial-copilot.md`
11. `.../54-biometric-identity-and-human-observation-governance.md`
12. `.../55-internet-research-and-external-connectors.md`
13. `.../56-microsoft-teams-connector-and-meeting-integration.md` quando Teams for material
14. `.../57-event-driven-autonomous-operations-and-automation-execution-hub.md` quando events/automation/RPA/autonomy forem materiais
15. `.../20-testing-and-acceptance-matrix.md`
16. `.../21-data-and-state-model.md`
17. `.../22-cursor-execution-protocol.md`
18. `.../25-requirements-traceability.md`
19. `.../evidence/execution-ledger.md`
20. specs temáticas da etapa.

`16` é a única authority de ordem. `49` é authority de code architecture/patterns. `57` governa Event/Signal Plane, Decision Intelligence, executor boundaries, RPA/computer-use, outcome verification e capability-scoped autonomy.

## 4. Ordem de construção

```text
C0 Platform + Architecture + Media/Privacy/Biometric/External/Automation/OT Foundation Freeze
→ C1 Standalone App Bootstrap
→ C2 Portal + Operational Context + Platform Commands
→ C3 Intelligence + Multimodal/Biometric/Internet/Connector/Decision Foundations
→ C4 Business + External Reads + Graph + Operational Read Intelligence
→ C5 Governed Business/External/Automation Writes + Durable Foundation
→ C6 Product Work + Meeting/Frontline + Automation Hub + Events + Ecosystem
→ C7 Autonomous Operations + Advanced Realtime/External Proactivity + Rollout
```

## 5. Primeira ação — C0.S0

Antes de qualquer runtime diff:

```text
git status
git rev-parse HEAD
```

Inventarie com paths/symbols/contracts/evidence.

### Portal/Core/Gateway/Infra/MFEs/APIs

Mapear auth/RBAC/manifest/federation/plugin-ui, HTTP clients, API/OpenAPI contracts, events/sockets/jobs, storage/network/secrets, deep links/context, notifications, workers/schedulers e domain sources conforme authorities existentes.

### Media/Meeting/Frontline/Biometric

Mapear speech/vision/media providers, recording/transcription, storage, privacy/consent/retention, shared devices, production terminals, biometric enrollment/templates/providers/liveness e governance owner.

### Internet/External Connectors

Mapear web/search, safe fetch, Microsoft Graph, Google Workspace, WhatsApp Business, OAuth flows, token storage, provider webhooks/subscriptions, reconciliation, attachment scanning e compliance owners.

### Microsoft Teams

Mapear Entra app registrations, tenant/admin owner, delegated/application/resource-specific consent, chats/channels/messages, meetings/transcripts/recordings, change notifications, app/tab/bot inventory, privacy/retention e raw-media constraints. Não assumir raw media bot como requirement do connector base.

### Automation / RPA / Autonomous Operations

Mapear factual:

- RPA tools/orchestrators/licences existentes;
- bots/robots/packages e owners;
- automações desktop/web;
- scripts/functions/jobs;
- event sources/brokers/topics/webhooks;
- queues/workers/worker pools/heartbeats;
- schedulers/polling jobs;
- service accounts/background identities;
- credential injection/secret owners;
- desktop/session/VDI execution infrastructure;
- package/version/deploy/rollback patterns;
- retry/idempotency/lease/lock patterns;
- RPA screenshots/artifacts/logging/retention;
- rule/decision engines existentes;
- BPM/workflow/process engines;
- business postcondition/outcome verification sources;
- notification/escalation channels;
- kill switch/emergency stop patterns;
- automation ownership/governance/SLA/support.

Não criar Automation Hub/RPA service por suposição. Classificar `REUSE | EXTEND | ADAPTER | CREATE_REQUIRED/IMPLEMENT_NEW` somente com evidence.

### Industrial/OT — inventário somente

Mapear telemetry/read interfaces e safety owners; command APIs apenas como fato. Não assumir autoridade de atuação física.

### Chat reference only

Inspect lessons/anti-patterns only; nunca `REUSE` como Copilot runtime.

Classify findings:

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

No runtime changes in C0.S0.

## 6. Foundation Freeze

Before C1:

```text
PLATFORM_INVENTORY=PASS
STANDALONE_BOUNDARY=PASS
NAMES_PATHS=PASS
AUTHORITIES=PASS
SHARED_PRIMITIVES=PASS
ARCHITECTURE_PATTERNS=PASS
PERSISTENCE_BOUNDARIES=PASS
INTEGRATION_CONTRACTS=PASS
MEDIA_PRIVACY_BOUNDARIES=PASS
BIOMETRIC_IDENTITY_BOUNDARY=PASS
HUMAN_OBSERVATION_BOUNDARY=PASS
EXTERNAL_EGRESS_BOUNDARY=PASS
OAUTH_CONNECTION_BOUNDARY=PASS
PROVIDER_SECRET_BOUNDARY=PASS
EXTERNAL_SOURCE_PRIVACY_BOUNDARY=PASS
EXTERNAL_EVENT_BOUNDARY=PASS
TEAMS_TENANT_GRAPH_BOUNDARY=PASS
AUTOMATION_EXECUTION_BOUNDARY=PASS
EVENT_SIGNAL_BOUNDARY=PASS
BACKGROUND_IDENTITY_BOUNDARY=PASS
EXECUTOR_CONTRACT_BOUNDARY=PASS
OUTCOME_VERIFICATION_BOUNDARY=PASS
AUTONOMY_SCOPE_BOUNDARY=PASS
SHARED_DEVICE_BOUNDARY=PASS
OPERATIONAL_CONTEXT_BOUNDARY=PASS
OT_SAFETY_BOUNDARY=PASS
CONFORMANCE_HARNESS=PASS
CHAT_RUNTIME_DEPENDENCY=0
FOUNDATION_DUPLICATION=0 material
```

## 7. Target physical structure

Recommended unless C0 evidence/ADR changes it:

```text
minha-delpi-copilot-api/
  app/domain
  app/application
  app/interfaces
  app/infrastructure
  app/composition
  migrations/tests/docs/scripts

plugins/minha-delpi-copilot/
  src/ui
  src/state
  src/data
  src/features
  src/contracts
  src/adapters
```

Automation & Execution Hub does **not** imply new service. C0 decides whether it is a bounded module inside Copilot API or neutral platform service based on ownership/consumers/evidence.

## 8. Architecture rules

```text
Clean Architecture
+ Ports & Adapters
+ pragmatic DDD
+ Event-Driven only with real event owner
+ State Machines for nontrivial lifecycle
+ Policy/Specification for deterministic decisions
+ light CQRS only when justified
```

Concrete providers/executors only in Infrastructure/Adapters. Composition Root wires implementations.

Before creating port/repository/factory/strategy/registry/event bus/RPA hub/worker queue/computer-use adapter, pass `49` Abstraction Gate.

## 9. Auth/RBAC and background identity

```text
Keycloak → identity/JWT
Core → platform permissions
Domain API → final business rule/authorization
External provider → connection scopes
AutonomyPolicy → additional execution constraints, never permission elevation
```

Background/autonomous action requires explicit actor:

```text
authenticated/delegated user
or
approved service identity with bounded capability scope
```

Never:

```text
event source = permission
worker identity = business user
device identity = authorization
biometric match = permission
```

## 10. Workspace/Operational Context

Reuse `WorkspaceContext + EntityRef + SourceRef` where material. Never include secrets or permission truth.

## 11. Business Actions

OpenAPI-first chain remains native to Copilot:

```text
OpenAPI
→ Action Catalog
→ Capability Projection
→ planner
→ validation
→ Policy/Decision
→ executor
→ Domain API
→ verified Outcome/Evidence
```

## 12. Event / Signal rules

Follow `57`.

```text
source event
→ validate/authenticate source
→ EventEnvelope
→ dedupe/order/correlation
→ Watch/Workflow/Decision use case
```

Required:

- event payload is untrusted for policy/permission;
- duplicate event cannot duplicate execution;
- polling/scheduler is bounded fallback only when source lacks event contract;
- freshness/cost/dedupe explicit;
- no new event bus by speculation.

## 13. Decision Intelligence rules

Not every event invokes an LLM.

```text
DecisionPathPolicy
├─ FAST        deterministic Policy/State Machine
├─ OPERATIONAL bounded reads/rules + optional classifier
└─ REASONING   Graph/Knowledge/Expertise/LLM
```

Material business readiness with known criteria uses deterministic `Policy/Specification` over authoritative facts. LLM may explain/investigate but is not the only authority.

No chain-of-thought persistence.

## 14. Automation & Execution Hub rules

Canonical separation:

```text
Copilot
= context + decision + orchestration

Automation & Execution Hub
= execution
```

Executor preference:

```text
1 API official
2 native supported integration
3 deterministic function/script
4 RPA
5 computer-use
6 human task
```

Planner sees semantic capability, never implementation mechanics.

Example:

```text
billing.invoice.issue
```

Allowed mapping:

```text
billing.invoice.issue → API executor
```

or, if legacy evidence requires:

```text
billing.invoice.issue → RPA executor
```

Forbidden:

```text
planner outputs click(x,y)
planner outputs CSS selector for ERP
planner embeds RPA package internals
```

## 15. Automation execution rules

Execution contract/lifecycle when implemented:

```text
QUEUED
→ RUNNING
→ SUCCEEDED | FAILED | AMBIGUOUS | CANCELLED | TIMED_OUT
```

Required metadata: correlation, capabilityRef, executorRef/version, actorRef, inputHash, attempt, idempotency, result/error refs, outcomeVerificationRef.

No duplicate effect after event replay, retry or workflow resume.

## 16. RPA rules

RPA is replaceable Infrastructure executor, never business authority.

When in scope require:

- package/version traceability;
- worker health/heartbeat;
- queue/lease/concurrency;
- environment separation;
- protected credential injection;
- desktop/session isolation;
- screenshot/artifact classification/retention;
- timeout/cancel;
- retry eligibility;
- ambiguous outcome handling;
- audit/correlation.

Prefer API when reliable authoritative contract exists.

## 17. Computer-use rules

Advanced fallback only, not default.

Requires sandbox/session isolation, app/domain/network allowlist, protected credentials, bounded actions, takeover/stop, audit and same Policy/Decision semantics.

Never arbitrary corporate-network browsing.

## 18. Outcome verification rules

Invariant:

```text
technical executor success != verified business outcome
```

Examples:

```text
HTTP 200 != invoice definitely issued
RPA clicked Save != transaction committed
provider accepted message != final delivery when async
```

Use authoritative API/event/record/postcondition verifier where material.

Never notify “concluído” when Outcome is pending/ambiguous.

## 19. Watch / Proactivity rules

C6:

```text
OBSERVE
ADVISE
PREPARE
```

C7 only:

```text
ACT
```

PREPARE builds candidate action/preview/draft/work plan and has no side effect.

ACT requires capability-scoped AutonomyPolicy, identity, limits, revalidation, kill switch and Outcome verification.

## 20. Autonomy rules

No global `Copilot=L5`.

Autonomy input:

```text
capability
+ actor/service identity
+ source/event trust
+ business context
+ risk/sensitivity
+ financial/material limits
+ environment
+ reversibility
+ policy
```

L5 is OFF by default.

Example levels are configured by policy, never hardcoded in planner.

## 21. Human-in-the-loop

Manual exception uses same Durable Workflow:

```text
Workflow
→ wait_user / wait_approval
→ Inbox/Decision
→ human resolution
→ resume same Workflow
```

No parallel “manual process engine”.

## 22. Notifications/escalations

Outcome/event/Watch can notify through approved Minha DELPI/email/Teams/WhatsApp channels.

Recipients, severity, dedupe, SLA/escalation and acknowledgement follow explicit policy. Notification success is not business Outcome.

## 23. External/Teams/Media/Biometric rules

Follow `53–56` without weakening privacy/RBAC/source ACLs. External/meeting content remains untrusted for policy. Teams is same Copilot runtime. Biometrics never grant permission.

## 24. OT safety rule

Copilot/Automation Hub is not a safety controller.

```text
free-form LLM → PLC/CNC/robot/machine = BLOCK
voice command → direct actuation = BLOCK
Copilot L5 → implicit OT authority = BLOCK
RPA/computer-use → machine safety bypass = BLOCK
```

Future physical actuation requires separate industrial safety architecture/gate.

## 25. C1 special rule

First runtime work is standalone bootstrap only. No RPA Hub/Event engine/autonomous runtime before Foundation Freeze.

## 26. Phase-specific automation mapping

```text
C0 → inventory/freeze events, executors, workers, service identity, outcome/autonomy boundaries
C1 → standalone bootstrap, no automation runtime
C2 → context/commands only
C3 → event/decision-path foundations, no material ACT
C4 → read-only readiness/anomaly intelligence
C5 → executor ports/adapters + execution lifecycle + outcome verification + governed writes
C6 → Watch OBSERVE/ADVISE/PREPARE + Automation Hub admin + exceptions/notifications
C7 → selected Watch ACT + capability-scoped L5 + advanced computer-use
```

## 27. Generic implementation protocol

For one `C*.S*` at a time:

```text
REVALIDATE HEAD
→ READ AUTHORITIES INCLUDING 57 WHEN AUTOMATION/EVENT/RPA IS MATERIAL
→ IDENTIFY OWNER/LAYER/PATTERN
→ ABSTRACTION GATE
→ DEPENDENCY GATE
→ BASELINE
→ MINIMAL CORRECT DIFF
→ WIRE PRODUCER/CONSUMER
→ UNIT/CONTRACT/INTEGRATION
→ POSITIVE/SIBLING/NEGATIVE
→ SECURITY/RBAC/PRIVACY/EXTERNAL/AUTOMATION/SAFETY
→ GENERALIZATION/METAMORPHIC/UNKNOWN
→ CHAT-INDEPENDENCE CHECK
→ ARCHITECTURE CONFORMANCE
→ RESIDUAL SEARCH
→ COMPLETE_GATE
→ DOCS/LEDGER
→ NEXT STEP
```

## 28. Prohibitions

- Chat runtime/database/API dependency;
- second RBAC/user authority;
- business rules in MFE/LLM/RPA bot;
- provider/executor hardcode in planner;
- manual endpoint catalog authority;
- RPA click/selector/coordenada in planner/domain/application;
- RPA selected over authoritative supported API without evidence;
- second Workflow engine inside Automation Hub;
- event payload directly executing write;
- event/worker/device identity granting permission;
- background execution without explicit bounded identity;
- blind retry after ambiguous write;
- technical executor success treated as business success;
- PREPARE silently becoming ACT;
- global unrestricted L5;
- autonomy kill-switch bypass;
- computer-use without sandbox/allowlist;
- secrets in prompt/LLM/MFE/log/screenshots;
- Chat/Teams-specific planner runtime;
- implicit external send;
- raw media/biometric policy bypass;
- hidden worker/person profiling;
- arbitrary LLM/RPA→PLC/CNC/robot;
- safety-interlock bypass.

## 29. Required tests

Use `20` as authority.

Automation scope must include:

```text
EVENT_SOURCE_AUTHENTICITY
EVENT_DEDUPE_NO_DUPLICATE_EXECUTION
EVENT_NOT_PERMISSION
FAST_PATH_NO_LLM_WHEN_DETERMINISTIC
DETERMINISTIC_READINESS_REPRODUCIBLE
PLANNER_NO_RPA_UI_MECHANICS
API_PREFERRED_OVER_RPA_WHEN_SUPPORTED
EXECUTOR_SUBSTITUTION_NO_PLANNER_PATCH
BACKGROUND_IDENTITY_EXPLICIT
AUTOMATION_EXECUTION_IDEMPOTENT
RPA_WORKER_SESSION_CREDENTIAL_ISOLATION
AMBIGUOUS_WRITE_NO_BLIND_RETRY
VERIFIED_BUSINESS_OUTCOME
PREPARE_NOT_ACT
CAPABILITY_SCOPED_AUTONOMY
L5_OFF_DEFAULT
AUTONOMY_KILL_SWITCH
COMPUTER_USE_BOUNDED
NO_ARBITRARY_OT_COMMAND
```

## 30. Complete Gate blockers

```text
PARTIAL
INCONCLUSIVE
PENDING
TEST_NOT_RUN
STALE_EVIDENCE
DUPLICATE_AUTHORITY
FOUNDATION_DRIFT
ARCHITECTURE_PATTERN_DRIFT
UNJUSTIFIED_ABSTRACTION
CHAT_RUNTIME_IMPORT
PORTAL_AI_LOGIC_LEAK
DOMAIN_RULE_DUPLICATION
EVENT_PERMISSION_ELEVATION
DUPLICATE_EVENT_DUPLICATE_EXECUTION
PLANNER_RPA_UI_MECHANICS_LEAK
RPA_SELECTED_OVER_AUTHORITATIVE_API_WITHOUT_JUSTIFICATION
BACKGROUND_EXECUTION_WITHOUT_EXPLICIT_IDENTITY
AUTOMATION_EXECUTION_DUPLICATE
AMBIGUOUS_WRITE_BLIND_RETRY
EXECUTOR_TECHNICAL_SUCCESS_AS_BUSINESS_SUCCESS
PREPARE_BECOMES_ACT_IMPLICITLY
GLOBAL_UNSCOPED_L5
AUTONOMY_KILL_SWITCH_BYPASS
COMPUTER_USE_UNBOUNDED_ACCESS
PROVIDER_TOKEN_LEAK
CROSS_USER_EXTERNAL_DATA_LEAK
BIOMETRIC_PERMISSION_ELEVATION
ARBITRARY_LLM_OT_COMMAND
SAFETY_INTERLOCK_BYPASS
```

## 31. Report format

```text
STEP:
HEAD_BEFORE:
HEAD_AFTER:
STATUS:
DEPENDENCY_GATE:
CP_REQUIREMENTS:
FILES_CHANGED:
OWNERS:
LAYER/PATTERNS:
PLATFORM_REUSE:
COPILOT_NEW_CODE:
CHAT_DEPENDENCIES:
EVENT_AUTOMATION_RPA_IMPACT:
WIRING_PROOF:
TESTS:
SECURITY_RBAC:
PRIVACY_RETENTION:
BACKGROUND_IDENTITY:
EXECUTOR_OUTCOME_VERIFICATION:
AUTONOMY_POLICY:
EXTERNAL_CONNECTIONS_EGRESS:
TEAMS_INTEGRATION:
INDUSTRIAL_SAFETY:
GENERALIZATION:
CHAT_INDEPENDENCE:
ARCHITECTURE_CONFORMANCE:
RESIDUAL_SEARCH:
COMPLETE_GATE:
LEDGER_UPDATED:
NEXT_UNLOCKED:
COMMIT:
PUSH:
```

## 32. Start here

Execute only:

```text
C0.S0
```

Do not create Copilot API/MFE runtime features, Automation Hub, RPA executor, background ACT, Meeting/Frontline or advanced integrations until C0.S7 `FOUNDATION_FREEZE=PASS`. After freeze, start C1.S1 with standalone API skeleton.
