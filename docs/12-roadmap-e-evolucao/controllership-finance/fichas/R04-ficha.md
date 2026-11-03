# R04 — Consumo por OP

Versão da ficha: 2.0 · 03/11/2026 · doc 152 + Gates 059–070.

Publicação: atualizada após implementação real — substitui a ficha 1.0
(31/10) que declarava `NOT_IMPLEMENTED`. Contrato operacional vigente.

## Identificação

- Código/nome: **R04 — Consumo por OP** (visão operacional de consumo
  de materiais por ordem de produção).
- Processo: PROC-0072 — registro no catálogo canônico (doc 118 §6).
- Owner técnico: produtor `consumption-audit` da api-delpi
  (contexto Suprimentos, GLPI #1353; reuso aprovado pela Controladoria).
- Produtor oficial candidato: `MATR860` — equivalência **não
  homologada** (`officialParity=pending`, `operational_view`).
- Implementação: **IMPLEMENTADO** — Portal → BFF
  `controllership-finance-api` → api-delpi → TOTVS (read-only).
- Rota Portal: `/closing/monthly-closing/{period}/reports/production-order-consumption`.

## Fonte e dados

- Endpoint produtor: `GET /supplies/consumption-audit/orders`
  (listagem) e `/orders/{production_order}` (detalhe), escopo S2S
  `consumption-audit.read`, clients `supplies-api` e
  `controllership-finance-api`.
- Listagem: `SC2010 OP` × `SB1010 P` (produto). Grão: uma OP.
  Campos: `C2_FILIAL`, `C2_OP`, `C2_NUM`, `C2_ITEM`, `C2_SEQUEN`,
  `C2_PRODUTO`, `B1_DESC`, `C2_UM`, `C2_QUANT`, `C2_QUJE`,
  `C2_STATUS`, `C2_TPOP`, `C2_EMISSAO`, `C2_DATPRI`, `C2_DATPRF`,
  `C2_DATRF`. Paginação `OFFSET/FETCH`.
- Detalhe: SC2 (ordem) + SG1 (estrutura) + SD4 (empenhos) + SD3
  (movimentos) + SH6 (apontamentos) + HZA (eventos) + SH8
  (alocações/operações) + SG2 (roteiro) — evidências separadas,
  nunca fundidas como acusação.
- SQL canônico: `consumption_audit_sql.py` — read-only, parâmetros
  bindados, `D_E_L_E_T_=''`.

## Regras de negócio

- `date_type` decide a data real do filtro: `emission`=C2_EMISSAO;
  `finished`=C2_DATRF; `appointment`=EXISTS SH6.H6_DTAPONT no
  período (datas planejadas C2_DATPRI/DATPRF não são `date_type`).
- Filtros: `branch` (obrigatória 01|02), `search` (fragmento
  C2_OP/C2_NUM), `product` (código/descrição), `status` (C2_STATUS),
  `work_center` e `operation` (EXISTS SH8 — por operação).
- **Ordenação global (Gate 070):** `sort_by` ∈ {production_order,
  product_code, product_description, status, date} +
  `sort_direction` ∈ {asc, desc}; whitelist fechada, desempate
  `C2_OP ASC`, aplicada antes da paginação. `date` segue o
  `date_type`. Sem parâmetros → ordem legada `C2_EMISSAO DESC,
  C2_OP ASC`. `work_center` não é ordenável (SH8 multi-operação).
- **Status:** `C2_STATUS` é flag administrativo — `N`/vazio =
  Normal, `S` = Sacramentada, `U` = Suspensa (fontes TOTVS Delpi
  DLP013/DEL016). É ortogonal ao progresso: OP «Normal» pode estar
  encerrada ou com produção concluída.
- **Centro de trabalho:** existe por operação em SH8 (`H8_CTRAB`),
  visível no detalhe da OP; a listagem não projeta campo escalar —
  uma OP pode envolver vários centros.

## Interpretação

- Visão operacional: evidências para auditoria de consumo; diferenças
  aritméticas entre fontes nunca são acusação de irregularidade.
- Equivalência MATR860 **pendente** — nunca afirmar paridade oficial.
- `not_informed`/ausências são tipadas como ausência de informação,
  não como erro ou reprovação.

## Operação

- Portal: página «Consumo por OP» com hero, filtros Filial/Tipo de
  data/Busca, grid paginado (25/página) com ordenação por cabeçalhos
  e detalhe por clique na OP.
- CLARA: `read(report.production_order_consumption)` — passthrough
  governado da rota BFF (period, branch, filtros, page/page_size,
  sort_by/sort_direction).
- Comparações: `NOT_COMPARABLE` com MATR860 até homologação.

## Governança

- Evidências: doc 152 (auditoria); Gate 070 (ordenação); Gate 067–069
  (UX); GLPI #1353 (produtor).
- Incidente: HTTP 400 na CLARA corrigido no Gate 072 — defaults
  `Query(...)` vazavam para o produtor quando o tool não repassava
  `sort_*`; corrigido na BFF (só strings reais são encaminhadas) e
  tool atualizado com os parâmetros.
- Limitações: visão operacional; equivalência oficial pendente;
  centro de trabalho apenas no detalhe; datas de referência são da
  OP, não do movimento de consumo.
- Referências: doc 150 §16–17; doc 152; `consumption_audit_sql.py`;
  `production_order_consumption_routes.py`.
