# R02 — Baixas a receber

Versão da ficha: 1.0 · 31/10/2026 · doc 127 Etapa 4.

Publicação: **release produtivo stage-05** (30/10/2026, srv-api, SHA `297068f1b7`) — serviço reconstruído e paridade verificada em produção; corpus `5bebf07f-a66a-479f-aa2b-e7d0e6c7ea00` (88 fontes / 2.186 itens).

## Identificação

- Código/nome: **R02 — Baixas a receber** (contas a receber baixadas).
- Finalidade: conferir recebimentos da competência — contraparte de R01
  no pacote documental do fechamento.
- Processo: PROC-0072 — `PROVEN` (doc 118 §6).
- Owner funcional: Controladoria / Contabilidade.
- Owner técnico: `api-delpi` + `controllership-finance-api`.
- Produtor do relatório oficial: `DLP06R01` custom —
  **`SOURCE_MISSING`** (fonte ausente do acervo; E1 com TI/ERP).
- Implementação: **`IMPLEMENTED`** — compartilha contrato de R01
  (`/closing/financial-settlements`, `side=receivable`).
- Homologação: G5 `PASS` (paridade agregada com o artefato), G4
  `PENDING` — toda regra provém de paridade, não de leitura de código;
  G6 `PENDING`.

## Fonte e dados

- Tabelas: SE5 × SE1 (títulos receber) × SED — `PROVEN` por paridade.
- Artefatos: `Recebidos.pdf` (36p), `Recebidos.xlsb` (657 linhas).
- Grão: baixa financeira. Eixo: `E5_DATA`. Filial: coluna `Orig`
  (semântica distinta da de R01 — doc 85 BR-R02-007 `PROVEN`).
- Capability CLARA: `read(report.settlements_summary)`.

## Regras de negócio (doc 85 §2 — todas por paridade, não por fonte)

- BR-R02-001 população do artefato — `PROVEN`.
- BR-R02-002 exclusões observadas — `AS-IS`; regra geral `PENDING`
  (sem fonte, não é possível afirmar o predicado completo).
- BR-R02-003 `Total Baixado` — `PROVEN`.
- BR-R02-004 `Valor Original` — `PROVEN` (2 regras físicas).
- BR-R02-005 resumos e componentes — `PROVEN`.
- BR-R02-006 XLSB × PDF — `PROVEN` agregado.
- BR-R02-007 coluna `Orig` — `PROVEN` (semântica distinta do pagar).
- BR-R02-008 produtor — `PENDING` (E1).

## Interpretação

- Mesma família de leitura de R01 com sinal oposto; nunca combinar
  totais de baixas a pagar × a receber em uma única medida.
- Sem o fonte, regras de exclusão finas são `PENDING` — a CLARA deve
  explicar que a seleção é provada por paridade, não por código.
- Divergência pontual linha-a-linha entre XLSB e PDF é registrada em
  log de inconsistências (mesmo padrão de R01).

## Operação

- Uso: pacote documental P2; conferência com a contabilidade.
- Não automatizável: emissão oficial `DLP06R01`, aceite contábil.
- Comparações: `COMPARABLE` intra-R02; `RELATED_REQUIRES_EXPLANATION`
  com R01 (mesma estrutura, sinal oposto); demais pares
  `INSUFFICIENT_EVIDENCE` por default.

## Governança

- Evidências: docs 83/84/85 §2; doc 80 §30 (errata); artefatos.
- Decisões pendentes: **E1** — fonte `DLP06R01` a confirmar com TI/ERP;
  G4/G6.
- Comparação transversal: suportado (`totalAmount`, `eventCount`;
  grains `nature`, `movement_type`; filtro `side=receivable`).
- Referências: doc 85 §2; doc 84 §2; doc 118 §6; doc 121.
