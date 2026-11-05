# MyWEG Necessidades — E5 Evolução do planejamento

> **TASK:** `MYWEG-NEEDS-E5-PLANNING-EVOLUTION`  
> **REWORK:** `MYWEG-NEEDS-E5-REWORK-FINAL-VALIDATION`  
> **FIX UNIDADES:** `MYWEG-NEEDS-E5-FISCAL-UNIT-MI-CONVERSION`  
> **Escopo:** WEG Linhares · filial DELPI `02` · Protheus `000001`/`09` · MyWEG `1009`/`1106`

## Reuse

| Campo | Valor |
|---|---|
| EXISTING_EQUIVALENT | YES (motor E5 + contratos) |
| REUSE_DECISION | EXTEND |

## Owners

| Owner | Papel |
|---|---|
| api-delpi | `POST /pedidos-venda-abertos/totvs-outbound-invoice-line-items` — itens SD2/SF2 com D2_FILIAL+CLIENTE+LOJA |
| production-control-api | Motor puro `myweg_needs_comparison` + `GET /myweg/need-batches/compare` |
| plugins/production-control | Painel «Evolução do planejamento» na tela MyWEG |

## Regra fundamental

Nota fiscal DELPI **não** comprova abatimento reconhecido pela WEG.  
Separar no contrato e na UI: observado × faturamento candidato × cenário FIFO hipotético × residual.

## Causas corrigidas no rework

| Problema | Causa | Solução |
|---|---|---|
| Janela fiscal 45 dias | `DEFAULT_BILLING_LOOKBACK_DAYS` a partir da coleta atual | Janela determinada pelo par `from`/`to` (ver regra abaixo) |
| FIFO/totais invisíveis | Painel só mostrava disclaimer | Seção «Faturamento indicativo» com `indicativeProducts` |
| Paginação inexistente | Frontend fixava `page=1`/`pageSize=50` | Paginação server-side + pesquisa + `changesOnly` |
| Ordem cronológica invertível | Sem validação de `collected_at` | Rejeita mesma coleta / ordem invertida; auto exige dias operacionais distintos |

## Regra da janela fiscal (conservadora)

Timezone: `America/Sao_Paulo`. Granularidade: dia de emissão (`D2_EMISSAO`).

- **Dias distintos:** `[collection_date(from), collection_date(to) − 1 dia]` (se o fim cair antes do início, usa o próprio início).
- **Mesmo dia (manual):** apenas aquele `collection_date`.
- **Não** usa lookback fixo de 45 dias nem a data de «hoje».
- WEG atualiza à tarde; DELPI costuma coletar na manhã seguinte — o cutoff exato é **desconhecido** e permanece explícito em `billing.cutoffUncertainty`.
- Não presume reconhecimento WEG; residual FIFO ≠ alteração confirmada da demanda.

Resposta de billing inclui: `period`, `periodCriterion`, `periodTimezone`, `periodGranularity`, `cutoffUncertainty`, quantidades candidatas por produto, status de disponibilidade.

## Unidades

- Autoridade da UM do item faturado: **`D2_UM`** (catálogo `B1_UM` só fallback).
- JOIN SB1 restrito a `B1_FILIAL = D2_FILIAL` + dedup por identidade fiscal (filial+doc+série+item).
- Necessidade MyWEG em **UN**.
- Normalização por item **antes** da agregação (owner api-delpi, `fiscal_quantity_to_un`):
  - `UN` / `UN.` → fator `1`
  - `MI` → fator `1000` (1 MI = 1.000 UN; alinhado a `UN_TO_MI_DIVISOR` MyWEG)
  - demais UMs (KG, CX, MT, …) → `comparable=false`, sem fator inventado
- Campos brutos `quantity`/`unit` preservados; autoridade FIFO = `quantity_un`.
- Production Control **não** reconverte: consome `quantity_un` do contrato.

Homologação WEG Linhares (diagnóstico): 155 itens / 65 produtos com `D2_UM=MI` — antes rejeitados; após o fix, elegíveis quanto à unidade se demais requisitos ok.

## Contratos efetivos

### Fiscal (api-delpi)

`list_customer_outbound_invoice_line_items`

Filtros: `branch=02`, `customer_code=000001`, `customer_store=09`, período do par, lote de `product_codes`, exclusão de devoluções (`F2_TIPO <> D`), soft-delete SF2/SD2.

Quantidade bruta: `D2_QUANT` como string decimal.  
Por item/total: `quantity_un`, `normalized_unit`, `conversion_factor`, `comparable`, `incompatibility_reason`, `original_units`.

### Comparação (PC JWT)

`GET /myweg/need-batches/compare?fromBatchId=&toBatchId=&billingMode=none|indicative&search=&page=&pageSize=&changesOnly=true`

Permissões: `production-control.access` + `myweg-needs.view` + `view.filial-02`.

S2S api-delpi: token de serviço canônico (`apply_internal_service_headers`) — **não** `X-Delpi-Caller-App` como autorização.

Campos novos relevantes: `totalCompared`, `totalChanges`, `billing.indicativeProducts`, `billing.period*`.

## Homologação operacional

`REAL_TWO_BATCH_SMOKE`: **PENDING** até existir segunda coleta distinta homologada em produção.

## Critérios de aceite (rework)

AC-01…AC-16 — ver relatório da task; testes automatizados cobrem janela, cronologia, paginação/search, unidades, auth negativa, FIFO e degradação fiscal.

## Testes executados (rework)

| Suite | Resultado |
|---|---|
| `production-control-api` `test_myweg_needs_compare_e5` + `test_myweg_needs_comparison_e5` | 22 passed |
| `production-control-api` E2+E4+E5 regressão MyWEG | 44 passed |
| `api-delpi` `test_customer_outbound_invoice_line_items` | 5 passed |
| MFE `vite build` (outDir temporário; `dist/` local root-owned) | PASS |
| MFE typecheck — erros pré-existentes LineFeeder/plugin-ui; nenhum em MyWEG Evolution | NO_MYWEG_TS_ERRORS |

Pendências: `REAL_TWO_BATCH_SMOKE` até segunda coleta real; deploy canônico pós-push.

## Fix MI → UN (`MYWEG-NEEDS-E5-FISCAL-UNIT-MI-CONVERSION`)

| Campo | Valor |
|---|---|
| ROOT_CAUSE | `COMPARABLE_NEED_UNITS` / `COMPARABLE_UNITS` só aceitavam UN/UN. |
| EXISTING_EQUIVALENT | PARTIAL (`UN_TO_MI_DIVISOR` MyWEG + `piecesFactor` MI=1000 em produção operacional) |
| REUSE_DECISION | EXTEND (helper fiscal na api-delpi; PC só consome `quantity_un`) |
