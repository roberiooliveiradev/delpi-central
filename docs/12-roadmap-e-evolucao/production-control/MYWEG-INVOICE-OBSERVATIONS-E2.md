# MyWEG → Production Control — NF Emitidas (Etapa 2)

> **TASK_ID:** `MYWEG-INVOICE-OBSERVATIONS-E2`  
> **Status:** conciliação analítica no compare/products (sem UI, sem baixa, sem timer)  
> **Depende de:** Etapa 1 (`myweg.invoice-observations.batch.v1` + V027)  
> **Owner:** `production-control-api`  
> **EXISTING_EQUIVALENT:** `PARTIAL` · **REUSE_DECISION:** `EXTEND`

## Objetivo

Explicar a diferença entre variação observada de necessidades e quantidade de NF
portal na janela entre duas coletas, **sem descontar** a necessidade atual.

## API

`GET /myweg/need-batches/compare/products?invoiceMode=none|portal`

- Default `none` — comportamento E5 intacto.
- `portal` — campos aditivos por item + bloco `portalInvoices`.

Janela: `[collection_date(from), collection_date(to) - 1]` (`America/Sao_Paulo`).

Cobertura: `complete` | `partial` | `conflict` | `unavailable` | `pending_invoice_ingestion`.

## Fórmulas (material WEG)

```text
observed_delta_un = current - previous
posted_nf_un = soma NF canônicas na janela (sem duplicar semantic_sha256)
adjusted_planning_delta_un = observed + posted   # estimativa, não baixa
compatible_reduction_un = min(max(-observed, 0), posted)
```

Cobertura incompleta/conflito → ajuste `null` (não usa parcial como total).

## Fora de escopo

UI, timers, Windows, Protheus write, compare por remessa, FIFO indicativo,
abatimento transacional, Etapas 3–5.
