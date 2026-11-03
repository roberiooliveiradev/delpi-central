# R15 — Cutoff / sacramentação / SB9

Versão da ficha: 1.0 · 31/10/2026 · doc 127 Etapa 4.

Estado operacional: visão de acompanhamento read-only implementada; execução de rotinas e aceite humano exigem evidência separada.

## Identificação

- Código/nome: **R15 — Cutoff / virada de saldos / sacramentação**
  (cadeia produtora do snapshot mensal de estoque).
- Finalidade: garantir que a competência foi "sacramentada" — snapshot
  `SB9010` gravado e `MV_ULMES` avançado — antes de tratar valores como
  fechados.
- Processo: PROC-0072, P3/cutoff — `PROVEN` (doc 118 §6).
- Owner funcional: Controladoria.
- Owner técnico: rotinas TOTVS (`MATA330`, `MATA280`) + leitura de
  estado na api-delpi/BFF.
- Implementação: **IMPLEMENTED** — visão de acompanhamento R12/R15 (doc 151, Gate 071); estado `STOCK_CLOSED` lido pelo
  fechamento; **não é relatório de medida** → comparação responde
  NOT_COMPARABLE — visão read-only, sem execução de rotina no Portal.
- Homologação: G3/G4 `PASS`; G5 `INCONCLUSIVE`.
- **Evidência humana ausente:** a ausência de evidência humana de aceite não é, por si só, reprovação comprovada do fechamento. O aceite humano fica `PENDING`/não demonstrado; não declarar `PASS` nem `FAIL` automaticamente. O estado técnico de cutoff deve ser consultado separadamente em `MV_ULMES`/`SB9` por filial. Essa distinção não substitui o aceite funcional da Controladoria.

## Fonte e dados

- Cadeia produtora provada por binding temporal + SX1 (doc 85 §14,
  rodada 28):
  - **`MATA330`** — Recálculo do Custo Médio (21 perguntas SX1);
    execuções observadas 30/09, 01/10, 02/10, 21/10.
  - **`MATA280`** — Virada de Saldos (serviço; "Gera Saldo Inicial");
    escreve campos de saldo inicial de OP em SC2; rajadas SB9 caem
    dentro das janelas MATA280 em **5/5 execuções** registradas —
    atribuição por timing ±4s + semântica SX1, **não** prova de insert
    auditado (SB9/SB2 sem TTAT — resíduo honesto E5).
  - **`SB9010`** — snapshot mensal íntegro por `B9_DATA`
    (`PROVEN`: cadeia ago/2025→set/2026 ambas filiais; set/2026 f01
    4.812 + f02 3.117 linhas únicas); lido por
    `stock_value_official_closure_sql` — `REUSE_CONFIRMED`.
  - **`MV_ULMES`** — marcador de último fechamento **por filial**
    (f01=f02=20260930); leitores MATR860/DLP023/DLP04F04/MATA103 —
    `PROVEN` no dado, writer `PENDING` (E5/E12).
- **Achado técnico relevante:** `I_N_S_D_T_` grava **UTC** (prova:
  SD3 recno × TTAT = exatamente −3h) — timestamps físicos −3h = horário
  local.
- Regra de cutoff literal (wizard): "o fechamento de custo só pode ser
  realizado em datas posteriores ao último fechamento" — `PROVEN`.
- Reabertura de estoque: botão existe (`AS-IS`); efeitos não
  comprovados — **E12**; owner reporta divergência de período anterior
  → reabertura+recálculo (`OWNER_REPORTED_VIA_PO`; não automatizar).
- Correções retroativas são absorvidas **antes** da virada (f01-set:
  cálculo 30/09 sem virada → virada só 21/10 após retificações) —
  `PROVEN` padrão temporal; consistente com "CPV vivo".

## Interpretação

- "O mês está fechado?" → consultar `MV_ULMES`/`SB9` por filial via
  estado governado — a CLARA não deduz por linguagem natural.
- SB9 é **snapshot as_of** — valor atual de `B2_*`/consultas vivas pode
  divergir legitimamente do snapshot (revalorização posterior).
- Reabertura é operação humana no ERP com efeitos não comprovados —
  a CLARA orienta, nunca executa nem recomenda sem evidência.
- Sem medida numérica → `NOT_COMPARABLE` contra qualquer total; pares
  com R12 idem.

## Operação

- Ação no ERP: MATA330/MATA280/wizard — nunca automatizados.
- Comparações: `NOT_COMPARABLE` (estado × medida).

## Governança

- Evidências: docs 56 Reg.11/12, 80 §47, 85 §14, 118; T-R15-01..07.
- Pendências: E5 (writer SB9/MV_ULMES), E12 (semântica de reabertura),
  G5.
- Referências: doc 85 §14; doc 118 §6; doc 121.

## Atualização v1.1 — 31/10/2026 (Ciclo 3)

- Idem R12 — gate doc 129: `MV_ULMES`/`SB9010` expostos como marcadores técnicos na projeção governada (`cutoff_marker`, `snapshot`), escritor segue `PENDING` (E5), reabertura fora de escopo (E12.6).
- Cadeia Portal: `read(report.cost_closing_state)` + página contextual `cost-closing-state`; comparação monetária continua `NOT_COMPARABLE`.
