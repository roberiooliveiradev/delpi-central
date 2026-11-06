# MyWEG → Production Control — NF Emitidas (Etapa 3)

> **TASK_ID:** `MYWEG-INVOICE-OBSERVATIONS-E3`  
> **Status:** UI de conciliação na análise Por produto  
> **Depende de:** Etapa 2 (`invoiceMode=portal` no compare/products)  
> **Owner:** plugin `production-control`  
> **EXISTING_EQUIVALENT:** `PARTIAL` · **REUSE_DECISION:** `EXTEND`

## Objetivo

Permitir ao PCP visualizar, na análise **Por produto**, a conciliação entre necessidades
MyWEG e observações de NF do portal — sem executar baixas e sem descontar NF da
necessidade atual.

## Superfície

`/apps/production-control/myweg-needs?branch=02&view=compare` → análise Por produto.

Toggle:

- **Necessidades** → `invoiceMode=none` (padrão)
- **Conciliação MyWEG** → `invoiceMode=portal`

## Comportamento

- Consome `GET /myweg/need-batches/compare/products`
- KPIs de NF, variação observada, ajuste estimado e cobertura fiscal
- Colunas aditivas na tabela (observada, NF, ajustada, situação da conciliação)
- Modal: resumo fiscal + detalhe sob demanda via
  `GET /myweg/invoice-observations/{id}` e `.../items` com filtro exato por `materialWeg`
- Ajuda/tooltips explicam estimativa vs baixa e NF portal ≠ Protheus indicativo

## Fora de escopo

Backend E2, ingestão E1, migrations, Protheus, timers, Windows, Etapa 4.

## Smoke E2 real

Permanece **PENDING** até comprovação com duas coletas reais e observações fiscais
na janela. Testes mockados da E3 não aceitam o resultado de negócio.
