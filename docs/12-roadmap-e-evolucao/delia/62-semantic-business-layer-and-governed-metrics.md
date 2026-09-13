# DÉLIA — Semantic Business Layer e Métricas Governadas

**Status:** `TARGET` — thematic data/product/architecture spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Business Graph:** [`35-delpi-business-graph.md`](./35-delpi-business-graph.md)  
**Evidence:** [`38-evidence-provenance-and-epistemic-ux.md`](./38-evidence-provenance-and-epistemic-ux.md)

## 1. Decisão

Business Graph e Semantic Business Layer são complementares:

```text
Business Graph
= relações entre entidades

Semantic Business Layer
= significado governado de métricas, dimensões, regras de agregação e conceitos analíticos
```

Graph != Semantic Layer. A DÉLIA não deve inventar fórmulas para métricas empresariais materiais.

## 2. MetricDefinition

Candidate semantics a decidir em C0/C3 somente se houver owner, consumers e contract reais:

```text
metricId
name
businessMeaning
formulaRef/expression
source owner
grain
dimensions[]
filters/default exclusions
unit
freshness/SLA
owner
version
status
permission/sensitivity classification
validation tests
```

A documentação não prova registry, schema ou store implementado.

## 3. Governed dimensions

Dimensões podem ter semântica governada, mas IDs/master data continuam nos systems owners. A Semantic Layer referencia; não replica nem se torna master-data authority.

Examples candidate:

```text
company/filial
customer
supplier
product
product family
cost center
machine
work center
OP
operation
calendar/fiscal period
salesperson/buyer/team
```

## 4. Semantic query flow

Target:

```text
user question
→ identify governed metric/concept
→ permission-aware semantic plan
→ owner query/read capability
→ deterministic calculation/aggregation
→ Evidence + metric definition/version refs
→ explanation
```

LLM interpreta intenção; cálculo material usa definição estruturada/reprodutível quando disponível.

## 5. Metric authority

Cada métrica material precisa de owner de negócio e source canônica. Alteração de fórmula exige lifecycle/versioning do owner; prompt, memory ou learning candidate não pode alterar fórmula oficial automaticamente.

Semantic metadata não substitui Domain API/BI owner nem concede source access.

## 6. Conflict handling

Se duas áreas usam definições diferentes:

```text
same label + different meaning
→ separate definitions/versions/scopes
→ explicit owners
→ UX surfaces conflict
```

Não escolher arbitrariamente nem fundir silenciosamente.

## 7. Zero-copy / federation principle

Quando tecnicamente adequado:

```text
semantic definition
→ query authoritative source
```

em vez de copiar todos os dados para uma camada central. Materializations/cache, se existirem, são derivados, bounded, versioned, permission-aware e freshness-aware.

## 8. Business glossary

A camada pode projetar conceitos governados além de métricas, desde que haja owner/source real. Exemplos ilustrativos:

```text
Pedido atrasado
Cliente ativo
Estoque disponível
Lead time
Inadimplência
OEE
Scrap
Backlog
Entrega no prazo
```

A lista não prova que definições oficiais existam hoje.

## 9. Integration with Graph/Process Intelligence/Twin

```text
Semantic Layer → meaning/metric semantics
Business Graph → entity relationships
Process Intelligence → observed process traces/variants
Operational Twin → simulated scenario state
```

Prediction/simulation outputs não viram fact/source of truth. Os quatro não colapsam em um único generic model.

## 10. Security

- semantic metadata does not grant data access;
- every query revalidates source/domain permissions;
- sensitive metric may require aggregation/redaction;
- row/resource-level domain rules remain authoritative;
- no arbitrary SQL against production databases;
- generated query/plan must use approved contracts/adapters;
- provider/model metadata never grants permission.

## 11. C0 inventory

Inventariar factual:

- existing BI semantic models;
- metric/KPI definitions in APIs/frontends/spreadsheets/docs;
- business glossary/documentation;
- data warehouse/lake/SQL sources;
- owners/conflicting definitions;
- freshness/SLA expectations;
- row/resource-level security boundaries.

Sem evidence suficiente = `TO_INVENTORY`.

## 12. Phase mapping

```text
C0 → glossary/metric/source/owner inventory + conflicts + contract decisions
C3 → semantic contracts/versioning foundations only when justified
C4 → governed metric reads/calculations and semantic query pilots
C6 → catalog/lineage/conflict UX and Process Intelligence integration
C7 → advanced federation/materialization/scenario semantics where justified
```

## 13. Acceptance

Quando implementada, provar:

- equivalent query uses same governed metric definition/version;
- formula/version/owner are traceable;
- unauthorized dimension/row remains inaccessible;
- metric conflict is surfaced, not silently merged;
- stale source is explicit;
- new metric can be onboarded without planner hardcode;
- calculations are reproducible from definition + authoritative source/version.

Sem prova obrigatória: `PENDING`/`INCONCLUSIVE`.

## 14. North Star

> **Quando um usuário perguntar por uma métrica empresarial material, DÉLIA deve usar a definição governada do owner correto e preservar lineage, permissions e freshness, nunca improvisar significado ou virar a source of truth do dado.**
