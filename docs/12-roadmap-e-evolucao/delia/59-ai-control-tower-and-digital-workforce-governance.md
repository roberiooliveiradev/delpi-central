# Minha DELPI Copilot — AI Control Tower e Governança da Força de Trabalho Digital

**Status:** thematic architecture/product/governance spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Observability:** [`11-observability-evals.md`](./11-observability-evals.md)  
**Automation Hub:** [`57-event-driven-autonomous-operations-and-automation-execution-hub.md`](./57-event-driven-autonomous-operations-and-automation-execution-hub.md)

## 1. Decisão de produto

A DELPI deve possuir uma visão central de **todos os ativos de IA e automação relevantes**, não apenas do Copilot.

Nome conceitual:

> **Minha DELPI AI Control Tower**

Ela é plano de governança/observabilidade/administração; não é um segundo planner nem um segundo runtime de decisão.

## 2. Escopo de ativos

```text
Copilot surfaces/runtime
LLM/model providers
Vision/Speech/Embedding/Predictive models
Expertise Packs
Domain Playbooks
Watches
Durable Workflows
Automations/Executors/RPAs
MCP servers/tools
A2A agents
External Connectors
Edge AI deployments
Semantic metrics/models
Knowledge sources
Prompt/policy versions
```

## 3. AI Asset Registry

Cada ativo material deve poder ser representado por metadata governável:

```text
assetId
assetType
name/version
owner
status
criticality/risk
capabilities
data domains/scopes
runtime/deployment ref
policyRef
model/provider refs?
cost center/budget?
eval status
last validated at
dependencies
killSwitchRef?
```

Registro não duplica o master do owner; mantém refs/projection.

## 4. Digital Workforce view

A Control Tower deve responder:

```text
quais automações/agentes estão ativos?
quem é o owner?
o que podem fazer?
quais dados acessam?
qual autonomia possuem?
qual custo/latência?
qual taxa de sucesso real?
quais estão degradados?
quais possuem incidentes?
quais estão sem avaliação válida?
```

## 5. Governance controls

Target:

```text
approve / publish / deprecate / revoke
enable / disable
cohort rollout
budget / rate limit
autonomy limit
model/provider allowlist
data-domain restriction
connection/connector restriction
kill switch
incident containment
rollback
```

Controles nunca podem ser alterados por prompt normal do usuário.

## 6. Risk tiers

C0 deve congelar uma taxonomia simples, por exemplo:

```text
LOW      → read-only/low sensitivity
MEDIUM   → bounded internal write / communication
HIGH     → financial/material/external/people impact
CRITICAL → safety/regulated/high irreversible impact
```

Risk tier influencia evals, approval, rollout, autonomy, observability e retention.

## 7. Cost / value governance

Medir separadamente:

```text
model/provider cost
automation execution cost
human review cost
infrastructure cost
saved time
cycle-time reduction
error/rework reduction
recovered value / avoided loss
verified business outcomes
```

Não declarar ROI apenas com tokens ou número de execuções.

## 8. Incident management

AI/automation incident deve ser first-class:

```text
incidentId
assetRefs[]
severity
detectedAt
symptoms/evidence
impact
containment
kill switches used
owner
resolution
postmortem/actions
```

Exemplos: provider leak, false autonomous write, repeated RPA failure, model drift, unsafe tool exposure, privacy incident.

## 9. Audit and lineage

Para ação material deve ser possível reconstruir:

```text
who/what triggered
which asset/version
which model/provider/policy
which Evidence/context
which Decision Gate
autonomy level
which executor
verified Outcome
notifications
```

Sem persistir chain-of-thought.

## 10. Separation of duties

Admin de Control Tower não implica automaticamente business permission para executar capability. Business/domain authorization continua nos owners oficiais.

## 11. C0 inventory

Inventariar:

- AI/model inventories atuais;
- provider accounts/contracts;
- existing monitoring/eval tooling;
- cost telemetry;
- RPA/automation inventory;
- prompt/policy registries;
- model deployment systems;
- incident/change-management owners;
- risk/compliance owners;
- current kill switches/feature flags;
- asset ownership gaps.

## 12. Phase mapping

```text
C0 → asset/risk/owner/control inventory and registry contracts
C3 → baseline asset metadata/eval lineage
C5 → execution/policy/outcome telemetry feeds Control Tower
C6 → admin/dashboard, health, coverage, incidents, cost/value
C7 → mature cross-runtime governance, budgets, advanced rollout and optimization
```

## 13. Acceptance

- every enabled L4/L5 capability has owner/policy/eval/kill switch;
- unknown/unregistered high-risk executor cannot run;
- asset version is traceable from material outcome;
- provider/model rollback is auditable;
- Control Tower can disable one capability without shutting down unrelated capabilities;
- ROI uses verified outcome metrics;
- no secret/raw credential exposed in registry/UI.

## 14. North Star

> **A DELPI deve saber quais inteligências e automações existem, quem é responsável por elas, o que podem fazer, quanto custam, que valor entregam e como interrompê-las com segurança.**
