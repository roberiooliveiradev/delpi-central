# Minha DELPI Copilot — Benchmark de Mercado e North Star

**Status:** `REFERENCE_ONLY` — referência estratégica, não authority de execução  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)

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
1 Copilot standalone
+ Capabilities
+ Expertise Packs
+ Domain Playbooks
+ Knowledge
+ Multimodal Tools
+ Durable Work
```

Workers internos podem existir como implementação subordinada ao mesmo policy/audit da Copilot API.

Outra decisão própria fundamental é **não evoluir o Minha DELPI Chat para virar Copilot**. O produto nasce com API/MFE/runtime próprios e usa o Chat apenas como referência histórica/técnica em C0.

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

Após a revisão standalone/foundation-first, a única ordem válida é:

```text
C0 Platform + Architecture Foundation Freeze
→ C1 Standalone Application Bootstrap
→ C2 Portal Context + Platform Commands
→ C3 Intelligence Core
→ C4 Business Reads + DELPI Business Graph
→ C5 Governed Writes + Durable Work Foundation
→ C6 Product Work + Proactivity + Ecosystem
→ C7 Autonomy + Optimization + Rollout
```

Exemplo: Business Graph tem alto valor estratégico, mas `EntityRef/RelationshipRef` nasce em C0 e o runtime entra em C4. O mesmo vale para Task/Case: seus contracts nascem em C0, Durable Workflow nasce em C5 e os produtos Task/Case entram em C6.

## 7. Interpretação correta dos benchmarks

As soluções de mercado podem inspirar experiência, governança e capacidades, mas não são justificativa para:

- multi-agent departmental runtime;
- acoplar Copilot ao Minha DELPI Chat;
- copiar arquitetura de terceiros sem aderência ao monorepo;
- criar authorities paralelas às APIs/Core;
- antecipar Model Router, Graph storage ou Durable Workflow antes de seus gates.

## 8. Regra de uso deste documento

Use este benchmark para avaliar direção e valor, não para instruir o Cursor a implementar uma feature.

Implementação sempre segue `16`, boundary `50`, contracts `17/21`, gates `20` e requirements `25`.