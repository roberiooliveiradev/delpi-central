# Minha DELPI Copilot — Matriz Canônica de Testes e Aceitação

**Status:** gate transversal canônico  
**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Boundary standalone:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Patterns:** [`49-architecture-and-design-patterns-standard.md`](./49-architecture-and-design-patterns-standard.md)

## 1. Regra de evidence

Todo PASS material registra, conforme aplicável:

```text
gitSha
Copilot API version/image
Copilot MFE version/bundle
manifest/config hashes
schema/migration version
OpenAPI/Action Catalog hashes
provider/model/config hashes
expertise/playbook hashes
environment
test/eval version
timestamp
```

Evidence posterior incompatível invalida o PASS afetado.

## 2. Gate C0 — Platform + Architecture Foundation Freeze

### Platform inventory

Provar com paths/contracts reais:

- Portal AuthContext/AppHost/AppLauncher/Router;
- Core `/me`, apps, routes, RBAC, manifest, notifications;
- Gateway dev/prod;
- Compose dev/prod;
- federation/plugin-ui;
- representative MFEs/manifests;
- APIs/OpenAPIs/auth/idempotency/entity IDs;
- rooms/events/jobs/notifications/workflows existentes;
- Chat analisado apenas como reference-only.

### Standalone boundary

Negative obrigatório:

```text
Copilot target imports minha-delpi-ai-api
Copilot target imports plugins/minha-delpi-chat source
Copilot schema depends on Chat table/session/agent
Copilot requires Chat API endpoint
Copilot requires Chat container to start
```

Todos devem resultar em `FAIL` arquitetural.

### Shared primitives

Positive/sibling/negative para:

- CorrelationContext;
- EntityRef/RelationshipRef;
- SourceRef/EvidenceRef/OutcomeRef;
- CapabilityProjection;
- PlatformCommand/Result;
- WorkspaceContext;
- Expertise/Playbook contracts;
- DecisionGate;
- WorkflowPlan/Step;
- TaskRef/CaseRef;
- EventEnvelope;
- IframeBridgeEnvelope.

### Architecture conformance

- dependency direction;
- no framework/provider concrete imports in Domain/Application;
- Ports/Adapters where boundary exists;
- Composition Root wiring;
- Repository only for owned persistent lifecycle;
- State Machine for nontrivial lifecycle;
- Error/Result translation at boundaries;
- retry/idempotency read/write semantics;
- frontend server/workspace/conversation/local/durable state ownership;
- no speculative Strategy/Factory/Saga/CQRS/registry/base class;
- ADR for material exception.

### FOUNDATION_FREEZE

```text
PLATFORM_INVENTORY=PASS
STANDALONE_BOUNDARY=PASS
NAMES_PATHS=PASS
AUTHORITIES=PASS
PRIMITIVES=PASS
ARCHITECTURE_PATTERNS=PASS
PERSISTENCE_BOUNDARIES=PASS
INTEGRATION_CONTRACTS=PASS
CONFORMANCE_HARNESS=PASS
CHAT_RUNTIME_DEPENDENCY=0
DUPLICATE_FOUNDATION=0 material
```

## 3. Gate C1 — Standalone Application Bootstrap

### Copilot API

- own root/package;
- `/health`;
- config validation;
- structured logging;
- JWT valid/expired/wrong issuer/wrong audience/signature;
- Core reachable/unavailable/timeout;
- current user/apps/routes authorization context;
- no Chat imports/endpoints/tables.

### Copilot MFE

- own plugin root;
- build/typecheck/tests;
- remoteEntry 200;
- React singleton/share scope;
- `@delpi/plugin-ui` loaded;
- mount/unmount;
- getAccessToken host contract;
- API error/401 handling.

### Manifest/Core/Gateway/Compose

- manifest schema valid;
- permission/route registration;
- forbidden route collision;
- API Gateway dev/prod path parity;
- MFE Gateway path;
- Compose services independent;
- health checks;
- no `depends_on` Chat.

### Portal

- authorized user opens full-page Copilot;
- unauthorized user blocked;
- F5/deep route;
- logout/login;
- global panel mounts same MFE/package contract;
- panel/full-page do not create different product states.

### Independence test

**Required:** Chat containers unavailable/stopped while Copilot bootstrap remains healthy and usable.

```text
COPILOT_API_OWN_RUNTIME=PASS
COPILOT_MFE_OWN_RUNTIME=PASS
NO_CHAT_IMPORT=PASS
NO_CHAT_API_DEP=PASS
NO_CHAT_DB_AUTHORITY=PASS
INDEPENDENT_DEPLOY_ROLLBACK=PASS
```

## 4. Gate C2 — Portal Context + Platform Commands

- WorkspaceContext bounded/sanitized;
- app/route/entity/filter/date context changes;
- stale context;
- logout context clear;
- Portal panel/full page parity;
- open app/route/entity authorized;
- unauthorized/revoked/TOCTOU;
- nonexistent target;
- arbitrary URL rejected;
- MFE sibling works without central branch;
- iframe PORTAL_ONLY;
- iframe origin/source/version/session negatives;
- no JWT/secret in bridge messages;
- business write via DOM/visual command rejected.

## 5. Gate C3 — Intelligence Core

### Conversation/understanding

- own conversation/session persistence;
- no `agent_id` or Chat session dependency;
- multi-intent/long request decomposition;
- clarification only when materially required;
- send/stream semantic parity.

### OpenAPI/Action Catalog foundation

- valid/invalid specs;
- multiple providers;
- schema normalization;
- no path/opId semantic hardcode;
- refresh/version handling;
- authorization filtering.

### Capability/Planner

- known action;
- sibling action;
- no-tool negative;
- unknown external OpenAPI;
- true metamorphic provider/path/opId rename;
- bounded typed plan;
- argument validation before execution.

### Expertise/Playbook/Knowledge

- positive/sibling/negative expertise;
- multi-domain composition;
- unknown pack without planner patch;
- pack/playbook cannot grant permission;
- Knowledge ACL enforced;
- project preference cannot elevate visibility.

### Multimodal/Evidence

- textual PDF;
- scanned PDF;
- image/drawing;
- unreadable region;
- page/region provenance;
- confidence/limitations;
- document prompt injection;
- FACT/CALCULATION/HYPOTHESIS/CONCLUSION/RECOMMENDATION semantics.

## 6. Gate C4 — Business Reads + Business Graph

### Generic reads

- known/sibling/unknown provider;
- path/query/body arguments;
- required missing;
- enum/type/format;
- unauthorized;
- upstream unavailable/timeout;
- normalized Outcome/Evidence;
- freshness/conflict/stale source;
- sensitive log redaction.

### Business Graph

- authorized traversal;
- relation absent;
- authoritative vs inferred;
- node without permission does not leak;
- cycle/depth budgets;
- source owner unavailable;
- sibling entity/relation without planner patch;
- traversal returns refs then fetches owner data;
- no master dataset replication.

## 7. Gate C5 — Governed Writes + Durable Foundation

### Decision Gate

- NO_GATE only when policy permits;
- ACKNOWLEDGE/CONFIRM/REVIEW_AND_CONFIRM/APPROVAL/BLOCK;
- arguments hash change;
- evidence change;
- expiry/rejection;
- approver permission;
- final RBAC/policy revalidation.

### Writes

- permitted/forbidden;
- idempotency replay;
- concurrent submit;
- conflict;
- ambiguous timeout;
- partial failure;
- outcome verification;
- no blind retry.

### Workflow foundation

- dependency DAG;
- safe parallel reads;
- checkpoint;
- wait_user;
- wait_approval;
- wait_event;
- timeout/cancel;
- crash after read/write;
- concurrent resume;
- duplicate event;
- permission/policy change while waiting;
- no duplicate write.

## 8. Gate C6 — Product Work + Proactivity + Ecosystem

### Task/Case

- create/reload/cancel/complete;
- state matches workflow;
- Evidence Board accepted/contested/missing/superseded;
- source permission remains required;
- Case does not auto-publish Experience.

### Rooms

- reuse/adapter contract against existing owner;
- participants/messages/files;
- membership does not grant source access;
- grounded summary;
- injection negative;
- Case correlation.

### Inbox

- pending decision/work/result/alert states;
- dedupe;
- resolved transition;
- revoked source permission sanitizes item;
- reading item does not execute write.

### Watch

- event match;
- OBSERVE/ADVISE grounded;
- wrong entity/duplicate/hostile event;
- permission revocation;
- expiry/disable;
- ACT remains blocked in C6.

### Knowledge/Learning/Studio

- source owner/version/provenance;
- Experience promotion requires review;
- PII handling;
- feedback does not change production automatically;
- draft/test/publish/rollback;
- admin RBAC;
- no technical endpoint catalog inside expertise/playbook.

### AI-ready onboarding

- unknown app/MFE/iframe/API/pack;
- contracts drive onboarding;
- no app-specific planner hardcode.

## 9. Gate C7 — Autonomy + Optimization + Rollout

### Autonomy/Watch ACT

- L5 OFF default;
- allowlist/limits/budget;
- Decision Gate when required;
- revocation during execution;
- kill switch;
- full audit.

### Simulation

- explicit baseline/assumptions;
- reproducible model/calculation;
- unsupported scenario does not invent numbers;
- simulation never writes;
- Apply is new governed Business Action.

### Model Router

- class selection based on compute policy;
- unavailable provider;
- compatible fallback;
- data-policy filtering;
- latency/cost thresholds;
- structured output validity;
- provider names isolated from domain/application.

### Rollout

- canary/cohort;
- feature flag owner/exit criteria;
- rollback;
- accessibility;
- incident metrics;
- final independence test with Chat offline.

## 10. Injection/safety transversal

Testar conforme surface:

```text
user prompt
tool/API result
RAG source
WorkspaceContext
iframe message
Expertise/Playbook content
PDF/image
room message/file
event payload
```

Untrusted data never changes system policy/permissions.

## 11. Surface parity

Material behavior must remain equivalent across:

```text
full page
Portal panel
send/stream
Task/Case/Inbox surfaces
iframe contextual entry when supported
admin preview/simulation
```

Only UX/transport may differ.

## 12. Anchor scenario final

```text
reclamação
→ Case
→ Business Graph
→ desenho multimodal
→ Evidence Board
→ Engineering + Quality expertise
→ 8D playbook
→ Task/Durable Workflow
→ wait_event revisão
→ Watch/Inbox
→ reanálise
→ Decision Gate
→ Domain API action
→ Outcome/Evidence/Audit
→ candidate Experience
```

Must work without Minha DELPI Chat runtime.

## 13. Release blockers

```text
CHAT_RUNTIME_IMPORT
CHAT_API_REQUIRED
CHAT_DATABASE_AUTHORITY
foundation duplication
architecture/pattern drift
claim without expected provenance
RBAC leakage
Graph source bypass
write without required Decision Gate
resume duplicate write
Case/Room source-data leak
Watch ACT without policy
simulation presented as fact
Experience auto-published
unknown provider/app requiring hardcode
required test FAIL/INCONCLUSIVE/NOT_RUN
stale/non-reproducible evidence
```

## 14. Regra final

Qualquer gate REQUIRED em `FAIL | INCONCLUSIVE | PENDING | TEST_NOT_RUN | STALE_EVIDENCE` bloqueia a fase. Nunca enfraquecer teste para fazer candidate passar.