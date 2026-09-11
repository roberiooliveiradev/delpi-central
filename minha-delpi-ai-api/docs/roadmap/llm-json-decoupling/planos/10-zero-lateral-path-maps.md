# Plano 10 — Zero mapa lateral por path/rota

**Prioridade:** P0  
**Status execução:** Onda I · **HISTÓRICO / ACEITE INVALIDADO POR DRIFT**  
**Plano corretivo vigente:** [`11-corrective-cutover-generalization-cleanup.md`](./11-corrective-cutover-generalization-cleanup.md)  
**Objetivo original:** nenhuma classificação, hint, factual, enrichment ou response map usa catálogo técnico paralelo ao OpenAPI/Action Catalog.

## Decisão de produto

```text
NENHUM MAPA LATERAL OU SUBSTITUTO SEMÂNTICO DEVE SER AUTHORITY.
```

A Onda I removeu diversas chaves laterais de `assistant/*.json` e executou smoke conhecido. Essa evidência continua válida para afirmar que determinadas **chaves JSON** foram removidas naquele estado, mas não prova a remoção da autoridade conceitual.

## EXECUTION_DRIFT pós-implementação

Uma revisão arquitetural posterior encontrou:

1. `ApiRouteDomainInferenceService._DOMAIN_RULES` com fragments de path conhecidos, portados do antigo mapa JSON;
2. `ParameterStrategyInferenceService` escolhendo strategy por path/operationId depois do DELETE do catálogo;
3. continuidade/route segment derivada de path-tail/operationId inventory;
4. `route.operationIds` como catálogo técnico paralelo residual;
5. gate E10 procurando nomes de chaves específicas, sem detectar representações equivalentes em Python/TS;
6. `UNKNOWN_PROVIDER_STILL_WORKS` baseado em evidência E9.S10 anterior às mudanças da Onda I;
7. smoke `unknown_safe_negative` usando mensagem sem sentido, que é negative/no-tool e **não** unknown external API.

## Reclassificação do aceite anterior

| Critério antigo | Estado histórico | Estado vigente |
|---|---|---|
| `CONTENT_PATHMARKERS_COUNT = 0` | PASS para as chaves verificadas | PASS histórico |
| `API_ROUTE_DOMAINS_PATH_MAP_REMOVED` | JSON removido | **FAIL conceitual** — mapa reapareceu em Python |
| `DOMAIN_FROM_OPENAPI_OR_CATALOG` | path do contrato usado para inferência | **PARTIAL** — path continua semantic authority |
| `UNKNOWN_PROVIDER_STILL_WORKS` | E9.S10 offline | **INCONCLUSIVE** para candidate final |
| `NO_NEW_PATH_MAP_SUBSTITUTE` | declarado PASS | **FAIL** |
| `LIVE_PRODUCT_STOCK_DOMAIN` | PASS conhecido | PASS histórico, não generalização |
| `LIVE_DEPARTMENT_KPI_SIBLING` | PASS conhecido | PASS histórico, não metamorphic |
| `LIVE_UNKNOWN_SAFE` | PASS negativo/no-tool | não conta como unknown API |

## Por que o gate antigo foi insuficiente

O gate validava ausência de nomes como:

```text
pathMarkers
pathToken
pathContains
pathRules
```

Isso não detecta equivalentes como:

```text
_DOMAIN_RULES = [(domain, ("/known/path", ...))]
if "/products/" in path: strategy = ...
routeSegment = normalize(path_tail)
operationIds = [known_operation]
```

O enforcement correto precisa distinguir uso técnico legítimo de `path/operationId` de **decisão semântica hardcoded**.

## Ação corretiva

A Onda I não deve ser reexecutada isoladamente. Seus drifts foram absorvidos pela Onda J:

- E11.S1 — Architecture Enforcement semântico;
- E11.S2 — domain classification sem path authority;
- E11.S3 — argument binding schema-driven;
- E11.S4 — multi-turn sem path/operationId continuity;
- E11.S5 — registry/operationIds sem routing authority;
- E11.S9 — unknown external API + metamorphic no candidate final;
- E11.S10 — residual scan + docs + verify-final.

## Regra de fechamento

Este plano só pode voltar a ser considerado atendido como objetivo arquitetural quando o Plano 11 provar no **candidate final**:

```text
PATH_COUPLED_RUNTIME_RULES = 0 para authorities removíveis
ENDPOINT_STRATEGY_RULES = 0
MULTI_TURN_PATH_COUPLING = 0
NO_TECHNICAL_REGISTRY_AUTHORITY = PASS
UNKNOWN_EXTERNAL_API = PASS
METAMORPHIC_RENAME = PASS
RESIDUAL_SCAN = PASS
```

Evidências antigas permanecem preservadas em `../evidence/` como histórico; não apagá-las nem renomeá-las para simular novo candidate.
