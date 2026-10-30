# R01 — Baixas a pagar

Versão da ficha: 1.0 · 31/10/2026 · doc 127 Etapa 4.

Publicação: **release produtivo stage-05** (30/10/2026, srv-api, SHA `297068f1b7`) — serviço reconstruído e paridade verificada em produção; corpus `5bebf07f-a66a-479f-aa2b-e7d0e6c7ea00` (88 fontes / 2.186 itens).

## Identificação

- Código/nome: **R01 — Baixas a pagar** (contas a pagar baixadas).
- Finalidade: conferir títulos pagos na competência por data e por
  natureza — base documental enviada à contabilidade no fechamento.
- Processo: PROC-0072, etapa P2/P3 (documental) — `PROVEN` (doc 118 §6).
- Owner funcional: Controladoria (análise) / Contabilidade (consumo).
- Owner técnico: `api-delpi` (produtor SE5/SE2/SED/F7G) +
  `controllership-finance-api` (BFF).
- Produtor do relatório oficial: `FINR190` + `FINR190_DLP.PRX`, layouts
  `DLP06R01.prt`/`nat.prt` — `PROVEN` (doc 85 §1, fonte no acervo).
- Implementação: **`IMPLEMENTED`** — Portal `/closing/financial-settlements*`
  + api-delpi `/financeiro/baixas/*`.
- Homologação: G1–G5 `PASS`; G6 (aceite funcional) `PENDING`.
  Paridade doc 84 §1 — `PROVEN` nos artefatos `Pagos por dt.pdf`,
  `Pagos por nat.pdf`, `pagos 09 26.xlsb` (948 linhas).

## Fonte e dados

- Tabelas: SE5 (baixas) × SE2 (títulos pagar) × SED (naturezas) × F7G —
  `PROVEN` (doc 85 §1).
- Artefatos de referência: `pagos 09 26.xlsb` (948 linhas de dados),
  `Pagos por dt.pdf` (33p), `Pagos por nat.pdf` (35p).
- Grão: baixa financeira (linha SE5).
- Eixo temporal: `E5_DATA` (data da baixa) por competência.
- Filial: dimensão de dado (`Orig` no relatório oficial).
- API operacional: `/closing/financial-settlements` (BFF → api-delpi
  `/financeiro/baixas/*`), agrupamento por natureza e tipo de movimento.
- Capability CLARA: `read(report.settlements_summary)`.

## Regras de negócio (doc 85 §1)

- BR-R01-001 população base — `PROVEN`.
- BR-R01-002 pareamento de estornos — `PROVEN`.
- BR-R01-003 `Total Baixado` — `PROVEN` (emissão observada).
- BR-R01-004 `Valor Original` — `PROVEN` (3 regras físicas).
- BR-R01-005/006 relacionamentos e resumos impressos — `PROVEN`.
- BR-R01-007 componentes monetários — `PROVEN`.
- BR-R01-008 coluna `Orig` (filial origem) — `PROVEN`.
- BR-R01-009 XLSB × PDF × log de inconsistências — `PROVEN` agregado /
  `PENDING` em linhas.
- BR-R01-011 layout ≠ produtor — `PROVEN` (layout custom não prova
  identidade do código implantado — E7).

## Interpretação

- O relatório mostra baixas **realizadas** na competência; não mostra
  títulos em aberto nem provisões — não usar como posição de dívida.
- Totais por natureza dependem do cadastro SED vigente na emissão;
  natureza alterada depois desloca a leitura histórica.
- Estornos são pareados (não aparecem como lançamentos negativos
  soltos) — doc 85 BR-R01-002.
- Divergência consulta operacional × PDF oficial: a consulta é
  **visão auxiliar**; paridade oficial só após emissão FINR190
  homologada — ver doc 121 matriz.

## Operação

- Uso: envio à contabilidade como documento do fechamento (P2); a CLARA
  orienta onde conferir no ERP (FINR190, consulta SE5 por `E5_DATA`).
- Não automatizável: emissão oficial do FINR190, aceite contábil.
- Comparações válidas: mesma medida (`totalAmount`, `eventCount`) entre
  competências/filiais — `COMPARABLE`.
- Comparações com explicação: R01×R02 (mesma estrutura, sinal oposto —
  nunca somar baixas a pagar e a receber); R05×R01 não é equivalente
  (fluxo financeiro × fluxo de estoque) — `RELATED_REQUIRES_EXPLANATION`
  / `INSUFFICIENT_EVIDENCE` conforme a matriz curada.

## Governança

- Evidências: docs 83/84/85 §1; artefatos XLSB/PDF; paridade doc 84 §1.
- Decisões pendentes: G6; confirmação de parâmetros de emissão (E10
  marginal); versão RPO (E7).
- Limitações: consulta operacional não é relatório oficial; sem
  permission específica além de `controllership-finance.access`.
- Comparação transversal: suportado pelo motor stage-03 (measures
  `totalAmount`, `eventCount`; grains `nature`, `movement_type`;
  filtros `side`, `nature_code`, `movement_type`).
- Referências: doc 85 §1; doc 84 §1; doc 118 §6; doc 121.
