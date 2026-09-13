# Minha DELPI Copilot — Process Intelligence, Process Mining e Task Mining

**Status:** thematic architecture/product spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Autonomous Operations:** [`57-event-driven-autonomous-operations-and-automation-execution-hub.md`](./57-event-driven-autonomous-operations-and-automation-execution-hub.md)  
**Evidence:** [`38-evidence-provenance-and-epistemic-ux.md`](./38-evidence-provenance-and-epistemic-ux.md)  
**State:** [`21-data-and-state-model.md`](./21-data-and-state-model.md)

## 1. Decisão de produto

O Copilot deve entender não apenas processos documentados, mas também **como os processos realmente acontecem**, a partir de event logs e evidências autorizadas.

Target:

```text
PROCESS DESIGN
+ REAL EVENT LOGS
+ TASK OBSERVATIONS GOVERNED
→ PROCESS INTELLIGENCE
→ variants / bottlenecks / deviations / opportunities
→ Evidence
→ recommendation / Watch / Playbook / Automation candidate
```

Process Intelligence não substitui o owner do processo nem altera procedimento automaticamente.

## 2. Capability family

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
Agent/Automation Execution Mining
```

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

Não criar cópia total de ERP/MES apenas para mineração. Preferir projections/materializations bounded e reproduzíveis.

## 4. Process instance versus employee surveillance

Process Mining mede fluxo/processo. Não criar, por default:

```text
secret employee productivity score
personality/trust score
behavioral disciplinary profile
continuous invasive desktop surveillance
```

Task Mining em desktop exige purpose, consent/governance, data minimization, app/domain allowlist, redaction, retention e Human Observation boundaries de `54`.

## 5. Conformance

```text
expected process model
+ observed event trace
→ conformant | deviation | unknown/incomplete evidence
```

Deviation não significa automaticamente erro humano ou fraude. Deve apontar fatos, contexto e impacto.

## 6. Automation opportunity loop

```text
process evidence
→ identify repetitive/manual/bottleneck step
→ opportunity candidate
→ owner validation
→ business case
→ semantic capability/executor design
→ Automation & Execution Hub
→ post-deployment process mining
→ measured improvement
```

Nenhuma oportunidade vira RPA automaticamente.

## 7. Integration with Watch

Process Intelligence pode gerar conditions/candidates, por exemplo:

```text
approval cycle > baseline
rework loop repeated
waiting state above threshold
variant associated with high failure rate
manual handoff recurring
```

Watch `OBSERVE/ADVISE/PREPARE/ACT` continua governado por `37` e `57`.

## 8. Process KPI semantics

Process KPIs devem usar a Semantic Business Layer quando existir, incluindo definition/version/owner/grain/time window. Não permitir que o modelo invente fórmula para lead time, SLA, throughput ou rework rate.

## 9. AI/LLM role

LLM pode:

- explicar variants;
- sintetizar causas candidatas;
- correlacionar Evidence;
- sugerir investigação/automation candidate;
- gerar descrição de processo/BPMN candidate.

LLM não é o motor determinístico de cálculo do event log e não inventa eventos ausentes.

## 10. Process model artifacts

Outputs podem incluir:

```text
process map
variant map
BPMN candidate
bottleneck report
conformance report
automation opportunity backlog
before/after comparison
```

Artefatos entram no Artifact Workspace e preservam provenance/version.

## 11. Security / privacy

- source ACL preservado;
- actor identity somente quando necessária;
- aggregated process metrics preferidas a individual ranking;
- personal/external source não entra em process mining organizacional sem autorização;
- task capture explícita e bounded;
- raw screen/input capture não é default;
- sensitive fields redacted conforme policy.

## 12. C0 inventory

Inventariar:

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

Unknown = `NOT_PROVEN`.

## 13. Phase mapping

```text
C0 → source/event/process-owner/privacy inventory + canonical event semantics
C3 → process-intelligence contracts/index foundations, no production mining conclusion yet
C4 → read-only process discovery/mining pilots with Evidence
C5 → automation opportunity may become governed PREPARE/work item; no automatic ACT
C6 → Process Intelligence product UX, conformance, variants, backlog, before/after measurement
C7 → selected closed-loop optimization recommendations/ACT only under autonomy gates
```

## 14. Acceptance

Required scenarios:

- known process reconstructed from event log;
- missing/out-of-order event remains explicit;
- multiple variants correctly separated;
- conformance does not accuse person;
- automation candidate references Evidence;
- post-automation before/after metrics reproducible;
- actor-level privacy boundaries enforced;
- new process source onboarded without planner hardcode.

## 15. North Star

> **O Copilot deve compreender o processo desenhado, observar o processo real, explicar suas variações e gargalos e transformar oportunidades em melhorias governadas e mensuráveis.**
