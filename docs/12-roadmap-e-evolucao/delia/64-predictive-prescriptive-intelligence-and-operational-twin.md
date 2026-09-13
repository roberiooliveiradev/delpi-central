# Minha DELPI Copilot — Predictive/Prescriptive Intelligence e Operational Twin

**Status:** thematic analytics/operations architecture spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Decision/Simulation:** [`39-decision-gates-and-what-if-simulation.md`](./39-decision-gates-and-what-if-simulation.md)  
**Autonomous Operations:** [`57-event-driven-autonomous-operations-and-automation-execution-hub.md`](./57-event-driven-autonomous-operations-and-automation-execution-hub.md)

## 1. Decisão

A inteligência operacional deve evoluir por quatro níveis distintos:

```text
DESCRIPTIVE  → o que aconteceu?
DIAGNOSTIC   → por que aconteceu?
PREDICTIVE   → o que provavelmente acontecerá?
PRESCRIPTIVE → quais alternativas são melhores sob objetivos/restrições?
```

Predição não é fato e prescrição não é autorização para agir.

## 2. Predictive capabilities target

Possíveis famílias, conforme dados/evidence/model ownership:

```text
demand forecast
stockout risk
supplier-delay risk
customer/churn/payment risk where appropriate
machine-failure risk
quality/scrap anomaly risk
production-delay risk
maintenance need
capacity/load forecast
service/SLA breach risk
```

Cada caso exige target metric, horizon, ground truth e eval próprios.

## 3. Prediction contract

```text
predictionId
modelRef/version
subject EntityRefs[]
target
horizon
prediction/value/probability
confidence/calibration metadata
input SourceRefs/features lineage
createdAt
validUntil/freshness
limitations
```

Nunca apresentar prediction como certeza.

## 4. Prescriptive contract

Prescrição compara alternativas sob objetivos e constraints estruturados:

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
Evidence
```

LLM pode explicar trade-offs; optimizer/simulation determinístico é preferido quando apropriado.

## 5. Operational Twin

Operational Twin é projeção dinâmica e orientada a cenário do estado operacional. Não é novo system of record.

```text
authoritative domain/OT state
→ bounded state projection
→ relationships / semantic variables
→ scenario branch
→ simulation
→ compare
→ no production write until Apply/Decision path
```

## 6. Twin scope

Pode representar progressivamente:

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

Todos os state values mantêm source owner/freshness.

## 7. Scenario isolation

Invariant:

```text
SIMULATED_STATE != PRODUCTION_STATE
```

What-if nunca escreve em ERP/MES/OT apenas porque usuário alterou variável de cenário.

Apply exige novo intent, revalidation, policy/Decision Gate e authoritative business action.

## 8. Example

```text
PRESS-04 unavailable for 4h
→ twin scenario
→ OPs impacted
→ capacity loss
→ inventory coverage
→ delivery risk
→ alternative line/overtime/subcontract options
→ compare cost/time/risk
→ recommendation
→ optional PREPARE action plan
```

## 9. Model risk

Prediction/prescription requires:

- training/evaluation lineage;
- drift monitoring;
- calibration where relevant;
- fallback when model unavailable;
- bounded applicability;
- explicit stale/out-of-distribution handling;
- no protected/sensitive-person feature use without separate governance.

## 10. Human/business authority

High-impact financial, people, quality and operational decisions continue under domain/policy owners. Model output is Evidence/Recommendation unless policy explicitly allows autonomy.

## 11. C0 inventory

Inventariar:

- existing forecasting/anomaly/optimization models;
- simulation/digital-twin tools;
- MES/IoT/historian sources;
- capacity/planning models;
- model owners/datasets/evals;
- scenario engines/solvers;
- source update frequency;
- current what-if spreadsheets/manual models;
- industrial network/safety constraints.

## 12. Phase mapping

```text
C0 → model/twin/data/owner/ground-truth inventory and semantics
C3 → prediction/prescription/twin contracts + model adapter foundations
C4 → read-only predictive/diagnostic pilots with Evidence
C5 → prescriptive PREPARE/Decision integration, no implicit apply
C6 → scenario/twin workspace and business-facing predictive products
C7 → advanced optimization, selected closed-loop actions under autonomy gates
```

## 13. Acceptance

- prediction carries model/version/horizon/freshness;
- stale/OOD case degrades truthfully;
- scenario never mutates production state;
- Apply is separate from Simulate;
- prediction calibration/eval is reproducible;
- prescriptive recommendation shows constraints/trade-offs;
- new model can be swapped behind adapter without planner rewrite;
- OT safety boundary remains intact.

## 14. North Star

> **O Copilot deve antecipar riscos, comparar futuros possíveis e recomendar a melhor resposta — sem confundir previsão com fato nem simulação com execução.**
