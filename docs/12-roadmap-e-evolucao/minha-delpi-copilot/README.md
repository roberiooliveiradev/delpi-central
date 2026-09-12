# Minha DELPI Copilot

> **Status:** **PLANEJAMENTO EXECUTÁVEL / NOT_STARTED**  
> **Próxima etapa:** **C0.S0 — Rebaseline e inventário real**  
> **Plano executável:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
> **Especialização do Copilot:** [`27-single-copilot-specialization-architecture.md`](./27-single-copilot-specialization-architecture.md)  
> **Prompt do Cursor:** [`23-prompt-cursor-execucao.md`](./23-prompt-cursor-execucao.md)  
> **Ledger:** [`evidence/execution-ledger.md`](./evidence/execution-ledger.md)

## 1. Visão

O **Minha DELPI Copilot** é a camada inteligente transversal da plataforma. Não é um chatbot isolado nem automação de cliques. Ele funciona como uma segunda interface operacional da Minha DELPI:

```text
usuário
→ conversa
→ goals/subtasks
→ capabilities autorizadas
→ expertise/playbooks relevantes
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

Esse princípio vale também para apps `iframe`: o iframe pode participar como adapter de navegação/contexto/experiência, mas operações de negócio continuam usando API/use case quando existir contrato.

### Princípio de especialização

> Existe **um único Minha DELPI Copilot**. Engenharia, Qualidade, Suprimentos, Comercial, Financeiro, RH e demais domínios não viram agentes independentes; especializam o mesmo runtime por **Expertise Packs**, **Domain Playbooks**, knowledge scopes, capabilities e ferramentas multimodais.

```text
NÃO
Copilot → trocar para agente Engenharia → trocar para agente Qualidade

SIM
Copilot único
→ entende goals/contexto
→ recupera Engineering + Quality Expertise
→ aplica playbooks necessários
→ usa tools/capabilities autorizadas
→ responde/executa no mesmo contexto
```

## 2. Arquitetura alvo

```text
                         USUÁRIO
                            │
               ┌────────────┴────────────┐
               │                         │
              UI                       COPILOT ÚNICO
               │                         │
               │                 Goals / Planner
               │                         │
               │           ┌─────────────┼───────────────┐
               │           │             │               │
               │           ▼             ▼               ▼
               │      Capability      Expertise        Playbooks
               │       Retrieval      Retrieval         Retrieval
               │           │             │               │
               │           └──────┬──────┴───────┬───────┘
               │                  │              │
               │                  ▼              ▼
               │             Knowledge      Multimodal
               │             RAG/Search       Tools
               │                  │              │
               │           ┌──────┴──────────────┘
               │           ▼
               │       Structured Plan
               │           │
               │           ├─ Business Actions → OpenAPI
               │           └─ Platform Actions → Portal Bridge
               ▼           ▼
           ┌────────────────────────────────────┐
           │ RBAC / policy / sensitivity /     │
           │ confirmation / audit / budgets    │
           └────────────────┬───────────────────┘
                            │
                     Generic Execution
                            │
              ┌─────────────┼──────────────┐
              ▼             ▼              ▼
            APIs           MFEs       iframe apps
```

## 3. Fonte de verdade por capability e especialização

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

Sem app→URL hardcoded no Copilot.

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

Playbooks não contêm endpoint técnico como authority.

### Workspace Context

```text
MFE ou iframe integrado
→ WorkspaceContext tipado
→ Portal Context Store
→ bounded turn context
→ Copilot
```

Contexto não é permissão.

### Apps iframe

```text
PORTAL_ONLY
→ Copilot abre app/rota

CONTEXTUAL
→ + iframe publica contexto via bridge tipado

INTERACTIVE
→ + recebe comandos visuais genéricos

AI_READY
→ + Business Actions reais via API/OpenAPI
```

A especificação canônica está em [`26-iframe-copilot-bridge.md`](./26-iframe-copilot-bridge.md).

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

A migração de agentes para expertise também **não autoriza runtime diff antes de C0.S0**. A arquitetura e o plano já estão definidos, mas primeiro o Cursor deve inventariar consumers, persistência, UI e compatibilidade real.

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
| [`27-single-copilot-specialization-architecture.md`](./27-single-copilot-specialization-architecture.md) | **Copilot único + especialização componível** |
| [`28-expertise-pack-specification.md`](./28-expertise-pack-specification.md) | **contrato de Expertise Packs** |
| [`29-domain-playbooks-specification.md`](./29-domain-playbooks-specification.md) | **contrato de Domain Playbooks** |
| [`30-multimodal-expertise-and-drawing-analysis.md`](./30-multimodal-expertise-and-drawing-analysis.md) | **multimodalidade/document vision/desenhos** |
| [`33-reference-expertise-packs-quality-engineering.md`](./33-reference-expertise-packs-quality-engineering.md) | **packs/playbooks de referência de Qualidade e Engenharia** |

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
| [`26-iframe-copilot-bridge.md`](./26-iframe-copilot-bridge.md) | protocolo Portal ↔ iframe |
| [`31-agent-to-expertise-migration-plan.md`](./31-agent-to-expertise-migration-plan.md) | **migração de agents para expertise** |
| [`32-expertise-runtime-implementation-plan.md`](./32-expertise-runtime-implementation-plan.md) | **plano executável do runtime de expertise** |
| [`evidence/execution-ledger.md`](./evidence/execution-ledger.md) | estado executável/evidências |

## 6. Funcionalidades alvo

O produto completo contempla:

- chat global e contextual;
- uma única identidade de Copilot, sem troca obrigatória de agente por departamento;
- especialização dinâmica por Expertise Packs;
- Domain Playbooks para métodos como 8D, causa raiz e análise de desenho;
- composição cross-domain no mesmo turno;
- document vision e análise multimodal como capacidades do mesmo runtime;
- abertura de apps/rotas/entidades;
- filtros/view context tipados;
- entendimento do que o usuário está vendo;
- integração gradual com apps iframe (`PORTAL_ONLY`, `CONTEXTUAL`, `INTERACTIVE`, `AI_READY`);
- contexto de iframe normalizado no mesmo `WorkspaceContext` usado pelos MFEs;
- comandos visuais tipados para iframes integráveis, sem DOM automation;
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
→ inteligência, planner, Action Catalog, expertise/playbook retrieval, tools, RAG, policies, memory, presentation

plugins/minha-delpi-chat
→ experiência conversacional, activity, confirmation, rendering

portal
→ Router, AuthContext, authorized apps/routes, Workspace Context, CopilotBridge, IframeBridge

Core API
→ apps, routes, permissions e governança

api-delpi e demais APIs
→ contratos/use cases de negócio via OpenAPI

MFEs
→ experiência especializada + contexto/deep links/view capabilities

iframes
→ abertura pelo Portal + contexto/comandos visuais tipados quando houver bridge compatível
```

Não criar uma IA por departamento. Domínios especializam o Copilot central por expertise, playbooks, capabilities, contexto, knowledge e policy.

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
13. Iframe não transmite JWT/refresh token pelo bridge.
14. Iframe não usa DOM automation como substituto de API.
15. postMessage é validado por origin + source + schema + sessão/protocolo.
16. Existe um único Copilot de produto; departamento não cria novo agente/runtime.
17. Expertise Pack não concede permission e não substitui OpenAPI/Action Catalog.
18. Domain Playbook não contém endpoint técnico como authority.
19. Tools multimodais podem ser usadas sem seleção de agente quando policy/capability permitirem.
20. Novo Expertise Pack compatível não exige patch no planner central.
```

## 9. Ordem de execução

```text
C0.S0 Rebaseline/inventário
  + inventário obrigatório de agents/skills/specialization/handoff
→ C0.S1 contracts/ownership incluindo ExpertisePack/Playbook quando necessário
→ C0.S2 harness
→ C1 Platform Actions + PORTAL_ONLY/handshake base
→ C2 Workspace Context + expertise context foundation
→ C3 Business Parity + decoupling de operational tools do agent activation após gates
→ C4 Workflows + playbooks cross-domain
→ C5 AI-ready ecosystem + admin/SDK/templates
→ C6 autonomy
→ C7 rollout final + remoção de legacy agent-routing
```

**O Cursor deve começar por `C0.S0`, não por UI, writes ou remoção direta de agents.**

## 10. Resultado esperado

Exemplo-alvo:

> “Analise o desenho 90264238, verifique os principais riscos de qualidade, consulte se já tivemos problemas semelhantes, compare fornecedores e monte um 8D preliminar. Depois abra o Portal de Suprimentos filtrado nesse item.”

O Copilot deve combinar Engenharia + Qualidade + Suprimentos no mesmo runtime, usar somente capabilities autorizadas, aplicar conhecimento/playbooks relevantes, analisar anexos quando necessário, explicar o plano operacional, pedir confirmação para alterações sensíveis, verificar outcomes e preservar contexto — sem exigir que o usuário escolha ou troque de agente.