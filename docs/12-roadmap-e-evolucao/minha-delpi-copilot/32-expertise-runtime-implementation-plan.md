# Minha DELPI Copilot — Detalhamento do Runtime de Expertise

**Status:** detalhamento temático  
**Autoridade de ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Regra:** os identificadores `E*` abaixo são referências técnicas, **não uma sequência executável independente**.

## 1. Objetivo

Detalhar a migração do modelo atual de agents/skills para o runtime de Copilot único, sem redefinir a ordem C0–C7.

## 2. Componentes alvo

Conceitualmente, se C0 provar gaps reais:

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

Nomes finais devem seguir patterns reais do repositório.

## 3. Boundaries

### Domain
- Expertise/Playbook models puros;
- selection/composition rules;
- sem filesystem/DB/HTTP/LLM.

### Application
- retrieve expertise;
- compose bounded context;
- resolve playbook applicability;
- integrate evidence com planning.

### Infrastructure
- repositories/indexes;
- bootstrap/import;
- embedding/LLM adapters;
- telemetry persistence.

### Interfaces
- admin/read DTO/endpoints quando necessários.

## 4. Mapeamento canônico

| Referência E* | Conteúdo | Fase canônica |
|---|---|---|
| E0 | inventário agent/skill consumers | C0.S0 |
| E1 | contracts/RED tests | C0.S2–C0.S5 |
| E2 | Expertise Catalog/Repository | C2.S2 |
| E3 | retrieval top-K | C2.S3 |
| E4 | bounded context composition | C2.S3 |
| E5 | decouple operational tools de agent activation | C4.S7 |
| E6 | remover soft handoff | C4.S8 |
| E7 | migrar specialization presets | C4/C6, após evidence de consumers |
| E8 | cleanup skill gating | C4, conforme owner/policy |
| E9 | Domain Playbooks | contracts C0; runtime C2.S4/C5 planning |
| E10 | multimodal integration | C2.S6–S7 |
| E11 | project preferences | C6.S4 |
| E12 | admin/observability | C6.S7–S8 |
| E13 | legacy agent-routing deprecation | C7.S5 |

Se este mapeamento divergir de texto antigo, a fase C acima prevalece.

## 5. Regras de implementação

- pack/playbook não concede permission;
- pack/playbook não contém path/method/operationId como authority;
- unknown pack funciona sem planner patch;
- retrieval usa goals/context/entities/attachments/project prefs de forma bounded;
- project preference melhora ranking, não força pack irrelevante;
- knowledge scopes continuam sujeitos a ACL;
- multimodal skill útil não exige `agent_id` quando policy/capability permitir;
- shadow selection tem exit criteria e não vira fallback permanente.

## 6. Migração legada

Inventariar/classificar:

```text
AgentSpecializationService
ChatWorkspaceAgentActivationService
ChatSoftAgentHandoffService
ChatSkillRegistry
agent repositories/entities/controllers
session.agent_id
chat_mode
project default agent
knowledge/actions por agent
agent admin/selector UX
```

Classificações:

```text
KEEP
MIGRATE_TO_EXPERTISE
MIGRATE_TO_PROJECT_CONTEXT
MIGRATE_TO_CAPABILITY_POLICY
DEPRECATE
REMOVE
NOT_PROVEN
```

## 7. Gates

Antes de remover seleção/roteamento material por agent:

```text
EXPERTISE_CONTRACT = PASS
EXPERTISE_RETRIEVAL = PASS
CROSS_DOMAIN_COMPOSITION = PASS
UNAUTHORIZED_CAPABILITY = PASS
UNAUTHORIZED_KNOWLEDGE = PASS
SESSION_WITHOUT_AGENT = PASS
LEGACY_SESSION_COMPATIBILITY = PASS durante janela definida
SOFT_HANDOFF_REMOVAL = PASS
MULTIMODAL_EXPERTISE = PASS quando no escopo
SEND_STREAM_PARITY = PASS
RESIDUAL_AGENT_ROUTING = PASS
```

## 8. Residual scan

```text
has_agent
userActivatedAgent
chat_mode == "agent"
switch_agent_and_resend
softAgentHandoff
agent allowed tools
agentId routing
```

Cada ocorrência final deve ser:

```text
VALID_NON_ROUTING_CONCEPT
LEGACY_COMPAT_WITH_EXIT_CRITERIA
REMOVE
```

Residual material sem exit criteria bloqueia C7.

## 9. Resultado alvo

> “Use Engenharia e Qualidade para analisar este desenho, consulte reclamações anteriores e monte um 8D preliminar.”

Deve funcionar no mesmo Copilot, sem troca de agente e sem perda de RBAC.