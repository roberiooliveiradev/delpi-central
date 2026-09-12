# Minha DELPI Copilot

> **Status:** **PLANEJAMENTO EXECUTÁVEL / NOT_STARTED**  
> **Próxima etapa:** **C0.S0 — Rebaseline e inventário real**  
> **Plano executável:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
> **Extensão operacional:** [`44-operational-intelligence-implementation-plan.md`](./44-operational-intelligence-implementation-plan.md)  
> **Especialização do Copilot:** [`27-single-copilot-specialization-architecture.md`](./27-single-copilot-specialization-architecture.md)  
> **Prompt do Cursor:** [`23-prompt-cursor-execucao.md`](./23-prompt-cursor-execucao.md)  
> **Ledger:** [`evidence/execution-ledger.md`](./evidence/execution-ledger.md)

## 1. Visão

O **Minha DELPI Copilot** é a camada inteligente transversal da plataforma. Não é um chatbot isolado nem automação de cliques. Ele evolui para a **camada inteligente operacional da empresa**.

```text
usuário
→ conversa/contexto/evento
→ goals/subtasks
→ capabilities autorizadas
→ expertise/playbooks
→ plano operacional
→ RBAC/policy/decision gates
→ execução/monitoramento
→ observação/evidence
→ análise/síntese
→ resultado/navegação/continuidade
```

### Princípio central

> Tudo que um usuário autorizado consegue consultar, analisar ou executar na Minha DELPI deve poder ser representado como uma **Capability** que o Copilot também consegue descobrir e utilizar, respeitando as mesmas permissões, políticas e contratos de negócio.

```text
UI ───────────────┐
                  ▼
              API / Use Case
                  ▲
Copilot ──────────┘
```

### North Star

> **Minha DELPI Copilot entende o contexto da organização, conecta dados, pessoas, processos e aplicações, investiga problemas, executa trabalho, acompanha resultados e transforma conhecimento empresarial em ação governada.**

O produto é organizado por quatro verbos:

```text
PERGUNTAR  → entender, pesquisar, explicar, analisar
FAZER      → abrir, consultar, criar, alterar, aprovar, executar
ACOMPANHAR → monitorar, detectar, lembrar, alertar, reagir
TRABALHAR  → investigar, colaborar, planejar, acompanhar ações, concluir
```

### Princípio de especialização

> Existe **um único Minha DELPI Copilot**. Engenharia, Qualidade, Suprimentos, Comercial, Financeiro, RH e demais domínios não viram agentes independentes; especializam o mesmo runtime por **Expertise Packs**, **Domain Playbooks**, knowledge scopes, capabilities e ferramentas multimodais.

## 2. Arquitetura alvo

```text
                          MINHA DELPI COPILOT
                                  │
              ┌───────────────────┼───────────────────┐
              ▼                   ▼                   ▼
           PERGUNTAR             FAZER             ACOMPANHAR
        Knowledge/RAG       Capabilities/APIs      Events/Watch
              │                   │                   │
              └───────────────────┼───────────────────┘
                                  ▼
                              TRABALHAR
                    Tasks / Cases / Interaction Rooms
                                  │
                    Expertise Packs + Domain Playbooks
                                  │
                         DELPI Business Graph
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        ▼                         ▼                         ▼
     OpenAPI                   Knowledge                Multimodal
     Actions             Decisions/Experience       Drawings/Images/Docs
        │                         │                         │
        └─────────────────────────┼─────────────────────────┘
                                  ▼
                 RBAC / Policy / Decision Gates / Audit
                                  │
                      Durable Workflow Runtime
```

## 3. Fontes de verdade e contexto

### Business Actions

```text
OpenAPI
→ Action Catalog
→ allowed actions
→ capability projection
→ planner/validator/policy
→ executor genérico
```

A `Capability Projection` é índice/visão semântica, **não nova fonte técnica**. Method/path/operationId/schema continuam no OpenAPI/Action Catalog.

### Platform Actions

```text
Core API /me/apps
→ apps/rotas autorizados
→ Platform Capability Projection
→ PlatformCommand tipado
→ CopilotBridge
→ Portal Router/MFE/IframeBridge
```

### Expertise

```text
goals/contexto/attachments
→ Expertise Catalog
→ semantic retrieval top-K
→ ExpertiseContext
→ planner/análise
```

Expertise melhora interpretação; não concede permission e não substitui Action Catalog.

### Domain Playbooks

```text
método de domínio
→ applicability/evidence checklist
→ planner converte em plano operacional usando capabilities autorizadas
```

### Workspace Context

```text
MFE ou iframe integrado
→ WorkspaceContext tipado
→ Portal Context Store
→ bounded turn context
→ Copilot
```

### Business Graph

```text
EntityRef + RelationshipRef
→ orienta traversal/retrieval/planning
→ source APIs continuam authorities dos dados atuais
```

### Evidence/Provenance

```text
source result/document
→ EvidenceRef
→ Claim (fact/calculation/hypothesis/conclusion/recommendation)
→ analysis/case/artifact
```

## 4. Trabalho persistente

O chat não é a única unidade de trabalho:

```text
Turn → Task → Case
              └→ Interaction Room
```

- **Task:** objetivo delimitado multi-step;
- **Case:** investigação/processo de longa duração;
- **Room:** colaboração entre pessoas + Copilot + evidências + ações;
- **Inbox:** pendências, approvals, resultados e alertas;
- **Watch:** condição/evento a acompanhar;
- **Durable Workflow:** wait/resume/checkpoint sem reexecutar tudo.

## 5. Conhecimento e decisão

O produto separa:

```text
Reference Knowledge
Operational Knowledge
Decision Knowledge
Experience Knowledge
Semantic Knowledge / Business Graph
```

Análises materiais diferenciam:

```text
FACT
CALCULATION
HYPOTHESIS
CONCLUSION
RECOMMENDATION
```

Decision Gates evoluem o simples `confirm=true` para aprovação proporcional a risco/impacto. What-if/Simulation só é tratado como simulação quando existe modelo/cálculo governado e premissas explícitas.

## 6. Apps iframe

```text
PORTAL_ONLY
→ abre app/rota

CONTEXTUAL
→ + publica contexto

INTERACTIVE
→ + comandos visuais genéricos

AI_READY
→ + Business Actions reais via API/OpenAPI
```

Fonte: [`26-iframe-copilot-bridge.md`](./26-iframe-copilot-bridge.md).

## 7. Dependência crítica atual

A iniciativa de desacoplamento OpenAPI/LLM da `minha-delpi-ai-api` permanece documentada com `VERIFY_FINAL_FAILED`.

```text
C0-C2
→ podem avançar

C3+ Business Actions production-ready
→ dependem dos gates OpenAPI-first/tool/eval relevantes PASS
```

A migração de agents para expertise e esta expansão estratégica **não autorizam runtime diff antes de C0.S0**.

## 8. Documentação canônica

### Produto, arquitetura e especialização

| Documento | Conteúdo |
|---|---|
| [`01-visao-produto.md`](./01-visao-produto.md) | visão e experiência-alvo |
| [`02-arquitetura.md`](./02-arquitetura.md) | arquitetura e responsabilidades |
| [`03-capability-model.md`](./03-capability-model.md) | capabilities |
| [`04-platform-actions.md`](./04-platform-actions.md) | Portal/Shell actions |
| [`05-workspace-context-protocol.md`](./05-workspace-context-protocol.md) | contexto |
| [`06-business-action-parity.md`](./06-business-action-parity.md) | UI ↔ API ↔ Copilot |
| [`07-agentic-workflows.md`](./07-agentic-workflows.md) | workflows |
| [`08-security-autonomy-audit.md`](./08-security-autonomy-audit.md) | RBAC/autonomia/audit |
| [`09-ux-copilot.md`](./09-ux-copilot.md) | UX |
| [`10-plugin-ai-ready-standard.md`](./10-plugin-ai-ready-standard.md) | AI-ready |
| [`11-observability-evals.md`](./11-observability-evals.md) | métricas/evals |
| [`12-roadmap.md`](./12-roadmap.md) | roadmap macro |
| [`13-functional-catalog.md`](./13-functional-catalog.md) | catálogo funcional |
| [`14-definition-of-done.md`](./14-definition-of-done.md) | DoD |
| [`15-integration-map.md`](./15-integration-map.md) | integração atual |
| [`26-iframe-copilot-bridge.md`](./26-iframe-copilot-bridge.md) | iframe bridge |
| [`27-single-copilot-specialization-architecture.md`](./27-single-copilot-specialization-architecture.md) | Copilot único |
| [`28-expertise-pack-specification.md`](./28-expertise-pack-specification.md) | Expertise Packs |
| [`29-domain-playbooks-specification.md`](./29-domain-playbooks-specification.md) | Domain Playbooks |
| [`30-multimodal-expertise-and-drawing-analysis.md`](./30-multimodal-expertise-and-drawing-analysis.md) | multimodal/desenhos |
| [`31-agent-to-expertise-migration-plan.md`](./31-agent-to-expertise-migration-plan.md) | migração de agents |
| [`32-expertise-runtime-implementation-plan.md`](./32-expertise-runtime-implementation-plan.md) | runtime expertise |
| [`33-reference-expertise-packs-quality-engineering.md`](./33-reference-expertise-packs-quality-engineering.md) | Qualidade/Engenharia |

### Evolução para camada operacional inteligente

| Documento | Conteúdo |
|---|---|
| [`34-market-benchmark-and-product-north-star.md`](./34-market-benchmark-and-product-north-star.md) | benchmark e North Star |
| [`35-delpi-business-graph.md`](./35-delpi-business-graph.md) | DELPI Business Graph |
| [`36-copilot-tasks-cases-and-interaction-rooms.md`](./36-copilot-tasks-cases-and-interaction-rooms.md) | Tasks/Cases/Rooms |
| [`37-copilot-inbox-watch-and-proactive-work.md`](./37-copilot-inbox-watch-and-proactive-work.md) | Inbox/Watch |
| [`38-evidence-provenance-and-epistemic-ux.md`](./38-evidence-provenance-and-epistemic-ux.md) | Evidence/Provenance |
| [`39-decision-gates-and-what-if-simulation.md`](./39-decision-gates-and-what-if-simulation.md) | Decision Gates/What-if |
| [`40-organizational-knowledge-and-governed-learning.md`](./40-organizational-knowledge-and-governed-learning.md) | conhecimento/aprendizagem |
| [`41-expertise-studio-governance.md`](./41-expertise-studio-governance.md) | Expertise Studio |
| [`42-model-router-and-compute-policy.md`](./42-model-router-and-compute-policy.md) | Model Router |
| [`43-durable-workflow-runtime.md`](./43-durable-workflow-runtime.md) | Durable Workflow Runtime |
| [`44-operational-intelligence-implementation-plan.md`](./44-operational-intelligence-implementation-plan.md) | plano O0–O13 |
| [`45-operational-intelligence-testing-gates.md`](./45-operational-intelligence-testing-gates.md) | gates de teste adicionais |
| [`46-operational-intelligence-requirements.md`](./46-operational-intelligence-requirements.md) | requisitos CP-090–CP-129 |
| [`47-cursor-operational-intelligence-extension.md`](./47-cursor-operational-intelligence-extension.md) | suplemento obrigatório do Cursor |

### Execução e implantação

| Documento | Conteúdo |
|---|---|
| [`16-execution-master-plan.md`](./16-execution-master-plan.md) | plano atômico C0–C7 |
| [`17-component-and-contract-map.md`](./17-component-and-contract-map.md) | ownership/contratos |
| [`18-app-onboarding-matrix.md`](./18-app-onboarding-matrix.md) | matriz de apps |
| [`19-rollout-and-migrations.md`](./19-rollout-and-migrations.md) | rollout/migrations |
| [`20-testing-and-acceptance-matrix.md`](./20-testing-and-acceptance-matrix.md) | testes base |
| [`21-data-and-state-model.md`](./21-data-and-state-model.md) | dados/estado |
| [`22-cursor-execution-protocol.md`](./22-cursor-execution-protocol.md) | protocolo Cursor |
| [`23-prompt-cursor-execucao.md`](./23-prompt-cursor-execucao.md) | prompt mestre consolidado |
| [`24-product-specification.md`](./24-product-specification.md) | especificação completa |
| [`25-requirements-traceability.md`](./25-requirements-traceability.md) | CP-001–CP-089 |
| [`evidence/execution-ledger.md`](./evidence/execution-ledger.md) | evidence/estado real |

## 9. Invariantes

```text
1. Copilot permissions ⊆ permissões efetivas do usuário.
2. Nenhuma action bypassa RBAC/policy/Decision Gate.
3. LLM não inventa URL, endpoint, actionId ou permission.
4. Business Actions usam API/use case quando existe contrato.
5. Novo app/API entra por contratos, não hardcode central.
6. Capability Projection não vira catálogo técnico paralelo.
7. Workspace Context/Business Graph não são authority de autorização.
8. Evidence e hipóteses não podem ser confundidas.
9. Writes respeitam sensitivity, idempotency e audit.
10. Durable Workflow revalida permissões ao retomar.
11. Watch/evento não concede autonomia por si só.
12. Experience Knowledge só é promovido por processo governado.
13. Expertise/Playbook não contém catálogo manual de endpoints.
14. Iframe não usa DOM automation como substituto de API.
15. Chain-of-thought não é persistida.
16. Existe um único Copilot de produto; departamento não cria novo agente/runtime.
17. Novo Expertise Pack compatível não exige patch no planner central.
18. Simulação não executa write implicitamente.
19. Model Router é detalhe interno e não fragmenta memória/contexto.
20. Task/Case/Room não concedem acesso às entidades originais.
```

## 10. Ordem de execução

O Cursor continua começando por **C0.S0**. A expansão estratégica deve ser inventariada e faseada; não autoriza criar todos os componentes de uma vez.

```text
C0 fundação/inventário/contratos
→ C1 navegação
→ C2 contexto
→ C3 business parity + evidence foundation
→ C4 workflows + tasks/checkpoints
→ C5 AI-ready + expertise + graph/cases progressivos
→ C6 autonomy + decision gates/watch governado
→ C7 rollout
→ ondas posteriores de Inbox/Simulation/Experience/Model Router conforme gates
```

A sequência detalhada O0–O13 está em `44-operational-intelligence-implementation-plan.md`.

## 11. Resultado esperado

> “Esse produto está dando problema no cliente. Analise o desenho, procure casos parecidos, relacione produção, qualidade e fornecedor, monte uma investigação 8D, acompanhe as evidências que faltam e me avise quando Engenharia liberar a nova revisão.”

O Copilot deve transformar isso em trabalho persistente, grounded, auditável e governado — não apenas em uma resposta de chat.