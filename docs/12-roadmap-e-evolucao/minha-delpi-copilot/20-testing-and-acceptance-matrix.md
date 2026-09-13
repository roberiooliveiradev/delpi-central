# Minha DELPI Copilot — Matriz Canônica de Testes e Aceitação

**Status:** gate transversal canônico  
**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Boundary standalone:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Patterns:** [`49-architecture-and-design-patterns-standard.md`](./49-architecture-and-design-patterns-standard.md)  
**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)  
**Biometric/Human Observation:** [`54-biometric-identity-and-human-observation-governance.md`](./54-biometric-identity-and-human-observation-governance.md)  
**Internet/External Connectors:** [`55-internet-research-and-external-connectors.md`](./55-internet-research-and-external-connectors.md)

## 1. Regra de evidence

Todo PASS material registra, conforme aplicável:

```text
gitSha
Copilot API/MFE version
manifest/config/schema hashes
OpenAPI/Action Catalog hashes
model/provider/config hashes
expertise/playbook versions
media/biometric policy versions
external connector/connection policy version
OAuth scope policy version
egress/web-fetch policy version
retention/consent policy version
environment
test/eval version
timestamp
```

Evidence incompatível ou stale invalida o PASS afetado.

## 2. Gate C0 — Foundation Freeze

### Inventário factual obrigatório

Provar com paths/contracts reais:

- Portal/Core/Gateway/Compose/federation/plugin-ui;
- APIs/OpenAPIs/auth/idempotency/events;
- rooms/jobs/notifications/workflows;
- media/storage/device/privacy owners;
- biometric enrollment/provider/storage/liveness quando existir;
- outbound HTTP/egress/proxy/DNS policy;
- OAuth callback/connection/secret-storage patterns;
- Microsoft Graph/Google Workspace/WhatsApp Business/other integrations existentes;
- webhook/subscription/push/scheduler/reconciliation patterns;
- external-data privacy/compliance owners;
- OT/industrial boundaries;
- Chat apenas como reference-only.

### Standalone negatives

Devem falhar arquiteturalmente:

```text
Copilot importa runtime/source do Chat
Copilot depende de Chat API/container/database authority
Copilot usa Chat media/biometric/external runtime como dependency obrigatória
```

### Shared foundations

Validar sem duplicação:

- CorrelationContext;
- EntityRef/RelationshipRef;
- SourceRef/EvidenceRef/OutcomeRef;
- CapabilityProjection;
- PlatformCommand/Result;
- WorkspaceContext;
- DecisionGate;
- WorkflowPlan/Step;
- TaskRef/CaseRef;
- EventEnvelope;
- MediaRef/biometric/external refs somente quando C0 provar necessidade.

### Media/Biometric/External foundation

Provar:

- capture/retention classes;
- shared-device isolation;
- biometric enrollment/template/revoke/correction boundaries;
- unknown/low-confidence semantics;
- prohibited person-inference classes;
- safe outbound web boundary;
- protected/internal destinations não podem ser alcançados por web research;
- redirects continuam sob a mesma policy;
- OAuth lifecycle e least privilege;
- provider credentials protegidos e fora de LLM/MFE/logs;
- USER_DELEGATED/ORG_MANAGED/SHARED_RESOURCE/SERVICE_CONNECTION permanecem distintos;
- personal source não vira organizational source implicitamente;
- read/write external capabilities permanecem separadas;
- webhook authenticity/dedupe/renewal/reconciliation definidos;
- external learning exige promoção governada;
- OT safety non-authority.

### Architecture conformance

- dependency direction;
- concrete providers apenas em infrastructure/adapters;
- Composition Root wiring;
- Repository somente para lifecycle/state owned;
- State Machine para lifecycle não trivial;
- error/result translation;
- idempotency/resilience;
- provider-neutral planner;
- no speculative abstraction;
- ADR para exceção material.

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
BIOMETRIC_IDENTITY_BOUNDARY=PASS
HUMAN_OBSERVATION_BOUNDARY=PASS
EXTERNAL_EGRESS_BOUNDARY=PASS
OAUTH_CONNECTION_BOUNDARY=PASS
PROVIDER_SECRET_BOUNDARY=PASS
EXTERNAL_SOURCE_PRIVACY_BOUNDARY=PASS
EXTERNAL_EVENT_BOUNDARY=PASS
EXTERNAL_LEARNING_BOUNDARY=PASS
SHARED_DEVICE_BOUNDARY=PASS
OPERATIONAL_CONTEXT_BOUNDARY=PASS
OT_SAFETY_BOUNDARY=PASS
CONFORMANCE_HARNESS=PASS
CHAT_RUNTIME_DEPENDENCY=0
DUPLICATE_FOUNDATION=0 material
```

## 3. Gate C1 — Standalone Bootstrap

### API/MFE/Platform

- API/MFE próprios;
- health/config/logging/JWT/Core integration;
- Module Federation/plugin-ui/mount/unmount;
- manifest/Gateway/Compose dev-prod;
- full-page + global panel;
- F5/logout/deep route;
- media/biometric/external capability UI não ativa nada implicitamente;
- provider credentials nunca aparecem no MFE;
- Chat offline não quebra Copilot.

Required:

```text
COPILOT_API_OWN_RUNTIME=PASS
COPILOT_MFE_OWN_RUNTIME=PASS
NO_CHAT_IMPORT=PASS
NO_CHAT_API_DEP=PASS
NO_CHAT_DB_AUTHORITY=PASS
INDEPENDENT_DEPLOY_ROLLBACK=PASS
```

## 4. Gate C2 — Portal Context + Commands

- WorkspaceContext bounded/sanitized;
- EntityRefs operacionais;
- SourceRef externo sem token/credential;
- device/biometric/external context não concede permission;
- logout/user-switch limpa state local;
- authorized app/route/entity commands;
- arbitrary URL navigation rejeitada;
- iframe contract seguro;
- no JWT/secret em bridge;
- visual/DOM command não vira Business Action.

## 5. Gate C3 — Intelligence + Multimodal/Biometric/External Foundations

### Planner/Action/Expertise

- own conversation state;
- OpenAPI ingestion/versioning;
- known/sibling/unknown provider;
- metamorphic provider/path/opId;
- provider-neutral planner;
- expertise/playbook cannot grant permission;
- Knowledge ACL/provenance.

### Media/Biometric

- PDF/image/voice/video provenance;
- confidence/limitations;
- hostile content does not alter policy;
- voice parity with text;
- biometric enrolled/non-enrolled/look-alike/unknown/correction/revoke cases;
- biometric match cannot authenticate or grant permission;
- biometric templates absent from ordinary logs/responses;
- liveness/anti-spoof when required by policy;
- Human Observation remains process-grounded;
- no psychological/sensitive inference or automated employment decision.

### Internet Research

- search/fetch success and provider failure paths;
- only policy-approved public destinations are fetched;
- redirect remains subject to destination validation;
- type/size/time/concurrency budgets;
- hostile webpage content cannot modify system/policy or request secrets;
- sensitive internal context is not unnecessarily sent to search/fetch providers;
- SourceRef/EvidenceRef/freshness captured;
- conflicting/stale sources surfaced truthfully;
- public web does not silently override corporate authority.

### External Connection lifecycle

- connect/cancel/failure;
- callback/session integrity validation;
- required scope present/missing;
- scope increase requires a new authorized flow;
- refresh/revoke/expiry/reconnect;
- user-delegated connection isolated to its owner;
- org/shared/service connection follows explicit policy;
- provider token absent from LLM context, MFE payload and ordinary logs;
- unknown connector onboarding without planner patch.

## 6. Gate C4 — Business + External Reads + Graph

### Business reads

- auth/schema/timeout/error/freshness;
- normalized Outcome/Evidence;
- permission-aware Graph traversal;
- no master-data duplication.

### External reads

- read works only with required connection/scope;
- search/read do not imply modify/send;
- cross-user connection access blocked;
- not-connected/scope-missing/provider-unavailable/resource-not-found distinguished;
- external attachment follows safe download/type/size policy;
- SourceRef/EvidenceRef includes provider/resource/freshness without credential;
- revoked connection blocks subsequent read;
- personal source remains private unless explicitly shared/promoted.

## 7. Gate C5 — Governed Business/External Writes + Durable Foundation

### Decision/Business writes

- Decision Gate/revalidation;
- idempotency/concurrency;
- no blind write retry;
- ambiguous outcome verification;
- no duplicate effect after resume.

### External writes

- read-only scope cannot perform write;
- `draft != send`;
- generated content is not sent implicitly;
- target/recipient/payload preview when policy requires;
- connection/scope revalidated immediately before action;
- revocation between preview and execution blocks action;
- provider timeout does not cause blind duplicate send;
- verified provider outcome stored as Outcome/Evidence;
- provider-specific constraints remain inside adapter.

### Workflow

- DAG/checkpoint/waits;
- crash/restart/concurrent resume;
- duplicate internal/external event;
- permission/policy/connection changes while waiting;
- no duplicate business or external write.

## 8. Gate C6 — Product Work + Meeting/Frontline + External Events/Learning

### Task/Case/Room/Inbox

- source permission remains required;
- external source shared only when authorized;
- revoked connection/source sanitizes projections;
- reading an Inbox item never writes.

### Watch / provider events

- provider event authenticity validation;
- duplicate/out-of-order handling;
- subscription expiry/renewal;
- missed-event reconciliation/degraded state;
- revoked permission/connection;
- hostile event content cannot alter policy or trigger ungoverned write;
- ACT remains blocked in C6.

### Meeting/Frontline

- same RBAC/policy/Evidence as other surfaces;
- external live query uses active connection scopes;
- ata identifies internal/external sources when material;
- external candidate action still requires governance;
- internal procedure/revision remains authoritative over unrelated public content;
- biometric/shared-device/privacy/OT gates remain intact.

### External learning

- transient research may remain non-durable;
- durable external knowledge starts as candidate;
- provenance/freshness/privacy/licensing checked;
- personal mailbox/message/file never auto-promotes to organizational Knowledge;
- owner/review/eval/version/publish required where material.

## 9. Gate C7 — External Proactivity + Advanced Autonomy/Rollout

- L5 OFF by default;
- external ACT uses explicit connection/action allowlist, limits and kill switch;
- provider terms/scopes revalidated;
- proactive/background research respects egress/privacy budgets;
- browser fallback, if ever introduced, is sandboxed and bounded;
- browser automation cannot become an alternate ungoverned write path;
- model/media/external provider data-policy filtering;
- progressive rollout/canary/rollback;
- final Chat-offline independence.

## 10. Injection/safety transversal

Treat as untrusted:

```text
user prompt
voice transcript
RAG/tool/API result
WorkspaceContext
biometric/Human Observation result
public webpage/search result
external email/message/file/calendar item
external attachment
provider webhook/event payload
iframe/room/meeting/frontline content
```

Untrusted data never changes system policy, permissions, provider scopes, retention or safety boundaries.

## 11. Surface parity

Security/authorization semantics remain equivalent across:

```text
Global
Workspace
Meeting
Frontline
Internet Research
external connector read/write
Task/Case/Inbox
iframe contextual entry
admin preview/simulation
```

## 12. Anchor scenarios

### Cross-domain + external investigation

```text
Case
→ internal APIs/Graph
→ authorized external correspondence/files when relevant
→ public research when needed
→ Evidence Board
→ Expertise/Playbook
→ Workflow/Watch
→ governed business/external action
→ verified Outcome/Audit
→ Knowledge candidate
```

### External communication

```text
retrieve authorized thread
→ correlate DELPI data
→ draft
→ review/Decision Gate when required
→ provider send
→ verified outcome
→ Evidence/Audit
```

### Meeting

```text
meeting
→ explicit capture
→ internal/external grounded query
→ decisions/candidate actions
→ ata viva
→ governed follow-up
```

All scenarios work without Minha DELPI Chat runtime.

## 13. Release blockers

```text
CHAT_RUNTIME_IMPORT
CHAT_API_REQUIRED
CHAT_DATABASE_AUTHORITY
FOUNDATION_DUPLICATION
ARCHITECTURE_PATTERN_DRIFT
RBAC_LEAKAGE
WRITE_WITHOUT_REQUIRED_DECISION_GATE
RESUME_DUPLICATE_WRITE
HIDDEN_MEDIA_CAPTURE
UNDEFINED_MEDIA_RETENTION
SHARED_DEVICE_STATE_LEAK
BIOMETRIC_PERMISSION_ELEVATION
LOW_CONFIDENCE_FORCED_IDENTITY
BIOMETRIC_TEMPLATE_LEAK
SENSITIVE_PERSON_INFERENCE
AUTOMATIC_EMPLOYMENT_DECISION_FROM_BIOMETRICS
UNSAFE_WEB_EGRESS
EXTERNAL_PROMPT_INJECTION_POLICY_CHANGE
OAUTH_SCOPE_ESCALATION
PROVIDER_TOKEN_LEAK
CROSS_USER_EXTERNAL_DATA_LEAK
EXTERNAL_WRITE_WITHOUT_GATE
DRAFT_SENT_IMPLICITLY
UNVERIFIED_EXTERNAL_SUCCESS
INVALID_PROVIDER_EVENT_ACCEPTED
MISSED_EVENT_WITHOUT_RECONCILIATION
PERSONAL_SOURCE_AUTO_PROMOTED_TO_ORG_KNOWLEDGE
UNSUPPORTED_WHATSAPP_SESSION_AUTOMATION
ARBITRARY_LLM_OT_COMMAND
SAFETY_INTERLOCK_BYPASS
REQUIRED_TEST_FAIL_OR_INCONCLUSIVE
STALE_NONREPRODUCIBLE_EVIDENCE
```

## 14. Regra final

Qualquer gate REQUIRED em `FAIL | INCONCLUSIVE | PENDING | TEST_NOT_RUN | STALE_EVIDENCE` bloqueia a fase. Nunca enfraquecer teste para fazer candidate passar.
