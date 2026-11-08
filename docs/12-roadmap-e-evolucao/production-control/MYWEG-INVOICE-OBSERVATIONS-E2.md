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

## Classificação gerencial (aditiva)

Campos aditivos por produto (não substituem brutos):

| Campo | Uso |
|---|---|
| `managerialStatus` | `invoiced` \| `partial_invoicing` \| `reduction_to_investigate` \| `reconciliation_pending` \| `other_movement` |
| `managerialReason` / `managerialExplanation` | Motivo e frase operacional |
| `residualUnexplainedUn` | Residual da redução sem NF compatível |
| `remessaInvoicingContext` / `managerialRemessaContext` | Contexto visual nas remessas — **sem rateio** |

**Faturado** exige cobertura completa + identidade confiável + NF positiva +
`compatibleReductionUn == |observedDelta|` + `adjustedPlanningDeltaUn == 0`
(Decimal exato). `invoiceMatchStatus=reconciled` isolado **não** basta.

Remessas reduzidas só recebem `compatible_with_invoicing` quando o produto está
Faturado, a soma das reduções fecha com o observado e **não** há aumentos
simultâneos. Não há FIFO nem atribuição NF→data.

## Fora de escopo

Timers, Windows, Protheus write, compare por remessa, FIFO indicativo,
abatimento transacional.
