# Minha DELPI Copilot — Tasks, Cases e Salas de Interação

**Status:** arquitetura de produto proposta  
**Objetivo:** permitir trabalho persistente que ultrapassa um único turno de chat.

## 1. Unidades de trabalho

```text
Turn
→ interação curta e imediata

Task
→ objetivo delimitado com múltiplos passos, normalmente minutos/horas

Case
→ investigação/processo persistente, normalmente horas/dias/semanas

Interaction Room
→ espaço colaborativo ligado a Task/Case com pessoas, Copilot, mensagens, arquivos, decisões e ações
```

O Chat continua sendo a porta de entrada, mas uma solicitação pode ser promovida a Task ou Case quando sua duração/complexidade justificar.

## 2. Copilot Task

Exemplo:

```text
TASK
Comparar fornecedores do item 90264238

status: running
owner: user

✓ compras últimos 12 meses
✓ atrasos
✓ qualidade
○ ranking
○ recomendação
```

Campos conceituais:

```text
taskId
goal
status
createdBy
owners
workspace/entity refs
workflowId
steps
result refs
artifacts
pending decisions
createdAt/updatedAt
```

## 3. Copilot Case

Case representa um problema/processo de negócio.

Exemplo:

```text
CASE #AI-2026-00418
Trinca no Produto X

status: investigating
severity: high

objective
entities
people
hypotheses
evidence
decisions
action plan
artifacts
room
workflow history
```

Casos candidatos:

- reclamação de cliente;
- não conformidade complexa;
- investigação de atraso;
- problema de fornecedor;
- análise de engenharia;
- projeto de melhoria;
- análise financeira relevante;
- incidente operacional.

## 4. Interaction Room

A sala é vinculada a uma Task/Case, não uma conversa solta.

```text
Room
├─ participantes
├─ Copilot
├─ mensagens
├─ arquivos
├─ entity refs
├─ evidências
├─ decisões
├─ ações
└─ timeline
```

O Copilot pode:

- resumir o que mudou;
- identificar pendências;
- responder com contexto do caso;
- relacionar anexos e entidades;
- sugerir próximo passo;
- acompanhar decisões;
- criar/atualizar Business Actions mediante policy;
- registrar artefatos/resultados.

## 5. Relação com conversa

Uma conversa pode:

```text
continuar simples
OU
criar Task
OU
criar Case
OU
abrir uma Task/Case existente
```

O usuário não precisa selecionar isso antes de começar.

O Copilot pode sugerir:

> “Essa investigação envolve várias etapas e acompanhamento. Quer transformar em um caso?”

Políticas podem criar automaticamente Task técnica interna quando necessário, sem mudar a UX.

## 6. Estado

Task/Case deve persistir estado operacional, não chain-of-thought:

- objetivo;
- fatos/evidências;
- referências;
- plano operacional;
- status dos passos;
- decisões humanas;
- resultados;
- artefatos;
- limitações/pendências;
- audit.

## 7. Case + Expertise + Playbook

Exemplo Qualidade:

```text
Case: RNC cliente
→ expertise quality.root-cause-analysis
→ playbook quality.8d
→ evidence
→ tasks
→ decision gates
→ action plan
```

O Case não é um agente; é um container de trabalho persistente.

## 8. Case + Business Graph

Task/Case deve guardar `EntityRef` e relações relevantes, não cópias arbitrárias de todos os dados.

Isso permite abrir o caso e atualizar dados atuais a partir das APIs owners.

## 9. Permissões

Acesso ao Case/Room não concede automaticamente acesso às entidades originais.

Toda leitura/ação continua sujeita a RBAC/policy.

Dados materializados no Case devem respeitar classificação/sanitização e política de retenção.

## 10. UX alvo

Superfícies futuras:

```text
Copilot Chat
Copilot Tasks
Copilot Cases
Interaction Rooms
Case Timeline
Evidence panel
Action plan
Approvals
Artifacts
```

## 11. Lifecycle

```text
DRAFT
ACTIVE
WAITING_USER
WAITING_EVENT
BLOCKED
RESOLVED
CLOSED
CANCELLED
```

Reabertura deve ser auditada.

## 12. Implantação

### TC0
- contratos `TaskV1`, `CaseV1`, status e refs;
- inventário de salas já existentes nos portais.

### TC1
- Task persistente ligada a WorkflowPlan.

### TC2
- Case básico + timeline/evidence.

### TC3
- Interaction Room integrada.

### TC4
- Inbox/Watch/approvals ligados a Tasks/Cases.

## 13. Gate

Não considerar Case pronto se for apenas uma conversa renomeada. Deve existir estado operacional estruturado, evidence, lifecycle e integração real com capabilities/workflows.