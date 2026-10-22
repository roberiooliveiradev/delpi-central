# 61 - Ciclo 1 - CPV: arquivo de Kardex fisico-financeiro

Data do inventario: 22/10/2026. PROC-0072. Fonte privada: planilha binaria de CPV da matriz, identificada pelo PO como referente a setembro/2026. **O arquivo original e seus dados comerciais/fiscais nao sao publicados neste repositorio.**

## 1. Natureza do artefato

A planilha tem **uma aba**, intitulada `01-02 - Kardex Fisico-Financei`, contendo relatorio detalhado de Kardex fisico-financeiro. Nao e evidenciada no arquivo uma aba separada de memoria de calculo gerencial do CPV, nem formula consolidada de CPV homologada. A fonte operacional candidata e a rotina **`MATR910`** citada na planilha de liberacoes (doc 60), mas o executavel que gerou este arquivo ainda precisa ser confirmado.

**Estrutura observada localmente**: cabecalho de referencia/emissao; blocos por produto; cadastro/contexto do item (tipo de material, unidade de medida e armazem); linhas de movimento; custo medio; saldos; resumo final por familia/tipo de material. Cerca de 1,5 mil blocos de produto e 9,3 mil linhas de movimento na amostra recebida. Estes quantitativos sao **perfil do arquivo**, nao regra de negocio nem volume esperado de fechamento.

## 2. Colunas funcionais

| Grupo | Campos/ideias observados | Interpretacao segura |
|---|---|---|
| Identificacao temporal | data de operacao, data de referencia, emissao | periodos e timestamps separados; nao inferir cutoff por nome |
| Documental/fiscal | TES, codigo fiscal, numero do documento | base para identificar natureza da operacao e exclusoes candidatas |
| Entradas | quantidade, custo total de entrada | movimentos de aumento de saldo |
| Saidas | quantidade, custo total de saida | movimentos de reducao de saldo |
| Valorizacao | custo medio do movimento, saldo de quantidade, saldo total valorizado | trilha de valorizacao, sujeito a regras oficiais |
| Contexto do item | codigo, tipo, unidade, grupo, armazem, segunda UM | dimensoes de agrupamento e conversao |
| Vinculos de movimentacao | referencia a pedido, fornecedor, CC, projeto, OP ou ordem | pistas para classificacao; nao presumir semantica unica |
| Resumo | quantidades e valores agrupados por familia/tipo de material | fechamento agregado do proprio relatorio, nao validacao automatica de CPV |

**Resultado da estrutura:** o arquivo incorpora movimentos de produtos de varios tipos e **nao somente produtos acabados**. O campo de referencia pode misturar diversas entidades; requer dicionario e interpretacao conforme a operacao.

## 3. Competencia, data e cutoff

O nome do arquivo indica setembro/2026, enquanto o cabecalho do relatorio traz referencia/emissao em 01/10/2026; linhas de movimento consultadas incluem datas de setembro. Isso e **consistente com exportacao pos-periodo, mas nao prova cutoff contábil, momento de apuracao nem processamento final de custo**. Conservar a distincao entre mes de competencia, intervalo do movimento, data da foto do custo, horario de geracao e status do Acompanha Custos (processado/revisado/homologado).

## 4. Cruzamento com video e docs anteriores

1. **Kardex/CPV**: reforca a existencia de trilha fisico-financeira no relatorio, conforme V12/V14-V15 do doc 57 e a rotina MATR910 no doc 60.
2. **TES, codigo fiscal e documento**: candidatos para localizar regras de elegibilidade de saidas, devolucoes, inventario e exclusoes fiscais. O filtro narrado no video por determinado documento de inventario nao pode ser generalizado a este arquivo sem ver parametros.
3. **Armazem**: os blocos observados representam Armazem 01; o video fala tambem de inventarios envolvendo outro armazem. **Nao concluir** que arquivo de Armazem 01 cobre inventario de 01+99 nem toda a base de CPV.
4. **Tipos de produto**: existem MP, PI, PA e demais categorias; evitar somar indistintamente qualquer saida do Kardex como CPV contabil. Identificar quais movimentos compoem custo dos produtos vendidos e quais sao consumo/transferencia/producao, com regras oficiais.
5. **Resumo final**: resumo por familias e evidência de agregacoes do relatorio; nao e paridade comprovada com MATR320, P7, DRE ou planilha gerencial.
6. **Custos negativos/estornos e custo zero**: examinar sinais, movimentos inversos e linhas de custo zerado antes de formular politica. Nao marcar anomalia automaticamente.
7. **Custo medio**: custo medio no registro e saldo valorizado nao autorizam substituir a rotina oficial de custeio ou recalcular o custo padrao por simples soma.
8. **Arquitetura**: P2 registra evidencia e validacao; P3 cuida de estoque/cutoff; P5 compoe pacote por destinatario. Toda consulta ERP futura via owner api-delpi, exposta a MFE somente pela BFF.

## 5. Investigacoes do Ciclo 2 e criterios de paridade

| Ref | Investigacao | Evidencia minima |
|---|---|---|
| CPV-01 | Confirmar produtor/rotina MATR910, versao e parametros | identificador tecnico, owner, menu, opcao e parametros |
| CPV-02 | Confirmar competencia/cutoff e estado do custeio | relatorio original, processamento, data de referencia e aprovacao |
| CPV-03 | Identificar fontes e chaves dos movimentos e saldos | dicionario SQL/aliases, joins, filial, armazem, documento e item |
| CPV-04 | Homologar inclusoes/exclusoes de CPV por tipo, TES/CFOP, movimento e sinal | criterio oficial Fiscal/Controladoria, fixture protegida, excecoes |
| CPV-05 | Comparar resumo e totais filtrados com Kardex, P7 e saidas oficiais | paridade com criterios de arredondamento/unidades/custos |
| CPV-06 | Identificar regras de custo zero, negativo, estorno e segunda UM | regra, tratamento e casos de teste protegidos |
| CPV-07 | Identificar variante por armazem e fluxo de inventario | parametros do relatorio e relacao com documento INVENT |
| CPV-08 | Determinar output esperado no checklist e package P5 | layout, responsavel, destinatario, evidencia de revisao |

## 6. Gates e segurança

`STRUCTURE=PROVEN_DOCUMENT`; `MOVEMENT_FIELDS=PROVEN_DOCUMENT`; `OFFICIAL_SOURCE_ROUTINE=TO_INVENTORY`; `COMPETENCY_CUTOFF=TO_INVENTORY`; `CPV_FORMULA=TO_INVENTORY`; `REPORT_PARITY=TEST_NOT_RUN`; `FINANCIAL_OUTCOME=INCONCLUSIVE`; `RUNTIME_IMPLEMENTATION=NO_GO`.

Este texto omite identificadores de produtos, documentos, fornecedores, valores, eventos e linhas de transacao, assim como hashes e o arquivo privado. Trata-se somente de modelo conceitual do relatorio.
