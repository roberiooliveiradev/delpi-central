# DÉLIA — Process Intelligence, Process Mining e Task Mining

**Status:** `TARGET` — thematic architecture/product spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Autonomous Operations:** [`57-event-driven-autonomous-operations-and-automation-execution-hub.md`](./57-event-driven-autonomous-operations-and-automation-execution-hub.md)  
**Evidence:** [`38-evidence-provenance-and-epistemic-ux.md`](./38-evidence-provenance-and-epistemic-ux.md)  
**State:** [`21-data-and-state-model.md`](./21-data-and-state-model.md)

## 1. Decisão de produto

A DÉLIA deve poder entender não apenas processos documentados, mas também **como os processos realmente acontecem**, quando existirem event logs, owners e evidências autorizadas suficientes.

Target:

```text
PROCESS DESIGN
+ REAL EVENT LOGS
+ GOVERNED TASK OBSERVATIONS
→ PROCESS INTELLIGENCE
→ variants / bottlenecks / deviations / opportunities
→ Evidence
→ recommendation / Watch / Playbook / Automation candidate
```

Process Intelligence não substitui o owner do processo, não cria business truth paralelo e não altera procedimento automaticamente.

## 2. Capability family

Capabilities candidatas:

```text
Process Discovery
Process Mining
Task Mining
Conformance Checking
Variant Analysis
Bottleneck Detection
Wait/Rework Analysis
Automation Opportunity Detection
Process KPI Mining
Process Change Impact Analysis
Automation Execution Mining
```

A lista é `TARGET`; não prova engines, stores, collectors ou produtos implementados.

## 3. Event-log model

C0 deve provar quais fontes possuem dados suficientes para mineração. Um evento útil pode exigir:

```text
caseRef / businessKey
activity
occurredAt
sourceSystem
actorRef? bounded/authorized
entityRefs[]
outcome/status
correlationId?
sourceRef/evidenceRef
```

O shape é candidate até owner/source/consumer/contract serem congelados. Não criar cópia total de ERP/MES apenas para mineração. Preferir projections/materializations bounded e reproduzíveis quando justificadas.

## 4. Process instance versus employee surveillance

Process Mining mede fluxo/processo. Não criar por default:

```text
secret employee productivity score
personality/trust score
behavioral disciplinary profile
continuous invasive desktop surveillance
```

Task Mining exige purpose, owner, explicit governance, data minimization, app/domain allowlist, redaction, retention e Human Observation boundaries de `54`.

## 5. Conformance

```text
expected process model
+ observed event trace
→ conformant | deviation | unknown/incomplete evidence
```

Deviation não significa automaticamente erro humano, fraude ou intenção. Deve apontar fatos, contexto, qualidade da evidência e impacto.

## 6. Automation opportunity loop

```text
process evidence
→ identify repetitive/manual/bottleneck step
→ opportunity candidate
→ owner validation
→ business case
→ semantic capability/execution design
→ Automation Hub when technical execution is required
→ post-deployment process mining
→ measured improvement
```

Nenhuma oportunidade vira RPA/ACT automaticamente. DÉLIA coordena Evidence/Decision/Work; Automation Hub continua owner da execução técnica.

## 7. Integration with Watch

Process Intelligence pode gerar conditions/candidates, por exemplo:

```text
approval cycle > governed baseline
rework loop repeated
waiting state above threshold
variant associated with high failure rate
manual handoff recurring
```

Watch segue `37` e `57`:

```text
C6 default = OBSERVE | ADVISE | PREPARE
C6 Watch autonomous ACT = BLOCKED
C5 governed ACT = available only through explicit authorized flow
C7 selected Watch autonomous ACT = gated
```

## 8. Process KPI semantics

Process KPIs devem usar a Semantic Business Layer **quando e se** o owner/contrato correspondente estiver comprovado, preservando definition/version/owner/grain/time window. O modelo não inventa fórmulas materiais para lead time, SLA, throughput ou rework rate.

## 9. AI/LLM role

LLM pode ajudar a explicar variants, sintetizar causas candidatas, correlacionar Evidence, sugerir investigação/automation candidate e gerar descrição/BPMN candidate.

LLM não é o motor determinístico do event log, não inventa eventos ausentes e não transforma correlação em causalidade comprovada.

## 10. Process model artifacts

Outputs candidatos:

```text
process map
variant map
BPMN candidate
bottleneck report
conformance report
automation opportunity backlog
before/after comparison
```

Artifacts preservam provenance/version e usam Artifact Workspace apenas quando essa capability estiver efetivamente implementada e autorizada.

## 11. Security / privacy

- source ACL preservado;
- actor identity somente quando necessária;
- aggregated process metrics preferidas a individual ranking;
- personal/external source não entra em process mining organizacional sem autorização;
- task capture explícita e bounded;
- raw screen/input capture não é default;
- sensitive fields redacted conforme policy;
- process deviation não vira decisão trabalhista automática.

## 12. C0 inventory

Inventariar factual:

- event logs/audit trails por domínio;
- case/business keys;
- timestamps/activities/statuses;
- existing process/BPMN documentation;
- process owners;
- scheduler/event bus/CDC availability;
- task-mining products/agents existentes;
- desktop telemetry policies;
- retention/privacy constraints;
- historical data quality/completeness;
- current BI/process KPI definitions.

Sem evidência suficiente = `TO_INVENTORY`, nunca `PROVEN` por documentação.

## 13. Phase mapping

```text
C0 → source/event/process-owner/privacy inventory + contract freeze
C3 → target contracts/foundations only when justified by C0
C4 → read-only process discovery/mining pilots with Evidence
C5 → automation opportunity may become PREPARE or governed ACT through explicit authorized capability; no automatic ACT
C6 → Process Intelligence UX, conformance, variants, backlog, before/after measurement
C7 → selected closed-loop autonomous optimization only under explicit L5/Watch gates
```

## 14. Acceptance

Quando em escopo, provar no SHA/config avaliado:

- known process reconstructed from authoritative event evidence;
- missing/out-of-order event remains explicit;
- multiple variants correctly separated;
- conformance does not accuse person;
- automation candidate references Evidence;
- post-change before/after metrics reproducible;
- actor-level privacy boundaries enforced;
- new process source onboarded without planner hardcode.

Sem prova obrigatória: `PENDING`/`INCONCLUSIVE`, nunca PASS.

## 15. North Star

> **DÉLIA deve compreender o processo desenhado, observar o processo real com evidência suficiente, explicar variações e gargalos e transformar oportunidades em melhorias governadas e mensuráveis sem se tornar process owner, surveillance engine ou executor técnico.**
