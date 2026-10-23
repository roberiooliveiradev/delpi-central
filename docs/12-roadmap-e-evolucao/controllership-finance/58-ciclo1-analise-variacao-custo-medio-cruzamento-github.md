# 58 - Ciclo I | Cruzamento conceitual da analise de variacao de custo medio

> Data: 2026-10-22. Status: DOCUMENTED_PARTIAL / READ_ONLY / NO_RUNTIME_GO.
> Origem privada: planilha "Analise.xlsx" e transcricao textual fornecidas pelo PO. Nao incorporar a planilha, extratos, codigos, descricoes, valores, screenshots com dados ou identificadores operacionais a este repositorio.

## 1. Escopo e cadeia de evidencia

Foi inspecionado localmente o formato da planilha e confrontado conceitualmente com documentos do GitHub em main: instrucoes oficiais, README da frente, docs 46, 49, 56, 57 e codigo do MFE de consulta R03. A busca por codigo do conector GitHub retornou lista vazia inclusive para termos conhecidos; **search miss nao prova ausencia**. Nao houve inventario exaustivo de todos os repositorios/producers nem verificacao de git status local. Nenhuma consulta live TOTVS ou prova de paridade foi executada nesta etapa.

A planilha contem colunas para status por moeda, filial, produto, descricao, tipo, grupo, armazem, custo medio inicial/final e variacao percentual. O arquivo analisado nao contem formulas Excel usadas para produzir a variacao: sao resultados exportados, nao fonte executavel do algoritmo ERP.

## 2. Matriz de cruzamento

| ID | Conceito observado no documento privado | Evidencia GitHub / boundary | Classificacao | Lacuna para fechar |
| --- | --- | --- | --- | --- |
| CV-01 | Lista de revisao de custos medios por produto e deposito | Doc 56, registro 07, descreve etapa TOTVS 'Analise e revisao' com campos equivalentes | PROVEN no contrato visual AS-IS; parity TEST_NOT_RUN | Identificar rotina/DTO e exportacao exata no ERP |
| CV-02 | Custo medio inicial, final e variacao percentual | Docs 56/57 descrevem revisao apos calculo Acompanha Custos; nao fornecem formula homologada | TO_INVENTORY | Confirmar calculo, base temporal, precisao, arredondamento e status |
| CV-03 | Custo inicial zero e variacao apresentada na exportacao | Excecao observada no arquivo; sem regra canonica comprovada no GitHub consultado | TO_INVENTORY | Sem dividir por zero; pesquisar convencao TOTVS e descricao ao usuario |
| CV-04 | Classificacao Positivo/Negativo/Neutro | Export e screenshot da etapa revisao; nomes nao provam beneficio ou prejuizo economico | TO_INVENTORY | Obter semantica exata, sinais, tolerancia e filtros |
| CV-05 | Filial, tipo de produto e armazem sao dimensoes | Doc 49 consulta operacional SB9/SB1 usa filial/armazem/tipo; doc 57 alerta escopos distintos | PROVEN como dimensoes; join/parity TO_INVENTORY | Confirmar granularidade e chaves da analise de custo medio |
| CV-06 | Consulta de estoque historico ja disponivel R03 | Doc 49: GET financeiro/stock-inventory via api-delpi, BFF e MFE, baseado em SB9/SB1, officialP7=false | PROVEN para R03; nao reutilizavel como calculo da variacao sem contrato | Comparar datasets, nao derivar variacao de saldo historico |
| CV-07 | Processamento de Acompanha Custos e wizard de revisao | Doc 56: calculo 100% distinto de homologacao do fechamento; runtime do Portal nao executa job | PROVEN na observacao; runtime TARGET nao aprovado | Inventariar owner, job/status, corte e autorizacao para eventual integracao |
| CV-08 | Dashboards ou indicadores de custo medio existentes na plataforma | Apenas boundaries de api-delpi e strategic-indicators-api afirmados no README; busca GitHub sem resultados uteis | TO_INVENTORY | Inventario dedicado dos repositorios e consumers, sem duplicar regra |
| CV-09 | Auditoria dos apontamentos e investigacao de desvios | Doc 57 prioriza reconciliacoes e investigacao, com gate humano | TARGET / DECISION_REQUIRED | Definir workflow, responsavel, visibilidade e persistencia antes de implementacao |

## 3. Fronteira de reutilizacao

- **Pode ser reutilizado conceitualmente:** identidade de competencia, dimensoes de filial/tipo/armazem, contexto da revisao de custo e padroes de consulta/paginacao/autorizacao do Portal, apos contrato especifico.
- **Nao esta provado reutilizavel como fonte de custo medio:** os saldos historicos SB9/SB1 de R03, totais P7 e dashboards adjacentes. A coexistencia de campos nao comprova equivalencia das regras de custo.
- **Owner do calculo ERP:** api-delpi/TI Protheus devem inventariar, sem copiar regras para a BFF/MFE. BFF compoe e autoriza com effective permissions Core; MFE usa apenas BFF.
- **Permissoes:** somente controllership-finance.access e controllership-finance.manage; filial e dimensao de dado, nao novo permission code.
- **Proibido** concluir que status POSITIVO seja ganho, implementar percentual quando base zero ou converter ausencia de evidencia em PASS.

## 4. Plano de levantamento Ciclo I

1. Pedir ao owner TOTVS/api-delpi identificador da rotina/exportacao da etapa Analise e revisao, parametrizacao, versao e campos fisicos com mapeamento alias->origem.
2. Verificar em READ-only calculo inicial/final, granularidade, referencia temporal, status por moeda, custo zero/negativo e regras de arredondamento; confrontar amostra protegida fora do GitHub.
3. Inventariar producers e consumers reais de custo medio/custo de produto em api-delpi, dashboards de Suprimentos/Producao e strategic-indicators-api. GitHub search vazio = INCONCLUSIVE, nao ausencia.
4. Criar matriz de testes sinteticos: inicial>0/final>0, inicial=0/final>0, inicial=0/final=0, valores negativos, moedas inativas, mesmo produto em depositos diferentes, recalc/historico e dado ausente.
5. Submeter classificacao e limiares a <GESTORA-PROC>/owner. Separar falha ERP de variacao legitima. Registrar parecer funcional e metodo de comparacao.
6. Somente apos contratos, owners e decisao de produto, propor gate transversal e eventual nova experiencia no Portal page-by-page; sem runtime neste ciclo.

## 5. Gates

- DOCUMENT_STRUCTURE = PROVEN (inspecao do anexo privado).
- FIELD_SEMANTICS = PARTIAL_PROVEN / TO_INVENTORY.
- EXISTING_R03_INTEGRATION = PROVEN_BY_GITHUB_DOC_AND_MFE.
- COST_AVERAGE_SOURCE_PARITY = TEST_NOT_RUN.
- CROSS_REPOSITORY_CONSUMER_INVENTORY = INCONCLUSIVE.
- SENSITIVE_DATA_COMMITTED = NO.
- IMPLEMENTATION_AUTHORIZED = NO.
- Proxima acao: inventario tecnico dirigido com owners, sem coletar/circular dados fiscais nos docs.
