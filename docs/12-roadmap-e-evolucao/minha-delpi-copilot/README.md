# Minha DELPI Copilot

> **Status:** proposta arquitetural / documentação-base
>
> **Escopo:** evolução da Minha DELPI para uma plataforma operacional assistida por IA, em que o Copilot pode explicar, analisar, navegar e executar tudo o que o usuário autorizado consegue fazer por meio de capabilities governadas.

## Visão

O **Minha DELPI Copilot** é a camada inteligente transversal da plataforma. Ele não é um chatbot isolado nem uma automação de cliques. Seu objetivo é oferecer uma segunda interface operacional para a Minha DELPI:

```text
usuário
→ conversa com o Copilot
→ Copilot entende objetivos
→ descobre capabilities autorizadas
→ planeja
→ explica o plano
→ executa consultas/navegação/ações
→ observa resultados
→ analisa
→ apresenta
→ continua o fluxo
```

### Princípio central

> Tudo que um usuário autorizado consegue consultar, analisar ou executar na Minha DELPI deve poder ser representado como uma **Capability** que o Copilot também consegue descobrir e utilizar, respeitando exatamente as mesmas permissões, políticas e contratos de negócio.

A UI e o Copilot não devem possuir regras de negócio concorrentes. Sempre que existir API/use case, ambos devem convergir para o mesmo contrato.

```text
UI ───────────────┐
                  ▼
              Use Case
                  ▲
Copilot ──────────┘
```

## Objetivos do produto

- permitir linguagem natural como interface de entrada para a plataforma;
- explicar processos, telas, indicadores, dados e decisões;
- consultar e cruzar dados corporativos;
- navegar por apps, módulos, rotas e entidades;
- preencher contexto de telas e filtros;
- cadastrar, editar, aprovar, cancelar e executar operações permitidas;
- orquestrar workflows envolvendo vários apps/APIs;
- gerar análises, resumos, relatórios e artefatos;
- recomendar próximos passos de forma contextual;
- atuar como copiloto contínuo do usuário dentro do Portal;
- manter segurança, RBAC, confirmação e auditoria fora do arbítrio do LLM.

## Arquitetura conceitual

```text
                         USUÁRIO
                            │
               ┌────────────┴────────────┐
               │                         │
              UI                       COPILOT
               │                         │
               │                 ┌───────▼────────┐
               │                 │ Turn Planner   │
               │                 │ Goals / DAG    │
               │                 └───────┬────────┘
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
           │             POLICIES               │
           │ RBAC / sensitivity / confirmation │
           └────────────────┬───────────────────┘
                            │
                     Generic Execution
                            │
              ┌─────────────┼──────────────┐
              │             │              │
              ▼             ▼              ▼
            APIs           MFEs           Core
           TOTVS          Portal          DELPI
```

## Documentos desta iniciativa

| Documento | Conteúdo |
|---|---|
| [`01-visao-produto.md`](./01-visao-produto.md) | visão do produto, personas, princípios e experiência-alvo |
| [`02-arquitetura.md`](./02-arquitetura.md) | arquitetura técnica e responsabilidades |
| [`03-capability-model.md`](./03-capability-model.md) | modelo de capabilities e catálogos |
| [`04-platform-actions.md`](./04-platform-actions.md) | navegação e ações do Portal/Shell |
| [`05-workspace-context-protocol.md`](./05-workspace-context-protocol.md) | contexto compartilhado entre Portal, MFEs e Copilot |
| [`06-business-action-parity.md`](./06-business-action-parity.md) | paridade UI ↔ Copilot via use cases/OpenAPI |
| [`07-agentic-workflows.md`](./07-agentic-workflows.md) | planejamento composto e workflows multi-app |
| [`08-security-autonomy-audit.md`](./08-security-autonomy-audit.md) | RBAC, níveis de autonomia, confirmação e auditoria |
| [`09-ux-copilot.md`](./09-ux-copilot.md) | UX do Copilot, activity, explicação e integração visual |
| [`10-plugin-ai-ready-standard.md`](./10-plugin-ai-ready-standard.md) | padrão para novos apps nascerem AI-ready |
| [`11-observability-evals.md`](./11-observability-evals.md) | observabilidade, métricas, evals e qualidade |
| [`12-roadmap.md`](./12-roadmap.md) | roadmap incremental de implementação |
| [`13-functional-catalog.md`](./13-functional-catalog.md) | catálogo funcional detalhado do Copilot |
| [`14-definition-of-done.md`](./14-definition-of-done.md) | critérios de conclusão por fase e globais |

## Integração com arquitetura existente

O Copilot deve evoluir sobre componentes já existentes da Minha DELPI:

```text
minha-delpi-ai-api
→ inteligência, planner, actions, RAG, memory, policies, presentation

plugins/minha-delpi-chat
→ experiência conversacional e renderização

portal
→ Router, AuthContext, apps autorizados, Shell, CopilotBridge

Core API
→ identidade de plataforma, apps, rotas, permissões efetivas

api-delpi e demais APIs
→ dados e operações corporativas via contratos OpenAPI
```

Não criar um segundo motor de IA por departamento ou por app. Portais, agentes e apps devem especializar o mesmo Copilot através de contexto, capabilities, knowledge e políticas.

## Invariantes

```text
1. Permissões do Copilot ⊆ permissões efetivas do usuário.
2. Nenhuma action pode bypassar RBAC/policy/confirmation.
3. LLM não inventa URL, actionId, endpoint ou permissão.
4. Business actions usam APIs/use cases; não automação de clique quando existe contrato.
5. Platform actions são tipadas e validadas pelo Portal.
6. Nova API OpenAPI deve ser utilizável sem código por endpoint no core genérico.
7. Novo app deve poder nascer AI-ready sem registrar hardcodes no Copilot central.
8. Planos operacionais são observáveis, mas chain-of-thought não é persistida/exposta.
9. Writes/admin/destructive actions respeitam sensitivity e confirmação.
10. UI e Copilot convergem para a mesma fonte de verdade de negócio.
```

## Resultado esperado

A experiência alvo deve permitir fluxos como:

> “Analise por que estamos atrasando as entregas do item 90264238, compare estoque, produção, compras e carteira de pedidos, mostre as principais causas, abra o Portal de Suprimentos já filtrado nesse item e crie uma solicitação para Compras revisar o caso.”

O Copilot deve decompor isso em objetivos, executar somente capabilities autorizadas, pedir confirmação para alterações sensíveis e manter contexto entre análise, navegação e execução.
