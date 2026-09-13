# Minha DELPI Copilot — Especificação de Expertise Packs

**Status:** thematic spec / contract detail  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Foundation:** schema/owner/version semantics em C0; runtime de retrieval na Copilot API em C3.

## 1. Definição

`Expertise Pack` é pacote versionado de conhecimento operacional/guidance que especializa o **mesmo Copilot** em um domínio. Não é agent, permission ou endpoint catalog.

Responde a quais conceitos/evidências/métodos/playbooks/knowledge scopes/multimodal needs/limitações importam para uma análise.

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

Shape final é congelado/reutilizado em **C0.S3**, depois de C0.S0–S2 provarem platform boundary, names e owners.

## 3. Authority

Fields permitidos incluem identity/version, domains/signals, terminology/guidance, knowledge refs, preferred playbooks, recommended capability semantics, multimodal needs e eval refs.

Proibido como technical authority:

```text
path
method
operationId
provider selector
permission override
JWT/secret
hardcoded department→endpoint
```

Business action authority permanece Domain OpenAPI + Copilot Action Catalog derivado.

## 4. Ativação/composição

```text
goals + Workspace/Entity context + attachments + preferences
→ Copilot Expertise Retriever
→ top-K candidates
→ ACL/policy filter
→ ExpertiseSelection
→ bounded ExpertiseContext
```

Vários packs podem compor o mesmo turno. System/safety/policy vencem; capability recommendation não concede access; knowledge scopes só entram após ACL.

## 5. Ranking

Pode considerar goals, domain signals, workspace/entity, attachments, terminology, capability candidates, structured context e preferences. `agent_id` não existe como requisito do runtime standalone.

## 6. Relações

```text
Expertise = como analisar
Capability = o que pode fazer
Playbook = método
Domain OpenAPI/Copilot Action Catalog = contrato técnico
Policy/RBAC = se pode fazer
```

## 7. Knowledge/Multimodal

Pack sugere scopes/needs, mas Knowledge ACL e tool availability continuam authorities próprias. Multimodal runtime pertence à Copilot API.

## 8. Versioning/observability

Registrar key/version/contentHash/evalHash/owner/status, selected candidates/reason codes, playbooks, knowledge/tools e outcomes, sem CoT.

## 9. Evals

- positive/sibling/negative;
- cross-domain composition;
- unauthorized knowledge/capability;
- malicious pack content;
- attachment-triggered case;
- unknown pack;
- metamorphic key rename;
- version regression;
- full-page/panel parity.

## 10. Lifecycle/admin

Candidate só vira published/active por lifecycle governado do Expertise Studio com schema/owner/refs/evals/security aplicáveis.

## 11. Pilotos

Começar por poucos packs de alto valor, por exemplo Qualidade Industrial, Engenharia de Produto e Suprimentos. Não criar catálogo de departamentos inteiro antes de validar retrieval/generalization.

## 12. Independence

A implementação não importa nem migra `AgentSpecializationService`, agent sessions ou skills do Minha DELPI Chat. Chat pode ser usado apenas como referência de C0.

## 13. Anti-patterns

- um agentId por expertise;
- pack como permission;
- pack como endpoint registry;
- prompt global com todas as expertises;
- seleção manual obrigatória;
- hardcode de pack no planner;
- runtime de Expertise delegado ao Chat.