# 65 - Ciclo 1 | Faturamento x MOD - inventario conceitual

Data 22/10/2026. Processo PROC-0072. Fonte privada: Fat x MOD.xlsb. **Nao publicar valores, codigos de produtos, estruturas reais, dados de clientes ou arquivo original**.

## Estrutura observada
A planilha possui duas abas `1-Fl01` e `2-Fl02`, identificadas como estrutura das filiais 01 e 02. Cabecalhos iguais: `PA`, `Seq Comp`, `Cod Produto`, `Desc Produto`, `Qtd Fat.`, `UM`, `Quantidade`, `Custo Unitario`, `Custo Total`, `Custo Produto`, `Horas`.

O conjunto examinado tem 2.459 registros na primeira aba e 2.017 na segunda; ambos sao registros de componentes com prefixo `MOD`. Unidades observadas incluem `HR`, `H` e, em parte da segunda aba, `PC`; semantica e conversao precisam de confirmacao. Campo `Custo Produto` esta zerado em todos os registros de dados da amostra. Existem alguns custos unitarios/total zerados, cuja semantica nao se presume.

## Relacoes matematicas observadas no arquivo
Nas 4.476 linhas de dados examinadas, dentro da tolerancia numerica da precisao armazenada:
- `Horas ~= Qtd Fat. * Quantidade`
- `Custo Total ~= Horas * Custo Unitario`
- `Custo Total` nao corresponde, em geral, a simples `Quantidade * Custo Unitario`.

**Interpretacao restrita:** a planilha parece representar o desdobramento de produtos acabados faturados em componentes/tempos de MOD de sua estrutura e a consequente valorizacao estimada. Isso **nao comprova** horas efetivamente apontadas na producao, contabilizacao de MOD, CPV reconhecido, base de folha de pagamento ou regra oficial do DLP204.

## Cruzamento com fontes
- O video de Joici apresenta conferencia de faturamento x MOD no fechamento; este arquivo oferece dimensoes de PA, sequencia, componente, quantidade faturada, horas e custo.
- A rotina `DLP204` listada no doc 60 e **candidata** a fonte; carece de confirmacao do produtor, parametros, periodo, formula, origem de custo unitario e componentes.
- Relaciona-se conceitualmente a P3/custos, ao WIP (doc 64), CPV/Kardex (doc 61), MATR320 (doc 62) e Registro de Inventario (doc 63), mas nenhum total foi reconciliado.
- As duas abas refletem contextos filial 01 e filial 02; nao introduzir escopo da antiga industria legada no checklist vigente.

## Inventario do Ciclo 2
| ID | Validacao tecnica necessaria |
|---|---|
| MOD-01 | Confirmar relatorio/programa de origem, versao, owner, parametros e data/competencia |
| MOD-02 | Identificar fonte de `PA`, `Seq Comp`, componente e estrutura de produto |
| MOD-03 | Determinar origem da quantidade faturada e efeitos de devolucoes/cancelamentos |
| MOD-04 | Homologar `Quantidade` por unidade de medida e regra de conversao de HR/H/PC |
| MOD-05 | Homologar as duas relacoes observadas e sua politica de arredondamento |
| MOD-06 | Identificar origem e vigencia do `Custo Unitario` e sentido de `Custo Produto` zerado |
| MOD-07 | Comparar tempos teoricos com apontamentos efetivos quando existirem, sem substitui-los |
| MOD-08 | Definir evidencia e formato de entrega para P2/P5, conforme contratos ja aprovados |

## Evidencia e restricoes
`TWO_SHEETS=PROVEN_DOCUMENT`; `COMPONENT_PREFIX_MOD=PROVEN_DOCUMENT`; `OBSERVED_FORMULAS=PROVEN_SAMPLE`; `REPORT_PRODUCER_DLP204=TO_INVENTORY`; `OFFICIAL_CALCULATION=TO_INVENTORY`; `ERP_PARITY=TEST_NOT_RUN`; `COST_ACCOUNTING_OUTCOME=INCONCLUSIVE`; `IMPLEMENTATION_AUTHORIZED=NO`.

Este documento possui somente metadados, conceitos, formulas abstratas e lacunas. Nao armazenar registros ou numeros financeiros originais no GitHub.
