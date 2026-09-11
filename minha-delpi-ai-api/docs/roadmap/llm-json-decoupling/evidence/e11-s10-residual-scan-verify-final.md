# E11.S10 — Residual scan + VERIFY_FINAL

**Status:** COMPLETE_GATE + **VERIFY_FINAL=PASS**  
**FINAL_CANDIDATE_GIT_SHA (runtime):** `782a49721319571f0fe4733d59b8a5cc65ac4c04`  
**HEAD docs/fechamento:** `6b27e54ea02625848d9f6c392f39de7b66d10100` (docs-only; runtime candidate inalterado)  
**SEMANTIC_* full-tree:** 0 (revalidado `audit_architecture_phase3.py --check-semantic-debt`)

## Busca residual (conceito)

Escopo: `app/` + `scripts/` (excl. docs/tests/fixtures). Classificação por hit material.

| Conceito | Hits (aprox.) | Classificação | Notas |
|---|---|---|---|
| `pathMarkers` em content JSON | 0 (só denylist `openapi_tool_routing.gate`) | CONTRACT_LEGITIMATE | gate anti-regressão |
| `pathMarkers` em código | ~16 | TRANSVERSAL_POLICY_KEEP / observer | leitura soft; KPI virtual sem markers (E11.S6); anomaly optional |
| `pathToken` / `pathContains` / `pathRules` em content | 0 (pathRules deleted E10) | — | code readers = compat vazia |
| `pathTokens` production JSON | 0 (E11.S6 DELETE) | REMOVE_NOW done | |
| `_DOMAIN_RULES` | 0 | REMOVE_NOW done (E11.S2) | |
| `route.operationIds` authority | 0 runtime | TRANSVERSAL_POLICY_KEEP | `operationIdsRole=observer`; CI coverage |
| Catalog `operationId` metadata | N | CONTRACT_LEGITIMATE | Action Catalog técnico |
| path→parameterStrategy | 0 | REMOVE_NOW done (E11.S3 stub) | |
| path-tail routeSegment / inventory | 0 authority | TRANSVERSAL_POLICY_KEEP | stubs vazios; facets estruturadas |
| `recommendationQueries` | profiles JSON | TRANSVERSAL_POLICY_KEEP | LEGACY_FALLBACK + exit criteria (E11.S7) |
| `_TOKEN_RULES` mappers | 3 files | TRANSVERSAL_POLICY_KEEP | facet/kind/catalogToken — não path HTTP |
| smoke cred defaults | 0 | REMOVE_NOW done (E11.S8) | |
| TODO/FIXME materials no core routing | 0 material | DOC_HISTORY_ONLY / TEST_ONLY | |
| FS em domain (PDF/drawing/lint/content) | vários | CONTRACT_LEGITIMATE / backlog CA | não restaura mapa lateral semântico; fora do objetivo P0 desta iniciativa |
| `SEMANTIC_CONTENT_LATERAL_PATH_KEY` | 0 | PASS | |

### REMOVE_NOW nesta subetapa

Nenhum hit adicional exigiu DELETE de código: débitos de authority já cortados em S2–S8. Residual restante é observer/compat/LEGACY com exit criteria.

### BLOCKED_WITH_EVIDENCE

Nenhum bloqueio material que conflite com o objetivo «zero authority de mapa lateral / OpenAPI-first».  
CA filesystem residual = backlog de engenharia, **não** reabre D11-01..05.

## Adversarial (plano §9)

| Pergunta | Resposta |
|---|---|
| Mapa JSON só movido para Python? | **Não** — path→domain / strategy / path-tail removidos; facets/catalogToken |
| path→domain authority? | **Não** (`SEMANTIC_PATH_DOMAIN_MAP=0`) |
| endpoint→parameterStrategy? | **Não** (`SEMANTIC_ENDPOINT_PARAMETER_STRATEGY=0`) |
| follow-up path/operationId? | last-resort path só se facet ausente; authority = facets |
| operationIds ensina routing? | **Não** (observer; cutover permanente) |
| unknown API exige código novo? | **Não** — S14 live logistics PASS |
| recommendationQueries oracle? | **Não** — LEGACY_FALLBACK + exit |
| capability metadata inventada? | **Não** — method+sensitivity |
| smoke secrets versionados? | **Não** |
| residual sem classificação? | **Não** — tabela acima |

## Definition of Done Onda J

```text
CUTOVER_RESULT = PASS
GENERALIZATION_RESULT = PASS
CLEANUP_RESULT = PASS
UNKNOWN_EXTERNAL_API = PASS_ON_FINAL_CANDIDATE
METAMORPHIC_RENAME = PASS_ON_FINAL_CANDIDATE
ARGUMENT_SCHEMA_AUTHORITY = PASS
MULTI_TURN_STRUCTURED_STATE = PASS
SEMANTIC_AUTHORITY_SINGLE_OWNER = PASS
CONTEXTUAL_RECOMMENDATIONS = PASS
CAPABILITY_SECURITY_METADATA = PASS
CLEAN_ARCHITECTURE = PASS
SECURITY_HYGIENE = PASS
SEND_STREAM_SIMULATE_UI = PASS
PERSIST_RELOAD_F5 = PASS
R1_R11_REQUIRED_DIMENSIONS = PASS
RESIDUAL_SCAN = PASS
DOCS_MATCH_FINAL_HEAD = PASS
COMPLETE_GATE = PASS
VERIFY_FINAL = PASS
FINAL_RESULT = PASS
```

Evidência candidate: [`e11-s9-final-candidate.md`](./e11-s9-final-candidate.md)

## Pós-programa (não bloqueia)

- DELETE arrays `operationIds` observer quando CI coverage migrar 100% para facets;
- DELETE profiles `recommendationQueries` após exit criteria canary;
- Migrar IO FS de lint/generator domain → infrastructure (backlog CA).
