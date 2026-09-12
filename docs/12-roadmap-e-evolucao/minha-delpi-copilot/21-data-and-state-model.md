# Minha DELPI Copilot — Modelo de Dados, Estado e Persistência

**Status:** target arquitetural foundation-first  
**Autoridade de ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)

## 1. Princípio

Separar claramente:

```text
REFERENCE
→ identidade/ref compartilhada

RUNTIME STATE
→ estado efêmero do turno/UI

DURABLE WORK STATE
→ workflow/task/case/decision/watch quando necessário

DERIVED INDEX/CACHE
→ capability/expertise/graph/search materializado

DOMAIN DATA
→ continua nas APIs/bancos donos do domínio
```

Não criar banco paralelo de dados operacionais, capability contracts ou chain-of-thought.

## 2. Regra de C0

C0 define **semântica, IDs, relações e ports** antes de decidir migrations.

C0.S0 deve provar:

- quais tabelas/repositories já existem;
- quais estados de conversa/workflow/approval existem;
- quais entity IDs são estáveis;
- quais rooms/notifications/cases podem ser reutilizados;
- quais event stores/queues existem;
- quais caches/indexes já são materializados.

Somente gaps reais justificam novas migrations.

## 3. Shared references

### 3.1 Correlation

Todo fluxo material deve ser correlacionável por um conjunto coerente de IDs:

```text
requestId
conversationId
turnId
workflowId?
taskId?
caseId?
traceId?
```

Não gerar um universo de IDs sem relação entre si por feature.

### 3.2 EntityRef

Referência lógica e compacta:

```text
entityType
entityId
sourceSystem/domain
label?
version/revision? quando material
```

Domain object completo continua no owner.

### 3.3 SourceRef / EvidenceRef / OutcomeRef

`SourceRef` aponta origem verificável.  
`EvidenceRef` registra observação/claim sourceable.  
`OutcomeRef` registra resultado real de execução.

Esses conceitos são transversais e devem ser reutilizados por:

- Chat;
- multimodal;
- Business Graph;
- workflow;
- Task;
- Case/Evidence Board;
- Simulation;
- audit/presentation.

Não criar variants incompatíveis por feature.

## 4. Workspace Context

**Owner primário:** Portal/MFE/iframe em runtime.  
**Persistência:** efêmera por padrão; snapshot bounded no turno somente quando necessário.

Campos conceituais:

```text
version
appId
routeId
entityRefs[]
filters
selection
dateRange
visibleDataRefs[]
source
updatedAt
```

Não persistir:

- estado React/DOM;
- tokens/secrets;
- datasets completos;
- campos sem finalidade.

## 5. Derived catalogs/indexes

### Capability Projection

Derivada das authorities:

```text
Business → OpenAPI/Action Catalog
Platform → Core apps/routes + generic action definitions
```

### Expertise/Playbook indexes

Authority é o catálogo canônico; embedding/vector/search é materialização derivada e invalidável por version/hash.

### Business Graph index

Pode materializar relações/referências, mas:

- não replica objetos operacionais completos;
- registra source/provenance;
- respeita lifecycle do source;
- traversal revalida permission quando necessário.

## 6. Evidence e epistemic state

Persistir evidence somente quando houver finalidade de continuidade/audit/Case.

Campos conceituais:

```text
evidenceId
sourceRef
entityRefs[]
kind
valueRef/value bounded
location/page/region?
observedAt
freshness
confidence?
limitations[]
extractor/version? quando multimodal
```

Classificação da síntese:

```text
FACT
CALCULATION
HYPOTHESIS
CONCLUSION
RECOMMENDATION
```

Hipótese/conclusão/recomendação não devem se disfarçar de source fact.

## 7. Decision Gate lifecycle

Unifica confirmation e approvals sob um modelo consistente.

Campos conceituais:

```text
decisionId
workflowId?/turnId?
stepId?/actionRef
requiredGate
argumentsHash
impactPreview
evidenceRefs[]
risk/sensitivity
status
requestedAt
expiresAt
decidedAt
decision
actor/approver refs
```

Gate levels:

```text
NO_GATE
ACKNOWLEDGE
CONFIRM
REVIEW_AND_CONFIRM
APPROVAL_WORKFLOW
BLOCK
```

Status mínimos:

```text
pending
acknowledged
confirmed
rejected
approved
expired
invalidated
blocked
```

Mudança material de argumentos, evidence ou policy invalida decisão quando aplicável.

## 8. Durable Workflow

Contrato semântico nasce em C0; persistence/runtime concreto nasce em C5 se gap for provado.

### Workflow

```text
workflowId
conversationId?
turnId?
subjectRef
planVersion
status
currentCheckpoint
createdAt
updatedAt
budget/limits refs
```

Status:

```text
planned
running
waiting_user
waiting_approval
waiting_event
waiting_time
succeeded
partially_succeeded
failed
cancelled
expired
```

### Workflow Step

```text
stepId
workflowId
capabilityRef
actionSourceRef?
dependsOn[]
status
attemptCount
idempotencyKey?
startedAt
finishedAt
resultRef/errorCode
decisionRef?
```

## 9. Copilot Task

Task é uma unidade de trabalho curta/média, normalmente backed por workflow.

Campos conceituais:

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
createdBy/owner
createdAt/updatedAt
```

Não criar engine separada para Task.

## 10. Copilot Case

Case é unidade de investigação/trabalho prolongado, não necessariamente um novo banco se C0 provar que conceito existente pode ser estendido.

Campos conceituais:

```text
caseId
title/objective
caseType
status
entityRefs[]
taskRefs[]
workflowRefs[]
evidenceRefs[]
hypothesis/decision/action refs
authorized participant refs
roomRef?
createdAt/updatedAt/closedAt
```

Lifecycle conceitual:

```text
open
investigating
waiting
actioning
resolved
closed
reopened
```

Case não substitui permissões das entidades fontes.

## 11. Evidence Board

É uma view/estrutura sobre `EvidenceRef`, não um segundo modelo de evidence.

Estados de board podem incluir:

```text
accepted
contested
missing
superseded
```

A classificação não altera a origem do evidence.

## 12. Interaction Room

Preferir owner existente.

Case armazena `roomRef`; mensagens/arquivos ficam no owner da sala. O Copilot acessa somente via permissions adequadas.

Não duplicar conteúdo integral da sala dentro do Case.

## 13. Inbox

Inbox deve preferir materialização/view sobre estados de Task/Case/Workflow/Decision/Watch, não novo workflow owner.

Item conceitual:

```text
inboxItemId
kind
sourceRef(task/case/workflow/decision/watch)
status
priority/severity
entityRefs[]
createdAt
resolvedAt?
```

Ler item não executa ação.

## 14. Event / Watch

### EventEnvelope

```text
eventId
eventType
source
entityRefs[]
occurredAt
payloadRef/payload bounded
correlation
schemaVersion
```

### Watch

```text
watchId
owner/user subject
condition/ref
mode OBSERVE|ADVISE|ACT
entity/capability scope
status
cooldown/dedupe policy
expiresAt?
createdAt/updatedAt
```

ACT continua sujeito a autonomy/Decision Gate/policy no momento do disparo.

## 15. Organizational Knowledge

Reference/Decision/Experience/Solution Pattern precisam de:

```text
id/version
owner
source refs
provenance
status draft/review/published/deprecated
review/eval metadata
createdAt/updatedAt
```

Não armazenar CoT em Decision/Experience record.

## 16. Project preferences

Projeto pode persistir:

- preferred expertise;
- knowledge scopes permitidos;
- files;
- artifact templates;
- guidance.

Não pode conceder permission/capability.

## 17. Idempotência e concurrency

Ordem de preferência para write:

1. idempotency contract nativo da API;
2. domain use case idempotente;
3. orchestration protection apenas quando necessária e explícita.

Workflow resume exige:

- dedupe de command/event;
- atomic checkpoint onde possível;
- tratamento de ambiguous outcome;
- locking/lease/concurrency strategy documentada.

Nunca assumir que `POST` é retry-safe.

## 18. Retention e LGPD

Por novo dado durável definir:

```text
purpose
owner
minimum fields
retention
access model
audit
redaction
archive/delete/anonymize policy
```

Case/Evidence/Room/Experience podem conter dados sensíveis e exigem atenção explícita.

## 19. Migration strategy

Toda migration segue:

```text
expand additive
→ compatible readers
→ writers
→ backfill se necessário
→ cutover
→ monitor
→ cleanup posterior
```

Não misturar criação de todos os modelos C5 em uma migration monolítica.

## 20. State machines

### Platform Command

```text
PROPOSED
→ VALIDATED
→ AUTHORIZED_TARGET_RESOLVED
→ EXECUTED
→ SUCCEEDED | REJECTED | FAILED
```

### Durable Workflow

```text
PLANNED
→ RUNNING
   ├→ WAITING_USER ───────┐
   ├→ WAITING_APPROVAL ───┤
   ├→ WAITING_EVENT ──────┤
   └→ WAITING_TIME ───────┤
                           ↓
                        RUNNING
                           │
              ┌────────────┼────────────┐
              ↓            ↓            ↓
         SUCCEEDED    PARTIAL       FAILED/CANCELLED
```

### Decision Gate

```text
REQUESTED
→ PENDING
→ ACKNOWLEDGED | CONFIRMED | APPROVED | REJECTED | EXPIRED | INVALIDATED | BLOCKED
```

## 21. O que explicitamente não criar

- tabela manual endpoint→intent;
- cópia do OpenAPI por capability;
- graph replicando tabelas operacionais;
- evidence model diferente por Case/Workflow/Multimodal;
- confirmation paralelo ao Decision Gate;
- Task engine independente do Workflow runtime;
- Room storage duplicado no Copilot se já houver owner;
- Watch event envelope próprio se o comum atende;
- memory paralela por app/case;
- CoT persistence;
- tokens/credentials em state.