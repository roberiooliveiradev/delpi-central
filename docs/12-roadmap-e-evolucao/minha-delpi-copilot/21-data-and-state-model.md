# Minha DELPI Copilot — Modelo de Dados, Estado e Persistência

**Status:** target arquitetural standalone  
**Autoridade de ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)

## 1. Princípio

Todo estado durável do produto Copilot pertence à **Copilot API nova** ou a um owner corporativo explicitamente referenciado.

```text
REFERENCE
→ refs para entities/sources de owners externos

COPILOT RUNTIME STATE
→ conversations/turns/plans/context snapshots

COPILOT DURABLE WORK STATE
→ decision/workflow/task/case/watch/inbox semantics

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
- indexes;
- concurrency/idempotency;
- migration/rollback strategy;
- quais dados são Copilot-owned versus refs/projections;
- quais existing rooms/notifications/events são referenciados por adapter.

## 4. Shared references

### CorrelationContext

```text
requestId
conversationId
turnId
workflowId?
taskId?
caseId?
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

### SourceRef / EvidenceRef / OutcomeRef

Copilot-owned contract usado transversalmente por:

- conversation synthesis;
- API results;
- multimodal;
- Business Graph;
- workflow;
- Task/Case;
- Simulation;
- audit/presentation.

Não existe dependência do evidence/state model do Chat.

## 5. Workspace Context

**Owner primário em runtime:** Portal/MFE/iframe.  
**Copilot persistence:** snapshot bounded somente quando necessário à conversa/workflow/audit.

Nunca persistir:

- DOM/React state;
- tokens/secrets;
- datasets completos;
- permissions como truth source.

## 6. Copilot conversations

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
plan/outcome/evidence refs
model/config metadata bounded
createdAt
```

Não armazenar chain-of-thought.

Não utilizar `agent_id`, `chat_mode` ou session rows do Minha DELPI Chat.

## 7. Derived catalogs/indexes

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

## 8. Evidence

Persistir apenas quando necessário à continuidade/audit/Case.

```text
evidenceId
sourceRef
entityRefs[]
kind
valueRef/value bounded
location?
observedAt
freshness
confidence?
limitations[]
extractor/version?
```

Epistemic classification:

```text
FACT
CALCULATION
HYPOTHESIS
CONCLUSION
RECOMMENDATION
```

## 9. Decision Gate

Copilot-owned lifecycle; final Domain API authorization continua obrigatória.

```text
decisionId
workflowId?/turnId?
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

## 10. Durable Workflow

Contract nasce em C0; runtime/persistence entra em C5.

Workflow:

```text
workflowId
conversationId?
caseId?/taskId?
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

## 11. Task

Copilot-owned product unit backed by Workflow runtime.

```text
taskId
objective
workflowRef
entityRefs[]
caseRef?
status
progressRef
pendingDecisionRefs[]
resultRefs[]
evidenceRefs[]
owner
timestamps
```

Task não possui executor próprio.

## 12. Case

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
timestamps
```

## 13. Evidence Board

View/state sobre `EvidenceRef`:

```text
accepted
contested
missing
superseded
```

Não cria outro evidence schema.

## 14. Interaction Room

C0 deve decidir owner após inventariar salas existentes.

Preferência:

```text
Case stores roomRef
messages/files stay with room owner
Copilot uses authorized adapter
```

Não duplicar sala nem conteúdo integral se existing owner atende.

## 15. Inbox

Copilot API é owner da **semântica de work inbox**; delivery/presentation pode usar Portal/Core infrastructure.

```text
inboxItemId
kind
sourceRef(task/case/workflow/decision/watch)
status
priority/severity
entityRefs[]
timestamps
```

## 16. Event / Watch

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

## 17. Organizational Knowledge

Reference/Decision/Experience/Solution Pattern records precisam:

```text
id/version
owner/source refs
provenance
lifecycle
review/eval metadata
timestamps
```

No CoT.

## 18. Copilot preferences/projects

Se projeto/contexto persistente for necessário:

- preferred expertise;
- allowed knowledge scopes refs;
- files;
- artifact templates;
- guidance.

Nunca concede permission/capability.

## 19. Idempotência e concurrency

Write preference:

1. native Domain API idempotency;
2. domain use-case idempotency;
3. Copilot orchestration guard when necessary.

Resume exige dedupe, checkpoint consistency, ambiguous-outcome verification and locking/lease strategy where needed.

## 20. Retention/LGPD

Por tabela/record novo definir:

```text
purpose
owner
minimum fields
retention
access model
audit
redaction
archive/delete/anonymize
```

## 21. Migration strategy

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

## 22. State machines

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

## 23. Explicitamente proibido

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
- credentials/tokens in state.