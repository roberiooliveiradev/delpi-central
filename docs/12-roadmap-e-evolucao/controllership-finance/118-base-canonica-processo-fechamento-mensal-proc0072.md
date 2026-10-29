# Documento 118 — Base canônica do processo de Fechamento Mensal (PROC-0072)

**Execução:** `CF-PROC0072-ANALYSIS-CONSOLIDATION-002` · **Data:** 2026-10-29
**Produto:** Portal Controladoria & Finanças — Minha DELPI · **Funcionalidade:** Central de Fechamento
**Processo:** `PROC-0072 — Gestão do Fechamento Mensal da Controladoria` (process_id `21f70cd0-d513-46f5-bfcf-29ae5573f2f6`, [doc 19](./19-rastreabilidade-teo.md))
**Natureza:** consolidação documental canônica. `DOCUMENTATION_ONLY` — **nenhuma alteração de runtime, contrato, migration ou deploy foi feita nesta execução.**
**Baseline:** HEAD `0e39cbc9a8` (revalidar em cada nova execução).

> **Como usar este documento.** Este é o ponto de entrada único do conhecimento do fechamento mensal. Ele não substitui a proveniência: cada regra cita a fonte que a sustenta (TÉO/Transformômetro para AS-IS e decisões TO-BE; gravação e artefatos para evidência observacional; GitHub para TARGET, contratos e código; decisões do PO para escolhas de produto). Ao implementar, ler primeiro a seção relevante aqui e seguir os links para a fonte primária. Ao encontrar evidência nova ou contraditória, aplicar as condições de reabertura do §17 — não reabrir o inventário por preferência.

## Estado das classificações usadas

`PROVEN` (evidência direta suficiente) · `INFORMED`/`OBSERVED` (relatado/observado sem prova integral) · `TARGET` (decisão aprovada, não implementada) · `PROPOSED` (candidato, não decidido) · `TO_INVENTORY` (fonte identificável, ainda não inspecionada) · `PENDING_CONTRACT` · `UNKNOWN` · `DECISION_REQUIRED` · `STALE_EVIDENCE` · `GAP-RULE` · `TEST_NOT_RUN` · `PASS`/`FAIL`/`INCONCLUSIVE` · `EXECUTION_DRIFT` · `REUSE_PARTIAL`/`REUSE_CONFIRMED` · `SOURCE_AVAILABLE`/`SOURCE_MISSING` · `CODE_PRESENT` (existe no HEAD, não comprova resultado) · `RUNTIME_VERIFIED`.

Regras deste documento: nenhuma observação operacional é promovida a regra formal sem fonte e autoridade; nenhuma hipótese vira causa; nenhuma aproximação vira fonte oficial; nenhum TARGET é apresentado como AS-IS; fonte indisponível nunca é representada como zero; decisões do PO não são sobrescritas silenciosamente; contradições materiais são preservadas, não reconciliadas por suposição; conclusão documental ≠ prontidão técnica de integração.

---

## 1. Como o fechamento realmente funciona (síntese executiva)

O fechamento mensal da Controladoria é uma **orquestração paralela** de processamentos no Protheus, relatórios oficiais, transformações em Excel e uma conciliação monetária determinística — não uma lista linear. A competência analisada em profundidade é **09/2026**, empresa DELPI, filiais 01 (Matriz) e 02, executora observada **JOICI** (gestora Joici Motta), em ambientes Protheus `02.9.0004` (Estoque/Custos) e `02.9.0006` (Financeiro) — [doc 83 §0](./83-ciclo2-crosswalk-evidencias-r01-r15.md).

Três núcleos:

1. **Cadeia de custos no Protheus** (executada no ERP, em produção, observada no vídeo): Recálculo do Custo de Reposição (`MATA320`) → Refaz Saldos (`MATA300`) → wizard "Acompanha Custo / Novo fechamento de custo" (4 etapas, motor `MATA330` custom) → Virada de Saldos (`MATA280`) que grava `SB9`, saldos iniciais de OP (`SC2.C2_VINI*`/`C2_APRINI*`) e avança `MV_ULMES`. Prova física por `SX1`+`TTAT`+timing (5/5 rajadas SB9 dentro das janelas MATA280) — [doc 83 R12/R15](./83-ciclo2-crosswalk-evidencias-r01-r15.md), [doc 80 §46/§47](./80-ciclo2-registro-vivo-investigacao-devin.md).
2. **Emissão iterativa de relatórios e planilhas** (R01–R15, catálogo §6): o mesmo relatório é reemitido ao longo do dia conforme correções entram no ERP — o P7 foi reemitido ao menos 4 vezes em 30/09 com totais distintos (`3.776.994,69` → `~2.756.1xx` → `3.946.431,87`/`2.976.967,56`), o que fundamenta a exigência de **versão/`as_of`** em qualquer contrato — [doc 83 §3](./83-ciclo2-crosswalk-evidencias-r01-r15.md).
3. **Conciliação tripla** — o coração do fechamento: `DIVERGENCIA = ENTRADAS_SAIDAS − P7 − H02`, com **paridade monetária exata R$ 0,00** (TÉO doc 06.2, homologada em [doc 15.1](./15.1-p3-criterios-paridade-monetaria.md)). Na demonstração, divergiu `R$ 48.660,78` (verbalizado `48.660,77`), localizada no grupo MP/em processo; a **causa não foi comprovada** — ver Q10 e GAP-02.

O fechamento termina com a montagem e entrega de pacotes documentais à Contabilidade/DRE e outras audiências (checklist `Arquivos de envio - contabil.xlsx`), incluindo entregáveis externos (extratos bancários, aplicações) que não nascem no Protheus — [doc 83 §1](./83-ciclo2-crosswalk-evidencias-r01-r15.md).

---

## 2. Modelo operacional canônico (etapas e dependências)

O processo tem execução paralela com **dependências duras**: a virada de saldos exige o custo recalculado; relatórios de estoque só têm valor de fechamento após o estado de custo da emissão; a conciliação só pode ser homologada após o corte. Legenda de tipo de operação: `ERP_EXEC` (executa no Protheus) · `ERP_QUERY` (consulta) · `REPORT` (emite relatório) · `EXCEL` (transforma planilha) · `RECONCILE` · `INVESTIGATE` · `APPROVE` · `DELIVER` · `CLARIFY`.

| ID | Etapa | Tipo | Gatilho / pré-condição | Fonte / processamento | Evidência | Validação | Dependências | Automação |
|---|---|---|---|---|---|---|---|---|
| OPS-01 | Recálculo do Custo de Reposição | `ERP_EXEC` | início do fechamento | `MATA320`; params visíveis: `Ult Custo Compra` (MC→MP) e `Estrutura` (PA→PI); `Dt Final Ref Taxa=30/09/2026` | vídeo 04:00; TTAT `SB1010.B1_CUSTD` 13.201+1.532 writes 30/09 14:36–15:14 +15.972 em 01/10 (JOICI) — doc 83 R12 | CM recalculado alimenta kardex/P7 | — | nenhuma na V1 (ERP) |
| OPS-02 | Refaz Saldos | `ERP_EXEC` | após movimentações | `MATA300` (SX1 `MTA300` 1:1; threads `c300P*`) | doc 83 R12 | efeito físico `PENDING` (SB9/B2 não auditados por TTAT) | OPS-01 | nenhuma na V1 |
| OPS-03 | Fechamento de custo (wizard) | `ERP_EXEC` | custos de reposição prontos | "Acompanha Custo → Novo fechamento de custo", 4 etapas: Predefinição → Cálculo → Análise e revisão → Fechamento; motor `MATA330` custom; lista `Fechamentos` = objeto de ciclo de vida | vídeo 14:47–16:xx; doc 83 §3/R12 | `Analise.xlsx` = export da etapa 3: CM final ≡ `B9_CM1`@30/09 em 1.966/1.994 (98,6%; 22 `MOD*` estruturais sem SB9 + 6 deltas de drift) | OPS-01/02 | Portal pode exibir estado; execução permanece ERP |
| OPS-04 | Virada de saldos / cutoff técnico | `ERP_EXEC` | wizard concluído | `MATA280` → rajada `SB9` + `SC2` (`C2_VINI1`/`C2_VINIRP1`/`C2_APRINI*`) + `MV_ULMES` por filial | doc 83 R15: 5/5 rajadas dentro das janelas; `I_N_S_D_T_` grava UTC | `MV_ULMES=20260930` f01+f02; writer interno pendente (E5) | OPS-03 | estado `STOCK_CLOSED` consultável (T03); escrita proibida na V1 |
| OPS-05 | Relação de baixas a pagar | `REPORT` | competência de caixa | `FINR190` "Relação de Baixas DLP" (fonte `FINR190_DLP.PRX`, layouts `DLP06R01.prt`/`nat.prt`) | `pagos 09 26.xlsb` 948 linhas; `Pagos por dt.pdf`/`Pagos por nat.pdf` | paridade row-level integral (doc 84 §1): 948/948 chaves; TB=`E5_VALOR`; VO=`E2_VALOR` 942 + 5 INV aglutinadas + 1 NF grupo | independente | contrato api-delpi implementado (read-only) |
| OPS-06 | Relação de baixas a receber | `REPORT` | idem | `DLP06R01` custom — **fonte ausente do acervo** (E1) | `Recebidos.xlsb` 657 linhas; `Recebidos.pdf` | paridade row-level do artefato (doc 84 §2): 649 SE5×SE1 + 8 `PA`/`FINA750` sem título; VO=`E1_VALOR` + provisão `'P'` espelhada | independente | contrato api-delpi implementado; binding do produtor pendente (E1) |
| OPS-07 | Entradas e Saídas (valor do estoque) | `REPORT` | após estado de custo | `MATR320.prt` padrão TOTVS via SP `MAT056` (não a variante `DLPR320`) | `Entradas e saidas.pdf` 01/09–30/09 f01 | **130/130 células Δ=0,000** no `as_of` da emissão; divergência MP +8.631,731 decomposta ao centavo (revalorização CM pós-emissão) — doc 84 §4 | OPS-01–04 | contrato candidato RQ-ANL-02 |
| OPS-08 | Registro de Inventário P7 | `REPORT` | após virada/emissões iterativas | "Registro de Inventário Modelo P7"; roster oficial vincula `MATR460`; cadeia `MATR460→MP7_*→MP7GDA→A460UNIT` — fonte `A460UNIT.prw` **confirmada no acervo** (ajuste de custo por produto, não filtro de escopo); `matr460.prx`/RPO ausente; alimenta SPED Bloco H (`MTR460` parâmetro `23 Arq. Sped`) | `Estoque.pdf` (folha 101, completo) + `Resumo Estoque.pdf` (folha 74, escopo MP/PA/PI) | binding de totalização `PROVEN`: EM ESTOQUE = saldo físico **excluindo armazém de processo `MV_LOCPROC='99'`** no `as_of` da emissão; EM PROCESSO = `MATR989` — doc 84 §3; **dois escopos (DEC-12)**: `all_products` = análise interna + operando da conciliação; `mp_pi_pa` = entrega DRE | OPS-01–04 | contrato candidato RQ-ANL-01; SB9 nunca servido como "P7 oficial" sem rótulo |
| OPS-09 | Material em Processo (H02) | `REPORT` | idem | `MATR989` analítico (`SOURCE_MISSING` — roster+aba) | `Material em processo.xlsb` 57.359 linhas, Dt.Ref 01/10 16:15 | dois blocos provados (doc 84 §5.2): SD3 `RE*` de OPs abertas (1.501/1.501) + `SB9010` loc99 não-OP (569/573 exatos +4 Δ temporais); total 355.240,51 = EM PROCESSO do P7 **exato** | OPS-01–04 | contrato candidato RQ-ANL-02 |
| OPS-10 | Kardex físico-financeiro (CPV + INVENT) | `REPORT` | idem | `MATR910` (`matr910_dlp.prx` disponível) | `cpv 09 26 matriz.xlsb` (14.382 linhas) + `Invent.xlsb` (50 linhas) | UNION `SD1(D1_DTDIGIT)+SD2(D2_EMISSAO)+SD3(D3_EMISSAO)`, `F4_ESTOQUE='S'`, `D3_ESTORNO<>'S'`, `ORIGLAN<>'LF'`; cadeia de saldo `B9`@0831; INVENT=`D3_DOC='INVENT'` TES 999/499 — doc 83 R06/R07 | OPS-01–04 | contratos candidatos RQ-ANL-05 |
| OPS-11 | Notas por Centro de Custo | `REPORT`+`EXCEL` | após digitação do mês | `EDAPP` export `SD1` (`SCAGQGA0.XML`) | `CC matriz.xlsb` 353 linhas; vídeo 47:00 (`SCAGPOU0.XML`) | seleção reconstruída integral (doc 84 §5.4): `D1_DTDIGIT`∈mês − 13 TES − `D1_TP='MP'` − 6 benefícios; Σ`D1_TOTAL`=169.704,12 exato | digitação completa | contrato candidato RQ-ANL-06; classificação Direto/Ind/Adm é manual (E10) |
| OPS-12 | NF a desconsiderar do faturamento | `REPORT`+`EXCEL` | idem | `EDAPP` export `SD2` (`Planilha2`) | `NF a desconsiderar.xlsb` 11 linhas | identidade de conjunto: `D2_GRUPO='9035'`∩`D2_TES='594'`∩`D2_EMISSAO`∈set∩f01; Σ`D2_TOTAL`=97.462,71; `D2_CUSTO1=0` estrutural (`F4_ESTOQUE='N'`) — doc 84 §5.5 | faturamento | contrato candidato; finalidade → E11 |
| OPS-13 | Faturamento × MOD | `REPORT` | após faturamento | `DLP204` ("Fat x Mod — Custo MO"; `DLP204.prw` disponível; SP `STP_DELPI_FORMA_PRECO_*` ausente → E9) | `Fat x MOD.xlsb` abas `1-Fl01` (2.459) + `2-Fl02` (2.017) | modelo provado linha-a-linha (doc 84 §5.3): `Qtd Fat`=Σ`D2_QUANT` do PA-âncora (TES `F4_DUPLIC='S'`); `Quantidade`=`SHY010.HY_TEMPAD` (fallback `SG2`); rate=`SBZ010.BZ_CUSTD` `as_of`; `Horas=QtdFat×Quantidade`; `CustoTotal=Horas×rate`; totais f01 164.985,66 / f02 579.268,58; G5 `INCONCLUSIVE` (27 tempos+7 MODs sem SBZ) | faturamento encerrado (processo externo — não é OPS do fechamento) | contrato candidato RQ-ANL-08 |
| OPS-14 | **Conciliação tripla** | `RECONCILE` | após OPS-07/08/09 da mesma referência | `DIVERGENCIA = ENTRADAS_SAIDAS − P7 − H02` | TÉO 06.2; demonstração divergiu R$ 48.660,78 (vídeo; doc 117 ANL) | **paridade exata R$0,00**; centavo ≠ zero bloqueia; fonte indisponível ≠ zero | OPS-07/08/09 com mesmo `as_of` | motor determinístico RQ-ANL-03 (TARGET) |
| OPS-15 | Investigação de divergências | `INVESTIGATE` | divergência ≠ 0 | drill-down por grupo de material, tipo, armazém, OP; correção no ERP e reemissão | doc 117 (localização MP); doc 84 §4.3 (decomposição por produto possível) | divergência localizada ≠ causa provada | OPS-14 | Portal exibe ponto de divergência; correção permanece ERP (doc 113 §2.5) |
| OPS-16 | Montagem e entrega dos pacotes | `DELIVER` | relatórios homologados + entregáveis externos | checklist `Arquivos de envio - contabil.xlsx` (eletrônico+físico: Extratos, XP, BB, aplicações, notas, inventário) | doc 83 §1; TÉO 07 (handoffs) | recebedores = Contabilidade/DRE e áreas configuradas | OPS-05–15 + fontes externas | TARGET P5: submissão interna no Portal (doc 37) |
| OPS-17 | Esclarecimentos e conclusão | `CLARIFY`/`APPROVE` | pedidos do destinatário | revisões, complementos, novas versões | TÉO 31.16; docs 37/113/115 | aceite humano por pacote/área; conclusão exige pacotes submetidos + zero clarifications abertas (doc 37 C2) | OPS-16 | P5/P6 implementados parcialmente (ver §8) |

**Condições que impedem o encerramento (consolidadas):** (a) divergência monetária ≠ R$0,00 na tripla; (b) source obrigatório indisponível/inválido (`UNAVAILABLE`, nunca zero); (c) fontes fora da mesma referência temporal/`as_of`; (d) documento exigido rejeitado/pendente de validação; (e) estado externo `STOCK_CLOSED` não confirmado quando o gate aplicável existir; (f) pacote aplicável não submetido, clarification aberta ou rejeição terminal — [docs 10](./10-p3-estoque-cutoff-e-conciliacao.md), [15.1](./15.1-p3-criterios-paridade-monetaria.md), [37](./37-p5-submissao-e-revisao-no-portal.md), [90 §5](./90-ciclo3-crosswalk-end-to-end-proc0072-teo-rq-ac-portal.md).

---

## 3. Matriz mestra de evidências

Origens: TÉO/Transformômetro (43 documentos PROC-0072, última revisão 2026-10-05 — dump integral confirmado nesta execução); gravação 54:44 (transcrição integral de 583 segmentos produzida no ANALYSIS-001); pasta `fechamento` do PO (20 arquivos — inventário doc 83 §1); acervo `docs/13-fontes-totvs-protheus`; corpus GitHub docs 44–115; código HEAD.

| ID | Afirmação | Fonte primária | Estado | Contrato/decisão |
|---|---|---|---|---|
| EV-01 | Cadeia de custos `MATA320→MATA300→MATA330→MATA280` é a execução real do fechamento | TTAT+SX1+timing (doc 83 R12/R15, doc 80 §46/47) | `PROVEN` | estado `STOCK_CLOSED` via owner/ERP (T03) |
| EV-02 | Regra `E/S − P7 − H02 = R$0,00` exata | TÉO 06.2; [doc 15.1](./15.1-p3-criterios-paridade-monetaria.md) | `PROVEN`+homologada | AC-P3-PARITY-01..07 |
| EV-03 | Divergência demo `R$48.660,78` em MP, causa desconhecida | vídeo/transcrição (doc 117 §10) | `PROVEN` (fato) / `NOT_PROVEN` (causa) | GAP-02 |
| EV-04 | R01 payable: paridade row-level 948/948 | doc 84 §1 | `PROVEN` | api-delpi settlements (implementado) |
| EV-05 | R02 receivable: paridade row-level 657 (649+8) | doc 84 §2 | `PROVEN` (artefato) / `SOURCE_MISSING` (produtor) | E1 |
| EV-06 | MATR320: 130/130 células Δ=0 no `as_of`; drift MP decomposto | doc 84 §4 | `PROVEN` | RQ-ANL-02 |
| EV-07 | P7: EM ESTOQUE=SB9 ex-`MV_LOCPROC` `as_of`; EM PROCESSO=MATR989 | doc 84 §3, doc 80 §33.D | `PROVEN` (binding totalização) / `TO_INVENTORY` (produtor+params) | E2, RQ-ANL-01 |
| EV-08 | MATR989 = SD3 OP aberta + SB9 loc99; total=EM PROCESSO P7 | doc 84 §5.2, doc 80 §41 | `PROVEN` | E8 |
| EV-09 | MATR910 kardex: UNION SD1/SD2/SD3 com regras de filtro | doc 83 R06/R07, doc 80 §37 | `PROVEN` | E7 |
| EV-10 | R10 CC: seleção `D1_DTDIGIT` + 13 TES + MP + benefícios; Σ169.704,12 | doc 84 §5.4 | `PROVEN` | E10, RQ-ANL-06 |
| EV-11 | Direto/Ind/Adm = classificação manual pós-exportação | doc 84 §5.4 | `PROVEN` | E10 (taxonomia → GAP) |
| EV-12 | R11: seleção `9035∩594∩emissão∩f01`; Σ97.462,71; CPV-zero estrutural | doc 84 §5.5 | `PROVEN` | E11 |
| EV-13 | R09 Fat×MOD: cadeia DLP204 reproduzida 4.476 linhas | doc 84 §5.3 | `PROVEN` (modelo) / `INCONCLUSIVE` (G5) | E9, RQ-ANL-08 |
| EV-14 | `Analise.xlsx` = export da etapa 3 do wizard; CM final≡`B9_CM1`@30/09 | doc 83 §6, doc 80 §46.D | `PROVEN` | — |
| EV-15 | `Invent.xlsb` = MATR910 filtrado `D3_DOC='INVENT'` TES 999/499 | doc 83 R07 | `PROVEN` | — |
| EV-16 | Entregáveis externos: extratos/XP/BB/aplicações (checklist físico+eletrônico) | `Arquivos de envio - contabil.xlsx`, doc 83 §1 | `PROVEN` (existência) / `UNKNOWN` (dados) | P2 upload TARGET |
| EV-17 | Envio histórico = arquivos por checklist; TARGET = submissão interna no Portal | doc 36 (supersedido) → [doc 37](./37-p5-submissao-e-revisao-no-portal.md) | `TARGET` aprovado | RQ-P5, doc 37 C2 |
| EV-18 | Fechamento é iterativo: P7 reemitido ≥4× com totais distintos | metadados PDFs + vídeo (doc 83 §3) | `PROVEN` | exige `as_of`/versão |
| EV-19 | SB9 drift: 4.812 linhas → 0 linhas em re-checks 30/09 f01 | doc 49 §7, doc 80 §34 | `EXECUTION_DRIFT` documentado | fail-closed; nunca exibir zero como fechamento |
| EV-20 | `FINR190_DLP.PRX` reproduz WHERE oficial do pagar; `DLP06R01` (receber) ausente | doc 84 §1/§2 | `SOURCE_AVAILABLE`/`SOURCE_MISSING` | E1 |
| EV-21 | `A pagar.xlsb`/`A Receber.xlsb` = posições em aberto (FINR130/150), não baixas | doc 83 §1/§6 | `PROVEN` | não misturar com R01/R02 |
| EV-22 | Roster oficial de rotinas liberadas (Fiscal/Contábil) | `Contabilidade liberações.xlsx`, doc 83 §2 | `PROVEN` | G3 de múltiplos itens |
| EV-23 | `MATR860` é candidato a consumo por OP; nenhum artefato na pasta | doc 83 R04 | `TO_INVENTORY`/`BLOQUEADO` | GAP-01 |
| EV-24 | `MV_ULMES=20260930` f01+f02; writer pendente (SX6 sem auditoria) | doc 83 R15 | `PROVEN` (estado) / `PENDING` (writer) | E5 |
| EV-25 | CPV canônico já existe: `GET /supplies/cpv` api-delpi (Σ`D2_CUSTO1`, CFOPs 5101/5124/6101/6124, `D2_EMISSAO`) | doc 80 §39, commit `4bd217a3ae` | `CODE_PRESENT`+`REUSE_PARTIAL` | sem `as_of`/snapshot |
| EV-26 | `vw_fin_despesas_centro_custo`/`despesas-centro-custo` ≠ seleção R10 (eixo emissão, CC-obrigatório, sem exclusões; 269/353) | doc 84 §5.4 | `REUSE_PARTIAL` | RQ-ANL-06 requer seleção própria |
| EV-27 | Decisões TO-BE Q01–Q30 aceitas em bloco; Q22 resolvida por decisão posterior (doc 37) | TÉO 33 + doc 37 | `TARGET` | §11 registro |
| EV-28 | P5: submissão interna Portal; e-mail = notificação, não transporte; versões imutáveis | doc 37; TÉO 31.16 | `TARGET` | doc 37 C2/P5-A..J |
| EV-29 | DRE: permission `controllership-finance.access.dre`; entrega = assignment `RECIPIENT` + versão `SUBMITTED` | docs 91, 115; manifesto HEAD | `PROVEN` (runtime) | legada `closing-documents.read` descontinuada |
| EV-30 | Runtime atual: competências, documentos, validações, pendências, pacotes P5, P3, admin, DRE, CLARA MCP existem no HEAD | código + docs 100/113/114/115; §8 | `CODE_PRESENT` | não equivale a homologação |

---

## 4. Resolução das dez questões do documento 117 §17

Método: investigação cruzada em TÉO (docs 05/06/06.1/06.2/07/09/20/30–34), corpus GitHub (docs 44–115, especialmente 80/83/84/85/86/90/113/115), código HEAD e artefatos — **sem novas entrevistas e sem reenvio de perguntas** (determinação do PO).

| Q | Fontes consultadas | Resposta consolidada | Conclusão | Classificação | Residual |
|---|---|---|---|---|---|
| **Q01 — bancos e contas** | checklist `Arquivos de envio`, TÉO 05/07/20, vídeo, TÉO 33 (E01), doc 90 §4 | A lista é **configurável por unidade** (decisão E01/doc 33 — nunca hardcode). O drift checklist × procedimento é real (CEF/Viacredi citados no procedimento; só Bradesco demonstrado em operação na gravação). | Contas obrigatórias da competência = cadastro administrado (P6), não lista fixa de código. `sem movimento exige comprovante` (TÉO 06). | `RESOLVED_BY_EXISTING_DECISION` | seed inicial de bancos/contas = **E01 pendente** (owner Controladoria) → GAP-06 |
| **Q02 — tipos/CFOPs de expurgo** | doc 84 §5.4, doc 80 §44, doc 85 §10, doc 56 Registro 17, artefato `CC matriz.xlsb` | O campo efetivo é **`D1_TES` (Tipo de Entrada/Saída), não CFOP** — a coluna "Tipo Entrada" do export EDAPP é `D1_TES`. Seleção reconstruída integral: `D1_DTDIGIT`∈mês → excluir **13 TES** `{001,003,016,020,030,040,080,083,085,120,159,204,318}` → excluir `D1_TP='MP'` → excluir 6 linhas de benefícios saúde/odonto sem CC. | Lista de expurgo homologável por identidade de conjunto (353/353). Divergência narrada-12 vs observada-13 (`016`,`159`, ambos `F4_DUPLIC='N'`) e ambiguidade `02`/`04` → E10. | `RESOLVED_BY_EVIDENCE` | confirmação formal da lista (12 vs 13) → **E10** |
| **Q03 — taxonomia de CC** | doc 84 §5.4, TÉO 20, artefato, doc 117 §13 | Direto/Indireto/Adm **não é campo físico**: é classificação manual pós-exportação por CC (prova: 2 linhas `direto` minúsculas = edição humana). 0407 é CC observado relevante (R$ 18.789,08, top-3); coparticipação = parcela colaborador excluída (6 linhas, R$ 6.990,44). | A taxonomia existe na prática, mas **não tem owner/fonte física comprovada** — não promover a regra canônica. Conflito de nomenclaturas `02xx/03xx/04xx` vs `02/03/05` preservado. | `PARTIALLY_RESOLVED` | owner da taxonomia + cadastro de CC × classe + regra benefícios colaborador×empresa → **E10** → GAP-09 |
| **Q04 — agregação Fat × MOD** | doc 84 §5.3, doc 80 §43, `DLP204.prw`, artefato | Modelo linha-a-linha provado: âncora = PA com TES `F4_DUPLIC='S'`; `Qtd Fat`=Σ`D2_QUANT` do âncora propagada aos descendentes; `Cod Produto`=`MOD`+`SH1010.H1_CCUSTO` do recurso; `Quantidade`=`SHY010.HY_TEMPAD` (roteiro congelado da OP; fallback `SG2010.G2_TEMPAD`); `Custo Unit`=`SBZ010.BZ_CUSTD` `as_of` emissão via TTAT; `Horas`/`CustoTotal`=identidades aritméticas. Intervalo = competência por `D2_EMISSAO`. | Suficiente para especificar a agregação (4.476/4.476 colunas-chave; 99,4% tempos). | `RESOLVED_BY_EVIDENCE` | SP `STP_DELPI_FORMA_PRECO_*` ausente, divisor `÷2` desdobramento, 27 tempos, 7 MODs sem SBZ → **E9**; G5 `INCONCLUSIVE` |
| **Q05 — arquivos complementares** | docs 83/84/85, artefatos | `NF a desconsiderar.xlsb` = export EDAPP SD2: conferência das NFs de **industrialização para terceiros** (`9035∩594`, CPV-zero estrutural — itens-irmãos TES 510 carregam o custo). `Analise.xlsx` = export da **etapa 3 do wizard Acompanha Custos** (revisão CM inicial×final por produto/armazém). `Invent.xlsb` = kardex `MATR910` filtrado a `D3_DOC='INVENT'` (TES 999/499), f02, work file de inventário. | Finalidade documentada para os três — não inventada. | `RESOLVED_BY_EVIDENCE` | qual apuração consome o desconsiderar (CPV×ROL×DRE) → **E11** |
| **Q06 — consumo por OP** | pasta de evidências, doc 83 R04, roster, fontes | **Nenhum artefato de consumo por OP existe na pasta**; `Material em processo.xlsb` traz OP mas é R08; `MATR860` permanece candidato (fonte presente, papel não observado em uso). | Evidência insuficiente para especificar fonte/campos/destinatário. | `EVIDENCE_NOT_FOUND` | **GAP-01** — confirmar artefato/rotina com Controladoria (não perguntado nesta execução por determinação do PO) |
| **Q07 — pós-corte/sacramentação** | doc 83 R12/R15, doc 80 §46/47, TÉO 31.14, docs 10/113, TÉO 34 (E02/E03) | Observado: a operadora executa o wizard e a virada (JOICI, vídeo+TTAT); correções posteriores provocam **reemissão iterativa** dos relatórios (P7 ≥4×); `Fechamentos` lista ciclos Concluído/cancelados e existe `Reabertura de estoque` na lista. `MV_ULMES` avança por filial. | Cadeia e operação reconstruídas; semântica de reabertura, executor elegível e processo de correção pós-sacramentação **ainda não homologados**. | `PARTIALLY_RESOLVED` | E02 (correção pós-corte), E03 (executor/perfis/segregação), E12.6/E12.7 (reabertura) → GAP-07/08 |
| **Q08 — envio dos pacotes** | checklist `Arquivos de envio`, doc 36 (supersedido), [doc 37](./37-p5-submissao-e-revisao-no-portal.md), doc 113 §2, doc 115 | AS-IS: checklist físico+eletrônico de arquivos enviados à Contabilidade (extratos, XP, BB, notas, inventário). TARGET (decisão posterior, autoridade vigente): **submissão interna na Minha DELPI** — "Enviar para análise" = disponibilizar a PackageVersion a revisores autenticados; e-mail é notificação com link, **não transporte**; correções = complementos/novas versões imutáveis. | Canal histórico ≠ canal TARGET — distinção resolvida pela decisão doc 37. | `RESOLVED_BY_EXISTING_DECISION` | detalhe do canal físico/eletrônico AS-IS (formato exato de envio) permanece incompleto mas é imaterial ao TARGET → GAP-14 |
| **Q09 — Bloco H / última página** | doc 84 §3, doc 80 §33–36, roster (SPEDFISCAL "Bloco H e K"), PDFs, vídeo 35:00/37:00 | P7 = "Registro de Inventário Modelo P7" (MATR460 pelo roster) e alimenta SPED Bloco H. Dois escopos confirmados: **completo** (`Estoque.pdf`, TOTAL 3.946.431,87) e **restrito MP/PA/PI** (`Resumo Estoque.pdf`, TOTAL 2.976.967,56 — mesma data-base/custo do completo; divergência só em MP, hipótese `QTNP@emissão>0` explica 99,987% — **não regra oficial**). | Escopo MP/PA/PI confirmado; **DEC-12 encerrou a escolha funcional**: `all_products` (interno/conciliação — a emissão da conciliação tinha as 10 classificações) e `mp_pi_pa` (entrega Contabilidade/DRE); nomes canônicos do contrato exploratório. Mecanismo técnico do recorte segue E2 (SX1 `MTR460` sem parâmetro de tipo). | `RESOLVED_BY_EVIDENCE` (binding + decisão PO) / `PARTIALLY_RESOLVED` (parametrização/mecanismo) | pacote E2.1/E2.2/E2.3 (params, folha 74 integral, produtor/RPO) → GAP-04 |
| **Q10 — divergência R$ 48 mil** | vídeo/transcrição, doc 117 §10/§13, doc 84 §3, prints RC-02 | Fórmula provada; divergência computada `48.660,78` vs verbalizada `48.660,77` (Δ de R$0,01 não explicado); localizada em MP/em processo; prints da sessão exibem WIP alternativos (`64.591,71`/`64.968,42` vs total MATR989 `355.240,51` — recortes/filiais distintos, **não reconciliados**); investigação por grupo documentada. | **Causa e desfecho não comprovados** — nenhuma fonte evidencia resolução posterior. | `PARTIALLY_RESOLVED` | **GAP-02** — desfecho real é indeterminado nas evidências |

Síntese: **4 RESOLVED_BY_EVIDENCE · 3 RESOLVED_BY_EXISTING_DECISION · 2 PARTIALLY_RESOLVED · 1 EVIDENCE_NOT_FOUND**. Nenhuma questão foi encaminhada a Joyce/PO nesta execução.

---

## 5. Matriz de contradições reconciliadas

| ID | Afirmação A (fonte) | Afirmação B (fonte) | Autoridade/decisão | Resolução | Consequência p/ contrato |
|---|---|---|---|---|---|
| CTR-01 | Lista de bancos do checklist (físico/eletrônico) | Lista do procedimento escrito (CEF/Viacredi) | TÉO 33 E01 | `DECISION_REQUIRED`→decidido em produto: lista configurável por unidade; seed pendente | cadastro P6 versionado; sem hardcode |
| CTR-02 | "12 tipos excluídos" narrado (doc 56 R17) | 13 TES observadas na reconstrução | evidência física 353/353 | reconstruído inclui `016`/`159`; narrativa prevalece como INFORMED | lista canônica = 13 TES observadas, sujeita a confirmação E10 |
| CTR-03 | tolerância operacional de arredondamento (prática) | paridade exata R$0,00 (TÉO 06.2) | TÉO 06.2 + doc 15.1 | **regra formal vence**: nenhuma tolerância | AC-P3-PARITY-01..07; epsilon proibido |
| CTR-04 | ordem observada no vídeo (intercalada/iterativa) | sequência ideal do inventário TÉO 05 | ambos válidos por escopo | processo é paralelo+iterativo; modelo §2 não lineariza | contratos devem aceitar reemissão/`as_of` |
| CTR-05 | P7 "Modelo P7" = MATR460 padrão | P7 escopo MP/PA/PI folha 74 | roster + artefatos | **dois escopos do mesmo relatório**, mesma data-base; não são produtores distintos | contrato P7 precisa de `report_scope`+`as_of` — DEC-12 aprovou os dois escopos (`all_products`/`mp_pi_pa`); mecanismo técnico do recorte resumido permanece E2 |
| CTR-06 | "em processo" = SB9 armazém 99 (293.273,09) | EM PROCESSO P7 = 355.240,51 | doc 84 §5.2 | MATR989 = loc99 + material alocado a OP aberta; **não são iguais** | H02 ≠ SB9 loc99 sozinho |
| CTR-07 | envio externo de pacote por e-mail/canal (TÉO 31.16/33, doc 36) | submissão interna no Portal (doc 37) | decisão posterior específica | **doc 37 supersede doc 36**; e-mail = notificação | P5 portal-first; T04/E04 limitados ao histórico |
| CTR-08 | baixas custom `_F190C` (quebrada) | FINR190 padrão | acervo + paridade | produtor pagar = `FINR190_DLP.PRX` (variante DLP localizada); receber = `DLP06R01` custom sem fonte | payable contrato OK; receber binding → E1 |
| CTR-09 | taxonomia `02xx/03xx/04xx` (corpus) | `02/03/05` (TÉO 20) | — | **preservada como conflito**; owner da taxonomia = E10 | não normalizar por suposição |
| CTR-10 | divergência verbalizada `48.660,77` | computada `48.660,78` | — | **preservada**: R$0,01 sem explicação | GAP-02; relatório exibe valor da fonte, não o verbalizado |
| CTR-11 | SB9@30/09 f01 = 4.812 linhas / R$3.884.439,52 (probe 1) | 0 linhas (re-check) | doc 49 §7 | `EXECUTION_DRIFT`: faixa regravada em 21/10 — estado muda | fail-closed; `as_of` explícito obrigatório |
| CTR-12 | "MATR460 não confirmado" (docs 46/47) | roster oficial "Estoque P7→MATR460" | roster `Contabilidade liberações.xlsx` | vinculação confirmada pelo roster; fonte/RPO e params seguem E2 | rotina confirmada; binding de produtor pendente |
| CTR-13 | `A pagar`/`A Receber` como baixas | posições em aberto | doc 83 §6 | artefatos distintos (FINR130/150) | não misturar nas APIs de baixas |
| CTR-14 | `Analise.xlsx` ≈ SB2 corrente | `B9_CM1`@30/09 | doc 83 §6 | SB2 descartado por amostra; snapshot vence | snapshot/`as_of` é a referência |
| CTR-15 | "divergência temporal" SB9×MATA280 | janelas coincidem | doc 83 R15 | artefato de fuso: `I_N_S_D_T_` grava UTC (+3h) | normalizar timezone em evidências temporais |
| CTR-16 | doc 117 listava fontes indisponíveis (`Material em processo`, `cpv`, `canal`, `_F190C`, filial 02) | ciclo 2 reconciliou esses artefatos | docs 83/84 | **atualização de estado**: `Material em processo.xlsb` lido integral (57.359 linhas); `cpv 09 26 matriz.xlsb` lido (14.382); canal resolvido por decisão; `FINR190_DLP` localizado; f02 coberta em Invent/Fat×MOD | gaps do doc 117 §4 substituídos por §12 desta base |
| CTR-17 | matriz R01–R15 declarativa no Portal | endpoints conectados | HEAD | apenas `financial-settlements` (SE5) e `stock-inventory` (SB9 exploratório) são dados reais; demais entradas são catálogo | honestidade de fonte por relatório |
| CTR-18 | "abertura formal exige template PUBLISHED" (AS-IS técnico) | consulta/abertura desacopladas (decisão 26/10) | docs 112/113 + runtime V015 | TARGET aprovado e parcialmente implementado (abrir sem checklist); demais gates em reconciliação | contratos de competência em reconciliação (§9) |

---

## 6. Catálogo canônico de relatórios e transformações

Estado de paridade por item (gates do Ciclo 2 — [doc 86](./86-ciclo2-relatorio-final-consolidado-e-handoff.md), [doc 84](./84-ciclo2-matriz-paridade-monetaria.md), [doc 85](./85-ciclo2-catalogo-regras-negocio-r01-r15.md)). `G6` = aceite funcional humano — **0/15 em todos os itens**; paridade técnica não é aceite.

| Código | Relatório / artefato | Produtor / fonte | Filtros observados | Transformação Excel | Consumidor | Estado | Contrato |
|---|---|---|---|---|---|---|---|
| R01 | Baixas a pagar (`pagos 09 26.xlsb`, `Pagos por dt/nat.pdf`) | `FINR190`+`FINR190_DLP.PRX`; layouts `DLP06R01.prt`/`nat.prt`; SE5×SE2/SED/F7G | competência por `E5_DATA`; exclusões FINR190 (ver §7 DR-02) | export p/ xlsb | Contabilidade | G1–G5 `PASS`, G6 `PENDING` | **implementado**: `/financeiro/baixas/*` api-delpi + `/closing/financial-settlements*` BFF |
| R02 | Baixas a receber (`Recebidos.xlsb/pdf`) | `DLP06R01` custom — `SOURCE_MISSING` | idem | idem | Contabilidade | G5 `PASS`, G4 `PENDING` (E1) | idem R01 |
| R03 | Registro de Inventário P7 / Bloco H (`Estoque.pdf`, `Resumo Estoque.pdf`) | `MATR460` (roster); **`A460UNIT.prw` localizado no acervo** — hook por produto `MP7GDA.VALOR += workfile.TOTAL` (custo, não escopo); `matr460.prx` ausente (`SOURCE_MISSING`); workfiles `MP7_*` retêm até ~04/2024 | data=fim competência; `Saldo em Processo=Sim` confirmado; `Poder3` 4 opções — opção efetiva por emissão `PENDING`; `MTR460` 25 perguntas catalogadas **sem parâmetro de tipo** → escopo MP/PA/PI exige mecanismo fora do SX1 (E2); DEC-12: `all_products`/`mp_pi_pa` | nenhuma | Contabilidade/SPED | binding totalização `PROVEN`; G4/G5 `PENDING` (E2) | **parcial**: `/closing/stock-inventory` (SB9 exploratório, não-P7, `RUNTIME_GATE` doc 49) |
| R04 | Consumo por OP | `MATR860` candidato | — | — | ? | `BLOQUEADO` (sem artefato) | nenhum → GAP-01 |
| R05 | Entradas e Saídas (`Entradas e saidas.pdf`) | `MATR320.prt` padrão via SP `MAT056` | competência, filial | nenhuma | conciliação tripla | G1–G5 `PASS` | candidato RQ-ANL-02 |
| R06 | Kardex/CPV armazém 01 (`cpv 09 26 matriz.xlsb`) | `MATR910` (`matr910_dlp.prx`) | loc 01; UNION SD1/SD2/SD3; `F4_ESTOQUE='S'`; `D3_ESTORNO<>'S'`; `ORIGLAN<>'LF'` | nenhuma | conferência interna | G1–G5 `PASS` | candidato RQ-ANL-05; CPV vivo `REUSE_PARTIAL` |
| R07 | Inventários (`Invent.xlsb`) | `MATR910` | `D3_DOC='INVENT'` TES 999/499; f02 loc 01+99 | work file | conferência interna | G1–G5 `PASS` | idem |
| R08 | Material em Processo / H02 (`Material em processo.xlsb`) | `MATR989` analítico (`SOURCE_MISSING`) | OPs abertas + loc99 | nenhuma | conciliação tripla + P7 | G1–G5 `PASS` (empírico), fonte E8 | candidato RQ-ANL-02 |
| R09 | Faturamento × MOD (`Fat x MOD.xlsb`) | `DLP204` (`DLP204.prw`; SP ausente → E9) | competência `D2_EMISSAO`, TES `F4_DUPLIC='S'` | abas por filial | custos/Controladoria | G4 `PASS`, G5 `INCONCLUSIVE` | candidato RQ-ANL-08 |
| R10 | Notas por Centro de Custo (`CC matriz.xlsb`) | `EDAPP` export SD1 (`SCAGQGA0.XML`) | `D1_DTDIGIT`∈mês − 13 TES − MP − benefícios | +coluna manual Direto/Ind/Adm | Controladoria | G1–G5 `PASS`; confirmações E10 | candidato RQ-ANL-06; `vw_fin_despesas_centro_custo` `REUSE_PARTIAL` |
| R11 | NF a desconsiderar (`NF a desconsiderar.xlsb`) | `EDAPP` export SD2 (`Planilha2`) | `9035∩594∩D2_EMISSAO∩f01` | roster do export | conferência faturamento | G1–G5 `PASS`; finalidade E11 | candidato |
| R12 | Acompanha Custos / Reposição / Refaz | `MATA320`/`MATA300`/wizard `MATA330`; `Analise.xlsx` | wizard 4 etapas | `Analise.xlsx` = export etapa 3 | operação | G4 `PASS`, G5 `INCONCLUSIVE` | nenhum (ERP-exec) |
| R13 | Extratos e aplicações | **externa** (bancos/XP/BB) | — | — | pacote DRE | G1 `PASS`, resto `PENDING` | P2 upload TARGET |
| R14 | Importação / SWIFT / câmbio / ACSI | externa/sem evidência | — | — | pacote | `BLOQUEADO` | P2 upload TARGET |
| R15 | Cutoff / virada / SB9 | `MATA330→MATA280→SB9`; `MV_ULMES` | — | — | estado de fechamento | G3/G4 `PASS`, G5 `INCONCLUSIVE` | estado `STOCK_CLOSED` via T03/canonical owner |

Nota CTR-16: o doc 117 registrava `Material em processo.xlsb` e `cpv 09 26 matriz.xlsb` como extrações indisponíveis/limitadas; o Ciclo 2 completou a leitura com paridade — esta base canônica prevalece nesses pontos, sem apagar o registro histórico do 117.

---

## 7. Catálogo de regras determinísticas

Regras homologáveis hoje (evidência `PROVEN`); owner funcional = Controladoria; owner técnico canônico de dados TOTVS = `api-delpi`; consumo pelo Portal via BFF. "Homologação documental" ≠ "aceite funcional" — G6 segue `PENDING` para todos.

| ID | Regra | Fórmula / seleção | Entradas | Status |
|---|---|---|---|---|
| DR-01 | **Conciliação tripla** | `Δ = ENTRADAS_SAIDAS − P7 − H02`; `PARIDADE_OK ⟺ Δ = R$0,00`; tolerância `NONE`; fonte indisponível ≠ 0 | MATR320 total, P7 total (mesmo `as_of`), MATR989 total | `PROVEN`+homologada (TÉO 06.2, doc 15.1) |
| DR-02 | População R01 | WHERE `FINR190_DLP`: `E5_MOTBX<>'DSD'`, `E5_MOVCX<>'S'`, `E5_SITUACA∉{C,E,X}`, `E5_HISTOR` sem "Baixa Automatica / Lote", `E5_TIPODOC∉{DC,D2,JR,J2,TL,MT,M2,CM,C2,ES,E2}`+par estorno `ES`/`E5_ORIGEM<>'FINA100'`, regra `CD`, `E5_DTCANBX=' '`; vínculo SE2 por chave de título | SE5/SE2/SED/F7G/SA2 | `PROVEN` (doc 84 §1) |
| DR-03 | Valores R01 | `Total Baixado=E5_VALOR`; `Jur/Multa=E5_VLJUROS+E5_VLMULTA`; `Correção=E5_VLCORRE`; `Descontos=E5_VLDESCO+E5_VLDECRE`; `VO=E2_VALOR` (942), INV aglutinado=`E5_VALOR` (5), NF-grupo=soma do grupo (1) | idem | `PROVEN` |
| DR-04 | População/valores R02 | 649 SE5×SE1 + 8 `PA`/`FINA750` sem título; supressão das 8 decomposições `MT/JR/DC` (valores já no `E5_VALOR` do `VL` — inferida, fonte ausente); `VO=E1_VALOR` ou provisão `'P'` espelhada; relabel de motivo em 3 linhas | SE5/SE1 | `PROVEN` artefato / `INFERRED` regra geral (E1) |
| DR-05 | Equação MATR320 | `SA = SI + Compras + MovInt + Requis + Transf + Produção − Vendas + DevV − DevC + EntPT − SaiPT` (TransfProc é memo) | SD1/SD2/SD3 classificados por coluna (poder3/`est`=S/`TIPO='D'`) | `PROVEN` (doc 84 §4) |
| DR-06 | Classificação MATR320 | Compras=SD1 `poder3=N`/`est=S`/`tipo≠'D'` `D1_CUSTO` `DTDIGIT`∈mês; Vendas=SD2 `D2_CUSTO1`; MovInt=SD3 OP-vazio `CF[3]≠'3'`; Requis=SD3 OP-preenchido; EntPT=SD1 `poder3≠'N'`; SaiPT=SD2 `poder3≠'N'`; DevV/DevC=`TIPONF='D'` | idem | `PROVEN` |
| DR-07 | P7 EM ESTOQUE | saldo físico `SB9`-compatível **excluindo `MV_LOCPROC='99'`** no `as_of` da emissão | SB9 `as_of` | `PROVEN` (binding totalização) |
| DR-08 | P7 EM PROCESSO = H02 | `MATR989` = SD3 `D3_CF∈{RE0,RE1,RE2,RE9}` de OPs abertas + `SB9010` loc99 não-OP | SD3/SB9/SC2 | `PROVEN` (doc 84 §5.2) |
| DR-09 | Kardex MATR910 | UNION `SD1(D1_DTDIGIT)`+`SD2(D2_EMISSAO)`+`SD3(D3_EMISSAO)`; `F4_ESTOQUE='S'`; `D3_ESTORNO<>'S'`; `D*_ORIGLAN<>'LF'`; ordem data+`D3_NUMSEQ`; saldo cadeia `B9`@mês-anterior | SD1/SD2/SD3/SB9 | `PROVEN` |
| DR-10 | INVENT | `D3_DOC='INVENT'`; TES 999 (`RE0` saída) / 499 (`DE0` entrada) | SD3 | `PROVEN` |
| DR-11 | Seleção R10 | `D1_DTDIGIT`∈mês ∩ `D1_TES∉{001,003,016,020,030,040,080,083,085,120,159,204,318}` ∩ `D1_TP<>'MP'` ∩ benefícios-saúde/odonto-sem-CC fora | SD1 | `PROVEN`; confirmação narrada → E10 |
| DR-12 | Seleção R11 | `D2_GRUPO='9035'`∩`D2_TES='594'`∩`D2_EMISSAO`∈mês∩`D2_FILIAL='01'`; `D2_CUSTO1=0` estrutural (`F4_ESTOQUE='N'`) | SD2 | `PROVEN` |
| DR-13 | Fat×MOD | `QtdFat`=Σ`D2_QUANT` PA-âncora (TES `F4_DUPLIC='S'`); `MOD`=`H1_CCUSTO`; `Quantidade`=`SHY.HY_TEMPAD` fallback `G2_TEMPAD`; `rate`=`SBZ.BZ_CUSTD` `as_of`; `Horas=QtdFat×Quantidade`; `CustoTotal=Horas×rate` | SD2/SHY/SG2/SH1/SBZ | `PROVEN` (99,4%); residuais E9 |
| DR-14 | CPV vivo | `Σ SD2.D2_CUSTO1`, `D2_CF∈{5101,5124,6101,6124}`, por `D2_EMISSAO` | SD2 | `CODE_PRESENT` (`/supplies/cpv`); sem `as_of` → `REUSE_PARTIAL` |
| DR-15 | Análise CM | `CM final ≡ B9_CM1`@fim da competência | SB9 | `PROVEN` (98,6%) |
| DR-16 | Disciplina temporal | todo indicador de fechamento exige `competence`+`filial`+`as_of`/versão; estado mutável (`EXECUTION_DRIFT` SB9) ⇒ fail-closed, nunca zero | — | regra consolidada desta base |

**Gatilhos de revalidação (consolidados de TÉO 31.14 + doc 10):** alteração de movimentações após corte; faturamento ainda ativo; reprocessamento/reabertura no ERP; reemissão de relatório com novo `as_of`; dados fora da mesma referência temporal. `SYSTEM_READINESS_SIGNALS → HUMAN_CONFIRMATION → CUTOFF_CONFIRMED`; sem fallback manual silencioso; `STOCK_CLOSED_SOURCE = CANONICAL_OWNER_STATE`.

---

## 8. Matriz AS-IS × TARGET (inclui runtime verificado no HEAD)

| Etapa AS-IS | Problema | Existe hoje no Portal (HEAD) | Contrato existente | Lacuna | Evolução |
|---|---|---|---|---|---|
| OPS-01–04 cadeia de custos/cutoff | execução manual no ERP; estado opaco | `P3CutoffPanel`, `p3_routes` (estado P3), `stock-inventory` SB9 (exploratório) | P3 estado + readiness (`CODE_PRESENT`); `STOCK_CLOSED` canônico = T03 pendente | estado externo oficial, writer `MV_ULMES` (E5) | P3: sinais→confirmação humana→revalidação (TARGET doc 10); nunca escrita ERP na V1 |
| OPS-05/06 baixas | geração manual PDF/Excel | `FinancialSettlementsPage` + BFF + api-delpi SE5 (**conectado**) | `/financeiro/baixas/*` + `/closing/financial-settlements*` | paridade contra artefato oficial não validada em produção; log de inconsistências | homologação + cobertura no checklist P2 |
| OPS-07 E/S | relatório PDF | matriz relatórios (declarativa para R05) | — | contrato MATR320 canônico (DR-05/06 provados) | RQ-ANL-02 |
| OPS-08 P7 | reemissões sem versão | `stock-inventory` SB9 **não é P7** (rótulo honesto); já expõe `report_scope=all_products|mp_pi_pa` exploratório | `/financeiro/stock-inventory` exploratório | contrato P7 oficial (escopo+`as_of`+emissão) — DEC-12 encerrou a escolha funcional; mecanismo do recorte segue E2 | RQ-ANL-01 |
| OPS-09 H02 | idem | — | — | contrato MATR989 (DR-08 provada, fonte E8) | RQ-ANL-02 |
| OPS-10 kardex | conferência manual | — | CPV `/supplies/cpv` `REUSE_PARTIAL` | contrato kardex/`as_of` | RQ-ANL-05 |
| OPS-11/12 EDAPP exports | trabalho manual, classificação manual | — | `despesas-centro-custo` `REUSE_PARTIAL` | seleção R10/R11 + taxonomia E10 | RQ-ANL-06 |
| OPS-13 Fat×MOD | consolidação manual | — | — | contrato DLP204 (modelo provado, E9) | RQ-ANL-08 |
| OPS-14 conciliação | cálculo manual em Excel | P3 estrutura pronta (estados) | doc 10/15.1 (TARGET) | motor determinístico + fontes | RQ-ANL-03/04 |
| OPS-15 divergências | investigação manual | "O que precisa de atenção" (Visão geral/Relatórios) | cockpit/reports read | drill-down por grupo/linha com proveniência | RQ-ANL-04 |
| OPS-16 pacotes/entrega | envio manual de arquivos | **P5 runtime**: `packages_routes` (15 endpoints: versões, finalizar, submeter, clarifications, complementos, recipients) + `PackagesPage`; **P2 runtime**: `documents_routes` + `validations_routes` + catálogo transacional `PUT /admin/checklist-templates/{id}/documents/{key}/requirement` (DR-1, GATE-015) | TÉO 31.3–31.16, docs 12/37/113/114 | homologação G2/G3 | continuidade sob gates |
| OPS-17 clarifications | e-mail/reunião | `document_message` (INTERNAL/SHARED) + `document_adjustment_request` (`OPEN→ANSWERED→CONFIRMED`); `received_documents_routes` + `access.dre` | docs 113/115 | resposta não encerra — confirmado; homologação | idem |
| adm/catálogos | recadastro manual | P6 runtime: `admin_checklist_routes`, `admin_catalogs_routes`, `CatalogsAdminPage`, `DocumentsAdminPage`, `ChecklistAdmin*` | RQ-P6, doc 13 | seed E01/E05/E06 | continuidade |
| CLARA | conhecimento tribal | MCP 18 tools publicadas (READ autenticado no ChatGPT, corpus 52 fontes/1.298 itens — doc 111); `clara_consent_routes` + batch | doc 94 (D01=B) | ACT delegado, G2/G3 | checkpoints M00–M06 doc 93 |

**Veredito de estado:** `CODE_PRESENT` para competências/documentos/validações/pendências/pacotes/P3-estado/admin/DRE/CLARA-READ e dados reais SE5+SB9; relatórios R03–R15 na matriz permanecem declarativos/manuais/externos (CTR-17). HTTP 200 ≠ resultado homologado; `TEST_NOT_RUN` onde não houver smoke homologado.

---

## 9. Contratos técnicos — existentes × candidatos (RQ/AC revisados)

Boundaries congelados: `api-delpi` = regras/consultas canônicas TOTVS; `controllership-finance-api` = orquestração/projeções do Portal; MFE = apenas BFF; Core = identidade/effective permissions; sem banco de domínio alheio como API.

**Existentes (implementados, HEAD):** `GET /closing/financial-settlements[ /summary]` (side=payable|receivable, período, nature/movement, paginação) → api-delpi `GET /financeiro/baixas/{pagar,receber,resumo}`; `GET /closing/stock-inventory` (period, branch, report_scope, warehouse) → api-delpi `/financeiro/stock-inventory` (SB9 exploratório); `/supplies/cpv` (api-delpi, fora do fechamento); surface interna BFF completa P1–P6 + DRE (§8).

**Revisão dos RQ-ANL (ledger 23 §ANALYSIS):**

| RQ | Regra de negócio | Producer→consumer | Estado anterior | **Estado revisado por esta base** |
|---|---|---|---|---|
| RQ-ANL-01 P7 | DR-07/08; escopos `all_products`/`mp_pi_pa` (DEC-12; nomes canônicos do exploratório doc 49 §9); `as_of`+emissão | api-delpi→BFF→MFE/P3 | dependia de fonte oficial | **Desenho detalhado autorizado para o escopo completo** — binding de totalização provado + decisão de escopo encerrada; recorte `mp_pi_pa` oficial `PENDING_SOURCE` até E2 (params/produtor/RPO; SX1 sem tipo); rótulo anti-"SB9=P7" obrigatório |
| RQ-ANL-02 H02+E/S | DR-05/06/08 | api-delpi→BFF→P3 | pendente | **Desenho detalhado viável** — regras provadas; E/S por equação de colunas ou views MATR320; H02 por reconstrução MATR989 (E8 pendente para fonte oficial) |
| RQ-ANL-03 motor conciliação | DR-01/16 | api-delpi (cálculo) → BFF → P3 | pendente | **Desenho detalhado viável** após contratos de dados; motor determinístico versionado; `UNAVAILABLE≠0` |
| RQ-ANL-04 drill-down | divergência por grupo/produto/armazém/OP | api-delpi→BFF | pendente | **Viável** — SD3/SB9 sustentam decomposição (doc 84 §4.3 prova ponte por produto) |
| RQ-ANL-05 kardex | DR-09/10 | api-delpi→BFF | dependia lista CF Joyce | **Dependência resolvida** — filtros provados por paridade (RE0/1/2/9/3, DE0/4/6, INVENT 999/499); desenho viável |
| RQ-ANL-06 SD1/CC | DR-11 | api-delpi→BFF→P4/P2 | dependia §17.2/3 | **Desenho viável para a seleção**; classificação Direto/Ind/Adm exige catálogo-mestre (E10) — não embutir taxonomia inventada |
| RQ-ANL-07 baixas | DR-02/03/04 | api-delpi→BFF→MFE | `_F190C` pendente | **Implementado** (read-only); residual = validação de paridade contra artefato + receber E1 |
| RQ-ANL-08 Fat×MOD | DR-13 | api-delpi→BFF | dependia §17.4 | **Desenho viável** — modelo provado; E9 (SP/tempos/SBZ) condiciona G5 |
| RQ-ANL-09 bancos | lista configurável; comprovante se sem movimento | cadastro P6→P2 | dependia E01 | **Decisão existe** (configurável); seed = E01 pendente |
| RQ-ANL-10 CLARA KB | glossário/regras/limites | corpus→MCP | pendente | **Esta base é a referência** + doc 94 + §10 |

**Novos candidatos (registro, não autorização):** RQ-ANL-11 — contrato `as_of`/versionamento de emissões (cross-cut, DR-16); RQ-ANL-12 — consumo por OP (bloqueado GAP-01); RQ-ANL-13 — entregáveis externos R13/R14 via P2 upload com roles configuráveis (E05); RQ-ANL-14 — `STOCK_CLOSED` canonical owner state (T03/E5).

---

### 9.1 Proposta de contrato — P7 oficial (TARGET, RQ-ANL-01; P7-EVIDENCE-REUSE-003, 28/10/2026)

Decisão funcional `DEC-12` encerrada; o desenho abaixo é proposta documental — **nenhum endpoint foi criado** nesta execução.

**Escopos (nomes canônicos — já existem no contrato exploratório, doc 49 §9):**
- `all_products` — todos os produtos da emissão completa; escopo principal de análise interna e **operando P7 da conciliação tripla** (a emissão usada na demonstração — folha 91 — continha as 10 classificações + EM PROCESSO; doc 83).
- `mp_pi_pa` — recorte MP/PA/PI conforme classificação oficial da emissão; escopo do entregável à Contabilidade/DRE. Equivale a `B1_TIPO IN ('MP','PI','PA')` **+ exclusão de material em poder de terceiros** no `as_of` (fato observado — ver veredito de equivalência abaixo; mecanismo oficial `PENDING`, E2).

**Entradas:** `competence=YYYY-MM` (obrigatório), `filial` (escopo de dados, não permission), `report_scope` (obrigatório), `third_party_materials: "include"|"exclude"` (candidato ao parâmetro `02 Saldo em Poder 3º?` do `MTR460`; oficial `all_products`=`include`, `mp_pi_pa`=`exclude` — binding `PENDING` E2), `emission`/`as_of` (quando emissões persistidas existirem), `warehouse` opcional, paginação limitada.

**Saídas:** `items[]` por produto (código, descrição, tipo, armazém, quantidade, valor, custo unitário, valor em processo); `summariesByType[]` com `em_estoque`/`em_processo` por classificação; `total_geral`; `emission` (id, `emittedAt`, data de fechamento, parâmetros efetivos, folha, versão/RPO quando identificável, destinatário quando aplicável); `status` (`available|source_missing|incomplete|parity_pending`).

**Totalizadores obrigatórios (homologados no dado):** `EM_ESTOQUE + EM_PROCESSO = TOTAL_GERAL` exato (BR-R03-006); EM ESTOQUE exclui `MV_LOCPROC='99'` (BR-R03-004, prova centesimal 3.591.191,36); EM PROCESSO = medida `MATR989`, não estoque físico de loc 99 (BR-R03-003).

**Reaproveitamento da implementação existente (P7-SCOPE-CONTRACT-004, 28/10/2026):**

| Componente | Já existe no api-delpi | Reuso no contrato oficial |
|---|---|---|
| `report_scope`=`all_products`/`mp_pi_pa` | `financeiro_stock_inventory/constantes.py` + `stock_inventory_request.product_types()` | nomes e validação preservados — mesma enumeração |
| Classificação de tipos | `domain/totvs/protheus_product_types.py` (MP/PA/PI + labels PT) — **owner canônico**, reusado por supplies/product/production | única fonte de classificação; nenhuma segunda regra de tipos |
| Competência→snapshot | `reference_date()` → `B9_DATA` último dia calendário | mesma chave temporal; `as_of` = data de fechamento/emissão |
| Indisponibilidade | `source_missing`/`incomplete`/`no_matching_items` (nunca zero falso) | preservada integralmente |
| Filial como filtro | `normalize_branch_scope`/`requested_branches` | preservada (dado, não permission) |
| Totalização oficial | — (exploratório não separa EM PROCESSO) | EM ESTOQUE ex-`MV_LOCPROC` + EM PROCESSO `MATR989` (RQ-ANL-02) |
| Exclusão poder3 do recorte | — (exploratório é tipo-only) | `third_party_materials` — ver veredito abaixo |

**Veredito de equivalência (CP3):** o filtro canônico `B1_TIPO IN ('MP','PI','PA')` **reproduz PA e PI exatamente** (valores bit a bit entre folha 74 e emissão completa — doc 80 §35) e **não reproduz MP**: a emissão oficial exclui adicionalmente produtos MP com quantidade em poder de terceiros no `as_of` (Δ EM ESTOQUE −587.698,28 — modelo `QTNP@emissão>0` = 587.621,85, residual 76,43; Δ EM PROCESSO −77.251,73 — modelo 79.194,35, residual +1.942,62). **Filtro de tipo é necessário, mas insuficiente**; a diferença mínima comprovada é a exclusão poder3 em MP, candidata ao parâmetro `02` do `MTR460` (`PENDING`, E2).

**Proveniência:** `producer="matr460"` + identidade de emissão + `as_of`; cadeia `MATR460→MP7_*→MP7GDA→A460UNIT` documentada e hook confirmado no acervo (`04. Estoque/A460UNIT.prw`); o exploratório SB9 permanece com `officialP7:false`.

**Erros e indisponibilidade:** `source_missing`/`UNAVAILABLE` nunca viram zero; snapshot SB9 ausente ≠ P7; paridade matemática isolada não prova equivalência ao relatório oficial; comparações somente entre emissões comparáveis (mesma competência/filial/`as_of`/escopo).

**Segurança:** effective permission `controllership-finance.access` server-side, fail-closed (interno). O escopo `mp_pi_pa` alcança a DRE **via pacote documental submetido** (DEC-05/08), não via consulta DRE a relatórios operacionais (doc 112 — exigência de ocultação para o perfil DRE).

**Paridade e aceite:** G4 = binding de totalização ao centavo contra emissão oficial de referência; G5 = reprodução `as_of` por escopo — completo `DESIGN_READY`, `mp_pi_pa` `PENDING_SOURCE` até E2; G6 = aceite humano da Controladoria.

**Contratos definitivos (P7-IMPLEMENTATION-READINESS-005, 28/10/2026):** [doc 119](./119-contratos-p7-implementacao-readiness.md) fecha o levantamento técnico — fórmula MATR989 por produto, semântica poder3 `QTNP`/`QTER`/`SB6`/`F4_PODER3` verificada em dados, contratos de consulta/exportação/integração documental/segurança/erros, plano de implementação por owner e gate final `PENDING_EXTERNAL_EVIDENCE` com subconjunto implementável (`all_products` + infraestrutura completa; `mp_pi_pa` como escopo declarado `parity_unverified` até E2). Evidência nova: SB9@30/09 existe nas duas filiais; filial 01 = MATRIZ; drift MP +8.182,43 (revalorização pós-emissão, `STALE_EVIDENCE`); PA/PI/II ex-99 bit a bit iguais ao oficial; QTNP/QTER só em `B2_LOCAL='01'`; exclusão do resumo é por produto (conjunto `QTNP>0`), não por quantidade.

## 10. Mapa de conhecimento para a CLARA (referência, não runtime)

**Glossário canônico:** P7 = Registro de Inventário Modelo P7 (MATR460); H02 = Material/Saldo em Processo (MATR989); E/S = Resumo Entradas e Saídas (MATR320); sacramentação/virada = `MATA330`→`MATA280`→`SB9`+`SC2`+`MV_ULMES`; CM = custo médio (`B9_CM1`/`B9_VINI1`); poder3 = `F4_PODER3` (material de terceiros); loc99 = `MV_LOCPROC` (armazém de processo); TES = `F4_*`/`D1_TES`/`D2_TES` (não confundir com CFOP `D*_CF`); MOD = mão de obra direta (`MOD`+`H1_CCUSTO`, rate `SBZ.BZ_CUSTD`); OP = ordem de produção (`SC2`/`SD3 D3_OP`); EDAPP = consulta genérica que exporta SD1/SD2; competência = `YYYY-MM`; filial = dimensão de dado, não permission.

**Regras que a CLARA pode citar:** DR-01–DR-16 com proveniência (sempre citar fonte: TÉO 06.2, docs 83/84/85/90/113/118); dependências OPS-*; exceções conhecidas (poder3, benefícios, `PA` sem título, decomposições MT/JR/DC, MOD* sem SB9).

**Perguntas que pode responder:** "o que é o P7?", "por que EM PROCESSO ≠ armazém 99?", "o que bloqueia a paridade?", "qual relatório sustenta cada número?", "quais etapas do fechamento existem?".

**Exigem resultado determinístico (nunca por linguagem natural):** valores de saldo/baixas/divergência — sempre via tools/contratos; paridade — sempre motor DR-01.

**Não pode afirmar sem evidência:** causa da divergência de R$48.660,78 (GAP-02); consumo por OP (GAP-01); taxonomia Direto/Ind/Adm como regra oficial (E10); parâmetros efetivos do P7 (E2); resultado de sacramentação futura; "zero" quando fonte indisponível.

**Limites (doc 94):** equivalência de autorização ≠ execução automática; ACT só com aval explícito por operação (D01=B); CLARA não corrige ERP, não inventa causa, não calcula saldo por interpretação; fail-closed sem fonte.

---

## 11. Registro permanente de decisões e dúvidas encerradas

| ID | Questão encerrada | Resposta consolidada | Decisão/fonte | Condição de reabertura |
|---|---|---|---|---|
| DEC-01 | Canal de envio do pacote | submissão interna Minha DELPI; e-mail = notificação | doc 37 (supersede doc 36/TÉO 33 Q22-pendente) | mudança formal de canal pelo PO |
| DEC-02 | Q01–Q30 TO-BE | aceitas em bloco | TÉO 33 | revisão formal do processo |
| DEC-03 | Paridade monetária | exata R$0,00, sem tolerância | TÉO 06.2 + doc 15.1 | nova regra fiscal homologada |
| DEC-04 | Lista de bancos | configurável por unidade (nunca hardcode) | TÉO 33 E01 | nova decisão PO |
| DEC-05 | Escopo DRE | permission `access.dre`; entrega = assignment `RECIPIENT`+versão `SUBMITTED`; sem aceite DRE | docs 91/115 | gate de segurança posterior |
| DEC-06 | MOD histórico | opção C (histórico homologado + corrente recalculado) | doc 81 (E6) — direction only; E6-D1..D6 pendentes | implementação efetiva |
| DEC-07 | Portal escreve no ERP? | **não na V1** (correção no Protheus pelos responsáveis; portal orienta) | docs 10/113 §2.5 | novo contrato+GO |
| DEC-08 | Duas permissions | três: `access`, `manage`, `access.dre` | docs 91/115 | mudança manifesto |
| DEC-09 | Consulta mensal exige abertura? | não — consulta por mês de referência; abertura é ação formal contextual (`access`) | docs 112/113 | reconciliação de contratos |
| DEC-10 | `Finalizar`/`Enviar`/`Concluir`/`Aceitar` | estados distintos; versão imutável; conclusão = C2 (pacotes aplicáveis submetidos + zero clarification + aceite por área) | doc 37; doc 113 | — |
| DEC-11 | CLARA executa ações? | sim, por delegação com aval por operação (D01=B); canal ≠ entidade autônoma | doc 94 §2 | contrato ACT |
| DEC-12 | Escopos do P7 | **dois escopos explícitos e separados**: `all_products` (P7 completo — análise interna da Controladoria; operando da conciliação tripla) e `mp_pi_pa` (recorte MP/PA/PI — entrega documental à Contabilidade/DRE); usuário autorizado escolhe ("Todos os produtos" × "MP, PA e PI — DRE"); totais nunca misturados nem alterados silenciosamente; contrato preserva competência/filial/escopo/`as_of`/parâmetros/versão/momento de emissão/destinatário | PO — execução P7-EVIDENCE-REUSE-003 (2026-10-28); evidência base doc 80 §35 + PDFs folha 101/74 | nova regra fiscal/escopo homologada; prova do mecanismo técnico do recorte (E2) |

## 12. Registro de lacunas reais

| ID | Lacuna | Evidência de que não é resolvível hoje | Owner/status |
|---|---|---|---|
| GAP-01 | Consumo por OP (Q06): artefato/rotina/campos/destinatário | nenhum artefato na pasta; roster não lista; MATR860 candidato não observado | Controladoria — `EVIDENCE_NOT_FOUND` |
| GAP-02 | Desfecho da divergência `R$48.660,78` (Q10) | nenhuma fonte documenta investigação posterior ou causa | `NOT_PROVEN` — pode nunca ser determinável |
| GAP-03 | Fonte do produtor de recebidos (`DLP06R01`) | ausente do acervo; WHERE do FINR190 não reproduz | TI/ERP — E1 |
| GAP-04 | Parâmetros efetivos por emissão do P7 (escopo folha 74; Δ76,43/1.942,62) + mecanismo do recorte de tipos | hipótese `QTNP@emissão>0` não é regra oficial; `A460UNIT.prw` localizado (28/10) — hook de custo, **não** de escopo; `MTR460` sem parâmetro de tipo; `matr460.prx`/RPO ausente | TI/ERP — E2.1/E2.2/E2.3 |
| GAP-05 | Versão RPO implantada de todos os produtores | fonte acervo ≠ RPO | TI/ERP — E1/E7/E8/E9 |
| GAP-06 | Seed de bancos/contas + disponibilidade de extratos (só Bradesco demonstrado; XP=Dennis) | documentos externos sem dados na pasta | Controladoria — E01 |
| GAP-07 | Correção pós-sacramentação: quem, quando, como (E02); executor/perfis da virada (E03) | decisões de produto pendentes | PO/Controladoria |
| GAP-08 | Semântica de `Reabertura de estoque` e critério de homologação | item existe na lista `Fechamentos`; efeitos não provados | Controladoria+TI — E12.6/E12.7 |
| GAP-09 | Taxonomia oficial CC (Direto/Ind/Adm; 0407/0413; benefícios colaborador×empresa) | classificação manual; conflito de nomenclaturas | Controladoria — E10 |
| GAP-10 | Apuração que consome o desconsiderar (CPV×ROL×DRE) e eixo do filtro EDAPP | seleção provada, finalidade não | Controladoria — E11 |
| GAP-11 | Writer interno SB9/`MV_ULMES` (função/RPO) | SB9/SX6 não auditáveis por TTAT | TI/ERP — E5 |
| GAP-12 | Cobertura filial 02 (artefatos majoritariamente Matriz) | f02 parcial (Invent, Fat×MOD aba 2, FINR `E5_FILORIG`) | análise por competência |
| GAP-13 | Identidade do subconjunto "log de inconsistências" FINR190 | total reconstruído em agregado; linhas não reproduzidas | TI/ERP — requer log de emissão |
| GAP-14 | Detalhe operacional do canal físico/eletrônico histórico | superseded pelo TARGET doc 37 | baixa prioridade |
| GAP-15 | T04 (capacidade corporativa de envio externo) | irrelevante ao P5 V1 (portal-first) | manter inventário apenas se canal externo voltar |

---

## 13. O que o Portal pode automatizar × o que permanece ERP/humano

**Automatizável (com evidência `PROVEN` de reprodutibilidade):** leitura de baixas pagar/receber (já implementada); consulta de estoque/inventário exploratória (já implementada, com rótulo honesto); contratos E/S, H02 e — condicionado a E2 — P7; kardex/INVENT; seleções R10/R11; Fat×MOD; motor de conciliação tripla determinístico; checklist/documentos/validações/pacotes/pendências (já em runtime, em homologação); catálogo DRE e entrega a destinatários (implementado); notificações e tarefas.

**Permanece exclusivamente no ERP:** todos os `ERP_EXEC` (MATA320/300/330/280), reabertura de estoque, correções de divergência, write-back de classificação — [doc 113 §2.5](./113-plano-canonico-fluxo-fechamento-mensal-proc0072.md).

**Permanece decisão humana (mesmo quando assistido):** confirmação de cutoff (`HUMAN_CONFIRMATION`); aceite de documentos/pacotes; confirmação de sugestão IA (P4); conclusão mensal; ações CLARA por delegação com aval (doc 94); definição de taxonomia, seeds e listas administradas (P6/`manage`).

---

## 14. Fontes oficiais ainda a integrar (prioridade)

1. **P7/MATR460** — parametrização por emissão + produtor (E2) → contrato `period+filial+scope+as_of`.
2. **H02/MATR989** — fonte `matr989.prx`/RPO (E8); reconstrução física já provada.
3. **`STOCK_CLOSED`/estado canônico de virada** — writer `MV_ULMES`/SB9 (E5, T03).
4. **Recebidos `DLP06R01`** — fonte para binding completo (E1).
5. **Bancos/extratos** — fontes externas para R13 (E01; coleta documental P2, não SQL).
6. **Consumo por OP** — bloqueado (GAP-01).
7. **Entregáveis externos R14** — importação/SWIFT/câmbio (evidência insuficiente).

---

## 15. Controle de qualidade — varredura residual

Verificações executadas nesta consolidação:

- ✅ Toda conclusão material tem fonte citada (TÉO/doc/artefato/código).
- ✅ Nenhuma decisão PO sobrescrita: doc 37 > doc 36 registrado como supersensão explícita; decisões 112/113/115 respeitadas.
- ✅ Nenhuma hipótese promovida a causa: `QTNP@emissão`, supressão de decomposições R02, causa da divergência Q10 permanecem `INFERRED`/`NOT_PROVEN`.
- ✅ Nenhuma aproximação promovida a oficial: `stock-inventory` SB9 rotulado exploratório; `despesas-centro-custo`/`/supplies/cpv` marcados `REUSE_PARTIAL`.
- ✅ Nenhuma regra fiscal inventada: Bloco H = rosto do P7 via roster; requisito Contabilidade por escrito segue GAP-04.
- ✅ Nenhuma fonte indisponível representada como zero (SB9 drift → `EXECUTION_DRIFT`, fail-closed).
- ✅ Nenhuma etapa AS-IS apresentada como runtime e nenhum TARGET como AS-IS.
- ✅ Perguntas do doc 117 §17: 10/10 investigadas com fontes registradas (§4).

**Ocorrências residuais preservadas com justificativa (não são esquecimento — são estados reais):** `TO_INVENTORY` — produtor P7, parâmetros MATR460, `MATR860`, T01/T03/T05; `PENDING_CONTRACT` — `STOCK_CLOSED` canônico, seed E01/E05/E06; `UNKNOWN` — canal físico AS-IS detalhado (GAP-14); `DECISION_REQUIRED` — ~~escopo P7 homologado por destinatário~~ **resolvido por DEC-12 (28/10/2026)**; `STALE_EVIDENCE` — SB9 f01@30/09 (regravado), deltas CM demo→gravação; `TBD` — nenhum novo introduzido; reconciliação RQ-P2-039 (TÉO 31.13) × ledger 23 permanece `TO_INVENTORY` para brief P2 ([doc 90 §4](./90-ciclo3-crosswalk-end-to-end-proc0072-teo-rq-ac-portal.md)).

**Mapeamento dos `GAP-RULE-01..07` (doc 04, espelho TÉO 06.1):** 01 SD1/CC → resolvido por DR-11, taxonomia em GAP-09; 02 Kardex/CPV → resolvido por DR-09/DR-14; 03 Kardex 99/Inventário → resolvido por DR-10; 04 Fat×MOD → resolvido por DR-13 (residuais E9); 05 Conciliação tripla → resolvido por DR-01 (paridade exata, TÉO 06.2); 06 Cutoff/sacramentação → cadeia MATA330→MATA280 provada, semântica/writer em GAP-07/08/11; 07 Pacote/completude → resolvido por decisão doc 37 (portal-first) + C2.

---

### 15.1 Matriz de aproveitamento — execução P7-EVIDENCE-REUSE-003 (28/10/2026)

| Item | Evidência existente | Precisou reabrir? | Resultado |
|---|---|---|---|
| Produtor P7 | roster + vídeo + PDFs (docs 46/83) | não | `MATR460` confirmado; `matr460.prx`/`RPO` `SOURCE_MISSING` |
| Hook de customização | cadeia doc 80 §35.B; acervo `docs/13-fontes-totvs-protheus/` | sim — acervo apenas | **`A460UNIT.prw` localizado** (hook por produto: `MP7GDA.VALOR += workfile.TOTAL` — custo, não escopo) |
| Parâmetros | SX1 `MTR460` 25 perguntas (doc 85 BR-R03-008) | não | **sem parâmetro de tipo** → recorte exige mecanismo externo/custom (E2) |
| P7 completo | `Estoque.pdf` folha 101 + paridade doc 84 §3 | não | totalização `PROVEN`; operando da conciliação (folha 91 tinha 10 classificações) |
| P7 MP/PA/PI | `Resumo Estoque.pdf` folha 74 + doc 80 §35 | não | escopo provado; mecanismo `PENDING` (hipótese `QTNP@emissão` não é regra) |
| Customização TOTVS | acervo 13-fontes | sim — busca dirigida | único artefato P7 = `A460UNIT`; sem fonte de rotina MATR460/MATR989 |
| Regra de totalização | doc 84 §3 (rodada 15) | não | `PROVEN` — EM ESTOQUE ex-99 + EM PROCESSO = TOTAL |
| Conciliação | docs 15.1/83/84/118 + vídeo | não | operando P7 = escopo completo |
| Contrato | doc 49 §9 exploratório implementado | não | `report_scope=all_products|mp_pi_pa` = nomes canônicos reutilizados |
| Bloco H | roster SPEDFISCAL + `MTR460` parâmetro `23 Arq. Sped` | não | P7 alimenta Bloco H via parâmetro/rotina SPED; folha 74 **não** é declarada Bloco H |

## 16. Gate final

### A. Consolidação documental — `PASS`

O conhecimento existente foi efetivamente consolidado com proveniência, deduplicação e resolução documental das 10 questões históricas. As lacunas restantes são **lacunas reais registradas** (§12), não falha de consolidação.

### B. Prontidão para engenharia — por contrato

**Podem avançar a desenho detalhado:** RQ-ANL-02 (E/S+H02 — regras provadas; E8/E5 como pendências de fonte oficial, não de modelo), RQ-ANL-03 (motor de conciliação — regra homologada), RQ-ANL-04 (drill-down), RQ-ANL-05 (kardex), RQ-ANL-06 seleção R10 (taxonomia exige catálogo E10 em paralelo), RQ-ANL-08 (Fat×MOD — G5 condicionado a E9), RQ-ANL-11 (contrato `as_of`).

**Condicionados a decisão/inventário de fonte:** RQ-ANL-01 (P7 — E2), RQ-ANL-07 (paridade R02 — E1), RQ-ANL-09 (seed — E01), RQ-ANL-12 (GAP-01), RQ-ANL-14 (T03/E5).

**Decisão encerrada (DEC-12, 28/10/2026):** PO aprovou os dois escopos do P7 — `all_products` (análise interna/conciliação) e `mp_pi_pa` (entrega DRE) como `report_scope` explícito, conforme a recomendação aqui registrada; mecanismo técnico do recorte oficial permanece E2 (§9.1).

Documentação concluída ≠ integração pronta: cada contrato avança sob o gate vigente (doc 93), com testes de paridade contra artefatos homologados e aceite funcional (G6 = 0/15 hoje).

---

## 17. Condições de reabertura do inventário

Reabrir a consolidação **somente** quando: (a) nova revisão do processo no TÉO (revisões monitoradas — última 2026-10-05); (b) novo relatório/artefato incorporado à rotina; (c) alteração de regra homologada (ex.: tolerância na paridade); (d) evidência contraditória a uma conclusão `PROVEN` aqui (ex.: fonte `DLP06R01`/`matr460.prx` localizada, resposta E1–E12 de owners); (e) mudança formal de owner/responsável; (f) decisão PO que altere DEC-01..DEC-11. Reabrir por preferência ou para "reconstruir" o AS-IS é proibido — o objetivo desta base é eliminar redescobertas.

---

## 18. Referências bidirecionais

- **AS-IS e evidências:** TÉO PROC-0072 (43 docs — [doc 19](./19-rastreabilidade-teo.md)); [doc 117](./117-analysis-001-inventario-processo-real-joyce.md) (inventário Joyce); [doc 83](./83-ciclo2-crosswalk-evidencias-r01-r15.md) (crosswalk R01–R15); [doc 84](./84-ciclo2-matriz-paridade-monetaria.md) (paridade); [doc 80](./80-ciclo2-registro-vivo-investigacao-devin.md) (rodadas); [doc 57](./57-ciclo1-matriz-verificacao-video.md)/[46](./46-ciclo1-investigacao-fontes.md)/[47](./47-t01-report-column-audit-tracker-v1.md).
- **Regras:** [doc 85](./85-ciclo2-catalogo-regras-negocio-r01-r15.md) (BR-Rxx-NNN); [doc 15.1](./15.1-p3-criterios-paridade-monetaria.md); TÉO 06/06.1/06.2.
- **Decisões/contratos TARGET:** TÉO 31/31.1–31.19/33/34; docs [09](./09-p2-checklist-e-documentos.md), [10](./10-p3-estoque-cutoff-e-conciliacao.md), [11](./11-p4-classificacoes-e-pendencias.md), [12](./12-p5-pacote-finalizacao-e-envio.md), [13](./13-p6-administracao-e-configuracao.md), [37](./37-p5-submissao-e-revisao-no-portal.md), [48](./48-r01-r02-design-baixas-financeiras.md)/[49](./49-r03-p7-design-estoque-inventario.md), [91](./91-ciclo3-contabilidade-acesso-documentos-historicos-gate.md), [112](./112-design-visual-fechamento-mensal-wireframes.md), [113](./113-plano-canonico-fluxo-fechamento-controladoria-dre-vigencia-documental.md), [114](./114-contrato-proposto-document-config-dr1-dr2-gate013.md), [115](./115-dre-access-019-documentos-recebidos-gate-91-implementacao.md), [23](./23-ledger-rq-ac-testes.md), [90](./90-ciclo3-crosswalk-end-to-end-proc0072-teo-rq-ac-portal.md), [93](./93-roadmap-executivo-central-fechamento-end-to-end-checkpoints.md).
- **CLARA:** [doc 94](./94-clara-especialista-mcp-controladoria-financas.md), [doc 111](./111-clara-chatgpt-smoke-autenticado-retomada-central-2026-10-26.md).
- **Plano do ciclo de análise:** [doc 116](./116-ciclo-inteligencia-fechamento-analysis-001-a-005.md); ledger [23](./23-ledger-rq-ac-testes.md); [README](./README.md).

**Versão:** 1.3 — §9.1 referencia doc 119 (contratos definitivos P7 + readiness de implementação) — P7-IMPLEMENTATION-READINESS-005, 2026-10-28. Anterior: 1.2 — reuso do filtro canônico `B1_TIPO` + veredito de equivalência — P7-SCOPE-CONTRACT-004. Próxima revisão somente sob as condições do §17.
