# Crosswalk integral R01–R15 — Consolidação de evidências do fechamento set/2026

**Documento:** `83-ciclo2-crosswalk-evidencias-r01-r15.md`
**Execução:** CF-C2-FULL-EVIDENCE-RECONCILIATION-001 · 2026-10-23 · Devin
**Origem das evidências:** pasta `fechamento` fornecida pelo PO (20 arquivos: 1 vídeo, 6 PDFs, 10 XLSB, 3 XLSX — metadados sanitizados aqui), documentos 03/46/47/55–57/71–82, acervo `docs/13-fontes-totvs-protheus/`, Rodadas 1–13 (doc 80).
**Escopo:** PROC-0072 · competência 09/2026 · empresa DELPI (Matriz + Filial) · ambiente Protheus `02.9.0004` (Estoque/Custos) / `02.9.0006` (Financeiro) · usuário observado JOICI.
**Restrições cumpridas:** somente leitura/local; nenhum SQL novo necessário para as promoções documentadas aqui; nenhum dado sensível versionado (apenas metadados, totais e estruturas).

---

## §1 — Inventário da pasta de evidências

| Arquivo | Formato | Identidade observada | Dt.Ref | Vínculo |
|---|---|---|---|---|
| Vídeo reunião (54:44, 1920×1080) | mp4 | gravação do acompanhamento do fechamento 30/09/2026 14:31 | 30/09/2026 | R03,R10,R11,R12,R15 |
| `A Receber.xlsb` | xlsb | "Posicao dos Titulos a Receber" — 574 linhas, cols prefixo/título/tipo/natureza/emissão/vencto/vencto real/bco/valor original/vencidos/a vencer | 30/09/2026 15:20 | R02* (posição, não baixa) |
| `A pagar.xlsb` | xlsb | "Posicao dos Titulos a Pagar" — 663 linhas, idem + dias atraso | 30/09/2026 15:28 | R01* (posição, não baixa) |
| `Recebidos.xlsb` | xlsb | "Relacao de Baixas" — 686 linhas (Prf, Numero, Prc, TP, Cli/For, Natureza, Vencto, Historico, Dt Baixa, valores) | 30/09/2026 15:26 | R02 |
| `pagos 09 26.xlsb` | xlsb | "Relacao de Baixas" — 974 linhas, mesmo layout | 30/09/2026 15:22 | R01 |
| `Pagos por dt.pdf` | pdf 33p | `SIGA/DLP06R01.prt/v.12` "Relacao dos Titulos Pagos em REAL por data de pagamento" | 30/09/2026 | R01 |
| `Pagos por nat.pdf` | pdf 35p | `SIGA/nat.prt/v.12` "Relacao dos Titulos Pagos em REAL por Natureza" | 30/09/2026 | R01 |
| `Recebidos.pdf` | pdf 36p | `SIGA/DLP06R01.prt/v.12` "Relacao dos Titulos Recebidos em REAL por data de pagamento" | 30/09/2026 | R02 |
| `Estoque.pdf` | pdf 1p | "REGISTRO DE INVENTÁRIO" completo — FOLHA 000.101, TOTAL GERAL 3.946.431,87 | 30/09/2026 | R03 |
| `Resumo Estoque.pdf` | pdf 1p | "REGISTRO DE INVENTÁRIO" escopo MP/PA/PI — FOLHA 000.074, TOTAL GERAL 2.976.967,56 | 30/09/2026 | R03 |
| `Entradas e saidas.pdf` | pdf 1p | `SIGA/MATR320.prt/v.12` "Resumo das Entradas e Saidas EM R$ — 01/09/2026 a 30/09/2026" | 01/10/2026 | R05 |
| `CC matriz.xlsb` | xlsb | export EDAPP da tabela **SD1** (sheet `SCAGQGA0.XML`): Filial, Item NF, Produto, Tipo, UM, Qtd, Tipo Entrada, Tp.Oper, Vlr.Unit/Tot, **C Custo**, C Contab, IPI/ICMS | — | R10 |
| `NF a desconsiderar.xlsb` | xlsb | export EDAPP da tabela **SD2** (sheet `Planilha2`): Filial, Item, Produto, Qtd, Vlr, IPI, ICMS, Tipo Saida 594, CF 5101 | — | R11 |
| `Fat x MOD.xlsb` | xlsb | 2 abas (1-Fl01: 2.461 linhas; 2-Fl02: 2.019): PA → Seq Comp → Cod MOD → Qtd Fat → **Horas** → Custo Unit → Custo Total | — | R09 |
| `Material em processo.xlsb` | xlsb | "Saldo em Processo (Anal" — **57.359 linhas**: CODIGO, DESCRICAO, UM, LOCAL, **ORDEM PRODUCAO**, TIPO RE/DE, QTDE EM PROCESSO, VALOR EM PROCESSO | 01/10/2026 16:15 | R08 (e OP → R04 adjacente) |
| `Invent.xlsb` | xlsb | Kardex de docs "INVENT" — 50 linhas: DATA, TES (999/499), C.F (RE0/DE0), entradas/saídas, saldo, CM do movimento | — | R07 |
| `cpv 09 26 matriz.xlsb` | xlsb | "Kardex Fisico-Financeiro" por produto — 14.382 linhas (produto + movimentos + saldo + CM) | 01/10/2026 16:58 | R06 |
| `Analise.xlsx` | xlsx | "Relatorio" — 1.995 linhas: Filial, Produto, Tipo, Grupo, Armazém, **CM inicial × CM final R$/US$/UFIR/MARCO/IENE + Variação%** | — | R04/R12 adjacente (variação custo médio, doc 58) |
| `Arquivos de envio - contabil.xlsx` | xlsx | checklist "Eletronico"/"Fisico" do envio à Contabilidade (Extratos, XP, BB, Aplicações, notas, inventário...) | — | R13 + fluxo de entrega |
| `Contabilidade liberações.xlsx` | xlsx | **roster oficial de rotinas liberadas** por usuário (Fiscal Jhenifer / Contabil Ravana) | — | G3 de múltiplos itens |

\* `A Receber.xlsb`/`A pagar.xlsb` são **posição de títulos em aberto** (FINR130/FINR150), não baixas — distinguir dos relatórios de baixas (R01/R02). O próprio doc 47 §7 alertava para não misturar.

## §2 — Roster oficial de rotinas (`Contabilidade liberações.xlsx`)

| Perfil | Rotina | Módulo | Finalidade declarada |
|---|---|---|---|
| Fiscal | MATA080 / MATA540 / DEL002 / COMXCOL / MATA103 | 2/4 | TES, exceção fiscal, texto legal, importador XML, doc. entrada |
| Fiscal | **EDAPP** | 4 | consulta genérica — "notas fiscais à desconsiderar do faturamento", tabelas de entrada (Excel) |
| Fiscal | MATA010 / MATA019 | 4 | produto, indicadores/alíquotas |
| Fiscal | **MATR910** | 4 | "Kardex diario — CPV e Inventarios" |
| Fiscal | SPEDNFE / SPEDFISCAL | 5/9 | NFe XML; **SPED Bloco H e K** |
| Fiscal | MATA900 / FISA140 / FISA170 | 9/34 | acertos fiscais, CBNEF, config. tributos |
| Contábil | **EDAPP** | 4 | "Faturamento e CC" |
| Contábil | **MATR460** | 4 | "Estoque P7" |
| Contábil | **MATR989** | 4 | "Material em processo" |
| Contábil | **DLP204** | 4 | "Fat x Mod — Custo MO" |
| Contábil | FINR150 / FINR130 | 6 | pendência a pagar / a receber |
| Contábil | **FINR190** | 6 | "Relação de baixas DLP — pagos e recebidos" |

**Resoluções diretas do acervo:** `DLP06R01.prt`/`nat.prt` = **layouts** do relatório de baixas (pago e recebido por data) — o mesmo `.prt` serve a rotinas distintas. Para **pagar**, produtor = **FINR190** ("Relação de Baixas DLP" no menu, vídeo 13:00 + roster), fonte `FINR190_DLP.PRX` no acervo cujo WHERE reproduz a população oficial (§17.B/C doc 80). Para **receber**, o WHERE do FINR190 **não** reproduz o artefato (§17.D): produtor = custom `DLP06R01`, fonte **ausente** do acervo (`BLOCKED`, E1).

## §3 — Timeline do vídeo (evidência observada diretamente)

Vídeo 54:44 · gravação 30/09/2026 14:31 · frames extraídos por detecção de cena + full-res nos pontos-chave (frames não versionados; timestamps registrados abaixo).

| Timecode | Tela observada | Evidência |
|---|---|---|
| 00:00–03:59 | SIGAEST home | ambiente 02.9.0004, sessão Delpi/Matriz |
| 04:00 | **"Recálculo do Custo de Reposição"** | tela de parâmetros visível: Utilizar Qual Moeda?=Nenhuma; Utilizar Taxa?=Diaria; Calcular os Custos Por?=Estrutura; Considerar Ult. Preco Compra?=Sim; Dt Final Ref Taxa?=30/09/2026; Tipo de produto até=MP; Considera Mão de Obra?=Ambos; Tempo Setup?=Som Tempo Propo |
| 09:00 | **"Contas a Pagar" (SIGAFIN)** | browse de títulos: Prefixo/Título/Parcela/Tipo/Natureza/Portador/Fornecedor/Emissão/Vencto/Vencto Real/Vlr.Título/DT Baixa — fonte operacional dos relatórios financeiros |
| 13:00 | menu Financeiro > Relatórios | itens visíveis: "Relação de Baixas", **"Relação de Baixas DLP"**, "Baixas Por Lote", "Resumo Financeiro" |
| 14:47–16:xx | **"Acompanha Custo → Novo fechamento de custo"** | wizard executado em produção: etapas `Predefinição de cálculo → Cálculo de custo → Análise e revisão → Fechamento`; etapa 2 a 100%: "Níveis validados / Arquivo de trabalho montado / Transferências entre filiais processadas / Análise das movimentações concluída"; botões Cancelar/Refazer cálculo/Próximo passo |
| 35:00 | **"Registro de Inventário Modelo P7"** (preview pág. 91/91) | RESUMO: EM ESTOQUE por tipo (EMBALAGEM 10.354,86; GASTOS 1,35; INSUMO 266.321,46; CONSUMO 12.121,47; LIMPEZA 5.675,39; MP 3.087.025,94; SEGURANÇA 7.820,42; EXPEDIENTE? 2.190,07; PA 12.489,84; PI 24.524,60) TOTAL ~3.420.5xx + EM PROCESSO ~348.4xx → TOTAL GERAL **3.776.994,69** |
| 37:00 | "Registro de Inventário Modelo P7" (preview pág. 64/64) | segunda emissão no vídeo com TOTAL GERAL ~2.756.1xx — **reemissões com totais evoluindo** (correções iterativas durante o fechamento) |
| 39–45min | diálogo de erro + retorno SIGAEST | erro em rotina (não legível integralmente), continuidade do processo |
| 47:00 | **EDAPP "Consulta Genérica" → Excel** | sheet `SCAGPOU0.XML` com dump **SD1** — prova do mecanismo que gera `CC matriz.xlsb`/`NF a desconsiderar.xlsb` |
| 47–54:44 | Excel pivô/análise + encerramento | conferências em planilhas |

**Achado temporal relevante:** os PDFs finais (`Estoque.pdf` 3.946.431,87; `Resumo Estoque.pdf` 2.976.967,56) foram gerados às ~19:19–19:22 do mesmo dia (metadados), **depois** das emissões vistas no vídeo (15:06–15:08) — o P7 foi reemitido ao menos 4 vezes com totais distintos: **o fechamento é iterativo**; a última versão é a homologável. Isso fundamenta a exigência de `as_of`/versão nos indicadores (AC-E6).

## §4 — Matriz R01–R15

Legenda de status da linha: VALIDADO (gates demonstráveis G1–G4 suficientes) · PARCIAL (parte dos vínculos) · BLOQUEADO (evidência esgotada). **Após o rework de gates (doc 47 §11.1) e a consolidação de 15 (doc 80 §33):** R05 alcançou G1–G5 PASS (escopo completo reproduzido ao centavo + drift decomposto); G4 de R02 segue revertido (produtor custom sem fonte) e G6 de todos os itens exige aceite funcional.

### R01 — Baixas a pagar — **PARCIAL (forte)**

| Dimensão | Conteúdo |
|---|---|
| Evidência operacional | `Pagos por dt.pdf` (DLP06R01.prt, 33p), `Pagos por nat.pdf` (nat.prt, 35p), `pagos 09 26.xlsb` (974 linhas); menu "Relação de Baixas DLP" (vídeo 13:00); Contas a Pagar browse (09:00) |
| Rotina | **FINR190** ("Relação de baixas DLP", roster Contabilidade); layout DLP06R01.prt (+nat.prt); fonte `FINR190_DLP.PRX` no acervo (rodada 5) |
| Finalidade | relação de títulos pagos da competência p/ conferência e envio à Contabilidade |
| Entrada | período (Dt.Ref 30/09/2026), disposição por data ou natureza |
| Saída | Prf, Numero, Prc, TP, Cli/For, Nome+CNPJ, Natureza, Vencto, Historico, Dt Baixa, Valor Original, Jur/Multa, Correcao, Descontos, Abatim., Impostos, Valor Ac, Total Baixado, Bco, Dt Dig., Mot, Ori + subtotais por data/natureza |
| Origem física | SE2/FK2/FK5/SED/F7G (+SA2) conforme SQL inspecionado do FINR190_DLP (§17 doc 80) |
| Comparação | **paridade row-level completa (CF-C2-PARITY-001, doc 84):** 948/948 chaves; `Total Baixado`=`E5_VALOR` 0 div.; VO=`E2_VALOR` 942 + INV=`E5_VALOR` 5 + grupo NF 1 (100% explicado); resumos/componentes/filorig exatos; PDF = xlsb − log 387.629,64 (subconjunto do log = residual) |
| Temporalidade | evento = Dt Baixa; emissão 01/10/2026 15:22 |
| Gates | **G1 PASS · G2 PASS · G3 PASS · G4 PASS · G5 PASS · G6 PENDING** |
| Residual | identidade do subconjunto "log de inconsistências"; versão RPO; aceite (G6) — owner Controladoria |

### R02 — Baixas a receber — **PARCIAL**

`Recebidos.pdf` (DLP06R01.prt, 36p) + `Recebidos.xlsb` (657 linhas de dados); produtor = `DLP06R01` custom, **fonte ausente do acervo** (`BLOCKED`, owner TI/ERP — E1). **Paridade row-level completa (CF-C2-PARITY-001, doc 84):** 649 chaves SE5×SE1 idênticas + 8 movimentos `PA` sem título (`FINA750`) = 657; 8 linhas de decomposição `MT`/`JR`/`DC` excluídas pelo produtor (valores embutidos no `E5_VALOR` do `VL`); `TB`=`E5_VALOR` exato; `VO`=`E1_VALOR` 649/649 + provisão `'P'` espelhada (MATA121/FINA050) 8/8 — **Δ R$0,00** (rework: "residual de R$1,00" era erro de soma, doc 80 §30); resumos = mesma regra do pagar. Gates: **G1 PASS · G2 PASS · G3 PASS · G4 PENDING** (binding do relatório não provado — coluna→campo e filtros do `DLP06R01` desconhecidos) · **G5 PASS** · G6 PENDING.

### R03 — P7 / Bloco H — **PARCIAL (forte)**

| Dimensão | Conteúdo |
|---|---|
| Evidência operacional | vídeo 35:00/37:00 (duas emissões do "Registro de Inventário Modelo P7" em preview, MATRIZ, 30/09/2026); `Estoque.pdf` (completo) + `Resumo Estoque.pdf` (escopo MP/PA/PI); SPEDFISCAL no roster (Bloco H) |
| Rotina | **"Registro de Inventário Modelo P7"** observada; roster vincula "Estoque P7"→**MATR460** (a confirmar se "Modelo P7" = MATR460 padrão ou variante — residual E2 estreitado) |
| Finalidade | registro fiscal-contábil do estoque no fechamento; alimenta SPED Bloco H |
| Entrada | data estoque (30/09/2026), empresa/filial, escopo de tipos (observados: completo × MP/PA/PI), armazém |
| Saída | CLASSIFICAÇÃO FISCAL, DISCRIMINAÇÃO, UNID, QUANTIDADE, UNITÁRIO, PARCIAL, TOTAL + RESUMO por tipo EM ESTOQUE/EM PROCESSO + TOTAL GERAL |
| Origem física | **Binding de totalização PROVEN (rodada 15, doc 80 §33.D):** EM ESTOQUE = saldo físico excluindo armazém de processo (`MV_LOCPROC='99'`) no `as_of` da emissão — fonte compatível SB9/`VINI1`; EM PROCESSO = MATR989 (medida por OP). Estrutural (doc 80 §31.G): hook `A460UNIT` ajusta `MP7GDA`; workfiles `MP7_*` com `TIPOMOV`∈{`aSalAtu`,`QtCus`,`aDadosCF9`} — produtor/`matr460.prx` `TO_INVENTORY` |
| Comparação | totais divergentes entre emissões (3.776.994,69 → ~2.756.1xx → 3.946.431,87 / 2.976.967,56): fechamento iterativo. **Paridade (doc 84 §3):** EM PROCESSO = `Material em processo.xlsb` exato (355.240,51); PA/PI EM ESTOQUE = MATR320 exato; **EM ESTOQUE total exato** — `SA_emissão − loc99_emissão = 3.591.191,36`. **Rodadas 17-18 (doc 80 §35/§36):** emissão resumida (folha 74) = **mesma data-base/custo** do completo (PA/PI bit a bit) + escopo MP/PA/PI + divergência só em MP — hipótese `QTNP@emissão>0` explica 99,987 % estoque (Δ76,43) e ~97,5 % processo (Δ1.942,62) — **não é regra oficial**; `MTR460` (SX1) catalogado — sem parâmetro de tipo |
| Gates | **G1 PASS · G2 PASS · G3 PASS · G4 PENDING · G5 PENDING · G6 PENDING** (binding de totalização provado; parametrização por emissão e produtor pendentes) |
| Residual | pacote E2 conclusivo (doc 82 §2.1): parâmetros da emissão resumida (E2.1) + relatório integral da folha 74 (E2.2 — fecha Δ76,43/Δ1.942,62) + produtor/RPO implantado (E2.3 — semântica poder3 + escopo de tipos fora do SX1); versão homologada |

### R04 — Consumo por OP — **BLOQUEADO (sem artefato novo)**

Nenhum relatório de consumo por OP na pasta. `Material em processo.xlsb` traz ORDEM PRODUCAO mas é R08; `matr860` permanece **candidato** (fonte presente, papel decodificado na rodada 7 — MOD via SD3 RE1/TM999 — mas não é o relatório de consumo por OP observado em uso). Gates: todos **PENDING**. Próxima ação: confirmar com Controladoria qual artefato/rosto o relatório tem (roster não lista).

### R05 — Entradas e Saídas / valor estoque — **PARCIAL (rotina+artefato+fonte identificados)**

`Entradas e saidas.pdf` = **`MATR320.prt`** — "Resumo das Entradas e Saidas EM R$", período 01/09–30/09/2026, MATRIZ; colunas por tipo (Tip): Saldo Inicial, Compras, Movimentações Internas, Requisições p/ Produção, Transferências, Produção, Vendas, Transf. p/ Processo, Devoluções, Poder de Terceiros, Saldo Atual + Total Geral. **Fonte localizado:** `matr320.prx` (padrão TOTVS, execução via SP `MAT056`; variante Delpi `Dmatr320.prx`/`DLPR320` zera poder3 e não foi a usada). **Reconciliação de colunas (doc 84 §4.2-4.4, doc 80 §31+§33):** **escopo completo reproduzido — 10 tipos × 13 colunas, 120/120 colunas de fluxo exatas ao centavo** no estado de emissão (inclui retificação retroativa `<NF-RETIF-A>` e reversão `TTAT_COLD` com corte por timestamp de emissão); MovInt residual 0,48 eliminado (artefato de sobre-reversão); divergência MP SA +8.631,731 **decomposta ao centavo por produto** (6 produtos revalorização CM pós-emissão — Δ 0,000, doc 80 §34.C); **130/130 células oficiais Δ = 0,000** no `as_of` da emissão. Gates: **G1–G3 PASS · G4 PASS · G5 PASS · G6 PENDING** (aceite funcional).

### R06 — CPV / Kardex 01 — **RECONCILIADO**

`cpv 09 26 matriz.xlsb` = "Kardex Fisico-Financeiro" por produto (14.382 linhas = 1.544 blocos + **9.357 movimentos** + layout). **Reconstrução física completa (rodada 19, doc 80 §37, doc 85 §6):** produtor MATR910 com fonte `matr910_dlp.prx` (`SOURCE_AVAILABLE`); UNION **SD1 (`D1_DTDIGIT`) + SD2 (`D2_EMISSAO`) + SD3 (`D3_EMISSAO`)**, `F4_ESTOQUE='S'`, `D3_ESTORNO<>'S'`, `D*_ORIGLAN<>'LF'`, loc 01; ordem data+`D3_NUMSEQ` (1.971/1.971); REF decodificado (F-/P-/OP/CC); custos `as_of` emissão (**100%** — 7.376 `CUR` + 1.981 `TTAT_OLD`; devoluções `TIPONF='D'` cruzam coluna com sinal −, `zMTR910Dev`/`MV_LISTDEV` — errata r20 doc 80 §38); cadeia de saldo `B9`@0831 → saldo impresso (1.544/1.544). População = produtos com movimento (MOD*/MO fora; SB9 sem movimento fora). Saídas agregadas **≠ CPV** (semântica composta — `AS-IS`). Residual: versão RPO + parâmetros efetivos (E7). Gates: **G1–G5 PASS · G6 PENDING** (aceite funcional).

### R07 — Inventários / Kardex 99 — **RECONCILIADO**

`Invent.xlsb` = mesmo kardex filtrado a `D3_DOC='INVENT'` (TES **999/RE0** saída, **499/DE0** entrada), filial 02 loc 01+99. **45/45 linhas vinculadas ao SD3** (35 diretas + 10 via `TTAT_OLD` de custo); totais oficiais reconciliados (E 2.348,108/R$185.103 · S 30.808,206 · líquido −28.460,098). Gates: **G1–G5 PASS · G6 PENDING**.

### R08 — Material em Processo / H02 — **PARCIAL**

`Material em processo.xlsb` = "Saldo em Processo" (**57.359 linhas**, Dt.Ref 01/10/2026 16:15): produto, UM, LOCAL (armazém 99 etc.), **ORDEM PRODUCAO**, TIPO RE/DE (RE2...), QTDE e VALOR EM PROCESSO. Roster: **MATR989**. Resolve a nota do doc 47 §3 (proxy SC2 "adjacente não equivalente"): artefato correto agora em mãos — binding físico pendente. Gates: **G1–G3 PASS · G4 PENDING · G5/G6 PENDING**.

### R09 — Faturamento × MOD — **PARCIAL**

`Fat x MOD.xlsb` (abas 1-Fl01/2-Fl02): explosão PA→componentes MOD: PA, Seq Comp, Cod Produto (MOD###), Descrição, Qtd Fat, UM=HR, Quantidade (horas componente), Custo Unitario (ex.: MOD393 = 70,81), Custo Total, Custo Produto, **Horas**. Roster: **DLP204** "Fat x Mod — Custo MO". Cruzamento com doc 80: o `Custo Unitario` (70,81 MOD393) confirma uso de rate MOD por produto/filial (SBZ010.BZ_CUSTD, PROVEN §22–§25). Gates: **G1–G3 PASS · G4 PENDING** (vínculo DLP204↔view/SGZ/estruturas) · G5/G6 PENDING.

### R10 — Notas por Centro de Custo — **PARCIAL**

`CC matriz.xlsb` = export direto **SD1** via EDAPP (sheet `SCAGQGA0.XML`; vídeo 47:00 mostra a mesma operação com `SCAGPOU0.XML`): Filial, Item NF, Produto, Tipo, UM, Qtd, Tipo Entrada, Tp.Oper, Vlr.Unit/Tot, **C Custo**, C Contab, IPI, ICMS. Roster: **EDAPP** "Faturamento e CC" + "tabelas entrada de notas fiscais (excel)". Gates: **G1–G3 PASS · G4 PASS** (a própria exportação é a tabela física SD1) · G5/G6 PENDING.

### R11 — NF venda / desconsiderar — **PARCIAL**

`NF a desconsiderar.xlsb` = export direto **SD2** via EDAPP: Filial, Item, Produto, Qtd, Vlr, IPI, ICMS, Tipo Saida (594), Cod. Fiscal (5101). Roster: EDAPP "notas fiscais à desconsiderar do faturamento". Gates: **G1–G3 PASS · G4 PASS (SD2) · G5/G6 PENDING**.

### R12 — Acompanha Custos / Reposição / Refaz Saldos — **PARCIAL**

Vídeo 04:00 (**Recálculo do Custo de Reposição**, parâmetros íntegros observados — lista em §3) e 14:47–16:xx (**Acompanha Custo → Novo fechamento de custo**, execução real com checklist de etapas). `DEL100.PRW` decodificado (rodada 10/11) = Refaz Saldos (reconstrução SD3/SD1/SD2 → comparação SB9; query vigente 3.058/421/242 sanitizada no doc 80 §24.E). Gates: **G1–G3 PASS · G4 PENDING · G5/G6 PENDING**.

### R13 — Extratos e aplicações — **BLOQUEADO (externalidade confirmada)**

`Arquivos de envio` lista Extratos/XP/Banco do Brasil/Aplicações BB como entregáveis físicos/eletrônicos — fonte **externa** confirmada por checklist, sem artefato de dados na pasta. Gates: **G1 PASS · G2–G6 PENDING**. Contrato de coleta = caminho indicado pelo doc 47 (fonte externa não exige tabela SQL).

### R14 — Importação / SWIFT / câmbio / ACSI — **BLOQUEADO**

Nenhuma evidência nova na pasta. Gates: todos PENDING.

### R15 — Cutoff / sacramentação / SB9 — **PARCIAL**

Vídeo mostra a execução do **fechamento de custo** (wizard "Novo fechamento de custo", 14:47, JOICI, Matriz) — `EXECUTION_OBSERVED` do processo de fechamento. SB9 = snapshot mensal de SB2 (PROVEN, §21). Ligação wizard→gravação SB9 **não byte-provada**: timestamps de inserção B9 (f02 02/10, f01 21/10) não coincidem com a execução observada 30/09 14:47 — hipóteses: reexecução posterior ("Refazer cálculo"), etapa distinta do wizard, ou rotina separada. Gates: **G1 PASS · G2 PASS · G3 PENDING · G4 PENDING · G5/G6 PENDING**.

## §5 — Efeito nas pendências (doc 82)

| Pedido | Estado após esta rodada |
|---|---|
| E1 (DLP06R01) | **Parcialmente respondido (rework 23/10 + paridade):** `DLP06R01.prt`/`nat.prt` = layouts compartilhados. **Pagar:** produtor = FINR190, fonte+WHERE+paridade row-level provados — residual = versão implantada (RPO) + identidade do subconjunto do log de inconsistências. **Receber:** paridade row-level do artefato provada (G5), mas produtor `DLP06R01` custom **segue sem fonte no acervo** — pendente o fonte para G4 (owner TI/ERP). |
| E2 (P7/MATR460) | **Substancialmente respondido (rodada 15):** artefato oficial + rotina observada + roster MATR460 + **binding de totalização provado** (EM ESTOQUE = saldo ex-`MV_LOCPROC` no `as_of`; EM PROCESSO = MATR989 — doc 80 §33.D). Residual: parâmetros efetivos por emissão (filtro tipos/armazém/`as_of`), fonte `matr460.prx`/variante, binding por produto/armazém, export p/ paridade. |
| E3 (DDL views) | mantido — DBA |
| E4 (jobs/SPs) | mantido — DBA |
| E5 (rotina SB9) | **estreitado:** execução do fechamento observada (wizard, 14:47); falta provar qual passo grava SB9 e por que B9_I_N_S_D_T_ diverge (02/10 e 21/10). |
| E6 | decidido (opção C — doc 81); pendências E6-D1..D6 conforme doc 82. |

## §6 — Divergências e notas de rigor

- `A Receber.xlsb`/`A pagar.xlsb` são **posições em aberto** (FINR130/FINR150) — não contam como baixas (R01/R02).
- `Analise.xlsx` = análise de variação de custo médio multimoeda (doc 58 histórico) — artefato resolvido; rotina produtora ainda `TO_INVENTORY`.
- Totais do P7 variaram entre emissões no mesmo dia → "valor homologado" exige versão/`as_of` (coerente com AC-E6-02/08).
- `SB9` deixou de ser apenas candidato: o binding de **totalização** do P7 foi provado (EM ESTOQUE = saldo ex-99 no `as_of` da emissão — doc 80 §33.D); o binding do **produtor** (`matr460.prx`/workfile) e a parametrização por emissão seguem `TO_INVENTORY`.
- Counts de linha XLSB são do export bruto (incluem cabeçalhos/subtotais); não equivalem diretamente às contagens de baixas da reconstrução SQL.
- Vídeo fornece telas/params/rotinas observadas; **não** prova código implantado (fonte acervo ≠ RPO) — classificação `CODE_DEPLOYED` continua dependendo do owner para itens sem fonte canônica.

## §7 — Resultado por item

| Item | Status | Rotina vinculada | Gates novos |
|---|---|---|---|
| R01 Baixas a pagar | PARCIAL | FINR190 + DLP06R01.prt/nat.prt | G2,G3,G4,**G5** (paridade row-level — doc 84) |
| R02 Baixas a receber | PARCIAL | `DLP06R01` custom (FINR190 descartado pelo WHERE §17.D) | G2,G3,**G5** (paridade row-level do artefato — doc 84; G4 segue PENDING) |
| R03 P7 / Bloco H | PARCIAL | "Registro de Inventário Modelo P7" (MATR460?) | G1,G2,G3 (binding de totalização provado rodada 15 — doc 80 §33.D; G4/G5 pendentes por parametrização) |
| R04 Consumo por OP | BLOQUEADO | — | — |
| R05 Entradas e Saídas | PARCIAL | MATR320 | G1,G2,G3,**G4**,**G5** (escopo completo reproduzido ao centavo + drift decomposto — doc 80 §33, doc 84 §4.4) |
| R06 CPV / Kardex 01 | RECONCILIADO | MATR910 (`matr910_dlp.prx`) | G1,G2,G3,**G4**,**G5** (UNION SD1/SD2/SD3 linha-a-linha — doc 80 §37, doc 85 §6; RPO/params → E7) |
| R07 Inventários | RECONCILIADO | MATR910 | G1,G2,G3,**G4**,**G5** (INVENT 45/45 — doc 80 §37.D, doc 85 §7) |
| R08 Material em Processo | PARCIAL | MATR989 | G1,G2,G3 |
| R09 Fat × MOD | PARCIAL | DLP204 | G1,G2,G3 |
| R10 Notas por CC | PARCIAL | EDAPP (SD1) | G1,G2,G3,G4 |
| R11 NF desconsiderar | PARCIAL | EDAPP (SD2) | G1,G2,G3,G4 |
| R12 Acompanha/Rep/Refaz | PARCIAL | Acompanha Custo wizard, Recálculo Reposição, DEL100 | G1,G2,G3 |
| R13 Extratos/aplicações | BLOQUEADO | externa | G1 |
| R14 Importação | BLOQUEADO | — | — |
| R15 Cutoff/SB9 | PARCIAL | fechamento wizard (execução observada) | G1,G2 |

\* Revisão 23/10 (doc 47 §11.1): rótulo VALIDADO retirado — evidência de rotina+artefato cobre G1–G3; G4/G5/G6 permanecem abertos para todos os itens.

**Coleta:** 39/60 = **65,0%** · **Auditoria:** 41/90 = **45,6%** · **Concluídos:** 0/15. (pós-rework doc 47 §11.1 + paridade §11.2: G4 de R02 revertido — produtor receber = `DLP06R01` custom sem fonte; **G5 de R01 e R02 promovidos** — paridade row-level, doc 84)

**Catálogo de regras de negócio (complemento, 23/10):** todas as regras necessárias para reproduzir os resultados oficiais estão consolidadas em **doc 85** (`BR-Rxx-NNN`, matriz de handoff e matriz de testes) — incluindo as regras de VO dual do receber (errata do residual R$1,00 em doc 80 §30) e a classificação PROVEN/AS-IS/TO_INVENTORY/TARGET/PENDING por regra.
