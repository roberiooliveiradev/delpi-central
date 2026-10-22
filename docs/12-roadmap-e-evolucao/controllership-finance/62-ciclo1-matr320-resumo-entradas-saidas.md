# 62 - Ciclo 1 | Resumo de Entradas e Saidas MATR320

Data da analise: 2026-10-22. Processo PROC-0072. Fonte privada: PDF de uma pagina fornecido pelo PO. **Documento original, valores, dados transacionais e imagem nao sao versionados.**

## 1. Identidade documental comprovada

O cabecalho do PDF identifica `SIGA/MATR320.prt/v.12`, titulo "Resumo das Entradas e Saidas EM R$", intervalo mensal de competencia, data posterior de referencia e emissao e um contexto de filial matriz. A tabela inclui linhas por **tipo de material** e **Total Geral**. E um relatorio agregado, nao um Kardex item a item nem uma apuracao de CPV pronta. A edicao/versao executada na infraestrutura atual ainda nao foi verificada.

## 2. Estrutura e semantica de colunas observadas

| Campo funcional | Descricao segura |
|---|---|
| `Tip` | tipo de material/grupo do resumo |
| `Saldo Inicial` | saldo valorizado de abertura do periodo |
| `Compras` | movimento agregado de compra |
| `Movimentacoes Internas` | movimentos classificados como internos |
| `Requisicoes para Producao` | saidas/requisicoes relacionadas a producao |
| `Transferencias` | transferencia classificada no relatorio |
| `Producao` | movimentos de producao |
| `Vendas` | movimentos classificados como vendas |
| `Transf. p/ Processo` | transferencias para processo |
| `Devolucao de Vendas` | devolucoes ligadas a vendas |
| `Devolucao de Compras` | devolucoes ligadas a compras |
| `Entrada Poder Terceiros` | operacoes de entrada envolvendo poder de terceiros |
| `Saida Poder Terceiros` | operacoes de saida envolvendo poder de terceiros |
| `Saldo Atual` | saldo valorizado de fechamento reportado |

Os sinais de cada coluna e sua relacao com o saldo atual devem ser mantidos conforme o layout oficial e validados com o owner; nao assumir formula de soma unica antes de reconciliar dados reais. A estrutura mostra categorias MP, PA, PI e outras, com total consolidado. Os exemplos individuais e valores de amostra nao foram transferidos a este registro.

## 3. Confronto com video e inventarios

- O documento corresponde ao relatorio **MATR320** descrito no video como apoio a conferencia de entradas/saidas e reconciliacao com posicao de estoque P7 e material em processo (docs 55, 56, 57).
- **MATR320 e MATR910 sao perspectivas distintas:** MATR320 resume movimentos financeiros por tipo; a planilha CPV/Kardex (doc 61) detalha movimentos por item, documento e armazem. Igualdade de totais so deve ser afirmada apos homologacao de escopo, cobertura e classificacao.
- **MATR320 e P7/MATR460 nao sao intercambiaveis:** saldo de movimentacao e posicao inventariada exigem corte, parametrizacao, status do custeio e regras de classificacao coerentes.
- `Vendas` neste resumo nao prova, isoladamente, custo dos produtos vendidos contabil, tampouco linha DRE ou saldo de CPV homologado.
- Diferencas entre competencia do movimento e data de referencia/emissao precisam ser modeladas explicitamente; o PDF foi gerado apos o periodo analisado.
- A existencia de colunas de terceiros e processo reforca a necessidade de tratamento de fronteira (estoque proprio x terceiros; MP/PI/PA e transferencias), sem inferir lancamento de DRE.
- O arquivo registra uma filial matriz, mas nao valida abrangencia global ou existencia de resultado equivalente para outra filial. Escopo ativo do levantamento: matriz e filial da empresa de componentes; industria legada fora do checklist vigente.

## 4. Fila de trabalho para Ciclo 2

| ID | Validacao minima requerida |
|---|---|
| M320-01 | Identificar owner da rotina, parametros, versao, tipo de data e abrangencia por filial/armazem |
| M320-02 | Levantar producers, tabelas, chaves, filtros, TES/CFOP e regras por coluna agregada |
| M320-03 | Validar formulas, sinais, arredondamentos, impacto de estornos/devolucoes e movimentos de terceiros |
| M320-04 | Comparar com Kardex MATR910 por mesma competencia, filial e escopo material |
| M320-05 | Comparar saldos com P7/MATR460 e material em processo, distinguindo variantes e cortes |
| M320-06 | Homologar criterios de CPV com Controladoria/Contabilidade; nao mapear `Vendas` diretamente a DRE |
| M320-07 | Inventariar layout de entregavel e requisitos P2/P5 sem duplicar aprovacao existente |

**Status:** `PDF_LAYOUT=PROVEN_DOCUMENT`; `MATR320_IDENTIFIER=PROVEN_DOCUMENT`; `AGGREGATION_BY_MATERIAL_TYPE=PROVEN_DOCUMENT`; `ERP_SOURCE_TABLES=TO_INVENTORY`; `CPV_DRE_PARITY=TEST_NOT_RUN`; `CROSS_REPORT_RECONCILIATION=TEST_NOT_RUN`; `IMPLEMENTATION_AUTHORIZED=NO`.

**Confidencialidade:** conceitos somente; nada de valores, transacoes, documentos fiscais, codigos de produto ou anexos originais.
