# MyWEG → Production Control — Notas Fiscais Emitidas (Etapa 1)

> **TASK_ID:** `MYWEG-INVOICE-OBSERVATIONS-E1`  
> **Status:** contrato + ingestão S2S + persistência histórica + consulta JWT (sem abatimento)  
> **Escopo:** filial **02** · empresa MyWEG **1009** · centro **1106** · fornecedor **50471**  
> **Owner:** `production-control-api`  
> **EXISTING_EQUIVALENT:** `PARTIAL` (padrão de necessidades MyWEG)  
> **REUSE_DECISION:** `EXTEND`

## 1. Objetivo

Importar observações históricas de Notas Fiscais Emitidas publicadas pelo Windows no Linux, com:

- contrato versionado `myweg.invoice-observations.batch.v1`;
- validação/leitura segura de `manifesto.json` + XLSX;
- persistência imutável e idempotente;
- consulta somente leitura JWT/RBAC;
- publicador one-shot manual (`--dry-run` / `--publish`).

**Fora desta etapa:** abatimento, conciliação E5, UI, timer Linux, escrita Protheus, lookup SB1.

## 2. Origem (somente leitura)

```text
~/.local/share/MyWEG-Automacao/notas-fiscais/
  filial-02/empresa-1009/centro-1106/fornecedor-50471/
    data-documento=YYYY-MM-DD/<collection_id>/
      manifesto.json
      EXPORT_*.xlsx   # ausente quando SEM_REGISTROS
```

Regra: ausência de manifesto/arquivo incompleto **nunca** significa zero notas. Zero só com
`status_validacao=SEM_REGISTROS_SINALIZADOS_PELO_SAP`.

## 3. Contrato `myweg.invoice-observations.batch.v1`

Envelope: `collection_id`, escopo MyWEG, `document_date`, `observation_status`
(`with_records` | `empty_signaled_by_sap`), `observed_at` (opcional), `source_prepared_at`,
`source_sha256`, `payload_sha256`, `semantic_sha256`, `record_count`, `records[]`.

Itens: número/série (texto), `material_weg`, descrição, quantidade original, unidade,
`quantity_un` (UN/MI), `departure_date`.

`semantic_sha256` = multiconjunto normalizado (ordem irrelevante; multiplicidade preservada).

## 4. API

| Método | Path | Auth | operationId |
|--------|------|------|-------------|
| POST | `/integrations/myweg/invoice-observations` | S2S `X-Delpi-Service-Token` | `ingest_myweg_invoice_observation_batch` |
| GET | `/myweg/invoice-observations` | JWT + `myweg-needs.view` + filial 02 | `list_myweg_invoice_observations` |
| GET | `/myweg/invoice-observations/{observationId}` | JWT | `get_myweg_invoice_observation` |
| GET | `/myweg/invoice-observations/{observationId}/items` | JWT | `list_myweg_invoice_observation_items` |

HTTP: 201 novo · 200 reenvio idempotente · 409 conflito de payload · 422 contrato · 401 S2S.

## 5. Persistência

Migration `V027__myweg_invoice_observations.sql`:

- `production_control.myweg_invoice_observations`
- `production_control.myweg_invoice_observation_items`

V025/V026 (necessidades) intactas.

## 6. Publicador manual

```bash
python -m production_control_app.jobs.myweg_invoice_observations_publisher \
  --dry-run --directory /caminho/da/coleta --json

python -m production_control_app.jobs.myweg_invoice_observations_publisher \
  --publish --collection-id <id> --json
```

Sem timer/systemd nesta etapa.

## 7. Aceite Etapa 1

Backend com contrato seguro, histórico confiável, consultas auditáveis e suporte a dias com
notas e dias sem registros (SAP). Nenhum cálculo de abatimento.
