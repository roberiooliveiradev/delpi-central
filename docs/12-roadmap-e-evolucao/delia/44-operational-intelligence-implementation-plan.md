# DÉLIA — Detalhamento da Inteligência Operacional

**Status:** `PLANNED / TARGET` — detalhamento temático  
**Autoridade de ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Regra:** identificadores `O*` são referência de assunto, não sequência independente nem prova de implementação.

## 1. Objetivo

Detalhar Evidence, Business Graph, Durable Work, Tasks, Cases, Rooms, Inbox, Watch, Decision Gates, Organizational Knowledge, Expertise Studio, Simulation e Model Router sem competir com C0–C7 e sem criar authority/executor paralelo.

## 2. Mapeamento canônico

| O* | Conceito | Foundation/decision | Runtime target |
|---|---|---|---|
| O0 | inventário operacional | C0.S0 | — |
| O1 | Evidence/Provenance | C0 owner/contracts | C3/C4 conforme `16` |
| O2 | DELPI Business Graph | C0 owner/contracts | C4 pilot quando unlocked |
| O3 | DÉLIA Task | C0 lifecycle/owner | C6 |
| O4 | Durable Workflow | C0 Workflow/Step/wait semantics | C5 |
| O5 | DÉLIA Case/Evidence Board | C0 owner/refs | C6 |
| O6 | Interaction Room | C0 inventory/owner | C6 |
| O7 | DÉLIA Inbox | C0 refs/state semantics | C6 |
| O8 | Watch | C0 Event/Watch semantics | C6 OBSERVE/ADVISE/PREPARE; selected autonomous ACT C7 |
| O9 | Decision Gates | C0 Decision semantics | C5 before governed material ACT |
| O10 | Organizational Knowledge/Learning | C0 provenance/lifecycle | C3/C6 |
| O11 | Expertise Studio | C0/C3 owner/contracts | C6 when justified |
| O12 | What-if/Simulation | model/source owner + assumptions | incremental per `16`; advanced Twin/optimization C7 |
| O13 | Model Router | approved model/provider baseline | simple abstraction earlier; intelligent routing C7 if justified |

Esse mapeamento não redefine fases do Plano Mestre.

## 3. Princípio de construção

```text
cross-cutting responsibility
→ owner
→ canonical source
→ consumers
→ contract
→ implementation
```

Só depois entram persistence, ports, registries, engines, queues ou stores, sujeitos ao Abstraction Gate.

## 4. Evidence

Reutilizar contratos canônicos somente quando C0 os congelar. Case, Workflow, Graph, Simulation e provider adapters não criam Evidence model paralelo.

## 5. Business Graph

Graph é relação/projeção, não master data nem Semantic Layer. Runtime/index/materialization só entram se consumers reais e performance/lifecycle justificarem.

## 6. Durable Work Foundation

C5 implementa Work/orchestration da DÉLIA, não um technical executor paralelo:

```text
Policy/Decision
→ governed ACT orchestration
→ Domain API direct path OR Automation Hub/approved executor contract
→ technical result
→ authoritative Outcome verification
→ checkpoint/waits/retry/reconciliation
```

DÉLIA Work nunca contém RPA clicks/selectors ou worker credentials.

Task/Case/Room/Inbox são product/work projections consumidoras, não motores separados.

## 7. Product Work em C6

```text
Task
→ Case/Evidence Board
→ Room integration
→ Inbox
```

Todos compartilham Work/Evidence/Decision semantics canônicas, sem duplicar technical-execution lifecycle do Automation Hub.

## 8. Proatividade / Watch

C6 default:

```text
OBSERVE
ADVISE
PREPARE
```

`PREPARE` não produz side effect material.

C5 governed ACT de capabilities explícitas pode existir independentemente do Watch. C7 adiciona **selected autonomous Watch ACT / advanced autonomy**, sempre capability-scoped, com L5 OFF por default.

Event processing requer authenticity/trust, dedupe, cooldown, expiry, actor resolution e live revalidation.

## 9. Decision Gates

Decision contract nasce em C0; runtime/gates entram antes do primeiro governed material ACT. Approval não substitui Core/domain authorization e é invalidável por mudança material de args/evidence/policy/state.

## 10. Organizational Knowledge

```text
Evidence
→ candidate
→ owner/review
→ eval
→ version
→ publish
```

Case/meeting/frontline/process outcome nunca auto-publica corporate truth.

## 11. Expertise Studio

C6 somente se runtime/owner/consumer real já justificar. Não cria agent CRUD, catalog paralelo ou storage próprio antecipado.

## 12. Simulation

Simulation/Scenario podem surgir antes de C7 quando `16` permitir análise/PREPARE e houver modelo owner/reproduzível. C7 fica para Twin/optimization/autonomy avançados e scale.

```text
SIMULATE != APPLY
```

Apply inicia nova live Decision/ACT path.

## 13. Model Router

C3 pode ter provider-neutral abstraction mínima quando necessária. Model lifecycle/approval/revoke é authority separada. C7 só adiciona intelligent routing se métricas/evals reais justificarem.

## 14. Independence

Proibido runtime dependency em:

```text
minha-delpi-ai-api planner/executor/RAG/session
plugins/minha-delpi-chat state/surfaces
Chat agent/skill registries
Chat workflow/persistence
Chat provider routing
```

C0 pode inspecionar esses componentes somente como reference/inventory.

## 15. Anti-duplicação

Não criar:

- Evidence/Entity/Event/Decision refs incompatíveis;
- Task workflow engine;
- confirmation system paralelo;
- graph entity ID próprio;
- room storage duplicado sem gap;
- auto-learning production path;
- model routing espalhado em features;
- DÉLIA technical executor paralelo ao Automation Hub;
- runtime fallback para Chat.

## 16. Cenário âncora

```text
reclamação
→ Case
→ Graph/source relations
→ desenho multimodal
→ Evidence Board
→ Engineering + Quality expertise
→ 8D candidate
→ Task/Durable Work
→ wait_event
→ Watch/Inbox
→ Policy/Decision
→ Domain API or Automation Hub technical execution
→ authoritative Outcome
→ Experience candidate
```

A execução é liberada gradualmente conforme `16` e gates/evidence. Documentação não avança fase nem prova runtime.
