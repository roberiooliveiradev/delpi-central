# E4.S3 — Semantic metadata / uxCapability

**Status:** `ATENDIDO` (2026-09-10)  
**Onda:** E (plano 04)  
**Harness:** `tests/unit/domain/services/test_e4_s3_ux_capability_contract.py` + `test_capability_ux_classifier_service.py`

## Contrato canônico

```json
{
  "category": "Estoque de produto | … | Outras consultas",
  "examples": ["…"],
  "source": "entity_shape|keyword|persisted|default|empty",
  "confidence": "high|medium|low"
}
```

- Materializado em `delpi_metadata.uxCapability` no import (`CapabilityUxClassifierService.attach_to_action`).
- Help lê via `resolve_ux_capability` (classifica on-the-fly se ausente).
- Haystack **exclui path** — path/operationId rename metamórfico não muda família quando entity/shape ou summary estáveis.
- **Não** inventa `x-delpi.capabilityGroup`.

## Aceite

```text
UX_CAPABILITY_CONTRACT = PASS
PATH_NOT_AUTHORITY = PASS
ENTITY_SHAPE_RENAME = PASS
UNKNOWN_FALLBACK_OUTRAS = PASS
NO_CAPABILITY_GROUP = PASS
R04-03 = ATENDIDO
```

## Próximo

**E4.S4** — dynamic capability view (help já Action Catalog; fechar gaps discovery).
