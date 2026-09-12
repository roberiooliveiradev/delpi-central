# Minha DELPI Copilot — Benchmark de Mercado e North Star

**Status:** `REFERENCE_ONLY` — referência estratégica, não authority de execução  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)

## 1. Objetivo

Registrar padrões de mercado que inspiraram o desenho sem copiar arquitetura proprietária nem definir a sequência de implementação.

## 2. North Star

> **Minha DELPI Copilot é a camada inteligente operacional da empresa: entende o contexto da organização, conecta dados, pessoas, processos e aplicações, investiga problemas, executa trabalho, acompanha resultados e transforma conhecimento empresarial em ação governada.**

```text
PERGUNTAR
FAZER
ACOMPANHAR
TRABALHAR
```

## 3. Padrões de mercado considerados

- contexto empresarial profundo/grafos;
- tools/actions ligadas a sistemas reais;
- long-running/durable workflows;
- event triggers/proatividade;
- human-in-the-loop/approvals;
- tasks/cases/collaboration spaces;
- evidence/provenance;
- specialization reutilizável;
- model routing/cost controls;
- governance de conhecimento/capabilities.

Referências conceituais pesquisadas incluíram SAP Joule, Microsoft Copilot Studio, Google Gemini Enterprise, Atlassian Rovo e ServiceNow.

## 4. Decisão própria da Minha DELPI

Não adotar “um agente por departamento” como experiência/authority principal.

```text
1 Copilot
+ Capabilities
+ Expertise Packs
+ Domain Playbooks
+ Knowledge
+ Multimodal Tools
+ Durable Work
```

Workers internos podem existir como implementação subordinada ao mesmo policy/audit.

## 5. Conceitos estratégicos incorporados

- DELPI Business Graph;
- Tasks/Cases/Rooms;
- Inbox/Watch;
- Evidence/Provenance;
- Decision Gates;
- Durable Workflow Runtime;
- Organizational Knowledge;
- Governed Learning;
- Expertise Studio;
- Simulation;
- Model Router.

## 6. Importante: prioridade estratégica ≠ ordem de construção

Classificações antigas como P0/P1/P2 eram prioridades de valor de produto, **não dependências técnicas**.

Após a revisão foundation-first, a única ordem válida é:

```text
C0 Foundations
→ C1 Platform/Context
→ C2 Intelligence Core
→ C3 Business Reads + Graph
→ C4 Governed Writes
→ C5 Durable Work
→ C6 Proactivity/Ecosystem/Learning
→ C7 Optimization/Autonomy/Rollout
```

Exemplo: Business Graph tem alto valor estratégico, mas seu `EntityRef/RelationshipRef` precisa nascer em C0 e o runtime só entra em C3.

## 7. Regra de uso deste documento

Use este benchmark para avaliar direção e valor, não para instruir o Cursor a implementar uma feature.

Implementação sempre segue `16`, contracts `17/21`, gates `20` e requirements `25`.