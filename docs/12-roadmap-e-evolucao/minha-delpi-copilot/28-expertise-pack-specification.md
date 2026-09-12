# Minha DELPI Copilot — Especificação de Expertise Packs

**Status:** thematic spec / contract detail  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Foundation:** schema/owner/version semantics definidos/reutilizados em C0; runtime de retrieval em C2.

## 1. Definição

`Expertise Pack` é um pacote versionado de conhecimento operacional e guidance que especializa o **mesmo Copilot** em um domínio.

Responde a:

- quais conceitos importam?;
- quais evidências devem ser buscadas?;
- quais métodos são adequados?;
- quais playbooks são relevantes?;
- quais knowledge scopes recebem boost?;
- quais necessidades multimodais existem?;
- quais limitações/riscos devem ser explicitados?.

Não define permission nem endpoint.

## 2. Estrutura conceitual

```json
{
  "schemaVersion": 1,
  "key": "quality-industrial",
  "version": "1.0.0",
  "label": "Qualidade Industrial",
  "description": "Especialização para qualidade, não conformidade e causa raiz.",
  "domains": ["quality", "manufacturing"],
  "signals": ["nonconformity", "inspection", "complaint", "8d"],
  "knowledgeScopes": ["global:quality"],
  "preferredPlaybooks": ["quality.8d", "quality.root-cause"],
  "recommendedCapabilities": ["knowledge.search", "analysis.compare", "document.vision"],
  "multimodalNeeds": ["image", "pdf", "technical-drawing"],
  "terminology": {},
  "analysisGuidance": [],
  "outputGuidance": [],
  "evalSuites": ["quality-core-v1"],
  "owner": "quality-owner",
  "status": "active"
}
```

Shape final é congelado/reutilizado em **C0.S2**, após C0.S0/S1 provarem owners/patterns existentes.

## 3. Campos permitidos

- key/version/label/description/owner/status;
- domains/signals/terminology;
- analysis/output guidance;
- knowledge scope refs;
- preferred playbook refs;
- recommended capability semantics;
- multimodal needs;
- eval refs.

## 4. Campos proibidos como authority

```text
path
method
operationId
provider selector
path/opId markers
parameter strategy
permission override
JWT/secret
hardcoded department→endpoint
```

Technical action authority permanece OpenAPI + Action Catalog.

## 5. Ativação

```text
goals + Workspace/Entity context + attachments + project preferences
→ Expertise Retriever
→ top-K candidates
→ compatibility/ACL/policy filter
→ ExpertiseSelection
→ bounded ExpertiseContext
```

Usuário não precisa selecionar pack manualmente.

## 6. Composição

Vários packs podem ser usados no mesmo turno.

Merge rules:

1. system/safety/policy vencem;
2. guidance não reduz safety;
3. knowledge scopes só entram após ACL;
4. terminology pode ser namespaceada;
5. playbooks são candidates;
6. capability recommendation não concede acesso;
7. context final é bounded.

## 7. Ranking

Pode considerar:

- goals/domain signals;
- Workspace app/entity;
- attachments;
- recognized terminology;
- capability candidates;
- recent structured context;
- project preferences.

`agent_id` não é requisito.

## 8. Knowledge

```text
pack knowledge refs
+ user ACL
+ source policy
→ permitted knowledge candidates
```

Pack nunca amplia visibility.

## 9. Capability relation

```text
Expertise = como analisar
Capability = o que pode fazer
Action Catalog = contrato técnico
Policy/RBAC = se pode fazer
```

## 10. Playbooks

Pack pode recomendar refs como:

```text
quality.8d
quality.root-cause
engineering.drawing-review
```

Playbook é objeto versionado separado.

## 11. Multimodalidade

Pack pode indicar necessidade de document/image/drawing perception, mas extraction tool continua capability/internal tool governada.

## 12. Versioning/provenance

Registrar quando material:

```text
key
version
contentHash
evalSuiteHash
owner/status
```

Mudança material invalida evidence de eval correspondente.

## 13. Observability

- candidates;
- selected packs;
- structured reasonCode/score;
- version/hash;
- playbooks;
- knowledge/tool usage;
- outcome/eval.

Sem CoT.

## 14. Evals

- positive;
- semantic sibling;
- unrelated negative;
- cross-domain composition;
- unauthorized knowledge;
- malicious pack content;
- attachment-triggered case;
- unknown pack;
- version regression;
- metamorphic key rename preserving semantics.

## 15. Lifecycle/admin

Candidate só pode ser published/active conforme lifecycle governado do Expertise Studio, com schema/owner/refs/evals/security aplicáveis.

## 16. Pilotos

Começar por poucos packs de alto valor, por exemplo:

- Qualidade Industrial;
- Engenharia de Produto;
- Suprimentos.

Não criar um catálogo de departamentos inteiro antes de validar retrieval/composition/generalization.

## 17. Anti-patterns

- um agentId por expertise;
- pack como permission;
- pack como endpoint registry;
- prompt monolítico global com todas as expertises;
- activation manual obrigatória;
- hardcode do pack no planner.
