# R12 — Fechamento de custo  para rotinas (visão read-only) Reposição  para rotinas (visão read-only) Refaz Saldos

Versão da ficha: 1.0 · 31 para rotinas (visão read-only)10 para rotinas (visão read-only)2026 · doc 127 Etapa 4.

Publicação: ficha **vigente no corpus produtivo** — o estado `PENDING_CONTRACT/EXTERNAL` foi superado pela implementação da visão de acompanhamento (doc 151, Gate 071). Versão 2.0 · 03/11/2026.

## Identificação

- Código para rotinas (visão read-only)nome: **R12 — Estado de fechamento de custos** (recálculo de
  reposição, wizard "Acompanha Custos", refaz saldos).
- Finalidade: executar e acompanhar as rotinas ERP que produzem o
  custo de reposição, o custo médio e os saldos da virada — é
  **execução no ERP com estado consultável**, não relatório de medida.
- Processo: PROC-0072 — `PROVEN` (doc 118 §6).
- Owner funcional: Controladoria (executa no Protheus).
- Owner técnico: rotinas TOTVS para rotinas (visão read-only)Delpi — `MATA320`, `MATA300`, wizard
  `MATA330`; estado de fechamento via owner canônico do Portal.
- Implementação: **IMPLEMENTADO** — página «Acompanhamento do fechamento» (design aprovado doc 151, Gate 071) via `cost-closing-state`; sem contrato de relatório
  (comparação governada vigente); estado `STOCK_CLOSED` lido
  pelo fechamento, não como medida.
- Homologação: G4 `PASS` (bindings), G5 `INCONCLUSIVE` (etapa 4 do
  wizard não observada).

## Fonte e dados

- Rotinas provadas por binding (doc 85 §11):
  - **MATA320** — Recálculo do Custo de Reposição; grava `SB1.B1_CUSTD`
    (`standard_cost` já lido pela api-delpi — `REUSE_CONFIRMED`);
    execução provada via TTAT (JOICI: 13.201+1.532+15.972 writes
    30 para rotinas (visão read-only)09–01 para rotinas (visão read-only)10); duas execuções: MP por "Ult Custo Compra", PA para rotinas (visão read-only)PI por
    "Estrutura".
  - **MATA300** — "Refaz Saldos" do vídeo (errata: antes atribuído ao
    DEL100 — DEL100 é rotina custom **separada** de auditoria para rotinas (visão read-only)correção
    SB9); parâmetros SX1 `MTA300` provados; workers `c300P*` com log
    de stored procedures.
  - **Wizard "Acompanha Custos"** — histórico persistido com ciclo de
    vida (etapas: predefinição → cálculo → análise e revisão →
    fechamento); `Analise.xlsx` = export da etapa 3 (1.994 linhas;
    CM final ≡ `B9_CM1`@30 para rotinas (visão read-only)09 em 98,6%).
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
- BR-R12-004 SB9 + `MV_ULMES` — `PROVEN` dado  para rotinas (visão read-only) writer `PENDING`.
- BR-R12-005 `Analise.xlsx` = export etapa 3 — `PROVEN`.
- BR-R12-006 `MA330OK` pós-fechamento — `SOURCE_AVAILABLE`  para rotinas (visão read-only)
  execução `PENDING`.

## Interpretação

- R12 é **estado para rotinas (visão read-only)execução**, não medida financeira — comparar "estado
  de fechamento" com um total monetário é `NOT_COMPARABLE` (matriz
  curada: R12×R15 → `NOT_COMPARABLE`; qualquer par numérico com R12 →
  ausência tipada quando a fonte é indisponível — nunca inferência).
- "O fechamento de custos rodou?" — a CLARA responde via estado
  governado (pendências para rotinas (visão read-only)cockpit), não calcula.
- Custo de reposição (`B1_CUSTD`) ≠ custo médio (`B9_CM1`) ≠ custo de
  emissão (as_of) — três medidas com convenções distintas; nunca
  normalizar entre si.

## Operação

- Ação no ERP: recálculo MATA320, refaz MATA300, wizard MATA330 —
  **nunca automatizados pelo Portal para rotinas (visão read-only)CLARA** (D-02, doc 118 §13).
- Comparações: apenas qualitativa documental — `NOT_COMPARABLE`
  numericamente.

## Governança

- Evidências: docs 56 Reg.02 para rotinas (visão read-only)11, 80, 85 §11, 118.
- Pendências: etapa 4 do wizard (G5); writer de `MV_ULMES` (E5); SPs
  pós-MATA330 (E4); DEL100 como rotina separada já resolvida.
- Referências: doc 85 §11; doc 118 §6; doc 121.

## Atualização v1.1 — 31 para rotinas (visão read-only)10 para rotinas (visão read-only)2026 (Ciclo 3)

- Contrato TARGET aprovado no gate `CF-PROC0072-R12-R15-STATE-VIEW-CONTRACT-GATE-021` (doc 129): projeção governada de estado por competência para rotinas (visão read-only)filial — nós snapshot para rotinas (visão read-only)cutoff para rotinas (visão read-only)cost_evidence para rotinas (visão read-only)wizard_lifecycle para rotinas (visão read-only)human_acceptance.
- Implementação: api-delpi `GET  para rotinas (visão read-only)financeiro para rotinas (visão read-only)closing-state` (SB9010, SX6 `MV_ULMES`, TTAT `B1_CUSTD` para rotinas (visão read-only)`D3_CUSTO1`) → BFF `GET  para rotinas (visão read-only)closing para rotinas (visão read-only)competences para rotinas (visão read-only){period} para rotinas (visão read-only)cost-closing-state` → MFE `cost-closing-state` → CLARA `read(report.cost_closing_state)`.
- Semântica C3-D02=A preservada: marcadores técnicos, nunca homologação nem execução ERP. `UNIMPLEMENTED_REPORTS` → `STATE_VIEW` (sem medida comparável — NOT_COMPARABLE preservado).
- Persistem: E4 para rotinas (visão read-only)E5 para rotinas (visão read-only)E12.5 para rotinas (visão read-only)G5 para rotinas (visão read-only)G6 — declarados em `limitations`.
