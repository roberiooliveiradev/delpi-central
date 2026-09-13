# Minha DELPI Copilot — Semantic Business Layer e Métricas Governadas

**Status:** thematic data/product/architecture spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Business Graph:** [`35-delpi-business-graph.md`](./35-delpi-business-graph.md)  
**Evidence:** [`38-evidence-provenance-and-epistemic-ux.md`](./38-evidence-provenance-and-epistemic-ux.md)

## 1. Decisão

Business Graph e Semantic Business Layer são complementares:

```text
Business Graph
= relações entre entidades

Semantic Business Layer
= significado oficial de métricas, dimensões, regras de agregação e conceitos analíticos
```

O Copilot não deve inventar fórmulas para métricas empresariais conhecidas.

## 2. MetricDefinition

Conceito candidate a congelar em C0/C3:

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

## 3. Governed dimensions

Dimensões também precisam de semântica consistente:

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

IDs continuam nos sistemas owners; camada semântica referencia, não replica master data.

## 4. Semantic query flow

```text
user question
→ identify governed metric/concept
→ permission-aware semantic plan
→ owner query/read capability
→ deterministic calculation/aggregation
→ Evidence + metric definition version
→ explanation
```

LLM interpreta intenção; cálculo material usa definição estruturada/reprodutível.

## 5. Metric authority

Cada métrica material possui owner de negócio. Alteração de fórmula exige versionamento/review e não pode ocorrer silenciosamente por prompt ou aprendizado automático.

## 6. Conflict handling

Se duas áreas usam definições diferentes:

```text
same label + different meaning
→ separate metric IDs/versions
→ explicit owner/scope
→ UX surfaces conflict
```

Não escolher uma definição arbitrariamente.

## 7. Zero-copy / federation principle

Quando tecnicamente possível:

```text
semantic definition
→ query authoritative source
```

em vez de copiar todos os dados para uma camada central. Materializações/cache são bounded, versionadas, com freshness e lineage.

## 8. Business glossary

A camada pode manter conceitos além de métricas:

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

Cada conceito possui definição, owner, exemplos, fonte e versionamento.

## 9. Integration with Graph/Process Intelligence/Twin

```text
Semantic Layer → metrics/meaning
Business Graph  → entity relationships
Process Intelligence → process metrics/variants
Operational Twin → state/scenario variables
```

Os quatro não devem colapsar em um único modelo genérico sem ownership claro.

## 10. Security

- semantic metadata does not grant data access;
- query revalidates source permissions;
- sensitive metric may require aggregation/redaction;
- row-level/resource-level domain rules remain authoritative;
- no SQL generated directly against arbitrary databases without approved adapter/contracts.

## 11. C0 inventory

Inventariar:

- existing BI semantic models;
- Power BI/other metric definitions if present;
- KPI formulas in APIs/frontends/spreadsheets;
- business glossary/documentation;
- data warehouse/lake/SQL sources;
- owners and conflicting definitions;
- freshness/SLA expectations;
- row-level security/permission boundaries.

## 12. Phase mapping

```text
C0 → glossary/metric/source/owner inventory and conflict map
C3 → canonical semantic contracts/versioning/registry foundations
C4 → governed metric reads/calculations and semantic query pilots
C6 → admin/catalog UX, lineage, Process Intelligence integration
C7 → advanced semantic optimization/federation and scenario semantics
```

## 13. Acceptance

- same metric returns same result across equivalent Copilot queries;
- formula/version is traceable;
- unauthorized dimension/row remains inaccessible;
- metric conflict is surfaced instead of silently merged;
- stale source is explicit;
- new metric can be added without planner code change;
- calculations are reproducible from definition + source snapshot/version.

## 14. North Star

> **Quando o usuário perguntar “qual é o faturamento?”, “qual é o lead time?” ou “qual é o OEE?”, o Copilot deve usar o significado empresarial oficial, não uma interpretação improvisada.**
