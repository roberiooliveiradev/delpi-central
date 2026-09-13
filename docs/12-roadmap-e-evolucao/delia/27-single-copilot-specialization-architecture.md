# DÉLIA — Arquitetura de Inteligência Única e Especialização Componível

**Status:** thematic architecture spec / TARGET  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)

## 1. Decisão

Existe **uma única DÉLIA**, implementada no novo runtime standalone da DÉLIA. O namespace técnico de API permanece temporariamente `minha-delpi-copilot-api` até C0.S1.

```text
NÃO
usuário escolhe agente RH/Qualidade/Engenharia
→ runtime/prompt/tools diferentes
→ handoff entre identidades

SIM
usuário fala com a mesma DÉLIA
→ goals/context
→ capabilities autorizadas
→ Expertise Packs/Playbooks relevantes
→ Knowledge/Multimodal
→ planner/policy/work orchestration
```

Nenhum componente desta arquitetura depende dos agents do Minha DELPI Chat.

## 2. Modelo conceitual

```text
DÉLIA Runtime
├─ Base Behavior / Safety / Policy
├─ Structured Understanding
├─ Workspace + Conversation Context
├─ Capability Retrieval
├─ Expertise Retrieval
├─ Playbook Retrieval
├─ Knowledge Retrieval
├─ Multimodal Intelligence
├─ Structured Planner
├─ Decision / Work Orchestration
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

Technical execution is not a “Generic Executors” subsystem owned by the DÉLIA core. Approved Domain APIs, provider adapters and the Automation Hub technical-execution boundary remain separate owners/contracts.

## 3. Capability

Representa **o que** a DÉLIA pode fazer semanticamente.

Examples:

- consultar estoque;
- abrir app/entidade;
- criar solicitação;
- analisar desenho;
- buscar knowledge;
- gerar artifact.

Authority técnica permanece no owner real: Portal/Core/Domain API/provider/Automation Hub conforme o tipo de capability.

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

Pack não concede permission e não define endpoint/executor technical authority.

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

Knowledge scopes e multimodal capabilities são implementados no runtime standalone da DÉLIA por boundaries/adapters aprovados quando necessários.

A existência de document vision/drawing analysis no Minha DELPI Chat pode informar C0, mas a DÉLIA não chama nem importa aquele runtime.

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

Sem handoff entre agents departamentais.

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
→ Policy/Decision Gate
→ DÉLIA Work orchestration
→ Domain API / approved provider / Automation Hub execution contract as applicable
→ observations/evidence
→ authoritative Outcome verification when material
→ synthesis/presentation
→ persist/audit/evals
```

## 9. Authorities

| Conceito | Authority |
|---|---|
| identity/SSO | Keycloak |
| platform apps/routes/RBAC/governance | Core API |
| platform host/navigation/published context | Portal |
| business actions/data/rules | Domain OpenAPI + Domain API |
| expertise | DÉLIA Expertise governance, when implemented |
| playbooks | DÉLIA Playbook governance, when implemented |
| knowledge retrieval | DÉLIA Knowledge boundary + source ACL |
| multimodal intelligence | DÉLIA orchestration + approved provider/media adapters |
| policy/decision/work | DÉLIA + Domain final authorization where applicable |
| technical automation execution | Automation Hub |
| external resources/scopes | provider + connection owner |
| visual host context | Portal/app source; DÉLIA contextualizes bounded refs |
| OT/safety | industrial/safety owner |

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

C6 Expertise Studio target can:

- list/version packs/playbooks;
- draft/review/eval/publish/rollback;
- assign owners;
- inspect coverage/metrics;
- validate knowledge/capability references.

This is `TARGET` until phase/evidence permits implementation.

## 13. No Chat migration

The following are explicitly out of scope for this DÉLIA architecture:

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
SINGLE_DELIA_IDENTITY
NO_DEPARTMENT_AGENT_RUNTIME
EXPERTISE_COMPOSITION
NO_PERMISSION_ELEVATION
UNKNOWN_PACK_GENERALIZATION
MULTIMODAL_WITHOUT_AGENT_CONCEPT
NO_PARALLEL_TECHNICAL_EXECUTOR_IN_DELIA
NO_CHAT_RUNTIME_DEPENDENCY
```

All must pass in the DÉLIA-owned runtime for the declared scope; documentation alone does not produce PASS.
