# Plano 07 — Presentation residual -> schema/shape-first

**Prioridade:** P2  
**Status execução:** Onda G · Plano 07 **ATENDIDO** (E7.S1–S7) · próxima plano 08 · display path→label **não** reabrir  
**Evidência:** [`../evidence/e7-s1-presentation-residual-inventory.md`](../evidence/e7-s1-presentation-residual-inventory.md) · [`../evidence/e7-s2-presentation-baseline.md`](../evidence/e7-s2-presentation-baseline.md) · [`../evidence/e7-s3-shape-defaults-primary-path.md`](../evidence/e7-s3-shape-defaults-primary-path.md) · [`../evidence/e7-s4-path-entity-cleanup.md`](../evidence/e7-s4-path-entity-cleanup.md) · [`../evidence/e7-s5-labels-formats-schema-first.md`](../evidence/e7-s5-labels-formats-schema-first.md) · [`../evidence/e7-s6-titles-framing-stable.md`](../evidence/e7-s6-titles-framing-stable.md) · [`../evidence/execution-ledger.md`](../evidence/execution-ledger.md)  
**Objetivo perceptível:** novas actions e APIs devem produzir apresentação útil sem exigir profile, path rule, title map ou presenter dedicado por endpoint.

**HEAD revalidado:** pós-E7.S3 (`8d7836483`+)

## CURRENT

Fontes prioritárias:

- `presentation_profiles.json`;
- `column_labels.json`;
- `product_operational_content.json`;
- `presenter_content.json`;
- `data_interpretation.json`;
- consumers de `pathContains`, entity/profile maps, table profiles, titles/framing e field formats.

O trabalho anterior já reduziu parte dos catálogos de display. Este plano trata somente dívida residual; não recriar o que já foi removido.

## TARGET

```text
responseSchema + payload + action metadata
-> shape/data analysis
-> presentationDecision/renderPlan
-> FieldLabelBundle / formats
-> views
-> contextual prose via síntese existente
```

Perfis especializados permanecem opcionais quando há necessidade real de domínio, nunca requisito para uma API funcionar.

## Requisitos

| ID | Requisito |
|---|---|
| R07-01 | Preferir shape/schema a path/entity para seleção genérica de view. |
| R07-02 | Preservar `fieldFormats` e policies determinísticas onde schema não basta. |
| R07-03 | Remover `pathContains` residual quando existir sinal canônico equivalente. |
| R07-04 | Não criar chamada LLM por título/visual. |
| R07-05 | Contextual framing pode usar síntese LLM já existente. |
| R07-06 | MFE deve renderizar contrato materializado, sem redecidir semântica. |

## Etapas

### E7.S1 — Inventário residual — **ATENDIDO** (2026-09-10)

**Fazer:** classificar cada key relevante como `SCHEMA_DIRECT`, `DETERMINISTIC_POLICY`, `SEMANTIC_PRESENTATION_METADATA`, `LLM_COMPOSITION_CANDIDATE`, `UX_COPY` ou `DEAD_CONTENT`.

**Feito:** inventário `e7-s1-presentation-residual-inventory.md` + freeze de contagens (`pathRules=78`, `entityProfiles=34`, table `pathContains=46`, shape defaults=8). Órfãos: `pathEntityFallbacks`, `schemaFirstMigratedProfiles`, `compositeVisualSpecs`.

**Não fazer:** tocar routing técnico do plano 01 — **respeitado**.


### E7.S2 — Baseline de presentation — **ATENDIDO** (2026-09-10)

Cobrir scalar, paged list, hierarchy, composite analysis, document export, unknown API e payloads parcialmente tipados.

**Feito:** corpus 6 famílias em `test_e7_s2_presentation_baseline.py`; unknown API openapiDerived + path rename estável; gap `product_stock` documentado; analyzer payload families; R4/R5/R8/R9/R11 baseline TU.

Medir R4/R5/R7/R8/R9/R11 — **baseline TU PASS** (R7 parcial sem multi-surface).


### E7.S3 — Shape defaults como caminho principal — **ATENDIDO** (2026-09-10)

**Fazer:** validar/fortalecer `openapiShapeDefaults` e shape analyzer; garantir fallback útil para schema desconhecido.

**Feito:** derive shape-only; `unknown` defaults; `infer_shape_from_rows` + `openapiShapeFromAnalyzer`; `rows=` em `build_resolved_profile`. Especializados (`product_stock`) preservados.

**Teste:** provider externo scalar/list/hierarchy sem profile local — PASS.


### E7.S4 — Path/entity rules cleanup — **ATENDIDO** (2026-09-10)

**Fazer:** substituir `pathContains` e entity maps por shape/schema/metadata canônica quando houver equivalência comprovada; manter exceção especializada somente com requisito de domínio documentado.

**Feito:** −29 `pathRules` replaceable; −23 table `pathContains` redundantes; DELETE órfãos; ledger `schemaFirstMigratedProfiles`; resolve entity-from-path antes de shape. `entityProfiles` especializados **não** cutover.

**Teste:** metamorphic path rename (entity+shape) — PASS; stock negativo — PASS.


### E7.S5 — Labels e formats

**Status:** **ATENDIDO** (2026-09-10) — evidência [`../evidence/e7-s5-labels-formats-schema-first.md`](../evidence/e7-s5-labels-formats-schema-first.md)

**Feito:** `build_presentation` wiring `resolve_schema_formats` → `_active_schema_formats`; colunas propagam `schema_formats`; meta override + JSON/inferência fallback; sem LLM de tipo.

**Não fazer:** LLM decidir tipo monetário/percentual sem validação.

### E7.S6 — Titles/framing

**Status:** **ATENDIDO** (2026-09-10) — evidência [`../evidence/e7-s6-titles-framing-stable.md`](../evidence/e7-s6-titles-framing-stable.md)

**Feito:** write-once de título materializado (`titleSource` no metadata); F5/path rename não reinferem; `fallbackTitle` de policy > reinferência path/shape; framing permanece campo separado.

**Teste:** history/F5 não reinfere título materializado — PASS.

### E7.S7 — MFE render-only e cleanup

**Status:** **ATENDIDO** (2026-09-10) — evidência [`../evidence/e7-s7-mfe-render-only-cleanup.md`](../evidence/e7-s7-mfe-render-only-cleanup.md)

**Feito:** remove espelho `product_operational_content.json` + sync do MFE; testes render-only (profileKey > path; unknown genérico). Residuais `routeKeyFromPath` / `showIn` diferidos.

**Teste:** send/stream/reload + render parity — PASS (MFE lê contrato; titles write-once no backend).

## Invariantes

- `fieldFormats`, table ordering, limits e policies não migram para LLM sem motivo.
- Factual/business interpretation continua grounded.
- Um profile especializado não pode impedir fallback genérico.

## Aceite

```text
UNKNOWN_API_PRESENTATION = PASS
PATH_RENAME_PRESENTATION = PASS
SCHEMA_SHAPE_DEFAULTS = PASS
NO_LLM_PER_VISUAL = PASS
MFE_RENDER_ONLY = PASS
PERSIST_RELOAD = PASS
```
