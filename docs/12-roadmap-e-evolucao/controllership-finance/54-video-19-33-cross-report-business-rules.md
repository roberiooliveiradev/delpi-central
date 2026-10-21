# 54 - Analise transversal do recorte de video: Kardex, inventarios, CPV e MOD

Data 2026-10-21. Escopo de evidencia: video recortado de 14 minutos enviado pelo PO, aproximadamente trecho 19-33 minutos da gravacao do PROC-0072; imagens observadas em quadros a cada 30s e transcricao de trabalho `PROC-0072_Transcricao_Integral_Video.md` recebida no projeto. AS-IS a confirmar formalmente com TEO/Joici, pois transcricao pode conter erros; codigos e valores citados sao relacoes observadas/ditas, NAO formulas canônicas verificadas contra SQL. Sem implementacao de runtime nem alteracao de contratos. Status: DOCUMENTED_PARTIAL, produto TARGET_ONLY.

## Sequencia e distincao de relatorios
- P7 padrao (estoque valorizado por data), layout Bloco H separado para contabilidade, com selecao de terceiros mencionada na transcricao. R03 nao e equivalente oficial ao MATR460 por deducao.
- Movimentacoes Kardex Diario dos armazens 01 e 99 exportados em Excel, setembro/2026; aba de Kardex e separada da aba de Entradas e Saidas.
- Entradas e Saidas R05: MATR320, setembro/2026, relatorio PDF agregado por tipo e categoria de movimento, ja comprovado pelo original. Nao e o Kardex R06/R07.
- Saldo em Processo e Em Processo aparecem como consultas distintas no TOTVS; seu papel exato na reconciliacao exige validar a regra final.
- Planilhas de faturamento/MOD sao exportadas e preparadas no Excel.

## Mapeamento de regras faladas e gestos visuais
| Tempo da gravacao (aprox) | Operacao AS-IS | Dado/regra transcrita | Estado |
|---|---|---|---|
| 19:20-20:10 | P7, selecionar data final, emitir padrao e Bloco H | Estoque valorizado; Poder de Terceiros excluido na fala; H para contabilidade | DOCUMENTED_PARTIAL; conferir parametros fisicos |
| 20:35-22:50 | Exportar Kardex 01/99, Em Processo, Entradas/Saidas | Kardex 01 para CPV; 99 para inventarios; periodo 01-30/09/2026 | PROVEN sequence visual, parametros parciais |
| 23:10-24:50 | Excel Kardex: filtrar `INVENT`, copiar linhas, somar colunas | Diferenca = valores de entrada menos valores de saida; fala de perda ~R$57 mil | SOURCE_REPORTED; precisao/fonte pendente |
| 25:10-25:50 | Revisao de item conhecido de terceiros | Residuo ~R$3,80 considerado de pequeno efeito no CPV *por julgamento humano* | SOURCE_REPORTED; NAO definir threshold automatico |
| 26:12-26:50 | Kardex 01 filtra codigos fiscais | Transcricao registra 501, 514, 61, 6124; pre-CPV ~388 mil | TO_VERIFY: codigos exatos, zeros/mascaras, colunas e sinal |
| 27:15-29:20 | Relatorio faturamento x MOD em Excel | Desmesclar, converter texto para numero, filtrar MOD; soma ~172 mil | SOURCE_REPORTED; DRE/planilha Minha DELPI nao comprovados como owner |
| ~30:45 | Suposta conferencia anterior ao salvamento dos Kardex | Referencia nao localizada pelo PO no trecho enviado; fala nao verificavel nas evidencias revisadas | STALE_EVIDENCE / RETRACTED; nao usar como regra ou dependencia |

A Joici declara que nao segue sequencia rigida: alterna rotinas para otimizar tempo. Logo a central de conferencia deve expor dependencias verificadas e nao impor ordem arbitraria baseada na gravacao.

## Hipotese de UX consolidada (TARGET, nao aprovada)
Uma unica area de `Conferencia de Estoques e Custos` por competencia/filial com visoes:
1. Inventarios (Kardex 01/99, movimentos `INVENT`, valor entrada/saida, diferenca);
2. Previa CPV (movimentos por codigos fiscais confirmados, drilldown de eventos);
3. Terceiros (saldos remanescentes e justificativas humanas, sem corte automatico inventado);
4. MOD (fonte, limpeza de formato, classificacao e total);
5. Conciliacao P7/MATR320/Saldos em processo (apenas quando formula/escopo e versoes estiverem provados).
Exibir origem, filtros, competencia, status, evidencias, divergencias e responsavel. Nao construir cinco paginas de replica dos relatórios sem decisao de produto.

## Gaps obrigatorios antes de qualquer implementacao
1. Confirmar no TEO e com Joici as falas, codigos fiscais, sinais, formulas e excecoes; video/transcricao nao sao contrato de API.
2. Resolver diferenca entre valores da gravacao e os PDFs P7/MATR320, e entre filial, armazem e competencia.
3. Identificar no api-delpi as fontes e contratos READ reais (SD3 apenas mencionada para inventario; nao presumir equivalencia de consulta existente).
4. Identificar owner e eventual ingestao do Excel de MOD: nao ler planilha de terceiro diretamente por conveniencia.
5. Mapear as comparacoes P7/MATR320/Saldo em Processo com evidencias positivas; a suposta fala aos 30:45 foi RETRACTED e nao pode ser exigida como conferencia.
6. Abrir DECISION_REQUIRED antes de novo produto/pagina/contrato; nenhuma permissao adicional nem acesso direto a api-delpi do browser.

## Evidencia e resultado
Video recortado entregue pelo PO neste dialogo (14 min); transcricao auxiliar local `PROC-0072_Transcricao_Integral_Video.md`, nao registrada como texto canonico. R05 PDF original: `SIGA/MATR320.prt/v.12`, 01-30/09/2026, emitido 01/10, e registrado em doc 46. Este documento e de processo/descoberta, nao de codigo. Verdict: INCONCLUSIVE para calculo e reconciliacao automatizada, DOCUMENTED_PARTIAL para operacoes humanas observadas.
