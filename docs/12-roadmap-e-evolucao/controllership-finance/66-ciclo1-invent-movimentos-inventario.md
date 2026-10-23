# 66 - Ciclo 1 | Invent: movimentos de ajuste de inventario

**Data de analise:** 22/10/2026. **Processo:** PROC-0072. **Fonte privada:** arquivo XLSB de inventario do PO. Documento de GitHub armazena apenas conceitos; sem datas pontuais de transacao, quantidades, valores, codigos de produtos, documentos particulares, fornecedores ou planilha.

## Estrutura e achados documentais

Arquivo com **uma aba** (`Planilha2`), contendo 12 colunas: `OPERACAO DATA`, `TES`, `C.F`, `DOCUMENTO NUMERO`, `ENTRADAS QUANTIDADE`, `ENTRADAS CUSTO TOTAL`, `CUSTO MEDIO DO MOVIMENTO`, `SAIDAS QUANTIDADE`, `SAIDAS CUSTO TOTAL`, `SALDO QUANTIDADE`, `SALDO VALOR TOTAL`, campo contextual `P.V.,FOR, CC, PJ, OP ou OS`.

A amostra possui **45 linhas de movimentos** e duas linhas finais fora desse padrao. Os 45 movimentos usam identificador documental tecnico `INVENT`. Foram observadas duas combinacoes:
- **`TES 999 / C.F RE0`:** 32 movimentos com quantidade e custo total de saida;
- **`TES 499 / C.F DE0`:** 13 movimentos com quantidade e custo total de entrada.

Os identificadores acima sao codigos de classificacao tecnicos/regras candidatas, nao IDs de transacoes. A amostra mostra saldos apos movimentos; **nao inclui coluna explicita de armazem, produto ou filial**, de modo que nao comprova cobertura integral dos armazens 01 e 99 nem a origem da extracao. Nao presumir que `C.F` seja CFOP fiscal: valores `RE0/DE0` aparentam codigos de operacao e exigem dicionario oficial.

## Relacao com processo e relatórios

- A narracao da <GESTORA-PROC> (video, docs 55-57) descreve consulta do Kardex dos armazens 01/99 filtrada pelo documento `INVENT`, com confronto entre entradas e saidas do inventario. Esta planilha demonstra o recorte por documento e o par de direcoes, mas **nao comprova o filtro de armazens do relatorio que a originou**.
- A planilha CPV/Kardex (doc 61) tem estrutura de movimentos fisico-financeiros; `Invent` parece um extrato filtrado/selecionado, nao uma apuracao final de CPV.
- MATR320 (doc 62) apresenta movimentos agregados por tipo, e P7 (doc 63) apresenta saldos posicionais; o elo entre os documentos exige granularidade, sinais e mesma competencia.
- Linhas com custos de entrada zerados ou saldo residual proximo de zero nao sao, isoladamente, falhas; dependem de regra ERP, arredondamento e fechamento de custo.
- Para P2/P5, o artefato e candidato a evidencia de inventario ou reconciliacao no checklist ja aprovado; nao abrir pagina, permission ou workflow paralelo.

## Perguntas do Ciclo 2

| Ref | Pergunta/gate |
|---|---|
| INV-01 | Confirmar produtor (rotina/versao) e parametros: filial, periodo, armazens 01/99 e criterio documento `INVENT` |
| INV-02 | Confirmar semantica oficial de `TES 999 / RE0` e `TES 499 / DE0`, bem como natureza de `C.F` |
| INV-03 | Recuperar chaves de produto, armazem, item e documento na origem sem deduzir pelas colunas ausentes |
| INV-04 | Homologar formula de efeito liquido entre entradas e saidas, sinais, custos zerados e reversoes |
| INV-05 | Provar cobertura e paridade contra Kardex/MATR910, MATR320 e P7 com mesmo cutoff |
| INV-06 | Definir destino, layout e criterios de evidencia no pacote de fechamento, com <GESTORA-PROC>/Contabilidade/Fiscal |

## Evidencia e controles

`FILE_STRUCTURE=PROVEN_DOCUMENT`; `INVENT_FILTER_IN_SAMPLE=PROVEN_DOCUMENT`; `RE0_DE0_DIRECTIONS=PROVEN_SAMPLE`; `WAREHOUSE_01_99_COVERAGE=TO_INVENTORY`; `PRODUCER=TO_INVENTORY`; `NET_COST_FORMULA=TO_INVENTORY`; `CROSS_REPORT_PARITY=TEST_NOT_RUN`; `IMPLEMENTATION_AUTHORIZED=NO`.

Nenhum resultado financeiro individual ou valor da empresa foi versionado. Estes dados nao autorizam operacoes mutantes no ERP.
