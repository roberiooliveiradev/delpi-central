# R07 — Inventários (ajustes)

Versão da ficha: 1.0 · 31/10/2026 · doc 127 Etapa 4.

## Identificação

- Código/nome: **R07 — Ajustes de inventário** (recorte MATR910).
- Finalidade: listar os ajustes de estoque da competência — quantidade
  e custo, entrada/saída — para conferência de divergências físicas.
- Processo: PROC-0072, P3 — `PROVEN` (doc 118 §6).
- Owner funcional: Controladoria.
- Owner técnico: `api-delpi` + `controllership-finance-api`.
- Produtor oficial: `MATR910` filtrado — mesmo produtor do R06.
- Implementação: **`IMPLEMENTED`** (IMPLEMENTATION-015) —
  `/closing/inventory-adjustments` (f02 loc 01+99 na evidência de
  paridade); paridade oficial `PENDING` (E8/G6).
- Homologação: G1–G5 `PASS`; G6 `PENDING`.

## Fonte e dados

- Artefato: `Invent.xlsb` (50 linhas, 45 movimentos efetivos — f02,
  loc 01+99).
- Seleção física: `SD3` com `D3_DOC='INVENT'`; TES **999/RE0** (saída)
  e **499/DE0** (entrada) — `PROVEN` (doc 85 §7).
- Grão: linha de movimento SD3. Eixo: `D3_EMISSAO`. Custo: `D3_CUSTO1`
  as_of.
- Capability CLARA: `read(report.inventory_adjustments)`.

## Regras de negócio (doc 85 §7)

- BR-R07-001 artefato = kardex filtrado a INVENT — `PROVEN`.
- BR-R07-002 semântica: entrada DE0 soma, saída RE0 subtrai; custo as_of;
  saldo impresso na linha — `PROVEN`.
- BR-R07-003 reconciliação 45/45 linhas ao SD3 (10 via `TTAT_OLD` de
  revalorização) — `PROVEN`. Totais oficiais: entradas 2.348,108 /
  R$185.103; saídas 30.808,206; líquido −28.460,098.

## Interpretação

- Ajuste de inventário **é um subconjunto** dos movimentos SD3 do
  kardex — comparar R07 × R06 é relacionado, não equivalente:
  `RELATED_REQUIRES_EXPLANATION`.
- Volume alto de ajustes sugere investigação de processo (acuracidade)
  — a CLARA **sustenta** a hipótese com dados reais (`read`), nunca
  afirma causa sem evidência. Pergunta "por que tantos ajustes?" exige
  consulta aos dados da competência + ficha para interpretar.
- Medidas: `totalValue`, `entryValue`, `outputValue`, `movementCount`,
  `documentCount`.

## Operação

- Uso: conferência mensal de divergências físicas; evidência P2.
- Não automatizável: execução do inventário no ERP; emissão oficial.
- Comparações: `COMPARABLE` entre competências/filiais na mesma medida;
  R07×R06 relacionado; R07×R08 `INSUFFICIENT_EVIDENCE` por default.

## Governança

- Evidências: docs 66/84/85 §7/122.
- Pendências: parâmetro de armazém da emissão; E7/E8; G6.
- Limitações: escopo loc-99 entra por armazém — filtrar por local
  exige o filtro governado, não interpretação.
- Comparação transversal: suportado pelo motor stage-03.
- Referências: doc 85 §7; doc 84; doc 118 §6; doc 122.
