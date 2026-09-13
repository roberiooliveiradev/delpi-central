# DÉLIA — Detalhamento do Runtime de Expertise

**Status:** `PLANNED / TARGET` — thematic implementation detail  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)

## 1. Objetivo

Detalhar como a DÉLIA pode implementar especialização dinâmica sem migrar agents do Minha DELPI Chat e sem criar abstrações antecipadas.

Este documento não prova que catalog, repository, retriever, embeddings ou storage existam.

## 2. Componentes conceituais

Somente após owner/source/consumer/contract e Abstraction Gate:

```text
Expertise catalog/retrieval capability
Playbook catalog/retrieval capability
bounded ExpertiseContext composition
storage/index adapters when needed
telemetry/evals
```

Os nomes abaixo são apenas exemplos e não devem ser criados por default:

```text
ExpertiseCatalogPort?
ExpertiseRepository?
ExpertiseRetriever?
DomainPlaybookCatalogPort?
DomainPlaybookRepository?
```

Uma coleção/config simples pode ser suficiente. “Pode ser útil depois” não justifica interface/repository/registry.

## 3. Layers

### Domain
- value/semantic models somente se ownership/lifecycle real justificar;
- pure applicability/composition semantics;
- no DB/HTTP/LLM/framework.

### Application
- retrieve/rank packs quando capability existir;
- compose bounded context;
- resolve playbook applicability;
- combine with Evidence/planning;
- project preference without permission elevation.

### Infrastructure
- concrete storage/index/model/provider adapters;
- credentials e provider SDKs somente aqui;
- telemetry.

### Interfaces
- admin/read DTO/endpoints somente quando product consumer real exigir.

## 4. Fase canônica

```text
C0
→ owner/source/consumers/contracts/persistence decisions

C3
→ minimal expertise/playbook runtime only when unlocked
→ retrieval/ranking/context composition
→ Knowledge ACL + multimodal integration as applicable
→ evals/generalization

C6
→ governance/admin/product preferences when prioritized

C7
→ performance/model-routing optimization only if metrics justify
```

## 5. Regras

- one DÉLIA product identity;
- pack/playbook never grants permission;
- no path/method/opId as semantic authority;
- unknown/new pack should not require planner-core patch;
- project/user preference improves ranking, not authorization;
- Knowledge/source ACL remains authoritative;
- multimodal capability does not depend on agent activation;
- versions/hashes are auditable when implemented;
- pack/playbook content is untrusted input to policy/system boundaries;
- no technical executor inside Expertise runtime.

## 6. No Chat migration

Explicitly not runtime dependencies:

```text
AgentSpecializationService
ChatWorkspaceAgentActivationService
ChatSoftAgentHandoffService
ChatSkillRegistry
Chat session.agent_id
Chat chat_mode
Chat project default agent
```

Podem ser observados em C0 apenas como inventory/reference.

## 7. Tests

Quando implementado:

```text
positive domain selection
sibling domain
negative unrelated
cross-domain composition
unknown pack
metamorphic pack rename
unauthorized capability
unauthorized knowledge
project preference conflict
malicious pack content
multimodal-triggered expertise
version regression
full-page/panel parity
```

PASS requer runtime/evidence do SHA/config avaliado.

## 8. Resultado alvo

> “Use Engenharia e Qualidade para analisar este desenho, consulte problemas anteriores e monte um 8D preliminar.”

A DÉLIA deve poder compor os métodos/capabilities necessários sem troca de agent, sem permission elevation e sem depender do Minha DELPI Chat.
