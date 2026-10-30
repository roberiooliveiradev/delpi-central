# R03 — P7 / Registro de Inventário

Versão da ficha: 1.0 · 31/10/2026 · doc 127 Etapa 4.

## Identificação

- Código/nome: **R03 — Registro de Inventário Modelo P7** (posição de
  estoque na data de fechamento, escopo completo e recorte MP/PA/PI).
- Finalidade: documento fiscal/estoque oficial do fechamento —
  sustenta o valor de estoque reportado à contabilidade e o bloco
  "EM PROCESSO" conciliado com o R08.
- Processo: PROC-0072, P3 (estoque/cutoff) — `PROVEN` (doc 118 §6).
- Owner funcional: Controladoria; consumidor: Contabilidade/SPED.
- Owner técnico: `api-delpi` + `controllership-finance-api`.
- Produtor oficial: `MATR460` (roster) — `matr460.prx` **ausente**
  (`SOURCE_MISSING`); `A460UNIT.prw` localizado (hook por produto);
  workfiles `MP7_*` retidos até ~04/2024 — doc 85 §3.
- Implementação: **`IMPLEMENTED`** (IMPLEMENTATION-006, 29/10) —
  `/closing/stock-inventory` evoluído a motor P7: SB9 ex-`MV_LOCPROC`
  + MATR989 `as_of`; `report_scope=all_products|mp_pi_pa`; export CSV
  com hash; `officialP7=false`, `parityStatus=PENDING` até homologação
  MATR460 (doc 119 §11).
- Homologação: binding de totalização `PROVEN`; G4/G5 `PENDING` (E2);
  G6 `PENDING`.

## Fonte e dados

- Artefatos: `Estoque.pdf` (completo, R$ 3.946.431,87), `Resumo
  Estoque.pdf` (MP/PA/PI, R$ 2.976.967,56); vídeo 35:00/37:00.
- Dados: SB9 (saldos de fechamento por `B9_DATA`) + bloco EM PROCESSO
  reconstruído via MATR989 `as_of` (físico loc-`MV_LOCPROC` + alocado a
  OPs abertas) — doc 119 §11.
- Grão: produto × armazém. Eixo: data fim de competência.
- Filial: parâmetro da emissão (Matriz observada; f02 consultável).
- Capability CLARA: `read(report.stock_inventory)`.

## Regras de negócio (doc 85 §3)

- BR-R03-001 identidade/finalidade — `AS-IS`.
- BR-R03-002 fechamento iterativo/versionamento — `PROVEN`.
- BR-R03-003 **EM PROCESSO = relatório MATR989** — `PROVEN`.
- BR-R03-004 EM ESTOQUE — `PROVEN` (totalização; parâmetros `PENDING`).
- BR-R03-005 origem física — `PROVEN` totalização / `TO_INVENTORY`
  produtor.
- BR-R03-006 EM ESTOQUE exclui armazém de processo — `PROVEN`.
- BR-R03-007 escopo MP/PA/PI e divergência MP — fatos `PROVEN`, causa
  `PENDING`.
- BR-R03-008 mapa de parâmetros MTR460 — `PROVEN` (catálogo SX1, 25
  perguntas, **sem parâmetro de tipo** → escopo exige mecanismo fora do
  SX1 — E2).
- BR-R03-009 filtro de tipos × emissão MP/PA/PI — `PROVEN` (fronteira
  negativa).

## Interpretação

- **EM PROCESSO ≠ saldo físico do armazém 99**: é armazém de processo
  + material alocado a OPs abertas (doc 85 BR-R08-007). Pergunta clássica
  da CLARA — responder com este split.
- Valor de estoque (snapshot `as_of`) **não é comparável** com soma de
  movimentações do período (fluxo) — são medidas de natureza distinta.
- `officialP7=false`: a visão operacional replica a totalização provada,
  mas a emissão oficial do MATR460 segue no ERP — a CLARA nunca chama a
  visão de "P7 oficial".
- Divergência MP no recorte MP/PA/PI é fato provado; causa `PENDING` —
  não inventar explicação.

## Operação

- Uso: entrega à contabilidade/SPED; conciliação tripla com R08 e R05.
- Não automatizável: emissão oficial MATR460; aceite contábil.
- Comparações: `COMPARABLE` mesma medida (`totalStockValue`) entre
  competências; R03×R05 e R03×R08 = `RELATED_REQUIRES_EXPLANATION`
  (snapshot × fluxo; universos SB9 disjuntos — doc 85 §18 BR-CMP-003);
  grãos `product_type`, `warehouse` com agregações completas.

## Governança

- Evidências: docs 49/84/85 §3/118/119 §11; artefatos PDF.
- Decisões pendentes: E2 (parâmetros efetivos do MATR460); E7 (RPO);
  G6; DEC-12 (`all_products`/`mp_pi_pa`).
- Limitações: `parityStatus=PENDING` sempre declarado; recorte por
  tipo é convenção documentada, não parâmetro provado do produtor.
- Comparação transversal: suportado (`totalStockValue`, `stockTotal`;
  filtros `report_scope`, `warehouse`).
- Referências: doc 85 §3; doc 84 §3; doc 118 §6; doc 119 §11; doc 49.
