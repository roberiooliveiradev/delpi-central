# DÉLIA — Modelo Canônico de Dados, Estado e Persistência

**Status:** `TARGET` arquitetural standalone  
**Autoridade de ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Requirements:** [`25-requirements-traceability.md`](./25-requirements-traceability.md)  
**Specs temáticas:** `53–66`

> Este documento define modelo alvo e candidatos. Nenhuma entidade, tabela, migration, registry, workflow ou state machine aqui descrita é considerada implementada sem evidência válida no HEAD/config correspondente.

## 1. Princípio

Todo estado durável pertence ao **owner correto**. A DÉLIA persiste somente state que possui ou projections/refs bounded necessários para continuidade, audit, search ou performance.

```text
CORPORATE IDENTITY / RBAC
→ Keycloak/Core

DOMAIN BUSINESS DATA
→ Domain APIs / ERP / MES / demais owners

EXTERNAL RESOURCES
→ external providers

OT / MACHINE TRUTH
→ industrial/domain owners

DÉLIA-OWNED STATE
→ conversation/intelligence/Evidence/Policy/Decision/Work/RecurringWork/memory/artifact/orchestration metadata only when owned

PHYSICAL SCHEDULER/TIMER STATE
→ platform/scheduler/execution owner provado em C0; não vira Work ou permission authority

AUTOMATION TECHNICAL EXECUTION STATE
→ Automation Hub / executor owner, quando implementation/contract forem provados

DERIVED PROJECTIONS/CACHES
→ invalidable, versioned, freshness-aware, never authority
```

Proibido criar shadow system of record apenas para facilitar IA.

## 2. Storage ownership

Freeze aceito C0.S1 (`PLANNED / FROZEN_ACCEPTED`; `ARCHITECTURE_REVIEW_C0_S1`, `REVIEWED_HEAD=c822f0e72495256c3459a4b36b9c37a3bba95cbb`):

```text
PERSISTENCE_OWNER = DÉLIA
LOGICAL_NAMESPACE = delia
MIGRATION_CHAIN = delia-api/migrations/   # CONDITIONAL — only when DÉLIA-owned persisted state exists
PHYSICAL_POSTGRES_CLUSTER = DEFER_PHYSICAL_PLACEMENT / TO_INVENTORY
```

C1-T6D1 Product Master: `OWN_MIGRATION_CHAIN = NOT_APPLICABLE_AT_C1` (no DÉLIA-owned persisted state introduced in C1). Empty scaffolding forbidden. First owned persistence task → REQUIRED → PASS with evidence (`52`§4).

```text
delia-api/migrations/   # own chain when applicable; only DÉLIA-owned state / bounded projections/refs
```

Histórico supersedido: `minha-delpi-copilot-api/migrations/`.

Proibido: Chat tables/migrations; Core tables; Domain tables; direct cross-context DB access.

Serviço separado só existe com boundary/owner/consumers reais e ADR. “Hub”, “Tower”, “Twin”, “Marketplace”, “Sandbox” ou “Scheduler” não justificam microservice por nome.

Segredos, biometric templates e alguns model/package artifacts podem pertencer a stores especializados; o DB transacional guarda refs/metadata, não secret material.

Recurring Governed Work pode justificar state DÉLIA-owned para **definição/lifecycle/correlation**, mas não autoriza duplicar a truth técnica de timer/job/lease/worker de um scheduler físico existente.

## 3. C0 antes de qualquer migration

Congelar:

- IDs/naming/versioning;
- classification/LGPD/retention/delete/export;
- encryption/key/secret owners;
- user/service/device identity refs;
- source authority/freshness;
- idempotency/concurrency;
- migration/rollback;
- DÉLIA-owned state vs projection/ref vs physical scheduler vs Automation Hub technical state;
- recurrence/timezone/DST/misfire/overlap semantics antes de RecurringWork migration;
- background identity/AuthZ/revoke semantics por ocorrência;
- cache TTL/invalidation;
- audit/evidence lineage;
- state-machine transitions;
- data classes novas somente se shared primitives existentes forem insuficientes.

## 4. Shared foundations — C0.S3 shared/reference semantics freeze accepted

```text
STATUS = FROZEN_ACCEPTED
REVIEW = ARCHITECTURE_REVIEW_C0_S3
REVIEWED_HEAD = 641ffc07284b98ffbdb5e13217ce214c4ad8ebb0
VERDICT = ACCEPT_WITH_RESIDUAL
C0.S0..C0.S3 = APPROVED
AUTHORITY_MAP = FROZEN_ACCEPTED
BOUNDED_CONTEXT_MAP = FROZEN_ACCEPTED
SHARED_REFERENCE_SEMANTICS = FROZEN_ACCEPTED
C0.S4_AUTHORIZED = YES
C0.S4 = APPROVED (see §4A)
ARCHITECTURE_PERSISTENCE_PRIVACY_SAFETY = FROZEN_ACCEPTED (see §4A)
C0.S5 = APPROVED (see 17 §22)
INTEGRATION_CONTRACTS = FROZEN_ACCEPTED
C0.S6_AUTHORIZED = YES
NEW_RUNTIME_ABSTRACTIONS = NONE
FOUNDATION_FREEZE = NOT APPROVED
DÉLIA_RUNTIME_DIFF = NONE
NOTE_SUPERSEDED_BY_C0_S7_T2: FOUNDATION_FREEZE current-state is APPROVED; this block records C0.S3 review-time fields only
```

C0.S3 congela **semântica de referência compartilhada**. Não cria código, classes, tabelas, migrations, endpoints ou services. Field sketches abaixo permanecem `TARGET` de contrato (C0.S5), não schema implementado. C0.S3 **não** decide timezone/DST/misfire/overlap/retry/background AuthZ/scheduler implementation.

### 4.0 Decision summary

#### REUSED_EXISTING_PRIMITIVES

| Primitive | Semantics | Must NOT become |
|---|---|---|
| CorrelationContext | correlation only | authority |
| EntityRef | typed ref to business object | authorization / business authority |
| UserRef | identity reference | permission snapshot |
| ServiceActorRef | explicit service/background actor identity | permission grant |
| DeviceRef | device identity | user identity / authorization |
| SourceRef | source/origin reference | source authority itself / source access |
| EvidenceRef | Evidence reference | SoT / authorization |
| OutcomeRef | verified business-outcome reference | technical executor success |
| EventEnvelope | normalized event envelope | permission / command / proof of EventBus |

Also reuse when already justified by prior authorities: `RelationshipRef`, `TaskRef`/`CaseRef`, `DecisionGateRequest/Decision`, `WorkflowPlan/WorkflowStep`, `AuditEvent` — sem promover meta-abstrações novas.

#### CapabilityProjection = PROJECTION_ONLY

Authorized semantic projection for DÉLIA capability discovery/planning.

Must NOT become: permission authority · business authority · technical executor registry authority · provider/tool metadata authority · Automation Hub technical SoT.

Technical resolution remains with canonical source / adapter / executor owner.

#### ACCEPTED_SHARED_PRIMITIVES (architectural refs only)

| Primitive | Min semantic identity | Core rules | Primary CPs |
|---|---|---|---|
| MetricDefinitionRef | metricId, version (+ namespace/scope?, ownerRef?) | ≠ metric/business authority; ≠ data access permission; formula stays with governed owner | CP-275, CP-276, CP-277 |
| ArtifactRef | artifactId, version (+ artifactType?, ownerRef?) | ≠ publication approval; ≠ automatic SoT; ≠ ACL grant; URL/path ≠ semantic authority | CP-283, CP-284 |
| PredictionRef | prediction id + ModelRef/version + subject EntityRef(s) + target + horizon + freshness | Prediction≠FACT; ≠permission; ≠autonomous ACT | CP-288, CP-289, CP-293 |
| ScenarioRef | isolated scenario/branch id | Scenario≠production; Twin≠SoT; SIMULATE≠APPLY; never authorizes production mutation | CP-291, CP-292, CP-294 |
| AutomationExecutionRef | executionId, executionOwnerRef (+ capabilityRef?, externalExecutionRef?) | Work≠AutomationExecution; ≠business Outcome; SUCCEEDED≠verified success; no duplicate Hub tech truth | CP-235–237, CP-239 |
| RecurringWorkRef | recurringWorkId, version | ≠scheduler job; schedule≠permission; stored intent≠permanent AuthZ; scheduler owner separate | CP-312, CP-314, CP-316 |
| WorkOccurrenceRef | occurrenceId, recurringWorkRef, scheduledFor | ≠timer tick; ≠scheduler job; ≠permission; trigger≠Outcome | CP-313, CP-315 |
| ModelRef | modelId, version, ownerRef (+ providerRef?, family?) | ≠model approval; ≠permission; ≠Decision authority; router≠approval | CP-288, CP-303, CP-304, CP-307 |

C0.S3 **não** decide timezone/DST/misfire/overlap/retry/background AuthZ/scheduler implementation (C0.S4/C0.S5).

#### NOT PROMOTED

| Item | Classification | Reason |
|---|---|---|
| ProcessTraceRef | REFERENCE_ONLY | typed process trace needed; no universal shared lifecycle yet; no generic process master | CP-250, CP-251 |
| MemoryItemRef | DOMAIN_LOCAL_ONLY (DÉLIA Personal Memory) | user-scoped/privacy; ≠Org Knowledge/Conversation/Workspace; no cross-boundary foundation need | CP-269–271 |
| AnalysisRunRef | REJECT_ABSTRACTION (shared) | use CorrelationContext.analysisRunId + SourceRef/EvidenceRef + ArtifactRef | CP-281, CP-282 |
| ExecutorRef | CLOSED_NONISSUE (C0.S5) | Do not promote shared ExecutorRef; use contract-local executionOwnerRef/executorClass; AutomationExecutionRef suffices | CP-235, CP-236, CP-238 |
| AIAssetRef | PROJECTION_ONLY; detail DEFER_BY_PHASE | Tower/Marketplace may project later; ≠permission; not global authority foundation | CP-257, CP-258, CP-305, CP-310 |
| EdgeDeviceRef | REUSE_EXISTING → DeviceRef | do not create separate EdgeDeviceRef; device≠user≠AuthZ | CP-171, CP-296, CP-298 |

#### REJECTED generic meta-abstractions

```text
UniversalRef
GenericBusinessObjectRef
GenericExecutionObject
GenericAIObject
GenericAssetRef
```

Forbidden unless future Abstraction Gate with real consumers proves need.

#### WorkspaceContext

`FROZEN_CANDIDATE` shape in `17` §22 (C0.S5-T2). May reuse EntityRef/SourceRef/DeviceRef and bounded Work/Artifact refs when justified. WorkspaceContext ≠ authorization ≠ SoT ≠ JWT/secret carrier. Not a runtime DTO.

#### Field sketches below

Subsections 4.x seguintes são sketches `TARGET` de conteúdo — **não** implementação e **não** promoção de candidates rejeitados acima.

### CorrelationContext

```text
requestId
conversationId?
turnId?
workflowId?
taskId?
caseId?
watchId?
recurringWorkId?
occurrenceId?
eventId?
executionId?
analysisRunId?
scenarioId?
meetingId?
frontlineSessionId?
traceId?
```

### EntityRef

```text
entityType
entityId
sourceSystem/domain
label?
version/revision?
```

### UserRef / ServiceActorRef / DeviceRef

- `UserRef` aponta para Keycloak/Core.
- background action usa service/user identity explícita.
- `DeviceRef` não é usuário.
- biometric candidate não é usuário autenticado.
- RPA worker não é business actor.
- scheduler/timer identity não é business actor nem permission authority.

### SourceRef / EvidenceRef / OutcomeRef

Usados transversalmente por APIs, web, connectors, Process Intelligence, analysis, predictive/twin, automation, Recurring Work, Meeting/Frontline e audit quando os contracts forem congelados.

Nunca guardar credential em Source/Evidence/Outcome.

## 4B. C3-T1 — Evidence / epistemic semantics + source linkage

```text
STATUS = FROZEN_ACCEPTED
REVIEW = ARCHITECTURE_REVIEW_C3_T1
REVIEWED_CANDIDATE_HEAD = fb5d63914511728b4c2546b5421da5071f0cb7c4
REVIEW_REANCHOR_HEAD = 8634cca98cb285114d7494aa0d6b264bab8f0b2a
VERDICT = ACCEPT_WITH_RESIDUAL
TASK = C3-T1
C3_T1 = APPROVED
EVIDENCE_EPISTEMIC_SEMANTICS = FROZEN_ACCEPTED
SOURCE_LINKAGE_SEMANTICS = FROZEN_ACCEPTED
MODE = DOCUMENTATION / CONTRACT FREEZE ONLY
RUNTIME = NONE
PERSISTENCE = NONE
OWN_MIGRATION_CHAIN = NOT_TRIGGERED_BY_C3_T1
C0_SHARED_REFERENCE_SEMANTICS = FROZEN_ACCEPTED (reused; not redesigned)
NO_PARALLEL_PRIMITIVE = YES
NEW_RUNTIME_ABSTRACTIONS = NONE
C3_STARTED = YES
C3_EXECUTED = NO
C3_T2_AUTHORIZED = YES
C3_T2 = APPROVED
PRODUCTION_READINESS = NOT_PROVEN
THEMATIC_OWNER_DETAIL = 38-evidence-provenance-and-epistemic-ux.md
FACT_STATUS != ACCESS_PERMISSION
NOTE_SUPERSEDED_CANDIDATE: historical C3-T1 candidate markers live in ledger §6.62
C3_T2_IMPLEMENTATION = delia-api/app/domain/evidence/ (C3-T2R1 APPROVED; IMPLEMENTATION_HEAD=d444e75f7; no store)
REVIEW = ARCHITECTURE_REVIEW_C3_T2R1
VERDICT = ACCEPT_WITH_RESIDUAL
NOTE_C3_T2R1: total epistemic ordering removed; TypedResultKind sole discriminator;
  SourceRef identity-only; source authority = FactQualificationCriteria input
BLOCKER_1_TOTAL_EPISTEMIC_ORDERING = RESOLVED
BLOCKER_2_TYPED_RESULT_DUPLICATION = RESOLVED
BLOCKER_3_SOURCE_REF_AUTHORITY = RESOLVED
C3_T3_AUTHORIZED = YES
C3_T3_EXECUTED = NO
C3_T3 = APPROVED
C3_T3_IMPLEMENTATION = delia-api/app/domain/model_invocation/ + application/model_invocation/ (no store; no real provider)
C3_T4_AUTHORIZED = YES
C3_T4 = APPROVED
C3_T4_IMPLEMENTATION = delia-api/app/domain/structured_understanding/ + application/structured_understanding/
C3_T5_AUTHORIZED = YES
C3_T5_EXECUTED = NO
C3_T5 = APPROVED
C3_T6_AUTHORIZED = YES
C3_T6 = APPROVED
C3_T7_AUTHORIZED = YES
C3_T7_EXECUTED = NO
REVIEW = ARCHITECTURE_REVIEW_C3_T3R1
VERDICT_C3_T3 = ACCEPT_WITH_RESIDUAL
REVIEW_C3_T4 = ARCHITECTURE_REVIEW_C3_T4R1
VERDICT_C3_T4 = ACCEPT_WITH_RESIDUAL
REVIEW_C3_T5 = ARCHITECTURE_REVIEW_C3_T5
VERDICT_C3_T5 = ACCEPT_WITH_RESIDUAL
REVIEW_C3_T6 = ARCHITECTURE_REVIEW_C3_T6R1
VERDICT_C3_T6 = ACCEPT_WITH_RESIDUAL
FABRICATED_EVAL_PASS = RESOLVED
REAL_DELPI_OPENAPI_COVERAGE = NOT_PROVEN
EXPERTISE_FOUNDATION = IMPLEMENTED (delia-api/app/domain/expertise/)
KNOWLEDGE_GOVERNANCE_FOUNDATION = IMPLEMENTED (delia-api/app/domain/knowledge/)
EXPERTISE_EVIDENCE_REF_TYPING = PASS / EvidenceRef
KNOWLEDGE_SCOPE = REMOVED
RETRIEVAL_INCLUDE_FLAGS = REMOVED
NORMAL_RETRIEVAL_SCOPE = PUBLISHED_ORGANIZATIONAL_KNOWLEDGE_ONLY
RETRIEVAL_PORT = DEFERRED
```

C3-T1 congela o **uso semântico** de Evidence/Source/epistemic para a inteligência futura. Não cria Evidence store, repository, schema, LLM, RAG, planner ou conversation runtime. C3-T2R1 domain model/tests foram aceitos por `ARCHITECTURE_REVIEW_C3_T2R1` (`ACCEPT_WITH_RESIDUAL`; `C3_T2=APPROVED`). C3-T3 foundation aceita por `ARCHITECTURE_REVIEW_C3_T3R1` (`ACCEPT_WITH_RESIDUAL`; `C3_T3=APPROVED`). C3-T4 Structured Understanding aceito por `ARCHITECTURE_REVIEW_C3_T4R1` (`ACCEPT_WITH_RESIDUAL`; `C3_T4=APPROVED`; `BOUNDED_SOURCE_OBSERVATION_EXTRACTION`); C3-T5 OpenAPI/CapabilityProjection aceito por `ARCHITECTURE_REVIEW_C3_T5` (`ACCEPT_WITH_RESIDUAL`; `C3_T5=APPROVED`; `REAL_DELPI_OPENAPI_COVERAGE=NOT_PROVEN`); C3-T6 Expertise/Knowledge governance + retrieval contracts aceito por `ARCHITECTURE_REVIEW_C3_T6R1` (`ACCEPT_WITH_RESIDUAL`; `C3_T6=APPROVED`; published-only retrieval; no physical store / RAG / RetrievalPort); store/RAG/planner/conversation/real provider remain out of scope; C3_T7_AUTHORIZED=YES.

### 4C. C3-T3 — Model invocation / eval lineage

```text
STATUS = APPROVED
REVIEW = ARCHITECTURE_REVIEW_C3_T3R1
VERDICT = ACCEPT_WITH_RESIDUAL
OWNER = DÉLIA (delia-api domain/application)
REUSES = ModelRef (C0.S3; no ModelIdentity duplicate)
PORT = ModelInvocationPort
LINEAGE = ModelInvocationLineage (invocation id + ModelRef + EvidenceRef[] + SourceRef[] + instruction/config identity + optional EvalIdentity)
EVAL_BINDING = EvalBindRequest → EvalIdentity only
EVAL_IDENTITY = evaluation-target identity / binding (≠ execution; ≠ evidence; ≠ outcome; ≠ PASS; ≠ authority; ≠ permission)
target_sha = identity of the software/code target an evaluation identity refers to
target_sha != proof evaluation ran / != evidence / != PASS
EVAL_RESULT = separate C3-local contract (ACCEPT_WITH_RESIDUAL)
EVAL_RESULT_OWNERSHIP = EXPLICIT_EVALUATION_OPERATION_OR_PROCESS
ModelInvocationResult != EvalResult (no eval_result field; no fabricated PASS)
FABRICATED_EVAL_PASS = RESOLVED
DEFAULT_MODEL_OUTPUT_CLASS = HYPOTHESIS
MODEL_OUTPUT != FACT automatically
LINEAGE != AUTHORIZATION
RECOMMENDATION != ACT
REAL_PROVIDER = BLOCKED_BY_EXTERNAL_CONFIGURATION
REAL_MODEL_EVAL = TEST_NOT_RUN / BLOCKED
EXPOSURE_GATE = ACCEPTABLE_TEMPORARY_FAIL_CLOSED (TEST_ONLY)
PERSISTENCE = NONE
```

C3-T3 does not persist invocations, does not call a real provider, and does not materialize EvidenceItem from model output.

### 4D. C3-T4 — Structured Understanding (APPROVED)

```text
STATUS = APPROVED
REVIEW = ARCHITECTURE_REVIEW_C3_T4R1
REVIEWED_IMPLEMENTATION_HEAD = 89bb5ad352b134ac6f8558c829a7f8720bc920d6
VERDICT = ACCEPT_WITH_RESIDUAL
PRIOR_BLOCKER_CALLER_EPISTEMIC_SELECTOR = RESOLVED
PRIOR_BLOCKER_PROVENANCE_OVERCLAIM = RESOLVED
PRIOR_BLOCKER_CONFIDENCE_CONTRACT = RESOLVED
BLOCKERS = NONE
SLICE = BOUNDED_SOURCE_OBSERVATION_EXTRACTION
STRUCTURED_UNDERSTANDING_BOUNDARY = ACCEPT
OWNER = DÉLIA (delia-api domain/application structured_understanding)
USE_CASE = UnderstandStructuredInput
REUSES = InvokeModel + ModelInvocationLineage + EpistemicClass + EvidenceRef/SourceRef/ModelRef
CONTENT = StructuredObservation[] (source-content OBSERVATION only)
OUTPUT_EPISTEMIC_CLASS = OBSERVATION_BY_CAPABILITY_CONTRACT
declared_result_epistemic_class = REMOVED
StructuredUnderstandingRequest has no declared_result_epistemic_class
StructuredUnderstandingResult has no confidence
StructuredObservation.source_ref = singular exact bounded SourceRef
StructuredObservation.evidence_refs = REMOVED
SOURCE_INPUT_CARDINALITY = EXACTLY_ONE SourceRef (0/N fail closed)
OBSERVATION_SOURCE_LINKAGE = SINGULAR_BOUNDED_SOURCE
OBSERVATION_EVIDENCE_LINKAGE = NONE_BY_DESIGN
EvidenceRef[] = request/result/invocation-lineage context only (!= per-observation support)
PROVENANCE_MODEL = ACCEPT
CONFIDENCE = REMOVED / DEFERRED
OUTPUT_SCHEMA_MODEL = ACCEPT (schema_id=c3t4.source_observation_extraction; schema_version=1; SchemaRegistry=NOT REQUIRED)
SOURCE_OBSERVATION != WORLD_FACT
MODEL_OUTPUT_AUTO_FACT = NO
FACT qualification remains outside this capability
CLAIM_PROPOSITION_MODEL = DEFERRED
ENTITY_EXTRACTION_BOUNDARY = DEFERRED
RELATIONSHIP_BOUNDARY = DEFERRED
REAL_PROVIDER = BLOCKED_BY_EXTERNAL_CONFIGURATION
REAL_MODEL_STRUCTURED_UNDERSTANDING_QUALITY = TEST_NOT_RUN / BLOCKED
PERSISTENCE = NONE
C3_T5_AUTHORIZED = YES
C3_T5_EXECUTED = NO
C3_T5 = APPROVED
C3_T6_AUTHORIZED = YES
C3_T6 = APPROVED
C3_T7_AUTHORIZED = YES
C3_T7_EXECUTED = NO
NOTE_SUPERSEDED_CANDIDATE: historical candidate/rework markers live in ledger §6.70–§6.71 / §6.74–§6.75
```

### 4B.1 Ownership

```text
RESPONSIBILITY: Evidence coordination + epistemic semantics + synthesis constraints
OWNER: DÉLIA (coordination/intelligence)
CANONICAL SOURCE OF ORIGINAL FACT: Domain API / provider / document owner / process owner
CONSUMERS (future): multimodal, Evidence Board, Internet Research, connectors, Teams,
  Process Intelligence, Prediction, Model lineage, Knowledge, planner, synthesis
CONTRACT: this §4B + C0.S3 SourceRef/EvidenceRef/ModelRef/PredictionRef + thematic 38
CURRENT IMPLEMENTATION: C3-T2 APPROVED (ARCHITECTURE_REVIEW_C3_T2R1 ACCEPT_WITH_RESIDUAL;
  IMPLEMENTATION_HEAD=d444e75f735fa78524efa4099c7e1695ff1637ec) — domain model + conformance in delia-api/app/domain/evidence/
  (no Evidence store / repository / LLM / RAG / planner / conversation;
   SourceRef identity-only; TypedResultKind sole typed-result discriminator;
   no global EpistemicClass numeric ordering;
   _EPISTEMIC_STRENGTH / epistemically_weaker / SourceAuthorityCapability = REJECTED/REMOVED)
```

```text
Evidence != source authority
EvidenceRef != permission
SourceRef != source-access grant
citation/reference != permission
epistemic class != authorization
confidence != authority
confidence != permission
FACT_STATUS != ACCESS_PERMISSION
```

### 4B.1A Epistemic qualification vs access authorization

```text
EPISTEMIC QUALIFICATION
= "What is the epistemic status of this proposition?"
  (source authority, provenance, source contract, validation,
   freshness/version, method, limitations, derivation lineage)

ACCESS / AUTHORIZATION
= "May the current actor obtain, dereference, disclose or use
   this protected source/evidence in this operation?"
  (identity, Core effective RBAC, Domain final business AuthZ,
   provider/source ACL, Policy/Decision, current operation/context)
```

```text
permission does not establish epistemic truth
epistemic truth does not grant permission
loss of access does not retroactively make a true proposition false
having source read permission does not make source content FACT
EvidenceRef does not carry permission
SourceRef does not carry permission
epistemic class does not carry permission
confidence does not carry authority
confidence does not carry permission
```

Any current operation that obtains, dereferences, discloses or uses protected source/evidence MUST perform applicable live authorization/access checks. FACT does not bypass ACL/RBAC and does not automatically grant access.

### 4B.2 Shared refs reused (no redesign)

```text
SourceRef     → identifiable origin; not invented authority; not access grant
EvidenceRef   → Evidence item reference; not SoT; not authorization
EntityRef     → typed business object; not authorization
ModelRef      → model identity/version/owner; not approval; not Decision authority
PredictionRef → prediction identity + ModelRef + subject/horizon/freshness; Prediction≠FACT
OutcomeRef    → verified business outcome; ≠ technical executor success
```

Forbidden: UniversalSource, GenericEvidenceObject, EpistemicEnvelope, parallel EvidenceRef/SourceRef.

### 4B.3 What qualifies as Evidence

Evidence is a **coordinated claim about the world** that points, when the source allows, to verifiable provenance. It is not the source system of truth and does not copy ownership of the underlying fact to DÉLIA.

Minimum semantic linkage for a material Evidence item:

```text
EvidenceRef
→ SourceRef (when an identifiable origin exists)
→ epistemic class
→ freshness / version / limitations when material
→ EntityRef[] when the claim is about typed entities
→ ModelRef / PredictionRef when the item is model-generated or a prediction
→ derivedFrom EvidenceRef[] when derived from other Evidence
```

A retrieval hit, citation string, summary, or model utterance is **not** Evidence automatically.

### 4B.4 Epistemic classes (canonical)

Canonical classes:

```text
OBSERVATION    → content directly captured, extracted or recorded from a source/input,
                 with known provenance of the observation, but whose proposition about
                 the world has not yet been qualified as FACT under applicable
                 source-authority / validation semantics
FACT           → proposition qualified as FACT under source authority + provenance +
                 source-contract/validation + sufficient freshness/version (explicit class)
CALCULATION    → derived by an identifiable method from inputs
HYPOTHESIS     → possible explanation not confirmed
CONCLUSION     → inference supported by sufficient Evidence
RECOMMENDATION → suggested action; never authorization
```

```text
OBSERVATION != FACT
OBSERVATION != authorization
NO automatic OBSERVATION → FACT promotion
```

Examples of OBSERVATION (non-exhaustive): OCR extraction, VLM extraction, detected region/object, document statement, sensor-reported reading, user-provided statement.

Separate typed results (not epistemic-class enum members):

```text
PREDICTION   → PredictionRef contract; Prediction ≠ FACT
SIMULATION   → ScenarioRef / Twin; SIMULATE ≠ APPLY; not current FACT
```

Freshness / board states (not epistemic class enum replacements):

```text
current/live | snapshot | cached-valid | stale | unknown   (38 §5)
accepted | contested | missing | superseded                 (Evidence Board; 38 §9)
```

Unvalidated OCR/VLM/extraction defaults to **OBSERVATION** (non-FACT) with limitations until appropriate contextualization/validation.

### 4B.5 Default epistemic treatment

| Input kind | Default treatment | May become FACT only if |
|---|---|---|
| Authoritative Domain/API response | FACT candidate when that Domain/API is authoritative for the proposition | provenance valid; freshness/version sufficient; source-contract semantics support the proposition (access to obtain/use the response is a separate AuthZ concern) |
| External webpage/content claim | untrusted content; often OBSERVATION / Evidence candidate; not FACT | Domain/Policy later validates against an authoritative source |
| Retrieved Knowledge content | Knowledge candidate / reference | published Organizational Knowledge gates pass (owner/version/ACL/review) |
| Document / OCR / vision extraction | OBSERVATION with limitations | validated against authoritative context/method (no automatic promotion) |
| Model inference / free-form generation | non-FACT (HYPOTHESIS/CONCLUSION/RECOMMENDATION as labeled) | never automatic; never from confidence alone |
| Classification / forecast | non-FACT / PREDICTION as applicable | PredictionRef rules; never silent FACT |
| Recommendation | RECOMMENDATION | never authorization |
| Cached / stale material | stale/unknown limitation required when currency matters | only if source contract says cached-valid |
| User statement | OBSERVATION / Personal Memory class as applicable; not Domain FACT | explicit user-confirmed personal class is Personal Memory, not Org FACT |
| Derived synthesis | preserves relevant uncertainty, limitations, provenance constraints and unsupported premises + lineage; EpistemicClass values are semantic kinds and do **not** define a single global numeric strength ordering | only if promotion rules below are met (never silent FACT) |

### 4B.6 FACT promotion rules

Required before treating a result as FACT (epistemic qualification):

```text
1. identifiable source / provenance (SourceRef or Domain-owned live contract equivalent)
2. source capable of being authoritative for the proposition
3. applicable validation / source-contract semantics
4. sufficient freshness/version for the decision being made
5. epistemic class explicitly FACT (not inferred from confidence or permission)
6. preserved limitations/lineage where material
7. no secret/token stored in Evidence or model context
```

Separately, any current operation that obtains, dereferences, discloses or uses protected source/evidence MUST perform applicable live authorization/access checks. Current-user AuthZ does **not** determine epistemic truth; FACT does not bypass ACL/RBAC.

Never silently promote to FACT:

```text
model output
retrieval hit
citation alone
confidence score
external page claim
OCR/VLM raw extraction (defaults to OBSERVATION)
OBSERVATION (no automatic OBSERVATION → FACT)
Prediction / Prescription
Recommendation
simulation / scenario output
Personal Memory item
summary / synthesis without lineage
Knowledge candidate (unpublished)
technical executor success
provider metadata
```

### 4B.7 Unknown / missing / conflict

```text
missing evidence != false
no search result != proof of absence
unknown identity != guessed identity
insufficient evidence != negative fact
conflicting evidence != fabricated reconciliation
```

When sources disagree: keep each item's provenance, epistemic class, freshness/version, source authority and limitations explicit. Do not auto-pick newest, highest confidence, model-preferred or most-retrieved unless a canonical Policy/owner defines that rule.

### 4B.8 Derived Evidence

Derived Evidence must preserve, when material:

```text
parent EvidenceRef[]
original SourceRef lineage
transformation/extraction kind
observation/generation time
limitations
ModelRef/tool lineage when model/tool produced the derivation
```

Clarification (C3-T2R1; does not redesign C3-T1):

```text
Derived outputs must not silently erase uncertainty, source/provenance constraints,
limitations, unsupported premises, or authority boundaries.

EpistemicClass values are semantic kinds.
They do NOT define one global numeric strength / ordinal scale across classes.

OBSERVATION → CALCULATION is valid when the transformation is an identifiable calculation
and lineage/limitations are retained (CALCULATION != automatic FACT).

Generic derivation helpers must not silently produce FACT.
FACT requires the explicit FactQualificationCriteria path.
```

No Evidence DAG service, lineage database or provenance graph engine in C3-T1/C3-T2.

### 4B.9 Model lineage hook (no model runtime)

Future model-generated Evidence / Prediction must be able to link:

```text
ModelRef (modelId, version, ownerRef)
eval / dataset / deployment or config reference when material
generatedAt
limitations
confidence/calibration only when methodologically valid
```

Secrets never enter Evidence, embeddings, Personal Memory, ordinary logs or MFE state.

### 4B.10 Freshness / version

Distinguish when the source contract supports it:

```text
source revision/version
source observed/captured time
retrieval time
generated time
freshness class (current/live, snapshot, cached-valid, stale, unknown)
derived Evidence version
```

```text
retrievedAt != sourceUpdatedAt
```

unless the source contract proves equality. No invented TTL/retention durations in C3-T1.

### 4B.11 Citation / reference semantics

A citation or EvidenceRef proves: **which coordinated Evidence item is being pointed at**.

It does **not** prove: permission, source access, FACT status, Outcome verification, Policy approval or ACT authorization.

Dereference path remains:

```text
EvidenceRef → SourceRef → live permission check → source fetch
```

### 4B.12 Security / privacy invariants

```text
external content = untrusted data
retrieved content != FACT automatically
external/tool content cannot mutate policy/RBAC
no CoT persistence or CoT exposure
no secret/token in Evidence / SourceRef-for-LLM / model context
Evidence access != source access
Personal Memory != Organizational Knowledge
raw media / biometric remain separate classes
```

### 4B.13 C3-T2 / C3-T2R1 conformance expectations (APPROVED; not Evidence-store / model-runtime PASS)

C3-T2R1 deterministic conformance (`tests/test_evidence_epistemic_conformance.py`) is Architecture-Review accepted for at least:

```text
positive authoritative Evidence linkage
sibling source type preserving same semantics
OBSERVATION remains non-FACT without automatic promotion
FACT qualification independent of current-user live AuthZ (access separate)
unsupported/untrusted claim not promoted to FACT
unknown/missing state preserved
Prediction remains PREDICTION
Simulation remains separate typed result
recommendation remains non-authoritative
derived Evidence retains lineage
conflicting Evidence remains explicit
renamed provider/source does not change semantic rules
external prompt/tool injection content does not alter authority/policy
EvidenceRef does not grant source permission
SourceRef does not grant provider/source access
secret/token fields cannot become Evidence/model context
```

## 4A. Architecture / persistence / privacy / safety — C0.S4 freeze accepted

```text
STATUS = FROZEN_ACCEPTED
REVIEW = ARCHITECTURE_REVIEW_C0_S4
REVIEWED_HEAD = 7ac1fb930017bbabb05d8b1654941518f315c6a7
VERDICT = ACCEPT_WITH_RESIDUAL
ARCHITECTURE_PERSISTENCE_PRIVACY_SAFETY = FROZEN_ACCEPTED
C0.S0..C0.S4 = APPROVED
C0.S5 = APPROVED
INTEGRATION_CONTRACTS = FROZEN_ACCEPTED (see 17 §22)
C0.S6 = APPROVED
RED_CONTRACT_CONFORMANCE_PRIVACY_SECURITY_HARNESS = FROZEN_ACCEPTED (see 20)
C0.S7 = APPROVED
FOUNDATION_FREEZE = APPROVED
C1_AUTHORIZED = YES
C1_STARTED = YES
C1_EXECUTED = NO
AUTHORITY_MAP = FROZEN_ACCEPTED
BOUNDED_CONTEXT_MAP = FROZEN_ACCEPTED
SHARED_REFERENCE_SEMANTICS = FROZEN_ACCEPTED
NEW_RUNTIME_ABSTRACTIONS = NONE
PROGRAM = PLANNED / NOT_STARTED
C0 = NOT_STARTED
RUNTIME_READINESS = NOT_PROVEN
PRODUCTION_READINESS = NOT_PROVEN
NEW_BEHAVIORAL_TESTS = TEST_NOT_RUN
FUTURE_C1_C7_GREEN_EVIDENCE_REQUIRED = YES
DÉLIA_RUNTIME_DIFF = delia-api skeleton + /health
NEXT = C1-T2 — JWT + CORE EFFECTIVE ACCESS INTEGRATION
```

C0.S4 congela **regras arquiteturais** de ownership de persistência, classificação, privacy, secrets/encryption, concorrência/idempotência, state machines, identidade background, segurança temporal de Recurring Work, Evidence/Outcome, Prediction/Scenario/Twin, biometric/media, conexões externas, audit/eval, Process/Task Mining, Sandbox/Artifact, Model/Marketplace/Tower, Edge/offline, OT/safety, falha/recovery e cache/projection.

Não cria código, tabelas, migrations, endpoints, services, vault, scheduler, event bus, Policy engine, SecretRef shared primitive ou OT control layer. Contratos tipados detalhados = C0.S5. Foundation Freeze accepted = C0.S7 (`APPROVED`; runtime still `NOT_PROVEN`).

### 4A.1 Persistence ownership

DÉLIA **may** persist only:

```text
DÉLIA-owned lifecycle/state
bounded refs
bounded projections/caches
Evidence/Decision/Policy/Work/Outcome coordination metadata
user-scoped Personal Memory (when lifecycle exists)
governed Knowledge/Artifact/Prediction/Scenario metadata when owned
```

DÉLIA **must NOT** duplicate:

```text
Domain business truth
Core RBAC truth
Automation Hub technical execution truth
physical scheduler/timer/job/lease truth
OT/safety truth
```

```text
Reference != ownership
Projection/cache != authority
```

### 4A.2 Physical PostgreSQL

```text
PERSISTENCE_OWNER = DÉLIA
LOGICAL_NAMESPACE = delia
MIGRATION_ROOT = delia-api/migrations/
PHYSICAL_POSTGRES_CLUSTER = DEFER_PHYSICAL_PLACEMENT / TO_INVENTORY
```

Do **not** select shared schema/database/cluster without evidence for: owner, isolation, HA, backup/restore, security, networking, migration independence, rollback, capacity, blast radius, classification.

### 4A.3 Data classification (architectural)

Practical classes (may overlap; **most restrictive** applicable governance wins):

```text
PUBLIC_EXTERNAL
INTERNAL_OPERATIONAL
CONFIDENTIAL_BUSINESS
PERSONAL_DATA
SENSITIVE_PERSONAL_DATA
BIOMETRIC_DATA
AUTHENTICATION_DATA
SECRET_CREDENTIAL
MEDIA_RAW
TRANSCRIPT
DERIVED_AI_OUTPUT
EVIDENCE
AUDIT_SECURITY
MODEL_ASSET
DEVICE_EDGE_DATA
OT_OPERATIONAL_DATA
```

For each class, freeze architectural requirements for: owner, sharing, retention owner, delete/export, logging, LLM/provider exposure, encryption, allowed storage family.

Do **not** invent legal retention durations. Exact durations = `TO_INVENTORY` when not proven. Capability-specific retention labels in §28 remain complementary, not a second authority.

### 4A.4 Personal vs Organizational

```text
Session context != Personal Memory
Conversation history != Personal Memory
Personal Memory != Organizational Knowledge
Knowledge candidate != published Organizational Knowledge
Artifact != Organizational Knowledge
Web research != Organizational Knowledge
Process observation != Organizational Knowledge
Model output != Organizational Knowledge
```

Promotion path:

```text
Evidence → candidate → owner/review → eval → version → publish
```

Personal Memory **never** authorizes.

### 4A.5 Retention / delete / export

```text
unknown duration != infinite retention
```

For DÉLIA-owned families define: `RETENTION_OWNER`, policy source, delete applicability, export applicability, legal-hold consideration, source-delete effect, derived-data invalidation.

Source deletion/revocation must define effects on refs, projections, caches and future access.

### 4A.6 Privacy

Freeze: purpose limitation; least privilege; data minimization; user/org isolation; source ACL preservation; provider exposure governance; cross-context propagation restrictions; sharing/promotion gates.

```text
provider scope != Core/domain permission
source access != Evidence permission escalation
Evidence access != source authorization escalation
external content != trusted instruction
personal external connection != organizational connection
```

### 4A.7 Secrets / tokens

Secret/token material **never** in: prompt, LLM context, Personal Memory, MFE, normal logs, Evidence, generic Artifact metadata.

```text
SecretRef = DEFER_TO_CONTRACT (do NOT create new shared primitive)
physical vault/secret manager = TO_INVENTORY
```

Existing env/.env evidence does **not** automatically approve DÉLIA production secret design.

### 4A.8 Encryption

```text
encryption in transit = required
encryption at rest = required for durable DÉLIA state
backup inherits classification/encryption
biometric + secrets = stronger protected boundaries
application plaintext config cannot own long-lived credentials/keys
key owner = explicit
rotation and revocation = must be possible
KMS/vault/key owner = TO_INVENTORY
```

### 4A.9 Concurrency / idempotency

```text
material writes require idempotency
duplicate trigger/event must not duplicate side effect
blind retry of ambiguous material write = forbidden
reconcile authoritative state before retry
material stale mutation requires concurrency/version protection when applicable
read snapshot != permission snapshot
stored Decision/intent != permanent authorization
exactly-once delivery must NOT be assumed
```

Endpoint-specific idempotency = C0.S5.

### 4A.10 State-machine rules

Require explicit state machines where lifecycle is real for: Decision, Work, Task, Case, RecurringWork, WorkOccurrence, Knowledge candidate/publish, ExternalConnection, Watch, MCP/A2A approval.

`AutomationExecution` inside DÉLIA = projection/correlation only; technical lifecycle remains Automation Hub/executor authority.

Do not duplicate artifact/model/marketplace lifecycle when another owner is authoritative.

```text
terminal state cannot silently reactivate
cancel/revoke = explicit
technical execution state != Work state
technical completion != verified Outcome
```

Candidate sketches in §33 remain TARGET until ownership/persistence proven.

### 4A.11 Background identity / AuthZ

Every background operation has explicit actor: user-context | service-context | approved delegated context.

Timer, scheduler, event, webhook, RPA worker and provider callback are **NOT** business actors or authorities.

Material operation chain:

```text
explicit actor
→ live Core AuthZ
→ final Domain authorization
→ provider/resource validation where applicable
→ Policy/Decision
→ idempotency
→ audit
→ execution
→ authoritative Outcome verification
```

Exact service/delegation mechanism = `DEFER_TO_CONTRACT` / `TO_INVENTORY`.

### 4A.12 Recurring Work temporal safety

```text
explicit IANA timezone
explicit DST policy
explicit misfire policy
explicit overlap policy
explicit retry policy
stable occurrence identity
pause/cancel/revoke prevents future unauthorized material occurrence
every material occurrence revalidates authority/policy
schedule != permission
```

Do **not** select scheduler. Physical scheduler = `TO_INVENTORY`.

### 4A.13 FAST / OPERATIONAL / REASONING

```text
FAST = deterministic
OPERATIONAL = structured context + rules + approved small model only when justified
REASONING = complex investigation
```

Material readiness with an authoritative deterministic rule must **not** rely solely on free-form model judgment.

### 4A.14 Evidence / Outcome

```text
Evidence != source of truth
Evidence preserves provenance
Evidence preserves source/freshness/version when material
derived summaries link to Evidence
technical executor success != business Outcome
Outcome uses authoritative postcondition
```

Staleness/invalidation semantics required for: source changed; source deleted; permission revoked; projection stale; model version changed/revoked.

### 4A.15 Prediction / Scenario / Twin

```text
Prediction != FACT
recommendation != authorization
ModelRef != Decision authority
Scenario != production state
Twin != source of truth
SIMULATE != APPLY
```

Future Apply creates a **new** live action context.

### 4A.16 Biometric / Human Observation

```text
closed-set enrolled only
unknown remains unknown
confidence/correction required
biometric match != authentication
biometric match != authorization
```

Separate: raw enrollment media | biometric template | identity candidate | confirmed association.

```text
biometric template = SPECIALIZED_STORE
physical store/owner = TO_INVENTORY
```

Human Observation = observable operational facts only.

Forbidden as truth: personality; honesty; emotion; health; sensitive attributes; professional-value score; automatic employment decision.

### 4A.17 Media

```text
raw media != transcript != summary != Evidence != Decision != action != Outcome
```

Continuous capture requires purpose, visible state, notice/consent according to policy, ACL preservation, classification and retention. Raw media retention is **not** default. Physical media storage = `TO_INVENTORY`.

### 4A.18 External Connections / OAuth

Ownership classes: `USER_DELEGATED` | `ORG_MANAGED` | `SHARED_RESOURCE` | `SERVICE_CONNECTION`.

Connection metadata must preserve: owner, provider, scope, status, expiry/revocation, sharing class.

```text
provider scope != DELPI authorization
OAuth grant != permanent business authorization
personal connection != organizational connection
expired/revoked token != success
read != write
draft != send
```

### 4A.19 Audit / observability / eval

Material lineage may include: trigger; actor; Evidence/source refs; Policy/Decision version; capability; metric/model/executor version refs; input/arguments hash; correlation/idempotency; technical result; verified Outcome.

Never store: CoT; secret/token; biometric template; unbounded sensitive payload; raw sensitive media in generic telemetry.

Eval datasets require provenance/privacy classification/version.

### 4A.20 Process / Task Mining privacy

```text
Process Mining != employee surveillance
Task Mining = disabled by default unless governance explicitly approves
```

Forbidden: secret productivity leaderboard; personality/trust scoring; fraud/intent inference from deviation alone; unrestricted continuous desktop capture; automatic disciplinary profile.

### 4A.21 Sandbox / Artifact

```text
sandbox isolated
bounded compute/time/storage
no unrestricted host/private network
no broad credentials
generated code untrusted
no arbitrary DDL/DML from read-only analysis boundary
```

Artifact: owner/version/ACL/provenance/sensitivity/retention; human edits not silently replaced; external sharing is separate governed action.

No physical sandbox/store selected.

### 4A.22 Model / Marketplace / Control Tower

```text
approved model only
revoked model unavailable
router != approval
Marketplace requested permissions != grants
publish != enable
enable != authorization
Control Tower admin != business permission
```

No runtime created.

### 4A.23 Edge / Offline

```text
offline does not expand authority
device identity != user identity
cached permission != permanent authorization
buffered event != ACT authorization
user switch cleans personal state
reconciliation idempotent
```

### 4A.24 OT / Safety

```text
DÉLIA = NOT A SAFETY CONTROLLER
OT ACTUATION = BLOCKED_BY_DEFAULT
```

Forbidden: free-form LLM → PLC/CNC/robot/machine; voice → machine actuation without industrial gate; vision → safety override; AI-inferred OT permission; business L5 autonomy = OT autonomy; software kill switch = emergency stop.

Future physical actuation requires separate industrial architecture, independent safety authority, typed commands, interlocks, fail-safe behavior, approval matrix and verified OT contract.

### 4A.25 Failure / recovery / rollback

```text
partial failure = explicit
ambiguous write = no blind retry
rollback/revoke only when authority really supports it
technical rollback != business rollback
cancel != undo
irreversible operation requires stricter Decision Gate
```

### 4A.26 Cache / projection

```text
cache != authority
projection != authority
staleness detectable
freshness/version metadata where material
invalidation owner explicit
permission cache cannot preserve revocation
offline cache cannot widen authority
```

### 4A.27 Abstraction Gate

```text
NEW_RUNTIME_ABSTRACTIONS = NONE
```

Do **not** create: new service; new scheduler; new vault; new event bus; new shared store; new generic Policy engine; new state engine; new SecretRef primitive; new OT control layer.

### 4A.28 Deferred / inventory (non-blocking for candidate persistence)

```text
TO_INVENTORY:
  physical PostgreSQL placement
  physical vault/secret manager / KMS/key owner
  physical scheduler/timer
  physical media store
  biometric template physical store/owner
  exact service/delegation AuthZ mechanism
  Automation Hub physical runtime
  Sandbox physical runtime/store
  event broker/transport

DEFER_TO_CONTRACT (C0.S5+):
  SecretRef contract (no new shared primitive)
  endpoint-specific idempotency
  WorkspaceContext transport shape
  ExecutorRef
  typed integration contracts

DEFER_BY_PHASE:
  Foundation Freeze (C0.S7)
  runtime bootstrap (C1+)
```

## 5. WorkspaceContext

Shape `FROZEN_CANDIDATE` em `17` §22 (C0.S5-T2). Pode carregar app/route/EntityRefs/SourceRefs/filters/selection/dateRange/device metadata e bounded refs para Task/Case/Watch/RecurringWork/execution/artifact quando justificado.

Nunca carregar como authority:

```text
JWT/provider secret
permission/autonomy truth
raw mailbox/dataset
biometric permission truth
RPA desktop state
scheduler permission truth
sandbox credential
model/package trust decision
```

## 6. Media/Biometric/Human Observation

Mantém separação conceitual:

```text
RAW MEDIA
BIOMETRIC ENROLLMENT
BIOMETRIC TEMPLATE
IDENTITY CANDIDATE
PERSON OBSERVATION
```

Identity candidate != authenticated session != permission grant.

Human Observation persiste apenas fatos objetivos do processo quando necessário; sem personality/trust/emotion/health/global employee score.

## 7. ExternalConnection / provider state

Candidate:

```text
connectionId
ownerType: USER_DELEGATED|ORG_MANAGED|SHARED_RESOURCE|SERVICE_CONNECTION
ownerRef
providerKey
resource/account label bounded
status
scopes[]
secretRef
policyRef
createdAt/updatedAt
expiresAt?
lastValidatedAt?
```

Secret material permanece no approved secret owner.

Subscription/sync state mantém provider subscription/cursor/expiry/reconciliation refs sem business authority.

## 8. Conversation state

DÉLIA-owned quando implementado. Turn pode referenciar WorkspaceContext snapshot, Evidence, memory influence refs, plans/outcomes/artifacts, nunca chain-of-thought ou credentials.

Recurring Work não depende de conversation state viva para disparar; conversation pode apenas originar/editar uma definição por use case autorizado.

## 9. Personal Memory — owned state candidate

`MemoryItem` / `MemoryItemRef` = **DOMAIN_LOCAL_ONLY** (C0.S3) sob Personal Memory. Não é shared/universal primitive. Memory ≠ Organizational Knowledge ≠ business authority ≠ permission.

Personal Memory é separada de conversation e Organizational Knowledge.

Candidate `MemoryItem`:

```text
memoryId
ownerUserRef
class: USER_PREFERENCE|USER_CONFIRMED_FACT|WORK_CONTINUITY_REF|FOLLOWED_TOPIC|PRIVATE_KNOWLEDGE_REF|TEMPORARY_PERSONAL_CONTEXT
value/valueRef bounded
sourceRefs[]?
confidence?
status: ACTIVE|CORRECTED|EXPIRED|DELETED|DISABLED
createdAt
updatedAt
lastUsedAt?
retentionClass
policyRef
supersedesRef?
```

Invariantes:

```text
PersonalMemory != OrganizationalKnowledge
PersonalMemory != permission
PersonalMemory != live business truth
```

User deletion/correction propaga a derived indexes de acordo com policy quando esse lifecycle existir.

## 10. Organizational Knowledge

Reference/Decision/Experience/Solution Pattern knowledge segue candidate→review/eval/version/publish. Personal/external/process/execution evidence nunca vira corporate truth automaticamente.

## 11. Business Graph state

Graph armazena refs/relationships/provenance/materializations quando justificadas. Não duplica master data.

`RelationshipRef`, se criado, deve carregar source/provenance/freshness suficientes para ser invalidável.

## 12. Semantic Business Layer state

Graph e Semantic Layer permanecem separados.

Candidate `MetricDefinition`:

```text
metricId
name
businessMeaning
formulaRef/expression
grain
dimensions[]
unit
sourceOwnerRef
freshnessSla?
securityClassification?
ownerRef
version
status: DRAFT|ACTIVE|DEPRECATED|REVOKED
validationRef?
```

Candidate glossary concept:

```text
conceptId
term
meaning
scope/domain
ownerRef
sourceRefs[]
version
status
```

Conflicting definitions keep separate IDs/versions; do not silently merge.

## 13. Event / Watch state

Candidate `EventEnvelope` normaliza internal/external/automation/Edge events:

```text
eventId
eventType
sourceRef
occurredAt
receivedAt
entityRefs[]
correlation keys
payloadRef/value bounded
trust/auth metadata bounded
```

Event payload never grants permission.

Candidate Watch:

```text
watchId
ownerRef
conditionRef
mode: OBSERVE|ADVISE|PREPARE|ACT
scopeRefs[]
capabilityRef?
status
cooldown/dedupe policy
expiresAt?
```

Semântica de fase:

```text
C5 → ACT governado pode existir para capability explicitamente autorizada e aprovada pelos gates de write/Decision/idempotency/audit/Outcome
C6 → produto Watch usa OBSERVE|ADVISE|PREPARE por default; PREPARE continua sem side effect
C7 → selected autonomous Watch ACT / advanced autonomy, capability-scoped; L5 continua OFF por default
```

Logo, `ACT` não é sinônimo de “C7-only”; o que é C7 é **autonomous/advanced ACT** conforme `16`.

Recurring Governed Work temporal é state/trigger model distinto de Watch; não reutilizar `Watch.mode=ACT` para representar schedule apenas para evitar uma boundary necessária.

## 14. Durable Workflow / Decision state

Workflow é o target de runtime durável único de **Work/orquestração da DÉLIA**, não um executor técnico paralelo ao Automation Hub.

```text
stepId
workflowId
capabilityRef
dependsOn[]
status
attemptCount
idempotencyKey?
connectionRef?
executorRef?
agentRef?
resultRef/errorCode
decisionRef?
```

Decision stores action/arguments hash/impact/evidence/risk/actor/approver/policy/version, never private chain-of-thought.

Material semantic/model/policy changes may invalidate an old Decision.

### 14.1 Recurring Governed Work — owned state candidates

Se C0 confirmar necessidade/persistência DÉLIA-owned, `RecurringWorkDefinition` representa **a intenção/lifecycle governado do Work**, não o job técnico do scheduler.

Candidate:

```text
recurringWorkId
ownerRef
createdByActorRef
workTemplateRef / workflowDefinitionRef
scheduleSpec                    # provider-neutral canonical recurrence
scheduleTimezone                # IANA timezone
startAt?
endAt?
status: ACTIVE|PAUSED|CANCELLED|EXPIRED|DISABLED_BY_POLICY
capabilityRefs[]
scopeRefs[]
connectionRefs[]?
targetRefs[]?                   # recipients/resources bounded, no credential
policyRef
misfirePolicy
failurePolicy
overlapPolicy
createdAt
updatedAt
version
nextRunAt?                      # derived/projection only when needed
```

`RecurringWorkDefinition` **não** guarda token/provider secret nem copia permission truth. `scheduleSpec` não deve depender do SDK/type de um scheduler específico no Domain/Application canônico.

Lifecycle mínimo target:

```text
CREATE → ACTIVE
ACTIVE → PAUSED | CANCELLED | EXPIRED | DISABLED_BY_POLICY
PAUSED → ACTIVE | CANCELLED | EXPIRED | DISABLED_BY_POLICY
```

Update/reschedule, se suportado, deve produzir nova versão ou semântica equivalente auditável; não sobrescrever silenciosamente uma definição que já possui ocorrências.

Candidate `WorkOccurrence`/`RecurringWorkOccurrence` para correlation/audit, somente se C0 provar que não existe primitive suficiente:

```text
occurrenceId
recurringWorkRef
recurringWorkVersion
scheduledFor
triggeredAt?
status: SCHEDULED|TRIGGERED|RUNNING|SUCCEEDED|FAILED|SKIPPED|BLOCKED|CANCELLED|INCONCLUSIVE
correlationContext
idempotencyKey
actorRef / serviceActorRef
workflowRef?
decisionRef?
executionRefs[]?
outcomeRef?
evidenceRefs[]?
reasonCode?
createdAt/updatedAt
```

Invariantes:

```text
schedule != permission
stored intent != live authorization
occurrence != technical scheduler job authority
physical scheduler success != Work/business Outcome
```

O scheduler físico pode manter job/trigger/lease/next-fire state próprio. A DÉLIA referencia apenas o necessário para Work correlation/audit; não duplica a truth técnica do scheduler.

Cada ocorrência material resolve/revalida current user/service identity, Core/domain AuthZ, Policy/Decision e connection/provider state antes de ACT.

## 15. Automation Capability / Executor mapping

Candidate projection owned pela DÉLIA somente se C0 provar necessidade:

```text
automationId
version
capabilityRef
executorType: API|FUNCTION|RPA|COMPUTER_USE|NOTIFICATION|HUMAN_TASK
executorRef
ownerRef
environment
inputSchemaRef
outputSchemaRef
preconditionsRef?
postconditionsRef?
timeoutPolicyRef
retryPolicyRef
idempotencyPolicyRef
status
```

Planner recebe capability/schema, não click/selector mechanics.

Esse mapping não transforma a DÉLIA em owner do runtime técnico de execução. Automation Hub/executor owner permanece responsável pela execução técnica conforme contrato congelado em C0.

## 16. AutomationExecution

A DÉLIA pode manter uma **projection/correlation lifecycle** necessária para Work/Decision/Outcome; o Automation Hub pode possuir estado técnico adicional de worker/job/runtime. Não duplicar authority ou lifecycle sem contrato explícito.

Candidate orchestration projection:

```text
executionId
correlationContext
capabilityRef
executorRef/version
workflowStepRef?
triggerEventRef?
actorRef
status: QUEUED|RUNNING|SUCCEEDED|FAILED|AMBIGUOUS|CANCELLED|TIMED_OUT
queuedAt?
startedAt?
endedAt?
attempt
inputHash
idempotencyKey?
resultRef?
errorCode?
outcomeVerificationRef?
```

`SUCCEEDED` técnico não implica verified business Outcome.

RPA worker/queue state só existe no owner técnico se RPA for priorizado/provado:

```text
workerRef
class/capabilities
environment
status
heartbeat
lease/currentExecutionRef
package/runtime versions
```

Credential nunca entra no state comum da DÉLIA.

## 17. Outcome verification

Candidate:

```text
verificationRef
executionRef
authoritativeSourceRef
expectedPostconditionRef
observedOutcomeRef
status: VERIFIED_SUCCESS|VERIFIED_FAILURE|PENDING|INCONCLUSIVE
verifiedAt?
```

Notification success não altera Outcome.

## 18. Process Intelligence state

Preferir event-log projections e refs em vez de copiar todos os sistemas.

Candidate event row/materialization:

```text
processRef
caseRef/businessKey
activity
occurredAt
sourceRef
entityRefs[]
actorRef? only when necessary
outcome/status?
correlationRef?
```

Candidate `ProcessTraceRef` = **REFERENCE_ONLY** (C0.S3): tipagem local de Process Intelligence quando necessária; **não** é shared/universal primitive nem process master object.

```text
traceRef
processRef
caseRef
sourceSet/version
firstEventAt
lastEventAt
completeness/freshness metadata
```

Process model/variant/conformance outputs são derived artifacts/projections, com Evidence/version, nunca employee score.

## 19. Analysis Sandbox state

Sandbox session é preferencialmente efêmera.

Persistir metadata quando audit/reproducibility exigir:

```text
analysisRunId
ownerRef
inputSourceRefs[]
runtimeImage/version
code/notebook hash or bounded sourceRef
parameters
startedAt/endedAt
status
outputArtifactRefs[]
resource/budget metadata
retentionClass
```

No secret/host credential in analysis state.

## 20. Artifact Workspace state

Candidate `ArtifactRef`:

```text
artifactId
artifactType
version
ownerRef
status: DRAFT|REVIEWED|APPROVED|PUBLISHED|SUPERSEDED|ARCHIVED
sourceRefs[]
evidenceRefs[]
analysisRunRef?
storageRef
hash
createdByRef
createdAt/updatedAt
sensitivity
retentionClass
```

Human edit/version history remains distinct from AI regeneration.

## 21. Prediction / Prescription state

Candidate `PredictionRef`:

```text
predictionId
modelRef/version
subjectEntityRefs[]
target
horizon
value/probability
confidence/calibration metadata
inputSourceRefs[]
createdAt
validUntil?
limitations[]
```

Prediction != FACT.

Prescriptive artifact/decision candidate stores objectives/constraints/candidate scenarios/trade-offs/assumptions/Evidence; does not imply authorization.

## 22. Operational Twin / Scenario state

Twin is a projection, not master.

Candidate `ScenarioRef`:

```text
scenarioId
baseStateRefs[]
baseObservedAt
variables/overrides bounded
assumptions[]
model/solver refs
createdByRef
createdAt
status
resultArtifactRefs[]
```

Invariant:

```text
SIMULATED_STATE != PRODUCTION_STATE
```

Apply starts a new live action context; scenario state cannot be reused as write authority.

## 23. MCP/A2A interoperability state

Candidate server/agent registry projection:

```text
integrationRef
type: MCP_SERVER|A2A_AGENT|OTHER_APPROVED_TOOL_PROVIDER
provider/endpoint ref bounded
ownerRef
approvedCapabilities[]
riskTier
dataDomains[]
allowedCallers/scopes
status: DISCOVERED|REVIEWED|APPROVED|ACTIVE|DEGRADED|DISABLED|REVOKED|DEPRECATED
protocol/version
policyRef
lastValidatedAt?
```

No broad credential in registry.

Delegated task metadata:

```text
taskRef
goal bounded
inputRefs[]
allowedCapabilityScope
expectedResultSchemaRef
budget/deadline
status
resultRefs[]
```

No hidden CoT/conversation dump.

## 24. AI Control Tower / AI Asset Registry state

Candidate `AIAssetRef` projection = **PROJECTION_ONLY** (C0.S3); detalhe de contrato = `DEFER_BY_PHASE`. AIAsset ≠ permission. Não é foundation global de autoridade.

```text
assetId
assetType
name/version
ownerRef
status
riskTier
capabilityRefs[]
dataDomain/scope refs
runtime/deployment refs
policyRef
model/provider refs?
evalStatus/ref
cost/budget metadata?
dependencies[]
killSwitchRef?
lastValidatedAt
```

Control Tower projection never grants business permission.

Incident state may reference asset/evidence/impact/containment/owner/resolution without secrets/CoT.

## 25. Model lifecycle state

Candidate `ModelRef`:

```text
modelId
version
family
providerRef?
ownerRef
purpose
approvedDataClasses[]
evalSuiteRef/status
riskTier
status: DRAFT|EXPERIMENT|EVALUATED|APPROVED|DEPLOYED|DEGRADED|DEPRECATED|REVOKED|RETIRED
runtime/deploymentRefs[]
latency/cost profile refs?
rollbackRef?
```

Dataset refs, if DELPI-owned, preserve provenance/licensing/privacy/version. Never persist training secrets in registry.

## 26. Capability Marketplace state

Candidate package/asset metadata:

```text
assetId/version/type
publisher/ownerRef
status: DRAFT|REVIEW|APPROVED|PUBLISHED|DEPRECATED|REVOKED
requiredCapabilities[]
requiredPermissions/scopes declarative only
configSchemaRef
dependencies[]
compatibility
riskTier
eval/test refs
packageHash/signatureRef?
releaseNotesRef?
```

Declared permissions/scopes are requirements, not grants.

## 27. Edge / Offline state

**C0.S3:** `EdgeDeviceRef` = REJECT as separate shared primitive → **REUSE `DeviceRef`**.

Device/Edge platform metadata (quando necessário) estende DeviceRef / domain-local device projection — não cria segundo tipo compartilhado:

```text
deviceRef
class/location
ownerRef
runtime/os/hardware capabilities bounded
networkZone
allowedCapabilityRefs[]
status/health
lastSeenAt
package/model versions
lastSyncAt?
```

Offline cache item:

```text
sourceRef
version/revision
syncedAt
validUntil?
retention
hash/signature?
```

Buffered event:

```text
localEventId
occurredAt
dedupe/idempotency key
payloadRef bounded
syncStatus
```

Offline mode must not widen authority.

## 28. Retention classes

At minimum distinguish, quando as respectivas capabilities existirem:

```text
TRANSIENT_MEDIA
RAW_AUDIO/RAW_VIDEO/SCREEN_CAPTURE
DERIVED_EVIDENCE
BIOMETRIC_ENROLLMENT_MEDIA/BIOMETRIC_TEMPLATE/IDENTITY_CANDIDATE
PERSON_OBSERVATION
WEB_RESEARCH_TRANSIENT/WEB_RESEARCH_EVIDENCE
EXTERNAL_RESOURCE_CACHE/EXTERNAL_MESSAGE_OR_FILE_EVIDENCE
EXTERNAL_CONNECTION_METADATA/EXTERNAL_SUBSCRIPTION_STATE
PERSONAL_MEMORY
PROCESS_EVENT_PROJECTION
PROCESS_MODEL_DERIVED
RECURRING_WORK_DEFINITION/RECURRING_WORK_OCCURRENCE_METADATA
AUTOMATION_EXECUTION_METADATA/AUTOMATION_ARTIFACT/RPA_SCREENSHOT
ANALYSIS_RUN_METADATA/ANALYSIS_TEMP_FILE
ARTIFACT_WORKSPACE_CONTENT
PREDICTION_OUTPUT/SCENARIO_STATE
AI_ASSET_METADATA/MODEL_METADATA/EVAL_ARTIFACT
EDGE_CACHE/EDGE_BUFFERED_EVENT
MEETING_ARTIFACT/FRONTLINE_RECORD
```

Cada classe implementada precisa de purpose/access/retention/redaction/encryption/delete/export/revoke/anonymize conforme aplicável. Classes arquiteturais C0.S4 (§4A.3) prevalecem quando houver overlap; duração legal exata permanece `TO_INVENTORY` se não provada.

## 29. Cache/materialization rules

Derived cache/materialization always carries:

```text
source refs
source version/freshness
created/materializedAt
scope/user/connection/domain boundaries
TTL/invalidation policy
schema/version
```

Cache/materialization never becomes permission or business authority.

## 30. Idempotency / concurrency

- duplicate event must not duplicate action;
- duplicate timer/scheduler trigger for same recurring occurrence must not duplicate action;
- recurring occurrence idempotency key must survive retry/restart/reconciliation as defined by contract;
- overlap/concurrency policy for recurring Work must be explicit rather than accidental worker behavior;
- missed-run/misfire behavior must be explicit; no silent material catch-up;
- Workflow resume must not duplicate side effect;
- ambiguous write verified before retry when possible;
- queue lease prevents double worker pickup quando queue/worker fizerem parte do owner técnico;
- external provider/RPA/domain idempotency differences modeled explicitly;
- offline Edge sync deduplicates/reconciles;
- A2A delegated write protects duplicate task/result handling.

## 31. Shared-device / Edge / worker isolation

Browser residency (C2-T1D1, `BROWSER_STATE_RESIDENCY_POLICY=APPROVED`):

- current DÉLIA runtime has no proven `BROWSER_RETAINED_STATE`; `BROWSER_RETAINED_STATE_CURRENTLY_REQUIRED=NO`;
- `CENTRALIZED_BROWSER_STATE_BOUNDARY=REQUIRED_ON_FIRST_RETAINED_STATE`; `CURRENT_RUNTIME_IMPLEMENTATION=NONE`;
- transient UI state may stay in the mounted component; retained browser state requires the gate in `49` §6.1;
- session-scoped state clears on logout/session invalidation; user-scoped state must not be readable by the next user; uncertain class clears;
- DÉLIA-owned keys, when they exist, must be namespaced, enumerable, and versioned so stale versions and the current session can be removed from one lifecycle path;
- no namespace syntax is frozen, and no namespace is claimed in the current runtime;
- browser copies are not authoritative and are not a shadow record for Evidence, Decision, Work, domain facts, or authorization.

- user switch clears personal/context/media/external/memory projections;
- RPA worker/session cannot leak prior execution credentials/data;
- scheduler/background occurrence does not reuse browser/session credential as authorization;
- Edge device local state follows user/device scope;
- offline cache for one user/domain cannot leak to unauthorized user.

## 32. Migration strategy

```text
EXPAND → compatible readers → writers → optional backfill → CUTOVER → CLEANUP
```

Provider/executor/model swaps use adapters/versioned refs.

RPA→API migration should change capability mapping rather than planner/business logic.

Physical scheduler swap should change adapter/trigger integration rather than RecurringWork domain semantics.

Metric/model/process definition changes are versioned, never silent overwrite.

## 33. State machines relevantes

Candidate lifecycles, somente quando ownership e persistência forem provados:

```text
ExternalConnection:
PENDING_AUTH → ACTIVE → EXPIRED|REAUTH_REQUIRED|REVOKED|DISABLED|ERROR

RecurringWorkDefinition:
ACTIVE → PAUSED|CANCELLED|EXPIRED|DISABLED_BY_POLICY
PAUSED → ACTIVE|CANCELLED|EXPIRED|DISABLED_BY_POLICY

RecurringWorkOccurrence:
SCHEDULED → TRIGGERED → RUNNING → SUCCEEDED|FAILED|SKIPPED|BLOCKED|CANCELLED|INCONCLUSIVE

AutomationExecution orchestration projection:
QUEUED → RUNNING → SUCCEEDED|FAILED|AMBIGUOUS|CANCELLED|TIMED_OUT

MCP/A2A integration:
DISCOVERED → REVIEWED → APPROVED → ACTIVE → DEGRADED|DISABLED|REVOKED|DEPRECATED

MemoryItem:
ACTIVE → CORRECTED|EXPIRED|DELETED|DISABLED

MetricDefinition:
DRAFT → ACTIVE → DEPRECATED|REVOKED

Artifact:
DRAFT → REVIEWED → APPROVED|PUBLISHED → SUPERSEDED|ARCHIVED

Model:
DRAFT/EXPERIMENT → EVALUATED → APPROVED → DEPLOYED → DEGRADED|DEPRECATED|REVOKED|RETIRED

Marketplace Asset:
DRAFT → REVIEW → APPROVED → PUBLISHED → DEPRECATED|REVOKED
```

Persistir state machine somente quando lifecycle real justificar.

## 34. Explicitamente proibido

- Chat tables/runtime as DÉLIA storage;
- shadow Core user/RBAC/domain database;
- duplicar no state da DÉLIA a truth técnica autoritativa de scheduler/timer/job/lease quando pertencer a outro owner;
- duplicar no state da DÉLIA o runtime técnico autoritativo do Automation Hub/executor;
- usar schedule/timer/recurring definition como permission truth;
- persistir authorization snapshot como autorização eterna para ocorrências futuras;
- provider/RPA/model/tool secret in prompt/log/MFE/Evidence;
- personal memory/source auto-shared to organization;
- memory as live business truth or permission;
- employee-surveillance dataset from Process Mining/Task Mining;
- semantic metric without owner/version for material use;
- sandbox storing broad DB/host credentials;
- analysis cache as authoritative business state;
- prediction stored as FACT;
- scenario/twin state used directly as production write truth;
- MCP/A2A registry entry as automatic trust;
- marketplace requested permission as granted permission;
- revoked model/server/package still selectable;
- Edge offline mode as permission expansion;
- RPA bot/package as business-rule authority;
- technical executor success as business success without required verification;
- global unrestricted `autonomyLevel=L5`;
- free-form machine-control state as DÉLIA authority.


## C3-T5 — Runtime CapabilityProjection foundation

Implementation candidate: `84c249bee0182ebf514142a24cb8bbea4090ca26`.

`CapabilityProjection` now has a minimal runtime representation inside the DÉLIA domain while preserving the C0 freeze:

```text
CapabilityProjection
= projection-only semantic capability metadata
!= current-user authorization
!= Core RBAC
!= Domain business authorization
!= provider credential
!= execution grant
!= Automation Hub technical truth
```

The bounded OpenAPI adapter remains Infrastructure-only. It projects source owner/contract/version/hash, stable `operationId`, semantic identity, canonical operation character, bounded input/output/error descriptors, descriptive security metadata and explicitly declared idempotency/reversibility/postcondition semantics.

Operation character is not inferred from HTTP method. C3-T5 found no canonical real DELPI OpenAPI extension or other real-source semantic classification contract to bind now; therefore the foundation uses explicit governed declarations in TEST_FIXTURE evidence, and unknown/ambiguous operations are not projectable. No persistence or catalog database is introduced.

## C3-T6 / C3-T6R1 — Expertise / Knowledge governance + retrieval contracts (APPROVED)

```text
STATUS = APPROVED
REVIEW = ARCHITECTURE_REVIEW_C3_T6R1
REVIEWED_IMPLEMENTATION_HEAD = 1a49e501fb8e2d900081572de83d2226cc09fb68
REVIEW_REANCHOR_HEAD = 446d93564a2219430c8afac3b283881f41c4d9ae
VERDICT = ACCEPT_WITH_RESIDUAL
OWNER = DÉLIA (delia-api domain/expertise + domain/knowledge)
ExpertisePack.evidence_refs = tuple[EvidenceRef, ...]
ExpertisePack.status / DomainPlaybook.status = descriptive non-authoritative metadata only
DomainPlaybook = versioned guidance (!= workflow / AutomationExecution / ACT)
KnowledgeCandidate != OrganizationalKnowledge (published)
KnowledgeOriginClass = TRANSIENT_RESEARCH | SESSION_EVIDENCE | PERSONAL_KNOWLEDGE_CANDIDATE | ORGANIZATIONAL_KNOWLEDGE_CANDIDATE | PUBLISHED_ORGANIZATIONAL_KNOWLEDGE
KnowledgeLifecycleStatus = CANDIDATE | REVIEWED | EVALUATED | PUBLISHED | DEPRECATED | REVOKED
publication_evaluation_completed = knowledge-governance lifecycle assertion (≠ model EvalResult)
REUSES = EvidenceRef, SourceRef
KnowledgeRetrievalRequest fields = purpose | owner_filters | version_constraint | max_results
KNOWLEDGE_SCOPE = REMOVED
RETRIEVAL_INCLUDE_FLAGS = REMOVED
NORMAL_RETRIEVAL_SCOPE = PUBLISHED_ORGANIZATIONAL_KNOWLEDGE_ONLY
REVOKED_DEPRECATED_RETRIEVAL_SEMANTICS = EXCLUDED_FROM_NORMAL_RETRIEVAL
KnowledgeRetrievalPort = DEFERRED
filter_organizational_retrieval_eligibility = deterministic in-memory eligibility only
retrieval hit != FACT / Evidence / permission
Personal/session/transient != auto Organizational Knowledge
PHYSICAL_KNOWLEDGE_STORE = TO_INVENTORY / DEFERRED
NEW_RUNTIME_ABSTRACTIONS = NONE
PERSISTENCE = NONE
MIGRATION = NONE
RAG = NONE
VECTOR_STORE = NONE
REGISTRY = NONE
PLANNER = NONE
ACT = NONE
C3_T7_AUTHORIZED = YES
C3_T7_EXECUTED = NO
```

C3-T6 does not persist knowledge assets, does not index vectors, does not implement Personal Memory runtime, Marketplace, planner, conversation, PREPARE or ACT. Accepted with residual via `ARCHITECTURE_REVIEW_C3_T6R1`.
