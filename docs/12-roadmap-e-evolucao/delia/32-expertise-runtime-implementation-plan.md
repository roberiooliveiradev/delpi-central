# Minha DELPI Copilot — Detalhamento do Runtime de Expertise

**Status:** thematic spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)

## 1. Objetivo

Implementar **nativamente na nova Copilot API** a especialização dinâmica do Copilot único.

Não existe migration de agents do Minha DELPI Chat nesta iniciativa.

## 2. Componentes conceituais

Conforme gaps e Abstraction Gate:

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

Nomes finais seguem C0/`49`; não criar todos antecipadamente.

## 3. Layers

### Domain
- Expertise/Playbook value/domain models;
- pure applicability/composition semantics;
- no DB/HTTP/LLM/framework.

### Application
- retrieve/rank packs;
- compose bounded ExpertiseContext;
- resolve playbook applicability;
- combine with evidence/planning;
- project preference without permission elevation.

### Infrastructure
- storage/index adapters;
- embedding/provider adapters;
- import/version adapters;
- telemetry.

### Interfaces
- admin/read DTO/endpoints when C6 requires them.

## 4. Fase canônica

```text
C0
→ Expertise/Playbook contracts, owners, persistence boundaries

C3
→ Catalog/Repository if required
→ retrieval/ranking
→ context composition
→ playbooks
→ Knowledge ACL integration
→ multimodal integration
→ evals/generalization

C6
→ project preferences
→ Expertise Studio/admin/coverage

C7
→ performance/model-routing optimization only if justified
```

## 5. Regras

- one Copilot identity;
- pack/playbook never grants permission;
- no path/method/opId as semantic authority;
- unknown/new pack works without planner patch;
- retrieval uses goals/context/entities/attachments/preferences boundedly;
- project preference improves ranking, not authorization;
- Knowledge source ACL remains authoritative;
- multimodal capability does not depend on agent activation;
- versions/hashes are auditable;
- packs/playbooks are data/configuration of the Copilot product, not user-facing agents.

## 6. No Chat migration

These concepts are explicitly **not inputs** to this runtime:

```text
AgentSpecializationService
ChatWorkspaceAgentActivationService
ChatSoftAgentHandoffService
ChatSkillRegistry
Chat session.agent_id
Chat chat_mode
Chat project default agent
```

They may be observed during C0 only to understand lessons/anti-patterns.

## 7. Tests

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

## 8. Resultado alvo

> “Use Engenharia e Qualidade para analisar este desenho, consulte problemas anteriores e monte um 8D preliminar.”

O mesmo Copilot deve compor os packs/playbooks necessários sem troca de agent e sem depender do Minha DELPI Chat.