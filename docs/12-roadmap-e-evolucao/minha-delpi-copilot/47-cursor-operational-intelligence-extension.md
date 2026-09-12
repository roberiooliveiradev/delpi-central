# Cursor — Extensão Obrigatória — Inteligência Operacional do Minha DELPI Copilot

**Status:** suplemento obrigatório do `23-prompt-cursor-execucao.md` quando qualquer requisito CP-071+ ou etapa O* estiver em escopo.

## 1. Leia antes de implementar

Além do prompt mestre, leia:

1. `34-market-benchmark-and-product-north-star.md`
2. `35-delpi-business-graph.md`
3. `36-copilot-tasks-cases-and-interaction-rooms.md`
4. `37-copilot-inbox-watch-and-proactive-work.md`
5. `38-evidence-provenance-and-epistemic-ux.md`
6. `39-decision-gates-and-what-if-simulation.md`
7. `40-organizational-knowledge-and-governed-learning.md`
8. `41-expertise-studio-governance.md`
9. `42-model-router-and-compute-policy.md`
10. `43-durable-workflow-runtime.md`
11. `44-operational-intelligence-implementation-plan.md`
12. `45-operational-intelligence-testing-gates.md`
13. `46-operational-intelligence-requirements.md`

## 2. Não interpretar visão estratégica como licença para big-bang

O plano continua:

```text
C0.S0 primeiro
→ contracts
→ minimum correct slice
→ evidence
→ COMPLETE_GATE
```

Não crie Business Graph, Cases, Inbox, event bus, workflow engine, model router e Studio em um único ciclo.

## 3. Regras arquiteturais adicionais

### Business Graph

- graph contém refs/relationships, não cópia indiscriminada dos bancos;
- source APIs continuam authority dos fatos;
- traversal respeita RBAC;
- relation inferred é marcada como inferred;
- nenhum matcher app-specific no planner.

### Evidence

- claims materiais preservam provenance;
- hipótese não vira fato;
- freshness é explícita;
- multimodal finding preserva localização quando possível.

### Tasks/Cases/Rooms

- persistir estado operacional, não CoT;
- Case/Room não concede permission sobre source entity;
- reuse estruturas existentes antes de criar domínio paralelo;
- lifecycle e audit obrigatórios.

### Inbox/Watch

- preferir eventos reais a polling;
- dedupe/cooldown;
- revalidar permission no trigger;
- `ACT` bloqueado até autonomy policy correspondente;
- alerta precisa de evidence/contexto acionável.

### Durable Workflows

- checkpoints estruturados;
- resume revalida RBAC/policy/freshness;
- write retry só com idempotência/verification;
- nenhum workflow long-running baseado em request HTTP aberto;
- não reexecutar prompt inteiro como estratégia de resume.

### Decision Gates

- gate proporcional ao risco;
- args/evidence materialmente alterados invalidam aprovação;
- approval humano não substitui backend authorization.

### Simulation

- preferir modelo/regra determinística owner;
- declarar baseline/premissas/limitações;
- simulate nunca aplica alteração;
- apply é Business Action separada.

### Organizational Knowledge

- feedback não publica conhecimento automaticamente;
- Experience/Solution Pattern exige review/eval/version;
- não persistir CoT como Decision Knowledge;
- LGPD/retention/scopes obrigatórios.

### Expertise Studio

- não criar agent builder;
- version lifecycle;
- eval before publish;
- rollback;
- sem endpoint catalog técnico dentro de expertise/playbook.

### Model Router

- não implementar antes de baseline de qualidade/custo/latência;
- routing por requirement/compute policy;
- privacy/provider constraints;
- fallback não relaxa safety.

## 4. Inventário adicional no C0.S0

Mapear com evidence:

```text
canonical entity IDs
entity relationships
existing event bus/events
background jobs/queues
interaction rooms/chats existentes
notifications/inbox existentes
approval models
workflow persistence/checkpoints existentes
provenance/audit metadata
knowledge sources/lifecycle
model/provider abstraction
latency/token/cost metrics
```

Classificar cada item:

```text
REUSE
EXTEND
MIGRATE
CREATE_REQUIRED
NOT_PROVEN
OUT_OF_SCOPE_WITH_DECISION
```

## 5. Reuse-first

Antes de criar componente novo, procurar:

- Minhas Solicitações para Task/Case-like state;
- salas de interação existentes;
- notifications/event-driven infrastructure;
- current workflow/background execution;
- audit logs;
- entity/deep-link contracts;
- Core app/routing metadata;
- AI memory/result refs;
- existing model config/services.

A visão estratégica não justifica duplicação.

## 6. Anchor scenario

O candidato maduro deve eventualmente suportar:

> “Esse produto está dando problema no cliente. Analise o desenho, procure casos parecidos, relacione produção, qualidade e fornecedor, monte uma investigação 8D, acompanhe as evidências que faltam e me avise quando Engenharia liberar a nova revisão.”

Trajetória esperada:

```text
Case
→ Business Graph
→ multimodal evidence
→ Expertise + Playbook
→ Tasks/Durable Workflow
→ wait_event/Watch
→ Inbox
→ reanalysis
→ Decision Gate
→ Business Action
→ evidence/outcome/audit
```

Sem seleção manual de agente e sem DOM automation.

## 7. Reporte adicional por O-step

```text
OPERATIONAL_STEP:
CP_REQUIREMENTS:
REUSED_COMPONENTS:
NEW_COMPONENTS_JUSTIFIED:
DATA_AUTHORITIES:
ENTITY_RELATIONS:
EVENT_SOURCES:
PERSISTENCE:
RBAC_POLICY:
PROVENANCE:
IDEMPOTENCY:
RELOAD_RESUME:
GENERALIZATION:
TEST_GATE:
COMPLETE_GATE:
```

## 8. Bloqueios

Não declarar PASS quando houver:

```text
manual relation catalog sem owner
unfiltered graph traversal
claim material sem provenance
case/room permission leakage
polling app-specific tratado como arquitetura final
watch ACT sem policy
duplicate write after resume
approval stale
simulation não reproduzível
knowledge auto-published
model router sem baseline/evals
```

## 9. Ordem

Seguir `44-operational-intelligence-implementation-plan.md`; cada O-step respeita dependências C0–C7 e não substitui o plano mestre.