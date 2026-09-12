# Minha DELPI Copilot — Model Router e Compute Policy

**Status:** arquitetura proposta  
**Objetivo:** usar o nível de inteligência, modalidade, latência e custo adequados para cada tarefa sem fragmentar a experiência do Copilot.

## 1. Princípio

O usuário fala com **um Copilot**. A escolha de modelo é detalhe interno governado.

```text
turn/task
→ requirement classification
→ compute policy
→ model/provider candidate
→ policy/security constraints
→ execute
```

Não criar “agentes” apenas para escolher modelos diferentes.

## 2. Dimensões de roteamento

- modalidade: texto / visão / documento;
- complexidade de reasoning;
- tamanho/contexto;
- necessidade de structured output;
- sensibilidade dos dados/provider policy;
- latency budget;
- cost budget;
- reliability/SLA;
- tool-use compatibility;
- idioma/domínio quando comprovadamente relevante.

## 3. Classes conceituais

```text
FAST
→ classificação, navegação simples, transformações curtas

STANDARD
→ consultas, sínteses e workflows comuns

DEEP_REASONING
→ problemas complexos/multi-step/causa raiz

MULTIMODAL
→ desenhos, imagens, documentos visuais

LONG_CONTEXT
→ grandes conjuntos documentais quando retrieval não é suficiente
```

As classes não precisam mapear 1:1 para fornecedores ou modelos fixos.

## 4. ComputePolicyV1

```json
{
  "taskType": "quality.root_cause_analysis",
  "requiredModalities": ["text"],
  "reasoningClass": "deep_reasoning",
  "latencyBudgetMs": 30000,
  "costClass": "controlled",
  "structuredOutput": true
}
```

O router resolve para configuração vigente de models/providers.

## 5. Fallback

Fallback deve preservar segurança e verdade operacional.

```text
preferred unavailable
→ compatible fallback
→ capability/policy requirements still valid
→ explicit degraded mode when quality materially differs
```

Nunca remover validation/policy para caber num modelo alternativo.

## 6. Multimodal routing

Desenho técnico pode exigir:

```text
native parser/OCR
→ multimodal model
→ expertise
```

O router deve considerar a necessidade real de visão; não enviar todas as mensagens para modelo multimodal por padrão.

## 7. Tool planner vs synthesis

A implementação pode usar modelos distintos para etapas internas se isso for comprovadamente melhor, mas:

- o workflow continua único;
- contracts estruturados separam etapas;
- policy não depende de texto livre entre modelos;
- provenance registra configurações relevantes;
- evals validam o pipeline real.

## 8. Privacidade e provider policy

O router deve filtrar candidates compatíveis com:

- classificação dos dados;
- região/tenancy quando aplicável;
- contratos corporativos;
- políticas de retenção;
- capabilities suportadas.

## 9. Observabilidade

Registrar sem segredo:

```text
model/provider class
reason for route (category, not private CoT)
latency
tokens/cost
fallback
quality/eval segment
```

## 10. Métricas

- task completion por class/model;
- cost per completed task;
- P50/P95 latency;
- fallback rate;
- retry rate;
- structured output validity;
- tool trajectory quality;
- multimodal extraction accuracy;
- correction rate.

## 11. Administração

Configuração central deve permitir:

- models/providers ativos;
- classes suportadas;
- budgets;
- rollout/cohort;
- emergency disable;
- provider health;
- policy constraints.

Não espalhar nome do modelo pelo domínio/application.

## 12. Testes

- tarefa simples escolhe classe apropriada;
- multimodal exige modelo compatível;
- provider indisponível;
- fallback incompatível é rejeitado;
- sensitive data não vai para provider proibido;
- latency/cost thresholds;
- output schema continua válido;
- same task under candidate config mantém outcome esperado.

## 13. Gate

Model Router só deve ser introduzido após existir baseline de qualidade/latência/custo. Antes disso, abstrair provider/config corretamente é suficiente; não adicionar roteamento “inteligente” sem evidence.