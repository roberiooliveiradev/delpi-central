# DÉLIA — Predictive/Prescriptive Intelligence e Operational Twin

**Status:** `TARGET` — thematic analytics/operations architecture spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Decision/Simulation:** [`39-decision-gates-and-what-if-simulation.md`](./39-decision-gates-and-what-if-simulation.md)  
**Autonomous Operations:** [`57-event-driven-autonomous-operations-and-automation-execution-hub.md`](./57-event-driven-autonomous-operations-and-automation-execution-hub.md)

## 1. Decisão

A inteligência operacional pode evoluir por níveis distintos:

```text
DESCRIPTIVE  → o que aconteceu?
DIAGNOSTIC   → por que aconteceu?
PREDICTIVE   → o que provavelmente acontecerá?
PRESCRIPTIVE → quais alternativas são melhores sob objetivos/restrições?
```

Invariantes:

```text
Prediction != FACT
Recommendation != authorization
Twin != source of truth
SIMULATE != APPLY
```

## 2. Predictive capabilities target

Famílias candidatas, somente quando dados, owner, ground truth e eval forem comprovados:

```text
demand forecast
stockout risk
supplier-delay risk
customer/payment risk where appropriate
machine-failure risk
quality/scrap anomaly risk
production-delay risk
maintenance need
capacity/load forecast
service/SLA breach risk
```

A lista não prova modelos existentes nem adequação de uso.

## 3. Prediction contract

Candidate semantics:

```text
predictionRef
modelRef/version
subject EntityRefs[]
target
horizon
prediction/value/probability
calibration/confidence metadata when valid
input SourceRefs/features lineage
createdAt
validUntil/freshness
limitations/applicability
```

Shape, storage e lifecycle só são congelados após C0/Abstraction Gate.

Prediction nunca é apresentada como certeza ou fato observado.

## 4. Prescriptive contract

Prescrição compara alternativas sob objetivos/constraints estruturados.

Candidate semantics:

```text
objective(s)
constraints
candidate actions/scenarios
assumptions
predicted outcomes
trade-offs
risk
recommended option? optional
model/solver refs
Evidence refs
```

LLM pode explicar trade-offs; deterministic optimizer/simulation é preferido quando apropriado e validado.

Prescrição não concede autorização nem executa implicitamente.

## 5. Operational Twin

Operational Twin é uma **projeção/scenario model derivada** sobre fontes autoritativas. Nunca é system of record.

```text
authoritative domain/OT state
→ bounded projection
→ semantic/state variables
→ scenario branch
→ simulation
→ comparison
→ optional recommendation/PREPARE
```

Nenhuma mutação de production state ocorre dentro da simulação.

## 6. Twin scope

Pode representar progressivamente, quando houver owner/source/freshness claros:

```text
plant / line / cell
machine / work center
OP / operation
product/revision
material/stock
maintenance state
quality state
capacity
energy when approved
supplier/logistics dependencies
```

Todos os valores mantêm source owner, freshness e limitações.

## 7. Scenario isolation

```text
SIMULATED_STATE != PRODUCTION_STATE
```

What-if nunca escreve em ERP/MES/OT apenas porque usuário ou modelo alterou variável de cenário.

Apply exige novo intent/action context, live source refresh, AuthZ, Policy/Decision, idempotency/audit e Outcome verification quando material.

## 8. Example

```text
PRESS-04 unavailable for 4h
→ twin scenario
→ affected OPs
→ capacity loss estimate
→ inventory coverage estimate
→ delivery risk
→ alternative line/overtime/subcontract options
→ compare cost/time/risk
→ recommendation
→ PREPARE action plan
→ separate governed Apply flow if explicitly authorized
```

## 9. Model risk

Prediction/prescription requires, conforme risco:

- training/evaluation lineage;
- model owner/version;
- ground truth definition;
- drift monitoring;
- calibration where relevant;
- fallback/degraded behavior;
- bounded applicability;
- stale/out-of-distribution handling;
- no protected/sensitive-person features without separate approved governance.

## 10. Human/business authority

High-impact financial, people, quality and operational decisions permanecem nos business/policy owners oficiais.

Model output = Evidence/Prediction/Recommendation, nunca permission.

Autonomous ACT futuro só pode ocorrer sob explicit capability-scoped L5 policy, com C7 gates e L5 OFF por default.

## 11. C0 inventory

Inventariar factual:

- existing forecasting/anomaly/optimization models;
- simulation/digital-twin tools;
- MES/IoT/historian sources;
- capacity/planning models;
- model owners/datasets/evals;
- scenario engines/solvers;
- source update frequency;
- current what-if spreadsheets/manual models;
- industrial network/safety constraints.

Sem evidence suficiente = `TO_INVENTORY`.

## 12. Phase mapping

```text
C0 → model/twin/data/owner/ground-truth inventory + contract decisions
C3 → prediction/prescription/twin foundations only when justified
C4 → read-only predictive/diagnostic pilots with Evidence
C5 → prescriptive recommendation/PREPARE and governed ACT only through separate authorized capability; no implicit Apply
C6 → scenario/twin workspace and business-facing predictive products
C7 → advanced optimization and selected autonomous closed-loop ACT under explicit L5 gates
```

## 13. Acceptance

Quando implementado, provar:

- prediction carries model/version/horizon/freshness/applicability;
- stale/OOD case degrades truthfully;
- scenario never mutates production state;
- Apply is separate from Simulate;
- model eval/calibration evidence is traceable to SHA/config/model/version;
- prescriptive recommendation exposes constraints/trade-offs;
- model can be replaced without planner hardcode where abstraction is justified;
- Twin projection never becomes source of truth;
- OT safety boundary remains intact.

Sem prova obrigatória: `PENDING`/`INCONCLUSIVE`.

## 14. North Star

> **DÉLIA deve antecipar riscos, comparar cenários e recomendar alternativas sem confundir previsão com fato, simulação com produção ou recomendação com autorização.**
