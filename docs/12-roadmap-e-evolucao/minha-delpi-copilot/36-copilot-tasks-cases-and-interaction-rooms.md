# Minha DELPI Copilot — Tasks, Cases e Salas de Interação

**Status:** thematic spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Runtime owner:** Durable Workflow foundation em C5; Task/Case/Room product features em C6.

## 1. Unidades de trabalho

```text
Turn → interação curta
Task → objetivo delimitado multi-step
Case → investigação/trabalho persistente
Interaction Room → colaboração humana ligada a Case/Task
```

O usuário pode começar pela conversa e evoluir para Task/Case quando a natureza do trabalho exigir.

## 2. Foundations

Reutilizar CorrelationContext, EntityRef, EvidenceRef, OutcomeRef, Decision refs, WorkflowPlan/Step, TaskRef e CaseRef. Não criar modelos paralelos por feature.

## 3. Copilot Task

Task é uma unidade de produto sobre Durable Workflow.

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
owner/createdBy
createdAt/updatedAt
```

Status alinha ao lifecycle canônico; frontend não cria enum incompatível.

## 4. Copilot Case

Case organiza investigação/trabalho longo:

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
participant refs
roomRef?
timestamps
```

Lifecycle conceitual:

```text
open → investigating/waiting/actioning → resolved/closed → reopened
```

Se C0 provar owner corporativo existente adequado, usar Adapter/Port em vez de criar tabela paralela automaticamente.

## 5. Evidence Board

Organiza os mesmos `EvidenceRef` como:

```text
accepted
contested
missing
superseded
```

Não duplica source/value/provenance.

## 6. Interaction Room

C0 deve inventariar as salas existentes, inclusive Portal Comercial, antes de definir owner.

Preferência:

```text
CaseRef/TaskRef
↔ RoomRef
```

Room owner mantém participants/messages/files/timeline. Copilot usa adapter autorizado e não copia tudo para Case state quando refs atendem.

## 7. Relações

```text
Conversation → may create/open Task/Case
Case + Evidence + Expertise + Playbook → WorkflowPlan/Tasks
Case EntityRefs → Business Graph/source owners
```

Case não é agent nem executor.

## 8. Permissions

```text
Case/Room access ≠ source entity permission
```

Toda source read/action continua sujeita a current RBAC/policy. Materializações respeitam retention/redaction/classification.

## 9. Durable behavior

Task/Case sobrevivem a F5, API/worker restart, waits, partial failure, cancel/expiry e resume sem repeat write.

## 10. UX surfaces

```text
Copilot Conversation
Tasks
Cases
Evidence Board
Case Timeline
Interaction Room
Decision/Action panel
Artifacts
Inbox
```

Todas usam o mesmo Copilot MFE/API; não existe segunda app de Cases.

## 11. Phase mapping

```text
C0 → Task/Case contracts + Room/Case owner inventory
C5 → Durable Workflow/checkpoints/waits foundation
C6.S1 → Task
C6.S2 → Case + Evidence Board
C6.S3 → Room integration
C6.S4 → Inbox
C6 → product reload/lifecycle/integration gates
```

## 12. Independence

Task/Case state pertence à Copilot API ou a owner corporativo adaptado; nunca às tabelas/sessions do Minha DELPI Chat.

## 13. Gate C6

Case só é produto real com structured lifecycle, shared refs, Workflow/Task integration, permissions, timeline/outcomes e persistence/reload quando necessário.

Uma conversa renomeada como “Case” não atende.