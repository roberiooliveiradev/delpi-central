# E7.S3 — Shape defaults como caminho principal

**Status:** `ATENDIDO` (2026-09-10)  
**Onda:** G (plano 07)  
**Owner:** `OpenApiPresentationProfileDeriverService` + `ChatPresentationProfileResolveService`  
**Harness:** `tests/unit/domain/services/test_e7_s3_shape_defaults_primary_path.py`

## Veredito

```text
SCHEMA_SHAPE_DEFAULTS = PASS
SHAPE_ONLY_DERIVE = PASS
UNKNOWN_SHAPE_FALLBACK = PASS
PAYLOAD_INFER_SHAPE = PASS
EXTERNAL_NO_LOCAL_PROFILE = PASS
SPECIALIZED_ENTITY_PRESERVED = PASS
NO_LLM_PER_VISUAL = PASS
```

## Mudanças

| Antes | Depois |
|-------|--------|
| `can_derive` exigia entity+shape | shape sozinho basta |
| shape desconhecido → defaults vazios | `openapiShapeDefaults.unknown` (table-first) |
| sem shape/meta → generic text-first | `infer_shape_from_rows` via analyzer + `openapiShapeFromAnalyzer` |
| profileKey sempre `openapi:{entity}` | shape-only → `openapi:shape:{shape}` |

## Invariantes

- `product_stock` / `entityProfiles` especializados **não** cutover em S3 (E7.S4).
- Sem LLM no deriver.
- `fieldFormats` intocados.

## Próximo

**E7.S4** — cleanup `pathContains` / entity maps com equivalência comprovada.
