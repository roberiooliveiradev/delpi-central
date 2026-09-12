# Minha DELPI Copilot — Benchmark de Mercado e North Star

**Status:** `REFERENCE_ONLY` — referência estratégica, não authority de execução  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)

## 1. Objetivo

Registrar padrões de mercado que inspiraram o desenho sem copiar arquitetura proprietária nem definir a sequência de implementação.

## 2. North Star

> **Minha DELPI Copilot é a interface inteligente entre as pessoas e a operação da DELPI: entende contexto empresarial e operacional, conecta dados, pessoas, processos e aplicações, investiga problemas, executa trabalho, acompanha resultados e transforma experiência validada em conhecimento governado — no escritório, em reuniões e no chão de fábrica.**

```text
PERGUNTAR
FAZER
ACOMPANHAR
TRABALHAR
APRENDER COM GOVERNANÇA
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
- multimodal interaction;
- voice/camera/screen experiences;
- meeting assistance;
- frontline/operator assistance;
- contextual training;
- model routing/cost controls;
- governance de conhecimento/capabilities.

Referências conceituais de mercado podem incluir soluções de enterprise copilot, collaboration/meeting AI e frontline operations, mas **nenhuma arquitetura externa substitui evidence do monorepo DELPI**.

## 4. Decisões próprias da Minha DELPI

Não adotar “um agente por departamento” como experiência/authority principal.

```text
1 Copilot standalone
+ Capabilities
+ Expertise Packs
+ Domain Playbooks
+ Knowledge
+ Multimodal Tools
+ Durable Work
+ Global/Workspace/Meeting/Frontline surfaces
```

Workers internos podem existir como implementação subordinada ao mesmo policy/audit da Copilot API.

Decisões fundamentais adicionais:

- não evoluir o Minha DELPI Chat para virar Copilot;
- não criar Meeting/Frontline como runtimes paralelos;
- voz/imagem/vídeo não ampliam RBAC;
- process learning produz candidates, não auto-rules;
- computer vision não vira quality authority por default;
- Copilot não vira industrial safety controller;
- free-form LLM→machine actuation permanece bloqueado sem iniciativa OT separada.

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
- Meeting Mode/ata viva;
- Frontline/operator assistance;
- multimodal voice/image/video/screen;
- shared-device safety;
- privacy/media lifecycle;
- Simulation;
- Model Router;
- advanced realtime only after evidence.

## 6. Importante: prioridade estratégica ≠ ordem de construção

Classificações antigas como P0/P1/P2 eram prioridades de valor de produto, **não dependências técnicas**.

A única ordem válida é:

```text
C0 Platform + Architecture + Media/Privacy/OT Foundation Freeze
→ C1 Standalone Application Bootstrap
→ C2 Portal + Operational Context + Platform Commands
→ C3 Intelligence Core + Multimodal Foundations
→ C4 Business Reads + DELPI Business Graph
→ C5 Governed Writes + Durable Work Foundation
→ C6 Product Work + Meeting/Frontline + Proactivity + Ecosystem
→ C7 Advanced Realtime + Autonomy + Optimization + Rollout
```

Exemplos:

- Business Graph tem alto valor, mas `EntityRef/RelationshipRef` nasce em C0 e runtime em C4;
- Task/Case contracts nascem em C0, Durable Workflow em C5 e produtos em C6;
- Meeting/Frontline têm alto valor, mas media/privacy/device/OT boundaries nascem em C0, media intelligence em C3 e product surfaces em C6;
- continuous video/realtime pertence a C7 somente após evidence de valor/custo/privacy.

## 7. Interpretação correta dos benchmarks

Soluções de mercado podem inspirar experiência, governança e capacidades, mas não justificam:

- multi-agent departmental runtime;
- acoplar Copilot ao Minha DELPI Chat;
- copiar arquitetura de terceiros sem aderência ao monorepo;
- criar authorities paralelas às APIs/Core;
- criar `FrontlineContext` paralelo;
- armazenar áudio/vídeo indiscriminadamente;
- adotar reconhecimento facial/emotion detection por default;
- transformar “AI agent” em caminho para PLC/CNC/robô;
- antecipar Model Router, Graph storage, advanced realtime ou Durable Workflow antes de seus gates.

## 8. Regra de uso deste documento

Use este benchmark para avaliar direção e valor, não para instruir o Cursor a implementar uma feature.

Implementação sempre segue `16`, boundary `50`, contracts `17/21`, patterns `49`, spec `53`, gates `20` e requirements `25`.