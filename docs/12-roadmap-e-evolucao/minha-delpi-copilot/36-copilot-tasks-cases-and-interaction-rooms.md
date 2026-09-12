# Minha DELPI Copilot — Tasks, Cases e Salas de Interação

**Status:** thematic spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Runtime owner:** Durable Workflow C5; Task/Case não criam executors próprios.

## 1. Unidades de trabalho

```text
Turn
→ interação curta

Task
→ objetivo delimitado multi-step

Case
→ investigação/trabalho persistente

Interaction Room
→ colaboração humana ligada a Case/Task quando aplicável
```

O usuário pode começar pelo chat e evoluir para Task/Case quando a natureza do trabalho exigir.

## 2. Foundations

Reutilizar:

```text
CorrelationContext
EntityRef
EvidenceRef
OutcomeRef
DecisionGate refs
WorkflowPlan/Step
TaskRef
CaseRef
```

Não criar Entity/Evidence/Decision models próprios desta feature.

## 3. Copilot Task

Task é uma **view/unidade de produto sobre Durable Workflow**.

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

Status deve alinhar ao lifecycle canônico do data/state model; não criar enum incompatível no frontend.

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
createdAt/updatedAt/closedAt
```

Lifecycle canônico conceitual:

```text
open
investigating
waiting
actioning
resolved
closed
reopened
```

Se C0 identificar um domínio existente que já representa esse conceito, preferir extensão/adaptação em vez de tabela paralela `copilot_cases` automaticamente.

## 5. Evidence Board

Evidence Board é organização dos **mesmos `EvidenceRef`**:

```text
accepted
contested
missing
superseded
```

Não duplica source/value/provenance.

## 6. Interaction Room

Preferir o owner/padrão de sala existente da Minha DELPI.

```text
CaseRef/TaskRef
↔ RoomRef
```

Room owner mantém:

- participants;
- messages;
- files;
- timeline própria.

Copilot pode produzir resumo/pendências e relacionar evidence/actions, respeitando ACL.

Não copiar todas as mensagens/arquivos para Case state se refs atendem.

## 7. Relação com conversa

Uma conversa pode:

- permanecer turn-based;
- criar Task;
- criar Case;
- abrir Task/Case existente.

O Copilot pode sugerir promoção, mas não precisa perguntar quando uma Task técnica interna for necessária apenas para durability, desde que a UX/policy permita.

## 8. Relação com Expertise/Playbook

```text
Case
+ Entity/Evidence Context
+ Expertise Packs
+ Playbook
→ WorkflowPlan/Tasks
```

Case não é agente.

## 9. Relação com Business Graph

Case guarda `EntityRef`; relações atuais são resolvidas pelo Graph/source owners.

Não persistir cópia arbitrária de todos os objetos relacionados.

## 10. Permissions

```text
Case/Room access ≠ source entity permission
```

Toda leitura/ação sobre source data continua sujeita a RBAC/policy.

Materializações em Case precisam classification/retention/redaction adequadas.

## 11. Durable behavior

Task/Case devem sobreviver a:

- F5;
- restart de worker/API;
- wait_user;
- wait_approval;
- wait_event;
- partial failure;
- cancel/expiry;

sem repetir write.

## 12. UX surfaces

```text
Copilot Chat
Tasks
Cases
Evidence Board
Case Timeline
Interaction Room
Decision/Action panel
Artifacts
Inbox
```

## 13. Implementation mapping

Não executar `TC*` como roadmap separado.

```text
C0 → Task/Case lifecycle contracts + inventory de Room/Case owners
C5.S1–S3 → Durable Workflow foundation
C5.S4 → Task
C5.S5 → Case + Evidence Board
C5.S6 → Room integration
C5.S7 → Inbox
C5.S8 → restart/resume gate
```

## 14. Gate

Case só é produto real quando possui:

- structured lifecycle;
- shared Entity/Evidence refs;
- real workflow/task integration;
- permissions corretas;
- timeline/outcomes;
- persistence/reload quando necessário.

Uma conversa renomeada como “Case” não atende.