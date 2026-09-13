# DÉLIA — AI Control Tower e Governança da Força de Trabalho Digital

**Status:** `TARGET` — thematic architecture/product/governance spec  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Observability:** [`11-observability-evals.md`](./11-observability-evals.md)  
**Automation Hub:** [`57-event-driven-autonomous-operations-and-automation-execution-hub.md`](./57-event-driven-autonomous-operations-and-automation-execution-hub.md)

## 1. Decisão de produto

A visão alvo prevê uma visão central governada dos ativos de IA e automação relevantes para a DELPI.

Nome conceitual:

> **DÉLIA AI Control Tower**

Control Tower é uma **projeção/experiência de governança, observabilidade e administração**. Não é segundo planner, segundo Work runtime, segundo executor, permission authority ou source of truth dos ativos que pertencem a outros owners.

## 2. Escopo de ativos

Candidates a serem projetados, conforme C0 provar owners/fontes/contratos:

```text
DÉLIA surfaces/runtime refs
LLM/model providers
Vision/Speech/Embedding/Predictive models
Expertise Packs
Domain Playbooks
Watches
Durable Work refs
Automation Hub execution assets
MCP servers/tools
A2A agents
External Connectors
Edge AI deployments
Semantic metrics/models
Knowledge assets
Prompt/policy versions
```

A lista é `TARGET`; não prova que registry, telemetry ou control plane já existam.

## 3. AI Asset Registry projection

Se C0 justificar um registry/projection, ele deve manter metadata/ref mínima suficiente para governança sem duplicar o master do owner.

Candidate shape:

```text
assetId
assetType
name/version
owner/sourceRef
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

O shape não é contrato congelado antes de C0/Abstraction Gate.

## 4. Digital Workforce view

A experiência deve poder responder, quando houver fonte autoritativa:

```text
quais automações/agentes/modelos estão ativos?
quem é o owner?
o que podem fazer?
quais dados acessam?
qual autonomia possuem?
qual custo/latência?
qual taxa de sucesso técnico?
qual taxa de Outcome verificado?
quais estão degradados?
quais possuem incidentes?
quais estão sem avaliação válida?
```

## 5. Governance controls

Controls podem existir apenas quando o owner/contrato permitir e não criam authority paralela:

```text
request approve / publish / deprecate / revoke
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

Control Tower pode invocar contratos dos owners; não redefine suas regras. Admin da Control Tower não herda business permission.

## 6. Risk tiers

C0 deve decidir se uma taxonomia compartilhada é necessária e quem a possui. Exemplo apenas ilustrativo:

```text
LOW
MEDIUM
HIGH
CRITICAL
```

Não congelar classificação por conveniência documental. Risk tier informa policy/eval/rollout; nunca concede permissão.

## 7. Cost / value governance

Medir separadamente, quando as fontes existirem:

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

Tokens ou número de execuções não provam ROI.

## 8. Incident management

Incidentes de IA/automação devem referenciar os ativos/owners reais e seguir o processo corporativo autoritativo de incident/change management, se existente.

Candidate projection:

```text
incidentRef
assetRefs[]
severity
detectedAt
symptoms/evidence
impact
containment
killSwitchRefs used
owner
resolutionRef
postmortem/actions refs
```

Control Tower não cria incident authority paralela.

## 9. Audit and lineage

Para ação material deve ser reconstruível, a partir das fontes corretas:

```text
trigger/actor
asset/version refs
model/provider/policy refs
Evidence/context refs
Decision ref
autonomy level
technical execution ref
verified Outcome
notifications
```

Sem chain-of-thought ou secrets.

## 10. Separation of duties

```text
Keycloak = identity/SSO
Core = apps/routes/RBAC/governance
Domain APIs = business authority
DÉLIA = intelligence/Evidence/Policy/Decision/Work orchestration
Automation Hub = technical execution
Control Tower = governed projection/admin experience over authorized owner contracts
```

Control Tower não se torna business authority, planner ou executor.

## 11. C0 inventory

Inventariar factual:

- AI/model inventories atuais;
- provider accounts/contracts;
- monitoring/eval tooling;
- cost telemetry;
- RPA/automation inventory;
- prompt/policy registries;
- model deployment systems;
- incident/change-management owners;
- risk/compliance owners;
- kill switches/feature flags;
- asset ownership gaps.

Sem evidence suficiente = `TO_INVENTORY`.

## 12. Phase mapping

```text
C0 → inventory + owner/source/contract freeze
C3 → metadata/eval-lineage foundations only when justified
C5 → execution/policy/Outcome refs may feed governed projections
C6 → Control Tower admin/dashboard/health/coverage/incidents/cost/value experience
C7 → mature cross-runtime governance, budgets, advanced rollout/optimization where owners expose safe controls
```

## 13. Acceptance

Quando implementada, provar:

- every enabled high-risk capability references an explicit owner/policy/eval/disable path;
- unknown/unapproved high-risk asset cannot be activated through Control Tower alone;
- asset/version is traceable from material Outcome;
- provider/model rollback/revoke reaches the authoritative owner;
- one capability can be disabled without unrelated shutdown when architecture supports it;
- ROI uses verified outcome metrics;
- no secret/raw credential exposed in registry/UI;
- Control Tower cannot grant business permission.

Sem prova obrigatória: `PENDING`/`INCONCLUSIVE`.

## 14. North Star

> **A DELPI deve conseguir enxergar e governar seu ecossistema de IA e automação por meio de uma Control Tower que projeta owners, riscos, custos, evals, health e outcomes sem criar uma segunda authority operacional.**
