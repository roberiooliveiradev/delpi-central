# Handoff Ciclo 2 — Pacote de Evidências para Owners

**Documento:** `82-ciclo2-handoff-pacote-evidencias-owners.md` (renumerado de `81-` em 2026-10-23 para resolver colisão com o documento de decisão)
**Origem:** `80-ciclo2-registro-vivo-investigacao-devin.md` §25 (Rodada 13, `4577c8c5e4`)
**Escopo:** PROC-0072 — estoque histórico, MOD, baixas financeiras, fechamento SB9
**Estado:** E6 `APPROVED / PRODUCT_DIRECTION_ONLY` (opção C — `81-decisao-e6-historico-monetario-mod-opcao-c.md`, `e68ae2d63129`) · `IMPLEMENTATION_AUTHORIZED = NO` · `NO_GATE_CHANGE` (Doc 47)

> Nenhum item deste pacote pede permissões amplas ou acesso privilegiado genérico.
> Cada solicitação pede **a evidência específica** e, quando possível, **extrato/resultado sanitizado** no lugar do acesso.

---

## §1 — Protocolo de recebimento de respostas

Para cada resposta recebida, classificar **separadamente** (uma resposta pode cobrir vários planos, mas nenhum plano deve ser presumido):

| Plano | Pergunta que responde | Aceite |
|---|---|---|
| `SOURCE_AVAILABLE` | a fonte/código existe no acervo ou foi entregue? | arquivo/fonte/DDL recebido e legível |
| `CODE_DEPLOYED` | o código recebido é o efetivamente implantado no RPO/DB de produção? | versão/RPO/data de compilação ou confirmação do owner |
| `EXECUTION_OBSERVED` | há evidência de execução em produção (log, schedule, timestamp)? | artefato de execução datado |
| `FUNCTIONAL_ACCEPTANCE` | o resultado foi homologado pelo negócio? | aceite do owner funcional (Controladoria) |

Referência vigente das reconstruções DEL100: **3.058 chaves / 421 valor / 242 quantidade** (query sanitizada no doc 80 §24.E). Contagens anteriores (724/672 e derivadas) estão `STALE_EVIDENCE`; a trilha preserva `EXECUTION_DRIFT` — não reutilizar os números antigos.

---

## §2 — Solicitações por responsável

### 2.1 — Owner TI/ERP (fontes e execução Protheus)

#### E1 — Produtores das baixas — **parcialmente respondido em 23/10; receber segue pendente**

| Campo | Conteúdo |
|---|---|
| Evidência atual | `Pagos por dt.pdf`/`Recebidos.pdf` trazem `SIGA/DLP06R01.prt/v.12` — **layout compartilhado, não produtor**. **Pagar:** produtor = FINR190 provado — fonte `FINR190_DLP.PRX` (commit `0df96daafe`) com TRCell→`E5_*` e WHERE que reproduz população oficial 948+motivo 5/5 (doc 80 §17.B/C; G4 PASS doc 47 §11.1). **Receber:** WHERE do FINR190 gera 649/690 ≠ 657 oficial (§17.D, PROVEN) — produtor = `DLP06R01` **custom, fonte ausente do acervo**; `DLP06P01/F01/F02/F03` verificados = utilitários não relacionados |
| Lacuna objetiva | (a) **fonte do `DLP06R01` custom** (receber) — nome da rotina, mapeamento coluna→campo e filtros (incl. regra de inclusão/exclusão dos movimentos sem título e do VO `FINA750`); (b) confirmar versão RPO do `FINR190_DLP.PRX`; (c) identidade do subconjunto do "log de inconsistências" de ambos os relatórios; ~~paridade monetária integral~~ **respondida 23/10 — G5 PASS ambos (doc 84)** |
| Fonte esperada | fonte AdvPL/PRX do `DLP06R01` (ou nome da rotina efetiva do relatório de recebidos) + confirmação de compilação no RPO + o arquivo de log de inconsistências emitido junto ao relatório |
| Impacto PROC-0072 | fecha G4 de R02 e a trilha receber; sem o fonte, G4 segue PENDING (paridade do artefato já provada em G5) |
| Critério de aceite | `SOURCE_AVAILABLE` + `CODE_DEPLOYED`; idealmente `EXECUTION_OBSERVED` |

#### E2 — Produtor e parâmetros do P7 / MATR460 — **solicitação conclusiva (rodada 18)**

| Campo | Conteúdo |
|---|---|
| Evidência atual | **Resolvido em 23/10:** rotina **"Registro de Inventário Modelo P7"** observada em preview no vídeo (35:00/37:00, MATRIZ, 30/09/2026); artefatos `Estoque.pdf` (completo, TOTAL 3.946.431,87, folha 101) e `Resumo Estoque.pdf` (escopo MP/PA/PI, 2.976.967,56, folha 74 — **emissão distinta, mesma data-base 30/09**); roster vincula "Estoque P7"→**MATR460**; SPEDFISCAL gera Bloco H. **Rodada 15 (doc 80 §33.D):** binding de totalização **provado** — `EM ESTOQUE` = saldo físico ex-`MV_LOCPROC='99'` no `as_of` da emissão e `EM PROCESSO` = MATR989. **Rodada 17 (doc 80 §35):** grupo SX1 **`MTR460` (25 perguntas) catalogado**; resumo = mesmo estado de custo (PA/PI bit a bit) + **escopo MP/PA/PI + divergência exclusiva em MP**; hipótese `QTNP@emissão` explica 99,987 % do estoque (Δ76,43) e ~97,5 % do processo (Δ+1.942,62) — **não é regra oficial** (doc 80 §36, doc 85 BR-R03-007) |
| Lacuna objetiva | exatamente três evidências abaixo (E2.1/E2.2/E2.3) |
| Impacto PROC-0072 | é a base do gate R03 e da distinção "consulta operacional × relatório oficial" |

**E2.1 — Parâmetros da emissão resumida**

Solicitar os parâmetros **efetivamente utilizados** para gerar
`Resumo Estoque.pdf` (folha 74, data-base 30/09/2026, filial 01),
especialmente:

- `Saldo em Poder 3º ?` (Sim/Não/De Terceiros/Em Terceiros);
- `Saldo em Processo ?`; armazém inicial/final; produto
  inicial/final; data de fechamento; `Lista Custo ?`;
- demais parâmetros ou filtros **externos ao SX1** que alterem o
  escopo de tipos (o grupo `MTR460` não possui pergunta de tipo).

Aceitar print da parametrização, registro de execução (`mv_par`,
log de schedule) ou evidência equivalente, desde que haja **vínculo
demonstrável com a emissão**.

**E2.2 — Relatório completo correspondente à folha 74**

Solicitar o arquivo **integral** da emissão de `Resumo Estoque.pdf`
(todas as folhas, com linhas de produto, quantidades, custos,
armazéns e totalizações). Objetivo: identificar a população excluída
e reconciliar os resíduos monetários (R$ 76,43 em estoque e
R$ 1.942,62 em processo — doc 80 §35.D/§36). A evidência original
deve permanecer **sob custódia autorizada, fora do GitHub**.

**E2.3 — Produtor efetivamente implantado**

Solicitar a identificação da rotina MATR460 efetiva: variante ou
customização, fonte disponível e **versão compilada no RPO** usada
na emissão. A confirmação deve contemplar a semântica da pergunta
`Saldo em Poder 3º ?` e o mecanismo de seleção de tipos de produto.
Não confundir fonte existente no acervo com código implantado
(`CODE_DEPLOYED` exige comprovação de versão/compilação).

**Critérios de aceite por evidência**

| Evidência | `SOURCE_AVAILABLE` | `CODE_DEPLOYED` | `EXECUTION_OBSERVED` | `FUNCTIONAL_ACCEPTANCE` |
|---|---|---|---|---|
| E2.1 parâmetros | n/a | n/a | registro/print vinculado à emissão | Controladoria confirma parâmetros usados |
| E2.2 relatório integral | arquivo completo recebido | n/a | folhas/totais conferem com folha 74 | resíduos reconciliados ou explicados |
| E2.3 produtor | fonte identificada | versão RPO comprovada | rotina executada observada | semântica poder3 + escopo de tipos confirmada |

Uma evidência parcial **não encerra** E2. Encerramento de G4 exige
bindings físicos demonstrados; G5 exige paridade centavo da
população; G6 exige homologação funcional da Controladoria.

#### E5 — Rotina que grava SB9 (fechamento)

| Campo | Conteúdo |
|---|---|
| Evidência atual | **Execução observada em 23/10:** vídeo 14:47 mostra o wizard "Acompanha Custo → Novo fechamento de custo" (4 etapas) sendo executado em produção por JOICI/Matriz na competência 09/2026. Porém `B9_I_N_S_D_T_` marca inserções f02=02/10 17h e f01=21/10 19h — **divergentes da execução de 30/09 14:47** (reexecuções? etapa distinta?). Hooks `MA330OK`/`STP_DELPI_*` = capacidade de fonte (§22.D) |
| Lacuna objetiva | qual passo/rotina efetivamente grava as linhas SB9 e por que os timestamps de inserção divergem da execução observada; papel das SPs pós-fechamento |
| Fonte esperada | log de execução do fechamento (wizard/Event Viewer/appserver) da competência 09/2026 + identificação do passo que escreve SB9 |
| Impacto PROC-0072 | transforma "snapshot observado" em "produtor identificado" — destrava R12/R15 |
| Critério de aceite | `EXECUTION_OBSERVED` (log/schedule datado da escrita SB9) + `CODE_DEPLOYED` |

#### E7 — Versão implantada do MATR910 + parâmetros efetivos do kardex

| Campo | Conteúdo |
|---|---|
| Evidência atual | **Rodada 19:** fonte `matr910_dlp.prx` no acervo (`SOURCE_AVAILABLE`) e modelo físico `PROVEN` — UNION SD1/SD2/SD3, `F4_ESTOQUE='S'`, `D3_ESTORNO<>'S'`, `D*_ORIGLAN<>'LF'`, datas por tabela, ordem NUMSEQ, custos `as_of`. Paridade linha-a-linha: 9.357/9.357 (R06) e 45/45 (R07) — doc 80 §37, doc 85 §6/§7 |
| Lacuna objetiva | (a) confirmação de que a versão compilada no RPO de produção corresponde ao fonte `matr910_dlp.prx` disponível (`CODE_DEPLOYED`); (b) parâmetros efetivos das emissões de 01/10 — especialmente mv_par10 `Saldo a considerar` (Atual/Fechamento), mv_par09, mv_par22 poder3 e o armazém usado na emissão de `Invent.xlsb` (loc 01+99 observados) |
| Fonte esperada | identificação da build/RPO da rotina MATR910 + print/registro de parametrização vinculado às emissões (aceita evidência equivalente com vínculo demonstrável) |
| Impacto PROC-0072 | converte `SOURCE_AVAILABLE` em `CODE_DEPLOYED`; encerra o residual de parâmetros de R06/R07 (G4/G5 já PASS com base na reconstrução; E7 fecha a cadeia produtor→versão) |
| Critério de aceite | `CODE_DEPLOYED` (versão RPO comprovada) + `EXECUTION_OBSERVED` (parâmetros vinculados) |

#### E8 — Fonte e versão implantada do MATR989 (Material em Processo)

| Campo | Conteúdo |
|---|---|
| Evidência atual | **Rodada 22:** `Material em processo.xlsb` (aba `01-01 - Saldo em Processo (Ana`) reconciliado linha-a-linha — bloco com OP = 1.501 linhas `SD3010` `RE0/RE1/RE2/RE9` de OPs abertas na emissão (sem `PR0`, sem `C2_DATRF`); bloco sem OP = `SB9010`@20260930 loc99; total = EM PROCESSO P7 exato (doc 80 §41, doc 85 §8). `matr989.prx` **ausente do acervo** (`SOURCE_MISSING`, classe DLP06R01) |
| Lacuna objetiva | (a) fonte ADVPL/PRX do MATR989 (standard ou custom) — confirma a semântica intra-dia do corte de OP (Dt.Ref vs timestamp 16:15) e o neteo `DE*` dentro de par impresso (não exercido nesta competência); (b) versão compilada no RPO de produção (`CODE_DEPLOYED`); (c) parâmetros efetivos da emissão de 01/10 16:15 (variante analítica, Dt.Ref, armazém de processo, tipos de CF) |
| Fonte esperada | `matr989.prx`/customização + build/RPO da rotina + registro de parametrização vinculado à emissão (aceita evidência equivalente com vínculo demonstrável) |
| Impacto PROC-0072 | fecha a cadeia produtor→versão de R08 (G4/G5 já PASS por reconstrução física; E8 remove o residual de fonte e prova os dois pontos não exercidos empiricamente) |
| Critério de aceite | `SOURCE_AVAILABLE` (fonte) + `CODE_DEPLOYED` (RPO) + `EXECUTION_OBSERVED` (parâmetros vinculados) |

**Residual de confidencialidade (owner segurança):** os códigos reais dos
4 produtos divergentes SB9×MATR989 constaram no commit `f5c50f7c04` antes
da sanitização da rodada 23 (aliases `<PRODUTO-WIP-A..D>` — doc 80 §42.D);
histórico Git não reescrito por decisão do PO (doc 80 §32). Avaliar se a
exposição residual exige ação adicional.

---

#### E9 — Stored procedure e versão implantada do DLP204 (Faturamento × MOD)

| Campo | Conteúdo |
|---|---|
| Evidência atual | **Rodada 24:** `DLP204.prw` no acervo (`SOURCE_AVAILABLE`); modelo físico reconstruído a 99,4% — seleção SD2 TES `F4_DUPLIC='S'` (4.476/4.476 `Qtd Fat.`), expansão via `SHY010`/`SG2010` + `SH1010.H1_CCUSTO` (4.449/4.476), rate `SBZ010.BZ_CUSTD` `as_of` emissão (4.469/4.469 com SBZ) — doc 80 §43, doc 85 §9 |
| Lacuna objetiva | (a) fonte/RPO da `STP_DELPI_FORMA_PRECO_<empresa>` — ausente de todos os bancos acessíveis (legado 2019): contém a regra de seleção de OP por PA, a semântica do divisor `÷2` em itens de desdobramento e o cálculo de `CUSTOPROD`; (b) versão compilada do DLP204 no RPO (`CODE_DEPLOYED`); (c) parâmetros efetivos da emissão (par03..11 — artefato indica par11=Não); (d) 27 linhas com tempo não localizado e 7 MODs sem registro `SBZ` na filial (cadastro ausente ou exceção intencional); (e) tratamento de NF `D2_TIPO='D'` com TES duplic-S (ramo não exercido nesta competência) |
| Fonte esperada | DDL/source da stored procedure + identificação da build/RPO do DLP204 + registro de parametrização vinculado à emissão (aceita evidência equivalente com vínculo demonstrável) |
| Impacto PROC-0072 | fecha a cadeia produtor→versão de R09 e os únicos pontos que impedem G5 PASS (paridade linha integral); sem a SP, a semântica interna permanece `PRODUCER_INFERRED_BY_ARTIFACT` |
| Critério de aceite | `SOURCE_AVAILABLE` (SP) + `CODE_DEPLOYED` (RPO) + `EXECUTION_OBSERVED` (parâmetros vinculados) |

### 2.2 — Owner DBA (objetos de banco)

#### E3 — DDL das views criptografadas

| Campo | Conteúdo |
|---|---|
| Evidência atual | `vw_Apontamentos_Eficiencia` homologada empiricamente: `RESULTADO_MOD = (TEMPO_PREVISTO − TEMPO_REAL) × SBZ010.BZ_CUSTD` (85.904/85.904); `OBJECT_DEFINITION` retorna `NULL` (WITH ENCRYPTION) |
| Lacuna objetiva | definição interna: joins exatos, origem de `TEMPO_PREVISTO_HORAS`/`PRODUTO_MOD`, semântica de `STATUS_MOD`, e se há filtro temporal de rate |
| Fonte esperada | DDL das views `vw_Apontamentos_Eficiencia`, `VW_PROTHEUS_CUSTO_ANALITIC_01/_05`, `VW_PROTHEUS_CUSTO_SINT_01/_05`, `vw_fin_despesas_centro_custo` (script ou `sp_helptext`) |
| Impacto PROC-0072 | confirma bindings físicos (G4) e a proveniência do rate; elimina dependência de inferência |
| Critério de aceite | `SOURCE_AVAILABLE`; confrontado com o contrato empírico já provado |

#### E4 — Jobs SQL Agent e SPs DELPI

| Campo | Conteúdo |
|---|---|
| Evidência atual | `SELECT` em `msdb.dbo.sysjobs` **negado**; `STP_DELPI_OP_TERCEIRO_*`/`STP_PROTHEUS_DELPI_AJUSTA_OP` ausentes das bases acessíveis (`DELPI`, `DELPI_TST01`, `DELPI_TST_WS`, `IntranetDelpiDev`) |
| Lacuna objetiva | existência e agendamento de jobs de fechamento; código e localização real das SPs chamadas pelo `MA330OK` |
| Fonte esperada | extrato sanitizado de `msdb.dbo.sysjobs`/`sysjobschedules` (nomes, schedule, última execução) + `sp_helptext` das duas SPs na base onde residem |
| Impacto PROC-0072 | prova/elimina a hipótese do job mensal SB9 e revela o pós-processamento do fechamento |
| Critério de aceite | `EXECUTION_OBSERVED` (job + histórico) ou `SOURCE_AVAILABLE` (código SP) |

---

### 2.3 — Owner Controladoria (decisão de negócio)

#### E6 — Histórico monetário MOD — `APPROVED / PRODUCT_DIRECTION_ONLY` (opção C)

**Decisão registrada:** `E6_OPTION = C` (duas leituras: histórico homologado + recalculado corrente) em `81-decisao-e6-historico-monetario-mod-opcao-c.md` (`e68ae2d63129`, 2026-10-23). Classificação `APPROVED / PRODUCT_DIRECTION_ONLY` — **não é GO de implementação**: `IMPLEMENTATION_AUTHORIZED = NO`; não autoriza contratos, tabelas, migrations, APIs, UI, jobs, alteração na view ou runtime, e não promove gates do doc 47.

Contexto (doc 80 §23–§25): a view aplica o `BZ_CUSTD` **corrente retroativamente**; revalorização de out/2026 moveu ~8–9% do resultado de set/2026 no subconjunto alterado (f01 +489,72; f02 −2.465,53). Não existe congelamento: indicadores são recalculados ao vivo.

**O que se solicita agora à Controladoria (e owners indicados no doc 81):** não uma escolha A/B/C — já decidida — e sim:

| Item | Solicitação | Responsável candidato |
|---|---|---|
| E6-D1 | O que constitui o **valor homologado**: relatório oficial, pacote do fechamento ou outro artefato; grão e moeda | Controladoria |
| E6-D2 | Definição do cutoff, versões, correções, reaberturas e momento de congelamento | Controladoria + TI/ERP |
| E6-D3 | Fonte e confiabilidade de rate por competência, logs, DDL da view e artefatos históricos | TI/ERP + DBA |
| E6-D4 | Owner da persistência de evidências, retenção, contratos, DTOs e integrações | Product owner + arquitetura |
| E6-D5 | Tolerâncias monetárias, rótulos, comparação de variação e aceites por competência e filial | Controladoria |
| E6-D6 | Escopo e propriedade da competência, acesso às evidências e auditabilidade | Segurança/owner |

Mais:

1. **Homologação dos valores-base set/2026** (ótica corrente): f01 `+R$5.918,90` / f02 `−R$32.694,32` — e da leitura por rate anterior no subconjunto alterado (f01 `+R$5.429,18` / f02 `−R$30.228,79`).
2. **Validação dos critérios AC-E6-01..AC-E6-10** do doc 81 §4 (hoje `TARGET_DRAFT / PENDING_OWNER_VALIDATION`): duas leituras rotuladas, trilha humana de homologação, recálculo identificável com `as_of`, paridade por grão oficial, comparação justa, tratamento de rate ausente, histórico incompleto (<27/04/2026), cutoff/republicação, boundary de segurança e evidência de testes.

| Campo | Conteúdo |
|---|---|
| Impacto PROC-0072 | transforma a direção aprovada (duas leituras) em semântica homologada de indicadores MOD |
| Critério de aceite | `FUNCTIONAL_ACCEPTANCE` registrado com versão e data + `DECISION_REQUIRED` de E6-D1..D6 respondidos pelos owners |

> **Bloqueio deliberado:** a direção está aprovada, mas `IMPLEMENTATION_AUTHORIZED = NO` — nada será implementado antes dos detalhamentos e das homologações acima.

#### E10 — R10 `CC matriz.xlsb`: confirmação da seleção EDAPP e regras de benefícios

**Contexto (doc 80 §44):** a seleção do artefato foi reconstruída linha
a linha (353/353 itens SD1, Σ `D1_TOTAL` = R$ 169.704,12 exato) e
corresponde 1:1 ao procedimento relatado no vídeo (doc 56 Registro 17):
digitação no mês → exclusão de tipos de entrada → exclusão de MP →
exclusão de coparticipação de benefícios → classificação manual
Direto/Indireto/Adm. G5 promovido a `PASS`; abaixo apenas os pontos de
confirmação documental, não uma nova investigação.

| Item | Solicitação | Evidência atual |
|---|---|---|
| E10.1 | **Lista exata de tipos de entrada excluídos** na sessão EDAPP (códigos 3 dígitos) | Narrada 12 códigos (`01,02,03,04,030,040,083,080,085,120,204,318`); observada 13 TES (`001,003,016,020,030,040,080,083,085,120,159,204,318`); `016`/`159` fora da lista narrada (ambos `F4_DUPLIC='N'`); `02`/`04` ambíguos → `020`/`040`? |
| E10.2 | **Consulta/filtro salvo EDAPP** ou data-hora da sessão de exportação | Exportação é seleção de operador, não relatório de produtor fixo — confirmação fixa a lista de E10.1 como regra, não conveniência do mês |
| E10.3 | **Regra de benefícios**: confirmação de que coparticipação plano saúde/odonto (parcela colaborador, sem CC) fica fora; tratamento da parcela empresa | 6 linhas excluídas: TES 046, tipo GG, sem CC, `<PRODUTO-BENEFICIO-*>` — R$ 6.990,44 |
| E10.4 | **Fonte da classificação Direto/Indireto/Adm** por centro de custo (taxonomia oficial?) | Coluna sem título pós-exportação, manual, guiada pelo CC — não é campo SD1/CTT; precisa owner da taxonomia para virar regra canônica |

| Campo | Conteúdo |
|---|---|
| Owner | Controladoria / operadora que emitiu o arquivo |
| Impacto PROC-0072 | fixa a lista de exclusão como regra versionável e o owner da taxonomia Direto/Ind/Adm; G5 já PASS — E10 documenta, não desbloqueia gate |
| Critério de aceite | lista de TES confirmada por escrito + filtro EDAPP preservado + regra benefícios + taxonomia de classe confirmada |

---

## §3 — Estado do ciclo e marcações preservadas

| Item | Estado |
|---|---|
| Reconstrução DEL100 vigente | 3.058/421/242 — query §24.E, validada (SF4 compartilhada ≡ `xFilial`, reproduzida 2×) |
| 724/672 e derivadas (§19.C, §20.A, §21.C) | `STALE_EVIDENCE` — `EXECUTION_DRIFT` registrado em §23.A |
| Pagar FINR190 | **paridade row-level PROVEN** (948/948 chaves, TB=`E5_VALOR`, VO=`E2_VALOR`+regras aglutinado, resumos/componentes exatos — doc 84); residual: subconjunto do log + versão RPO |
| Receber DLP06R01 | **paridade row-level do artefato PROVEN, Δ R$0,00** (649 SE5×SE1 + 8 `PA`/`FINA750` sem título; TB=`E5_VALOR`, VO=`E1_VALOR` 649 + VO=provisão `'P'` espelhada MATA121/FINA050 8/8 — doc 84, errata doc 80 §30); residual: fonte do produtor (G4) + regra geral do sem-título (3 excluídos identificados) — **pende de TI/ERP** |
| MOD fórmula/rate | PROVEN; direção de apresentação `APPROVED / PRODUCT_DIRECTION_ONLY` (opção C, doc 81) · `IMPLEMENTATION_AUTHORIZED = NO` · detalhamentos E6-D1..D6 e AC-E6 pendentes |
| R10 CC matriz (SD1 EDAPP) | **seleção reconstruída + paridade PROVEN** (353/353 itens, Σ `D1_TOTAL` 169.704,12 exato; digitação+13 TES-out+MP-out+benefícios-out — corroborado owner doc 56 §Reg.17; G5 PASS); residual: lista exata TES + taxonomia Direto/Ind/Adm — **E10** |
| SB9 | snapshot SB2 PROVEN no recorte; produtor `BLOCKED` (E4/E5) — **reforço 23/10:** onda retificadora de ~20-21/10 confirmada por RECNO (SD1 doc `<NF-RETIF-A>` sanitizado reclassificado 001→085 + SB9 f01 inserido 21/10 19:13) — corrobora "reexecução/etapa distinta" sem identificar o writer |
| MATR320 (R05) | **fonte localizado 23/10:** `matr320.prx` padrão TOTVS (execução via SP `MAT056`; variante `DLPR320` descartada por poder3 zerado no fonte × não-zerado no PDF). Colunas MP reconciliadas 12/13 ao centavo em estado de emissão (doc 84 §4.2, doc 80 §31, regras doc 85 §5); residual: MovInt ~R$0,48 e `as_of` do saldo |
| DLP06R01, P7 | **parcialmente resolvidos 23/10** — DLP06R01.prt=layout compartilhado (pagar: produtor FINR190 provado; receber: custom `DLP06R01` sem fonte — E1 pendente); P7="Registro de Inventário Modelo P7"/MATR460 + artefatos; residuais estreitados (E1/E2) |
| Doc 47 | crosswalk doc 83 + §11/§11.1/§11.2: **39/60 = 65,0% coleta · 41/90 = 45,6% auditoria** — 37 gates 23/10 (rework) + G5 de R01/R02 (paridade row-level, doc 84) |

---

## §4 — Referências

- Registro vivo: `80-ciclo2-registro-vivo-investigacao-devin.md` §17–§26
- Decisão E6: `81-decisao-e6-historico-monetario-mod-opcao-c.md` (`e68ae2d63129`)
- Crosswalk evidências: `83-ciclo2-crosswalk-evidencias-r01-r15.md` (23/10)
- Tracker de gates: `47-t01-report-column-audit-tracker-v1.md` (G1–G6)
- Acervo de fontes: `docs/13-fontes-totvs-protheus/` (`DEL100.PRW`, `MA330OK.PRW`, `FINR190_DLP.PRX`, `matr860`, `DLP34R01.PRW`)
- Commits-âncora: `9281aa9f09` (R5), `a1f2e47f18` (R6), `4fea4c09b3` (R7), `dd2ea700ee`+`b7cc80c246` (R8), `c06826af9d` (R9), `287f94a2aa` (R10), `f7c899fffe` (R11), `f95c7213eb` (R12), `4577c8c5e4` (R13)

**Última atualização:** 2026-10-23 · preparado por Devin
