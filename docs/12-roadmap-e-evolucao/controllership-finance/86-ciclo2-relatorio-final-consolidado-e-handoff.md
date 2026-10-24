# Documento 86 — Ciclo 2 · Relatório Final Consolidado e Handoff

**Rodada:** `CF-C2-FINAL-CONSOLIDATION-AND-HANDOFF-001` (rodada 29 — 2026-10-24)
**Escopo:** consolidação documental R01–R15 · PROC-0072 · Central de Fechamento.
**Natureza:** documental. Nenhuma implementação, runtime, contrato, job ou
alteração Protheus autorizada ou realizada nesta rodada.

> **CICLO 2 — INVESTIGAÇÃO CONSOLIDADA** ≠ `G6 PASS` ≠
> `IMPLEMENTATION_AUTHORIZED` ≠ `RUNTIME_VERIFIED` ≠ `PRODUCT_HOMOLOGATED`.

---

## 1. Resumo executivo

O Ciclo 2 investigou, com evidência física e documental, os 15 itens do
processo de fechamento mensal da Controladoria sobre Protheus (competência
set/2026), o arquivo de evidências do PO e a gravação oficial de 54:44.

**Comprovado:** identificação e correlação operacional das rotinas de fechamento
(`MATA320`→`MATA300`→`MATA330`→`MATA280`→SB9), com atribuição do `INSERT` em SB9 ao MATA280 sustentada por SX1, TTAT e associação temporal (não por auditoria direta da escrita; confirmação de RPO/função interna pendente em E5); paridade integral dos
artefatos R01/R02/R05/R06/R07/R08/R10/R11 ao nível de linha/centavo, modelo
físico do DLP204 (R09, 99,4% com residuais declarados), e a cadeia
produtora do snapshot SB9 com binding temporal ±4s.

**Pendente:** fonte/RPO de produtores custom (`DLP06R01`, `MATR989`,
parâmetros MATR460/MATR910, SPs/jobs DELPI), itens externos/bloqueados
(R04, R13, R14), semântica de reabertura e homologação funcional (G6) de
todos os itens.

## 2. Matriz canônica R01–R15 (espelho do doc 47 — única authority)

| ID | Item | Producer | Fonte | G1–G6 | Residual → owner |
|---|---|---|---|---|---|
| R01 | Baixas a pagar | `FINR190` + `DLP06R01.prt` | `FINR190_DLP.PRX` no acervo; WHERE reproduz 948+motivo | PASS×5 · G6 PENDING | aceite → Controladoria |
| R02 | Baixas a receber | `DLP06R01` custom | **fonte ausente**; paridade do artefato PROVEN (649+8 provisões `'P'`) | G4 PENDING · G5 PASS | fonte → TI/ERP (E1) |
| R03 | P7 / Bloco H | "Registro Inventário P7"/`MATR460` | totalização provada; poder3 = hipótese | G4,G5 PENDING | fonte+parâmetros+emissão resumida → TI/ERP (E2) |
| R04 | Consumo por OP | `MATR860` (candidato) | sem artefato oficial | G1–G4 PENDING · G5 TEST_NOT_RUN | artefato/critério → Controladoria |
| R05 | Entradas e Saídas | `MATR320` | 130 células oficiais reproduzidas as_of | G1–G5 PASS | aceite → Controladoria |
| R06 | CPV / Kardex f01 | `MATR910` | `matr910_dlp.prx` no acervo; 9.357/9.357 linhas | G1–G5 PASS | RPO/parâmetros → E7 |
| R07 | Inventários / Kardex 99 | `MATR910` | 45/45 linhas | G1–G5 PASS | idem E7 |
| R08 | Material em Processo | `MATR989` | 1.501 OP + 573 no-OP/SB9 reconciliados | G1–G5 PASS | fonte/params → E8 |
| R09 | Faturamento × MOD | `DLP204` | `DLP204.prw` no acervo; SP ausente | G4 PASS · G5 `INCONCLUSIVE` | SP/RPO/27 tempos/7 MOD → E9 |
| R10 | Notas por CC | `EDAPP`→SD1 | 353/353, Σ 169.704,12 exato | G1–G5 PASS | taxonomia/filtro → E10 |
| R11 | NF a desconsiderar | `EDAPP`→SD2 | 11/11 identidade; CPV-zero estrutural (TES 594 `F4_ESTOQUE='N'`) | G1–G5 PASS | finalidade → E11 |
| R12 | Fechamento de custos | `MATA320`/`MATA300`/wizard `MATA330` | SX1 1:1 + TTAT `B1_CUSTD`; `Analise.xlsx`↔SB9 98,6% | G1–G4 PASS · G5 `INCONCLUSIVE` | efeitos MATA300, etapa 4 → E12/E5 |
| R13 | Extratos/aplicações | externa | sem artefatos bancários | G2–G4 PENDING · G5 TEST_NOT_RUN | fontes bancárias → Controladoria |
| R14 | Importações/câmbio | mista | sem evidência suficiente | G1–G4 PENDING · G5 TEST_NOT_RUN | inventário → Controladoria |
| R15 | Cutoff / SB9 | `MATA330`→`MATA280`→SB9 | TTAT+SX1+timing 5/5; `I_N_S_D_T_`=UTC | G1–G4 PASS · G5 `INCONCLUSIVE` | RPO MATA280, `MV_ULMES`, reabertura → E5/E12 |

## 3. Métricas — cálculo reproduzível

- `COLETA` (G1–G4): 13+12+12+10 = **47/60 = 78,3%**
- `AUDITORIA` (G1–G6): 47 + G5×8 (R01,R02,R05,R06,R07,R08,R10,R11) + G6×0
  = **55/90 = 61,1%**
- `RELATORIOS_CONCLUIDOS`: **0/15** (G6 exige aceite humano — nenhum
  registrado)

## 4. Matriz vídeo → evidência (timestamps-chave)

| vídeo | etapa | evidência | rotina/artefato | R-ID | status |
|---|---|---|---|---|---|
| 01:55–02:08 | histórico | `OBSERVED_ON_VIDEO` | lista `Fechamentos` (status/filial/datas + `Reabertura`) | R15 | `EXECUTION_OBSERVED` navegação |
| 02:18–02:40 | predefinição | `OBSERVED_ON_VIDEO` | wizard etapa 1 (último 31/08 → 30/09, Diária, filial) | R15 | cutoff `PROVEN` |
| 03:09–04:00 | reposição | `OBSERVED_ON_VIDEO` + SX1+TTAT | `MATA320`/`MTA320`→`B1_CUSTD` | R12 | `PROVEN` |
| 04:36 | refaz saldos | `OBSERVED_ON_VIDEO` + SX1 | `MATA300`/`MTA300` | R12 | binding `PROVEN`; efeito `PENDING` |
| ~05:34 | refaz DIT terceiros | `REPORTED_BY_OPERATOR` | rotina não identificada | R12 | `PENDING` (E12.2) |
| 06:46 | recálculo saldos | `OBSERVED_ON_VIDEO` | log threads `c300P* - Ok` | R12 | `OBSERVED` |
| 14:47 | cálculo custo | `EXECUTION_OBSERVED` + TTAT `MATA330` | wizard etapa 2, 100% | R12/R15 | `PROVEN` |
| 16:40–36:10 | análise/revisão | `EXECUTION_OBSERVED` | etapa 3 → `Analise.xlsx` | R12 | `PROVEN` (1.966/1.994) |
| etapa 4 | fechamento final | **não exibida** | virada posterior por filial (MATA280) | R15 | `PENDING` visual; `PROVEN` em dados |
| 50:00+ | conferências | `OBSERVED_ON_VIDEO` | Excel/Kardex/P7 | R03/R06/R10 | derivação auxiliar |

## 5. Mapa de reuso (doc 80 §0)

| Necessidade Portal | Owner | Contrato existente | Classe |
|---|---|---|---|
| snapshot estoque mensal | api-delpi | `stock_value_official_closure_sql` / `stock_value_historical_sql` (SB9 por `B9_DATA`) | `REUSE_CONFIRMED` |
| custo de reposição | api-delpi | `standard_cost` (`SB1.B1_CUSTD`) | `REUSE_CONFIRMED` |
| CPV mensal vivo | api-delpi/Suprimentos | `GET /supplies/cpv` (`SUM D2_CUSTO1`, CFOP 51/61×4) | `REUSE_PARTIAL` (sem `as_of`; fórmula intocada) |
| despesas por CC | Financeiro/api-delpi | `vw_fin_despesas_centro_custo` | `REUSE_PARTIAL` (448 linhas ≠ 353 oficiais) |
| apontamentos/horas | Produção | `vw_Apontamentos_Eficiencia` | `REUSE_PARTIAL` (horas reais ≠ tempo padrão×faturado) |
| orquestração/status de fechamento | api-delpi | **não existe** | `TARGET` — requer decisão + gate |
| `MV_ULMES`/estado de competência | api-delpi | **não existe** | `TARGET` |
| trilha de auditoria de fechamento | — | nenhuma | `TARGET` |

## 6. Resíduos por owner (doc 82 — consolidado)

**TI/ERP**
- E1: fonte `DLP06R01` (G4 R02) — critério: `SOURCE_AVAILABLE`/`CODE_DEPLOYED`.
- E2: fonte/params `matr460.prx` + emissão resumida P7 (R03).
- E7: versão RPO MATR910 + parâmetros efetivos (R06/R07 — gates já PASS).
- E8: fonte/params `matr989.prx` + semântica corte intra-dia (R08).
- E9: `DLP204` RPO + SP interna + divisor + 27 tempos + 7 MOD (R09).
- E12.2/E12.3: rotina "Refaz DIT" + efeitos físicos MATA300.

**DBA**
- E3: DDL das views (`vw_Apontamentos_Eficiencia`, `vw_fin_despesas_*`).
- E4: jobs SQL Agent (`sysjobs` negado) + SPs `STP_DELPI_*`/
  `STP_PROTHEUS_DELPI_*` ausentes das bases acessíveis.
- E5 (**estreitado r28**): confirmação de RPO/função interna do `MATA280`
  que insere SB9 e avança `MV_ULMES` — a cadeia está provada; falta a linha
  de código (SB9/SX6 não auditáveis por TTAT).

**Controladoria (+TI/ERP em E12)**
- E4 parcial/R04: artefato de consumo por OP e critério oficial.
- E10: taxonomia Direto/Ind/Adm + lista TES + filtro EDAPP (R10).
- E11: finalidade da exclusão 9035/594 e apuração destino (R11).
- E12.1/E12.4–E12.7: sequência oficial, checkpoints, papel `MV_ULMES`,
  tratamento de falhas, **semântica `Reabertura de estoque`**, **critério
  de homologação**.
- R13: arquivos bancários, periodicidade, conferências.
- R14: fontes SWIFT/câmbio/ACSI, documentos e responsáveis.
- G6 de todos: aceite funcional.

**Segurança**
- Residual histórico: identificadores operacionais em commits antigos
  (sanitização de aliases aplicada; reescrita de histórico =
  `DECISION_REQUIRED`, fora do escopo).

## 7. Decisões

**Aprovadas (não reabrir):**
- CPV mensal **vivo** com correções retroativas na competência original
  após recálculo autorizado (doc 80 §40).
- Histórico monetário MOD: **E6 = opção C** (`APPROVED /
  PRODUCT_DIRECTION_ONLY`; `IMPLEMENTATION_AUTHORIZED = NO` — doc 81).
- Identidade congelada: `controllership-finance` / BFF
  `controllership-finance-api`; permissions `.access`/`.manage`; filial =
  dimensão de dados; autorização fail-closed via Core.

**Pendentes (`DECISION_REQUIRED` quando material):**
- Critério formal de homologação do fechamento (virada técnica × aceite
  da Controladoria) — E12.7.
- Semântica e governança de `Reabertura de estoque` — E12.6.
- Contrato futuro de orquestração/status de fechamento (TARGET) — exige
  decisão de produto + gate transversal antes de design detalhado.
- Escopo de R13/R14 (integrações externas bancárias/importação) —
  inventário depende das fontes que a Controladoria indicar.

## 8. Readiness — classificação do próximo ciclo

| Item | Estado | Justificativa |
|---|---|---|
| R05, R06, R07, R08, R10, R11 | `READY_WITH_CONSTRAINTS` | paridade integral + fonte; dependem de aceite G6 e (R06–R08) RPO/parâmetros |
| R01 | `READY_WITH_CONSTRAINTS` | provado; depende G6 |
| R02 | `READY_WITH_CONSTRAINTS` | paridade provada; producer sem fonte (E1) |
| R09 | `READY_WITH_CONSTRAINTS` | modelo provado; SP interna + RPO pendentes (E9) |
| R12/R15 (orquestração fechamento) | `READY_WITH_CONSTRAINTS` | cadeia provada; writer interno/reabertura/homologação pendentes (E4/E5/E12); sem contrato TARGET |
| R03 | `BLOCKED_BY_OWNER` | fonte MATR460/params/emissão resumida (E2) |
| R04 | `BLOCKED_BY_OWNER` | sem artefato/critério oficial |
| R13, R14 | `BLOCKED_BY_OWNER` | fontes externas não fornecidas |

**Nível 1 (base documental): pronto.** Nível 2 (design/contratos): só com
escopo+boundary+decisões acima. Nível 3 (runtime): bloqueado até gate
transversal explícito + homologação.

**Contagem de readiness:** 11/15 itens `READY_WITH_CONSTRAINTS` (R01, R02, R05–R12 e R15) e 4/15 `BLOCKED_BY_OWNER` (R03, R04, R13 e R14). Readiness não equivale a aprovação G6, contrato ou runtime.

## 9. Priorização recomendada (não executada)

1. **Homologação funcional G6** — pacote por item (§10): destrava
   "concluído" sem escrever código.
2. **Read-only Central de Fechamento** (R15/R12): expor estado de
   competência (`MV_ULMES`, lista `Fechamentos`, SB9 por `B9_DATA`,
   diferenças de análise) via BFF própria consumindo api-delpi — alto
   valor, reuso confirmado, risco baixo; requer decisão de contrato.
3. **Painéis de paridade** (R05/R06/R07/R08/R10/R11): render das
   reconciliações já provadas — reusa queries existentes.
4. **Diagnóstico de divergências** (R09/R12): trilha read-only de
   análise/revisão — depende de E9/E12.
5. **Bloqueados** R03/R04/R13/R14: permanecem em acompanhamento com
   owners; não bloqueiam o design dos itens acima.

## 10. Pacote de homologação (G6) — sumário por item

Cada item possui: evidência disponível (doc 80 §§/doc 84), resultado
observado vs esperado (paridades), divergências declaradas e owner.
Formato para aceite da Controladoria:

- R01/R02: paridade 948/649+8 provada; aceitar números oficiais ×
  produzidos; divergências: fonte DLP06R01 ausente (não impede aceite
  funcional do artefato).
- R05: 130 células reproduzidas; aceitar conferência MATR320 oficial.
- R06/R07: kardex linha-a-linha; aceitar emissões MATR910.
- R08: reconciliação OP+SB9; aceitar P7 EM PROCESSO.
- R09: modelo provado; declarar 27 tempos residuais.
- R10: seleção 353/353; confirmar taxonomia Direto/Ind/Adm (E10).
- R11: conjunto 11/11; confirmar finalidade da exclusão (E11).
- R12/R15: apresentar cadeia MATA320/300/330/280, `Analise.xlsx`↔SB9,
  viradas por filial; definir formalmente o que caracteriza "fechamento
  homologado".

## 11. Critérios de transição

**Para iniciar design (Nível 2):** escopo e owner declarados por página;
decisões de produto das §7 pendentes tomadas ou explicitamente adiadas;
contrato pretendido referenciando reuso §5; sem escrita Protheus.

**Para iniciar runtime (Nível 3):** gate transversal explícito; aceite G6
dos itens em escopo; E4/E5/E12 resolvidos ou formalmente aceitos como
limite; implementação page-by-page autorizada.

## 12. Estado final

- Gates coerentes com doc 47 (matriz §2 acima é espelho — authority lá).
- Métricas: `COLETA 47/60 = 78,3%` · `AUDITORIA 55/90 = 61,1%` · `0/15`.
- 100 regras `BR-*` e 75 testes `T-*` no doc 85; erratas preservadas.
- E1–E12 com owner, evidência faltante e critério de aceite (doc 82).
- Vídeo rastreável (docs 56/57/78 + matriz §4).
- **`CYCLE2_DOCUMENTATION_READY`** — pendente de revisão e aceite do PO.

### PENDÊNCIAS DE EVIDÊNCIA, HOMOLOGAÇÃO E AUTORIZAÇÃO

Resumo: producer-fontes custom (E1/E2/E7/E8/E9), jobs/SPs (E4), linha de
código MATA280 (E5), sequência/reabertura/homologação (E12), taxonomias e
finalidades (E10/E11), inventário externo (R04/R13/R14), G6×15 e decisões
de produto/contrato do próximo ciclo. Nada disso autoriza implementação.

*Documentos-fonte: 47 (matriz/gates), 56/57/78 (vídeo), 80 §0–§47
(registro vivo), 81 (E6=C), 82 (owners E1–E12), 83 (crosswalk), 84
(paridades), 85 (catálogo BR/T). Este documento referencia — não duplica —
as evidências.*
