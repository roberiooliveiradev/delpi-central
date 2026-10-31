# Gate contratual — R12/R15 · Estado de fechamento de custos e cutoff (Ciclo 3)

**Gate:** `CF-PROC0072-R12-R15-STATE-VIEW-CONTRACT-GATE-021`
**Data:** 2026-10-31 · **Tipo:** `READ → INVENTORY → VERIFY → CONTRACT` —
contrato TARGET aprovado para implementação pela ordem master
`CF-PROC0072-REPORTS-CYCLE3-MASTER-EXECUTION` (GO PO 31/10/2026).
**BASE_HEAD:** `8398fc4a55` · **Inventário:** [doc 128](./128-ciclo3-inventario-consolidado-r04-r09-r12-r13-r14-r15.md).
**Autoridades:** doc 85 §11/§14/§15 (BR-R12/R15 provadas), doc 88 §4/§7 +
doc 89 (C3-D02=A aprovado), doc 118 §13 (ERP_EXEC nunca no Portal),
doc 120 pacote 017, doc 121, fichas R12/R15.

---

## 1. Premissas resolvidas por authority (não reabrem decisão)

- **D-3 (semântica):** C3-D02=**A** formalizado (doc 89) — estados
  separados por nó com fonte/proveniência própria; nunca colapsar em
  "fechado"; nunca inferir etapa/aceite sem contrato.
- **D-4 (STOCK_CLOSED):** flag canônica do workflow P3 — **nenhum writer
  novo**; esta visão lê marcadores ERP, não sincroniza `closing_stock_state`.
- **Homologação (C3-D05=A):** processo humano; superfícies exibem
  `not_informed`, nunca derivada.
- **Reabertura (C3-D03=B + E12.6):** fora de escopo — nenhuma leitura,
  ação ou histórico de reabertura.
- **E12.5:** tabela do lifecycle do wizard **não identificada** — o nó
  `wizard_lifecycle` é `unavailable` estrutural; nada é inferido.
- **Permissões congeladas**; S2S reusa `stock-inventory.read` (mesma
  família financeiro — zero provisionamento novo).

## 2. Contrato TARGET — projeção governada de estado

### 2.1 Producer — api-delpi `GET /financeiro/closing-state`

Marcadores físicos brutos (sem semântica de Portal):

- `period` (`YYYY-MM`, obrigatório) → `snapshotDate` = fim do mês.
- `branch` (`all|01|02`, filtro de dados — mesmo critério de
  stock-inventory, doc 49 §8).

Por filial autorizada:

| Campo | Fonte física | Semântica |
|---|---|---|
| `cutoffMarker.value` | `SX6010.X6_CONTEUD` `X6_VAR='MV_ULMES'`, `X6_FIL`=filial | marcador técnico de último fechamento — provado no dado (BR-R15-004) |
| `snapshot` | `SB9010` `B9_DATA=snapshotDate`, `B9_FILIAL`=filial | `available`, `rowCount`; ausência ≠ zero |
| `replacementCostEvidence` | `SB1010_TTAT_LOG` `TTAT_FIELD='B1_CUSTD'` na janela | writes/firstAt/lastAt — evidência observada do efeito MATA320 (BR-R12-001) |
| `movementCostEvidence` | `SD3010_TTAT_LOG` `TTAT_FIELD='D3_CUSTO1'` na janela | writes/firstAt/lastAt — evidência do efeito MATA330 (BR-R15-002) |

Janela de evidência: `[periodStart, periodEnd + 45 dias]` (cobre virada
posterior — f01-set gravou 21/10). `observedAt` do produtor; envelope
api-delpi padrão `success/message/data/meta`; erros tipados
(`scope_unavailable`, S2S_*, 503).

### 2.2 BFF `GET /closing/competences/{period}/cost-closing-state`

Composição governada por `(competência, filial)` — nós independentes:

| Nó | Derivação | Estados |
|---|---|---|
| `snapshot` | SB9010 | `available`/`partial` (filial faltando)/`missing` |
| `cutoff_marker` | `MV_ULMES` ≥ fim da competência | `observed`/`not_advanced`/`unavailable` |
| `cost_evidence` | TTAT writes > 0 | `observed`/`unavailable` |
| `wizard_lifecycle` | — | `unavailable` (E12.5 fixo) |
| `human_acceptance` | — | `not_informed` (C3-D05 fixo) |

`officiality`: `technical_markers` — marcadores observados, **não**
homologação nem confirmação de execução. `evidenceRefs[]` e
`limitations[]` obrigatórios (E4/E5/E12.5, G5, SB9/SX6 sem TTAT).
`NOT_COMPARABLE` — estado, não medida.

### 2.3 Matriz/CLARA/MFE

- `REPORT_CATALOG` (BFF): R12/R15 → `source_kind="STATE_VIEW"`,
  `operational_view="cost-closing-state"`, `official_parity="PENDING"`
  (visão técnica; aceite G6 humano).
- MFE: página contextual `reports/cost-closing-state` servindo R12 e
  R15 (trilha de nós por filial) — sem tela paralela nova.
- CLARA: `read(report.cost_closing_state)` — READ_ACTIONS; comparação
  segue `NOT_COMPARABLE`/`INSUFFICIENT_EVIDENCE`.
- `UNIMPLEMENTED_REPORTS`: R12/R15 saem do conjunto negativo como
  "sem contrato"; permanecem fora do catálogo comparável (sem medidas) —
  resposta honesta de comparação preservada.

## 3. RQ/AC candidatos (registrar no ledger doc 23)

| RQ | AC |
|---|---|
| RQ-C3S-01 | período+filial → nós com `state`+`evidenceRefs`; filial fora de escopo → 403 fail-closed |
| RQ-C3S-02 | SB9010 ausente → `snapshot.missing` explícito, nunca `available` nem zero |
| RQ-C3S-03 | `MV_ULMES` < fim da competência → `cutoff_marker.not_advanced` |
| RQ-C3S-04 | sem writes TTAT → `cost_evidence.unavailable` (não "não executado") |
| RQ-C3S-05 | nenhum nó afirma execução/homologação; `wizard_lifecycle` sempre `unavailable` |
| RQ-C3S-06 | 401 anônimo / 403 sem `.access`; S2S `stock-inventory.read` + client `controllership-finance-api` |
| RQ-C3S-07 | matriz mostra `STATE_VIEW`; comparação segue `NOT_COMPARABLE` |
| RQ-C3S-08 | Help + loading UX-022 + estados vazio/erro/parcial |

## 4. Matriz de segurança

Humano Bearer + `controllership-finance.access` (Core efetivo) → BFF →
api-delpi (S2S client-credentials `controllership-finance-api` +
`stock-inventory.read` + Bearer delegado; filial = filtro de dados).
Fail-closed em todas as camadas; `scope_unavailable` → 403 tipado.

## 5. Limitações declaradas (vão no contrato e na UI/Help)

- Marcador ≠ homologação; `MV_ULMES`/SB9 não provam G6.
- Escritor de SB9/`MV_ULMES` não auditável (E5); SX6/SB9 sem TTAT.
- Lifecycle do wizard indisponível (E12.5); SPs pós-MATA330 (E4).
- `I_N_S_D_T_` é UTC (−3h) — timestamps exibidos com nota de fuso.

**Parecer:** contrato determinado pelas autoridades → `READY` para
implementação mínima page-by-page com testes.
