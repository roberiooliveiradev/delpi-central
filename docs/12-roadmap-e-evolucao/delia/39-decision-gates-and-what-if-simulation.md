# DÉLIA — Decision Gates e What-if Simulation

**Status:** `TARGET` — thematic spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Evidence rule:** contracts/engine/simulation runtime só existem quando fase, owner, contract e implementation forem provados.

## 1. Decision Gate

O target usa um modelo único de decisão proporcional ao risco:

```text
NO_GATE
ACKNOWLEDGE
CONFIRM
REVIEW_AND_CONFIRM
APPROVAL_WORKFLOW
BLOCK
```

Não manter confirmation booleana como authority paralela.

## 2. Inputs de policy

Podem incluir:

- action/capability risk;
- sensitivity/data class;
- financial/operational impact;
- volume/scope;
- reversibility;
- final arguments;
- Evidence refs/freshness;
- actor/approver permissions;
- autonomy level;
- business criticality;
- environment and materiality.

LLM pode ajudar a preparar preview, nunca definir authority final de gate.

## 3. Contracts compartilhados

Request/Decision contracts são target até C0 congelar owner/source/consumers. Não criar `DecisionGateV1` local ou lifecycle paralelo.

Decision precisa vincular materialmente args/evidence/policy/version/expiry quando isso for necessário para evitar TOCTOU.

## 4. Invalidation

Pode invalidar decisão anterior:

- arguments materialmente diferentes;
- Evidence crítica mudou/stale;
- permission/policy alterada;
- entity version/precondition mudou;
- expiry;
- approver perdeu autoridade.

Revalidar live AuthZ/Policy imediatamente antes do ACT.

## 5. Approval workflow

```text
Decision request
→ pending approval
→ approved | rejected | expired
→ current-state revalidation
→ ACT | BLOCK
```

Approval não substitui Core/domain authorization.

## 6. What-if / Simulation

What-if/Scenario/Simulation podem aparecer de forma incremental conforme `16` e specs de predictive/prescriptive/twin. Este documento **não restringe toda simulação a C7**.

C4/C5 podem produzir analysis/scenario/PREPARE quando contracts/models aprovados existirem. C7 é reservado para advanced autonomy/optimization/scale e aplicações avançadas do Twin, conforme Plano Mestre.

## 7. Simulation state

Candidate semantics:

```text
simulationId
baseline Source/Evidence refs
assumptions
inputs
model/rule ref + version
outputs
limitations
createdAt
```

Não criar foundation global se domínio/model owner já tiver contrato adequado. Reuse/adapter antes de schema transversal.

## 8. Fontes de cálculo

Preferência:

1. authoritative domain simulation API/use case;
2. deterministic versioned rules;
3. governed analytical/optimization model;
4. LLM para estruturar/explain, não inventar números.

## 9. Simulate != Apply

```text
simulate
→ projected result
→ review/PREPARE
→ separate ACT intent
→ live AuthZ/Policy/Decision
→ approved executor path
→ authoritative Outcome verification
```

Simulation nunca concede autorização.

## 10. Epistemic UX

Separar:

- observed baseline;
- user-provided input;
- assumption;
- model/calculation;
- projected result;
- confidence/uncertainty quando suportada;
- limitations.

Simulation output nunca é current FACT.

## 11. Security

- no hidden write;
- source RBAC;
- model/rule owner/version;
- sensitive assumptions redacted in logs;
- stale baseline handling;
- provider/data policy;
- external/tool content treated as untrusted;
- `recommendation != authorization`.

## 12. Tests

Decision:

- each gate level;
- args changed;
- Evidence changed;
- expired;
- unauthorized approver;
- live revalidation.

Simulation:

- correct baseline;
- explicit assumptions;
- reproducible model;
- unsupported scenario;
- stale baseline;
- no hidden write;
- Apply requires new live Decision path.

## 13. Mapping

```text
C0 → owner/contracts/semantics
C5 → Decision Gate + wait_approval before governed material ACT
C4/C5/C6 → scenario/simulation/PREPARE only where model/contract is ready and master-plan dependencies allow
C7 → advanced Twin/optimization/autonomous application and scale
```

## 14. Ownership

DÉLIA owns Policy/Decision orchestration within its boundary. Domain APIs/Core remain final authorities for permission/business rules; models/simulation owners remain authorities for calculation semantics.

## 15. Gate

- nenhum material ACT bypassa required Policy/Decision/AuthZ;
- Simulation só é chamada assim quando cálculo/modelo governado existe;
- qualitative scenario sem modelo permanece hypothesis/scenario, não quantitative simulation;
- missing proof remains `PENDING/INCONCLUSIVE`.
