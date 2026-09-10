# Residual path→display — dívidas restantes

**Plano vigente:** `~/.cursor/plans/residual_path_catalogs_3a3dbf91.plan.md`  
**BASE:** `c20064c06` · **HEAD ao documentar (pré-D1):** `13dbec11a`  
**Veredito atual:** `PASS` (D1 H-CAP-04 = A — pathRules removidos)  
**Live:** revalidar E10 após rebuild AI

Este arquivo é a lista **canônica do que ainda falta** após o cutover/cleanup/generalização de path→display.

---

## Fechado (não refazer)

| Domínio | Estado | Evidência |
|---------|--------|-----------|
| Action labels sem `pathLabels` | PASS | E1 + smoke |
| Titles sem fragment maps | PASS | E2 |
| `stackPresentationPlan` per-response | PASS | E3 |
| MFE render-only + mirrors | PASS | E4 + E13 |
| Field formats KEEP | PASS | E6 |
| Recommendations `recommendationQueries` | PASS | E16 + D2 |
| Field-label parity | PASS | E8 |
| Locale pt-BR coverage | PASS | E11 |
| Live STREAM/SIMULATE | PASS | D4 |
| **capabilities.pathRules → Action Catalog uxCapability (D1)** | **PASS** | E5 H-CAP-04 A + classifier + DELETE pathRules |
| Dead `title_for_path` | PASS | E9 |
| MFE merge title sem hardcode Estoque | PASS | E8 |

---

## Dívidas abertas

### D3 — Locale EN==pt stubs (api-delpi)

| | |
|--|--|
| **Status** | BACKLOG qualidade OpenAPI (fora de path→display) |
| **Owner** | api-delpi |

### D5 — Evals R1–R11 corpus completo

| | |
|--|--|
| **Status** | NÃO RODADO como corpus formal |
| **Quando** | sob demanda |

---

## Fora de escopo

| Item | Destino |
|------|---------|
| `presentation_profiles.pathRules` / pathMarkers | W-ROUTING |
| `segment_map` path-tail humanizer | LEGITIMATE_KEEP (fallback labels) |
| `assistant_capabilities_catalog_generator._PATH_RULES` | featureId index (não UX capabilities) |

---

## Referências

| Artefato | Uso |
|----------|-----|
| `residual_path_display_e5_hcap04_decision.json` | Decisão A H-CAP-04 |
| `residual_path_display_e0_rebaseline.json` | Dead code E0 |
| `capability_ux_classification.json` | Regras determinísticas import/runtime fallback |
| `scripts/smoke_catalog_display_openapi.py` | Smoke HTTP |
