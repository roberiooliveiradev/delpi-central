# Roadmap — desacoplamento de JSONs e generalização LLM/OpenAPI

**Status:** ativo — Ondas A **ATENDIDA**; B/C/D **ATENDIDO_PARCIAL**; E **EM_ANDAMENTO** (plano 04 OK → E5.S1 composition)  
**Owner arquitetural:** Minha DELPI AI / OpenAPI-first tool routing  
**Dependência:** `../openapi-first-universal-tool-routing.md`  
**Baseline freeze:** [`evidence/onda-a-baseline/manifest.json`](./evidence/onda-a-baseline/manifest.json)

## 1. Resultado esperado

Evoluir o chat de um comportamento parcialmente orientado por catálogos/heurísticas conhecidas para um motor generalizável:

```text
CURRENT
mensagem
-> termos/regex/predicates
-> registry/path/operationId conhecidos
-> parameterStrategy específica
-> execução
-> presenter/profile conhecido

TARGET
mensagem + contexto estruturado
-> Turn Understanding
-> goals/subtasks
-> allowed Action Catalog
-> semantic retrieval
-> structured planner
-> OpenAPI argument binding/validation
-> RBAC/policy/confirmation
-> generic execution
-> responseSchema + metadata
-> schema-driven presentation
-> grounded synthesis/recommendations
```

## 2. Ledger de requisitos

| ID | Requisito | Estado no roadmap |
|---|---|---|
| RQ-01 | Remover autoridade técnica de JSONs que duplicam path/method/operationId/schema/strategy | ATENDIDO_NO_PLANO |
| RQ-02 | Reduzir NLU hardcoded por termos, exclusões, regex e predicates | ATENDIDO_NO_PLANO |
| RQ-03 | Fazer pedidos longos virarem goals/subtasks sem compressão em uma intent única | ATENDIDO_NO_PLANO |
| RQ-04 | Generalizar follow-up com estado estruturado, sem substring de path | ATENDIDO_NO_PLANO |
| RQ-05 | Extrair argumentos semanticamente e validar pelo OpenAPI | ATENDIDO_NO_PLANO |
| RQ-06 | Remover mini Action Catalog/capabilities manuais duplicados | ATENDIDO_NO_PLANO |
| RQ-07 | Tornar composição/enrichment dependentes do objetivo e das actions permitidas | ATENDIDO_NO_PLANO |
| RQ-08 | Tornar recomendações e sugestões contextuais sem inventar capabilities | ATENDIDO_NO_PLANO |
| RQ-09 | Preservar policies, business rules, safety e copy legítima fora do LLM | HERDADO_POR_SOLUCAO_TRANSVERSAL |
| RQ-10 | Remover acoplamento residual de apresentação por path quando schema/metadata bastam | ATENDIDO_NO_PLANO |
| RQ-11 | Preservar send/stream/simulate, persistência/F5, histórico e UI | ATENDIDO_NO_PLANO |
| RQ-12 | Provar API externa desconhecida e teste metamórfico de rename | ATENDIDO_NO_PLANO |
| RQ-13 | Controlar latência, tokens, tool count e número de chamadas LLM | ATENDIDO_NO_PLANO |
| RQ-14 | Remover conteúdo morto somente após cutover comprovado | ATENDIDO_NO_PLANO |

## 3. Decisões travadas

### D-01 — não existe migração cega JSON -> LLM

Destino depende da natureza do conteúdo:

| Conteúdo | Destino |
|---|---|
| path/method/operationId/params/schema | OpenAPI + Action Catalog |
| classificação semântica estável de action | materializada no import/index quando necessária |
| compreensão de pedido/contexto | LLM estruturado |
| required/type/enum/format | validator determinístico |
| RBAC/sensitivity/confirmation | policy determinística |
| business rule/factual verdict | domínio determinístico |
| UX/copy/prompt | JSON/conteúdo configurável |
| apresentação genérica | responseSchema + payload + metadata |
| framing/recommendação contextual | síntese LLM existente, quando possível |

### D-02 — preferência de custo/latência

```text
fonte canônica direta
> transformador determinístico
> cache/materialização semântica
> reutilizar chamada LLM já existente no turno
> nova chamada LLM dedicada
```

Nova chamada LLM só entra com justificativa mensurável.

### D-03 — planner não autoriza execução

`retrieval/planner` escolhe entre candidates permitidas; validator e policy continuam soberanos.

### D-04 — generalização é critério de arquitetura

Uma API externa desconhecida deve operar sem source code, intent, selector, marker, parameter strategy ou presenter por endpoint.

### D-05 — compatibilidade antes de remoção

Registry/heurística antiga pode existir temporariamente como shadow/fallback observável. Só remover após candidate provar cobertura e ausência de regressão material.

## 4. Matriz de fluxos

| Fluxo | CURRENT principal (HEAD) | TARGET | Prioridade | Plano | Nota |
|---|---|---|---|---|---|
| Routing técnico | OpenAPI-first no cold path + **registry residual** (intent/grounded/params) | Action Catalog + retrieval + planner sem preempção | P0 | 01 | Não reinventar OpenAPI-first |
| Understanding/intents | `product_query_intent`, `production_operational_intent`, `department_kpi_rules`, vocabularies; TU em **shadow** | Turn Understanding estruturado | P0 | 02 | |
| Follow-up/refinement/args | route segments, terms, regex, `pathContains` | state + schema + planner/binder | P0 | 03 | |
| Capabilities/actions | `capability_registry.action.*` (+ UX via `uxCapability`; **pathRules removido**) | Action Catalog materializado | P1 | 04 | R04-02 ATENDIDO (D1) |
| Composition/enrichment | routeIds/scope maps pré-programados | planner orientado a goals/budget | P1 | 05 | |
| Recommendations/composer | `recommendationQueries` por profile (estático elevado; lista textual removida) | recomendações **contextuais** validadas | P1 | 06 | D2 ≠ aceite 06 |
| Presentation residual | entity/path profiles e hints | shape/schema-first | P2 | 07 | display maps path→label já limpos |
| Skills/help residual | endpoint hints em conteúdo editorial | runtime capability lookup | P2 | 08 | |
| Evals/rollout/cleanup | validação fragmentada | baseline/candidate R1-R11 | transversal | 09 | |

### Drift documental resolvido (2026-09-10)

- `capabilities.pathRules` não é mais CURRENT — ver plano 04.
- Cold path já é OpenAPI-first — ver plano 01.
- Recommendations estáticas textuais removidas; `recommendationQueries` ainda authority — ver plano 06.

## 5. Ordem de execução

### Onda A — congelar baseline e contratos — **ATENDIDO** (2026-09-10)

1. Inventariar consumidores e fallbacks atuais. → [`evidence/onda-a-inventory.md`](./evidence/onda-a-inventory.md)
2. Congelar dataset e métricas de routing offline + flow-family matrix. → [`evidence/onda-a-baseline/`](./evidence/onda-a-baseline/)
3. Hashes de conteúdo assistant no manifest; `openApiSchemaHash` / `actionCatalogHash` = `PENDING_RUNTIME` (plano 09).
4. Classificar nós → inventário §7.

### Onda B — routing universal — **EM_ANDAMENTO**

Plano 01: E1.S3 **ATENDIDO**; E1.S4 **SHADOW_ON** ([`evidence/e1-s4-registry-selection-shadow.md`](./evidence/e1-s4-registry-selection-shadow.md)). Nenhuma remoção final antes de `unknown external API` + metamorphic rename + divergências shadow explicáveis.

### Onda C — entendimento semântico — **PRONTO após início B**

Executar plano 02, com foco em pedidos longos, intents próximas, linguagem informal, typos e no-tool. Inventário intents: Onda A §6.

### Onda D — multi-turn e argument binding — **BLOQUEADO_SOFT por B**

Executar plano 03. Follow-up deve depender de contexto estruturado e schema, não de route substring.

### Onda E — capabilities e composition — **PARCIAL**

Executar planos 04 (restante: mini-catálogo `action.*`) e 05. **Não** reabrir cutover de `pathRules` (D1). Enrichment passa a ser decisão planner-driven sob budget.

### Onda F — UX inteligente — **PRONTO_APÓS_E**

Executar plano 06. Subir recomendações **contextuais** acima de `recommendationQueries` (que permanece só como fallback). Composer usa contexto + allowlist com budget.

### Onda G — apresentação e conteúdo residual — **PRONTO_APÓS_F**

Executar planos 07 e 08. Preservar copy/business rules; retirar somente conhecimento técnico duplicado.

### Onda H — cutover e limpeza — **CONTÍNUO**

Executar plano 09. Remover registries, predicates e mappings mortos somente após evidência de equivalência/superioridade. Ampliar corpus/hashes runtime a partir do freeze Onda A.

## 6. Métricas obrigatórias

Medir baseline/candidate, por família e global:

```text
task_decomposition_recall
action_top_k_recall
action_selection_accuracy
argument_extraction_accuracy
missing_required_argument_accuracy
false_tool_call_rate
unnecessary_follow_up_rate
multi_request_completion_rate
multi_turn_reference_accuracy
unknown_api_task_success_rate
metamorphic_rename_pass_rate
task_success_rate
safety_violation_rate
p50/p95_latency
llm_calls_per_turn
tokens_per_turn
tool_calls_per_turn
catalog_path_coupling_count
manual_intent_rule_count
```

## 7. Invariantes de segurança e negócio

Não migrar para decisão livre do LLM:

- RBAC e permissions;
- sensitivity/write/admin/destructive classification sem validação canônica;
- confirmation policy;
- URL/host executável;
- required/type/enum/format;
- factual verdicts e regras de domínio;
- regras de desenho/conformidade;
- limites operacionais, paginação máxima, payload caps, timeout e retries;
- secrets/config de provider.

## 8. Compatibilidade e rollout

Para cada fluxo de alto risco:

```text
CURRENT
-> BASELINE
-> candidate em shadow quando possível
-> divergência instrumentada
-> canary restrito
-> default candidate
-> fallback monitorado
-> cleanup do legado
```

Não manter fallback silencioso que esconda regressão. Toda queda para catálogo antigo deve ser observável.

## 9. Paridade transversal obrigatória

Cada plano deve avaliar explicitamente:

- send;
- stream;
- simulate;
- multi-turn;
- persist/reload/F5;
- histórico/replay;
- admin/debug/telemetry;
- MFE render-only quando apresentação estiver envolvida;
- Ajuda quando comportamento user-facing mudar.

## 10. Definition of Done global

A iniciativa só pode ser considerada concluída quando:

```text
UNKNOWN_EXTERNAL_API = PASS
METAMORPHIC_PROVIDER_PATH_OPERATION_RENAME = PASS
COMPOUND_LONG_REQUEST = PASS
MULTI_TURN_FOLLOW_UP = PASS
REQUIRED_ARGUMENT_CLARIFY = PASS
UNAUTHORIZED_WRITE_SAFETY = PASS
SEND_STREAM_SIMULATE_PARITY = PASS
PERSIST_RELOAD = PASS
R1_R11_RELEASE = PASS
NO_NEW_ENDPOINT_CATALOG = PASS
NO_MATERIAL_LATENCY_COST_REGRESSION_UNJUSTIFIED = PASS
RESIDUAL_PATH_COUPLING = explicitamente justificado ou zero no core genérico
```

## 11. Rastreabilidade macro

| Requisito | Decisão | Plano | Prova principal |
|---|---|---|---|
| RQ-01/RQ-12 | D-01/D-04 | 01, 09 | unknown API + metamorphic |
| RQ-02/RQ-03 | D-01 | 02 | decomposition + semantic siblings |
| RQ-04/RQ-05 | D-01/D-03 | 03 | multi-turn + args validator |
| RQ-06 | D-01/D-04 | 04 | dynamic capabilities from catalog |
| RQ-07 | D-02/D-03 | 05 | goal coverage + budget |
| RQ-08/RQ-13 | D-02 | 06 | grounded recommendation + LLM-call budget |
| RQ-09/RQ-10 | D-01 | 07, 08 | schema-first + invariant tests |
| RQ-11/RQ-14 | D-05 | 09 | parity + cleanup gates |
