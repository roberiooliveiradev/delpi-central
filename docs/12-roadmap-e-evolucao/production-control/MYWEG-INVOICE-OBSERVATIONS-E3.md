# MyWEG → Production Control — NF Emitidas (Etapa 3)

> **TASK_ID:** `MYWEG-INVOICE-OBSERVATIONS-E3`  
> **Status:** UI gerencial com conciliação portal sempre ativa  
> **Depende de:** Etapa 2 (`invoiceMode=portal` + classificação gerencial)  
> **Owner:** plugin `production-control`  
> **EXISTING_EQUIVALENT:** `YES` · **REUSE_DECISION:** `EXTEND`

## Objetivo

Permitir ao PCP visualizar, na análise **Por produto**, a conciliação entre necessidades
MyWEG e observações de NF do portal — sem executar baixas e sem descontar NF da
necessidade atual — com leitura gerencial clara (faturado / parcial / investigar / pendente).

## Superfície

`/apps/production-control/myweg-needs?branch=02&view=compare` → análise Por produto.

A UI **sempre** envia `invoiceMode=portal`. O toggle Necessidades/Conciliação foi removido.
O parâmetro `invoiceMode=none` permanece no contrato da API para outros consumidores.
Botão discreto **Atualizar conciliação** preserva refresh/polling.

## Comportamento

- Consome `GET /myweg/need-batches/compare/products?invoiceMode=portal`
- KPIs de NF, variação observada, ajuste estimado e cobertura fiscal
- Colunas prioritárias: status gerencial, anterior, atual, NF MyWEG, residual, variação observada
- Modal redesenhado: badge gerencial, 4 indicadores, explicação operacional, remessas
  com contexto «Compatível com faturamento» (sem rateio NF×remessa), seção
  **Notas fiscais relacionadas** sob demanda
- Distinções obrigatórias na leitura:
  - movimentação observada (histórico de necessidades intacto);
  - faturamento MyWEG observado;
  - quantidade conciliável;
  - residual sem explicação fiscal;
  - limites: conciliação por material/janela — **não** atribui NF a uma data de remessa.
- Ajuda/tooltips explicam estimativa vs baixa e NF portal ≠ Protheus indicativo

## Fora de escopo

Segundo motor de conciliação, migrations, Protheus, timers, Windows, baixas, Etapa 4.

## Smoke E2 real

Fixture de regressão UI: produto `90263746` / material `17382643` / NF `000017061`
(redução 2.450 UN integralmente conciliada → status **Faturado**).
