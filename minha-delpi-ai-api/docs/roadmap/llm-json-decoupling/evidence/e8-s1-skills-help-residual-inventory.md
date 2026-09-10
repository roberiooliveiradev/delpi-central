# E8.S1 — Inventário residual skills/help (catálogos técnicos)

**Status:** `ATENDIDO` (2026-09-10)  
**Onda:** G (plano 08)  
**Escopo:** auditoria — **sem** mutação de JSON de conteúdo  
**Freeze:** `tests/unit/domain/services/test_e8_s1_skills_help_residual_inventory.py`

## Veredito

```text
RESIDUAL_INVENTORY = PASS
ROUTE_HINTS_STILL_ZERO = PASS
SKILL_PATHISH_HINTS_LIVE_DISPLAY = PASS
FEATURES_REQUIRED_ACTIONS_PATH_LIVE = PASS
NO_CONTENT_MUTATION = PASS
```

## Contagens HEAD (freeze)

| Sinal | Valor |
|-------|------:|
| skills total | **7** |
| `executionPathHint` path-like | **0** (E8.S2) |
| `executionDerivedKey` | **1** |
| features total | **21** |
| features com `requiredActions` path | **12** |
| tokens path em `requiredActions` | **26** |
| menções `METHOD /path` em `capabilities.json` | **8** |
| `capability_registry.routeHints` | **0** (E4 — não reabrir) |
| `external_action_responses.actionSelection` keys | **61** (→ E8.S4) |

## Matriz skills (`executionPathHint`)

| ID | key | hint | Classe | Live? | Nota |
|----|-----|------|--------|-------|------|
| S01 | `sql` | `POST /data/sql` | PATH_COUPLED / OPENAPI_DUPLICATE | display | Gate real = Python/`executionDerivedKey` |
| S02 | `drawing-analysis-delpi` | `GET /products/{code}/analyser` | PATH_COUPLED / OPENAPI_DUPLICATE | display | |
| S03 | `quality-action-plans-delpi` | `/quality/action-plans` | PATH_COUPLED | display | |
| S04 | `company-knowledge` | `search_knowledge_base` | UX_COPY | display | capability key |
| S05 | `tv-dashboard-copilot` | `tv_dashboard_copilot` | UX_COPY | display | |
| S06 | `document-vision-delpi` | `ChatDocumentVisionService` | UX_COPY | display | vazamento de classe |
| S07 | `technical-description-delpi` | Normas… | UX_COPY | display | editorial |

`policyFile` / labels / aliases / examples → **KEEP** (R08-02).

## Matriz help/features

| ID | Artifact | Classe | Live? | Cutover |
|----|----------|--------|-------|---------|
| H01 | `features_catalog.requiredActions` (paths) | PATH_COUPLED / OPENAPI_DUPLICATE | **authority help** | E8.S3 |
| H02 | `capabilities` HTTP em copy | UX_COPY + OPENAPI_DUPLICATE | catalog-answer | E8.S3 |
| H03 | `generation.pathRulesVersion` | DEAD naming | label | S6/doc |
| M01 | EAR `actionSelection` | PATH_COUPLED / POLICY | LIVE routing | E8.S4 |

## DEAD já limpo (não reabrir)

- `capabilities.pathRules` (E4)
- `capability_registry.routeHints` (E4.S5)

## Gaps vs TARGET

```text
skill editorial → ainda mostra path HTTP em 3 hints
help availability → ainda casa requiredActions por substring de path
EAR → copy misturada com selectors técnicos
```

## Próximo

**E8.S2** — skill catalog: trocar hints path-like por capability keys neutras (sem esconder limitações).
