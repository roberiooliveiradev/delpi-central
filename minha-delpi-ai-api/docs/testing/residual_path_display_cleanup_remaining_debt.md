# Residual path→display — dívidas restantes

**Plano vigente:** `~/.cursor/plans/residual_path_display_cleanup_28b9adee.plan.md`  
**Plano STALE (parcialmente absorvido):** `~/.cursor/plans/residual_path_catalogs_cleanup_7f3a9c21.plan.md`  
**BASE:** `c20064c06` · **HEAD ao documentar:** `ee4a43c0e`  
**Veredito atual:** `PASS_WITH_DOCUMENTED_DEBT` (D4 STREAM/SIMULATE fechado)  
**Live:** SEND / F5 / HISTORY / STREAM / SIMULATE = PASS  
(`docs/testing/evidence/residual_path_display_live_surfaces.json`, `residual_path_display_stream_simulate.json`)

Este arquivo é a lista **canônica do que ainda falta** após o cutover/cleanup/generalização de path→display. Não reabre o kill de catálogos já removidos.

---

## Fechado (não refazer)

| Domínio | Estado | Evidência |
|---------|--------|-----------|
| Action labels sem `pathLabels` | PASS | E1 + smoke inprocess |
| Titles sem fragment maps / `pathTitles` | PASS | E2 |
| `stackPresentationPlan` per-response | PASS | E3 |
| MFE render-only + mirrors `routeTitles`/`routeFraming` | PASS | E4 + E13.S3 |
| Scopes API↔MFE sync | PASS | E13.S4 |
| Field formats KEEP (OPENAPI_COVERED=0) | PASS | E6 |
| Recommendations producer turno (delta LLM=0) | PASS | E16 + live recs |
| Field-label parity table/chart/KPI/insight | PASS | E8 |
| Locale pt-BR coverage (551/551) | PASS | E11 |
| Ajuda features/capabilities | PASS | E18.S1 |
| Live SEND + F5/HISTORY + smoke HTTP | PASS | live_surfaces + smoke |
| Live STREAM + SIMULATE (D4) | PASS | stream_simulate |
| W-ROUTING charter + plano-filho (docs only) | PASS | `w_routing_charter.json` |

---

## Dívidas abertas

### D1 — `capabilities.pathRules` (KEEP)

| | |
|--|--|
| **Status** | BLOQUEADO / dívida consciente |
| **Por quê** | H-CAP-01..05 não justificaram `x-delpi.capabilityGroup`; E5 decidiu KEEP |
| **Não fazer** | Introduzir `capabilityGroup` ou apagar `pathRules` sem inventário Action Catalog |
| **Próximo plano** | Charter próprio: classificação de categorias UX no Action Catalog → cutover consumer → DELETE pathRules |
| **Evidência** | `docs/testing/evidence/residual_path_display_e5_capability_hcap.json` |

### D2 — Cleanup do JSON estático de recommendations

| | |
|--|--|
| **Status** | DEFERRED |
| **Por quê** | Producer eleva `recommendationQueries` no turno; lista `recommendations` textual ainda é LEGACY_FALLBACK para perfis sem queries |
| **Pronto para cleanup quando** | 100% dos profiles usados em produção tiverem `recommendationQueries` (ou producer equivalente) + eval negativo |
| **Não fazer** | Remover static agora e deixar profile órfão sem próximo passo |
| **Evidência** | `residual_path_display_e16_recommendations_producer.json` |

### D3 — Locale EN==pt stubs (api-delpi)

| | |
|--|--|
| **Status** | BACKLOG qualidade OpenAPI (fora de path→display) |
| **Contagem** | ~28 ops com `locale.en.summary == locale.pt-BR.summary` |
| **Não misturar** | Com kill de catálogos de display do chat |
| **Owner** | api-delpi / `tv_route_audience.json` + polish locale |

### D4 — STREAM / SIMULATE formal

| | |
|--|--|
| **Status** | PASS |
| **Feito** | Harness `scripts/smoke_residual_path_display_stream_simulate.py` + fix simulate passa `allowedActionIds` do binding do agente no sandbox |
| **Evidência** | `docs/testing/evidence/residual_path_display_stream_simulate.json` |
| **Aceite** | STREAM SSE e SIMULATE admin com `stackPresentationPlan` / tabela e sem leak técnico EN |

### D5 — Evals R1–R11 corpus completo

| | |
|--|--|
| **Status** | NÃO RODADO como corpus formal |
| **Feito** | Unit + smoke + live P0 |
| **Gap** | `BASELINE_RUN_ID` / `CANDIDATE_RUN_ID` nulos no verify-final |
| **Quando** | Se houver regressão de inteligência/routing/display em produção; senão opcional |

---

## Fora de escopo (não é dívida deste plano)

| Item | Destino |
|------|---------|
| `operational_route_registry` / `pathMarkers` | W-ROUTING (`w_routing_pathmarkers_*.plan.md`) |
| `presentation_profiles.pathRules` / pathContains | Routing / presentation detect — charter separado |
| MegaLabelService / LLM por visual | Proibido (D-07 do plano) |
| Commit/push como DoD do plano antigo | Superado — commits já realizados por pedido explícito |

---

## Ordem sugerida para fechar

```text
1. D2 cleanup recommendations static (quando coverage de profiles OK)
2. D1 capabilities pathRules (plano novo, maior risco)
3. D3 EN==pt (backlog api-delpi paralelo)
4. D5 evals corpus (sob demanda)
```

---

## Referências de evidência

| Artefato | Uso |
|----------|-----|
| `docs/testing/evidence/residual_path_display_e10_verify_final.json` | Veredito C/C/G |
| `docs/testing/evidence/residual_path_display_live_surfaces.json` | Live SEND/F5 |
| `docs/testing/evidence/residual_path_display_stream_simulate.json` | Live STREAM/SIMULATE (D4) |
| `docs/testing/evidence/residual_path_catalogs_7f3a9c21_residual_verify.json` | Residual do plano STALE |
| `docs/testing/evidence/w_routing_charter.json` | Charter routing |
| `scripts/smoke_catalog_display_openapi.py` | Smoke inprocess+http (`message` field) |
| `scripts/smoke_residual_path_display_stream_simulate.py` | Smoke STREAM+SIMULATE |
