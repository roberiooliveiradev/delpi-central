# Supplier enrichment — comparison domain contract (S1)

> **Status: IMPLEMENTED (domain only).** SUPPLIES-ENRICHMENT-01 S1.
> Escopo: engine determinística de comparação em `supplies-api`, sem HTTP,
> sem persistência, sem provider externo, sem escrita ERP.
> Fonte do mapeamento SA2/SX3: `api-delpi/docs/integrations/protheus-rest-supplier-post-field-matrix.md`.

## Localização

```text
supplies-api/app/domain/supplier_enrichment/
  __init__.py        — exports públicos
  models.py          — snapshots, propostas, review, enums de estado
  field_mapping.py   — FieldSpec + política CNPJ_SA2_MAPPING_V1 (limites SX3)
  comparison.py      — compare_supplier_snapshots (engine determinística)
```

O domínio é framework-free: nenhum import de Flask, requests, psycopg ou SDK.

## Modelo

| Conceito | Papel |
|---|---|
| `SupplierRef` | identidade SA2 (code 6 dígitos + store 2 dígitos) |
| `CanonicalSupplierSnapshot` | estado atual lido via api-delpi; `baseline_reference` para stale-check futuro |
| `ExternalRegistrySnapshot` | retorno do provider CNPJ autorizado; `fields` indexados por `source_field` externo |
| `SupplierFieldProposal` | resultado por campo: valores brutos preservados + estado + elegibilidade + decisão `PENDING` |
| `SupplierEnrichmentComparison` | resultado determinístico (proposals + summary) |
| `SupplierEnrichmentReview` | envelope da comparação; `review_id`/`unit_context` são atribuídos pela camada de aplicação |

## Estados

- `ComparisonState`: `MATCH | DIFFERENT | SOURCE_MISSING | CURRENT_MISSING | NOT_COMPARABLE | PROTECTED | UNSUPPORTED | ERROR`
- `EligibilityState`: `ELIGIBLE_TO_APPLY | PROTECTED | NOT_APPLICABLE | PENDING_VALIDATION`
- `FieldDecisionState`: `PENDING | ACCEPTED_FOR_DRAFT | REJECTED_SUGGESTION` (modelado; sem API de decisão em S1)

`DIFFERENT` **nunca** implica elegibilidade. Elegibilidade exige regra canônica comprovada.

## Regras de comparação (fail-closed)

1. **Identidade**: `external.tax_id` (14 dígitos) deve igualar `canonical.tax_id` → senão `EnrichmentIdentityMismatchError` (comparação bloqueada).
2. **Escopo CNPJ**: `person_type != "J"` ou documento de 11 dígitos → `EnrichmentUnsupportedDocumentError`.
3. **Somente campos mapeados** entram na comparação; campos internos (financeiro, contábil, pagamento, registros fiscais) não são enriquecidos.
4. **Ausência externa nunca limpa valor interno**: `source_field` ausente → `SOURCE_MISSING`/`source_field_absent`; vazio → `SOURCE_MISSING`/`source_field_empty`; ambos `NOT_APPLICABLE`.
5. **Campos protegidos** (`tax_id`, identidade): `PROTECTED` + `EligibilityState.PROTECTED`, sem sugestão.
6. **Informativos** (situação, CNAE, natureza jurídica, abertura): comparados para exibição, `NOT_APPLICABLE`/`informational_only` — nunca geram PUT.
7. **Limites SX3**: sugestão normalizada maior que o campo → `PENDING_VALIDATION`/`exceeds_sa2_limit` (nunca truncada silenciosamente).
8. **`supplier_short_name`**: nome fantasia externo não é presumido equivalente a `A2_NREDUZ` → `PENDING_VALIDATION`/`equivalence_rule_pending`.
9. **Contato** (`area_code`, `phone`, `email`): requer política de fonte confiável → `PENDING_VALIDATION`/`trusted_source_policy_pending`; formato inválido → `invalid_suggested_value`.
10. **Grupo município** (`state`, `city`, `city_code`) é indivisível:
    - sem `municipality_index` → `PENDING_VALIDATION`/`municipality_reconciliation_unavailable`;
    - fonte sem UF/cidade/IBGE completo → `municipality_source_incomplete`;
    - par (UF, cidade) fora do índice CC2 → `municipality_not_conciliated`;
    - resolvido → grupo `ELIGIBLE_TO_APPLY`, `city_code` sugere o **código canônico CC2 resolvido** — o IBGE externo (7 dígitos) nunca é copiado para `A2_COD_MUN` (5 dígitos).
11. `municipality_index`: `Mapping[(uf, normalized_city_name) → city_code]` fornecido pela aplicação (catálogo `municipalities` da api-delpi no futuro); o domínio não busca dados.

## Normalização (`norm-v1`)

- `text`: trim, colapso de espaços, remoção de acentos (NFKD), casefold — preserva valores brutos para exibição;
- `digits`: somente dígitos; vazio → ausente;
- `uf`: trim + upper;
- `email`: trim + casefold; `@` exigido na elegibilidade.

Determinismo: sem relógio, rede ou aleatoriedade; mesmas entradas → mesmo output (provado em teste).

## Fronteiras não implementadas (etapas futuras)

- Ports `CanonicalSupplierReader`, `CompanyRegistryProvider`, `SupplierEnrichmentReviewRepository` — **não materializadas**: nenhum use case as consome em S1; serão criadas com a primeira aplicação real (S2), evitando abstração especulativa.
- Nenhuma rota HTTP, blueprint, migration, provider adapter ou alteração em POST/PUT.
- `change_context`/proveniência governamental: permanece fail-closed na api-delpi até contrato de evidência v2.

## Testes

`tests/test_supplier_enrichment_comparison.py` — 29 casos: identidade (CNPJ divergente, CPF, não-J), estados de comparação A–J, grupo município (com/sem índice, fonte incompleta, não conciliado), normalização, políticas de elegibilidade, limites, campos informativos, isolamento de mapeamento, determinismo e metadados.

## Resíduos conhecidos

- `resource_scope`/unidade do recurso fornecedor: `TO_INVENTORY` — capability `supplies.access` comprovada, mas a relação fornecedor↔filial/empresa precisa de contrato Core antes das rotas (S2).
- AuthZ efetiva continuará na application/BFF; o domínio não decide autorização.
- Política de retenção LGPD para reviews/decisões: pendente — nenhuma persistência criada.
