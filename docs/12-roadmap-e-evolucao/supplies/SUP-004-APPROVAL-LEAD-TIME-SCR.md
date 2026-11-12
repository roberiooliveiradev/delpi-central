# SUP-004 / Helpdesk #1004 — Tempo de aprovação de SC

**Status:** evolução do indicador #1004. Validar em produção após deploy e homologação.
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
- **Identidades:** `CR_LIBAPRO` identifica quem *efetivamente aprovou*;
  `CR_USERLIB` identifica o usuário executor da aprovação.
  A `SAK010` (cadastro: `AK_COD`, `AK_NOME`, `AK_USER`) permite
  apresentar o nome e usuário Protheus associados. Exemplo confirmado
  `AK_COD=000005` → `MAX ULIANO LEMOS`, usuário `000074`.
  Consulta SAK é somente enriquecimento de identidade; a SCR continua
  sendo a única fonte de eventos.

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


## Evolução: aprovadores pendentes e desempenho individual

- **Pendências ativas:** SCR com `CR_TIPO=SC` e `CR_STATUS=02`;
  responsável designado = `CR_APROV`, nome = `SAK010.AK_NOME`
  por `AK_COD`. O status `01` é uma alçada futura em fila, não conta
  como pendente ativa. Apenas SCs ainda presentes na SC1010 são listadas.
- **Prazos de pendência:** `CR_EMISSAO` até a data atual, em dias
  corridos, não necessariamente desde a criação da SC. A coluna
  `sc1_approved` sinaliza divergências nas quais a SC1010 parece liberada
  mas há SCR pendente. Exemplo de validação: `01/177300`.
- **Universos separados:** as pendências aparecem em tabela e contador
  próprios, **sem participar** da média de SCs concluídas.
- **Ranking por pessoa:** deduplica por filial+SC+nível+`CR_LIBAPRO` e
  calcula o prazo do evento de aprovação como
  `DATEDIFF(day, etapa_disponivel_estimativa, CR_DATALIB)`.
  `etapa_disponivel_estimativa` é o máximo entre emissão da SC,
  `CR_EMISSAO` da linha aprovada e término do nível anterior
  (o fim de cada nível é a última aprovação daquele nível).
  Quando a cronologia é invertida ou não comprovada, a observação
  **não** entra na média pessoal. A janela analítica considera apenas
  SCs elegíveis e totalmente aprovadas pelo contrato anterior.
- **Interpretação:** este não é um relógio exato de distribuição de tarefa;
  trata-se de uma estimativa com datas inteiras. Registros de reaprovação
  podem influenciar a média. Para evitar falsos "mais lentos",
  o gráfico horizontal lista apenas aprovadores com **5 ou mais**
  eventos no período, com o número da amostra ao lado.
  A tabela inclui todos, inclusive poucos eventos e pendências sem
  aprovações concluídas no recorte.
- **Evidências 12/11/2026:** consulta BlazeSQL sobre 2026 validou
  JOICI MOTTA 16 eventos e média 3,44 d; MAX ULIANO LEMOS
  95 eventos e média 3,14 d; LAERCIO AUGUSTO KOCH 75 e média 1,96 d;
  JOSE CARLOS 101 e média 1,78 d; FABIANO SCHMITZ 595 e média 1,52 d.
  Havia 6 SCs ativas com status SCR 02 no recorte, uma com SC1 já
  liberada (inconsistência a analisar).
- **Integração:** somente estende o payload da API existente com
  `approver_stats`, `pending_items`, `pending_total`,
  `pending_truncated`, `summary.pending_requests` e
  `items[].events[].approver_name`. Nenhuma migration ou escrita ERP.

### Smoke desta evolução

1. `01/178771`: etapa 1 no dia 26/10, aprovador **MAX ULIANO LEMOS**
   (código 000005, usuário 000074).
2. `01/179909`: pendente etapa 1, aprovador **JOSE CARLOS**
   (000012) deve aparecer no bloco de pendências, **não** na média
   de SCs concluídas.
3. `01/175190` e `01/175193`: históricos SCR antigos sem SC ativa;
   devem ser excluídos da lista de pendentes.
4. `01/177300`: pendência SCR 02 apesar dos itens atuais da SC1010
   terem status L. Sinalizar divergência.
5. `01/171945`: 3 níveis; média individual de nível 3 considera
   a etapa anterior e não imputa 10 dias ao terceiro aprovador.
6. Validar gráfico em desktop lado a lado e em mobile empilhado,
   tipos/contrastes, e tabela de médias incluindo tamanho da amostra.
