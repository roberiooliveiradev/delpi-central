# MyWEG → Production Control — Necessidades (Etapa 2)

> **Status:** persistência + ingestão S2S + consultas JWT (sem MFE, sem ETL Linux)  
> **Escopo:** filial **02** · empresa `1009` · centro `1106`  
> **Depende de:** [MYWEG-NEEDS-INGESTION-E1.md](./MYWEG-NEEDS-INGESTION-E1.md) (`myweg.needs.batch.v1`)

## REUSE_DECISION

| Decisão | Detalhe |
|--------|---------|
| ESTENDER | `validate_ingest_batch` / contrato E1 |
| ESTENDER | S2S `X-Delpi-Service-Token` + bypass `/integrations/myweg/` |
| ESTENDER | schema `production_control`, envelope `{success,message,data}`, BranchAccess |
| CRIAR | `V025__myweg_need_batches.sql`, repo, service, rotas S2S/JWT |
| NÃO | misturar com `GET /demand`, SQL Protheus, UI MFE, ETL Linux |

## Persistência

Migration aditiva `V025__myweg_need_batches.sql`:

- `production_control.myweg_need_batches` — snapshot imutável (`status=accepted`)
- `production_control.myweg_need_records` — linhas do lote (FK `ON DELETE RESTRICT`)
- `UNIQUE(collection_id)` — identidade da coleta
- `payload_sha256` **não** é UNIQUE global
- `collection_date` = data de `collected_at` em `America/Sao_Paulo` (≠ `data_remessa`)

Nunca substituir lote anterior pelo mais recente. Ausência de coleta ≠ snapshot fictício. Falha de ingestão não remove a última coleta válida.

## Idempotência

| Caso | Resultado |
|------|-----------|
| Mesmo `collection_id` + mesmo `payload_sha256` | 200 + lote existente (`created=false`) |
| Mesmo `collection_id` + hash diferente | **409** (lote original intacto) |
| Novo `collection_id` + mesmo hash | **201** nova observação histórica |

Corrida: `UNIQUE(collection_id)` + re-leitura pós-`UniqueViolation`.

`Idempotency-Key` = `collection_id:payload_sha256` (opcional se omitido; se enviado, deve bater).

## Rotas

### S2S (serviço)

| Método | Path | operationId | Auth |
|--------|------|-------------|------|
| POST | `/integrations/myweg/need-batches` | `ingest_myweg_need_batch` | `X-Delpi-Service-Token` |

Público via gateway: `/apps/production-control-api/integrations/myweg/need-batches`.

### JWT (usuário — somente leitura)

Permissões: `production-control.access` + `production-control.myweg-needs.view` + `production-control.view.filial-02`.

| Método | Path | operationId |
|--------|------|-------------|
| GET | `/myweg/need-batches` | `list_myweg_need_batches` |
| GET | `/myweg/need-batches/latest` | `get_latest_myweg_need_batch` |
| GET | `/myweg/need-batches/{batchId}` | `get_myweg_need_batch` |
| GET | `/myweg/need-batches/{batchId}/items` | `list_myweg_need_batch_items` |

Query de items: `search`, `remessaFrom`, `remessaTo`, `page`, `pageSize`.

Ordenação de listagem/`latest`: `collected_at DESC`, depois `imported_at DESC`, depois `collection_id ASC` — importar coleta antiga depois **não** altera a última coleta válida.

## Recuperação de falhas

1. Validação E1 falha → 422, nada persistido.
2. Erro no meio da transação → rollback completo.
3. Reenvio idêntico após sucesso → 200 idempotente.
4. Linux/automação **não** é alterada nesta etapa; primeiro envio real = homologação manual.

## Atividades no Linux (fora do Cursor)

1. Grant Keycloak `production-control.myweg-needs.view` (+ filial 02) aos papéis PCP ES.
2. Homologar conector S2S apontando para o POST acima (token interno + Idempotency-Key).
3. Não alterar ETL/Windows/PDFs/agendamento 05h00 nesta fatia.
