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
