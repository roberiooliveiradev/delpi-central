# Plano 10 — Zero mapa lateral por path/rota

**Prioridade:** P0  
**Status execução:** Onda I · **EM_ANDAMENTO** (docs/política 2026-09-11; implementação pendente)  
**Depende de:** Ondas A–H ATENDIDAS (`globalReleasePass=true`)  
**Evidência:** [`../evidence/execution-ledger.md`](../evidence/execution-ledger.md) · inventário abaixo  
**Objetivo perceptível:** nenhuma classificação, hint, factual, enrichment ou response map no `assistant/*.json` pode usar `pathMarkers` / pathContains / pathToken como **mapa lateral** paralelo ao OpenAPI indexado.

## Decisão de produto (2026-09-11)

```text
NENHUM MAPA LATERAL DEVE EXISTIR.
```

Revoga a disposição `JUSTIFIED_POLICY` para mapas de domínio/path no content do assistente.

Informação de rota/operation vem **somente** de:

```text
OpenAPI importado
→ Action Catalog persistido/indexado
→ metadata da action (tags, operationId, path do contrato, x-* se existirem)
```

JSON do assistente fica limitado a: UX/copy, policy transversal, vocabulário, caps/budgets — **nunca** catálogo ou mapa por path/endpoint.

## Inventário atual (débito aberto)

| Superfície | Uso residual | Destino |
|---|---|---|
| `api_route_domains.json` | `ChatOperationalApiDomainService.classify_path` | DELETE mapa; domínio via tag/metadata OpenAPI ou Action Catalog |
| `operational_factual_verdict.json` | `pathMarkers` por profile | DELETE; binding por `operationId` / actionId / schema |
| `operational_sufficiency_critic.json` | `pathMarkers` | DELETE; idem |
| `product_enrichment_composition.json` | `pathMarkers` | DELETE; goals + Action Catalog |
| `external_action_responses.json` | `pathMarkers` / `pathMarkersKey` | DELETE; schema-driven + content transversal |
| `openapi_tool_routing.json` | residual path markers | DELETE ou reduzir a policy sem path |
| `department_kpi_rules.json` | `pathToken` / pathContains | migrar para operationId/actionId/tags |

Consumidores típicos a religar:

- `ChatOperationalApiDomainService`
- `external_action_route_selection_service` (`classify_path`)
- factual verdict / sufficiency / enrichment / empty-rival responses

## Subetapas

### E10.S1 — Inventário + contrato alvo — **EM_ANDAMENTO**

**Fazer:** lista completa producers/consumers; contrato de domínio/label **sem** pathMarkers; testes que falham se `"pathMarkers"` reaparecer em content (exceto evidência histórica).

**Aceite:** inventário fechado; gate CI ou teste de ausência definido.

### E10.S2 — Domínio sem `api_route_domains`

**Fazer:** substituir `classify_path` por metadata do Action Catalog / OpenAPI tags; DELETE ou esvaziar `api_route_domains.json` path maps.

**Teste:** positive unknown provider; sibling api-delpi; negative sem reintroduzir pathMarkers.

### E10.S3 — Factual / sufficiency / enrichment / responses

**Fazer:** remover `pathMarkers` dos JSONs listados; consumers por `operationId`/`actionId`/schema.

### E10.S4 — KPI pathToken + limpeza final

**Fazer:** migrar `department_kpi_rules` para ids estáveis; audit gate zero `"pathMarkers"` em `app/content/pt-BR/assistant/**/*.json`.

### E10.S5 — Verify + docs canônicas

**Fazer:** atualizar `openapi-first-universal-tool-routing`, changelog, ledger; E9.S7 residuals sem JUSTIFIED para mapas laterais.

## Aceite da Onda I

```text
NO_LATERAL_PATH_MAP = PASS
API_ROUTE_DOMAINS_PATH_MAP_REMOVED = PASS
CONTENT_PATHMARKERS_COUNT = 0
DOMAIN_FROM_OPENAPI_OR_CATALOG = PASS
UNKNOWN_PROVIDER_STILL_WORKS = PASS
NO_NEW_PATH_MAP_SUBSTITUTE = PASS
```

## Proibições

- Não “justificar” de novo `pathMarkers` como policy permanente.
- Não criar `routeFamily` / `pathClass` / `capabilityGroup` por endpoint.
- Não mover o mapa para outro JSON com o mesmo papel.
- Não quebrar RBAC/required/schema — só remover o mapa lateral.
