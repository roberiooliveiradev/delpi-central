# E11.S6 — Semantic authority + cleanup NLU path-teaching

**Status:** COMPLETE_GATE  
**Cobre:** RQ11-05 (RQ11-12 compound/live → E11.S9)

## Inventário (CUTOVER)

| Camada | Papel pós-S6 |
|---|---|
| `ChatTurnUnderstanding` + family mappers | Authority de **entendimento estruturado** (facet/kind/catalogToken) |
| `ChatIntentRouter` | Triagem de família transversal (RAG/web/operational/…) |
| `ChatTurnAnalysis` | LLM clarify\|execute\|narrate |
| OpenAPI Action Catalog | Authority de **seleção de action** |
| Product `_TOKEN_RULES` | **KEEP** — facets/intentBinding (não path HTTP) |
| Production `_TOKEN_RULES` | **KEEP** — kind semântico; `pathTokens` JSON **DELETED** |
| KPI `_TOKEN_RULES` | Vocabulary → `catalogToken`; virtual route sem pathMarkers |

## CUTOVER

- Virtual KPI route: `id`/`domain`/`intentBinding`/`continuityFacets`; **sem** `pathMarkers`/`operationIdMarkers`.
- Production: `pathTokens` removidos do bundle; `path_token_for` → `""`; selection só registry kind + allowlist.
- Capabilities catalog generator: key interna `pathHints` (sem lateral `pathMarkers`).
- Sufficiency synthetic plan: sem key `pathMarkers`.
- Gate `SEMANTIC_CONTENT_LATERAL_PATH_KEY` full-tree: **0** (antes 4).

## GENERALIZAÇÃO (unit)

| Caso | Resultado |
|---|---|
| KPI virtual sem markers laterais | PASS |
| Production path token vazio (todos kinds) | PASS |
| Product facet `stock` sem `/` | PASS |
| Bundle sem `pathTokens` | PASS |
| E2 family cutover + KPI route selection | PASS |

## Residual

- Heurísticas de vocabulary KPI/production/product permanecem (não escolhem path HTTP diretamente).
- `assistant_capabilities_catalog_generator` ainda usa hints de path **internos** (`pathHints`) para feature tagging — não content lateral key.
- R1/R2/R9 compound live: E11.S9 candidate fresco.
- Defaults smoke cred: E11.S8.
