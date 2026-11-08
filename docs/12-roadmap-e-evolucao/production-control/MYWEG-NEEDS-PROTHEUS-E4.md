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

Persistência de vínculos exige `evaluate_field_semantics` com amostra ≥20 pares e ≥80% `confirmed` com `matched_by` em `{code_and_reference, reference_prefer_production}`. Caso contrário: `ARCHITECTURE_DECISION_REQUIRED` (dry-run livre; persist bloqueado).

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

1. Filtrar candidatos elegíveis (não bloqueados) com a mesma referência WEG (`B1_REFEREN`).
2. Se houver produção (`9…`) elegível → selecionar o **maior `B1_COD` numérico**
   (`prefer_highest_production_code`). O código de origem MyWEG é rastreável
   (`product_code`), mas **não** tem prioridade absoluta — mesmo quando for outro `9` válido.
3. Sem produção elegível e com amostra (`8…`) → selecionar o maior `B1_COD` numérico de
   amostra (`provisional_highest_sample_code_no_production`; único elegível usa
   `provisional_sample_code_no_production`).
4. Comparação estritamente numérica (não lexicográfica). Códigos não numéricos não entram
   no desempate; sem vencedor inequívoco → `ambiguous` (`multiple_production_codes`).
5. Produto bloqueado (`B1_MSBLQL=1`) não é escolhido; código `9` informado e bloqueado
   permanece `blocked` (não é substituído silenciosamente).
6. Divergência / código informado inexistente / referência incompatível permanecem
   `divergent` / `ambiguous` / `not_found` conforme a classificação base (sem “adivinhar”).
7. `matched_by=code_and_reference` **somente** quando o verificado coincide com o informado;
   desempate por referência usa `reference_prefer_production` (produção) ou `reference_only`
   (amostra provisória). Não consultar `B1_REVATU` / `B1_UREV`.

Casos reais:

- Material WEG `18765646` · informado `80015414` · candidatos `80015414`, `80015629`,
  `90264125`, `90264263` → verificado `90264263`.
- Material WEG `19740817` · sem origem · candidatos `80016662`, `80016673` →
  verificado `80016673` (amostra provisória).
- Materiais com origem `9` menor que outro `9` elegível na mesma referência → passam a
  verificar o maior código (ex.: origem `90261614` com candidato maior elegível).

### Recuperação de lotes já persistidos

`skip_if_complete=true` na automação pode ignorar lotes já resolvidos (inclusive
`ambiguous` ou confirmações pela origem antiga). Após esta regra:

1. Homologar com `dry_run=true` e `skip_if_complete=false` no `collection_id` alvo.
2. Comparar resolução anterior × nova (códigos substituídos pelo maior elegível).
3. Persistência produtiva só com autorização explícita + `skip_if_complete=false`.
4. Não fazer UPDATE manual; não alterar V025/V026; não reprocessar histórico em massa.

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
