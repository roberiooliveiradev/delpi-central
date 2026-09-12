# Minha DELPI Copilot — Modelo de Dados, Estado e Persistência

**Status:** target arquitetural standalone  
**Autoridade de ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)

## 1. Princípio

Todo estado durável do produto Copilot pertence à **Copilot API nova** ou a um owner corporativo explicitamente referenciado.

```text
REFERENCE
→ refs para entities/sources de owners externos

COPILOT RUNTIME STATE
→ conversations/turns/plans/context snapshots

COPILOT DURABLE WORK STATE
→ decision/workflow/task/case/watch/inbox semantics

COPILOT COLLAB/MEDIA STATE
→ meeting/frontline/media metadata only when required

DERIVED INDEX/CACHE
→ capabilities/expertise/graph/search indexes

DOMAIN DATA
→ permanece nas Domain APIs
```

**Proibido:** usar tabelas/sessions/agents/migrations do Minha DELPI Chat como foundation do Copilot.

## 2. Storage ownership

Target recomendado:

```text
minha-delpi-copilot-api/migrations/
→ única migration chain do Copilot
```

O cluster PostgreSQL físico pode ser compartilhado com outros plugins se a infraestrutura vigente recomendar isso, porém ownership lógico é separado.

```text
same PostgreSQL cluster != same product schema/authority
```

Nenhuma migration do Copilot edita tabelas do Chat.

## 3. Regra C0

Antes de criar migrations, C0 define:

- DB/schema/table naming convention;
- IDs;
- versioning;
- retention/LGPD;
- media retention classes;
- consent/policy references;
- indexes;
- concurrency/idempotency;
- migration/rollback strategy;
- quais dados são Copilot-owned versus refs/projections;
- quais existing rooms/notifications/events são referenciados por adapter;
- se `MediaRef` ou primitive equivalente é necessário;
- shared-device session boundaries;
- o que nunca pode ser durable raw media por default.

## 4. Shared references

### CorrelationContext

```text
requestId
conversationId
turnId
workflowId?
taskId?
caseId?
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

Não copia o Domain object.

OP, máquina, produto, lote, material, operação e posto devem preferir `EntityRef` em vez de criar um segundo contexto industrial.

### SourceRef / EvidenceRef / OutcomeRef

Copilot-owned contract usado transversalmente por:

- conversation synthesis;
- API results;
- multimodal;
- media;
- Business Graph;
- workflow;
- Task/Case;
- Meeting/Frontline;
- Simulation;
- audit/presentation.

Não existe dependência do evidence/state model do Chat.

## 5. MediaRef — candidate foundation

C0 decide se a necessidade transversal justifica `MediaRef` ou equivalente.

Semântica candidata:

```text
mediaId/ref
kind: audio|image|video|screen|document
source
capturedAt
sessionRef?
owner/actor ref?
retentionClass
consentPolicyRef?
contentHash/version?
storageRef?  # somente se persistido
```

Regra:

```text
EvidenceRef → MediaRef/location
```

quando necessário, sem duplicar raw media dentro de Evidence.

## 6. Workspace Context

**Owner primário em runtime:** Portal/MFE/iframe/device adapter.  
**Copilot persistence:** snapshot bounded somente quando necessário à conversa/workflow/audit.

Pode carregar semanticamente:

```text
appId
routeId
EntityRefs[]
filters/selection/dateRange
bounded device/session metadata
```

Nunca persistir como truth:

- DOM/React state;
- tokens/secrets;
- datasets completos;
- permissions;
- inferência visual de identidade de usuário.

## 7. Device/session metadata

Device identity não é user identity.

Bounded metadata candidato:

```text
deviceRef/workstationRef
surface: global|workspace|meeting|frontline
deviceClass: desktop|tablet|kiosk|room|mobile|other
sessionStartedAt
capability flags: mic/camera/screen/touch/audioOut
```

Não deve conter permission truth nem substituir autenticação do usuário.

## 8. Copilot conversations

O Copilot possui modelo próprio desde C3.

Campos conceituais:

```text
conversationId
owner/participant refs
status
title?
createdAt/updatedAt
context/preferences refs
```

Turn:

```text
turnId
conversationId
input/output refs
workspace snapshot ref?
media/evidence refs?
plan/outcome/evidence refs
model/config metadata bounded
createdAt
```

Não armazenar chain-of-thought.

Não utilizar `agent_id`, `chat_mode` ou session rows do Minha DELPI Chat.

## 9. Media session

Realtime/capture session só é persistida se continuity/audit/policy exigir.

Conceitualmente:

```text
mediaSessionId
kind/surface
actor/user ref
deviceRef?
meetingRef?/frontlineRef?/conversationRef?
active modalities
consent/policy refs
startedAt/endedAt
status
provider/config refs bounded
```

Raw stream não precisa ser armazenado para existir media session.

## 10. Retention classes

Não tratar tudo como “attachment”.

Distinguir lifecycle de:

```text
TRANSIENT_MEDIA
TRANSCRIPT
RAW_AUDIO
RAW_VIDEO
SCREEN_CAPTURE
DERIVED_EVIDENCE
MEETING_ARTIFACT
FRONTLINE_RECORD
```

Cada classe define purpose, access, retention, redaction, delete/anonymize e provider handling.

## 11. Meeting session

Meeting durable state é Copilot-owned apenas quando a feature estiver em escopo e a policy exigir persistência.

Campos conceituais:

```text
meetingId
status
subject/title
startedAt/endedAt
initiatorRef
participantRefs[]
conversationRef?
caseRef?/roomRef?
active/captured modality metadata
transcriptRef?
summaryArtifactRef?
evidenceRefs[]
decisionRefs[]
candidateActionRefs[]
taskRefs[]
retentionPolicyRef
```

Distinguir:

```text
transcript != summary != confirmed decision != executed action
```

## 12. Frontline assistance session

Persistir somente quando necessário à continuidade/audit/process improvement.

Campos conceituais:

```text
frontlineSessionId
actor/user ref
device/workstation ref
status
startedAt/endedAt
entityRefs[]  # OP, machine, product, operation, etc.
conversationRef?
media/evidence refs[]
issue/finding refs[]
escalation/task/case/request refs[]
candidateKnowledgeRefs[]
```

Não virar employee-surveillance datastore.

## 13. Derived catalogs/indexes

### Copilot Action Catalog

Authority técnica permanece no OpenAPI source; catálogo/index Copilot é derivado/versionado.

### Capability Projection

Derivada de:

```text
Business → OpenAPI/Action Catalog + authorization
Platform → Core apps/routes + generic platform actions
```

### Expertise/Playbook indexes

Catalogs são Copilot-owned; vector/search indexes são derivados e invalidáveis por version/hash.

### Business Graph index

Pode guardar `RelationshipRef`/lookup metadata/provenance, nunca master copies dos Domain objects.

## 14. Evidence

Persistir apenas quando necessário à continuidade/audit/Case/Meeting/Frontline.

```text
evidenceId
sourceRef
entityRefs[]
kind
valueRef/value bounded
location?  # page/region/frame/time-range
mediaRef?
observedAt
freshness
confidence?
limitations[]
extractor/model/version?
```

Epistemic classification:

```text
FACT
CALCULATION
HYPOTHESIS
CONCLUSION
RECOMMENDATION
```

Visual/audio finding não vira FACT apenas por existir modelo multimodal.

## 15. Decision Gate

Copilot-owned lifecycle; final Domain API authorization continua obrigatória.

```text
decisionId
workflowId?/turnId?/meetingId?/frontlineSessionId?
actionRef
requiredGate
argumentsHash
impactPreview
evidenceRefs[]
risk/sensitivity
status
requestedAt/expiresAt/decidedAt
actor/approver refs
```

## 16. Durable Workflow

Contract nasce em C0; runtime/persistence entra em C5.

Workflow:

```text
workflowId
conversationId?
caseId?/taskId?
meetingId?/frontlineSessionId?
status
planVersion
checkpoint
budget/limits refs
createdAt/updatedAt
```

Step:

```text
stepId
workflowId
capabilityRef
actionSourceRef?
dependsOn[]
status
attemptCount
idempotencyKey?
resultRef/errorCode
decisionRef?
```

Wait states:

```text
WAITING_USER
WAITING_APPROVAL
WAITING_EVENT
WAITING_TIME
```

## 17. Task

Copilot-owned product unit backed by Workflow runtime.

```text
taskId
objective
workflowRef
entityRefs[]
caseRef?
meetingRef?/frontlineRef?
status
progressRef
pendingDecisionRefs[]
resultRefs[]
evidenceRefs[]
owner
timestamps
```

Task não possui executor próprio.

## 18. Case

Copilot Case é Copilot-owned **salvo se C0 provar que um owner corporativo existente deve ser estendido**.

Se existing Requests/Case infrastructure for reused:

```text
Copilot Case semantics
→ Adapter/Port
→ existing owner
```

Nunca acesso direto à tabela de outro serviço.

Conceptual fields:

```text
caseId
title/objective
caseType
status
entityRefs[]
taskRefs[]
workflowRefs[]
evidenceRefs[]
decision/action refs
participant refs
roomRef?
meetingRefs[]?
frontlineSessionRefs[]?
timestamps
```

## 19. Evidence Board

View/state sobre `EvidenceRef`:

```text
accepted
contested
missing
superseded
```

Não cria outro evidence schema.

## 20. Interaction Room

C0 deve decidir owner após inventariar salas existentes.

Preferência:

```text
Case stores roomRef
messages/files stay with room owner
Copilot uses authorized adapter
```

Não duplicar sala nem conteúdo integral se existing owner atende.

Meeting artifact pode ser referenciado por Room/Case sem duplicar transcript/raw media.

## 21. Inbox

Copilot API é owner da **semântica de work inbox**; delivery/presentation pode usar Portal/Core infrastructure.

```text
inboxItemId
kind
sourceRef(task/case/workflow/decision/watch/meeting)
status
priority/severity
entityRefs[]
timestamps
```

## 22. Event / Watch

`EventEnvelope` é shared Copilot contract para ingestão/correlação de eventos de platform/domain owners.

Watch:

```text
watchId
owner
condition/ref
mode OBSERVE|ADVISE|ACT
entity/capability scope
status
cooldown/dedupe policy
expiresAt?
timestamps
```

ACT revalida authorization/policy no disparo.

## 23. Organizational Knowledge

Reference/Decision/Experience/Solution Pattern records precisam:

```text
id/version
owner/source refs
provenance
lifecycle
review/eval metadata
timestamps
```

Meeting/process/frontline observation pode gerar **candidate**, nunca published truth diretamente.

No CoT.

## 24. Copilot preferences/projects

Se projeto/contexto persistente for necessário:

- preferred expertise;
- allowed knowledge scopes refs;
- files;
- artifact templates;
- guidance.

Nunca concede permission/capability.

## 25. Idempotência e concurrency

Write preference:

1. native Domain API idempotency;
2. domain use-case idempotency;
3. Copilot orchestration guard when necessary.

Resume exige dedupe, checkpoint consistency, ambiguous-outcome verification and locking/lease strategy where needed.

Voice/Meeting/Frontline repeated utterance/event não pode duplicar Business Action.

## 26. Shared-device isolation

Quando device é compartilhado:

```text
end user session
→ clear local auth/context/media cache
→ invalidate bounded session refs
→ next user starts clean context
```

Nunca reutilizar conversation/meeting/frontline state de usuário anterior por conveniência.

## 27. OT/machine state

Copilot não persiste “machine truth” própria. Estado de máquina vem do owner OT/domain system.

Se futura atuação OT existir:

```text
machine command request
→ typed/deterministic contract
→ industrial safety/authorization owner
→ machine state/precondition check
→ independent interlocks
→ verified outcome
```

Nenhum LLM-generated free-form command vira machine instruction direta.

## 28. Retention/LGPD

Por tabela/record/media class novo definir:

```text
purpose
owner
minimum fields
retention
access model
consent/policy ref when needed
audit
redaction
archive/delete/anonymize
provider processing
```

## 29. Migration strategy

Copilot migrations são independentes e seguem:

```text
expand additive
→ compatible readers
→ writers
→ backfill if required
→ cutover
→ monitor
→ cleanup
```

Não existe migration Chat→Copilot como requisito desta iniciativa.

## 30. State machines

### Platform Command
```text
PROPOSED → VALIDATED → TARGET_RESOLVED → EXECUTED → SUCCEEDED|REJECTED|FAILED
```

### Workflow
```text
PLANNED → RUNNING
          ├→ WAITING_USER ──────┐
          ├→ WAITING_APPROVAL ──┤
          ├→ WAITING_EVENT ─────┤
          └→ WAITING_TIME ──────┤
                                 ↓
                              RUNNING
                                 ↓
                  SUCCEEDED|PARTIAL|FAILED|CANCELLED
```

### Decision
```text
REQUESTED → PENDING → ACKNOWLEDGED|CONFIRMED|APPROVED|REJECTED|EXPIRED|INVALIDATED|BLOCKED
```

### Media Session
```text
CREATED → CAPTURING → PROCESSING? → STOPPED → COMPLETED|FAILED|CANCELLED
```

### Meeting
```text
DRAFT → ACTIVE → ENDING → COMPLETED|FAILED|CANCELLED
```

### Frontline Session
```text
READY → ACTIVE → WAITING_HELP|ESCALATED? → COMPLETED|CANCELLED|FAILED
```

Final states/lifecycles só são congelados em C0/C6 se runtime provar necessidade; não criar tabelas apenas por este desenho conceitual.

## 31. Explicitamente proibido

- Chat conversation/session/agent tables como Copilot storage;
- foreign-key do Copilot para internal Chat row;
- migration do Chat alterada para feature Copilot;
- manual endpoint→intent table;
- graph master copies;
- feature-specific Evidence;
- confirmation parallel to Decision Gate;
- Task engine parallel to Workflow runtime;
- duplicated Room storage when owner exists;
- CoT persistence;
- credentials/tokens in state;
- raw audio/video retention sem policy;
- biometric/employee-surveillance dataset por default;
- machine-control state tratado como Copilot authority.