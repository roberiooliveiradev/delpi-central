# Minha DELPI Copilot

> **Status:** `PLANNED / NOT_STARTED`  
> **Decisão de produto:** **aplicação nova e standalone**  
> **Próxima etapa:** **C0.S0 — Platform/Rebaseline inventory**  
> **Ordem executável:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
> **Boundary standalone:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
> **Baseline da plataforma:** [`51-platform-integration-baseline.md`](./51-platform-integration-baseline.md)  
> **Estrutura/Bootstrap:** [`52-standalone-repository-and-bootstrap-plan.md`](./52-standalone-repository-and-bootstrap-plan.md)  
> **Arquitetura/design patterns:** [`49-architecture-and-design-patterns-standard.md`](./49-architecture-and-design-patterns-standard.md)  
> **Prompt do Cursor:** [`23-prompt-cursor-execucao.md`](./23-prompt-cursor-execucao.md)  
> **Ledger:** [`evidence/execution-ledger.md`](./evidence/execution-ledger.md)

## 1. Decisão fundamental

O **Minha DELPI Copilot não é uma expansão do Minha DELPI Chat**.

```text
Minha DELPI Chat                 Minha DELPI Copilot
-----------------------------    ------------------------------
plugins/minha-delpi-chat         novo MFE próprio
minha-delpi-ai-api               nova API própria
runtime/persistência do Chat     runtime/persistência próprios
release do Chat                  release próprio

                 SEM DEPENDÊNCIA DE RUNTIME
```

O Copilot será construído **do zero até 100%**, preservando apenas as fundações corporativas da Minha DELPI: Portal, Core API, Keycloak, Gateway, Manifest, Module Federation, `plugin-ui` e APIs de domínio.

O código do Chat pode ser consultado como referência técnica durante inventário, mas não pode virar dependency, base class, proxy, database authority ou migration path do Copilot.

## 2. North Star

> **Minha DELPI Copilot é a camada inteligente operacional da empresa, implementada como aplicação independente e integrada à plataforma Minha DELPI.**

```text
PERGUNTAR  → entender, pesquisar, explicar, analisar
FAZER      → navegar, consultar, criar, alterar, aprovar, executar
ACOMPANHAR → monitorar, detectar, alertar, reagir
TRABALHAR  → investigar, colaborar, planejar, acompanhar, concluir
```

## 3. Owners alvo

```text
minha-delpi-copilot-api/          → backend/runtime inteligente independente
plugins/minha-delpi-copilot/      → MFE React/Vite independente
portal/                           → Shell/host/navegação/contexto global
core-api/                         → apps/rotas/RBAC/governança
keycloak                          → identidade/SSO
gateway/                          → entrada/routing
plugins/plugin-ui/                → design system compartilhado
APIs de domínio                   → dados e regras de negócio
infra/                            → compose/deploy/env/network
```

Nomes finais são congelados em C0; a arquitetura física recomendada está em `52`.

## 4. Arquitetura resumida

```text
Usuário
  ↓
Portal Shell
  ↓
Minha DELPI Copilot MFE (federated)
  ↓
Gateway
  ↓
Minha DELPI Copilot API
  ├─ Core API / RBAC / apps/routes
  ├─ Domain APIs / OpenAPI
  ├─ Knowledge / Multimodal / Models
  └─ Copilot-owned persistence
```

O Portal **hospeda** o Copilot; não implementa sua inteligência.

A Copilot API **orquestra**; não assume ownership das regras de negócio das outras APIs.

## 5. Integração com o Portal

O Portal atual já suporta MFEs `federated` via `AppHost`, que resolve `remoteEntry`, carrega `mount()` e injeta `getAccessToken`, `basePath`, pathname, rotas e contexto do usuário.

O Copilot terá:

1. **app/full page** registrado por manifesto e acessível pelo launcher/menu;
2. **surface global** no Shell, como painel/botão, montando o mesmo MFE por contrato, sem duplicar frontend/runtime.

Workspace Context e Platform Commands atravessam um bridge tipado; autorização continua em Core/domain owners.

## 6. Princípios não negociáveis

1. **Copilot API própria**; nenhum endpoint do Chat é requisito de funcionamento.
2. **Copilot MFE próprio**; nenhum source import de `plugins/minha-delpi-chat`.
3. **Persistência/migrations próprias**; nenhuma tabela do Chat é authority do Copilot.
4. Core/RBAC continua authority de permissões.
5. Domain APIs continuam authority de dados/regras de negócio.
6. Business Actions são OpenAPI-first desde a fundação do Copilot.
7. Portal continua authority de navegação/hosting.
8. `plugin-ui` é o design system compartilhado do MFE.
9. Um único Copilot de produto; Expertise/Playbooks especializam o runtime sem agentes departamentais.
10. Entity/Evidence/Decision/Workflow/Event usam foundations compartilhadas internas ao Copilot.
11. Business Graph conecta referências e não replica bancos de domínio.
12. Durable Work reutiliza executors canônicos.
13. Chain-of-thought não é persistida/exposta.
14. Clean Architecture + Ports & Adapters + DDD pragmático conforme `49`.

## 7. Nova ordem foundation-first

```text
C0 — Platform + Architecture Foundation Freeze
→ C1 — Standalone App Bootstrap + Portal/Core/Gateway/SSO
→ C2 — Workspace Context + Platform Commands
→ C3 — Intelligence Core + Expertise/Knowledge/Multimodal/Evidence
→ C4 — Business Reads + Business Graph
→ C5 — Governed Writes + Durable Work Foundation
→ C6 — Tasks/Cases/Rooms/Inbox/Watch/Ecosystem/Learning
→ C7 — Autonomy/Simulation/Model Routing/Rollout
```

A mudança é deliberada: **primeiro provamos que a nova aplicação existe e integra corretamente com a plataforma; só depois construímos inteligência**.

## 8. C0 — o que precisa congelar

```text
platform inventory
standalone boundaries
repo/service names
Gateway/Compose/Manifest contracts
Core/RBAC integration
MFE hosting contract
shared primitives
architecture/patterns
ports/persistence boundaries
error/event/state/resilience rules
contract/conformance harness
```

C1 só inicia com `FOUNDATION_FREEZE=PASS`.

## 9. Business Actions não dependem do Chat

A antiga dependência do roadmap `llm-json-decoupling` do Minha DELPI Chat deixa de ser bloqueadora para o Copilot.

O Copilot implementará sua própria cadeia desde o início:

```text
OpenAPI
→ Copilot Action Catalog/index
→ allowed capabilities
→ retrieval/planner
→ schema/argument validation
→ RBAC/policy/Decision Gate
→ generic executor
→ Domain API
→ Outcome/Evidence
```

Código genérico existente só pode ser reutilizado se C0 provar que já é componente compartilhado neutro ou se for extraído para owner compartilhado independente.

## 10. Documentos canônicos

| Documento | Papel |
|---|---|
| `16` | única ordem de implementação |
| `17` | owners/primitives/contracts |
| `20` | testes/gates |
| `21` | state/persistence |
| `23` | prompt mestre Cursor |
| `25` | requisitos CP-* |
| `49` | architecture/design patterns |
| `50` | boundary standalone |
| `51` | baseline factual Portal/Core/APIs/MFEs |
| `52` | estrutura física/bootstrap |
| ledger | estado/evidence executável |

Specs temáticas `03–44` detalham comportamento, mas não podem contradizer `16/50/51/52`.

## 11. Relação com documentos antigos de migração de agents

Qualquer trecho que trate o Copilot como migração de `AgentSpecializationService`, `userActivatedAgent`, `softAgentHandoff`, `agent_id` ou sessions do Chat está **SUPERSEDED / OUT_OF_SCOPE**.

O Copilot novo simplesmente não nasce com essas dependências.

## 12. Primeiro passo

Abrir `23-prompt-cursor-execucao.md` e executar **somente C0.S0**.

C0.S0 é inventário e evidence. Não cria ainda planner, RAG, Graph, Case, Watch ou Model Router.

O primeiro runtime após Foundation Freeze será o **bootstrap standalone**: API + MFE + auth + Core + Gateway + Compose + Manifest + Portal federated mount.