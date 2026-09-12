# Minha DELPI Copilot — Model Router e Compute Policy

**Status:** thematic spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Runtime phase:** C7, somente depois de baseline real de qualidade, latência, custo e data policy.

## 1. Princípio

O usuário fala com **um Copilot**. Model/provider selection é detalhe interno governado.

```text
task requirements
→ Compute Policy
→ permitted model/provider candidates
→ selected config
→ execute
```

Não criar agentes apenas para usar modelos diferentes.

## 2. Dimensões

- modality;
- reasoning complexity;
- context size;
- structured output requirements;
- data sensitivity/provider policy;
- latency budget;
- cost budget;
- reliability/SLA;
- tool compatibility;
- language/domain only when evidence justifies.

## 3. Classes conceituais

```text
FAST
STANDARD
DEEP_REASONING
MULTIMODAL
LONG_CONTEXT
```

Classes não mapeiam necessariamente 1:1 para um provider/model fixo.

## 4. Compute Policy

C0 define owner/data-policy boundaries; C7 pode criar/estender contract concreto se gap for provado.

Exemplo conceitual:

```text
required modalities
reasoning class
structured output requirement
latency budget
cost class
data classification/provider constraints
```

Evitar criar `ComputePolicyV1` prematuramente se abstração atual de provider/config já atende.

## 5. Fallback

```text
preferred unavailable
→ candidate compatible with security/data/output requirements
→ fallback
→ degraded mode explicit if quality materially differs
```

Fallback nunca relaxa policy/validation.

## 6. Multimodal

Router seleciona multimodal somente quando percepção visual é necessária; não enviar todo turno a modelo multimodal por padrão.

## 7. Internal stage specialization

Planner/synthesis/perception podem futuramente usar modelos diferentes se:

- shared contracts separam stages;
- policy permanece central;
- evidence/provenance registra config material;
- evals provam vantagem;
- não cria experiências/agentes separados.

## 8. Data/provider policy

Filtrar candidates por:

- data class;
- provider allowlist;
- privacy/residency/tenancy constraints;
- retention contract;
- supported capabilities;
- health.

Fallback não pode violar data policy.

## 9. Observability

Registrar:

- model/provider/class;
- structured route reason code;
- latency;
- tokens/cost;
- fallback;
- output validity;
- eval segment.

Sem private CoT.

## 10. Metrics

- completion by class/model;
- cost per completed task;
- P50/P95 latency;
- fallback/retry;
- structured output validity;
- multimodal accuracy;
- correction rate.

## 11. Admin

Centralize:

- active providers/models;
- class mapping;
- budgets;
- cohorts;
- emergency disable;
- health;
- data-policy constraints.

Não espalhar model names pelo domain/application code.

## 12. Tests

- simple task class;
- multimodal compatibility;
- unavailable provider;
- incompatible fallback rejected;
- sensitive data provider blocked;
- latency/cost budgets;
- structured output validity;
- baseline vs candidate quality.

## 13. Implementation mapping

```text
C0 → provider/model inventory + data-policy/owner boundaries
C2–C6 → collect baseline metrics; no intelligent routing required
C7 → implement/extend Model Router only if evidence justifies
```

## 14. Gate

Sem baseline de qualidade/latência/custo, a solução correta é provider/config abstraction simples — não “roteamento inteligente” especulativo.