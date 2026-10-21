# 55 — PROC-0072 | Levantamento consolidado de conferencias de estoques e custos (AS-IS)

**Data de registro:** 21/10/2026. **Estado:** DOCUMENTED_PARTIAL / TO_INVENTORY; reconciliacao numerica = INCONCLUSIVE; paridade ERP/API = TEST_NOT_RUN; design de ferramenta consolidada = TARGET / DECISION_REQUIRED. **Sem autorizacao para implementar runtime.**

## 1. Objetivo, metodo e evidencias
Objetivo: capturar as regras e dependencias demonstradas no recorte audiovisual fornecido pelo PO, em vez de copiar cada relatorio TOTVS para uma pagina. Autoridade AS-IS: TEO e responsavel humana do processo; este documento e um **levantamento observacional**, nao confirmacao formal. Autoridade TARGET: GitHub HEAD/ADRs. Fontes:
- Video de acompanhamento PROC-0072, segmento recortado com 14 minutos, correspondente aproximadamente a 19:00–33:00 da reuniao original; capturas e transcricao de trabalho anteriormente examinadas. Marcacoes temporais abaixo aproximadas, conferiveis no material primario. **Nao afirmar que os audios foram transcritos/verificados literalmente nesta revisao.**
- Screenshots do TOTVS com abas `Movimentacoes Kardex Diario - Padrao`, `Saldo Em Processo`, `Em Processo`, `Entradas e Saidas`; parametros do MATR320.
- PDF original `Entradas e saidas.pdf`: `SIGA/MATR320.prt/v.12`, uma pagina, periodo 01/09/2026–30/09/2026, filial MATRIZ, emissao 01/10/2026. Documento original disponivel na conversa, nao reproduzido no repo.
- Inventario de relatorios doc 46 (especialmente R03 a R10 e secao R05 original) e doc 54 (primeira leitura cruzada do recorte). Na divergencia entre anotacoes/transcricao e documento original, preservar ambos e sinalizar divergencia, nunca conciliar por suposicao.

**Legendas:** `PROVEN` = observavel na fonte fornecida, com limite de escopo; `SOURCE_REPORTED` = fala/transcricao ou relato, sujeito a confirmacao; `TO_INVENTORY` = regra/campo nao verificado; `TARGET` = hipotese de produto. Resultado `PASS/FAIL/PENDING/INCONCLUSIVE/TEST_NOT_RUN/STALE_EVIDENCE` refere-se a verificacao, nao a disponibilidade da pagina.

## 2. Mapa dos artefatos do fechamento
| ID | Artefato TOTVS/externo | Funcao observada | Evidencia | Lacuna de integracao |
|---|---|---|---|---|
| R03 | P7 `MATR460` (padrao e layout H) | estoque historico valorizado e recorte para contabilidade/financeiro | PDFs P7 e video/documento 46 | algoritmo, parametro H e paridade SQL ainda nao provados |
| R04 | Consumo / relacao por OP `MATR860` | consumo em OP, segundo catalogo | doc 46 | ainda nao demonstrado como parte desta conciliacao |
| R05 | `MATR320` Resumo Entradas e Saidas | saldos inicial/final por tipo, compras, requisicoes, vendas, transferencias etc. | PDF original e dialog TOTVS | fonte, formula e reconciliacao fisica |
| R06 | Movimentacoes Kardex Diario armazem 01 | movimentos detalhados; filtros fiscais para previa de CPV | aba TOTVS + relato no video | programa, coluna CFOP exata, sinal e total |
| R07 | Movimentacoes Kardex Diario armazem 99 | movimentos/inventarios; filtro `INVENT` | video/transcricao | programa, chaves e valor de ajustes |
| R08 | Saldo Em Processo e Em Processo | duas consultas distintas para saldos/ordens em processo | abas TOTVS | parametros, diferencas, valores e formula de conciliacao |
| R09 | Excel Faturamento x MOD | tratamento de dados exportados e filtragem MOD | video/transcricao | producer, tabela/arquivo oficial, regra de transformacao |
| Outros | P7 Bloco H, relatorios auxiliares | contexto de apuracao | docs 46/54 | nao presumir reconciliacao automatica |

**Distincao importante:** MATR320 e Kardex sao saidas diferentes no TOTVS; nao deduplicar R05 com R06/R07 apenas porque ambos dizem respeito a entradas/saidas.

## 3. Linha do tempo da atividade humana (tempo aproximado na gravacao integral)
| Janela | Evidencia observada / relatada | Finalidade candidata | Estado |
|---|---|---|---|
| 19:20–20:10 | P7 data final, relatorio padrao e Bloco H; mencao a terceiros | estoque de fechamento/escopo contabil | DOCUMENTED_PARTIAL |
| 20:35–22:50 | emissao/exportacao Kardex 01 e 99, Saldo em Processo, Em Processo e Entradas/Saidas | preparar fontes para conferencias posteriores | PROVEN sequencia de telas, nao equivalencia das saidas |
| 21:35–21:42 | parametros MATR320: inicio/fim tipo e produto, datas, primeira moeda, saldo Movimento, MOD Nao | parametrizar R05 | PROVEN parcial por screenshot; conferir telas completas |
| 23:10–24:50 | planilha Kardex, filtro `INVENT`, copia/soma de entradas e saidas | diferenca de inventario | SOURCE_REPORTED, reproducao numerica PENDING |
| 25:10–25:50 | avaliacao de residuo de materiais de terceiros da ordem de R$3,80 | conferir custo residual | SOURCE_REPORTED; decisao humana contextual |
| 26:12–26:50 | Kardex 01, selecao de codigos fiscais; previa de CPV por soma | CPV operacional | SOURCE_REPORTED, codigos exatos TO_VERIFY |
| 27:15–29:20 | Excel faturamento/MOD, desmesclar, converter valores em numero, filtrar MOD | apurar parcela MOD | SOURCE_REPORTED, total/linhas pendentes |
| ~30:45 | mencao de conferencia a realizar antes de salvar Kardex | dependencia nao esclarecida | PENDING: fala/tela especifica e outcome ainda nao transcritos com confianca |

Nao transformar a ordem de navegacao em workflow imutavel; Joici relata alternancia para economia de tempo.

## 4. Regras candidatas de negocio e seu teste de evidencia

### CF-INV-01 — Inventario em armazens 01 e 99
**Entrada:** Kardex detalhado do periodo, armazem, produtos, movimento `INVENT`, campos de entrada/saida e valores.
**Operacao relatada:** filtrar `INVENT`, somar entradas e saidas e obter diferenca `entradas - saidas`. Relato de perda perto de R$57 mil.
**Nao comprovado:** expressao exata por coluna/valor, sinal na fonte, se os dois armazens entram no mesmo resultado ou sao conciliados separadamente, linhas especiais, tolerancias, criterio de aprovacao.
**Evidencia minima para PASS:** export original 01 e 99, layout de colunas, filtros salvos, somas independentes por armazem, total reexecutado e aceite humano da formula.

### CF-CPV-01 — Previa de CPV via Kardex 01
**Entrada:** eventos do Kardex 01 classificados por codigos fiscais.
**Operacao relatada:** aplicar filtro por codigos transcritos como `501`, `514`, `61`, `6124`; somar resultante, estimativa falada ~R$388 mil.
**Nao comprovado:** CFOPs completos com zeros, se codigos sao internos ou fiscais, sinal, devolucoes, transferencias, competencia, vinculo com faturamento e valor final do CPV.
**Evidencia minima:** screenshot legivel dos codigos na planilha, export fonte com colunas e linhas, demonstracao da soma e confirmacao de Joici/TEO.

### CF-TER-01 — Materiais de terceiros
**Operacao relatada:** conferir saldos remanescentes, com julgamento humano de um residuo ~R$3,80.
**Nao comprovado:** algoritmo, universo de terceiros, origem de saldo, importancia material do valor e regras de excecao. **Proibido** adotar R$3,80 como limite automatico de tolerancia.
**Evidencia minima:** referencia do item, relatorio e parametros de origem, sinal, saldo esperado, responsavel por justificativa/aceite.

### CF-MOD-01 — MOD de planilha
**Operacao relatada:** exportar, desmesclar, converter campos textuais para numericos, filtrar linhas MOD e somar; referencia oral ~R$172 mil.
**Nao comprovado:** proprietario da fonte, campos, chave de rateio, unidade, moeda, exclusoes, formula final, relacao com CPV.
**Evidencia minima:** arquivo original + transformacao reproduzivel + versao/competencia + amostra de linhas + aceite de owner.

### CF-REC-01 — Conciliacao P7 / MATR320 / saldos em processo
**Hipotese de necessidade:** comparar saldos de fechamento, movimentos do periodo e saldos em processo. Os relatorios nao estao demonstrados como equivalentes: podem ter algoritmos, escopos e datas distintos.
**Nao comprovado:** equacao de reconciliacao, param filtro, tratamento dos armazens 01/99, terceiros, MOD e custo. **Nao** usar soma direta sem evidenciar semantica e movimentos.

### CF-GATE-01 — Conferencia anterior ao salvamento dos Kardex
**Origem:** fala observada/relatada perto de 30:45.
**Estado:** PENDING. Registrar acao exata, entrada, criterio e resultado antes de promover a requisito de bloqueio.

## 5. Referencia monetaria de R05 (MATR320), setembro de 2026
PDF `SIGA/MATR320.prt/v.12`, moeda da impressao indicada como R$, filial MATRIZ, periodo 01–30/09, tres decimais:
| Campo total | Valor impresso |
|---|---:|
| Saldo inicial | 3.931.904,103 |
| Compras | 658.723,710 |
| Movimentacoes internas | -84.151,785 |
| Requisicoes para producao | -805.255,012 |
| Transferencias | 0,000 |
| Producao | 476.325,870 |
| Vendas | 544.313,350 |
| Transferencias para processo | -940.599,335 |
| Devolucao de vendas | 544,897 |
| Devolucao de compras | 4.732,694 |
| Entrada poder terceiros | 319.258,140 |
| Saida poder terceiros | 63.839,435 |
| **Saldo atual** | **3.884.464,444** |

**Nao somar cegamente as colunas para inferir regra**: sinais de vendas, terceiros, requisicoes e transferencias podem depender do programa. Saldo MP final = 3.364.910,314; II = 266.321,455; PA = 190.511,240; PI = 24.528,596; demais EM/GG/MC/MH/MS/MX detalhados no PDF/doc46. Nao confundir total R05 com P7 original ou SB9 operacional. Relatorio original e fonte do numero; comparacao SQL TEST_NOT_RUN.

## 6. Matriz das comparacoes e lacunas
| Par de fontes | Por que comparar | Campos comuns indispensaveis | Situacao |
|---|---|---|---|
| P7 vs MATR320 | saldo inicial/final por tipo e movimentos | data-base, filial, armazens, moeda, escopo, terceirizacao, regra de custo | INCONCLUSIVE |
| Kardex 01 vs Kardex 99 | ajustes INVENT e seus locais | tipo, data, identificador de movimento, entradas/saidas, filial e armazem | TO_INVENTORY |
| Kardex 01 vs previa CPV | derivar subtotal fiscal | codigo fiscal completo, valor, natureza e sinal | TO_INVENTORY |
| Saldo em Processo vs Em Processo | diferenciar universo/saldos | OP, produto, status, competencia, valor/quantidade, data | TO_INVENTORY |
| MOD vs CPV | entender apropriação do custo | periodo, centro de custo/OP, natureza, regra de rateio | TO_INVENTORY |
| Inventarios vs R05 | identificar efeito dos ajustes no resumo | tipo, movimentos, periodo, locais, valor/custo | TO_INVENTORY |

## 7. Contrato de evidencia da futura experiencia consolidada (TARGET, nao GO)
Uma area por competencia/filial poderia ter guias `Saldos`, `Inventarios`, `CPV`, `Terceiros`, `MOD` e `Divergencias`. Cada indicador derivado deve mostrar:
- source_id, programa/relatorio, produtor e data da extracao;
- filtros, filial/armazem/competencia, moeda e precisao;
- formula homologada com versao e owner;
- total calculado, total original, diferenca, estado de disponibilidade e motivos;
- trilha de origem ate as linhas, quando o contrato permitir.
Esta e hipotese TARGET; nao criar nova rota, nova permission, SQL em frontend ou estado automatico de aceite.

## 8. Plano de verificacao sem refazer o levantamento
**Gate V1 — AS-IS audiovisual/TEO:** confirmar CF-GATE-01, codigos fiscais e operacoes que seguem apos 30:45, mais formulas INVENT, terceiros e MOD. Perguntas objetivas apenas para pontos sem prova.
**Gate V2 — fonte tecnica DAVI + GitHub:** localizar owners/programas, APIs READ existentes, tabelas e semantica; testar consulta/fixture de setembro 2026 sem alterar dados.
**Gate V3 — conciliacao:** reproduzir totais por relatorio com mesmo universo e parametrizacao, explicar divergencias e obter aceite humano.
**Gate V4 — DECISION_REQUIRED:** PO decide modelo consolidado, boundaries, contrato, rotas e quais comparacoes virarão controles. Gate transversal antes de implementar.

## 9. Perguntas residuais objetivas para a Joici/TEO
1. Qual conferencia exata e mencionada aos 30:45, qual entrada, calculo e criterio de conclusao?
2. O filtro `INVENT` soma os movimentos do 01 e do 99 em separado ou liquida um contra o outro?
3. Quais codigos/CFOP completos compoem o CPV e como entradas, saidas e devolucoes afetam sinal?
4. Em quais condicoes um saldo de terceiros exige justificativa ou bloqueia fechamento?
5. Qual arquivo/fonte produz MOD, qual coluna se soma apos converter para numero e quais linhas ficam de fora?
6. Quais totais concretos de P7, MATR320, Saldo em Processo e Em Processo devem bater, em qual data/moeda/armazem/filial?

## 10. Estado de conclusao
`AS_IS_REPORT_SET=PROVEN_PARTIAL`; `INV_FORMULA=SOURCE_REPORTED/PENDING_VERIFICATION`; `CPV_FILTERS=TO_VERIFY`; `MOD_PROVENANCE=TO_INVENTORY`; `PRE_KARDEX_CHECK=PENDING`; `MATR320_ORIGINAL=PROVEN`; `CONSOLIDATED_RECONCILIATION=INCONCLUSIVE`; `SQL_PARITY=TEST_NOT_RUN`; `IMPLEMENTATION_AUTHORIZED=NO`.

Proxima acao: validar itens pontuais do video com TEO e owners; depois coordenar verificacao READ de producers e contratos. **Nao exigir reenviar o mesmo recorte para repetir levantamento.**
