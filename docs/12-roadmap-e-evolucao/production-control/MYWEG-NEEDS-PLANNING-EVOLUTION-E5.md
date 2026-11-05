# MyWEG Necessidades — E5 Evolução do planejamento

> **TASK:** `MYWEG-NEEDS-E5-PLANNING-EVOLUTION`  
> **Escopo:** WEG Linhares · filial DELPI `02` · Protheus `000001`/`09` · MyWEG `1009`/`1106`

## Reuse

| Campo | Valor |
|---|---|
| EXISTING_EQUIVALENT | PARTIAL (snapshots E2, SB1 E4, NF cliente/produto parciais) |
| REUSE_DECISION | EXTEND |

## Owners

| Owner | Papel |
|---|---|
| api-delpi | `POST /pedidos-venda-abertos/totvs-outbound-invoice-line-items` — itens SD2/SF2 com D2_FILIAL+CLIENTE+LOJA |
| production-control-api | Motor puro `myweg_needs_comparison` + `GET /myweg/need-batches/compare` |
| plugins/production-control | Painel «Evolução do planejamento» na tela MyWEG |

## Regra fundamental

Nota fiscal DELPI **não** comprova abatimento reconhecido pela WEG.  
Separar no contrato: observado × faturamento candidato × cenário FIFO hipotético.

## Contratos

### Fiscal (api-delpi)

`list_customer_outbound_invoice_line_items`

Filtros: `branch=02`, `customer_code=000001`, `customer_store=09`, período, lote de `product_codes`, exclusão de devoluções (`F2_TIPO <> D`), soft-delete SF2/SD2.

Quantidade: `D2_QUANT` como string decimal (sem float autoridade).

### Comparação (PC JWT)

`GET /myweg/need-batches/compare?fromBatchId=&toBatchId=&billingMode=none|indicative`

Permissões: `production-control.access` + `myweg-needs.view` + `view.filial-02`.

## Homologação operacional

`REAL_TWO_BATCH_SMOKE`: **PENDING** até existir segunda coleta distinta homologada em produção.
