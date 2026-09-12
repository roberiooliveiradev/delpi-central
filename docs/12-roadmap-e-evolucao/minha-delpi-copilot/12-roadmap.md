# 12 — Roadmap macro do Minha DELPI Copilot

> **Status:** planejamento  
> **Autoridade de execução atômica:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
> **Próxima etapa:** `C0.S0`

Este arquivo descreve a evolução do produto em nível macro. O Cursor deve usar o Plano Mestre para executar subetapas, dependências, gates e evidências.

## Visão geral

```text
C0 — Fundação, inventário e contratos
C1 — Platform Actions + CopilotBridge
C2 — Workspace Context
C3 — Business Action Parity
C4 — Agentic Workflows
C5 — Ecossistema AI-ready
C6 — Autonomia governada
C7 — Rollout final
```

## C0 — Fundação

Objetivos:

- inventariar Portal/Core/AI/MFEs/APIs reais;
- congelar ownership producer/consumer;
- reutilizar contratos existentes antes de criar novos;
- formalizar PlatformCommand, WorkspaceContext e Capability Projection quando necessário;
- criar harness contratual e negatives antes do runtime.

Saída:

```text
INVENTORY = PROVEN
OWNERSHIP = PROVEN
CONTRACTS = VERSIONED
BASE_GATES = PASS
```

## C1 — Platform Actions

Objetivo: permitir ao Copilot navegar pela plataforma sem URL arbitrária e sem lista hardcoded de apps.

Entrega:

- projection derivada de `/me/apps`;
- CopilotBridge no Shell;
- `portal.open_app`;
- `portal.open_route`;
- transport send/stream;
- activity/result/audit;
- unauthorized/TOCTOU negatives.

Valor percebido:

> “Abra o Portal Comercial.”

> “Vá para pedidos em aberto.”

## C2 — Workspace Context

Objetivo: tornar a conversa relativa ao app/tela/entidade atual.

Entrega:

- WorkspaceContext contract;
- Portal Context Store;
- helper/SDK MFE;
- piloto real;
- context chips;
- contextual explanation;
- stale context/F5/logout security semantics.

Valor percebido:

> “Explique este cliente.”

> “E no mês passado?”

## C3 — Business Action Parity

Objetivo: UI e Copilot utilizarem os mesmos contratos/use cases.

```text
UI ──────────┐
             ▼
         API/use case
             ▲
Copilot ─────┘
```

Ondas:

1. reads;
2. prepare write;
3. confirmed writes;
4. sensitive/destructive apenas com policy forte.

### Dependência

Business Actions production-ready dependem do pipeline OpenAPI-first/Action Catalog/evals relevante estar aprovado no candidate vigente da Minha DELPI AI. A Onda J aberta não deve ser ignorada nem reimplementada aqui.

## C4 — Agentic Workflows

Objetivo: executar objetivos compostos multi-app.

Entrega:

- goals/DAG;
- dependencies;
- parallel safe reads;
- confirmation boundaries;
- retry/idempotency;
- partial failure;
- checkpoints/activity;
- persist/reload/resume;
- mixed read+write.

Caso-âncora:

> “Analise o atraso deste item, consulte estoque, produção e compras, prepare uma solicitação para Compras e abra o registro resultante.”

## C5 — Ecossistema AI-ready

Objetivo: novos apps entrarem por contrato sem patch no core do Copilot.

Entrega:

- readiness levels L1–L5;
- scanner;
- templates/helpers;
- entity/deep-link conventions;
- workspace context padrão;
- waves de onboarding;
- coverage dashboard.

Matriz: [`18-app-onboarding-matrix.md`](./18-app-onboarding-matrix.md).

## C6 — Autonomia governada

Objetivo: aumentar automação sem elevar poder do usuário.

```text
L0 explain
L1 navigate
L2 read/analyze
L3 prepare write
L4 confirmed write
L5 explicitly policy-allowed autonomy
```

L5 começa OFF e requer allowlist, limits, idempotency, audit e kill switch.

## C7 — Rollout final

```text
internal canary
→ app canary
→ reads scale
→ L3/L4 canary
→ selected workflows
→ metrics/incident review
→ progressive expansion
```

Sem big-bang.

## Dependências e gates

Toda fase segue:

```text
PLAN
→ INVENTORY/CONTRACTS
→ IMPLEMENT
→ WIRING
→ TESTS
→ SECURITY
→ GENERALIZATION
→ RESIDUAL SEARCH
→ COMPLETE_GATE
→ CANARY/ROLLOUT quando aplicável
```

Detalhes:

- execução: [`16-execution-master-plan.md`](./16-execution-master-plan.md);
- rollout/migrations: [`19-rollout-and-migrations.md`](./19-rollout-and-migrations.md);
- testes: [`20-testing-and-acceptance-matrix.md`](./20-testing-and-acceptance-matrix.md);
- estado/persistência: [`21-data-and-state-model.md`](./21-data-and-state-model.md);
- Cursor: [`22-cursor-execution-protocol.md`](./22-cursor-execution-protocol.md);
- requisitos: [`25-requirements-traceability.md`](./25-requirements-traceability.md).

## MVPs

### MVP de percepção

```text
C1 + fatia C2
```

Navega e entende contexto, sem risco de write.

### MVP operacional

```text
C3 reads + L3 prepare + primeiro L4 confirmed write
```

### Copilot multi-app

```text
C4 + primeiros apps L5 workflow-ready
```

### Plataforma AI-ready

```text
C5 + C6 + C7
```

## Primeira implementação

Não começar pela UI final. Começar por:

```text
C0.S0 rebaseline/inventory
→ C0.S1 ownership/contracts
→ C0.S2 harness
→ C1.S1 Authorized Portal Capability Projection
```

O estado executável é registrado em [`evidence/execution-ledger.md`](./evidence/execution-ledger.md).