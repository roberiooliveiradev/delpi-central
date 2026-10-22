# 63 - Ciclo 1 | Registro de Inventario: resumo de estoque e em processo

Data de analise: 2026-10-22. Processo: PROC-0072. Fonte: PDF privado "Estoque" recebido do PO. **Nao versionar PDF original, identificadores fiscais/empresariais, valores, exemplos de movimentos ou imagem.**

## 1. Evidencia do documento

PDF de **uma pagina** com titulo "REGISTRO DE INVENTARIO", identificando **matriz** e posicao "ESTOQUES EXISTENTES EM" **30/09/2026**. O material e uma pagina de **RESUMO** que agrupa valores de inventario em duas secoes: **EM ESTOQUE** e **EM PROCESSO**, seguidas de **TOTAL GERAL**. Cabecalhos reservam classificacao fiscal, discriminacao, unidade, quantidade, unitario, parcial e total, mas **nesta pagina** os registros preenchidos sao agregacoes por classe no campo de total; nao ha detalhe individual de produto, quantidade ou custo unitario para verificar.

O arquivo e **compatível conceitualmente** com resumo de Registro de Inventario P7/MATR460 demonstrado no video e inventariado nos docs 46/57/60, mas a propria pagina **nao exibe codigo MATR460**. Logo `SOURCE_ROUTINE_MATR460=TO_VERIFY`, nao PROVEN_RUNTlME. A denominacao "layout Bloco H" tambem nao aparece no PDF; confirmar variante fiscal/contabil/abrangencia antes de classifica-la como tal.

## 2. Estrutura observada e significado

| Secao | Classes resumidas | Leitura permitida |
|---|---|---|
| EM ESTOQUE | materiais de embalagem, gastos gerais, insumos industriais, consumo, limpeza, materia-prima, seguranca, expediente, produto acabado, produto intermediario | posicao de estoque resumida por natureza |
| EM PROCESSO | embalagem, limpeza, materia-prima, produto intermediario | saldos agregados relacionados a processo, sem composicao detalhada |
| TOTAL GERAL | somatorio das duas secoes | consolidado do proprio PDF, nao valor oficial comprovado da DRE |

**Distincao importante:** um tipo (ex.: materia-prima) pode existir nas duas secoes; nao confundir a natureza do material com o seu estado/posicao. A soma aritmetica dos subtotais e coerente na apresentacao, mas isso nao prova reconciliacao com saldos TOTVS ou regras de custo.

## 3. Confronto documental

- **MATR320, doc 62:** resumo de entradas/saidas *do periodo* por tipo de material com saldo inicial, compras, producao, transferencias e saldo final. Este PDF e *foto de inventario em uma data* com segregacao entre em estoque/em processo. Escopo, origem de valorizacao e variantes precisam de conciliacao; nao comparar os totais como obrigatoriamente identicos.
- **Kardex/CPV, doc 61:** movimentos por documento/item/armazem versus este resumo por classificacao; exige ponte de agrupamento e corte.
- **Video e doc 57:** narracao distingue P7 completo de uma variante/layout para entrega contabil, e material em processo. Este PDF **nao traz metadados suficientes** para identificar qual variante foi exportada.
- **Checklist, doc 59:** candidato a evidencia de entrega digital de estoque no P2/P5, com objeto e layout a confirmar conforme destinatario.
- **Contexto empresarial:** somente matriz aparece na pagina; nao presumir cobertura da filial. A antiga unidade industrial documentada em checklist historico nao faz parte das obrigacoes ativas definidas pelo PO.

## 4. Investigacoes Ciclo 2

| Ref | Ponto a verificar | Evidence/criterio |
|---|---|---|
| EST-01 | Qual rotina e variante gerou exatamente esta pagina | producer, print de parametros, layout, owner |
| EST-02 | O que significa EM PROCESSO no produtor | fontes, chaves e estado de custeio |
| EST-03 | Origem de classes e correspondencia com tipos ERP | cadastro/produtos e mapeamentos vigentes |
| EST-04 | Abrangencia de filial, armazem, terceiros, movimentos e fechamento | filtros, competencia, status de custos |
| EST-05 | Reconciliacao P7 vs MATR320 e Kardex (mesmo escopo) | criterios, sinais, arredondamentos, transito/processo |
| EST-06 | Se existe diferenca entre P7 completo e layout destinado a Contabilidade | layout de origem e copia de export protegida |
| EST-07 | Qual item do checklist P2 e qual pacote P5 recebe o arquivo | requisito, owner, destino, evidencia e aceite |

## 5. Gates

`PDF_LAYOUT=PROVEN_DOCUMENT`; `SNAPSHOT_DATE=PROVEN_DOCUMENT`; `STOCK_VS_IN_PROCESS=PROVEN_DOCUMENT`; `SOURCE_MATR460=TO_INVENTORY`; `BLOCO_H_VARIANT=TO_INVENTORY`; `ERP_DATA_PARITY=TEST_NOT_RUN`; `CPV_DRE_ALIGNMENT=TEST_NOT_RUN`; `IMPLEMENTATION_AUTHORIZED=NO`.

A pagina foi inspecionada visualmente. **Resumo documentado != consulta implementada; somatorio apresentado != paridade oficial.**
