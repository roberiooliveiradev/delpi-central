# Minha DELPI Copilot — Detalhamento da Inteligência Operacional

**Status:** detalhamento temático  
**Autoridade de ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Regra:** identificadores `O*` são referência de assunto, não sequência independente.

## 1. Objetivo

Detalhar Business Graph, Evidence, Tasks, Cases, Rooms, Inbox, Watch, Decision Gates, Organizational Knowledge, Expertise Studio, Simulation e Model Router sem competir com a ordem C0–C7.

## 2. Mapeamento canônico

| O* | Conceito | Contrato/foundation | Runtime canônico |
|---|---|---|---|
| O0 | inventário operacional | C0.S0 | — |
| O1 | Evidence/Provenance | C0.S2–S4 | C2/C3 |
| O2 | DELPI Business Graph | C0 Entity/Relationship contracts | C3.S5–S7 |
| O3 | Copilot Task | C0 Task lifecycle | C5.S4 |
| O4 | Durable Workflow | C0 workflow/wait semantics | C5.S1–S3 |
| O5 | Copilot Case/Evidence Board | C0 Case lifecycle + EvidenceRef | C5.S5 |
| O6 | Interaction Room | C0 inventory/owner | C5.S6 |
| O7 | Copilot Inbox | C0 reference/state semantics | C5.S7 |
| O8 | Watch | C0 EventEnvelope | C6.S1; ACT C7.S2 |
| O9 | Decision Gates | C0 Decision contracts | C4.S1–S3 |
| O10 | Organizational Experience | C0 provenance/lifecycle principles | C6.S5–S6 |
| O11 | Expertise Studio | Expertise contracts C0 | C6.S7 |
| O12 | What-if/Simulation | owner/model assumptions | C7.S3 |
| O13 | Model Router | model/provider inventory + policy | C7.S4 |

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

Runtime C2/C3 deve fornecer:

- provenance/freshness;
- multimodal page/region;
- conflicting evidence handling;
- FACT/CALCULATION/HYPOTHESIS/CONCLUSION/RECOMMENDATION.

Case, Workflow e Simulation referenciam o mesmo Evidence model.

## 5. Business Graph

Reutiliza `EntityRef`/`RelationshipRef`.

Runtime C3:

- relationship registry/index;
- permission-aware traversal;
- source fetch;
- provenance;
- depth/cycle budget;
- authoritative vs inferred.

Não replica tabelas operacionais.

## 6. Durable Work

C5 implementa nesta ordem interna:

```text
Durable Workflow foundation
→ waits/checkpoints
→ DAG runner
→ Task
→ Case/Evidence Board
→ Room integration
→ Inbox
→ restart/resume gate
```

Task/Case não criam executors próprios.

## 7. Proatividade

C6 começa apenas com:

```text
OBSERVE
ADVISE
```

Watch `ACT` exige C7 autonomy/Decision Gate policy.

Event processing precisa dedupe/cooldown/expiry/revalidation.

## 8. Decision Gates

Contrato nasce em C0; runtime antes de writes em C4.

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

## 9. Organizational Knowledge

C6:

```text
Reference
Decision
Experience
Solution Pattern
```

com owner/version/provenance/review/eval. Case resolution gera candidate, nunca auto-publish.

## 10. Expertise Studio

C6, após Expertise runtime estável:

```text
draft → review → eval → published → deprecated/rollback
```

Não criar agente por pack.

## 11. Simulation

C7 somente para domínio com modelo/calculadora owner, baseline e premissas reproduzíveis.

```text
SIMULATE != APPLY
```

Apply passa por Business Action/Decision Gate.

## 12. Model Router

C7 somente depois de métricas reais.

Compute policy pode selecionar:

```text
FAST
STANDARD
DEEP_REASONING
MULTIMODAL
LONG_CONTEXT
```

com privacy/provider/latency/cost/output constraints.

## 13. Anti-duplicação

Não criar:

- `CaseEvidence` incompatível com EvidenceRef;
- `WatchEvent` incompatível com EventEnvelope;
- Task workflow engine;
- confirmation system paralelo ao Decision Gate;
- graph entity ID próprio;
- room storage duplicado sem gap provado;
- Experience auto-learning pipeline sem governance;
- model selection conditions espalhadas pelas features.

## 14. Cenário âncora

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

A execução desse cenário só é liberada gradualmente conforme cada fase C correspondente esteja PASS.