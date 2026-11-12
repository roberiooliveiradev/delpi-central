# SUP-004 / Helpdesk #1004 — Tempo de aprovação de SC

**Status:** implementação em branch para revisão/homologação; não equivale a deploy.
**Fonte canônica de eventos:** exclusivamente `SCR010`. A `SC1010` fornece
somente a data de criação, identidade da SC e sua situação atual. Não usar
`C1_APROV` como data nem o polling de notificações como histórico.

## Indicador

- **Grão:** SC distinta `(C1_FILIAL, C1_NUM)`, independente da quantidade
  de itens e de grupos `CR_GRUPO` repetidos.
- **Filtro de competência:** `C1_EMISSAO` (data de criação), por filial
  `01` e/ou `02`. Período limitado a 367 dias.
- **Elegibilidade:** SC ativa em `SC1010`, todos os seus itens com
  `C1_APROV = L`, data de emissão válida, e ao menos uma entrada
  `CR_TIPO=SC` em SCR ativa, com `CR_STATUS=03`, data de liberação
  válida, `CR_USERLIB` e `CR_LIBAPRO` preenchidos. Excluir
  solicitações cujos eventos SCR contenham aprovações não comprovadas,
  eventos pendentes/rejeitados, data final anterior à criação, e
  qualquer SC sem histórico SCR.
- **Finalização:** maior `CR_DATALIB` entre entradas aprovadas da
  mesma SC. Não confundir com data do primeiro pedido de compra.
- **Fórmula:** `DATEDIFF(day, MIN(C1_EMISSAO), MAX(CR_DATALIB))`.
  Dias corridos; no mesmo dia = 0. São datas sem horário oficial.
- **Níveis:** `COUNT(DISTINCT CR_NIVEL)` para aprovações 03.
  A lista de eventos deduplica por filial+SC+nível+data+executor+aprovador
  para evitar multiplicação por grupo de alçada.
- **Identidades:** `CR_USERLIB` (usuário executor) é distinto de
  `CR_LIBAPRO` (código do aprovador). Rótulos mostram códigos quando
  nome completo não tiver mapeamento confiável.

**Não são medidos nesta entrega:** aprovação automática presumida,
SCs liberadas sem SCR, relógio pós-aprovação até emissão de pedido,
horas/minutos, e aprovações/reaprovações que dependam de validação
de negócio para separar liberação inicial da última reaprovação.

## Rotas (somente consulta)

1. `GET /supplies/purchase-requests/approval-lead-time` da `api-delpi`:
   SQL TOTVS em repository, acessível somente a caller interno confiável
   `supplies-api` com token válido.
2. `GET /apps/supplies-api/purchase-requests/approval-lead-time`:
   BFF Flask com `supplies.access`, `branch=01&branch=02` obrigatório,
   filtros opcionais `date_from`, `date_to`, `request_number`, `page`,
   `page_size`; rejeita qualquer filtro desconhecido e não reenvia dados
   sensíveis de erros internos.
3. `/apps/supplies/purchase-requests/approval-lead-time`:
   dashboard do plugin com KPIs, faixas completas de prazo e tabela paginada,
   com detalhes por nível e deep link para a ficha da SC.

## Homologação

1. Rodar `pytest api-delpi/tests/test_purchase_request_approval_lead_time_sql.py`
   no contexto `api-delpi` e
   `pytest tests/interface/http/test_purchase_request_approval_lead_time.py`
   no contexto `supplies-api`.
2. Rodar testes do plugin `npm test -- --run src/features/purchase-requests/approvalLeadTimeApi.test.ts`
   e `npm run build` no diretório `plugins/supplies`.
3. Com ambiente autenticado, validar as SCs `01/171945` (3 níveis,
   13/02/2026 a 23/02/2026 = 10 dias), `02/169847` (grupos
   duplicados), e uma SC liberada sem SCR (deve ficar fora).
4. Usar o recorte 2026: Matriz 367 SC / 2,19 dias; Filial 527 / 1,90 dias
   nas amostras de validação de 12/11/2026. Valores reais podem evoluir.
5. Antes de considerar KPI oficial, revisar com Suprimentos os casos
   com pedido emitido antes da maior data SCR e sua semântica de reaprovação.

Nenhum passo requer alteração de dados do Protheus. Sem migrar ou duplicar
histórico SCR no PostgreSQL do Portal.
