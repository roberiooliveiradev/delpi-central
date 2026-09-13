# Minha DELPI Copilot — Detalhamento da Inteligência Operacional

**Status:** detalhamento temático  
**Autoridade de ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Regra:** identificadores `O*` são referência de assunto, não sequência independente.

## 1. Objetivo

Detalhar Evidence, Business Graph, Durable Work, Tasks, Cases, Rooms, Inbox, Watch, Decision Gates, Organizational Knowledge, Expertise Studio, Simulation e Model Router sem competir com a ordem C0–C7 e sem reutilizar o runtime do Minha DELPI Chat.

## 2. Mapeamento canônico

| O* | Conceito | Contrato/foundation | Runtime canônico |
|---|---|---|---|
| O0 | inventário operacional | C0.S0 | — |
| O1 | Evidence/Provenance | C0 shared refs | C3.S9–S10 + C4.S3 |
| O2 | DELPI Business Graph | C0 Entity/Relationship contracts | C4.S4–S5 |
| O3 | Copilot Task | C0 TaskRef/lifecycle | C6.S1 |
| O4 | Durable Workflow | C0 Workflow/Step/wait semantics | C5.S4–S6 |
| O5 | Copilot Case/Evidence Board | C0 CaseRef + EvidenceRef | C6.S2 |
| O6 | Interaction Room | C0 inventory/owner | C6.S3 |
| O7 | Copilot Inbox | C0 refs/state semantics | C6.S4 |
| O8 | Watch | C0 EventEnvelope | C6.S5; ACT C7.S2 |
| O9 | Decision Gates | C0 Decision contracts | C5.S1–S3 |
| O10 | Organizational Knowledge/Learning | C0 provenance/lifecycle | C3.S8 + C6.S6–S7 |
| O11 | Expertise Studio | Expertise/Playbook contracts C0 | C6.S8 |
| O12 | What-if/Simulation | owner/model assumptions | C7.S3 |
| O13 | Model Router | provider baseline/policy | C3.S1 baseline; C7.S4 router |

Esse mapeamento substitui qualquer ordem antiga `O0→O13` como regra de execução.

## 3. Princípio de construção

```text
contract first
→ owner/port
→ persistence boundary
→ tests
→ runtime
→ UX
→ rollout
```

Nenhum conceito operacional cria primitive próprio quando C0 já oferece um compartilhado.

## 4. Evidence

Reutiliza `SourceRef`, `EvidenceRef`, `OutcomeRef` e epistemic classes C0.

```text
C3.S9–S10
→ multimodal evidence + epistemic synthesis

C4.S3
→ Evidence normalizada de resultados das Domain APIs

C6.S2
→ Evidence Board reutiliza as mesmas refs
```

Case, Workflow, Graph e Simulation nunca criam Evidence model paralelo.

## 5. Business Graph

Reutiliza `EntityRef`/`RelationshipRef`.

Runtime C4:

- relationship registry/index se necessário;
- permission-aware traversal;
- source fetch nas APIs owners;
- provenance;
- depth/cycle budget;
- authoritative vs inferred;
- cross-domain analysis.

Não replica tabelas operacionais.

## 6. Durable Work Foundation

C5 implementa somente a fundação executora/durável:

```text
Decision Gate Engine
→ governed write executor
→ outcome verification
→ WorkflowPlan/DAG runtime
→ checkpoints/waits
→ crash/retry/idempotency gate
```

Task/Case/Room/Inbox não são motores C5; entram como produtos/consumidores em C6.

## 7. Product Work em C6

```text
C6.S1 Task
→ C6.S2 Case + Evidence Board
→ C6.S3 Interaction Room integration
→ C6.S4 Inbox
```

Todos usam o mesmo Durable Workflow Runtime C5 e os mesmos refs compartilhados.

## 8. Proatividade

C6.S5 começa somente com:

```text
OBSERVE
ADVISE
```

Watch `ACT` exige C7.S2 + autonomy/policy/Decision Gate adequados.

Event processing precisa dedupe/cooldown/expiry/revalidation.

## 9. Decision Gates

Contrato nasce em C0; engine entra em C5 antes do primeiro write production-ready.

Níveis:

```text
NO_GATE
ACKNOWLEDGE
CONFIRM
REVIEW_AND_CONFIRM
APPROVAL_WORKFLOW
BLOCK
```

Approval antiga não autoriza payload/evidence materialmente alterado.

## 10. Organizational Knowledge

```text
C3.S8 → Reference Knowledge/RAG da Copilot API
C6.S6 → Decision/Experience/Solution Patterns
C6.S7 → Governed Learning
```

Case resolution gera candidate, nunca auto-publish.

## 11. Expertise Studio

C6.S8, após Expertise runtime C3 estar estável:

```text
draft → review → eval → published → deprecated/rollback
```

Não criar agente por pack e não migrar CRUD de agents do Chat.

## 12. Simulation

C7.S3 somente para domínio com modelo/calculadora owner, baseline e premissas reproduzíveis.

```text
SIMULATE != APPLY
```

Apply passa por Business Action/Decision Gate.

## 13. Model Router

C3.S1 fornece provider/model abstraction baseline simples.

C7.S4 só adiciona roteamento inteligente depois de métricas reais da própria Copilot API.

Compute policy pode selecionar:

```text
FAST
STANDARD
DEEP_REASONING
MULTIMODAL
LONG_CONTEXT
```

com privacy/provider/latency/cost/output constraints.

## 14. Independence

É proibido usar como runtime dependency:

```text
minha-delpi-ai-api planner/executor/RAG/session
plugins/minha-delpi-chat state/surfaces
Chat agent/skill registries
Chat workflow/persistence
Chat provider routing
```

C0 pode estudar esses componentes somente como referência técnica/anti-pattern. Reuso só é válido via componente neutro com owner compartilhado real.

## 15. Anti-duplicação

Não criar:

- `CaseEvidence` incompatível com EvidenceRef;
- `WatchEvent` incompatível com EventEnvelope;
- Task workflow engine;
- confirmation system paralelo ao Decision Gate;
- graph entity ID próprio;
- room storage duplicado sem gap provado;
- Experience auto-learning pipeline sem governance;
- model selection conditions espalhadas pelas features;
- runtime fallback para Minha DELPI Chat.

## 16. Cenário âncora

```text
reclamação
→ Case
→ Graph
→ desenho multimodal
→ Evidence Board
→ Engineering + Quality expertise
→ 8D
→ Task/Durable Workflow
→ wait_event
→ Watch/Inbox
→ Decision Gate
→ Business Action
→ Outcome/Audit
→ Experience candidate
```

A execução desse cenário é liberada gradualmente conforme C3–C7 e seus gates estejam PASS; nenhuma etapa depende de migração/cutover do Chat.