# DÉLIA — Tasks, Cases e Salas de Interação

**Status:** thematic spec / TARGET  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Runtime owner:** DÉLIA Durable Work foundation em C5 após gates; Task/Case/Room product features em C6.

## 1. Unidades de trabalho

```text
Turn → interação curta
Task → objetivo delimitado multi-step
Case → investigação/trabalho persistente
Interaction Room → colaboração humana ligada a Case/Task
```

O usuário pode começar pela conversa e evoluir para Task/Case quando a natureza do trabalho exigir.

## 2. Foundations

`CorrelationContext`, `EntityRef`, `EvidenceRef`, `OutcomeRef`, Decision refs, `WorkflowPlan/Step`, `TaskRef` e `CaseRef` são contracts TARGET a reutilizar **somente se C0 os comprovar/congelar**. Não criar modelos paralelos por feature nem tratar a lista como implementação existente.

## 3. DÉLIA Task

Task é uma unidade de produto sobre DÉLIA Durable Work.

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

Status alinha ao lifecycle canônico quando congelado; frontend não cria enum incompatível.

## 4. DÉLIA Case

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

Lifecycle conceitual, somente se a necessidade real justificar State Machine:

```text
open → investigating/waiting/actioning → resolved/closed → reopened
```

Se C0 provar owner corporativo existente adequado, usar Adapter/Port conforme Abstraction Gate em vez de criar tabela paralela automaticamente.

## 5. Evidence Board

Organiza os mesmos `EvidenceRef` como, se esse lifecycle/classification for aprovado:

```text
accepted
contested
missing
superseded
```

Não duplica source/value/provenance e não transforma classificação de Case em source truth externa.

## 6. Interaction Room

C0 deve inventariar as salas existentes, inclusive qualquer implementação no Portal/Apps, antes de definir owner/contrato.

Preferência target:

```text
CaseRef/TaskRef
↔ RoomRef
```

Room owner mantém participants/messages/files/timeline. DÉLIA usa adapter autorizado e não copia tudo para Case state quando refs atendem.

## 7. Relações

```text
Conversation → may create/open Task/Case
Case + Evidence + Expertise + Playbook → WorkflowPlan/Tasks
Case EntityRefs → Business Graph/source owners
```

Case não é agent, permission authority nem technical executor.

## 8. Permissions

```text
Case/Room access ≠ source entity permission
```

Toda source read/action continua sujeita a current Core/domain/provider authorization e DÉLIA Policy/Decision quando aplicável. Materializações respeitam retention/redaction/classification.

## 9. Durable behavior

Quando implementados, Task/Case sobrevivem a F5, DÉLIA API/Work-worker restart, waits, partial failure, cancel/expiry e resume sem repeat write.

Automation Hub technical execution state permanece externo; Task/Case guardam apenas refs/correlation/outcomes necessários ao Work lifecycle.

## 10. UX surfaces

```text
DÉLIA Conversation
Tasks
Cases
Evidence Board
Case Timeline
Interaction Room
Decision/Action panel
Artifacts
Inbox
```

Todas usam o mesmo DÉLIA MFE/API; não existe segunda app/planner de Cases por default.

## 11. Phase mapping

```text
C0 → Task/Case contracts + Room/Case owner inventory
C5 → Durable Work/checkpoints/waits foundation conforme 16
C6 → Task/Case/Room/Inbox consumers conforme substeps canônicos de 16
```

Este documento não redefine numeração atômica de substeps; `16` é authority exclusiva.

## 12. Independence

Task/Case state pertence ao runtime da DÉLIA quando realmente owned, ou a owner corporativo adaptado; nunca às tabelas/sessions do Minha DELPI Chat.

Também não duplica technical execution truth do Automation Hub.

## 13. Gate C6

Case só é produto real com structured lifecycle justificado, shared refs aprovadas, Workflow/Task integration, permissions, timeline/outcomes e persistence/reload quando necessário.

Uma conversa renomeada como “Case”, documentação de schema ou tabela sem wiring/behavior/evidence não atende o gate.
