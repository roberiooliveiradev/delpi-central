# Minha DELPI Copilot — Plano de Migração de Agentes para Expertise

**Status:** plano arquitetural de migração  
**Objetivo:** remover a dependência estrutural de agentes selecionáveis no Copilot sem perder conhecimento, skills, projetos ou capacidades já existentes.

## 1. Direção

```text
ANTES
agent identity
+ agent specialization
+ agent-bound skills/tools
+ soft handoff

DEPOIS
single Copilot identity
+ expertise packs
+ domain playbooks
+ authorized capabilities
+ project preferences/context
+ dynamic knowledge/multimodal tools
```

## 2. Princípio de migração

Não apagar recursos úteis porque foram implementados sob o nome "agent".

Cada responsabilidade existente deve ser classificada:

```text
IDENTITY/PERSONA
KNOWLEDGE
EXPERTISE
CAPABILITY
POLICY
PROJECT CONTEXT
LEGACY UX
LEGACY TECHNICAL COUPLING
```

Somente depois decidir KEEP / MIGRATE / DEPRECATE / REMOVE.

## 3. Inventário obrigatório no C0.S0

Mapear ao menos:

- entidades/tabelas de agents;
- agent CRUD/admin;
- agent metadata;
- agent specialization;
- agent skills;
- allowed actions por agent;
- workspace/session `agent_id`;
- `chat_mode` common/agent;
- project default agent;
- UI de seleção/ativação;
- soft handoff;
- knowledge namespaces vinculados;
- prompts/policies por agent;
- tests/fixtures/scripts/docs;
- telemetry de uso.

## 4. Mapeamento inicial conhecido

### `AgentSpecializationService`

Atual:

- presets RH/TI/Financeiro/Comercial/Jurídico;
- knowledge domains/namespaces/tags;
- guideline categories;
- allowed tools.

Alvo:

```text
knowledge fields
→ ExpertisePack.knowledgeScopes / semantic metadata

guideline fields
→ ExpertisePack.analysisGuidance / safety/output guidance

allowedTools
→ remover como authority departamental
→ disponibilidade vem de capability/policy/RBAC
```

### `ChatWorkspaceAgentActivationService`

Atual:

- `agent_id` controla modo agent;
- tools operacionais exigem agente ativo.

Alvo:

```text
Copilot runtime sempre único
operational capability availability independente de agent_id
legacy agent_id somente compatibility até migração concluída
```

### `ChatSoftAgentHandoffService`

Atual:

- sugere trocar para Agente Minha DELPI e reenviar consulta.

Alvo:

```text
miss de capability/expertise
→ dynamic retrieval/replan
→ clarification se required
→ unavailable explanation se não existir capability autorizada
```

Sem handoff de identidade.

### `ChatSkillRegistry`

Atual:

- skills úteis e bindings parcialmente dependentes de `has_agent`/agent metadata.

Alvo:

- preservar capabilities úteis;
- separar disponibilidade de capability de configuração de agente;
- mover preferências/contexto para `ExpertiseContext`/Project quando apropriado;
- remover path-token/operation-marker como semântica sempre que violar a arquitetura OpenAPI-first vigente.

## 5. Estratégia em fases

### M0 — Inventory only

Nenhum runtime diff.

Saídas:

- graph producer/consumer;
- tabela KEEP/MIGRATE/DEPRECATE/REMOVE;
- uso real por banco/UI;
- riscos de compatibilidade.

### M1 — Contratos novos

Definir/reutilizar:

- `ExpertisePackV1`;
- `ExpertiseSelectionV1`;
- `ExpertiseContextV1`;
- `DomainPlaybookV1`;
- provenance/version metadata.

Sem remover agent ainda.

### M2 — Dual-read controlado

```text
legacy specialization config
→ migration adapter
→ ExpertiseContext
```

O adapter é temporário, com exit criteria e telemetry.

Proibido criar duas autoridades permanentes.

### M3 — Copilot-first cutover

Novas conversas e superfícies do Copilot:

- não exigem agent selection;
- operational tools não dependem de agent activation;
- expertise é recuperada automaticamente;
- projects podem sugerir preferred packs.

### M4 — UI deprecation

Remover/ocultar fluxo de "trocar agente" no produto Copilot após:

- usage telemetry;
- migration tests;
- rollback definido;
- documentação atualizada.

### M5 — Data migration

Configuração útil de agents existentes pode virar:

```text
agent knowledge config → expertise/project knowledge preferences
agent specialization → expertise pack refs
agent skill toggles → project/runtime capability preferences somente quando não forem security authority
agent instructions → project guidance ou pack guidance após revisão
```

Não migrar automaticamente instrução insegura ou permission override.

### M6 — Runtime cleanup

Remover:

- agent-required gates sem função residual;
- soft handoff;
- selectors de agente sem consumidor;
- compatibility adapters após exit criteria;
- tests/docs obsoletos.

## 6. Persistência

### Durante transição

Sessões antigas com `agent_id` devem continuar legíveis.

### Futuro

Contexto relevante pode persistir como:

```text
selectedExpertiseRefs
projectId
knowledgeScopeRefs
workflow state
workspace context
```

Evitar persistir expertise selecionada como authority eterna: novo turno pode reavaliar conforme objetivo/contexto.

## 7. Projetos

Se agentes atuais também funcionam como "espaço de trabalho configurável", separar esse conceito de identidade do Copilot.

Projeto pode conter:

- arquivos;
- knowledge scopes;
- preferred expertise;
- templates;
- domain guidance;
- default apps/context.

Projeto não concede permissão nem cria novo planner.

## 8. Compatibilidade de API

Endpoints de administração de agents existentes devem ser inventariados antes de remoção.

Opções:

```text
1. manter read-only durante janela de migração;
2. introduzir endpoints de expertise/playbooks;
3. migrar consumidores;
4. deprecar com versão/data;
5. remover somente após zero consumers provados.
```

## 9. Rollback

Até M4/M5, manter rollback configurável quando tecnicamente necessário.

Após cutover final, não manter `LEGACY_FALLBACK` material indefinidamente.

## 10. Testes de migração

Obrigatórios:

- sessão antiga com agent_id;
- nova sessão sem agent_id;
- query RH/Financeiro/Qualidade sem seleção manual;
- compound cross-domain;
- project preferred expertise;
- capability unauthorized continua bloqueada;
- knowledge scope unauthorized continua bloqueado;
- send/stream parity;
- reload;
- no soft-handoff;
- telemetry/provenance correta;
- residual search por gates `has_agent`/`userActivatedAgent`.

## 11. Critério de conclusão

A migração só fecha quando:

```text
[ ] Copilot funciona sem agente selecionado
[ ] tools/capabilities são governadas por RBAC/policy, não agent activation
[ ] especialização dinâmica cobre casos antes dependentes de presets
[ ] projects preservam customização necessária
[ ] knowledge ACL permanece intacta
[ ] soft handoff removido
[ ] UX não exige troca de agente
[ ] sessões legadas tratadas/migradas
[ ] residual material de agent-routing = zero
[ ] evals candidate final PASS
```
