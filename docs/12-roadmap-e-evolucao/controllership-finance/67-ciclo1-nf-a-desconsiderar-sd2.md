# 67 - Ciclo 1 | NF a desconsiderar: inventario SD2

Data: 2026-10-22. Processo PROC-0072. Fonte: planilha privada de itens de notas fiscais de saida. Somente entendimento conceitual, sem linhas, produtos, numeros fiscais, parceiros, valores, hashes ou anexo.

## Identidade do arquivo
Uma aba Planilha2. Primeira linha identifica `SD2`, com titulo/cabecalhos de itens de documentos de saida. Exportacao larga, com **184 colunas** e **11 linhas de dados** na amostra recebida. As familias de campos incluem filial, item, produto, unidade e quantidade, local/armazem, preco e valor, tributos, TES (`Tipo Saida`), `Cod. Fiscal`, contas e centro de custo, documento, serie e vinculos de devolucao/origem. Esse conjunto de colunas tem a forma de uma **extracao de itens SD2**, e nao um relatorio que explique por si mesmo o motivo da exclusao.

## Observacoes sem dados sensiveis
- Os 11 itens examinados pertencem ao mesmo contexto de filial e apresentam **uma unica combinacao de TES e codigo fiscal** nessa amostra. Isto e **descricao da amostra**, nao criterio geral de negocio.
- Nao foi identificada coluna expressa de **motivo da desconsideracao** ou decisao de quem avaliou cada documento.
- Presenca de campos fiscais/valores nao prova que os itens foram faturados, reconhecidos na DRE, abatidos do CPV ou cancelados. Exige consulta a cabecalho, tipos de operacao, situacao documental, natureza fiscal, contexto e competencia.
- O video e o checklist (docs 56, 57 e 59) mencionam selecao de notas a desconsiderar e excecoes de faturamento/CPV. Este arquivo **corrobora a existencia do recorte manual**, mas nao confirma quais totais ou relatorios recebem a exclusao. Nao confundir exclusao analitica de relatorio com anulacao ou alteracao fiscal da NF.
- `SD2` e um candidato forte de fonte fisica dos itens; validar tabelas vinculadas, filtros e o papel da consulta EDAPP relatada no doc 60. Nao afirmar que a planilha reproduz a totalidade da SD2.
- Item candidato de evidencia/excecao no checklist P2 e pacote P5, com aprovacao humana e estados existentes. Nao criar permission por TES, filial ou documento.

## Checklist do Ciclo 2
| ID | Verificacao |
|---|---|
| NFEX-01 | Joici/Fiscal: finalidade de desconsiderar, apuracao impactada e justificativa documentavel |
| NFEX-02 | ERP: confirmar origem SD2, produtor EDAPP, parametros, competencia e filtros de selecao |
| NFEX-03 | Confirmar joins documentais, cabecalhos, filial, documento, serie, item, TES e codigo fiscal |
| NFEX-04 | Identificar razoes de exclusao permitidas e tratamento de cancelamento, devolucao e operacao entre contextos |
| NFEX-05 | Confrontar com faturamento, CPV/Kardex, MOD e demonstracoes de referencia sem assumir paridade |
| NFEX-06 | Definir como a evidencia da excecao e seus motivos/revisao ficam auditaveis no fluxo P2/P5 |
| NFEX-07 | Verificar se filtro exclusivo da amostra e especifico da competencia; nao criar regra global por codigo isolado |

## Status
`SD2_HEADER=PROVEN_DOCUMENT`; `FIELD_FAMILIES=PROVEN_DOCUMENT`; `SAMPLE_FILTER_HOMOGENEITY=PROVEN_SAMPLE`; `EXCLUSION_REASON=TO_INVENTORY`; `ERP_QUERY_PARITY=TEST_NOT_RUN`; `EXCLUDED_FROM_DRE_OR_CPV=INCONCLUSIVE`; `IMPLEMENTATION_AUTHORIZED=NO`.

**Confidencialidade:** documentos e dados originais permanecem restritos; nenhuma linha, numero de NF, ID fiscal, valor ou codigo individual da empresa foi persistido.
