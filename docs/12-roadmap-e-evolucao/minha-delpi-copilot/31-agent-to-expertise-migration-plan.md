# Minha DELPI Copilot — Migração de Agents para Expertise

**Status:** thematic migration spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)

## 1. Direção

```text
ANTES
agent identity
+ specialization
+ agent-bound skills/tools
+ soft handoff

DEPOIS
single Copilot identity
+ Expertise Packs
+ Domain Playbooks
+ authorized capabilities
+ Project Context/preferences
+ dynamic knowledge/multimodal tools
```

## 2. Regra de execução

Este documento **não define fases próprias de implantação**. O cutover segue C0–C7:

```text
C0 inventory/contracts
→ C2 expertise runtime/shadow
→ C4 action availability + handoff cutover
→ C6 projects/admin/preferences
→ C7 legacy cleanup
```

## 3. Classificação obrigatória em C0.S0

Cada responsabilidade atual deve ser classificada por função:

```text
IDENTITY/PERSONA
KNOWLEDGE
EXPERTISE
CAPABILITY
POLICY
PROJECT_CONTEXT
LEGACY_UX
LEGACY_TECHNICAL_COUPLING
```

E por destino:

```text
KEEP
MIGRATE_TO_EXPERTISE
MIGRATE_TO_PROJECT_CONTEXT
MIGRATE_TO_CAPABILITY_POLICY
DEPRECATE
REMOVE
NOT_PROVEN
```

## 4. Inventário obrigatório

Mapear:

- agent entities/tables/repos;
- CRUD/admin;
- metadata/instructions;
- specialization;
- skills;
- allowed actions/tools;
- session/workspace `agent_id`;
- `chat_mode`;
- project default agent;
- UI selector/activation;
- soft handoff;
- knowledge namespaces;
- prompts/policies;
- tests/fixtures/scripts/docs;
- telemetry/consumers externos.

## 5. Mapeamento conhecido a revalidar

### `AgentSpecializationService`

Alvo conceitual:

```text
knowledge config → Expertise/Knowledge metadata
analysis guidelines → Expertise guidance
allowedTools → capability/policy authority, não department agent
```

### `ChatWorkspaceAgentActivationService`

Alvo:

```text
operational capability availability
→ identity/RBAC + allowed actions + policy
```

`agent_id` não permanece gate de operação no target.

### `ChatSoftAgentHandoffService`

Alvo:

```text
capability/expertise miss
→ retrieve/replan
→ clarify if required
→ unavailable explanation
```

Sem troca de identidade.

### `ChatSkillRegistry`

Preservar capabilities úteis, mas separar:

```text
capability availability
≠ agent active
```

Remover semantic routing técnico incompatível com OpenAPI-first quando encontrado.

## 6. C0 — contracts/migration design

Sem runtime cutover.

Saídas:

- producer/consumer graph;
- migration classification;
- public API consumers;
- data migration needs;
- legacy session strategy;
- rollback/exit criteria;
- Expertise/Project/Capability boundaries.

## 7. C2 — expertise runtime + shadow validation

Implementar/reutilizar:

- Expertise Catalog;
- semantic retrieval;
- bounded ExpertiseContext;
- Playbook retrieval;
- multimodal integration;
- session without mandatory agent.

Shadow comparison pode usar legacy output para evaluation, mas não como fallback permanente.

## 8. C4 — operational cutover

Somente após capability/RBAC/policy gates:

- operational tools deixam de exigir agent activation;
- soft handoff sai do fluxo alvo;
- misses usam retrieval/replan/clarify;
- writes continuam governados por Decision Gate;
- legacy sessions continuam legíveis durante janela definida.

## 9. C6 — projects/admin/preferences

Separar projeto de identidade do Copilot.

Projeto pode conter:

- files;
- Knowledge scope refs sujeitos a ACL;
- preferred expertise;
- templates;
- domain guidance;
- app/context preferences.

Projeto não concede permission nem novo planner.

Administração de Expertise/Playbooks segue lifecycle governado.

## 10. C7 — cleanup

Remover/deprecar somente após zero consumers materiais e gates:

- `agent_id` routing;
- `chat_mode=agent` behavior material;
- soft handoff;
- agent-required tool gates;
- dead selectors/config;
- compatibility adapters;
- obsolete tests/docs.

## 11. Persistência

Durante migração, sessões antigas devem continuar legíveis.

Target pode persistir refs como:

```text
selectedExpertiseRefs quando útil
projectId
knowledge refs
workflow/task/case refs
workspace snapshot bounded
```

Expertise selecionada não vira authority eterna; novo turno pode reavaliar.

## 12. Data migration

Não migrar blindly todo conteúdo de agent.

Cada campo precisa owner/destino:

```text
knowledge config → Knowledge/Expertise
specialization → Expertise
skill preference → Project/runtime preference somente se não for security authority
instructions → reviewed Project/Expertise guidance
permission override → NÃO migrar como expertise
```

## 13. API compatibility

Endpoints administrativos atuais precisam consumer inventory.

Estratégia possível:

```text
compatibility read
→ expertise/playbook endpoints
→ consumer migration
→ deprecation window
→ zero-consumer proof
→ remove
```

## 14. Rollback

Durante cutover:

- feature flag/cohort quando padrão local suportar;
- legacy data permanece legível;
- rollback não pode reintroduzir unauthorized tool exposure;
- fallback possui exit criteria e prazo.

## 15. Gates

Antes do cutover final:

```text
session_without_agent PASS
expertise retrieval/composition PASS
unknown pack PASS
knowledge ACL PASS
unauthorized capability PASS
multimodal no-agent PASS quando no escopo
soft handoff replacement PASS
legacy consumer inventory complete
send/stream parity PASS
residual scan PASS
```

## 16. Residual scan

Buscar:

```text
has_agent
userActivatedAgent
chat_mode == agent
switch_agent_and_resend
softAgentHandoff
agent allowed tools
agentId routing
```

Cada residual final:

```text
VALID_NON_ROUTING_CONCEPT
LEGACY_COMPAT_WITH_EXIT_CRITERIA
REMOVE
```

Residual material sem exit criteria bloqueia C7.

## 17. Resultado alvo

> “Analise este desenho com Engenharia e Qualidade, procure problemas semelhantes e monte um 8D preliminar.”

O mesmo Copilot compõe expertise/tools/capabilities sem troca de identidade ou perda de RBAC.