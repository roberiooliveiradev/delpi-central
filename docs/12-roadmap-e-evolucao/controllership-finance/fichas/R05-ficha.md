# R05 — Entradas e Saídas (MATR320)

Versão da ficha: 1.0 · 31/10/2026 · doc 127 Etapa 4.

Publicação: **release produtivo stage-05** (30/10/2026, srv-api, SHA `297068f1b7`) — serviço reconstruído e paridade verificada em produção; corpus `5bebf07f-a66a-479f-aa2b-e7d0e6c7ea00` (88 fontes / 2.186 itens).

## Identificação

- Código/nome: **R05 — Resumo de Entradas e Saídas em R$** (MATR320).
- Finalidade: fluxo monetário do estoque na competência por produto —
  entradas, saídas, saldo inicial/final; peça da conciliação tripla
  (com R03 e R08).
- Processo: PROC-0072, P3 — `PROVEN` (doc 118 §6).
- Owner funcional: Controladoria (conciliação).
- Owner técnico: `api-delpi` + `controllership-finance-api`.
- Produtor oficial: `MATR320.prt` padrão via SP `MAT056` —
  `SOURCE_AVAILABLE`; a variante `Dmatr320.prx`/`DLPR320` (zera poder
  de terceiros) **não** foi a usada na emissão de referência.
- Implementação: **`IMPLEMENTED`** (IMPLEMENTATION-009, 29/10) —
  `/closing/stock-movements` + export: matriz MATR320
  (SD1/SD2/SD3/SF4 + SA SB9), `report_scope=all_products|mp_pi_pa`;
  `officialMatr320=false`, `parityStatus=PENDING` (doc 119 §12).
- Homologação: G1–G5 `PASS`; G6 `PENDING`.

## Fonte e dados

- Artefato: `Entradas e saidas.pdf` (01/09–30/09/2026, Matriz).
- Tabelas: SD1 (entradas), SD2 (saídas), SD3 (internas), SF4 (TES),
  SB9 (saldo inicial do recorte).
- Grão: produto (linha de resumo). Eixo: competência. Filial: Matriz
  na emissão de referência.
- Capability CLARA: `read(report.stock_movements)`.

## Regras de negócio (doc 85 §5)

- BR-R05-001 eixos do relatório — `PROVEN` (fonte).
- BR-R05-002 Saldo Atual = SB9 no recorte — `PROVEN` (10/10 tipos).
- BR-R05-003 seleção física por tabela — `PROVEN`.
- BR-R05-004/005 classificação SD1/SD2 e SD3 — `PROVEN` (matches exatos).
- BR-R05-006 Saldo Atual e Saldo Inicial — `PROVEN`.
- BR-R05-007 reconciliação coluna a coluna — `PROVEN` (ao centavo).
- BR-R05-011 reconstrução `as_of` de custos via TTAT — `PROVEN`.
- BR-R05-012 ponte emissão→snapshot por produto — `PROVEN`.
- BR-R05-008 retificações retroativas alteram leitura histórica —
  `PROVEN`.
- BR-R05-009 armazéns especiais — `AS-IS` (constantes).
- BR-R05-010 identidade da SP e janela SD1 — `TO_INVENTORY`.

## Interpretação

- **Fluxo × snapshot:** o R05 mede movimento monetizado no período;
  comparar seu "saldo final" com o R03 é válido via reconciliação, não
  por igualdade direta de medidas.
- Retificação retroativa (reemissão/recálculo) altera a leitura
  histórica — um valor "diferente do PDF antigo" pode ser retificação
  legítima, não erro.
- Medidas disponíveis: `sales`, `purchases`, `netMovement`,
  `closingBalance`, `openingBalance` — grão `product_type`.

## Operação

- Uso: conciliação tripla com R03 (posição) e R08 (processo).
- Não automatizável: emissão oficial MATR320; aceite contábil.
- Comparações: `COMPARABLE` mesma medida entre competências/filiais;
  R05×R06 = `RELATED_REQUIRES_EXPLANATION` (fluxo resumido × kardex
  valorizado linha a linha — doc 85 §18); demais pares por default
  `INSUFFICIENT_EVIDENCE`.

## Governança

- Evidências: docs 62/84 §4/85 §5; artefato PDF.
- Decisões pendentes: G6; identidade SP (BR-R05-010).
- Limitações: `officialMatr320=false` declarado; recorte por tipo segue
  convenção documentada.
- Comparação transversal: suportado (grãos `product_type`).
- Referências: doc 85 §5; doc 84 §4; doc 118 §6; doc 119 §12.
