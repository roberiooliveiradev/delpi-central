# R12 — Fechamento de custo / Reposição / Refaz Saldos

Versão da ficha: 1.0 · 31/10/2026 · doc 127 Etapa 4.

## Identificação

- Código/nome: **R12 — Estado de fechamento de custos** (recálculo de
  reposição, wizard "Acompanha Custos", refaz saldos).
- Finalidade: executar e acompanhar as rotinas ERP que produzem o
  custo de reposição, o custo médio e os saldos da virada — é
  **execução no ERP com estado consultável**, não relatório de medida.
- Processo: PROC-0072 — `PROVEN` (doc 118 §6).
- Owner funcional: Controladoria (executa no Protheus).
- Owner técnico: rotinas TOTVS/Delpi — `MATA320`, `MATA300`, wizard
  `MATA330`; estado de fechamento via owner canônico do Portal.
- Implementação: **`TARGET_ONLY`** — sem contrato de relatório
  (`report_not_implemented` na comparação); estado `STOCK_CLOSED` lido
  pelo fechamento, não como medida.
- Homologação: G4 `PASS` (bindings), G5 `INCONCLUSIVE` (etapa 4 do
  wizard não observada).

## Fonte e dados

- Rotinas provadas por binding (doc 85 §11):
  - **MATA320** — Recálculo do Custo de Reposição; grava `SB1.B1_CUSTD`
    (`standard_cost` já lido pela api-delpi — `REUSE_CONFIRMED`);
    execução provada via TTAT (JOICI: 13.201+1.532+15.972 writes
    30/09–01/10); duas execuções: MP por "Ult Custo Compra", PA/PI por
    "Estrutura".
  - **MATA300** — "Refaz Saldos" do vídeo (errata: antes atribuído ao
    DEL100 — DEL100 é rotina custom **separada** de auditoria/correção
    SB9); parâmetros SX1 `MTA300` provados; workers `c300P*` com log
    de stored procedures.
  - **Wizard "Acompanha Custos"** — histórico persistido com ciclo de
    vida (etapas: predefinição → cálculo → análise e revisão →
    fechamento); `Analise.xlsx` = export da etapa 3 (1.994 linhas;
    CM final ≡ `B9_CM1`@30/09 em 98,6%).
  - **MA330OK** — ponto de entrada pós-MATA330 chamando
    `STP_DELPI_OP_TERCEIRO` + `STP_PROTHEUS_DELPI_AJUSTA_OP`
    (`SOURCE_AVAILABLE`; SPs ausentes — execução `PENDING`, E4).
- Persistência: `SB9010` + `MV_ULMES` por filial — `PROVEN` no dado,
  writer `PENDING` (E5).

## Regras de negócio (doc 85 §11)

- BR-R12-001 MATA320 ↔ `B1_CUSTD` — `PROVEN` (rotina + efeito).
- BR-R12-002 wizard 4 etapas — `AS-IS` (`EXECUTION_OBSERVED` etapas
  1–3; etapa 4 `PENDING` — G5).
- BR-R12-003 Refaz Saldos = MATA300 — `PROVEN` (binding; errata
  incorporada).
- BR-R12-004 SB9 + `MV_ULMES` — `PROVEN` dado / writer `PENDING`.
- BR-R12-005 `Analise.xlsx` = export etapa 3 — `PROVEN`.
- BR-R12-006 `MA330OK` pós-fechamento — `SOURCE_AVAILABLE` /
  execução `PENDING`.

## Interpretação

- R12 é **estado/execução**, não medida financeira — comparar "estado
  de fechamento" com um total monetário é `NOT_COMPARABLE` (matriz
  curada: R12×R15 → `NOT_COMPARABLE`; qualquer par numérico com R12 →
  `INSUFFICIENT_EVIDENCE`/`report_not_implemented`).
- "O fechamento de custos rodou?" — a CLARA responde via estado
  governado (pendências/cockpit), não calcula.
- Custo de reposição (`B1_CUSTD`) ≠ custo médio (`B9_CM1`) ≠ custo de
  emissão (as_of) — três medidas com convenções distintas; nunca
  normalizar entre si.

## Operação

- Ação no ERP: recálculo MATA320, refaz MATA300, wizard MATA330 —
  **nunca automatizados pelo Portal/CLARA** (D-02, doc 118 §13).
- Comparações: apenas qualitativa documental — `NOT_COMPARABLE`
  numericamente.

## Governança

- Evidências: docs 56 Reg.02/11, 80, 85 §11, 118.
- Pendências: etapa 4 do wizard (G5); writer de `MV_ULMES` (E5); SPs
  pós-MATA330 (E4); DEL100 como rotina separada já resolvida.
- Referências: doc 85 §11; doc 118 §6; doc 121.
