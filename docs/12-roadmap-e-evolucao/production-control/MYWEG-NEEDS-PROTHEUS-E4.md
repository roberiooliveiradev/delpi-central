# MyWEG Necessidades — E4 Protheus product matching (SB1)

> **TASK:** `MYWEG-NEEDS-E4-PROTHEUS-PRODUCT-MATCHING`  
> **Rework:** `MYWEG-NEEDS-E4-REWORK-FINAL-HOMOLOGATION`  
> **Automação:** `MYWEG-NEEDS-AUTOMATIC-SB1-RESOLUTION`  
> **Escopo:** filial DELPI `02` · empresa MyWEG `1009` · centro `1106`  
> **Somente leitura no Protheus.** Snapshots V025 imutáveis.

## Reuse decision

| Decisão | Valor |
|---|---|
| EXISTING_EQUIVALENT | PARTIAL (`GET /products/search` é LIKE por prefixo; `fetch_product_by_*` é unitário TOP 1) |
| REUSE_DECISION | EXTEND — lookup tipado + resolve S2S + orquestração no publicador Linux |

## Owners

| Owner | Responsabilidade |
|---|---|
| api-delpi | `POST /products/sb1-identity-lookup` — igualdade exata + classificação; política 9/8 **opcional** via `disambiguation_policy` |
| production-control-api | `MyWegSb1ResolveService`, projeção V026, S2S resolve, publicador que orquestra E2→E4 |
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
- Request: `{ branch, items[{ client_key, product_code?, customer_reference? }], disambiguation_policy? }` (max 1000)
- `disambiguation_policy` omitido = classificação neutra (demais consumidores)
- `disambiguation_policy=prefer_production_over_sample` = política PCP MyWEG (ver abaixo)
- Response: `results[]` com `match_status` ∈ confirmed|not_found|ambiguous|divergent|blocked|pending
- Sem LIKE, sem TOP 1 que esconda ambiguidade, sem efeitos colaterais

### production-control-api — S2S

`POST /integrations/myweg/need-batches/sb1-resolve`

```json
{ "collection_id": "...", "dry_run": true, "skip_if_complete": false }
```

- Exige `X-Delpi-Service-Token`
- `dry_run=true` (default): diagnóstico + contagens, sem persistir
- `dry_run=false`: upsert atômico (run + vínculos na mesma transação) em `myweg_need_sb1_resolutions` **somente** se semântica comprovada
- `skip_if_complete=true`: se PG já tem run completed + vínculos cobrindo o lote sem `unavailable`, retorna `skipped` sem reconsultar Protheus
- MyWEG resolve sempre envia `prefer_production_over_sample` ao lookup

URL no gateway:

```text
http://127.0.0.1/apps/production-control-api/integrations/myweg/need-batches/sb1-resolve
```

### Automação diária (publicador)

Após ingestão bem-sucedida (ou `already_published` no watermark), o job
`myweg-needs-publisher` chama o mesmo endpoint com `dry_run=false` e
`skip_if_complete=true`. Rollback: `MYWEG_PUBLISHER_AUTO_SB1_RESOLVE=false`.
Detalhes operacionais: `MYWEG-NEEDS-LINUX-PUBLISHER.md`.

## Regra PCP — códigos DELPI 8 e 9

Informada pelo PCP; aplicada **somente** com `disambiguation_policy=prefer_production_over_sample`:

| Prefixo | Significado |
|---|---|
| `8…` | Fase de amostra |
| `9…` | Produto de produção |

Regras:

1. Mesma referência WEG (`B1_REFEREN`) com amostra e produção → priorizar o **único** código 9 elegível (não bloqueado).
2. Sem 9 elegível e um único 8 elegível → confirmar 8 provisório (`provisional_sample_code_no_production`).
3. Dois ou mais códigos 9 elegíveis → `ambiguous` (`multiple_production_codes`),
   **exceto** quando o código DELPI de origem já é produção (`9…`), existe no SB1,
   não está bloqueado e o par `B1_COD + B1_REFEREN` confere exatamente — nesse caso
   permanece `confirmed` com o código informado (`matched_by=code_and_reference`).
   Contrapeças/variações que compartilham a referência não invalidam essa confirmação.
4. Produto bloqueado (`B1_MSBLQL=1`) não é escolhido; código 9 informado e bloqueado
   permanece `blocked` (não é substituído por outro 9 elegível).
5. Divergência real código×referência permanece `divergent` (sem associação arbitrária).
6. Resposta preserva código informado (`product_code`), código verificado e `reason` / `matched_by` (`reference_prefer_production` quando houve desempate).

Casos reais:

- Material WEG `19106407` · informado `80015942` · produção única `90264221` → verificado `90264221`.
- Material WEG `11403512` · informado `90261614` · outros 9 na mesma referência → verificado `90261614`.
- Material WEG `12322556` · informado `90262016` · outros 9 na mesma referência → verificado `90262016`.

### Recuperação de lotes já persistidos como `ambiguous`

`skip_if_complete=true` na automação pode ignorar lotes que já têm resolução (mesmo
`ambiguous`). Após esta correção no classificador:

1. Identificar lotes afetados (consulta JWT / itens `ambiguous` com código 9 informado).
2. Prévia: `POST .../sb1-resolve` com `dry_run=true` e `skip_if_complete=false`.
3. Comparar status anterior × novo; confirmar os exemplos acima quando SB1 validar.
4. Persistência produtiva só com autorização explícita + `skip_if_complete=false`.
5. Não fazer UPDATE manual nas tabelas; não alterar V025/V026; não reprocessar histórico em massa.

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

A automação do publicador executa `dry_run=false` **somente** quando
`evaluate_field_semantics` comprova a hipótese e os gates S2S estão ok.
Rollback: desligar `MYWEG_PUBLISHER_AUTO_SB1_RESOLVE` ou o timer.

Homologação de uma **nova** coleta real pós-deploy da automação: **PENDING**
até evidência AC-01/AC-02 (publicada + SB1 persistida sem ação humana).

Procedimento manual (diagnóstico / intervenção):

1. Dry-run S2S e conferir `semantics.proven` + contagens
2. `dry_run=false` uma vez se necessário
3. Reexecutar com `skip_if_complete=true` e confirmar `skipped`
4. Smoke JWT + Portal PCP / comparação E5
