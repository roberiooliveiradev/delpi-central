# Minha DELPI Copilot — Arquitetura de Copilot Único e Especialização Componível

**Status:** thematic architecture spec  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)

## 1. Decisão

Existe **um único Minha DELPI Copilot**, implementado na nova `minha-delpi-copilot-api`.

```text
NÃO
usuário escolhe agente RH/Qualidade/Engenharia
→ runtime/prompt/tools diferentes
→ handoff entre identidades

SIM
usuário fala com o mesmo Copilot
→ goals/context
→ capabilities autorizadas
→ Expertise Packs/Playbooks relevantes
→ Knowledge/Multimodal
→ planner/policy/execution
```

Nenhum componente desta arquitetura depende dos agents do Minha DELPI Chat.

## 2. Modelo conceitual

```text
Copilot Runtime
├─ Base Behavior / Safety / Policy
├─ Structured Understanding
├─ Workspace + Conversation Context
├─ Capability Retrieval
├─ Expertise Retrieval
├─ Playbook Retrieval
├─ Knowledge Retrieval
├─ Multimodal Tools
├─ Structured Planner
├─ Generic Executors
├─ Durable Work
└─ Presentation / Audit / Evals

Per-turn specialization
├─ Expertise Pack(s)
├─ Domain Playbook(s)
├─ Knowledge scopes
├─ terminology/methods
├─ multimodal requirements
└─ eval expectations
```

## 3. Capability

Representa **o que** o Copilot pode fazer.

Examples:

- consultar estoque;
- abrir app/entidade;
- criar solicitação;
- analisar desenho;
- buscar knowledge;
- gerar artifact.

Authority técnica permanece no owner real: Portal/Core/OpenAPI/Domain API.

## 4. Expertise Pack

Representa **como analisar melhor um domínio**.

Examples:

- quality-industrial;
- product-engineering;
- supplies;
- commercial;
- finance;
- production;
- maintenance;
- HR.

Pack não concede permission e não define endpoint technical authority.

## 5. Domain Playbook

Representa método/procedimento:

- 8D;
- root cause;
- drawing review;
- FMEA;
- delay analysis;
- nonconformity triage.

Playbook define stages/evidence/criteria. Planner resolve capabilities autorizadas.

## 6. Knowledge / Multimodal

Knowledge scopes e multimodal tools são implementados na Copilot API por ports/adapters próprios.

A existência de document vision/drawing analysis no Minha DELPI Chat pode informar C0, mas o Copilot não chama nem importa aquele runtime.

## 7. Composição

Um turno pode ativar múltiplas expertises:

```text
“Analise atraso do item e risco no desenho”

→ Supplies + Production
→ Product Engineering + Quality
→ delay-analysis playbook
→ drawing-review playbook
→ authorized Business Reads
→ one synthesis/workflow
```

Sem handoff entre agents.

## 8. Pipeline

```text
message + workspace + attachments
→ validation
→ structured understanding
→ authorized capability retrieval
→ expertise/playbook retrieval
→ knowledge/multimodal evidence
→ bounded context
→ structured plan
→ policy/Decision Gate
→ execution/wait
→ observations/evidence
→ synthesis/presentation
→ persist/audit/evals
```

## 9. Authorities

| Conceito | Authority |
|---|---|
| identity | Keycloak |
| platform permissions/apps/routes | Core API |
| business actions | Domain OpenAPI + Domain API |
| platform actions | Core + Portal |
| expertise | Copilot Expertise Catalog |
| playbooks | Copilot Playbook Catalog |
| knowledge retrieval | Copilot Knowledge runtime + source ACL |
| multimodal | Copilot multimodal adapters |
| policy/decision | Copilot Policy + Domain final authorization |
| visual context | Portal Workspace Context |

## 10. Retrieval

Inputs:

- goals;
- entities;
- workspace;
- attachments;
- capability candidates;
- domain terminology;
- project preferences.

Output uses structured scores/reason codes, never private CoT.

Top-K loading avoids concatenating all expertise into every prompt.

## 11. Projects/preferences

Project may configure:

- preferred packs;
- allowed knowledge refs;
- files/context;
- artifact templates;
- domain guidance.

It never creates another runtime or grants permission.

## 12. Administration

C6 Expertise Studio can:

- list/version packs/playbooks;
- draft/review/eval/publish/rollback;
- assign owners;
- inspect coverage/metrics;
- validate knowledge/capability references.

## 13. No Chat migration

The following are explicitly out of scope for this Copilot architecture:

```text
AgentSpecializationService migration
ChatWorkspaceAgentActivationService changes
ChatSoftAgentHandoffService removal
ChatSkillRegistry migration
agent_id/chat_mode conversion
Chat session compatibility
```

Those concerns remain with the Chat product if ever addressed.

## 14. Acceptance

```text
SINGLE_COPILOT_IDENTITY
NO_DEPARTMENT_AGENT_RUNTIME
EXPERTISE_COMPOSITION
NO_PERMISSION_ELEVATION
UNKNOWN_PACK_GENERALIZATION
MULTIMODAL_WITHOUT_AGENT_CONCEPT
NO_CHAT_RUNTIME_DEPENDENCY
```

All must pass in the Copilot-owned runtime.