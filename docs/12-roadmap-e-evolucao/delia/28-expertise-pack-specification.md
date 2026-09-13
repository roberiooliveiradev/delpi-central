# DÉLIA — Especificação de Expertise Packs

**Status:** `TARGET` — thematic spec / contract detail  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Evidence rule:** schema, storage, catalog e retrieval só deixam de ser target quando C0/C3 provarem owner, contract e implementation.

## 1. Definição

`Expertise Pack` é um contrato conceitual versionado de conhecimento operacional/guidance que pode especializar a **mesma DÉLIA** em um domínio. Não é agent, permission, endpoint catalog, policy authority ou executor.

Responde a quais conceitos, evidências, métodos, playbooks, knowledge scopes, necessidades multimodais e limitações importam para uma análise.

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

O shape é **candidate**, não contrato implementado. C0 deve decidir owner, source canônica, consumers, versioning, persistence e lifecycle antes de qualquer freeze.

## 3. Authority

Fields podem incluir identity/version, domains/signals, terminology/guidance, knowledge refs, preferred playbooks, recommended capability semantics, multimodal needs e eval refs.

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

Business-action authority permanece no Domain API/use case autoritativo. A projeção semântica da DÉLIA nunca substitui RBAC, domain validation ou provider scope.

## 4. Ativação/composição

Target:

```text
goals + Workspace/Entity context + attachments + preferences
→ Expertise retrieval/ranking
→ ACL/policy filtering
→ ExpertiseSelection
→ bounded ExpertiseContext
```

Vários packs podem compor o mesmo turno. System/safety/policy vencem; capability recommendation não concede access; knowledge scopes só entram após ACL.

## 5. Ranking

Pode considerar goals, domain signals, workspace/entity, attachments, terminology, capability candidates, structured context e preferences. `agent_id` não é requisito do runtime standalone.

## 6. Relações

```text
Expertise = como analisar
Capability = o que pode fazer
Playbook = método
Domain API/OpenAPI = contrato técnico/business authority
Policy/Decision = se e como pode agir
```

## 7. Knowledge/Multimodal

Pack apenas referencia/sugere scopes e needs. Knowledge ACL, media policy, provider availability e source authority continuam independentes.

Qualquer multimodal adapter da DÉLIA permanece provider-neutral e sujeito ao Abstraction Gate.

## 8. Versioning/observability

Quando implementado, registrar key/version/contentHash/evalHash/owner/status, selected candidates/reason codes, playbooks, knowledge/tools e outcomes, sem CoT.

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

Mudança de IA não fecha apenas com teste verde: generalization, safety e task outcome devem ser provados no SHA/config avaliado.

## 10. Lifecycle/admin

Candidate só vira published/active por lifecycle governado, com owner/review/eval/version/publish. O nome da surface administrativa não cria um repository ou lifecycle paralelo.

## 11. Pilotos

Pilotos de Qualidade Industrial, Engenharia de Produto e Suprimentos são exemplos de target, não evidência de implementação ou prioridade executiva fora de `16`.

## 12. Independence

A implementação não importa nem migra `AgentSpecializationService`, agent sessions ou skills do Minha DELPI Chat. Chat é reference-only.

## 13. Anti-patterns

- um agentId por expertise;
- pack como permission;
- pack como endpoint registry;
- prompt global com todas as expertises;
- seleção manual obrigatória como única estratégia;
- hardcode de pack no planner;
- repository/registry criado sem Abstraction Gate;
- runtime de Expertise delegado ao Chat.
