# Plano 01 — Routing registry -> OpenAPI + Action Catalog

**Prioridade:** P0  
**Objetivo perceptível:** uma action nova deve ser descoberta e selecionada por semântica/contrato sem exigir `pathMarkers`, `operationIdMarkers`, `routeSegment` ou `parameterStrategy` por endpoint no conteúdo do assistente.

## CURRENT

Fontes de dívida prioritárias:

- `app/content/pt-BR/assistant/operational_route_registry.json`;
- `app/content/pt-BR/assistant/api_route_domains.json`;
- consumers em seleção, readiness, route resolver, entity capability e lint/generator;
- snapshots CI e fallbacks associados.

Fluxo atual residual:

```text
mensagem
-> predicate/domain
-> route registry
-> pathMarkers/operationIdMarkers/priority
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

### E1.S1 — Inventário de ownership

**Objetivo:** mapear producer -> consumers -> fallback -> tests dos fields `pathMarkers`, `operationIdMarkers`, `excludePathMarkers`, `routeSegment`, `pathSuffix`, `pathExactEnd`, `method`, `priority`, `parameterStrategy` e `routeId`.

**Fazer:** localizar todos os reads; classificar cada consumer como routing, policy, readiness, presentation, telemetry, lint/test ou legado.

**Não fazer:** alterar runtime.

**Teste:** produzir matriz sem consumer órfão; cruzar com code search e testes existentes.

**Pronto quando:** 100% dos reads conhecidos têm owner alvo e estratégia de cutover.

### E1.S2 — Baseline de routing

**Objetivo:** congelar comportamento atual.

**Fazer:** dataset com product, production, KPI, SQL policy, sibling actions, no-tool, multi-provider e unknown external API.

**Teste:** R1/R2/R3/R8/R10/R11; registrar action top-K, selected action, args, latency e fallback.

**Pronto quando:** baseline imutável possui runId/config hashes.

### E1.S3 — Action Catalog suficiente

**Objetivo:** provar que catálogo normalizado contém semântica suficiente.

**Fazer:** verificar summary, description, tags, params/descriptions, request/response schema, sensitivity e binding; corrigir import/index genericamente quando necessário.

**Não fazer:** adicionar metadata DELPI manual por endpoint para passar casos.

**Teste:** unknown API sem extensão proprietária entra no retrieval.

**Pronto quando:** top-K recall atende corpus sem registry técnico.

### E1.S4 — Selection cutover em shadow

**Objetivo:** tornar retrieval/planner candidate o decisor principal em modo comparável.

**Fazer:** executar legacy e candidate quando seguro; registrar divergência sem duplicar chamadas externas.

**Não fazer:** ocultar divergências com fallback silencioso.

**Teste:** semantic siblings + provider rename + path/operationId rename.

**Pronto quando:** divergências são explicáveis e candidate não depende de literal técnico antigo.

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
