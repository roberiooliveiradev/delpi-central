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
MIGRATION_CHAIN = delia-api/migrations/
PHYSICAL_PG_CLUSTER = DEFERRED
```

```text
delia-api/migrations/   # own chain; only DÉLIA-owned state / bounded projections/refs
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

## 4. Shared foundations

Todos os tipos abaixo são `TARGET/CANDIDATE` até C0 provar necessidade e ownership.

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

## 5. WorkspaceContext

Pode carregar app/route/EntityRefs/SourceRefs/filters/selection/dateRange/device metadata e bounded refs para Task/Case/Watch/RecurringWork/execution/artifact.

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

Candidate `ProcessTraceRef` somente se necessário:

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

Candidate `AIAssetRef` projection:

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

Candidate `EdgeDeviceRef`:

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

Cada classe implementada precisa de purpose/access/retention/redaction/encryption/delete/export/revoke/anonymize conforme aplicável.

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
