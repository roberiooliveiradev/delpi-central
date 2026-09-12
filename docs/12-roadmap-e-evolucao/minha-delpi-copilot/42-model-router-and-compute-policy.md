# Minha DELPI Copilot — Model Router e Compute Policy

**Status:** thematic spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Runtime phase:** C7.S4, somente depois de baseline real da própria Copilot API sobre qualidade, latência, custo e data policy.

## 1. Princípio

O usuário fala com **um Copilot**. Model/provider selection é detalhe interno governado da `minha-delpi-copilot-api`.

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

C0 define owner/data-policy boundaries; C3.S1 cria a abstraction baseline simples de provider/model; C7 pode criar/estender roteamento inteligente somente se métricas provarem necessidade.

Exemplo conceitual:

```text
required modalities
reasoning class
structured output requirement
latency budget
cost class
data classification/provider constraints
```

Evitar criar `ComputePolicyV1` prematuramente se a abstração baseline já atende.

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

Understanding/planning/synthesis/perception podem futuramente usar modelos diferentes se:

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

Centralizar no Copilot:

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
- baseline vs candidate quality;
- Chat indisponível sem impacto no provider routing do Copilot.

## 13. Implementation mapping

```text
C0 → provider/model inventory + data-policy/owner boundaries
C3.S1 → provider/model abstraction baseline da Copilot API
C3–C6 → coletar métricas reais; sem intelligent routing obrigatório
C7.S4 → implementar/estender Model Router somente se evidence justificar
```

## 14. Independence

Configuração de provider/model, fallback, telemetry e routing do Minha DELPI Chat não são runtime authority nem fallback do Copilot.

## 15. Gate

Sem baseline de qualidade/latência/custo da **própria Copilot API**, a solução correta é provider/config abstraction simples — não “roteamento inteligente” especulativo.