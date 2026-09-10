# E7.S2 — Baseline de presentation (shape/schema-first)

**Status:** `ATENDIDO` (2026-09-10)  
**Onda:** G (plano 07)  
**Harness:** `tests/unit/domain/services/test_e7_s2_presentation_baseline.py`  
**Inventário:** [`e7-s1-presentation-residual-inventory.md`](./e7-s1-presentation-residual-inventory.md)

## Veredito

```text
PRESENTATION_BASELINE_FROZEN = PASS
UNKNOWN_API_OPENAPI_DERIVED = PASS (5 famílias)
PATH_RENAME_STABLE_FOR_UNKNOWN = PASS
SPECIALIZED_ENTITY_GAP_DOCUMENTED = PASS (product_stock)
SHAPE_ANALYZER_PAYLOAD_FAMILIES = PASS
NO_LLM_PER_VISUAL = PASS
```

## Corpus (authority atual)

| Família | Entity/shape | openapiDerived? | View policy |
|---------|--------------|-----------------|-------------|
| scalar | ext_acme_kpi / scalar | sim | kpi_when_available |
| paged_list | ext_acme_orders / paged_list | sim | table_when_available |
| hierarchy | ext_acme_bom / hierarchy | sim | tree_when_available |
| composite_analysis | ext_acme_dossier / composite | sim | text_when_available |
| document_export | ext_acme_export / document_export | sim | text_when_available |
| specialized_stock_gap | product_stock / paged_list | **não** (stock JSON) | table (perfil stock) |

Metamórfico: `path_a` ≠ `path_b` com mesmo entity/shape → mesmo `profileKey` nas 5 unknown APIs.

## Dimensões (baseline TU — não eval live completo)

| Dim | Sinal no harness |
|-----|------------------|
| R4 | defaults/shape úteis sem profile local |
| R5 | viewPolicy + analyzer `recommended` |
| R7 | N/A parcial (sem multi-surface render neste TU) |
| R8 | path rename unknown estável |
| R9 | famílias do pedido cobertas no corpus |
| R11 | deriver sem LLM |

## Gap material (E7.S3–S4)

`entityProfiles` / pathRules ainda impedem derive OpenAPI em entidades DELPI especializadas (ex.: `product_stock`).

## Próximo

**E7.S3** — fortalecer `openapiShapeDefaults` + analyzer como caminho principal para schema desconhecido.
