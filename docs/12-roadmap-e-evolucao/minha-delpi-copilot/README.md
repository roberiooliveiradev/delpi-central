# Minha DELPI Copilot

> **Status:** **PLANEJAMENTO EXECUTÁVEL / NOT_STARTED**  
> **Próxima etapa:** **C0.S0 — Rebaseline e inventário real**  
> **Plano executável:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
> **Prompt do Cursor:** [`23-prompt-cursor-execucao.md`](./23-prompt-cursor-execucao.md)  
> **Ledger:** [`evidence/execution-ledger.md`](./evidence/execution-ledger.md)

## 1. Visão

O **Minha DELPI Copilot** é a camada inteligente transversal da plataforma. Não é um chatbot isolado nem automação de cliques. Ele funciona como uma segunda interface operacional da Minha DELPI:

```text
usuário
→ conversa
→ goals/subtasks
→ capabilities autorizadas
→ plano operacional
→ RBAC/policy/confirmation
→ execução
→ observação
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

## 2. Arquitetura alvo

```text
                         USUÁRIO
                            │
               ┌────────────┴────────────┐
               │                         │
              UI                       COPILOT
               │                         │
               │                 Goals / Planner
               │                         │
               │              Capability Retrieval
               │                         │
               │           ┌─────────────┼─────────────┐
               │           │             │             │
               │           ▼             ▼             ▼
               │       Business      Platform       Knowledge
               │       Actions       Actions          Tools
               │           │             │             │
               │           ▼             ▼             ▼
               │        OpenAPI       Portal        RAG/Web
               │           │          Bridge
               │           │             │
               ▼           ▼             ▼
           ┌────────────────────────────────────┐
           │ RBAC / policy / sensitivity /     │
           │ confirmation / audit / budgets    │
           └────────────────┬───────────────────┘
                            │
                     Generic Execution
                            │
              ┌─────────────┼──────────────┐
              ▼             ▼              ▼
            APIs           MFEs           Core
```

## 3. Fonte de verdade por capability

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
→ Portal Router/MFE
```

Sem app→URL hardcoded no Copilot.

### Workspace Context

```text
MFE
→ WorkspaceContext tipado
→ Portal Context Store
→ bounded turn context
→ Copilot
```

Contexto não é permissão.

## 4. Dependência crítica atual

A iniciativa de desacoplamento OpenAPI/LLM da `minha-delpi-ai-api` permanece documentada com `VERIFY_FINAL_FAILED`.

Consequência:

```text
C0-C2
→ podem avançar

C3+ Business Actions production-ready
→ dependem dos gates OpenAPI-first/tool/eval relevantes PASS no candidate vigente
```

O Copilot não cria workaround nem duplica a correção da Onda J.

## 5. Documentação completa

### Produto e arquitetura

| Documento | Conteúdo |
|---|---|
| [`01-visao-produto.md`](./01-visao-produto.md) | visão, personas, experiência-alvo |
| [`02-arquitetura.md`](./02-arquitetura.md) | arquitetura e responsabilidades |
| [`03-capability-model.md`](./03-capability-model.md) | modelo de capabilities |
| [`04-platform-actions.md`](./04-platform-actions.md) | ações do Portal/Shell |
| [`05-workspace-context-protocol.md`](./05-workspace-context-protocol.md) | contexto Portal/MFE/Copilot |
| [`06-business-action-parity.md`](./06-business-action-parity.md) | paridade UI ↔ API/use case ↔ Copilot |
| [`07-agentic-workflows.md`](./07-agentic-workflows.md) | DAG/workflows multi-app |
| [`08-security-autonomy-audit.md`](./08-security-autonomy-audit.md) | RBAC, autonomia, confirmação, audit |
| [`09-ux-copilot.md`](./09-ux-copilot.md) | UX do Copilot |
| [`10-plugin-ai-ready-standard.md`](./10-plugin-ai-ready-standard.md) | padrão AI-ready |
| [`11-observability-evals.md`](./11-observability-evals.md) | métricas/evals |
| [`12-roadmap.md`](./12-roadmap.md) | visão macro das fases |
| [`13-functional-catalog.md`](./13-functional-catalog.md) | catálogo funcional |
| [`14-definition-of-done.md`](./14-definition-of-done.md) | DoD global/por fase |
| [`15-integration-map.md`](./15-integration-map.md) | mapa dos componentes atuais |

### Execução e implantação

| Documento | Conteúdo |
|---|---|
| [`16-execution-master-plan.md`](./16-execution-master-plan.md) | **plano atômico C0–C7 e C*.S*** |
| [`17-component-and-contract-map.md`](./17-component-and-contract-map.md) | ownership, producer/consumer e contratos v1 |
| [`18-app-onboarding-matrix.md`](./18-app-onboarding-matrix.md) | matriz AI-ready de apps |
| [`19-rollout-and-migrations.md`](./19-rollout-and-migrations.md) | deploy, flags, canary, rollback, migrations |
| [`20-testing-and-acceptance-matrix.md`](./20-testing-and-acceptance-matrix.md) | gates de teste/aceite |
| [`21-data-and-state-model.md`](./21-data-and-state-model.md) | contexto, workflow, confirmation, persistence |
| [`22-cursor-execution-protocol.md`](./22-cursor-execution-protocol.md) | protocolo obrigatório por step |
| [`23-prompt-cursor-execucao.md`](./23-prompt-cursor-execucao.md) | prompt mestre para implementação |
| [`24-product-specification.md`](./24-product-specification.md) | especificação funcional/técnica consolidada |
| [`25-requirements-traceability.md`](./25-requirements-traceability.md) | requisitos CP-* → owner → fase → gate |
| [`evidence/execution-ledger.md`](./evidence/execution-ledger.md) | estado executável/evidências |

## 6. Funcionalidades alvo

O produto completo contempla:

- chat global e contextual;
- abertura de apps/rotas/entidades;
- filtros/view context tipados;
- entendimento do que o usuário está vendo;
- consultas business read via OpenAPI;
- criação/edição/aprovação/cancelamento conforme capabilities reais;
- preview/confirmation/idempotency para writes;
- análise e comparação multi-domínio;
- RAG/conhecimento;
- artefatos;
- recomendações contextuais;
- workflows multi-app;
- partial failure/retry/resume;
- autonomia L0–L5 governada;
- onboarding AI-ready;
- observabilidade/admin/coverage;
- rollout, canary, kill switch e auditoria.

A fonte consolidada é [`24-product-specification.md`](./24-product-specification.md); a rastreabilidade está em [`25-requirements-traceability.md`](./25-requirements-traceability.md).

## 7. Integração com a plataforma existente

```text
minha-delpi-ai-api
→ inteligência, planner, Action Catalog, tools, RAG, policies, memory, presentation

plugins/minha-delpi-chat
→ experiência conversacional, activity, confirmation, rendering

portal
→ Router, AuthContext, authorized apps/routes, Workspace Context, CopilotBridge

Core API
→ apps, routes, permissions e governança

api-delpi e demais APIs
→ contratos/use cases de negócio via OpenAPI

MFEs
→ experiência especializada + contexto/deep links/view capabilities
```

Não criar uma IA por departamento. Apps especializam o Copilot central por capabilities, contexto, knowledge e policy.

## 8. Invariantes

```text
1. Copilot permissions ⊆ permissões efetivas do usuário.
2. Nenhuma action bypassa RBAC/policy/confirmation.
3. LLM não inventa URL, endpoint, actionId ou permission.
4. Business Actions usam API/use case quando existe contrato.
5. Platform Actions são tipadas e validadas pelo Portal.
6. Nova API OpenAPI não exige código por endpoint no core genérico.
7. Novo app AI-ready não exige hardcode central.
8. Plano operacional pode ser exibido; chain-of-thought não.
9. Writes/destructive respeitam sensitivity, confirmação, idempotency e audit.
10. Capability Projection não vira catálogo técnico paralelo.
11. Workspace Context não é authority de autorização.
12. Evidência de SHA/config anterior não fecha candidate novo.
```

## 9. Ordem de execução

```text
C0.S0 Rebaseline/inventário
→ C0.S1 contracts/ownership
→ C0.S2 harness
→ C1 Platform Actions
→ C2 Workspace Context
→ C3 Business Parity
→ C4 Workflows
→ C5 AI-ready ecosystem
→ C6 autonomy
→ C7 rollout final
```

**O Cursor deve começar por `C0.S0`, não por UI ou writes.**

## 10. Resultado esperado

Exemplo-alvo:

> “Analise por que estamos atrasando as entregas do item 90264238, compare estoque, produção, compras e carteira de pedidos, mostre as principais causas, abra o Portal de Suprimentos já filtrado nesse item e crie uma solicitação para Compras revisar o caso.”

O Copilot deve decompor objetivos, usar somente capabilities autorizadas, explicar o plano operacional, executar reads, pedir confirmação para alterações sensíveis, verificar outcomes, abrir a interface adequada e preservar contexto relevante.