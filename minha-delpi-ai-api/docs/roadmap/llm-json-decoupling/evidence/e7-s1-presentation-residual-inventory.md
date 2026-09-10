# E7.S1 — Inventário residual de presentation (schema/shape-first)

**Status:** `ATENDIDO` (2026-09-10)  
**Onda:** G (plano 07)  
**HEAD:** pós-Onda F (`e2e3325fa`+)  
**Escopo:** presentation residual — **não** routing técnico do plano 01  
**Freeze counts:** `tests/unit/domain/services/test_e7_s1_presentation_residual_inventory.py`

## Veredito

```text
RESIDUAL_INVENTORY = PASS
PATH_TO_LABEL_DISPLAY_NOT_REOPENED = PASS
SHAPE_DEFAULTS_PRESENT = PASS
PATH_ENTITY_SELECTION_STILL_LIVE = PASS
DEAD_ORPHANS_FLAGGED = PASS
NO_RUNTIME_MIGRATION = PASS
```

Dívida viva concentrada em **seleção de profile/table por path/entity**, não em labels path→display (já limpos).

## Contagens HEAD (freeze)

| Sinal | Valor |
|-------|------:|
| `pathRules` | **49** (E7.S4 −29) |
| `entityProfiles` | 34 |
| `entityTableProfiles` | 18 |
| `entityPathHints` | 139 |
| `tableProfiles` com `detect.pathContains` | **23** / 76 (E7.S4 −23) |
| `openapiShapeDefaults` keys | 9 (incl. `unknown`) |
| `pathEntityFallbacks` | **removido** (E7.S4) |
| `entitySets.schemaFirstMigratedProfiles` | **ledger populado** (E7.S4) |

## Matriz (resumo)

| ID | Artifact | Class | Live? |
|----|----------|-------|-------|
| P01 | `openapiShapeDefaults` | SCHEMA_DIRECT | LIVE |
| P02–P03 | shape equivalents / replaceable keys | DETERMINISTIC_POLICY | LIVE |
| P04 | `pathRules` (78) | SEMANTIC_PRESENTATION_METADATA | LIVE |
| P05 | `entityProfiles` (34) | SEMANTIC_PRESENTATION_METADATA | LIVE |
| P06 | `entityTableProfiles` | DETERMINISTIC_POLICY | LIVE |
| P07 | `profiles` especializados | SEMANTIC_PRESENTATION_METADATA | LIVE |
| P08 | `stackPlans` | DETERMINISTIC_POLICY | LIVE |
| P09 | `entityPathHints` | SEMANTIC_PRESENTATION_METADATA | LIVE |
| P10 | `pathEntityFallbacks=[]` | DEAD_CONTENT | DEAD |
| P11 | buckets migração vazios | DEAD_CONTENT | DEAD |
| C01 | `fieldFormats` | DETERMINISTIC_POLICY | LIVE (KEEP) |
| C02 | table detect por keys | DETERMINISTIC_POLICY | LIVE |
| C03 | table `pathContains` ×46 | SEMANTIC_PRESENTATION_METADATA | LIVE |
| C04–C06 | preferredColumns / priority / aliases | DETERMINISTIC_POLICY | LIVE |
| C07 | columnLabelDiscovery | LLM_COMPOSITION_CANDIDATE | LIVE (labels, não view) |
| O01 | scopes.byPathFragment | SEMANTIC_PRESENTATION_METADATA | LIVE |
| O03–O05 | routeTitles / framing / sections | UX_COPY / LLM_COMPOSITION_CANDIDATE | LIVE |
| R01–R05 | presenter_content schemaDriven/titles | UX_COPY / SCHEMA_DIRECT | LIVE |
| R06 | `compositeVisualSpecs` | DEAD_CONTENT | DEAD_RUNTIME |
| D01 | `data_interpretation` | UX_COPY | LIVE |

## Gaps vs TARGET

```text
TARGET: schema+payload → shape → presentationDecision → labels/formats → views
ATUAL:  entityProfiles/pathRules primeiro; shape derive só se replaceable/generic
```

- Table assembly ainda path-discriminated (46 detects).
- `routeFraming` estático vs síntese (R07-05) aberto.
- Aceites `UNKNOWN_API_PRESENTATION` / `PATH_RENAME_PRESENTATION` → E7.S2+.

## Não tocar

- path→label display já limpo (FieldLabelBundle / preferredColumns keys-only / titlesByPathFragment ausentes)
- `capabilities.pathRules` (plano 04)
- routing OpenAPI plano 01

## Famílias baseline E7.S2

scalar · paged_list · hierarchy · composite_analysis · document_export · unknown API · partially typed (+ path rename metamórfico)

## Próximo

**E7.S2** — baseline de presentation (R4/R5/R7/R8/R9/R11).
