# Minha DELPI Copilot — Benchmark de Mercado e North Star do Produto

**Status:** proposta estratégica incorporada ao roadmap  
**Objetivo:** elevar o Copilot de chat com actions para camada operacional inteligente da Minha DELPI.

## 1. North Star

O produto alvo não é apenas um assistente que responde perguntas e chama APIs.

> **Minha DELPI Copilot é a camada inteligente operacional da empresa: entende o contexto da organização, conecta dados, pessoas, processos e aplicações, investiga problemas, executa trabalho, acompanha resultados e transforma conhecimento empresarial em ação governada.**

## 2. Quatro verbos do produto

```text
PERGUNTAR
→ entender, pesquisar, explicar, analisar

FAZER
→ abrir, consultar, criar, alterar, aprovar, executar

ACOMPANHAR
→ monitorar, detectar, lembrar, alertar, reagir

TRABALHAR
→ investigar, colaborar, planejar, acompanhar ações, concluir
```

O chat é a porta de entrada em linguagem natural, não a única superfície nem a única unidade de trabalho.

## 3. Tendências de mercado que informam o desenho

Os produtos corporativos mais maduros convergem para alguns padrões:

- contexto empresarial profundo e grafos de conhecimento/trabalho;
- tools/actions conectadas a sistemas reais;
- workflows duráveis e de longa duração;
- event triggers/proatividade;
- human-in-the-loop e approvals;
- espaços colaborativos/cases/tasks;
- evidência/provenance e auditabilidade;
- especialização componível sem duplicar todo o runtime;
- roteamento de modelos conforme custo/complexidade;
- administração governada de conhecimento e capacidades.

Referências de benchmark usadas para orientar o produto, sem copiar arquitetura proprietária:

- SAP Joule / AI Agents / Knowledge Graph;
- Microsoft Copilot Studio / event triggers / autonomous agents / approvals;
- Google Gemini Enterprise / long-running agents / collaboration spaces / agent inbox;
- Atlassian Rovo / Teamwork Graph / reusable skills;
- ServiceNow AI Agent Orchestrator / governança de trabalho multi-sistema.

A Minha DELPI deliberadamente não adota o modelo de “um agente por departamento” como identidade principal. O produto mantém **um Copilot único** e especialização componível.

## 4. Diferencial arquitetural da Minha DELPI

```text
1 Copilot
+ N Capabilities
+ N Expertise Packs
+ N Domain Playbooks
+ N Knowledge Scopes
+ N Multimodal Tools
+ N Durable Workflows
```

Workers internos especializados podem existir futuramente como detalhe de implementação, desde que invisíveis ao usuário e subordinados ao mesmo runtime/policy/audit.

## 5. Componentes estratégicos adicionais

A evolução alvo incorpora:

1. **DELPI Business Graph** — mapa semântico de entidades e relações empresariais;
2. **Copilot Tasks / Cases / Rooms** — unidades de trabalho além do turno de chat;
3. **Copilot Inbox** — pendências, decisões, confirmações, alertas e resultados;
4. **Copilot Watch** — monitoramento orientado a eventos/condições;
5. **Evidence & Provenance Layer** — fatos rastreáveis, frescor, confiança e fontes;
6. **Decision Gates** — aprovação baseada em risco/impacto/policy;
7. **Simulation / What-if** — análise de cenários antes de aplicar mudanças;
8. **Organizational Knowledge** — referência, operação, decisões e experiência;
9. **Expertise Studio** — lifecycle governado de especialidades/playbooks;
10. **Model Router** — escolha de modelo conforme tarefa/custo/latência;
11. **Durable Workflow Runtime** — wait/resume/checkpoint/event/approval;
12. **Governed Learning Loop** — feedback → proposta → eval → publicação.

## 6. Prioridade sugerida

### P0 — fundação do produto excelente

- Business Graph mínimo;
- Tasks/Cases;
- Evidence/Provenance;
- arquitetura de Copilot único já definida.

### P1 — operação contínua

- Inbox;
- Watch/event triggers;
- Decision Gates;
- Durable Workflow Runtime;
- Expertise Studio básico.

### P2 — decisão avançada e eficiência

- What-if/Simulation;
- Organizational Experience Memory;
- Model Router avançado;
- aprendizagem governada.

## 7. Regra de produto

Toda nova funcionalidade deve responder:

```text
isso melhora PERGUNTAR, FAZER, ACOMPANHAR ou TRABALHAR?
```

Se não contribuir de forma material para um desses pilares, não deve aumentar a complexidade do core.