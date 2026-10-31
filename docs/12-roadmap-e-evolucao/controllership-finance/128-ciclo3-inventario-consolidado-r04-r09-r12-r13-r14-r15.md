# Inventário consolidado — Ciclo 3 · relatórios R04/R09/R12/R13/R14/R15

**EXECUTION_ID:** `CF-PROC0072-REPORTS-CYCLE3-INVENTORY-00` (Etapa 00 do
master `CF-PROC0072-REPORTS-CYCLE3-MASTER-EXECUTION`).
**Data:** 2026-10-31 · **Tipo:** `READ → INVENTORY → VERIFY → CLASSIFY` —
documental, **zero runtime/migration/deploy**.
**BASE_HEAD (inventário):** `2ff4193b8c` · **HEAD revalidado:** `8398fc4a55`
(main — avanço concorrente apenas em `tv-dashboard-api`/vista; zero impacto
no escopo Controladoria).
**GIT_STATUS:** working tree com alterações preexistentes de outros
workstreams (UX-022 staged em `plugins/controllership-finance/src/features/
closing/*`, products engineering, CAIO, etc.) — inventariadas e
**preservadas**; nenhuma usada como evidência nem incluída em commits deste
ciclo.
**Autoridades consultadas:** docs 23, 80, 81, 82, 83, 85, 88, 89, 113, 118,
120, 121, 122, 126, 127, fichas R01–R15 + `fichas/README.md`, README do
produto, instruções oficiais do GPT Arquiteto, `.cursor/rules`, código no
HEAD (`api-delpi`, `controllership-finance-api`,
`plugins/controllership-finance`), migrations V001–V019, catálogo MCP.

---

## 1. Matriz AS-IS → TARGET (estado real no HEAD)

| Relatório | Artefato oficial | api-delpi (producer) | BFF cf-api | MFE | CLARA (MCP) | Estado |
|---|---|---|---|---|---|---|
| R01/R02 | SE5/artefatos | `/financeiro/settlements/*` | `/closing/financial-settlements*` | `FinancialSettlementsPage` | `read(report.settlements[/_summary])` | `PROVEN` operacional · paridade/G6 `PENDING` |
| R03/P7 | MATR460 | `/financeiro/stock-inventory` (SB9010) | EXISTS | `StockInventoryPage` | `read(report.stock_inventory)` | `PROVEN` · E2 `PENDING` |
| R05 | MATR320 | `/financeiro/stock-movements` (SD1/SD2/SD3+SF4) | EXISTS | `StockMovementsPage` | `read(report.stock_movements)` | `PROVEN` · paridade `PENDING` |
| R06/R07 | MATR910/INVENT | `/financeiro/stock-kardex*` + `/inventory-adjustments*` | EXISTS | `StockKardexPage`/`InventoryAdjustmentsPage` | `read(report.stock_kardex[/_summary])`, `.inventory_adjustments[/_summary]`, `.cpv` | `PROVEN` (stage-05 live) |
| R08/H02 | MATR989 | `/financeiro/work-in-process` (SD3 `RE*/DE*`+SC2) | EXISTS | `WorkInProcessPage` | `read(report.work_in_process)` | `PROVEN` · E8 `PENDING` |
| R10/R11 | EDAPP/roster | `/financeiro/cost-center-expenses`, `/billing-exclusion-roster` | EXISTS | páginas próprias | `read(report.cost_center_expenses)`, `.billing_exclusion_roster` | `PROVEN` (stage-05 live) |
| **R04** | **ausente — GAP-01** | — | `PENDING_CONTRACT` | ausente | nenhuma | **`BLOQUEADO`** |
| **R09** | `Fat x MOD.xlsb` `PROVEN` 4.476/4.476 | perna faturamento `EXISTS`; perna MOD ausente | `PENDING_CONTRACT` | ausente | ficha `TARGET` publicada | **`DESIGN_READY`** (E9 residual) |
| **R12** | rotinas + `Analise.xlsx` | probes parciais (TTAT/`B1_CUSTD`) | `PENDING_CONTRACT`; `closing_stock_state` passivo | `canonical_stock_state` em P3/cockpit | ficha `TARGET` | **`DESIGN_READY` condicional** |
| **R15** | SB9010+`MV_ULMES` `PROVEN` | SB9010 já lido; `MV_ULMES` legível via SX6 | `PENDING_CONTRACT`; cutoff P3 governado | `P3CutoffPanel` (workflow) | ficha `TARGET` | **`DESIGN_READY` condicional** |
| **R13** | fonte externa | n/a | pipeline P2 + 12 itens `EXTERNAL` semeados | `MonthlyDocumentsPanel` | ficha `TO_INVENTORY` | **Opção A já materializada** |
| **R14** | nenhum artefato | n/a | 4 itens `EXTERNAL` semeados | idem | ficha `TO_INVENTORY` | **`BLOQUEADO` funcional** |

Fatos transversais verificados no HEAD:

- **G6 = 0/15** — nenhuma homologação humana registrada; nada pode ser
  apresentado como homologado.
- **Permissões congeladas** em código
  (`controllership-finance-api/.../authz.py:21-26`): `.access`, `.manage`,
  `.access.dre` — nenhuma permission por relatório será criada.
- **Corpus produtivo `5bebf07f`** publicado 30/10 (88 fontes/2.186 itens,
  17 fichas) — fichas R01–R15 **já publicadas**; ciclo 3 **versiona**,
  não duplica.
- Motor de comparação genérico e fail-closed em produção:
  `domain/report_comparison/` (`UNIMPLEMENTED_REPORTS` = R04/R09/R12/R15
  `PENDING_CONTRACT`; R13/R14 `EXTERNAL`; pares curados R09×R10
  `RELATED_REQUIRES_EXPLANATION`, R12×R15 `NOT_COMPARABLE`).

## 2. Achados que alteram premissas do plano-mestre (drift relativo)

1. **CLARA não mora em `minha-delpi-ai-api`** — superfície MCP própria
   dentro da `controllership-finance-api` (`interface/mcp/`, 6 tools
   semânticos congelados + registro `(entity,action)` em
   `semantic_bridge.py`). "Capability no catálogo" = entrada em
   `READ_ACTIONS` + `REPORT_CATALOG` + ficha — **não** é provider
   OpenAPI do chat.
2. **R09: MOD vem de roteiro, não só de estrutura** — cadeia documentada
   SD2/SF4 + `SHY010` (roteiro congelado da OP, `HY_TEMPAD`) + `SG2010`
   (fallback `G2_TEMPAD`) + `SH1010`/`SHB010` (CC MOD via `H1_CCUSTO`,
   ressalva `CT-01C` f02) + `SBZ010.BZ_CUSTD` (rate `as_of` via
   `SBZ010_TTAT_LOG`). SG1 participa da expansão de âncoras quando
   aplicável. Nenhuma dessas tabelas é lida hoje pela api-delpi.
3. **E9 é mais estreito que "não recriar"** — modelo físico `PROVEN`
   item a item (4.476/4.476) por reprodução documentada
   (BR-R09-003..011). Residual E9: SP `STP_DELPI_FORMA_PRECO_*` ausente,
   versão RPO do DLP204 não vinculada, 27 linhas residuais, divisor de
   desdobramento `PENDING`, 7 MODs sem SBZ. A decisão material é
   **E6-D1..D6** (`IMPLEMENTATION_AUTHORIZED=NO`, docs 81/82).
4. **Lifecycle do wizard não identificado** — a lista `Fechamentos`
   persiste ciclo de vida na UI Protheus (`EXECUTION_OBSERVED`, doc 85
   BR-R15-005) mas a **tabela física não foi localizada em nenhum banco
   acessível** (doc 88 §2 → `PENDING_EVIDENCE`, E12.5). Proibição
   vigente: não inferir "concluído" de saldo preenchido.
5. **Defeito latente no MFE (real, reproduzido no HEAD):**
   `MonthlyReportsPanel.tsx` — `reportAvailable` (~L1130) e o bloco de
   badge dos cards (~L1305) atribuem o status do operando `h02` (R08) a
   `stock-kardex`, `inventory-adjustments`, `cost-center-expenses`,
   `billing-exclusion-roster` e `cpv`. Verificado no diff: o trabalho
   staged de UX-022 **não** toca essa lógica — correção independente.
6. **Nuance do catálogo MCP:** `_semantic_catalog` exibe `gate="access"`
   para todos os reads; gates efetivos divergem (catalog/template =
   `manage`, received = `access.dre`) — metadata display-only, não
   autoriza.
7. **Doc-name collision:** doc 62 trata de MATR320 (relatório R05),
   não da rotina `MATA320` (R12).

## 3. Decisões de autoridade já existentes (resolvem parte de D-3/D-4)

Doc 89 (24/10/2026) formalizou **C3-D01..D06 = A/A/B/B/A/A** para escopo
e design, `IMPLEMENTATION_AUTHORIZED=NO` à época:

- **C3-D02=A (vigente):** estados separados — cálculo → persistência →
  conferência → homologação — cada nó com fonte/proveniência própria;
  **nunca** colapsar em "fechado"; nunca inferir etapa/aceite sem
  contrato/evidência. → **é a semântica aprovada para o contrato
  R12/R15 (D-3 resolvido na semântica)**.
- **C3-D03=B:** reabertura fora de qualquer superfície (E12.6 pendente).
- **C3-D04=B (escopo V1 apenas):** `closing-context`/`MV_ULMES` adiado
  **como requisito da primeira fatia** — não é revogação; o pacote 017
  do doc 120 (29/10, posterior) e a ordem master PO (31/10) reabrem o
  contrato com gate próprio.
- **C3-D05=A:** homologação exclusivamente humana — superfícies nunca
  afirmam aceite (G6 = processo humano fora do sistema).
- **C3-D06=A:** excluir superfícies sem fonte/contrato comprovado.
- **D-4 (STOCK_CLOSED):** `closing_stock_state` é flag canônica do
  workflow P3, sincronizada pelo owner — **nenhuma rota a escreve**
  (`p3_routes.py` §header; RQ-P3-08). O contrato R12/R15 **lê marcadores
  ERP** e não cria writer nem owner paralelo — a projeção governada é
  evidência observada, distinta do flag de workflow.

## 4. Matriz de reuso (produtor → consumidor)

| Necessidade | Reuso candidato | Classe |
|---|---|---|
| R09 perna faturamento | `commercial_rol_return_sql` (regra canônica TES `F4_DUPLIC`, SD2+SD1) | `REUSE_CONFIRMED` |
| R09 roteiro MOD/tempos | `SHY010`/`SG2010`/`SH1010`/`SHB010` — **leituras novas** | `TARGET` |
| R09 rate as-of | padrão TTAT (`SBZ010_TTAT_LOG`, mesma técnica do kardex) | `REUSE_PARTIAL` |
| R04 motor SD3 `RE*/DE*` por OP | `work_in_process_sql.py` (grão provado R08) + `/supplies/consumption-audit` (S2S-locked a supplies-api) | `REUSE_POSSIBLE` (equivalência não provada — GAP-01) |
| R12/R15 snapshot | `stock_value_official_closure_sql` (SB9010 por `B9_DATA`) | `REUSE_CONFIRMED` |
| R12/R15 marcador cutoff | `build_sx6_param_query` (leitor SX6 genérico → `MV_ULMES`) | `REUSE_CONFIRMED` (mecanismo existe; `MV_ULMES` nunca lido) |
| R12 evidência MATA320 | `SB1010_TTAT_LOG` (writes `B1_CUSTD`; batches JOICI observados doc 85 §11) | `REUSE_PARTIAL` (probe novo, mesmo padrão TTAT) |
| R13/R14 | pipeline documental P2 completo (upload idempotente, versões, validação `manage`, recipient DRE, audit) | `REUSE_CONFIRMED` |

## 5. Contratos existentes × candidatos

Existentes (BFF): settlements, stock-inventory, stock-movements,
work-in-process, stock-kardex(+3), inventory-adjustments(+2), cpv,
cost-center-expenses, billing-exclusion-roster, report matrix
(`/closing/competences/{period}/reports`), `POST /closing/analysis/
report-comparison`, pipeline documental P2 completo, cutoff P3
governado (`/p3`, `/p3/cutoff`, `/closing-state`, `/cockpit`).

Candidatos (rótulos do doc 85 §15 — **não são endpoints aprovados**):

| Pacote | Rótulo | Base | Estado |
|---|---|---|---|
| R12+R15 | `cost-closing-run` / `month-end-stock` | marcadores `PROVEN` (SB9010, `MV_ULMES`, TTAT `B1_CUSTD`) | gate aberto por este ciclo (doc 129) |
| R09 | `billing-mod-breakdown` + `mod-cost-rate` | modelo `PROVEN` 4.476/4.476; E6=C direção | `DECISION_REQUIRED` E6-D1..D6 |
| R04 | nenhum | sem artefato/owner | `BLOQUEADO` |
| R13/R14 | entregáveis externos via P2 + roles (RQ-ANL-13/E05) | pipeline implementado | `DECISION_REQUIRED` (obrigatoriedade) |

## 6. Projeção governada de estado — desenho (authority: docs 88/89 + plano §7.3)

Por `(competência, filial)`, nós independentes — cada um com `state`,
`evidence`, `source`, `observedAt`, `limitations`:

| Nó | Fonte física | Classe de evidência |
|---|---|---|
| `replacement_cost` (MATA320) | `SB1010_TTAT_LOG` (`B1_CUSTD` writes) | `observed_evidence` — nunca "concluído" |
| `average_cost` (MATA330) | TTAT mass-writes SD3/SC2 (quando mensurável) | `observed_evidence` |
| `snapshot` | `SB9010.B9_DATA` + contagem por filial | `SNAPSHOT_AVAILABLE` |
| `cutoff_marker` | `SX6.MV_ULMES` por filial | `CUTOFF_MARKER_OBSERVED` |
| `wizard_lifecycle` | — | `UNAVAILABLE` (E12.5 — tabela não identificada) |
| `human_acceptance` | — | `NOT_INFORMED` (C3-D05 — nunca sistêmico) |
| `reopening` | — | fora de escopo (C3-D03/E12.6) |

`officiality` do conjunto: marcadores técnicos observados — **não**
homologação, **não** confirmação de execução. `limitations` e
`evidenceRefs` obrigatórios; ausência de marcador nunca vira "fechado"
nem "zero".

## 7. Registro de gaps e bloqueios por relatório

| Relatório | Gap/bloqueio | Classe |
|---|---|---|
| R04 | GAP-01 sem artefato/owner; MATR860 não confirmado | `BLOCKED_BY_EVIDENCE` |
| R09 | E9 (SP/RPO/residuais) + E6-D1..D6 + G5 | `DESIGN_READY` + `DECISION_REQUIRED` |
| R12 | E4 (SPs pós-MATA330), E5 (writer), E12.5 (tabela wizard), G5 | `DESIGN_READY` com limitações declaradas |
| R15 | E5 (writer SB9/`MV_ULMES`), E12.6/7 (reabertura/homologação) | `DESIGN_READY` com limitações declaradas |
| R13 | E01/GAP-06 (seed bancos), E05 (roles configuráveis), contrato de entrada externo | `DECISION_REQUIRED` |
| R14 | sem artefato; entregáveis/obrigatoriedade indefinidos | `DECISION_REQUIRED` |
| Transversal | G6 = 0/15; paridades oficiais `PENDING` | acompanhamento |

## 8. Decisões pendentes (D-1..D-6 do master)

| # | Decisão | Authority | Estado |
|---|---|---|---|
| D-1 | E6-D1..D6 R09 (valor homologado, cutoff, rate, persistência, tolerâncias, escopo) | PO/Controladoria | `DECISION_REQUIRED` — suspende implementação R09 |
| D-2 | reconstruído documentado × aguardar SP/RPO (E9) | Arquitetura+PO | `DECISION_REQUIRED` — depende de D-1 |
| D-3 | semântica do contrato R12/R15 | — | **RESOLVIDA** por C3-D02=A + §6 deste doc (gate formal em doc 129) |
| D-4 | owner `STOCK_CLOSED` | — | **RESOLVIDA por restrição**: ler marcadores ERP; nenhum writer/owner paralelo |
| D-5 | R13/R14 modalidade + obrigatoriedade documental | Controladoria | `DECISION_REQUIRED` — pipeline A preservado |
| D-6 | owner + artefato R04 | Controladoria | `DECISION_REQUIRED` — permanece `BLOCKED_BY_EVIDENCE` |

## 9. RQ/AC herdados e novos

Herdados vigentes (doc 23): RQ-ANL-08 (R09 `DESIGN_READY`), RQ-ANL-12
(R04 `BLOCKED`), RQ-ANL-13 (R13/R14 `PROPOSED`), RQ-ANL-14 (R12/R15
`PROPOSED`), RQ-P3-08/08A (`STOCK_CLOSED` owner/terminal), RQ-CMP-CAT/
SEM/TEST (comparação `PASS 35/35`), RQ-C3-04 (marcador rotulado
"técnico", nunca "homologado").

Candidatos a registrar no gate (doc 129): projeção de estado R12+R15
por competência/filial, nós com `evidenceRefs`/`limitations`, erros
tipados, AuthZ fail-closed por filial, ausência→`unavailable` explícito,
`officiality` sem claim de homologação.

## 10. Limitações deste inventário

- Sem acesso a Protheus live neste ambiente — estados de execução
  avaliados por evidência documental `PROVEN` e bindings registrados,
  não por consulta em tempo real.
- Trabalho concorrente identificado (UX-022 staged, engineering
  products, CAIO, vista) — preservado; commit deste ciclo isola somente
  arquivos do escopo via split de patch quando necessário.
- `origin/main` divergiu do HEAD local por rebase/amend de terceiro em
  escopo vista — reconciliação (fetch+rebase ff) antes de push.

## 11. Próximos gates

1. **Doc 129** — gate contratual R12/R15 (contrato TARGET, RQ/AC,
   matriz de segurança, matriz de paridade, modelo Portal×CLARA) —
   elegível imediatamente.
2. **Doc 130** — gate contratual R09 + pacote `DECISION_REQUIRED`
   E6-D1..D6/E9 para o PO — documental elegível.
3. R04/R13/R14 — classificação formal `BLOCKED_BY_EVIDENCE`/
   `DECISION_REQUIRED` (registrada aqui e no ledger).

**Parecer do pacote:** `ACCEPT` — inventário completo, produtores e
consumidores mapeados, contratos candidatos delimitados pelas
autoridades, bloqueios classificados com evidência.
