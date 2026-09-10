# E7.S5 — Labels e formats schema-first

**Status:** `ATENDIDO` (2026-09-10)  
**Onda:** G (plano 07)  
**Harness:** `tests/unit/domain/services/test_e7_s5_labels_formats_schema_first.py`

## Veredito

```text
SCHEMA_FORMATS_WIRED = PASS
OPENAPI_CURRENCY_DATATYPE = PASS
META_FIELDFORMATS_OVERRIDE = PASS
JSON_FIELDFORMATS_FALLBACK = PASS
NO_LLM_FORMAT_INVENTION = PASS
```

## Gap corrigido (causa)

`ExternalActionResultBuildService.build_presentation` descartava OpenAPI:

```python
merge_meta_field_formats({}, data)  # antes
```

Agora:

```python
merge_meta_field_formats(
    host._column_labels.resolve_schema_formats(response_schema),
    data,
)
```

Pipeline canônico de formats:

```text
OpenAPI x-dataType / format
→ meta.fieldFormats (override)
→ fieldFormats JSON / inferência determinística
→ (não LLM)
```

Labels: `OpenAPI/meta → humanize → discovery` preservado; `schema_formats` propagado em `resolve_columns_for_items` / `_enrich_column`.

## Residuais

- `present()` não recebe `response_schema`; tipagem nesse path depende de `meta.fieldFormats` no payload (owner schema-first = `build_presentation`).
- Inferência por token (`valor`, `price`, …) permanece determinística (KEEP) — não é LLM.

## Testes

| Caso | Resultado |
|------|-----------|
| Positive: `x-dataType: currency` → `dataType` | PASS |
| Wiring: `build_presentation` → colunas tipadas | PASS |
| Sibling: meta override OpenAPI | PASS |
| KEEP: `sale_price` sem schema | PASS |
| Negative: `sku_ref` sem inventar currency via LLM | PASS |

## Próximo

**E7.S6** — titles/framing estáveis (metadata/action/schema; history/F5).
