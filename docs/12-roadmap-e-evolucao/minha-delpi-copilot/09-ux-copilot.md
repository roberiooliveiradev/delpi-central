# 09 — UX do Minha DELPI Copilot

**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Specs temáticas:** `53–66`

## 1. Princípio

O Copilot deve parecer parte do trabalho real, não uma janela de chat. Conversa, dados, processos, análises, automações, artefatos, modelos e contexto industrial convergem para uma experiência única com provenance, estado e governança visíveis quando materiais.

## 2. Surfaces

```text
GLOBAL      → painel contextual
WORKSPACE   → análise/trabalho completo
MEETING     → reunião assistida
FRONTLINE   → posto/máquina/operator assistance
TEAMS       → futura surface do mesmo runtime
ADMIN       → Connections/Control Tower/Automation/Process/Semantic/Model governance conforme role
```

Não são produtos/agentes separados.

## 3. Source and authority UX

Quando material, distinguir:

```text
Minha DELPI / source oficial
Internet pública
External connected source
Personal Memory
Semantic Metric Definition
Prediction/Simulation
Process-derived insight
AI-generated artifact
```

Prediction/recommendation/simulation nunca deve parecer FACT oficial.

## 4. Activity UX — sem CoT

Mostrar passos verificáveis:

```text
Consultando dados da DELPI
Pesquisando internet
Consultando Outlook/Teams
Resolvendo métrica governada
Analisando processo
Executando análise em ambiente isolado
Gerando artefato
Rodando previsão/simulação
Preparando ação
Aguardando decisão
Executando automação
Verificando resultado
Sincronizando Edge
```

Não mostrar cadeia de raciocínio privada.

## 5. Connections / External UX

Preservar UX de conexões pessoais/organizacionais/compartilhadas/serviço, scopes em linguagem humana, reconnect/revoke, source provenance, `draft != send`, provider outcome real e degraded subscription state.

## 6. Watch / Autonomous Work UX

Watch deve mostrar:

```text
condition
source/event
mode: OBSERVE | ADVISE | PREPARE | ACT
scope/capability
autonomy policy
status/last trigger
what happens when triggered
pause/disable
```

C6 não mostra ACT como habilitado. Em C7, ACT exige capability-specific policy/limits/kill switch visibility.

## 7. Automation & Execution Hub UX

Admin/operator view target:

```text
Automations
Executions
Workers
Exceptions
Outcomes
```

For each automation:

- semantic capability;
- owner;
- executor type/version;
- environment;
- autonomy mode;
- status/health;
- technical success rate;
- verified Outcome rate;
- kill switch.

Execution timeline distinguishes:

```text
QUEUED
RUNNING
TECHNICALLY_SUCCEEDED
VERIFYING_OUTCOME
VERIFIED_SUCCESS | VERIFIED_FAILURE | AMBIGUOUS
```

Never label technical bot completion as business success prematurely.

## 8. Process Intelligence UX

Workspace should support:

```text
Process Map
Variants
Bottlenecks
Wait/Rework
Conformance
Automation Opportunities
Before/After
```

Every finding links to event/source Evidence.

Do not default to employee leaderboard. If actor data appears for legitimate operational reason, show purpose/scope and avoid personality/fraud judgments.

## 9. AI Control Tower UX

Role-gated admin experience:

```text
Digital Workforce
AI Assets
Models
Automations
Connectors
MCP/A2A integrations
Edge deployments
Incidents
Cost & Verified Value
Risk / Evals / Kill Switches
```

Cards should answer owner, version, status, risk, data/capabilities, eval freshness, dependencies, cost and health.

Control Tower administrative access does not visually imply permission to execute underlying business actions.

## 10. MCP / A2A UX

Admin lifecycle:

```text
DISCOVERED → REVIEWED → APPROVED → ACTIVE → DISABLED/REVOKED
```

Before approval show requested capabilities, data domains, write/read classification, owner, trust source and required credentials/scopes.

For delegated task, user-facing activity may show:

```text
Delegando subtarefa ao agente aprovado X
Aguardando resultado
Resultado recebido / indisponível / cancelado
```

No raw protocol or hidden context dump.

## 11. Personal Memory UX

A surface **Memória pessoal** should allow:

```text
Ver o que o Copilot lembra
Corrigir
Apagar/esquecer
Desabilitar personalização
Definir preferências/retention quando aplicável
```

When a material answer is personalized, optional disclosure:

> “Priorizei estes itens porque você acompanha Projeto X e Indicador Y.”

Personal Memory never appears as organizational fact.

## 12. Personalized Briefing

Target:

```text
changes since last view
pending decisions
Tasks/Cases/Watches
meeting/calendar items
risks/anomalies
followed metrics/topics
```

All business facts are fetched live/authorized; memory only helps relevance/presentation.

## 13. Semantic Business Layer UX

Metric cards/details should expose progressive disclosure:

```text
metric name
business definition
value/unit
period/grain/dimensions
source/freshness
owner
formula/version
```

If conflicting definitions exist, show the conflict and ask/resolve scope instead of hiding it.

## 14. Analysis Sandbox UX

User asks naturally; no need to know Python/SQL.

Activity/status:

```text
Preparing authorized data
Running analysis
Generating chart/table
Completed / Failed / Timed out
```

Advanced users/admin may inspect reproducibility metadata/code/artifacts when authorized. Sandbox failure must not produce invented numbers.

## 15. Artifact Workspace UX

Artifacts appear as editable work objects, not chat blobs:

```text
Report
Spreadsheet
Presentation
Chart
BPMN/Process Map
A3/8D/FMEA candidate
Checklist/Procedure draft
Project plan
Meeting minutes
```

Show:

- version/status;
- source/evidence links;
- AI-generated vs human-edited state when relevant;
- comments/review;
- attach to Case/Task/Room;
- export/share actions.

Regenerate must not silently overwrite human edits.

## 16. Predictive / Prescriptive UX

Prediction example:

```text
Risco de ruptura: 76%
Horizonte: 4 dias
Modelo: ...
Atualizado: ...
Confidence/calibration/limitations
```

Use explicit labels:

```text
PREVISÃO
CENÁRIO
RECOMENDAÇÃO
```

Never present as “vai acontecer”.

Prescriptive view shows alternatives/objectives/constraints/trade-offs and separate `[Preparar ação]` / `[Aplicar]` only when allowed.

## 17. Operational Twin / Scenario UX

Scenario workspace clearly indicates simulation mode:

```text
CENÁRIO — NÃO É PRODUÇÃO
```

Allows parameter changes, assumptions, compare scenarios and impact cards. Production Apply is separate, revalidates live state and creates new Decision flow.

## 18. Edge / Offline UX

Frontline must visibly show:

```text
ONLINE
DEGRADADO
OFFLINE — dados sincronizados em <time>
SINCRONIZANDO
```

For critical procedure/drawing, show revision and freshness. Stale critical source must be blocked/degraded per policy.

User switch/logout clears personal context; offline does not expose previous operator state.

## 19. Model lifecycle / Marketplace UX

Control Tower/Marketplace can show:

```text
Model/Asset name/version
owner/publisher
status
risk
eval status
compatibility/dependencies
required permissions/scopes (requirements only)
release notes
health/rollback
```

Buttons such as Enable/Install must explain that actual RBAC/provider authorization remains separate.

## 20. Meeting / Frontline / Biometrics

Preserve current explicit capture indicators, biometric `UNKNOWN→CANDIDATE→CONFIRMED/CORRECTED`, large-touch/hands-free Frontline and internal procedure/revision authority.

Meeting transcript/source/decision/action/outcome remain semantically distinct.

## 21. Context chips

Examples:

```text
Portal Comercial · Cliente 000123
Case Q-2026-0042
Outlook · thread fornecedor
Processo · Compras · Variant 3
Métrica · Lead Time v4
Cenário · PRESS-04 parada 4h
Artifact · Relatório de Risco v2
```

User can remove/correct context; chip does not imply permission.

## 22. Decision UX

Before material action show action/target/impact/evidence/risk/source/model/metric/version as needed, and clearly differentiate:

```text
Preview
Prepared
Waiting approval
Executing
Verifying outcome
Completed/Failed/Ambiguous
```

## 23. Error/degraded UX

Must distinguish source unavailable vs no data, connection expired, metric unknown/conflict, process data incomplete, sandbox timeout, model unavailable/OOD, agent/tool revoked, Edge stale/offline, package/model revoked and outcome inconclusive.

Never mask degraded state as business conclusion.

## 24. Privacy UX

Where material disclose:

- personal vs organizational source/memory;
- capture/recognition active state;
- source sharing/persistence/promotion;
- model/AI asset use when materially relevant;
- offline cache/freshness;
- how to revoke/delete/disable.

## 25. Accessibility

Keyboard/focus/screen-reader/contrast/live regions/captions/large-touch/non-voice fallback are mandatory across new admin/data/process/scenario/artifact surfaces.

Charts/process maps require textual alternatives/summary.

## 26. UX success

A user should move naturally through:

```text
question/event
→ grounded internal/external/process/semantic analysis
→ prediction/scenario when useful
→ artifact or recommendation
→ PREPARE/Decision
→ Task/Workflow/Automation
→ verified Outcome
→ notification
→ governed learning/personal continuity
```

without needing to know APIs, RPA, model providers, MCP/A2A protocols or internal architecture.
