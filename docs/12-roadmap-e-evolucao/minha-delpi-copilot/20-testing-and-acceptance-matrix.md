# Minha DELPI Copilot — Matriz Canônica de Testes e Aceitação

**Status:** gate transversal canônico  
**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Boundary standalone:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Patterns:** [`49-architecture-and-design-patterns-standard.md`](./49-architecture-and-design-patterns-standard.md)  
**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)

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
media/provider policy hashes
retention/consent policy version
device/session class
industrial safety boundary/version when applicable
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
- browser/media/streaming patterns existentes;
- shared-device/tablet/kiosk/room patterns quando existirem;
- media/object storage existente;
- privacy/retention/consent owners existentes;
- OP/machine/operation/product context sources;
- OT APIs/events/protocol boundaries existentes, sem assumir command authority;
- Chat analisado apenas como reference-only.

### Standalone boundary

Negative obrigatório:

```text
Copilot target imports minha-delpi-ai-api
Copilot target imports plugins/minha-delpi-chat source
Copilot schema depends on Chat table/session/agent
Copilot requires Chat API endpoint
Copilot requires Chat container to start
Copilot media pipeline calls Chat runtime as required dependency
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
- IframeBridgeEnvelope;
- `MediaRef` ou equivalente, **somente se C0 confirmar necessidade**.

### Media/privacy/Frontline foundation

Provar antes de runtime multimodal contínuo:

- capture mode classes;
- media retention classes;
- transcript/raw-audio/raw-video/screen/Evidence lifecycle separado;
- consent/policy owner;
- shared-device identity/session isolation;
- operational context reuse de WorkspaceContext/EntityRef;
- realtime budgets/backpressure direction;
- industrial/OT boundary;
- no hidden surveillance default;
- no facial/emotion recognition introduced implicitly.

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
- media/provider integrations behind justified boundaries;
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
MEDIA_PRIVACY_BOUNDARIES=PASS
SHARED_DEVICE_BOUNDARY=PASS
OPERATIONAL_CONTEXT_BOUNDARY=PASS
OT_SAFETY_BOUNDARY=PASS
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
- API error/401 handling;
- responsive baseline;
- media capability/permission state does not start capture automatically;
- accessibility baseline compatible with future Frontline/Meeting surfaces.

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
- operational EntityRefs: OP/machine/product/operation/lote/posto when source exists;
- device/session metadata bounded and non-authoritative;
- stale context;
- logout context clear;
- user change on shared device clears prior local context;
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

## 5. Gate C3 — Intelligence Core + Multimodal Foundations

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

### Document/Image multimodal

- textual PDF;
- scanned PDF;
- image/drawing;
- unreadable region;
- page/region provenance;
- confidence/limitations;
- document/image prompt injection;
- FACT/CALCULATION/HYPOTHESIS/CONCLUSION/RECOMMENDATION semantics.

### Voice/audio

Quando voice baseline entrar no candidate:

- mic permission denied;
- mic permission revoked mid-session;
- speech-to-text success/partial/error;
- noisy/ambiguous utterance;
- correction/repeat flow;
- text-to-speech fallback;
- voice command equals typed command sem privilege difference;
- material action with uncertain transcription does not execute silently;
- no raw-audio persistence without policy.

### Camera/video

Quando camera/video entrar no candidate:

- camera permission denied/revoked;
- image/frame provenance;
- short-video segmentation/time-range provenance;
- unsupported/large video becomes bounded async/degraded flow;
- model uncertainty exposed;
- hostile visual/document instruction does not alter policy;
- raw-video retention follows configured class;
- visual finding does not become authoritative quality decision by default.

### Media policy

- transient capture without raw persistence;
- configured retention class honored;
- delete/anonymize path where required;
- provider/data policy filtering;
- session stop actually stops capture;
- F5/reconnect never restarts camera/mic silently.

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
- no master dataset replication;
- media/meeting/frontline evidence links to EntityRefs without copying source master data.

### Operational context correlation

Quando sources existirem:

- OP → product/revision;
- machine → maintenance/history;
- operation → procedure/instruction;
- lot/material → supplier/quality;
- user without permission does not gain data because device/machine context exists.

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
- no blind retry;
- repeated voice utterance/event does not duplicate write;
- meeting action candidate is not write until governed transition.

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

## 8. Gate C6 — Product Work + Proactivity + Meeting/Frontline + Ecosystem

### Task/Case

- create/reload/cancel/complete;
- state matches workflow;
- Evidence Board accepted/contested/missing/superseded;
- source permission remains required;
- Case does not auto-publish Experience;
- meeting/frontline refs do not duplicate raw source content.

### Rooms

- reuse/adapter contract against existing owner;
- participants/messages/files;
- membership does not grant source access;
- grounded summary;
- injection negative;
- Case correlation;
- meeting artifact link preserves source permissions.

### Inbox

- pending decision/work/result/alert states;
- meeting candidate actions pending review when applicable;
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

### Meeting Mode

Quando C6 Meeting scope for candidate:

- explicit start/stop;
- visible mic/transcript/camera/screen/raw-record indicators;
- capture cannot start hidden;
- participant/session context correct;
- live query uses user permissions;
- meeting transcript != summary != confirmed decision;
- generated ata cites/refers to sources when material;
- candidate action requires review/Decision Gate before write;
- resume/next meeting can load authorized pending actions;
- revoked participant/source access is respected;
- raw audio/video retention follows policy;
- meeting works without Chat runtime.

### Frontline Mode

Quando C6 Frontline scope for candidate:

- shared terminal login/user switch;
- prior-user local context/data does not leak;
- OP/machine/product/operation context resolves from canonical EntityRefs;
- hands-free command fallback to touch/text;
- noisy speech does not trigger unsafe action;
- camera finding exposes confidence/limitations;
- training step links to current revision/procedure source;
- unavailable source/provider yields safe degraded guidance;
- register issue/escalate uses governed Business Action;
- no physical machine command from free-form LLM;
- Frontline works without Chat runtime.

### Process learning / Knowledge

- observation creates candidate only;
- candidate has provenance/Evidence/context;
- expert/owner review required;
- feedback/meeting/operator statement does not change production behavior automatically;
- no hidden individual productivity scoring;
- PII/media handling;
- draft/test/publish/rollback;
- admin RBAC;
- no technical endpoint catalog inside expertise/playbook.

### AI-ready onboarding

- unknown app/MFE/iframe/API/pack;
- contracts drive onboarding;
- no app-specific planner hardcode;
- Frontline-ready requirements do not alter business permission semantics.

## 9. Gate C7 — Autonomy + Advanced Realtime + Optimization + Rollout

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
- provider names isolated from domain/application;
- realtime/media provider filtering by data policy.

### Advanced realtime/media

Quando candidate:

- session duration/budget limits;
- concurrent session limits;
- frame sampling/bitrate bounds;
- backpressure/network loss;
- graceful degraded/async fallback;
- realtime provider unavailable;
- capture stop/kill switch;
- cost telemetry;
- edge processing only with defined data boundary.

### Industrial/OT negative gate

Obrigatório enquanto não houver programa específico aprovado:

```text
free-form LLM output → PLC/CNC/robot command = BLOCK
voice command → direct machine actuation = BLOCK
visual finding → machine safety override = BLOCK
Copilot L5 → implicit OT permission = BLOCK
```

Se future OT actuation for explicitamente aprovada, exigir test matrix separada para deterministic command schema, state/preconditions, independent interlocks, simulation, authorization, fail-safe e audit.

### Rollout

- canary/cohort;
- feature flag owner/exit criteria;
- rollback;
- accessibility;
- incident metrics;
- media/privacy incident controls;
- final independence test with Chat offline.

## 10. Injection/safety transversal

Testar conforme surface:

```text
user prompt
voice transcript
tool/API result
RAG source
WorkspaceContext
device/session metadata
iframe message
Expertise/Playbook content
PDF/image
camera/video/screen
room message/file
event payload
meeting transcript
frontline observation
```

Untrusted data never changes system policy/permissions/retention/safety boundary.

## 11. Surface parity

Material security/authorization behavior deve permanecer equivalente entre:

```text
full page
Portal panel
Meeting
Frontline
send/stream/voice
Task/Case/Inbox surfaces
iframe contextual entry when supported
admin preview/simulation
```

UX/transport podem variar; RBAC/policy/Decision/Evidence semantics não.

## 12. Anchor scenarios finais

### Cross-domain investigation

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

### Meeting

```text
reunião produção
→ explicit capture/transcript
→ pergunta sobre linha/máquina
→ authorized APIs/Graph
→ grounded answer
→ decisões/pending actions
→ ata viva
→ review/Decision Gate
→ Task/Case
→ next-meeting follow-up
```

### Frontline

```text
operador + OP + máquina + operação
→ voice/camera question
→ drawing/procedure + history reads
→ Evidence/Hypothesis
→ guided response
→ issue/escalation candidate
→ governed action
→ Task/Case/Knowledge candidate
```

Todos devem funcionar sem Minha DELPI Chat runtime.

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
HIDDEN_MEDIA_CAPTURE
UNDEFINED_MEDIA_RETENTION
SHARED_DEVICE_STATE_LEAK
VOICE_PERMISSION_BYPASS
VISUAL_FINDING_AS_UNVALIDATED_FACT
HIDDEN_WORKER_SURVEILLANCE
ARBITRARY_LLM_OT_COMMAND
SAFETY_INTERLOCK_BYPASS
required test FAIL/INCONCLUSIVE/NOT_RUN
stale/non-reproducible evidence
```

## 14. Regra final

Qualquer gate REQUIRED em `FAIL | INCONCLUSIVE | PENDING | TEST_NOT_RUN | STALE_EVIDENCE` bloqueia a fase. Nunca enfraquecer teste para fazer candidate passar.