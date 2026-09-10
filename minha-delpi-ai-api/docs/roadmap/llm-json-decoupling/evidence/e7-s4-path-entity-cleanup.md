# E7.S4 — Path/entity rules cleanup (equivalência shape/OpenAPI)

**Status:** `ATENDIDO` (2026-09-10)  
**Onda:** G (plano 07)  
**Harness:** `tests/unit/domain/services/test_e7_s4_path_entity_cleanup.py`

## Veredito

```text
PATH_ENTITY_SAFE_CUTOVER = PASS
PATH_RENAME_PRESENTATION = PASS (entity+shape)
SPECIALIZED_ENTITY_PRESERVED = PASS
DEAD_ORPHANS_REMOVED = PASS
SCHEMA_FIRST_MIGRATED_LEDGER = PASS
```

## Delta

| Sinal | Antes (E7.S1) | Depois |
|-------|--------------:|-------:|
| `pathRules` | 78 | **49** (−29 replaceable) |
| table `detect.pathContains` | 46 | **23** (−23 redundantes) |
| `pathEntityFallbacks` | `[]` | **removido** |
| `compositeVisualSpecs` | órfão | **removido** |
| `schemaFirstMigratedProfiles` | `[]` | **54 ids** (ledger) |

## Não tocado (domínio)

- `entityProfiles` especializados (`product_stock`, analyser, factory_status, trees…)
- catch-alls (`/production/`, `/quality/`, `/hr/`, …)
- divergências (`/pedidos-venda-abertos*`, `/propostas-comerciais`, `/dashboard/department-idd`)
- table detects com colisão de keys (allocation-gaps ↔ finished-without-consumption, factory*)

## Wiring

`build_resolved_profile`: se entity ausente, resolve entity do path **antes** de `shape_for_entity` (path-only alinhado ao happy path OpenAPI).

## Próximo

**E7.S5** — labels e formats (FieldLabelBundle / schema-first formats).
