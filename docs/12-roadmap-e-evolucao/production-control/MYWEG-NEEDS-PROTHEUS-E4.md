# MyWEG Necessidades — E4 Protheus product matching (SB1)

> **TASK:** `MYWEG-NEEDS-E4-PROTHEUS-PRODUCT-MATCHING`  
> **Escopo:** filial DELPI `02` · empresa MyWEG `1009` · centro `1106`  
> **Somente leitura no Protheus.** Snapshots V025 imutáveis.

## Reuse decision

| Decisão | Valor |
|---|---|
| EXISTING_EQUIVALENT | PARTIAL (`GET /products/search` é LIKE por prefixo; `fetch_product_by_*` é unitário TOP 1) |
| REUSE_DECISION | EXTEND |

## Owners

| Owner | Responsabilidade |
|---|---|
| api-delpi | `POST /products/sb1-identity-lookup` (`lookup_products_sb1_identity`) — igualdade exata B1_COD/B1_REFEREN em lote + classificação |
| production-control-api | Resolução manual S2S, projeção V026, consultas JWT enriquecidas |
| plugins/production-control | Labels e colunas da tela Necessidades WEG |
| Core | Permissões existentes (`myweg-needs.view` + filial-02); resolve **não** usa view |

## Semântica dos campos (hipótese → prova)

| Campo MyWEG (contrato E1) | Hipótese SB1 | Rótulo UI E4 |
|---|---|---|
| `material_weg_tratado` | `B1_REFEREN` | Material WEG |
| `codigo_referencia_weg` | `B1_COD` (rótulo E1 enganoso) | Código DELPI (origem) |

Persistência de vínculos exige `evaluate_field_semantics` com amostra ≥20 pares e ≥80% `confirmed` com `matched_by=code_and_reference`. Caso contrário: `ARCHITECTURE_DECISION_REQUIRED` (dry-run livre; persist bloqueado).

## Contratos

### api-delpi — `POST /products/sb1-identity-lookup`

- Auth: `api-delpi.access` (S2S service token ok)
- Request: `{ branch, items[{ client_key, product_code?, customer_reference? }] }` (max 1000)
- Response: `results[]` com `match_status` ∈ confirmed|not_found|ambiguous|divergent|blocked|pending
- Sem LIKE, sem TOP 1 que esconda ambiguidade, sem efeitos colaterais

### production-control-api — S2S

`POST /integrations/myweg/need-batches/sb1-resolve`

```json
{ "collection_id": "...", "dry_run": true }
```

- Exige `X-Delpi-Service-Token`
- `dry_run=true` (default): diagnóstico + contagens, sem persistir
- `dry_run=false`: upsert idempotente em `myweg_need_sb1_resolutions` **somente** se semântica comprovada

## Migration

`V026__myweg_need_sb1_resolutions.sql` — aditiva:

- `myweg_need_sb1_resolution_runs`
- `myweg_need_sb1_resolutions` (UNIQUE `record_id`)

**Não altera** V025 nem `CHECK (sb1_status = 'pending')` nas records.

## UI

`/apps/production-control/myweg-needs?branch=02`

Colunas: Material WEG · Código DELPI (origem) · Código DELPI verificado · Descrição DELPI · Situação do vínculo · qtd/remessa.

## Homologação

Coleta: `20261104_172829_20261104_142827_EXPORT_20261104_142826`

1. Deploy api-delpi + production-control-api (+ migration V026)
2. Dry-run S2S → registrar contagens
3. Se `semantics.proven`, persistir com `dry_run=false`
4. Smoke na tela (amostra vs resposta api-delpi)
5. Sem cron / sem backfill em massa
