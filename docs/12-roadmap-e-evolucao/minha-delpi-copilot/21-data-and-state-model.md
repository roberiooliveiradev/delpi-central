# Minha DELPI Copilot — Modelo de Dados, Estado e Persistência

**Status:** target arquitetural standalone  
**Autoridade de ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)  
**Biometric/Human Observation:** [`54-biometric-identity-and-human-observation-governance.md`](./54-biometric-identity-and-human-observation-governance.md)  
**Internet/External Connectors:** [`55-internet-research-and-external-connectors.md`](./55-internet-research-and-external-connectors.md)  
**Autonomous Operations/Execution Hub:** [`57-event-driven-autonomous-operations-and-automation-execution-hub.md`](./57-event-driven-autonomous-operations-and-automation-execution-hub.md)

## 1. Princípio

Todo estado durável do Copilot pertence à **Copilot API nova** ou a um owner corporativo/externo explicitamente referenciado.

```text
REFERENCE
→ refs para entities/users/resources de owners externos

COPILOT RUNTIME STATE
→ conversations/turns/plans/context snapshots

COPILOT DURABLE WORK STATE
→ decision/workflow/task/case/watch/inbox

COPILOT MEDIA/BIOMETRIC STATE
→ meeting/frontline/media/biometric metadata only when required

COPILOT EXTERNAL CONNECTION STATE
→ connection metadata, scopes, sync/subscription state, secretRef

COPILOT AUTOMATION STATE
→ capability-to-executor mapping, execution correlation/lifecycle, outcome refs, only when Copilot owns it

DERIVED INDEX/CACHE
→ capabilities/expertise/graph/search/external caches

DOMAIN DATA
→ permanece nas Domain APIs

EXTERNAL RESOURCE DATA
→ permanece no provider; Copilot guarda refs/cache bounded apenas quando necessário

CORPORATE USER IDENTITY
→ permanece Keycloak/Core-owned
```

Proibido usar Chat tables como foundation, criar shadow user directory, replicar mailbox/Drive/WhatsApp como system of record ou transformar Automation Hub em segundo system of record de negócio.

## 2. Storage ownership

Target:

```text
minha-delpi-copilot-api/migrations/
→ única migration chain do Copilot
```

Mesmo cluster físico não implica mesma authority lógica.

Biometric templates, provider credentials e RPA credentials podem exigir storage/keys separados do banco transacional; C0 define owner/adapter antes de criar tabela.

Se Automation & Execution Hub for provado como neutral platform service separado, ele terá ownership/migrations próprios por ADR. Não assumir microservice antecipadamente.

## 3. Regra C0 antes de migrations

Definir:

- naming/IDs/versioning;
- retention/LGPD/data classification;
- media/biometric/external/automation artifact retention classes;
- encryption/key management;
- connection/credential ownership;
- provider token lifecycle;
- personal vs organizational source semantics;
- webhook/subscription/sync state;
- external cache TTL/freshness;
- event/execution correlation;
- executor mapping ownership;
- service/background identity refs;
- RPA package/worker/queue ownership;
- execution/outcome retention;
- concurrency/idempotency;
- migration/rollback;
- Copilot-owned versus refs/projections;
- shared primitives somente se necessários.

## 4. Shared references

### CorrelationContext

```text
requestId
conversationId
turnId?
workflowId?
taskId?
caseId?
watchId?
eventId?
executionId?
meetingId?
frontlineSessionId?
mediaSessionId?
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

### UserRef / ServiceActorRef

`UserRef` aponta para Keycloak/Core. Background automation pode precisar de actor/service identity explícita.

Candidate conceitual, somente se C0 provar necessidade:

```text
actorType: USER | SERVICE
actorRef
sourceAuthority
purpose/scope bounded
```

Nunca transformar event source, bot, worker ou biometric candidate em user authority.

### SourceRef / EvidenceRef / OutcomeRef

Usados transversalmente por Domain API, web, connectors, multimodal, Graph, Workflow, Automation, Meeting/Frontline e audit.

External SourceRef pode conter provider/resource/freshness sem credential.

OutcomeRef pode apontar para:

```text
businessAction outcome
external provider outcome
automation execution outcome
postcondition verification
```

Technical executor result e verified business Outcome podem ser referências distintas.

## 5. MediaRef — candidate foundation

Se C0 provar necessidade, mantém media metadata bounded e Evidence referencia MediaRef/location sem copiar raw media.

## 6. Workspace Context

Pode carregar app/route/EntityRefs/SourceRefs/filters/selection/dateRange/device metadata.

Pode mostrar execution/task/watch refs bounded para UX, mas nunca persistir como truth:

- DOM state;
- JWT/provider/RPA secrets;
- permissions/scopes/autonomy as authority;
- datasets/mailboxes completos;
- biometric candidate como permission truth;
- raw RPA desktop session state.

## 7. Device/session metadata

Device identity != user identity. RPA worker/desktop session identity também não equivale a business actor.

## 8. Biometric identity state

Separar RAW MEDIA, ENROLLMENT, TEMPLATE e IDENTITY CANDIDATE. Candidate != authenticated session != permission grant.

## 9. Human Observation state

Somente observações objetivas de processo com Evidence/provenance. Não armazenar personality/trust/emotion/health/sensitive/global employee score.

## 10. ExternalConnection — candidate owned state

```text
connectionId
ownerType
ownerRef
providerKey
providerAccount/resource label bounded
status
scopes[]
secretRef
createdAt/updatedAt
expiresAt?
lastValidatedAt?
policyRef
```

`secretRef` nunca vai para LLM/MFE/SourceRef/Evidence.

## 11. Provider secret/credential state

Credential material pertence ao approved secret owner/adapter. O mesmo vale para RPA/service-account credentials.

Nunca persistir token/password/desktop secret em conversation/log/MFE/Evidence.

## 12. External resource references

Preferir SourceRef antes de novo ExternalResourceRef. Não copiar conteúdo integral por default.

## 13. External sync/subscription state

```text
subscriptionId
connectionRef
resourceScope
providerSubscriptionRef
status
expiresAt
lastEventAt?
lastReconciledAt?
syncCursor/deltaRef?
errorCode?
```

## 14. External cache / fetched content

Cache derivado, scoped, TTL/freshness explícitos; personal content não vira shared cache por default.

## 15. Internet Research state

Pode ser totalmente transitória. Persistir somente refs/evidence bounded quando Task/Case/audit exigir.

## 16. Copilot conversations

Copilot-owned, sem `agent_id/chat_mode`. Turn pode referenciar workspace/media/evidence/identity/external source/plan/outcome, nunca CoT/credentials.

## 17. Media/Meeting/Frontline sessions

Persistir apenas quando continuity/audit/policy exigir. Frontline não vira surveillance datastore.

## 18. Retention classes

Separar pelo menos:

```text
TRANSIENT_MEDIA
TRANSCRIPT
RAW_AUDIO
RAW_VIDEO
SCREEN_CAPTURE
DERIVED_EVIDENCE
BIOMETRIC_ENROLLMENT_MEDIA
BIOMETRIC_TEMPLATE
IDENTITY_CANDIDATE
PERSON_OBSERVATION
WEB_RESEARCH_TRANSIENT
WEB_RESEARCH_EVIDENCE
EXTERNAL_RESOURCE_CACHE
EXTERNAL_MESSAGE_OR_FILE_EVIDENCE
EXTERNAL_CONNECTION_METADATA
EXTERNAL_SUBSCRIPTION_STATE
AUTOMATION_EXECUTION_METADATA
AUTOMATION_EXECUTION_ARTIFACT
RPA_SCREENSHOT_OR_ARTIFACT
AUTOMATION_LOG_BOUNDED
MEETING_ARTIFACT
FRONTLINE_RECORD
```

Cada classe define purpose/access/retention/redaction/encryption/revoke/delete/anonymize.

## 19. Evidence

Evidence pode apontar para fontes internas/públicas/conectadas e automation execution artifacts.

```text
evidenceId
sourceRef
entityRefs[]
userRef? only when necessary
kind
valueRef/value bounded
location?
mediaRef?
executionRef?
observedAt
freshness
confidence?
limitations[]
extractor/model/version?
```

RPA screenshot/output não vira FACT apenas por existir; authoritative business state continua no owner apropriado.

## 20. Decision Gate

Pode referenciar Business Action, External Action ou Automation capability.

```text
actionRef
argumentsHash
impactPreview
evidenceRefs
risk/sensitivity
status
actor/approver refs
connectionRef?
automationCapabilityRef?
```

Decision antiga não sobrevive a material permission/context/arguments/policy change.

## 21. Durable Workflow

Workflow/Step é runtime único para business/external/automation capabilities.

```text
stepId
workflowId
capabilityRef
connectionRef?
executorRef?
target/resourceRef?
dependsOn[]
status
attemptCount
idempotencyKey?
resultRef/errorCode
decisionRef?
```

Nunca armazenar credential no step.

## 22. Task / Case / Room / Inbox

Podem referenciar external SourceRefs/EvidenceRefs e AutomationExecutionRef bounded. Room membership não concede mailbox/executor permission.

Exception manual usa Inbox/Decision e retoma o mesmo Workflow.

## 23. Event / Watch

`EventEnvelope` normaliza eventos internos/externos/automation outcomes.

Campos conceituais relevantes:

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

Event payload nunca concede permission.

Watch:

```text
watchId
owner
condition/ref
mode OBSERVE|ADVISE|PREPARE|ACT
entity/capability scope
status
cooldown/dedupe policy
expiresAt?
timestamps
```

C6 libera `OBSERVE|ADVISE|PREPARE`; `ACT` permanece C7.

## 24. AutomationCapability / Executor mapping — candidate state

C0/C5 decidem schema final. Conceitualmente:

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
createdAt/updatedAt
```

Planner recebe capability/schema e não detalhes de UI.

Se a mesma capability muda de RPA para API, application/planner não deve mudar por causa disso.

## 25. AutomationExecution state

Candidate Copilot-owned state quando execution correlation/lifecycle pertencer ao Copilot/Hub:

```text
executionId
correlationContext
capabilityRef
executorRef
executorVersion
workflowStepRef?
triggerEventRef?
actorRef
status
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

Lifecycle:

```text
QUEUED
→ RUNNING
→ SUCCEEDED | FAILED | AMBIGUOUS | CANCELLED | TIMED_OUT
```

`SUCCEEDED` técnico não significa automaticamente business Outcome verificado.

## 26. RPA worker/queue state

Somente se RPA for priorizado e Copilot/Hub for owner apropriado.

Worker ref:

```text
workerRef
workerClass/capabilities
environment
status ONLINE|BUSY|OFFLINE|DRAINING
lastHeartbeatAt
currentExecutionRef?
package/runtime versions bounded
```

Queue/execution state pode carregar:

```text
priority
lease/lock owner
leaseExpiresAt
attempt
notBeforeAt?
```

Nunca armazenar worker password/token em state comum.

Desktop/session IDs são infrastructure refs e não business user identity.

## 27. Executor artifacts

RPA/computer-use podem gerar logs/screenshots/files. Persistir somente quando audit/support/evidence justificar.

Artifact metadata:

```text
artifactRef
executionRef
kind
classification
retentionClass
storageRef
hash/version
createdAt
```

Aplicar redaction para PII/secrets e não tornar screenshot de desktop compartilhado automaticamente visível a todos.

## 28. Outcome verification state

Quando ação material exige postcondition:

```text
verificationRef
executionRef
authoritativeSourceRef
expectedPostconditionRef
observedOutcomeRef
status VERIFIED_SUCCESS|VERIFIED_FAILURE|PENDING|INCONCLUSIVE
verifiedAt?
```

Exemplos:

```text
RPA clicked Save
!= VERIFIED_SUCCESS

API returned accepted
!= final business completion when owner is async
```

## 29. Decision path metadata

Não persistir CoT. Pode persistir bounded operational metadata:

```text
decisionPath: FAST|OPERATIONAL|REASONING
policyVersion
model/configRef? only when used
input evidence refs
result/decision ref
latency/cost bounded
```

Isso permite observability sem expor raciocínio privado.

## 30. Autonomy policy state

Autonomia não é campo global do Copilot. Candidate configuration:

```text
capabilityRef
scope/entity constraints
actor/service constraints
allowedLevel
financial/material limits?
environment constraints
rate/budget limits
requiredGate
killSwitchRef
policyVersion
status
```

L5 default = disabled.

## 31. Notification/escalation state

Notificação referencia Event/Outcome/Task/Case/Workflow sem duplicar business truth.

Candidate metadata:

```text
notificationRef
sourceOutcome/eventRef
recipientRefs[]
channelRefs[]
severity
status
dedupeKey
sentAt?
acknowledgedAt?
escalationRef?
```

Notification success não altera Outcome do processo.

## 32. Organizational Knowledge

External/process/execution source pode produzir candidate knowledge, nunca corporate truth automática.

Execution history:

```text
Event + Context + Decision + Action + Outcome
→ Evidence
→ candidate pattern/optimization
→ review/eval
→ publish
```

## 33. Idempotência/concurrency

Business/external/RPA writes precisam proteger replay/resume/ambiguous outcome.

- duplicate event must not duplicate execution;
- workflow resume must not duplicate material effect;
- ambiguous executor timeout requires verification before retry when possible;
- queue lease prevents double worker pickup;
- idempotency keys align with domain/provider/executor capabilities.

## 34. Shared-device / worker isolation

Troca de usuário limpa auth/context/media/external state. RPA worker/session não pode reutilizar state/credential de execução anterior fora de policy.

## 35. OT/machine state

Machine truth permanece owner OT/domain. Automation Hub não é caminho alternativo para arbitrary physical actuation.

## 36. Migration strategy

Copilot migrations independentes:

```text
EXPAND → compatible readers → writers → optional backfill → CUTOVER → CLEANUP
```

Executor/provider swaps usam adapters/versioned contracts, sem reescrever Domain/Application.

RPA→API migration deve preferir alterar mapping `capabilityRef → executorRef`, preservando planner/workflow contracts.

## 37. State machines relevantes

```text
ExternalConnection:
PENDING_AUTH → ACTIVE → EXPIRED|REAUTH_REQUIRED|REVOKED|DISABLED|ERROR

ExternalSubscription:
CREATING → ACTIVE → RENEWING → ACTIVE|EXPIRED|REAUTH_REQUIRED|DISABLED|ERROR

AutomationExecution:
QUEUED → RUNNING → SUCCEEDED|FAILED|AMBIGUOUS|CANCELLED|TIMED_OUT

Worker:
ONLINE ↔ BUSY → DRAINING|OFFLINE
```

Só persistir state machine quando lifecycle real justificar.

## 38. Explicitamente proibido

- Chat state/tables como Copilot storage;
- provider/RPA secret em prompt/log/MFE/SourceRef/Evidence;
- shadow copy de external systems como master data;
- cross-user external/worker state leak;
- personal source auto-promoted;
- external scope persistido como Core permission;
- RPA bot/package como business authority;
- click/selector/coordenada como planner durable state;
- event payload como permission/autonomy truth;
- technical executor success armazenado como business success sem required verification;
- global `autonomyLevel=L5` irrestrito;
- hidden computer-use session without audit/control;
- biometric/employee surveillance dataset por default;
- free-form machine-control state como Copilot authority.
