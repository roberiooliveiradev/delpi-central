# E4.S2 — Baseline de capability discovery

**Status:** `ATENDIDO` (2026-09-10)  
**Onda:** E (plano 04)  
**Harness:** `tests/unit/domain/services/test_e4_s2_capability_discovery_baseline.py` (5 passed)

## Veredito

```text
DISCOVERY_BASELINE_FAMILIES = PASS
ACTION_TYPE_FILTER = PASS
HELP_ALLOWED_ACTION_IDS = PASS
PATHRULES_NOT_REQUIRED = PASS
```

## Famílias congeladas

| Family | Mensagem | Top capability |
|--------|----------|----------------|
| action_stock | estoque 10080001 | `action.product_stock` |
| action_search | busque terminais | `action.product_search` |
| action_description | ficha do produto | `action.product_description` |
| rag_norms | normas da empresa | `rag.company_knowledge` |
| web_search | pesquisa na web | `web.search` |
| skill_compliance | conforme a norma | `skill.technical_description_compliance` |
| transform_reason | resuma | `transform.reason` |
| help_question | o que você pode fazer? | *(sem hit no registry — help é Action Catalog)* |

## Drift observável (não corrigir no freeze)

- `política`/`politica` **não** aciona `rag.company_knowledge` (whenToUse com acento vs normalize).
- Help capabilities não passa pelo discovery registry — superfície separada (correto p/ TARGET).

## Próximo

**E4.S3** — consolidar `uxCapability` / lacunas de metadata.
