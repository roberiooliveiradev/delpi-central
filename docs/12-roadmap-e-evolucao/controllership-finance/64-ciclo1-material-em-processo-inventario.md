# 64 - Ciclo 1 | Material em processo, saldo analitico

**Data:** 22/10/2026. **PROC-0072.** Fonte: planilha binaria privada de material em processo enviada pelo PO. **Somente metadados conceituais:** nao versionar linhas de materiais/OP, valores, identificadores, planilha ou imagens.

## Identidade e estrutura

Uma aba: `01-01 - Saldo em Processo (Ana` (titulo truncado no limite exibido do XLSB). Data de referencia e emissao no cabecalho: inicio de outubro/2026, a confrontar com competencia de setembro/2026. O conjunto tem cerca de **57 mil linhas de dados** e apresenta **cabecalhos repetidos**. **Nao tratar a aba como tabela limpa unica sem identificar secoes e registros especiais.**

Campos: `CODIGO`, `DESCRICAO`, `UM`, `LOCAL`, `ORDEM PRODUCAO`, `TIPO RE/DE`, `QTDE EM PROCESSO`, `VALOR EM PROCESSO`.

A observacao local identifica locais `01` e `99`, registros com tipos `RE0`, `RE1`, `RE2`, `RE9`, alem de muitas linhas com tipo vazio e valores zerados. Ha linhas estruturalmente diferentes, inclusive identificadores textuais de grupo, campos de ordem vazios e cabecalhos dentro da tabela. **O significado dos tipos RE/DE e dos registros sem OP nao foi confirmado.** Nao inferir estoque disponivel, valor oficial ou total contábil com uma soma bruta.

## Papel no fechamento

- Evidencia candidata a relatorio de **saldo analitico de materiais em processo**, potencialmente ligado a rotina `MATR989` da planilha de acessos contabeis (doc 60). Esta associacao e candidata, nao prova tecnica do producer do arquivo.
- Pode explicar a composicao dos valores classificados como **EM PROCESSO** no Registro de Inventario resumido (doc 63), desde que sejam homologados filial, local, data/cutoff, categorias, situacao de OP, criterios de inclusao, valorizacao e exclusoes.
- Complementa a visao agregada de **MATR320** (doc 62) e a trilha de movimentos do Kardex (doc 61), mas **nao equivale automaticamente** a nenhuma dessas fontes.
- Os locais do arquivo sao dimensoes do ERP e **nao** empresas/filiais/permission codes. Escopo empresarial vigente continua matriz e filial da empresa de componentes; nao reutilizar referencia industrial legada.
- Na Central de Fechamento, eventual evidencia digital de material em processo pertence ao catalogo P6, ao checklist P2 e ao pacote P5 conforme as decisoes ja aprovadas; nao criar pagina ou approval paralelo.

## Inventario necessario no Ciclo 2

| Ref | Descoberta/validacao | Owner e teste esperado |
|---|---|---|
| WIP-01 | Identificar producer exato, rotina, parametros e versao | ERP/Joici; output protegido equivalente |
| WIP-02 | Distinguir competencia, data de referencia, emissao e estado de fechamento do custeio | Controladoria/ERP |
| WIP-03 | Obter dicionario de `RE0/RE1/RE2/RE9`, campos, joins, OP, local e item | api-delpi/ERP |
| WIP-04 | Classificar linhas de movimento, saldos, agrupadores, registros sem OP e zeros | Controladoria/ERP; regra de elegibilidade homologada |
| WIP-05 | Provar composicao por tipo de material e diferenca entre armazens 01/99 | Controladoria/Estoque |
| WIP-06 | Reconciliar com seção EM PROCESSO do P7 e resumo MATR320 em mesma competencia/filial | testes de paridade por fonte/corte |
| WIP-07 | Inventariar responsavel, destinatario e formato do entregavel P2/P5 | Joici + areas revisoras |

**Atencao:** arquivo massivo com muitos registros zerados, cabeçalhos repetidos e tipos nao homologados. Ausencia de OP em parte das linhas exige analise da estrutura do relatorio, nao classificacao automatica como erro.

## Evidencia

`ONE_SHEET=PROVEN_DOCUMENT`; `FIELDS=PROVEN_DOCUMENT`; `RE_TYPES=PROVEN_DOCUMENT`; `SEMANTICS_RE=TO_INVENTORY`; `SOURCE_MATR989=TO_INVENTORY`; `P7_RECONCILIATION=TEST_NOT_RUN`; `OFFICIAL_WIP_TOTAL=INCONCLUSIVE`; `RUNTIME_IMPLEMENTATION=NO_GO`.

Somente estrutura, conceitos, identificadores tecnicos da rotina e pendencias. Nenhum dado transacional da DELPI ou arquivo original e publicado.
