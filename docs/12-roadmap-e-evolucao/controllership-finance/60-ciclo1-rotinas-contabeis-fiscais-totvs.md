# 60 - Ciclo 1 | Rotinas fiscais e contabeis TOTVS: inventario documental

Data: 2026-10-22. Processo: PROC-0072. Fonte privada: planilha de levantamento de rotinas e niveis de privilegio. Este registro **nao inclui nomes de usuarios, identificadores pessoais, dados fiscais transacionais, valores ou extratos**, nem anexa a planilha.

## Descoberta documental
O arquivo possui **duas abas de trabalho**: uma de rotinas fiscais com 14 linhas de rotina e outra de rotinas contabeis com 7 linhas de rotina; nesta segunda, existe ainda anotacao isolada sobre criacao de acesso sem codigo de rotina, que nao deve ser interpretada como procedimento aprovado. O texto transcrito enviado no chat continha apenas o conjunto fiscal; a planilha complementa esse texto com rotinas contabeis. Cada linha descreve nome da rotina, modulo TOTVS, codigo/programa, nivel de privilegio registrado e finalidade informada.

Esta e uma matriz **descritiva de rotinas e privilegios**; nao e comprovante de grants efetivos, execucao, ownership de CRUD nem lista de entregaveis do checklist. Validar perfis e autorizacoes vigentes diretamente com autoridade de seguranca/ERP, sem copiar grants para o Portal.

## Inventario conceitual por area

| Area | Programas citados | Funcao relatada no documento | Status |
|---|---|---|---|
| Fiscal - parametros tributarios | `MATA080`, `MATA540`, `MATA019`, `FISA170` | TES, excecoes fiscais, indicadores fiscais de produto e configuracao de tributos | DOCUMENTED / technical contract TO_INVENTORY |
| Fiscal - cadastros e regularizacao | `DEL002`, `MATA900`, `FISA140` | texto legal, acertos fiscais e registro auxiliar fiscal | DOCUMENTED / WRITE_AUTORIZATION_NOT_PROVEN |
| Fiscal - notas e produto | `COMXCOL`, `MATA103`, `EDAPP`, `MATA010`, `SPEDNFE` | importar/consultar entradas, consulta generica, cadastro de produtos e exportacao XML | DOCUMENTED / TO_INVENTORY |
| Fiscal - custos e obrigações | `MATR910`, `SPEDFISCAL` | Kardex para CPV/inventario; geracao SPED/Bloco H/K conforme relato | DOCUMENTED / TO_INVENTORY |
| Contabil - consulta de dados | `EDAPP`, `MATR460`, `MATR989`, `DLP204` | consulta generica, P7, material em processo e faturamento x MOD | DOCUMENTED / TO_INVENTORY |
| Contabil - financeiro | `FINR150`, `FINR130`, `FINR190` | titulos em aberto a pagar/receber e relacao de baixas | DOCUMENTED / TO_INVENTORY |

**Nivel de privilegio relatado:** algumas rotinas fiscais incluem incluir/alterar/consultar; outras e todas as rotinas contabeis listadas aparecem como consulta. Isto **nao comprova que permission/role/grant esteja ativo**, nem concede autorizacao para automacao ou alteracoes em ERP. O apontamento de acesso na planilha e uma necessidade a investigar com o owner, nao pedido de provisionamento.

## Cruzamento com o acompanhamento do video e documentos canonicos

- `EDAPP` liga consultas genericas a faturamento e CC; para a triagem da SD1, dicionario de campos, TES, SB1 e cadastro de CC continuam `TO_INVENTORY`. Consulta nao equivale a API canonica.
- `MATA010` e a rotina candidata de consulta do cadastro de produtos; pode fundamentar pesquisa de itens e tipos, com approval de owner.
- `MATA080` e `MATA540` podem ajudar a explicar cadastros fiscais relacionados a TES/excecoes, sem inferir classificacoes gerenciais.
- `MATR910` corrobora o identificador do Kardex diario empregado em CPV/inventarios, mas nao prova paridade com os arquivos tratados manualmente.
- `MATR460` corrobora P7 oficial, distinto do R03 operacional de SB9/SB1; comparar full versus layout contabil em contrato proprio.
- `MATR989` corrobora a identificacao de rotina de material em processo, mas nao sua formula ou origem fisica completa.
- `DLP204` e um candidato preciso para a consulta de faturamento x MOD, com dados e formulas ainda nao validados.
- `FINR150` e `FINR130` referem-se a posicao de titulos em aberto; `FINR190` e relacao de baixas. Nao confundir conceitos, nem afirmar paridade com R01/R02 sem evidencias.
- `SPEDFISCAL` foi descrito no documento como rotina ligada a Bloco H e K; nao assumir que a geracao SPED substitui layout P7 ou vice-versa sem homologacao.
- O checklist por empresa/unidade fica sob P6/P2/P5, **nao** sob essa matriz de rotinas/perfis.

## Fila do Ciclo 2
1. Confirmar owner, versao e customizacao de cada rotina, identificador real de executavel/programa, parametros e tabelas fontes/consumidoras.
2. Mapear alias e campos fisicos de SD1, SB1, centros de custo/TES, Kardex, estoque/custo, MOD, titulos/baixas; priorizar conforme matrizes docs 46, 55, 57, 58 e 59.
3. Descobrir producers/consumers existentes em `api-delpi`, BFF e dashboards, evitando duplicacao de logica.
4. Validar segregacao de acesso efetivo com owners de TI/TOTVS e Core. Permissoes do Portal continuam **somente** `controllership-finance.access` e `controllership-finance.manage`; filial como contexto de dados.
5. Separar rotinas de leitura/relatorio de comandos mutantes (fiscal, recalculos e configuracoes). Nenhum write autorizado.
6. Provar output/paridade com fixture protegida fora do GitHub, e mapear formato/versao de cada entrega P2/P5 com aprovacao humana.

## Status
`TWO_SHEETS=PROVEN_DOCUMENT`; `ROUTINE_CODES=PROVEN_DOCUMENT` (existencia no arquivo, nao no runtime); `PRIVILEGE_LIST=DOCUMENTED_NOT_GRANTED`; `ERP_RUNTIME_ACCESS=TEST_NOT_RUN`; `SOURCE_PARITY=TEST_NOT_RUN`; `NEW_API_DESIGN=TO_INVENTORY`; `IMPLEMENTATION_AUTHORIZED=NO`.


## Correcao de proveniencia e catalogo por rotina - 22/10/2026

**Informacao adicional do PO, atribuida a <GESTORA-PROC>:** esta planilha representa **as rotinas que o pessoal da Contabilidade consegue acessar no TOTVS**. Isso e evidencia de conhecimento operacional relatado pela responsavel, mais forte do que uma lista generica de possibilidades, mas ainda nao e auditoria tecnica de grants por usuario/perfil/ambiente. **Nao inferir que a sigla DRE nomeie usuario ou processo tecnico**: aqui DRE e um potencial consumidor gerencial a estudar, sem acesso demonstrado para ele.

### Rotinas da aba Contabil - finalidade e saida informada, sem payload

| Programa | Funcao informada | O que se espera consultar/obter segundo o documento | O que permanece nao demonstrado |
|---|---|---|---|
| `EDAPP` | Consulta generica | Consultas configuradas a bases/relatorios; escopo exato varia por configuracao | Tabelas liberadas, filtros, export, colunas e permissao efetiva |
| `MATR460` | Registro de Inventario Modelo P7 | Posicao/inventario de estoque para conferencia e prestacao contabil | Parametros completos, variantes, status/cutoff, formula e paridade |
| `MATR989` | Material em processo | Relatorio de materiais/saldos em processo | Tabelas, calculo, unidade e composicao |
| `DLP204` | Faturamento x MOD | Comparativo de faturamento e mao de obra direta | Numeradores, denominadores, campos e calculo oficial |
| `FINR150` | Titulos a pagar em aberto | Posicao de obrigacoes em aberto | Parametros, eventos de compensacao, fontes e layout |
| `FINR130` | Titulos a receber em aberto | Posicao de direitos em aberto | Parametros, status, fonte e layout |
| `FINR190` | Relacao de baixas | Relatorio de baixas financeiras | Variantes/customizacao, cinco saidas, paridade com R01/R02 |

### Rotinas da aba Fiscal - escopo de leitura/operacao informado, sem pressupor retorno de API

| Programa | Funcao descrita na planilha | Resultado funcional descrito (nao DTO comprovado) |
|---|---|---|
| `MATA080` | Cadastro TES | Parametros fiscais, geracao de impostos/duplicatas e movimento de estoque |
| `MATA540` | Excecao fiscal | Regras tributarias fora do padrao |
| `DEL002` | Cadastro de texto legal | Textos legais de notas fiscais de saida |
| `COMXCOL` | Importador XML | Entrada automatizada de documento fiscal eletronico |
| `MATA103` | Documento de entrada | Consulta/registro manual de documentos de entrada |
| `EDAPP` | Consulta generica | Extracoes de entrada e documentos a desconsiderar de faturamento |
| `MATA010` | Cadastro de produto | Classificacao, tipo, origem e atributos fiscais do material |
| `MATA019` | Indicador de produto | Aliquotas fiscais associadas ao cadastro |
| `MATR910` | Kardex diario | Movimentacoes para CPV e inventario |
| `SPEDNFE` | Faturamento NFe | Exportacao XML de nota fiscal |
| `SPEDFISCAL` | Geracao SPED | Arquivo fiscal digital e blocos relatados |
| `MATA900` | Acertos fiscais | Correcoes fiscais em documentos de entrada |
| `FISA140` | Cadastro de codigo fiscal auxiliar | Cadastro de codigo para registro fiscal |
| `FISA170` | Configurador de tributos | Configuracao tributaria relatada para novo regime |

**Separar quatro evidencias:** (1) codigo e finalidade **PROVEN_DOCUMENT**; (2) acesso pela equipe de Contabilidade **OWNER_REPORTED_VIA_PO**, sujeito a auditoria atual; (3) relatorio/export especifico **TO_INVENTORY**; (4) tabela, coluna, formula, API e permissao efetiva **TO_INVENTORY/TEST_NOT_RUN**. Nao assumir leitura de dados em toda rotina: varias sao cadastros ou geracoes, e a planilha lista privilegios de escrita em parte do escopo Fiscal. Nenhuma permissao TOTVS implica permissao do Portal.

**Proximo estudo Ciclo II:** inventariar cada codigo com owner TI/Protheus, versao, perguntas, caminho de menu, objetivo, formato de saida, tabela/campo, filtros, granularidade, efeitos colaterais e consumidores contabeis; consultar efetivamente apenas por ferramentas read-only autorizadas e comparar com relatorio original protegido. Ligar os artefatos homologados aos deliverables de P2/P5, sem criar endpoint por rotina automaticamente.
