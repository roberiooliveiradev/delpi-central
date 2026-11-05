# MyWEG Necessidades — E4 Protheus product matching (SB1)

> **TASK:** `MYWEG-NEEDS-E4-PROTHEUS-PRODUCT-MATCHING`  
> **Rework:** `MYWEG-NEEDS-E4-REWORK-FINAL-HOMOLOGATION`  
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

## Semântica dos campos (comprovada no dry-run homologado)

| Campo MyWEG (contrato E1) | SB1 | Rótulo UI E4 |
|---|---|---|
| `material_weg_tratado` | `B1_REFEREN` | Material WEG |
| `codigo_referencia_weg` | `B1_COD` (rótulo E1 enganoso) | Código DELPI (origem) |

Persistência de vínculos exige `evaluate_field_semantics` com amostra ≥20 pares e ≥80% `confirmed` com `matched_by=code_and_reference`. Caso contrário: `ARCHITECTURE_DECISION_REQUIRED` (dry-run livre; persist bloqueado).

**Atenção:** a prova é do cadastro **atual** no momento da verificação (`verified_at`). Não comprova o estado histórico na data da coleta.

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
- `dry_run=false`: upsert atômico (run + vínculos na mesma transação) em `myweg_need_sb1_resolutions` **somente** se semântica comprovada

URL no gateway:

```text
http://127.0.0.1/apps/production-control-api/integrations/myweg/need-batches/sb1-resolve
```

## Migration

`V026__myweg_need_sb1_resolutions.sql` — aditiva:

- `myweg_need_sb1_resolution_runs`
- `myweg_need_sb1_resolutions` (UNIQUE `record_id`)

**Não altera** V025 nem `CHECK (sb1_status = 'pending')` nas records.

## Rework de confiabilidade (pós-revisão)

1. **SQL listagem:** `count_sql` e `list_sql` compartilham o mesmo `FROM records r LEFT JOIN resolutions res` — pesquisa por `verified_product_code` não quebra a contagem.
2. **Transação:** `persist_sb1_resolution_batch` grava run + upserts com **um único commit**; falha → rollback completo; `persisted=true` só após sucesso.

## UI

`/apps/production-control/myweg-needs?branch=02`

Colunas: Material WEG · Código DELPI (origem) · Código DELPI verificado · Descrição DELPI · Situação do vínculo · qtd/remessa.

## Homologação — dry-run real (evidência)

Coleta: `20261104_172829_20261104_142827_EXPORT_20261104_142826`

| Campo | Valor |
|---|---|
| HTTP | 200 |
| dryRun | true |
| persisted | false |
| recordCount | 532 |
| semantics.proven | true |
| confirm_ratio | 1.0 |

Contagens (desta coleta; **não** é invariante permanente):

| Estado | Qtd |
|---|---|
| confirmed | 532 |
| pending | 0 |
| not_found | 0 |
| ambiguous | 0 |
| divergent | 0 |
| blocked | 0 |
| unavailable | 0 |

### Persistência produtiva

**PENDENTE de autorização explícita.** Não executar `dry_run=false` automaticamente.

Procedimento após autorização:

1. Repetir dry-run e confirmar 532 confirmed / `semantics.proven`
2. Conferir amostra sanitizada (código origem, verificado, descrição SB1, `matched_by`)
3. `dry_run=false` uma vez
4. Reexecutar e confirmar idempotência (mesmo número de resoluções)
5. Smoke JWT + Portal PCP
6. Sem cron / sem backfill em massa
