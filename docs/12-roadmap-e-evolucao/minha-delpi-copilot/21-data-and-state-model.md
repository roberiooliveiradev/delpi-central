# Minha DELPI Copilot — Modelo de Dados, Estado e Persistência

**Status:** target arquitetural standalone  
**Autoridade de ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)  
**Biometric/Human Observation:** [`54-biometric-identity-and-human-observation-governance.md`](./54-biometric-identity-and-human-observation-governance.md)

## 1. Princípio

Todo estado durável do produto Copilot pertence à **Copilot API nova** ou a um owner corporativo explicitamente referenciado.

```text
REFERENCE
→ refs para entities/sources/users de owners externos

COPILOT RUNTIME STATE
→ conversations/turns/plans/context snapshots

COPILOT DURABLE WORK STATE
→ decision/workflow/task/case/watch/inbox semantics

COPILOT COLLAB/MEDIA/BIOMETRIC STATE
→ meeting/frontline/media/biometric metadata only when required

DERIVED INDEX/CACHE
→ capabilities/expertise/graph/search indexes

DOMAIN DATA
→ permanece nas Domain APIs

CORPORATE USER IDENTITY
→ permanece Keycloak/Core-owned
```

**Proibido:** usar tabelas/sessions/agents/migrations do Minha DELPI Chat como foundation do Copilot ou criar um shadow user directory biométrico como nova authority corporativa.

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

Biometric template storage pode exigir storage/keys diferentes do banco transacional comum; C0 deve decidir o owner/adapter apropriado antes de criar tabela.

## 3. Regra C0

Antes de criar migrations, C0 define:

- DB/schema/table naming convention;
- IDs;
- versioning;
- retention/LGPD;
- media retention classes;
- biometric data/template retention class;
- enrollment/revocation/deletion lifecycle;
- consent/policy references;
- encryption/key management;
- indexes;
- concurrency/idempotency;
- migration/rollback strategy;
- quais dados são Copilot-owned versus refs/projections;
- quais existing rooms/notifications/events são referenciados por adapter;
- se `MediaRef` ou primitive equivalente é necessário;
- se biometric/person-observation refs são necessários;
- shared-device session boundaries;
- o que nunca pode ser durable raw media/template por default.

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

### UserRef

O Copilot referencia usuário corporativo por identificador canônico resolvido a partir de Keycloak/Core.

```text
userRef
→ corporate identity authority
```

Biometric enrollment/candidate aponta para `userRef`; não cria outro usuário.

### SourceRef / EvidenceRef / OutcomeRef

Copilot-owned contract usado transversalmente por:

- conversation synthesis;
- API results;
- multimodal;
- media;
- biometric identity evidence;
- Human Observation;
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
confirmed/current userRef from authenticated session
```

Nunca persistir como truth:

- DOM/React state;
- tokens/secrets;
- datasets completos;
- permissions;
- biometric candidate como permission truth;
- provider biometric payloads desnecessários.

## 7. Device/session metadata

Device identity não é user identity.

Bounded metadata candidato:

```text
deviceRef/workstationRef
surface: global|workspace|meeting|frontline
deviceClass: desktop|tablet|kiosk|room|mobile|other
sessionStartedAt
capability flags: mic/camera/screen/touch/audioOut/biometricReady?
```

Não deve conter permission truth nem substituir autenticação do usuário.

## 8. Biometric identity state

Separar quatro conceitos:

```text
RAW BIOMETRIC MEDIA
→ foto/frame/audio/video usados no enrollment/match quando necessário

BIOMETRIC ENROLLMENT
→ relação governada userRef + modality + purpose + lifecycle

BIOMETRIC TEMPLATE
→ representação protegida usada para matching

IDENTITY CANDIDATE / ASSOCIATION
→ resultado de uma observação/match em uma sessão
```

### Candidate `BiometricEnrollmentRef`

Somente se C0 confirmar ownership/modelo:

```text
enrollmentId
userRef
modality: face|voice
purpose/policyRef
status
createdAt/updatedAt/revokedAt/deletedAt?
templateVersion/modelVersion
retentionClass
quality metadata bounded
```

Lifecycle conceitual:

```text
PENDING → ACTIVE → REVOKED | DELETED
```

### Biometric template

Não deve ser tratado como attachment comum.

Requisitos:

```text
templateId/ref
enrollmentRef
modality
model/template version
encrypted/protected storageRef
createdAt
status
```

Não incluir embedding/template em:

- ordinary logs;
- MFE payload comum;
- generic Evidence value;
- analytics export genérico.

### Candidate `BiometricIdentityCandidate`

```text
candidateId
candidateUserRef?
modality
confidence
media/sourceRef
meeting/frontline/mediaSession ref?
deviceRef?
modelVersion
templateVersion?
policyRef
status: UNKNOWN|CANDIDATE|CONFIRMED|CORRECTED|REJECTED
observedAt
```

Invariante:

```text
BiometricIdentityCandidate != authenticated session != permission grant
```

Low confidence pode persistir apenas como `UNKNOWN`/session-local evidence quando necessário; não forçar associação.

Correção de associação não altera enrollment/template automaticamente.

## 9. Human Observation state

Se C0/C3 provarem necessidade, usar `PersonObservationRef` ou equivalente **somente para observações objetivas ligadas ao processo**.

Semântica candidata:

```text
observationId
sessionRef
userRef?              # apenas quando necessário/autorizado
entityRefs[]           # OP/machine/product/operation...
media/evidence refs[]
observationType
observed facts bounded
confidence?
limitations[]
observedAt
```

Não armazenar campos de:

```text
personality score
honesty/trust score
emotion truth
loyalty
mental/health diagnosis
sensitive attribute inference
global employee score
disciplinary propensity
```

O objetivo é descrever processo/comportamento observável, não criar perfil psicológico do trabalhador.

## 10. Copilot conversations

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
identity candidate refs?  # somente quando material
plan/outcome/evidence refs
model/config metadata bounded
createdAt
```

Não armazenar chain-of-thought.

Não utilizar `agent_id`, `chat_mode` ou session rows do Minha DELPI Chat.

## 11. Media session

Realtime/capture session só é persistida se continuity/audit/policy exigir.

Conceitualmente:

```text
mediaSessionId
kind/surface
actor/user ref
deviceRef?
meetingRef?/frontlineRef?/conversationRef?
active modalities
identityRecognitionEnabled?
consent/policy refs
startedAt/endedAt
status
provider/config refs bounded
```

Raw stream não precisa ser armazenado para existir media session.

## 12. Retention classes

Não tratar tudo como “attachment”.

Distinguir lifecycle de:

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
MEETING_ARTIFACT
FRONTLINE_RECORD
```

Cada classe define purpose, access, retention, encryption/redaction, revoke/delete/anonymize e provider handling.

Apagar enrollment/template deve impedir matches futuros conforme contract, independentemente de retention permitida para alguma Evidence já produzida.

## 13. Meeting session

Meeting durable state é Copilot-owned apenas quando a feature estiver em escopo e a policy exigir persistência.

Campos conceituais:

```text
meetingId
status
subject/title
startedAt/endedAt
initiatorRef
participantRefs[]
participantIdentityCandidateRefs[]?
conversationRef?
caseRef?/roomRef?
active/captured modality metadata
identityRecognitionEnabled?
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
transcript != summary != identity candidate != confirmed participant association != confirmed decision != executed action
```

## 14. Frontline assistance session

Persistir somente quando necessário à continuidade/audit/process improvement.

Campos conceituais:

```text
frontlineSessionId
actor/user ref
identityCandidateRef?  # se biometric assistance participou da resolução
device/workstation ref
status
startedAt/endedAt
entityRefs[]  # OP, machine, product, operation, etc.
conversationRef?
media/evidence refs[]
personObservationRefs[]?
issue/finding refs[]
escalation/task/case/request refs[]
candidateKnowledgeRefs[]
```

Não virar employee-surveillance datastore.

## 15. Derived catalogs/indexes

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

Pode guardar `RelationshipRef`/lookup metadata/provenance, nunca master copies dos Domain objects ou biometric person profiles.

## 16. Evidence

Persistir apenas quando necessário à continuidade/audit/Case/Meeting/Frontline.

```text
evidenceId
sourceRef
entityRefs[]
userRef?              # somente quando necessário/autorizado
kind
valueRef/value bounded
location?  # page/region/frame/time-range
mediaRef?
identityCandidateRef?
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

Visual/audio/Human Observation finding não vira FACT apenas por existir modelo multimodal.

## 17. Decision Gate

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

Biometric identity candidate não substitui `actor/approver` autenticado.

## 18. Durable Workflow

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

## 19. Task

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

## 20. Case

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

## 21. Evidence Board

View/state sobre `EvidenceRef`:

```text
accepted
contested
missing
superseded
```

Não cria outro evidence schema.

## 22. Interaction Room

C0 deve decidir owner após inventariar salas existentes.

Preferência:

```text
Case stores roomRef
messages/files stay with room owner
Copilot uses authorized adapter
```

Não duplicar sala nem conteúdo integral se existing owner atende.

Meeting artifact pode ser referenciado por Room/Case sem duplicar transcript/raw media/biometric template.

## 23. Inbox

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

## 24. Event / Watch

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

## 25. Organizational Knowledge

Reference/Decision/Experience/Solution Pattern records precisam:

```text
id/version
owner/source refs
provenance
lifecycle
review/eval metadata
timestamps
```

Meeting/process/frontline/Human Observation pode gerar **candidate**, nunca published truth diretamente.

Preferir knowledge abstraído para processo, não perfis de pessoa, salvo autoria/participação necessária e autorizada.

No CoT.

## 26. Copilot preferences/projects

Se projeto/contexto persistente for necessário:

- preferred expertise;
- allowed knowledge scopes refs;
- files;
- artifact templates;
- guidance.

Nunca concede permission/capability.

## 27. Idempotência e concurrency

Write preference:

1. native Domain API idempotency;
2. domain use-case idempotency;
3. Copilot orchestration guard when necessary.

Resume exige dedupe, checkpoint consistency, ambiguous-outcome verification and locking/lease strategy where needed.

Voice/Meeting/Frontline repeated utterance/event não pode duplicar Business Action.

## 28. Shared-device isolation

Quando device é compartilhado:

```text
end user session
→ clear local auth/context/media/biometric-candidate cache
→ invalidate bounded session refs
→ next user starts clean context
```

Nunca reutilizar conversation/meeting/frontline/identity-candidate state de usuário anterior por conveniência.

## 29. OT/machine state

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

## 30. Retention/LGPD

Por tabela/record/media/biometric class novo definir:

```text
purpose
owner
minimum fields
retention
access model
consent/policy ref when needed
audit
encryption/key boundary when needed
redaction
archive/delete/anonymize/revoke
provider processing
```

## 31. Migration strategy

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

Biometric template/model migration exige versão explícita e estratégia de compatibilidade/reenrollment; não reinterpretar embeddings incompatíveis silenciosamente.

## 32. State machines

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

### Biometric Enrollment
```text
PENDING → ACTIVE → REVOKED|DELETED
```

### Identity Candidate
```text
OBSERVED → UNKNOWN|CANDIDATE → CONFIRMED|CORRECTED|REJECTED
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

## 33. Explicitamente proibido

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
- biometric template/embedding em ordinary logs;
- biometric shadow user directory;
- open-world person-identification dataset por default;
- personality/emotion/trustworthiness/health/sensitive-attribute profile;
- hidden employee-surveillance/productivity score dataset;
- automatic employment decision state derived from biometrics/Human Observation;
- machine-control state tratado como Copilot authority.
