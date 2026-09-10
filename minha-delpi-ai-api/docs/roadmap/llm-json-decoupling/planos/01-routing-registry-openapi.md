# Plano 01 — Routing registry -> OpenAPI + Action Catalog

**Prioridade:** P0  
**Status execução:** Onda B · E1.S1–S2 ATENDIDOS · E1.S3 **ATENDIDO** · E1.S4 **SHADOW_ON** · próxima = telemetria agree + shadow product preemption  
**Evidência:** [`../evidence/onda-a-inventory.md`](../evidence/onda-a-inventory.md) · [`../evidence/e1-s3-action-catalog.md`](../evidence/e1-s3-action-catalog.md) · [`../evidence/e1-s4-registry-selection-shadow.md`](../evidence/e1-s4-registry-selection-shadow.md) · [`../evidence/execution-ledger.md`](../evidence/execution-ledger.md)  
**Objetivo perceptível:** uma action nova deve ser descoberta e selecionada por semântica/contrato sem exigir `pathMarkers`, `operationIdMarkers`, `routeSegment` ou `parameterStrategy` por endpoint no conteúdo do assistente.

## CURRENT

Fontes de dívida prioritárias:

- `app/content/pt-BR/assistant/operational_route_registry.json`;
- `app/content/pt-BR/assistant/api_route_domains.json`;
- consumers em seleção residual, readiness, route resolver, entity capability, grounded/composition, lint/generator;
- snapshots CI e fallbacks associados.

### EXECUTION_DRIFT (2026-09-10)

O **cold path principal** já é OpenAPI-first:

```text
RetrieveActionCandidatesService
-> PlanExternalActionsService / OpenApiLlmActionPlannerService
-> OpenApiFirstSelectionBridgeService
```

(`OpenApiPlannerModeService` efetivamente on; `select_operational_registry(...)` sem callers no pipeline frio principal.)

Este plano **não** reinventa retrieval/planner. Foco = remover **autoridade residual** do registry que ainda preempta ou classifica por markers:

- product+intent / route_segment → registry filter;
- grounded/composition via `select_registry_route_id`;
- `api_route_domains.parameterStrategy` no binding;
- readiness/lint/CI que ainda leem markers.

Fluxo residual a eliminar:

```text
mensagem
-> predicate/domain / intent+segment
-> route registry (pathMarkers/operationIdMarkers/priority)
-> parameterStrategy
-> action
```

## TARGET

```text
mensagem + contexto
-> goals
-> allowed Action Catalog
-> retrieval top-K
-> planner escolhe actionId candidate
-> OpenAPI binder/validator
-> policy
-> executor genérico
```

Registry pode permanecer apenas para policy transversal que não duplique contrato técnico, e somente enquanto houver ownership canônico comprovado.

## Requisitos

| ID | Requisito |
|---|---|
| R01-01 | Inventariar todos os consumers de fields técnicos do registry. |
| R01-02 | Provar que retrieval/planner já conseguem resolver as families cobertas pelo registry. |
| R01-03 | Remover dependência de path/operationId da seleção principal. |
| R01-04 | Preservar SQL/policies legítimas sem reintroduzir catálogo técnico. |
| R01-05 | Provar unknown provider/API e metamorphic rename. |
| R01-06 | Instrumentar divergência entre legacy e candidate antes do cutover. |

## Decisões travadas

- OpenAPI/Action Catalog é owner de method/path/operationId/parameters/schema.
- Planner recebe apenas candidates autorizadas.
- `parameterStrategy` por endpoint não pode ser autoridade do core genérico.
- Não substituir registry por outro registry semântico manual.
- Qualquer classification persistida deve ser derivada/materializada no import/index e possuir fallback genérico.

## Etapas

### E1.S1 — Inventário de ownership — **ATENDIDO** (2026-09-10)

**Objetivo:** mapear producer -> consumers -> fallback -> tests dos fields `pathMarkers`, `operationIdMarkers`, `excludePathMarkers`, `routeSegment`, `pathSuffix`, `pathExactEnd`, `method`, `priority`, `parameterStrategy` e `routeId`.

**Feito:** matriz em [`../evidence/onda-a-inventory.md`](../evidence/onda-a-inventory.md) §§2–3 (routing / policy / readiness / lint). `fallbackPolicies` classificado KEEP (policy).

**Não feito (correto):** alterar runtime.

### E1.S2 — Baseline de routing — **ATENDIDO_PARCIAL** (2026-09-10)

**Objetivo:** congelar comportamento atual.

**Feito:** harness offline 6/6 + flow-family matrix 25 + content hashes — [`../evidence/onda-a-baseline/manifest.json`](../evidence/onda-a-baseline/manifest.json).

**Gap explícito:** corpus ainda estreito (sem unknown API / metamorphic no freeze offline); `openApiSchemaHash`/`actionCatalogHash` = `PENDING_RUNTIME` → ampliar em plano 09 sem invalidar este runId.

### E1.S3 — Action Catalog suficiente — **ATENDIDO** (2026-09-10)

**Objetivo:** provar que catálogo normalizado contém semântica suficiente.

**Feito:** harness `test_e1_s3_registry_family_topk_retrieval.py` (9 passed) — families + sibling + negative + metamorphic sem pathMarkers. Evidência: [`../evidence/e1-s3-action-catalog.md`](../evidence/e1-s3-action-catalog.md).

**Residual (E1.S4):** filters/markers em `select_registry_route_id` e product intent preemption.

### E1.S4 — Selection cutover em shadow — **SHADOW_ON** (2026-09-10)

**Objetivo:** tornar retrieval/planner candidate o decisor principal em modo comparável.

**Feito (sem cutover):** flag `registrySelectionShadow` + metadata em `select_registry_route_id`; lexical-only; testes agree/diverge/off. Evidência: [`../evidence/e1-s4-registry-selection-shadow.md`](../evidence/e1-s4-registry-selection-shadow.md).

**Pendente:** shadow no preemption product `intent+route_segment`; telemetria live de `agree`; cutover default candidate.

### E1.S5 — Parameter strategy removal

**Objetivo:** mover binding para `mensagem + contexto + action schema`.

**Fazer:** identificar strategies que apenas duplicam parâmetros OpenAPI; migrar para binder genérico e validators; preservar apenas regras transversais justificadas.

**Teste:** required present/missing, enum/type, dates, branch, pagination, body/query/path.

**Pronto quando:** nova action com schema equivalente funciona sem strategy dedicada.

### E1.S6 — Cutover e cleanup

**Objetivo:** retirar autoridade runtime do registry técnico.

**Fazer:** remover fields/consumers mortos e regenerar snapshots/gates; manter somente conteúdo policy legítimo ou mover para owner correto.

**Teste:** full R1-R11 + grep/audit arquitetural de path coupling.

**Pronto quando:** unknown API e metamorphic rename passam e nenhuma seleção genérica exige registry por endpoint.

## Riscos

- catch-all legado mascarar falha de retrieval;
- queda de recall em actions pouco descritas;
- SQL policy misturada com routing técnico;
- alteração simultânea de dataset esconder regressão;
- crescimento de LLM calls por falta de retrieval eficiente.

## Aceite

```text
ACTION_SELECTION_WITHOUT_ENDPOINT_REGISTRY = PASS
UNKNOWN_OPENAPI_PROVIDER = PASS
METAMORPHIC_RENAME = PASS
ARGUMENT_SCHEMA_VALIDATION = PASS
SQL_POLICY_PRESERVED = PASS
NO_NEW_PARALLEL_CATALOG = PASS
```
