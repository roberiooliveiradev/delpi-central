# Minha DELPI Copilot — Plano de Implementação do Runtime de Expertise

**Status:** plano executável complementar ao C0–C7  
**Regra:** este plano não autoriza pular C0.S0. Runtime diff só começa após inventário, ownership e contracts estarem provados.

## 1. Objetivo

Implementar especialização dinâmica no mesmo Copilot, reaproveitando runtime existente e removendo acoplamentos desnecessários ao modelo de agente ativo.

## 2. Componentes alvo

Conceitualmente:

```text
ExpertiseCatalogPort
ExpertiseRepository
ExpertiseRetriever
ExpertisePolicyFilter
ExpertiseContextComposer
DomainPlaybookCatalogPort
DomainPlaybookRepository
DomainPlaybookRetriever
PlaybookPlannerAdapter
MultimodalEvidenceAdapter
ExpertiseTelemetry
```

Nomes finais devem respeitar os padrões reais encontrados em C0.S0.

## 3. Clean Architecture

### Domain

Pode conter:

- `ExpertisePack` value/model;
- `DomainPlaybook` model;
- pure composition rules;
- compatibility/selection policy interfaces;
- validation rules sem IO.

Não pode:

- ler arquivo;
- acessar banco;
- chamar LLM;
- executar HTTP;
- consultar vector store.

### Application

Pode conter:

- retrieve expertise;
- compose expertise context;
- resolve playbook applicability;
- orchestrate multimodal evidence + planning;
- migration adapter use cases.

### Infrastructure

- DB/repository;
- index/vector retrieval;
- file/bootstrap import;
- LLM/embedding adapter quando necessário;
- telemetry persistence.

### Interfaces

- admin/read endpoints;
- schemas DTO;
- migration/admin commands.

### Composition

- wiring/DI;
- feature flags temporárias com exit criteria.

## 4. Sequência de implementação

### E0 — Inventory and ownership

Integrar ao `C0.S0`.

Inventariar symbols e consumers de:

```text
AgentSpecializationService
ChatWorkspaceAgentActivationService
ChatSoftAgentHandoffService
ChatSkillRegistry
agent repositories/entities/controllers
session.agent_id
chat_mode
project default agent
knowledge filters por agent
agent admin UI
agent-related tests
```

Saída: migration matrix com evidence.

### E1 — Contracts and failing tests

Depois de C0.S0 e dentro do freeze de contratos:

Definir/reutilizar:

```text
ExpertisePackV1
ExpertiseSelectionV1
ExpertiseContextV1
DomainPlaybookV1
MultimodalEvidenceRefV1
```

Criar testes RED para:

- pack inválido;
- endpoint técnico proibido no pack;
- pack não concede permission;
- composição de 2 packs;
- unrelated query não ativa pack;
- project preference não força pack quando irrelevante;
- unauthorized knowledge scope removido.

### E2 — Catalog and repository

Implementar authority canônica persistente/indexável.

Preferência:

```text
DB catalog + repository port
→ optional bootstrap/import content
→ semantic index materializado
```

Não manter JSON e DB como authorities concorrentes permanentes.

Requisitos:

- version;
- owner;
- status;
- content hash;
- created/updated audit;
- deprecation.

### E3 — Expertise retrieval

Implementar retrieval top-K com inputs estruturados.

```text
goals
workspace context
entities
attachment metadata
project preferences
candidate capability semantics
→ expertise candidates
```

Saída estruturada com score/reasonCode/version.

Testes:

- positive;
- sibling;
- negative;
- cross-domain;
- unknown pack indexed by contract;
- metamorphic rename do `key` sem alterar semântica do conteúdo.

### E4 — Runtime composition

Adicionar `ExpertiseContextComposer` ao pipeline do turno.

Ordem alvo:

```text
understanding
→ capability retrieval
→ expertise/playbook retrieval
→ context composition
→ planner
```

O composer deve carregar apenas conteúdo necessário e respeitar budget.

Não despejar catálogo completo no prompt.

### E5 — Decouple operational tools from agent activation

Após testes de capability/policy estarem verdes:

Alterar owner canônico do gate operacional.

Objetivo:

```text
OLD: userActivatedAgent && actionsEnabled
NEW: runtime capability enabled + allowed actions + policy + user context
```

Antes do cutover:

- mapear todos consumers;
- provar negative unauthorized;
- provar send/stream;
- provar sessão sem agent_id;
- provar sessão legada.

### E6 — Replace soft handoff

Remover comportamento "trocar para agente".

Novo comportamento:

```text
retrieval miss
→ second-pass capability/expertise retrieval quando justificado
→ clarify missing requirement
→ safe unavailable answer
```

A UI pode exibir expertise aplicada, não identidade trocada.

### E7 — Migrate specialization presets

Converter presets úteis de `AgentSpecializationService` em packs/bootstrap data revisados.

Exemplo:

```text
rh → hr
financeiro → finance
comercial → commercial
ti → it-support
juridico → legal-compliance
```

Não migrar `allowedTools` como authority.

### E8 — Skills runtime cleanup

Revisar `ChatSkillRegistry`.

Objetivos:

- `has_agent` deixa de ser condição central para skill/capability útil;
- disponibilidade deriva de feature + capability + policy + runtime;
- path-token/operation markers semanticamente frágeis são removidos conforme arquitetura OpenAPI-first;
- skills multimodais permanecem reutilizáveis pelo Copilot único.

### E9 — Domain Playbooks

Implementar catálogo/retrieval e adapter para planner.

Primeiros pilotos recomendados:

```text
quality.root-cause
quality.8d
engineering.drawing-review
operations.delivery-delay-analysis
```

Não iniciar com dezenas de playbooks.

### E10 — Multimodal integration

Integrar output estruturado de document vision/drawing analysis como evidence refs do turno.

Provar:

```text
attachment
→ evidence
→ expertise retrieval
→ playbook
→ optional Business Actions
→ grounded synthesis
```

### E11 — Projects/preferences

Separar customização de projeto de agent identity.

Projeto pode persistir:

- preferred expertise;
- knowledge sources;
- artifact templates;
- guidance;
- files.

Não pode conceder permission.

### E12 — Admin and observability

Adicionar visão administrativa para:

- packs;
- versions;
- owners;
- playbooks;
- usage;
- selection precision;
- eval status;
- deprecations;
- migration progress.

### E13 — Legacy deprecation

Somente após telemetry/evals:

- deprecar agent selection no Copilot;
- parar novas gravações dependentes de agent_id;
- migrar consumers;
- remover handoff;
- remover fallback material;
- manter somente conceitos de projeto/persona se possuírem finalidade própria e claramente separada.

## 5. Integração com C0–C7

| Expertise step | Fase Copilot |
|---|---|
| E0 | C0.S0 |
| E1 | C0.S1–S2 |
| E2–E4 | C2 foundation / C3 scaffolding |
| E5–E8 | C3, após gates AI aplicáveis |
| E9–E10 | C3/C4 |
| E11 | C2/C5 |
| E12 | C5/C7 |
| E13 | C7 após migration gates |

## 6. Gates obrigatórios

Antes de liberar cutover sem agent selection:

```text
EXPERTISE_CONTRACT = PASS
EXPERTISE_RETRIEVAL = PASS
CROSS_DOMAIN_COMPOSITION = PASS
UNAUTHORIZED_CAPABILITY = PASS
UNAUTHORIZED_KNOWLEDGE = PASS
SESSION_WITHOUT_AGENT = PASS
LEGACY_SESSION_COMPATIBILITY = PASS
SOFT_HANDOFF_REMOVAL = PASS
MULTIMODAL_EXPERTISE = PASS quando no escopo
SEND_STREAM_PARITY = PASS
R1_R11_APPLICABLE = PASS
RESIDUAL_AGENT_ROUTING = PASS
COMPLETE_GATE = PASS
```

## 7. Residual search

Buscar após cutover:

```text
has_agent
userActivatedAgent
chat_mode == "agent"
switch_agent_and_resend
softAgentHandoff
agent specialization
agent allowed tools
agent required tools
agentId routing
```

Cada ocorrência deve ser classificada como:

```text
LEGACY_COMPAT_WITH_EXIT_CRITERIA
VALID_NON_ROUTING_CONCEPT
REMOVE
```

## 8. Rollout

```text
shadow expertise selection
→ compare with current behavior
→ internal canary without agent selection
→ selected users/projects
→ default single-Copilot mode
→ deprecate old selector
→ remove legacy runtime dependency
```

Shadow não pode virar fallback permanente.

## 9. Relatório por subetapa

Usar o protocolo canônico do Copilot e registrar adicionalmente:

```text
EXPERTISE_PACKS_TOUCHED:
PLAYBOOKS_TOUCHED:
LEGACY_AGENT_CONSUMERS_FOUND:
MIGRATION_CLASSIFICATION:
EXPERTISE_SELECTION_EVIDENCE:
PACK_VERSION_HASH:
RESIDUAL_AGENT_ROUTING:
```

## 10. Resultado final

O runtime completo deve suportar:

> "Use o conhecimento de Engenharia e Qualidade para analisar este desenho; consulte também reclamações anteriores do item e monte um 8D preliminar."

sem seleção de agente, sem perda de RBAC e sem duplicar a arquitetura de tools/actions.