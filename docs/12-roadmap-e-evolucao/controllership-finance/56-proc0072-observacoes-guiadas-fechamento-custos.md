# 56 - PROC-0072 | Observacoes guiadas pelo PO: fechamento de custos

Data de registro: 2026-10-21. Fonte: relato direto do PO enquanto acompanha a gravacao, associado ao screenshot TOTVS `Acompanha Custo > Novo fechamento de custo`. Registro incremental: acrescentar proximos trechos em ordem sem recontar o audiovisual por inferencia.

**Regra de evidencia:** `OWNER_REPORTED_VIA_PO` para falas da <GESTORA-PROC> relatadas pelo PO; `PROVEN_SCREENSHOT` para controles e valores visiveis na imagem; `TO_INVENTORY` para comportamento interno de TOTVS, algoritmos e contratos; `TARGET` apenas para ideias futuras. Nao afirmar audio literalmente transcrito ou validar formula TOTVS com screenshot.

## Registro 01 - inicio do fluxo, referencia temporal informada pelo PO ~01:25 a 02:08

### AS-IS: escolha da primeira atividade e paralelismo
1. A <GESTORA-PROC> **prefere iniciar pelos processamentos de fechamento de estoque**, por serem os que mais demoram (segundo relato do PO).
2. Enquanto o TOTVS executa o processamento, ela **continua outras atividades e extrai outros relatorios**. Essa concorrencia de atividades e comportamento observado/relatado, nao promessa de jobs assincronos no Portal.
3. A primeira rotina acionada e **Acompanha Custos**, fluxo **Novo fechamento de custo**. Conforme o PO, sua finalidade operacional e analisar movimentacoes do periodo e gerar o **custo medio do mes**; a formula especifica ainda nao foi verificada.
4. Ela explica que, para executar o fechamento do periodo, precisa estar com a **data do sistema no ultimo dia do mes de referencia**. Por isso, quando executa o fluxo em 01 do mes seguinte, muda temporariamente a data operacional do TOTVS para o ultimo dia do mes anterior. Essa necessidade e **regra operacional relatada pela usuaria**, nao regra tecnica TOTVS confirmada em codigo/contrato. Nao automatizar mudanca da data global.
5. Na tela apresentada escolhe **Metodo de apropriacao = Diaria** e segue em **Proximo passo**; o TOTVS passa a processar o calculo de custos (segundo relato PO). Enquanto processa, ela segue com outras emissões.

### Evidencia visual objetiva do screenshot
- Produto TOTVS Estoque/Custos, modulo `ACOMPANHA CUSTO`, breadcrumb `Fechamentos > Novo fechamento de custo`.
- Wizard visivel de quatro etapas: `Predefinicao de calculo` -> `Calculo de custo` -> `Analise e revisao` -> `Fechamento`. **A imagem apenas mostra os passos, nao comprova que foram concluidos.**
- `Ultimo fechamento realizado: 31/08/2026`.
- `Data para fechamento de custo: 30/09/2026`.
- `Metodo de apropriacao: Diaria`.
- `Filiais para calculo: Filial corrente`.
- Texto da interface: processo de fechamento de custo so pode ser realizado em datas posteriores ao ultimo fechamento.
- Acao exibida: `Proximo passo`. O screenshot captura predefinicao, nao resultado final do calculo.

### Campos e invariantes candidatos a mapear no AS-IS
| Campo | Observado | Origem/evidencia | O que NAO esta provado |
|---|---|---|---|
| Competencia fechamento | Setembro/2026, data 30/09/2026 | screenshot + PO | timezone, data de movimento efetivamente usada no calculo |
| Ultimo fechamento | 31/08/2026 | screenshot | historia de todas as filiais |
| Apropriacao | Diaria | screenshot | algoritmo do recalculo de custo medio |
| Filial | Filial corrente | screenshot | lista e quantidade de filiais processadas |
| Data TOTVS | PO relata ajuste manual ao fim do mes | OWNER_REPORTED_VIA_PO | se a rotina exige mudanca de data global em todos os cenarios |
| Job/calculo | PO relata processamento demorado, em paralelo com extracoes | OWNER_REPORTED_VIA_PO | status, logs, id do job, tratamento de falha, retentativa, lock |

### Relacao com o que ja existe no Portal
- **R01/R02 Baixas a pagar/receber**: consultas operacionais de eventos financeiros, NAO processamento de custo medio.
- **R03 P7**: consulta operacional historica SB9/SB1, NAO a rotina de fechamento e recalculo do custo medio do TOTVS; `officialP7:false`.
- **R05 MATR320, Kardex 01/99, Saldo em Processo e Em Processo**: saídas e conferencias consultadas posteriormente; NAO prova de que o Portal executa `Acompanha Custos`.
- **Implementacao em TARGET**: nenhuma automacao ou botao de fechamento de custo foi autorizado. Se houver proposta de orquestracao de job, requer owner TOTVS/api-delpi, contrato, revisao de seguranca, decisoes de negocio e gate transversal.

### Perguntas residuais objetivas (nao perguntar ao PO agora se o trecho seguinte resolver)
1. Qual status/comprovante aparece quando a etapa de `Calculo de custo` termina? Ha log, protocolo e duracao?
2. O que faz a <GESTORA-PROC> em `Analise e revisao` antes de confirmar `Fechamento`?
3. Quando ha erro de calculo ou data invalida, qual procedimento de correcao e reexecucao?
4. A data ajustada e realmente a data global/sessao de usuario, ou apenas a data de referencia da rotina? Confirmar com TOTVS e responsavel.
5. Como o recalculo de custo medio afeta P7, MATR320, Kardex e consultas de saldos, e quando cada extracao ocorre em relacao ao termino do job?

## Conclusao do registro 01
`AS_IS_STEP=OWNER_REPORTED_VIA_PO`; `TOTVS_WIZARD_FIELDS=PROVEN_SCREENSHOT`; `COST_AVERAGE_ALGORITHM=TO_INVENTORY`; `COST_CLOSING_JOB_RUNTIME=TO_INVENTORY`; `AUTOMATION_DESIGN=TARGET_NOT_APPROVED`; `ERP_PARITY=TEST_NOT_RUN`.

**Proximo registro:** continuar cronologicamente com as observacoes verbalizadas pelo PO. Evitar usar o trecho de video antigo como autoridade sobre timestamps quando o PO esta narrando outro ponto.


## Registro 02 - Custo de Reposicao, aproximadamente 03:09-03:59

**Fonte:** narracao direta do PO nesta conversa e capturas da rotina TOTVS `Custo de Reposicao [02.9.0004]`. Classificacao: `OWNER_REPORTED_VIA_PO` para finalidade e criterio de custo liquido; `PROVEN_SCREENSHOT` para campos visiveis. Nao confundir com P7.

### Primeira execucao: materiais MC ate MP (cerca de 03:11)
- <GESTORA-PROC> abre `Custo de Reposicao` > `Recalculo do Custo de Reposicao` > `Perguntas`.
- Finalidade relatada: alimentar o indicador **custo de operacao / custo operacional**. Owner, formula e integracao efetiva com indicador estrategico ainda `TO_INVENTORY`.
- Parametros vistos: `Utilizar Qual Moeda? = Nenhuma`; `Utilizar Taxa? = Diaria`; `Calcular os Custos Por? = Ult Custo Compra`; `Considerar Ult. Preco Compra? = Sim`; `Dt. Final Ref. Taxa? = 30/09/2026`; `Do Tipo do Produto? = MC`; `Ate o Tipo do Produto? = MP`.
- Outros campos visiveis: grupo inicial em branco e final alto (`zzzz`); `Considerar Qtdes. Negativa? = Nao`; `Avisar Divergencia? = Atualizar`; `Seleciona filiais? = Nao`; `Considera Mao de Obra? = Ambos`; `Considera Tipo Dec. OP? = Nao`; `Tempo Setup? = Sem Tempo Proprio`; roteiro de operacoes em branco.
- PO relata que considera **custo liquido, sem tributacoes**; a captura nao prova a regra fiscal/algoritmo, a natureza liquida ou se isso resulta especificamente do parametro de ultimo custo de compra. Status `OWNER_REPORTED_VIA_PO / TECHNICAL_FORMULA_TO_INVENTORY`.

### Segunda execucao: PA ate PI (cerca de 03:54)
- <GESTORA-PROC> reabre a rotina para outro conjunto de tipos: `Do Tipo do Produto? = PA`, `Ate o Tipo do Produto? = PI`.
- Mantem referencia ao ultimo dia do mes `30/09/2026`.
- Altera `Calcular os Custos Por? = Estrutura` (diferente da primeira execucao, que usava ultimo custo de compra). Na captura tambem permanecem `Considerar Ult. Preco Compra? = Sim`, `Utilizar Taxa? = Diaria` e demais opcoes visiveis; nao inferir que parametros nao mostrados sao iguais.
- PO relata que manda executar. Nao ha evidência do log de sucesso nem valores de saida nesta captura.
- Relacao com os dois P7 PDFs: o PO associou este recorte PA/PI ao trabalho que envia um relatorio para Financeiro, mas **Custo de Reposicao nao e MATR460/P7**. A afirmacao de identidade, derivacao do P7 ou equivalencia entre relatorios nao esta comprovada e nao deve ser implementada.

**Cuidado:** intervalo `MC..MP` ou `PA..PI` e parametro TOTVS representado por dois limites; nao assumir inclusividade alfabetica, conjunto fechado ou equivalencia a `B1_TIPO IN (...)` sem validar processamento.

## Registro 03 - Refaz Saldos e rotina de terceiros (04:36 e ~05:34)

### Refaz Saldos, aproximadamente 04:36
- <GESTORA-PROC> abre a rotina `Refaz Saldos [02.9.0004]` (identificacao visual da aba) e preenche parametros para **todos os materiais/produtos** conforme o PO.
- Campos visiveis no screenshot: `Do Armazem?` em branco / limite inicial nao legivel; `Ate o Armazem? = zz`; `Do Produto?` em branco; `Ate o Produto?` com codigo de limite superior; `Zera o saldo de produtos MOD? = Recalcular`; `Zera o CM de produtos MOD? = Recalcular`. Outros parametros podem existir fora do viewport.
- Relato do PO: executa **recalculo dos saldos**, utilizado quando ha falhas no processamento, para corrigir inconsistencias. Isso e contexto operacional relatado, **nao e prova** de garantia de correcao, idempotencia ou ausencia de impacto transacional.
- `PROVEN_SCREENSHOT` para visibilidade dos campos; `OWNER_REPORTED_VIA_PO` para finalidade; `RESULT_TEST_NOT_RUN` para comportamento efetivo.

### Refaz por DIT terceiros, citado por volta de 05:34
- PO relata que <GESTORA-PROC> **apenas cita** outra rotina, chamada por ele de `Refaz por DIT terceiros` (nome tecnico exato `TO_VERIFY`); **nao a executa nem exporta relatorio** neste trecho.
- Segundo PO/<GESTORA-PROC>, e usada esporadicamente e requer comunicacao ou alinhamento com o Financeiro, porque sua execucao **pode impedir temporariamente outras rotinas de faturamento** relacionadas a materiais em poder de terceiros.
- Contexto relatado: materia-prima fornecida pelo cliente para a DELPI fabricar o produto final (material de terceiro). A classificacao proprietaria/contratual e efeitos fiscais devem ser confirmados com owner.
- **Nao inferir bloqueio de todo faturamento**, regra de tolerancia, janela de indisponibilidade, lock SQL, agendamento automatico ou autorizacao para execucao.
- Classificacao: `CITED_ONLY / OWNER_REPORTED_VIA_PO`; execucao `TEST_NOT_RUN`; mecanismo de bloqueio `TO_INVENTORY`.
- Se houver futura proposta de acao de reprocessamento pelo Portal: `DECISION_REQUIRED` (owner ERP e Financeiro, risco operacional, lock/concorrencia, autorização explicita, fail-closed, trilha e plano de rollback). **Nao implementar agora**.

## Relacoes com o Portal e fronteiras, apos registros 02-03
| Rotina | Evidencia | Ja implementada no Portal? | Proxima verificacao |
|---|---|---|---|
| Acompanha Custos - fechamento | screenshot + relato PO | Nao; R03 consulta SB9/SB1 nao executa fechamento | estado do job, calculo e dependencia entre extracoes |
| Custo de Reposicao MC-MP / PA-PI | screenshots e relato PO | Nao; nao equivale a P7 nem indicador estrategico comprovado | owner do indicador, campos e regras do calculo |
| Refaz Saldos | screenshot e relato PO | Nao | escopo de dados alterados, autorizacao, log e idempotencia |
| DIT terceiros | somente citado por PO | Nao | nome exato e impacto de concorrencia no faturamento |
| R01/R02 e R03 | contratos/codigo ja documentados | Sim, consultas operacionais | nao misturar com comandos mutantes de estoque/custo |

## Estado deste incremento
`REPLACEMENT_COST_PARAMETERS=PROVEN_SCREENSHOT`; `REPLACEMENT_COST_USE=OWNER_REPORTED_VIA_PO`; `NET_COST_RULE=TO_INVENTORY`; `REBUILD_BALANCES_PARAMS=PROVEN_SCREENSHOT_PARTIAL`; `REBUILD_BALANCES_PURPOSE=OWNER_REPORTED_VIA_PO`; `THIRD_PARTY_ROUTINE=CITED_ONLY`; `THIRD_PARTY_LOCK_EFFECT=OWNER_REPORTED_VIA_PO/TO_VERIFY`; `IMPLEMENTATION_AUTHORIZED=NO`.

**Proximo passo de observacao:** usuario continua narrando cronologicamente; nao interpretar capturas isoladas como ordem de execucao ou conclusao de jobs.


## Registro 04 - Faturamento x MOD e conclusao observada do Refaz Saldos (06:04-06:46)

**Fonte:** narracao direta do PO ao assistir o video e quatro screenshots do TOTVS. `OWNER_REPORTED_VIA_PO` para finalidade/regras explicadas; `PROVEN_SCREENSHOT` para parametros e mensagens visiveis. Horarios aproximados do video original indicados pelo PO.

### Faturamento x MOD (aprox. 06:04-06:40)
1. <GESTORA-PROC> navega no modulo `Estoque/Custos > Relatorios > Analises > Faturamento x MOD`; a aba `Faturamento X Mod [02.9.0004]` aparece aberta na captura.
2. **Finalidade explicada pelo PO:** comparar custo esperado de mao de obra direta com o efetivamente realizado; verificar se a mao de obra cobrada corresponde ao que efetivamente foi pago/incorrido. Esta formulacao e `OWNER_REPORTED_VIA_PO`, **nao formula operacional validada**, pois a imagem nao demonstra os campos de custo calculado/pago, nem a metodologia do confronto.
3. Na janela `Parametros`, intervalo visivel `Data de? = 01/09/2026`, `Data ate? = 30/09/2026`. Filtros adicionais: `Produto Acabado de?` e `Produto Acabado Ate?` (limite superior preenchido), `Grupo De?` em branco e `Grupo Ate?` com valor `0040` aparente na captura. Nao inferir semantica dos grupos.
4. Na etapa seguinte `Selecao de Filiais` aparecem duas linhas, `01 - MATRIZ` e `02 - DELPI - UES`; contador inferior `Elem. Selecionado(s) = 2`. PO relata selecao de ambas e continuacao do processamento.
5. **Nao ha planilha gerada ou comparacao de valores provada nestas capturas**. O processo descrito aqui e parametrizacao e solicitacao do relatorio, nao calculo homologado nem exportacao.
6. O modulo `Faturamento x MOD` tambem foi mencionado no trecho posterior da gravacao (docs 54/55), em que se relatou tratamento de planilha no Excel. Correlacionar os dois pontos do processo sem inventar igualdade de bases, criterios de agrupamento ou valores.

### Refaz Saldos - retorno do processamento (aprox. 06:46)
1. <GESTORA-PROC> retorna a rotina aberta `Refaz Saldos`, janela `Recalculo dos Saldos`, e abre/visualiza o `Log de processamento das STORED PROCEDURES`.
2. A lista visivel contem varias linhas com estado textual `Processamento Thread: ... - Ok`; o PO relata que **todas terminaram OK** e ela confirma fechando a janela em `Ok`.
3. `PROVEN_SCREENSHOT` = existem linhas de threads com `Ok` naquele log. `OWNER_REPORTED_VIA_PO` = processamento concluido e usuario confirmou. **Nao equivale a** paridade financeira/estoque, verificacao pos-processamento do banco, duracao, idempotencia, transacao atomica ou ausencia de alerta em linhas nao visiveis.
4. O Refaz Saldos **nao produz exportacao neste trecho** (relato do PO); a evidencia operacional demonstrada e o log de processamento, nao um relatorio de saldos.
5. Se o Portal no futuro precisar acompanhar job, distinguir `processing`, `completed`, `failed` e o resultado de validacao de saldos: `Ok` de thread nao prova conferencia de negocio `PASS`. Proposta apenas `TARGET / DECISION_REQUIRED`.

### Campos e conciliacoes ainda a validar
| Topico | Comprovado ou relatado | Pendente |
|---|---|---|
| Escopo temporal Faturamento x MOD | Setembro/2026 inteiro, 01 a 30 (captura) | data de referencia da efetiva apuracao, competencia e timezone |
| Filiais Faturamento x MOD | 01 MATRIZ + 02 DELPI-UES selecionadas (captura) | se a consolidacao soma filiais ou mostra resultados por filial |
| Escopo MOD | mao de obra direta, custo esperado vs realizado (relato PO) | campos, formula, unidade e origem de custo pago/previsto |
| Criterio de conclusao Refaz Saldos | linhas de thread `Ok` visiveis, confirmacao manual (captura/relato) | log integral, total de threads, efeitos nas fontes e verificacao de outcome |
| Integraçao Portal | nenhuma funcionalidade de executar job/cobrar MOD existente provada neste registro | owners api-delpi/ERP e strategic-indicators-api quando aplicavel |

**Status:** `MOD_REPORT_PARAMETERS=PROVEN_SCREENSHOT_PARTIAL`; `MOD_BUSINESS_PURPOSE=OWNER_REPORTED_VIA_PO`; `MOD_FORMULA=TO_INVENTORY`; `MOD_OUTPUT=TEST_NOT_RUN`; `REBUILD_BALANCES_THREAD_LOG=PROVEN_SCREENSHOT_PARTIAL`; `REBUILD_BALANCES_SUCCESS=OWNER_REPORTED_VIA_PO`; `POST_JOB_BUSINESS_OUTCOME=INCONCLUSIVE`; `IMPLEMENTATION_AUTHORIZED=NO`.

**Proximo registro:** continuar cronologicamente a partir da fala do PO; nao reavaliar como comprovadas as formulas/conciliacoes so por existirem parametros ou logs.


## Registro 05 - Dependencias do calculo e compensacoes financeiras (07:25 a 09:18)

Fonte: narrativa do PO nesta conversa e screenshots do TOTVS. Classificar falas como OWNER_REPORTED_VIA_PO e elementos visuais como PROVEN_SCREENSHOT. Nao afirmar resultado transacional sem comprovante.

### 07:25 - Restricoes durante Acompanha Custos
<GESTORA-PROC> relata que, enquanto o processamento de fechamento de custo esta em andamento, nao consegue emitir/exportar o Kardex do armazem 01 (usado para previa de CPV), o Kardex do armazem 99 (inventario e perda de contagem) e relatorio de saldo em estoque. Aguarda a conclusao do processamento; aproveita esse intervalo para outras atividades. Mecanismo de bloqueio, API de status e lista exata de relatórios afetados ainda TO_INVENTORY. Nao inferir lock global nem dependencia contratual do Portal.

### 07:56 a 09:18 - Conferencia de titulos para compensacao
<GESTORA-PROC> acessa TOTVS Financeiro > Contas a Pagar; revisa titulos e filtros para localizar pares a compensar. PO explica a finalidade de conciliar pagamentos antecipados (PA), notas de devolucao e outros creditos/debitos. Na tela de exemplo (~08:48), dois documentos apresentam valor igual segundo o PO. Explicacao dada: houve pagamento antecipado antes de lancar a nota; depois do lancamento, precisa compensar os documentos. Nao inferir que igualdade de valor e condicao suficiente, nem que o evento final foi comprovado pela captura.

Screenshots confirmam tabela de Contas a Pagar e janelas Gerenciador de Filtros e Compensacao de Titulos, com campos de valor compensado, saldo e selecao. Caso Mercado Livre foi citado como de localizacao mais dificil, sem regra causal confirmada. Evitar publicar dados de titulos individuais.

**Fronteira:** R01/R02 hoje consultam eventos de baixas. Nao comprovam cobertura de titulos em aberto ou candidatos a compensacao e nao executam compensacao. Uma eventual lista READ-only de pendencias e TARGET / DECISION_REQUIRED, dependente de owner, campos e contrato; acao transacional no ERP NAO autorizada.

### Questões objetivas a validar
- Chaves e criterios para pareamento: tipo PA/devolucao, fornecedor/loja, documento, filial, moeda, data, saldo; compensacoes parciais, autorizacao e resultado.
- Regras especificas de identificacao dos casos Mercado Livre.
- APIs e tabelas READ existentes para titulos em aberto e adiantamentos; nao substituir com endpoint de baixas sem prova.
- Sinal verificavel de fim de Acompanha Custos e escopo preciso das extracoes bloqueadas.

Estado: KARDEX_DEPENDENCY=OWNER_REPORTED_VIA_PO; COMPENSATION_PURPOSE=OWNER_REPORTED_VIA_PO; COMPENSATION_SCREEN=PROVEN_SCREENSHOT_PARTIAL; COMPENSATION_OUTCOME=INCONCLUSIVE; MATCHING_RULE=TO_INVENTORY; ERP_WRITES=NOT_AUTHORIZED.


## Registro 06 - Emissao de titulos em aberto, pagar e receber (10:09-11:32)

**Fonte:** narracao guiada do PO nesta conversa; duas capturas do TOTVS Financeiro com janelas de impressao e parametros. `OWNER_REPORTED_VIA_PO` para comportamento/escopo descrito; `PROVEN_SCREENSHOT` apenas para rotinas e filtros visiveis.

### 10:09 - Posicao dos Titulos a Pagar
- <GESTORA-PROC> inicia a emissao de `Posicao dos Titulos a Pagar`; a rotina de impressao na captura mostra `FINR150` (leitura visual a confirmar no artefato impresso).
- Segundo o PO, o objetivo e obter **todos os titulos ainda em aberto**, incluindo vencimentos passados e futuros, **nao somente o mes de referencia**. Isso nao significa necessariamente que nao existam outros filtros do relatorio.
- Na captura a tela `Parametros` inclui filtros por natureza, vencimento e banco. O intervalo mostrado de vencimento deve ser preservado como **parametro efetivamente selecionado** quando for confirmado; nao afirmar que o relatorio contempla um universo ilimitado sem comparar o output.
- `OWNER_REPORTED_VIA_PO`: emissao iniciada; `OUTPUT_PARITY=TEST_NOT_RUN`.

### ~11:08 - Posicao dos Titulos a Receber
- <GESTORA-PROC> repete o procedimento no Contas a Receber, com janela `Posicao dos Titulos a Receber` e rotina visual `FINR130` (identificador sujeito a confirmacao em original gerado).
- A imagem revela campos de titulo, banco, vencimento e natureza. O recorte mostra filtro de vencimento na tela; nao pressupor inclusao de qualquer data fora da selecao.
- Intencao, segundo o PO: consultar posicao aberta a receber, equivalente funcional de levantamento de pendencias, com regras e filtros especificos do relatorio a validar.

### ~11:32 - Inicio de analise dos outputs
- PO informa que a Posicao dos Titulos a Pagar ja foi gerada e que <GESTORA-PROC> comeca a examinar os relatorios produzidos.
- Capturas fornecidas nao comprovam valores totais, detalhes da planilha/PDF, criterio de classificacao de vencidos/vincendos, nem desfecho de compensacao.

### Conexao com o Portal e riscos de equivalencia
- **R01/R02 atuais = eventos de baixas financeiras** (o que foi liquidado), com filtros por data de baixa, natureza e movimento; nao sao o universo de titulos abertos. Os relatorios `Posicao dos Titulos` constituem **novas fontes/visoes AS-IS para mapear**, mas nao autorizam criar endpoints ou paginas.
- Candidata futura: `Posicao Financeira em Aberto` com lado pagar/receber, vencidos/vincendos, riscos de prazo e possiveis compensacoes; **TARGET / DECISION_REQUIRED**, dependente de producer e ownership api-delpi, criterios e permission effective access/manage conforme contrato do produto.
- A janela de impressao com periodo selecionado nao comprova universo completo historico; conferir documento original e parametros gravados. Nao inventar totais.
- Manter **compensacao**, **baixa** e **posicao em aberto** como tres conceitos financeiros distintos.

### Pendencias objetivas
1. Obter PDF/Excel original da Posicao dos Titulos a Pagar e a Receber ou seu layout/colunas e filtros efetivos.
2. Confirmar `FINR150` e `FINR130` e variacoes customizadas do ambiente.
3. Verificar regra de aberto: saldo parcial, titulos vencidos/futuros, antecipacoes, notas de devolucao, filiais e datas de referencia.
4. Identificar leitura canonica em api-delpi/Protheus antes de qualquer proposta de comparacao com baixas R01/R02.
5. Seguir a narracao apos ~11:32 e capturar quais comparacoes <GESTORA-PROC> realmente faz com os outputs.

Estado: `PAYABLE_OPEN_TITLES=OWNER_REPORTED_VIA_PO`; `RECEIVABLE_OPEN_TITLES=OWNER_REPORTED_VIA_PO`; `PRINT_DIALOGS=PROVEN_SCREENSHOT_PARTIAL`; `PRINTED_CONTENT=TO_INVENTORY`; `R01_R02_PARITY=NOT_ESTABLISHED`; `IMPLEMENTATION_AUTHORIZED=NO`.


## Registro 07 - Relacao de baixas DELPI e revisao do custo medio (12:48-16:57)

**Proveniencia:** descricao oral do PO durante revisao do video e quatro capturas TOTVS. `OWNER_REPORTED_VIA_PO` para explicacoes de <GESTORA-PROC> narradas pelo PO; `PROVEN_SCREENSHOT` para mensagens e campos visiveis. Nao usar como prova de paridade de dados. Capturas do erro TOTVS e dos passos do Acompanha Custos sao artefatos de evidencia do dialogo; nao armazenar credenciais ou identificadores de usuario no repo.

### 12:48-13:52 - Relacao de Baixas DLP e limitacao do ambiente
- <GESTORA-PROC> tenta abrir a rotina DELPI `Relacao de Baixas DLP [02.9.0006]`, descrita pelo PO como reunindo movimentacoes de baixas do Financeiro, tanto pagar quanto receber, com contraparte fornecedor/cliente e identificacao CNPJ.
- A tentativa da gravacao falha. Captura apresenta `Help: NO_IX`, com texto de que uma funcao de usuario nao esta compilada no repositorio. Em outra captura, a Central de Diagnostico identifica a rotina `U_FINR190C` (leitura visual; confirmar no codigo customizado) com estado `Nao configurado`; nao inferir que o erro inteiro decorre somente desse campo.
- **Nao houve geracao de output da Relacao de Baixas DLP neste trecho**; `REPORT_OUTPUT=TEST_NOT_RUN` / `ERROR=PROVEN_SCREENSHOT`. Nao chamar a rotina de FINR190 padrao sem verificacao.
- Segundo PO/<GESTORA-PROC>, o relatorio configurado especificamente para DELPI combina **cinco saidas** usadas pela Aliance, parceira terceirizada da Controladoria, para importacao em sua ferramenta:
  1. Excel de Contas a Pagar;
  2. Excel de Contas a Receber;
  3. PDF de Contas a Receber por data;
  4. PDF de Contas a Pagar por data;
  5. PDF de Contas a Pagar por natureza de operacao.
- A fala relata que essas saidas permitem compor a informacao consolidada; **nao comprova** que sejam um `UNION` simples, que tenham o mesmo granulo/linhas nem as chaves e o layout de importacao da Aliance. O PDF/Excel real do ultimo fechamento, mapeamento campo a campo, duplicidades, competencias, filtragem e parametrizacao estao `TO_INVENTORY`.
- Relacao com Portal: R01/R02 ja consultam **eventos de baixas financeiras** via BFF, portanto ha fonte candidata reutilizavel para analise READ. Contudo `R01_R02_TO_DLP_PARITY=TEST_NOT_RUN`; CNPJ no payload, abrangencia de todas as naturezas, cinco saidas e layout da importacao nao estao comprovados. **Nao adicionar CNPJ por inferencia nem exportacao do universo inteiro sem contrato e gate.**
- Diferenca para Registro 06: Posicao dos Titulos em aberto (FINR150/FINR130 provisoriamente) **nao equivale** a Relacao de Baixas DLP; tampouco a compensacao de titulos e a mesma transacao que uma baixa.

### ~16:00-16:57 - Acompanha Custos: calculo 100% e revisao ainda aberta
- Captura da etapa **Calculo de custo** do assistente TOTVS mostra barra **100%**, com marcacoes `Niveis validados`, `Arquivo de trabalho montado`, `Transferencias entre filiais processadas` e `Analise das movimentacoes concluida`, alem do botao `Proximo passo`. Isso evidencia **conclusao visual desta etapa**, nao confirmacao do fechamento mensal.
- Apos avancar, tela **Analise e revisao** apresenta tabela por filial, codigo de produto, tipo, grupo, armazem, custo medio inicial, custo medio final e variacao percentual, com status (como POSITIVO), busca, opcao de exportar e acao `Refazer calculo`. Um texto de pagina menciona `Mostrando 10 de 1991 produtos em custo medio do periodo` na captura.
- Segundo PO/<GESTORA-PROC>, as variacoes de custo medio precisam ser avaliadas antes de concluir; **ela nao avanca para a etapa final de Fechamento naquele momento**, porque ainda ha outras conferencias a realizar.
- Nao interpretar status `POSITIVO` da linha como aceite ou ausencia de discrepancia, nem o percentual variacao como erro automatico; limiares, resultados e criterios humanos ainda `TO_INVENTORY`.
- **Distincao fundamental:** processamento do custo medio completo (100%) != analise/revisao homologada != fechamento mensal confirmado. Qualquer proposta futura no Portal deve manter esses tres estados separados, sem executar comando TOTVS de fechamento sem autorizacao especifica.

### Mapa de verificacoes proximas
| Item | Evidencia atual | O que falta |
|---|---|---|
| `U_FINR190C` DELPI | screenshot de diagnostico e falha `NO_IX` | owner do fonte customizado, versao, regra/rotina e motivo preciso de indisponibilidade |
| Cinco exportacoes Aliance | relato PO | arquivos originais do ultimo fechamento, filtro, campo, relacao entre formatos, contrato de ingestao |
| R01/R02 vs relatorio DELPI | endpoints operacionais implementados | prova campo a campo e reconciliacao de totais/linhas com cinco saidas |
| Calculo custo | etapa 100% e checks visiveis | resultado de job, historico e contrato de consulta |
| Analise/revisao custo medio | tabela e variacoes visiveis | criterios de excecao, tolerancias e resultado humano por competencia |
| Fechamento definitivo | ainda nao observado neste registro | sequencia e comprovante da confirmacao final |

### Status
`DELPI_DLP_REPORT=OWNER_REPORTED_VIA_PO`; `DLP_RUNTIME_FAILURE=PROVEN_SCREENSHOT`; `CUSTOM_ROUTINE_ID=PROVEN_SCREENSHOT_PARTIAL`; `DLP_FIVE_OUTPUTS=OWNER_REPORTED_VIA_PO`; `DLP_SQL_PARITY=TEST_NOT_RUN`; `COST_CALC_STAGE_100=PROVEN_SCREENSHOT`; `COST_REVIEW_SCREEN=PROVEN_SCREENSHOT`; `COST_CLOSING_COMPLETED=NOT_PROVEN`; `IMPLEMENTATION_AUTHORIZED=NO`.


## Registro 08 - Retorno ao Estoque/Custos, P7, Kardex e movimento/processo (17:10-21:53)

**Fonte:** narracao orientada pelo PO e capturas TOTVS associadas aos marcadores de tempo ~17:39, 17:57, 18:43, 19:00, 19:04, 19:08, 19:19, 19:49, 20:28, 20:41, 21:05 e 21:42. Classificacoes `OWNER_REPORTED_VIA_PO` (finalidade/explicacao) e `PROVEN_SCREENSHOT` (campos e interfaces). Este trecho continua o Registro 07: calculo de custo 100%, porem revisao/fechamento definitivo ainda nao demonstrado. <GESTORA-PROC> alterna rotinas visando otimizar tempo; uma aba aberta nao comprova output concluido.

### Sequencia com procedencia e limites de prova
| Tempo aproximado | Rotina/acao | Fato visivel ou relato | Estado |
|---|---|---|---|
| 17:10 | Retorna de Financeiro a Estoque/Custos | PO relata alternancia para aproveitar o tempo de extracao | OWNER_REPORTED_VIA_PO |
| 17:47-17:57 | Registro de Inventario - Modelo P7, impressao `MATR460` | Primeiro P7 padrao, para propria analise: saldo de estoque na data-base 30/09/2026. PO relata exclusao de materiais em poder de terceiros. Captura mostra parametros de armazem/produto, `Produtos Sem Movim.? Nao`, `Prods. c/ Saldo Neg.? Sim` | MIXED; parametrizacao completa TO_VERIFY |
| ~18:00-18:43 | Segundo P7, layout Bloco H para contabilidade | PO relata recorte MP/PI/PA e exclusao de material de consumo, a partir do mesmo processo de inventario P7; duas abas P7 visiveis | OWNER_REPORTED_VIA_PO; layout/filtros exatos pendentes |
| 18:53-19:49 | Movimentacoes Kardex Diario - Padrao, janela `Kardex Fisico-Financeiro (DIA)`, impressao `MATR910` | Duas emissoes destinadas aos armazens 01 e 99. Capturas mostram periodo 01/09/2026 a 30/09/2026 em quadro final; `Lista Prods S/Movim.? Nao`, `Qual Armazem? 01` em quadro, `Saldo a considerar? Atual`, export `Planilha / MS Excel` | PROVEN_SCREENSHOT_PARTIAL + OWNER_REPORTED_VIA_PO |
| ~20:00 | Uso dos Kardex | 01 = conferencia CPV; 99 = inventario/perdas de contagem; inventarios em outros armazens sao raros, segundo PO/<GESTORA-PROC> | OWNER_REPORTED_VIA_PO; formulas ainda nao validadas |
| 20:28-21:05 | Consulta `Saldo Em Processo`, separada da aba `Em Processo` | Pesquisa TOTVS e Smart View com opcao de visao/tabela dinamica. Janela de `Saldo em Processo (Analitico)` mostra `MATR989`, data de fechamento 30/09/2026, `Lista MOD em Processo? Nao`, `Verif Sld Processo? Data de Emissao`, `Lista Custo? Medio`, `Considera armazem processo? Sim` | PROVEN_SCREENSHOT_PARTIAL |
| 21:20-21:42 | `Resumo das Entradas e Saidas` / MATR320 | Emitido com periodo 01/09/2026 a 30/09/2026, `Moeda=1a Moeda`, `Saldo a considerar=Movimento`, `Considera Saldo MOD=Nao`; parametros visiveis em captura | PROVEN_SCREENSHOT; valores originais ja no doc 46 |
| 21:53 em diante | Saidas comecam a ficar prontas; <GESTORA-PROC> passa a explicar seu uso | PO relata mudanca de etapa: de preparacao/exportacao para conferencia e analise dos arquivos | OWNER_REPORTED_VIA_PO; regras especificas nos proximos registros |

**Cronologia corrigida pelo PO:** a referencia anterior a 22:24 foi erro de digitacao; a extracao de materiais em processo deve ser situada em torno de **21 minutos**, coerente com as capturas de `Saldo em Processo` (~20:41-21:05). Esta correcao substitui a divergencia temporal antes apontada; `Em Processo` e `Saldo Em Processo` continuam rotinas/abas distintas. `Em Processo` e `Saldo Em Processo` aparecem em abas diferentes, portanto nao devem ser unificados sem contrato.

### Distincoes funcionais
- **P7 padrao**: fotografia do estoque historico para conferencias internas; **P7 Bloco H**: recorte e layout usado para contabilidade. Nao presumir que os conjuntos sao exatamente iguais aos filtros operacionais `all_products` / `mp_pi_pa` ja presentes no R03. As duas saidas nao sao dois calculos identicos por padrao.
- **Kardex MATR910 01/99**: movimentacoes detalhadas por armazem, com referencia de periodo; nao e MATR320, que agrega entradas/saidas. CPV e perdas por inventario sao usos de conferencia, nao somatorios homologados ainda.
- **Saldo em Processo MATR989 / Smart View**: exibicao/corte proprio (data, MOD, custo medio e armazem de processo); `Em Processo` existe separadamente. A paridade entre as visoes nao foi demonstrada.
- **MATR320**: impresso R05 original no doc 46; o proprio nome `Entradas e Saidas` nao autoriza chamar a saida de Kardex.
- **Dependencia**: relatada anteriormente: <GESTORA-PROC> aguarda termino de `Acompanha Custos` para emitir Kardex e alguns saldos. Aqui o inicio das emissoes depois da tela de calculo 100% e **consistente** com o relato, mas nao prova mecanismo de bloqueio.
- **Portal hoje**: R03 exibe extracao operacional SB9/SB1 historica, nao a rotina MATR460 nem exportacao Bloco H; R01/R02 baixas financeiras nao executam conciliacao dos relatorios de estoque. Nada foi implementado neste registro.

### Parametros para confrontar com originais
| Fonte | Parametros visiveis | Incerteza remanescente |
|---|---|---|
| MATR460 P7 | data-base ultimo dia do mes relatada; recorte armazem/produto e flags parcialmente visiveis | terceiros, MP/PI/PA, Bloco H, periodo, filial, layout impresso e soma |
| MATR910 Kardex | periodo 01-30/09, armazem 01 em quadro, formato Excel, `Saldo Atual`, sem produtos sem movimento | confirmar parametros de armazem 99, filtro fiscal/ITENS, sinal dos valores, ordenacao e output |
| MATR989 Saldo em Processo | 30/09, MOD Nao, custo Medio, considera armazem processo Sim | indicadores, escopo OP, produtos e consistencia com `Em Processo` |
| MATR320 | 01-30/09, primeira moeda, saldo Movimento, MOD Nao | regras de sinal, origem e divergencias com P7 |

### Gate para a proxima parte da narracao
A partir de 21:53, capturar **regra demonstrada** no Excel ou tela com operacao, filtros, sinais, colunas e totais; separar relato oral da formula reproduzivel. Nao criar nova pagina para cada relatorio. Confrontar inventario dos docs 46/54/55 e preservar divergencias explicitas. Sem decisao de arquitetura, contrato, owner ou runtime novo.

**Resultado:** `AS_IS_EXTRACTION_SEQUENCE=DOCUMENTED_PARTIAL`; `P7_DUAL_LAYOUTS=OWNER_REPORTED_VIA_PO`; `KARDEX_PROGRAM=MATR910_PROVEN_SCREENSHOT`; `MATR989=PROVEN_SCREENSHOT`; `MATR320=PROVEN_ORIGINAL`; `FORMULAS_RECONCILIATION=INCONCLUSIVE`; `TARGET_CONSOLIDATED_PAGE=DECISION_REQUIRED`; `IMPLEMENTATION_AUTHORIZED=NO`.


## Registro 09 - Conferencia de inventario, Kardex armazens 01 e 99 (21:56-23:33)

**Proveniencia:** explicacao guiada do PO nesta conversa, capturas da extracao Excel e da manipulacao das planilhas pela <GESTORA-PROC>. `PROVEN_SCREENSHOT` somente para campos, numeros e formula visiveis; `OWNER_REPORTED_VIA_PO` para interpretacao de negocio e encaminhamento; SQL `TEST_NOT_RUN`. Nao inferir total conciliado no ERP.

### Sequencia operacional documentada
1. Por volta de 21:56, <GESTORA-PROC> abre os dois arquivos exportados de `Kardex Fisico-Financeiro (DIA)`: armazem 01 (associado tambem ao CPV) e armazem 99 (inventario). Capturas mostram planilhas Excel com movimentos, coluna `DOCUMENTO NUMERO`, `ENTRADAS CUSTO`, `SAIDAS CUSTO` e outros campos.
2. No arquivo de inventario, filtra `DOCUMENTO NUMERO = INVENT`. Repete a selecao no outro armazem e consolida registros filtrados dos dois em uma planilha de trabalho. Os headers impressos no Excel podem ser aliases do relatorio; nao presumir nomes fisicos das tabelas TOTVS.
3. <GESTORA-PROC> soma os valores de custo das **entradas** e das **saidas** para os registros selecionados, sem confundir as colunas de quantidade com valor.
4. No minuto ~23:13, a formula de planilha observada e `=F251-I251` (entradas menos saidas no layout de trabalho). Resultado negativo, interpretado como perda/prejuizo de inventario pela <GESTORA-PROC>.
5. Por volta de 23:33, salva a planilha `99 inventarios` em compartilhamento da Controladoria para envio/consulta posterior pelo Financeiro/Controladoria. A imagem comprova o dialogo de salvamento, nao comprova posterior envio nem retencao.
6. PO indica `SD3010` como tabela de origem citada na gravacao. Tratar como **`SOURCE_REPORTED / TO_VERIFY`**: confirmar owner Protheus, joins, campos de filial/local, identificador INVENT, natureza da movimentacao e custo pela fonte canonica; nao confundir com `SD3` geral ou nomes de coluna do Excel.

### Valores reproduziveis no Excel observado (setembro/2026)
| Medida | Valor mostrado na planilha |
|---|---:|
| Soma de entradas (custo) | 1.650.614,61 |
| Soma de saidas (custo) | 1.707.796,41 |
| Diferenca entradas - saidas | **-57.181,80** |

Esses numeros e a formula sao `PROVEN_SCREENSHOT` **na planilha editada**. Nao provam independentemente que todas as linhas de ambos armazens estavam selecionadas, que a classificacao de perdas e contabilmente homologada, nem paridade com relatorio mensal/SQL. A frase perda/prejuizo e `OWNER_REPORTED_VIA_PO`; sinal negativo e aritmetica sao verificaveis.

### Correspondencia com o que ja existe no Portal
- R03 P7/SB9+SB1 apresenta fotografia historica operacional; nao fornece o universo de movimentos `INVENT` do Kardex, portanto **nao calcula a perda identificada aqui**.
- R05 MATR320 resume categorias de entradas e saidas; nao substitui movimentos detalhados Kardex 01/99. Nao supor igualdade direta com -57.181,80.
- Consulta consolidada de inventario seria `TARGET`: competencia, filial, armazem, evento INVENT, valor de entradas/saidas, diferenca, identificadores de origem, filtros e versao de extracao; detalhes de auditoria devem permitir rastrear linhas e sinais. Persistencia no Portal, contratos, owners e criterios de aprovacao sao **`DECISION_REQUIRED`**; nao implementar automaticamente.
- A pasta compartilhada do Financeiro/Controladoria e evidencia de atividade humana, nao API nem autorizacao para ingerir arquivos sem contrato.

### Verificacoes pendentes antes de automatizar
1. Confrontar dados originais dos dois Kardex com filtros exatos e total de movimentos de cada armazem, evitando duplicacoes na juncao.
2. Confirmar tabela/alias fisico `SD3010` com DAVI/owner `api-delpi` e mapear entradas, saidas, custo, sinais, competencia, filial, local, documento e tipo de movimento.
3. Recalcular separadamente 01 e 99 e depois o conjunto, explicando -57.181,80 com precisao e regra de arredondamento.
4. Confirmar se todo `INVENT` faz parte da perda e se existem classificacoes, ajustes ou excecoes antes da contabilizacao.
5. Confirmar owner do resultado, regra de aceite, armazenamento e retencao da evidencia.

**Resultado:** `INVENTORY_WORKFLOW=DOCUMENTED_PARTIAL`; `INVENT_FILTER=PROVEN_SCREENSHOT`; `EXCEL_FORMULA=PROVEN_SCREENSHOT`; `EXCEL_NET_LOSS=-57181.80_OBSERVED`; `SD3010_ORIGIN=SOURCE_REPORTED_TO_VERIFY`; `SQL_PARITY=TEST_NOT_RUN`; `PORTAL_IMPLEMENTATION=TARGET_DECISION_REQUIRED`.

**Proximo marcador da gravacao: 23:33**, aguardando a continuidade da narracao do PO.


## Registro 10 - CPV do Kardex 01, materiais de terceiros e arquivamento (aprox. 23:46-25:46)

**Proveniencia:** relato do PO durante reproducao e capturas de tela Excel e `Salvar como`. `PROVEN_SCREENSHOT` para filtros, campo destacado e arquivos visiveis; `OWNER_REPORTED_VIA_PO` para regra operacional e interpretacao; `TO_INVENTORY` para classificacao tecnica de terceiros e formula canonica. Este registro continua o Registro 09; nao presume que os mesmos filtros/arquivos sejam usados em toda competencia.

### Conferencia de materias-primas de terceiros
1. Depois de salvar a conciliacao de inventarios, <GESTORA-PROC> retorna a planilha `cpv 09 26 matriz`, proveniente do Kardex do armazem 01.
2. PO relata que verifica produtos e materias-primas **em poder de terceiros / fornecidos pelo cliente** usados na estrutura de um produto acabado; nesses casos, ela espera **ausencia de custo proprio** na parcela de material do cliente, para nao inflar o CPV. A formulacao deve ser validada quanto a propriedade, tipo de movimento e custeio; **nao afirmar que todo custo de um PA contendo insumo de terceiro deva ser zero**.
3. A conferencia ocorre hoje parcialmente por experiencia da executora (relato `feeling`). Capturas mostram uso de `Localizar e substituir` por um codigo de produto e linhas correspondentes no Kardex; ha exemplo de registro que, segundo PO, aparece indevidamente, atribuido a falha/parametrizacao TOTVS. **Bug de ERP nao comprovado por RCA**: registrar como ocorrencia a investigar, sem alterar base ou descartar movimentos automaticamente.
4. Candidato de verificacao READ no futuro: produto -> estrutura/BOM -> componentes -> indicador canonico de material do cliente/terceiros -> custo do movimento, exibindo excecoes, sinais, competencia, armazem, identificadores e justificativa. **Nao confundir identificacao em cadastro SB1 com prova de propriedade juridica, nem assumir estrutura historica atual = estrutura vigente em 09/2026.** Producer/contract/owner `TO_INVENTORY`.

### Filtro fiscal do CPV e coluna de calculo
1. PO cita os codigos `5101`, `5124`, `6101` e `6124`. A captura da planilha, ao filtrar a coluna `C.F`, mostra entradas como `5101`, `6101` e codigos de TES como `501`/`614` em coluna adjacente; **nao confundir TES com CFOP** e nao promover conjunto como canonico antes de confirmar os quatro codigos no relatorio/ERP.
2. <GESTORA-PROC> seleciona e soma **`SAIDAS CUSTO`** do Kardex 01 para movimentos correspondentes ao filtro fiscal. A captura com coluna selecionada e barra de status do Excel confirma a operacao de soma, mas **nao constitui apuracao definitiva do CPV**; tratamento de devolucoes, estornos, terceiros, periodizacao, custos zerados e arredondamento continua nao verificado.
3. A planilha `cpv 09 26 matriz` e arquivada na pasta da competencia. A captura mostra arquivo previamente salvo e procedimentos posteriores de salvamento/exportacao; nao declarar que esse proprio arquivo seja a fonte oficial contabil final.

### Relação com indicador CPV ja existente na Minha DELPI
PO informa que existe calculo de CPV em dashboard de **Suprimentos**. Isso e uma **pista de reutilizacao**, nao prova de que o mesmo escopo, periodo, filtros, sinal, custo medio e tratamento de terceiros reproduzam a soma usada por <GESTORA-PROC>. Verificar no GitHub o producer/contract e testes do dashboard e confrontar com a conferencia manual. Nao importar domain/application de outro bounded context e nao copiar SQL sem authority `api-delpi`.

### Arquivamento de evidencias
- Captura mostra estrutura de diretorios `Fechamentos > Componentes > Matriz > 2026 > 09 Set`, com subpasta `Financeiro`; arquivos `99 inventarios` e `cpv 09 26 matriz` aparecem salvos. Esse caminho e apenas evidencia de pratica humana, **nao contrato de armazenamento no Portal**.
- Em ~25:46, <GESTORA-PROC> salva tambem o arquivo `TITULOS A RECEBER` na subpasta Financeiro; capturas mostram o dialogo de salvar com nome de arquivo, nao comprovante de envio a terceiros.
- Para eventual trilha de auditoria digital: competencia, unidade/filial, fonte, versao de extracao, filtros, resultado, operador, data de geracao e identificador do artefato, conforme decisao de owner e retention policy. Nao automatizar persistencia neste gate documental.

### Matriz de verificacao dirigida
| Questao | Evidencia | Resultado atual |
|---|---|---|
| CFOPs 5101, 5124, 6101, 6124 | Relato do PO, `C.F` na captura com 5101/6101 | `DOCUMENTED_PARTIAL`; conjunto completo `TO_VERIFY` |
| Valor usado para CPV | Coluna `SAIDAS CUSTO` selecionada para soma | `PROVEN_SCREENSHOT` operacao; formula e total reconciliado `INCONCLUSIVE` |
| Materiais de clientes/terceiros | Explicacao PO, busca por produto no Kardex | `OWNER_REPORTED_VIA_PO`; estrutura historica e propriedade `TO_INVENTORY` |
| Registro anomalo | Exemplo localizado em planilha, interpretado pela <GESTORA-PROC> | `INCONCLUSIVE` causa e impacto |
| Indicador CPV Suprimentos | Informacao PO | `TO_INVENTORY` comparacao de contrato e formula |
| Salvamentos | Arquivos de inventario/CPV e nome `TITULOS A RECEBER` visiveis | `PROVEN_SCREENSHOT_PARTIAL`; envio `NOT_PROVEN` |

**Estado:** `KARDEX01_CPV_METHOD=DOCUMENTED_PARTIAL`; `THIRD_PARTY_COST_CHECK=OWNER_REPORTED_VIA_PO`; `FISCAL_FILTER=TO_VERIFY`; `CPV_SQL_PARITY=TEST_NOT_RUN`; `SUPPLY_DASHBOARD_REUSE=TO_INVENTORY`; `PORTAL_AUDIT_PERSISTENCE=TARGET_DECISION_REQUIRED`; `IMPLEMENTATION_AUTHORIZED=NO`.

**Proximo marcador da gravacao: apos ~25:46.**


## Registro 11 - Conferencia de mao de obra direta (MOD), 26:25-29:54

**Fonte e precedencia:** narrativa do PO acompanhando a gravacao e quatro capturas de Excel. Os valores visiveis e operacoes de selecao sao `PROVEN_SCREENSHOT`; finalidade, circulacao entre areas e eventual uso em indicadores sao `OWNER_REPORTED_VIA_PO`. O tema e continuidade da rotina `Faturamento x MOD` registrada em ~06:04; nao foi homologada identidade de todas as saidas no mesmo layout.

### Evidencia operacional
- <GESTORA-PROC> abre a planilha de estrutura/custos, com abas `1-FI01` e `2-FI02` para filiais. Colunas visiveis: `PA`, `Seq Comp`, `Cod Produto`, `Desc Produto`, `Qtd Fat.`, `Quantidade`, `Custo Unitario`, `Custo Total`, `Custo Produto` e `Horas`.
- As linhas incluem produtos acabados e componentes com codigos `MOD...`, descritos como `MAO DE OBRA DIRETA...`, indicando que a planilha associa componentes de mao de obra a produtos/estruturas.
- Segundo PO, <GESTORA-PROC> seleciona/filtra itens de mao de obra direta e soma `Custo Total`; uma captura do Excel mostra `Soma: 172.001,37` na barra de status da selecao. **Classificacao: valor observado na selecao, nao total conciliado nem formula DRE homologada.** Confirmar quais abas, filtros e linhas estavam incluidas no intervalo da soma; nao multiplicar ou somar novamente pelo numero de pecas sem regra canonica.
- <GESTORA-PROC> relaciona a conferencia a custo esperado vs custo realizado/pago na operacao fisica, conforme relato do PO. As capturas nao mostram sistema de folha/pagamento, apontamentos realizados ou reconciliacao entre previsto, executado e pago; **a correspondencia de cada conceito ainda `TO_INVENTORY`**.
- PO relata conversao manual de valores numericos importados como texto e travamento do Excel antes de prosseguir no salvamento. Isso e friccao de formato de exportacao, nao regra de negocio a reproduzir no Portal. Nao declarar arquivo final como salvo a partir das capturas deste trecho.
- Por volta de 29:30, <GESTORA-PROC> comenta que deveria ter verificado tambem os valores do fechamento de custos ao arquivar os Kardex. Isso reforca um **check de conferencia de valores anterior ao aceite final**, mas sem criterios ou tolerancias comprovados.
- Este registro termina em ~29:54. Eventuais retomadas posteriores da conferencia de MOD deverao ser vinculadas a este registro, sem presumir fechamento conclusivo.

### Circulacao de informacao e oportunidade transversal fora do escopo atual
PO descreve o fluxo atual **<GESTORA-PROC> -> DRE/Controladoria -> Fabiano -> preenchimento manual de indicadores no Google Sheets de Producao -> dashboards**. A identidade do indicador, dono da planilha, formula, fontes, periodicidade e correspondencia com a soma `172.001,37` **nao foram verificadas em codigo ou contrato**.
- Hipotese `TARGET / CROSS_CONTEXT_DISCOVERY`: substituir, quando comprovada a mesma metrica, a digitacao manual por um producer canonico de dados e integracao via contrato, respeitando boundaries. **Nao escrever direto no dashboard, nao usar Google Sheets como banco de integracao e nao transferir formula para este Portal por copia.**
- `strategic-indicators-api` preserva ownership das metas/indicadores estrategicos quando aplicavel; `api-delpi` preserva regras SQL/Protheus; identificar owner real do dashboard de Producao. Backends se integram por HTTP/evento/contrato, sem imports de domain/application entre contextos.
- Pesquisa textual no GitHub nesta rodada, por `mao de obra direta`, `custo MOD`, `MOD producao`, `indicadores producao`, `MOD` e `laborCost`, **nao retornou resultado indexado**. `SEARCH_MISS != ABSENCE`: nao declarar que nao ha indicador, API ou integracao. **Verificacao documental e de codigo do owner continua PENDING.**
- Descoberta registrada para revisao em padroes de desenvolvimento: sempre mapear indicador manual -> fonte canonica -> contrato -> consumer -> parity/evidencia antes de sugerir duplicacao de dados ou eliminacao de entrada manual. Esta observacao nao altera o padrao oficial congelado nem concede autorizacao de implementacao.

### Afericao pendente para eventual implementacao
1. Obter arquivo Faturamento x MOD original e comprovante da filtragem de `MOD` por filial, produto, sequencia e periodo; reconciliar soma de 172.001,37 com definicao contábil.
2. Especificar se o valor corresponde a MOD planejada, custo da estrutura, custo apontado, valor faturado ou efetivamente pago; separar claramente metrica e bases.
3. Identificar dashboard(s) Producao, origem Google Sheets e contrato de leitura (owner, metrica, competencias, formula).
4. Confirmar se consulta existente na `api-delpi` entrega esses campos, sem replicar semantica entre contextos.
5. Definir criterios do check de fechamento referido pela <GESTORA-PROC> em 29:30 e qual evidencia valida seu aceite.

**Estado:** `MOD_STRUCTURE_EXCEL=PROVEN_SCREENSHOT`; `MOD_SELECTED_SUM_172001_37=PROVEN_SCREENSHOT_PARTIAL`; `MOD_BUSINESS_INTERPRETATION=OWNER_REPORTED_VIA_PO`; `MOD_DRE_PRODUCTION_SHEETS_FLOW=OWNER_REPORTED_VIA_PO`; `PRODUCTION_DASHBOARD_MAPPING=TO_INVENTORY`; `TECHNICAL_PARITY=TEST_NOT_RUN`; `IMPLEMENTATION_AUTHORIZED=NO`.

**Proximo marcador da gravacao: 29:54.**


### Complemento ao Registro 11 - Filtro MOD e recorte mensal (captura ~27:54)

**Esclarecimento do PO:** a emissao do relatorio considera o periodo **do primeiro ao ultimo dia do mes de referencia**. Para analisar **Mao de Obra Direta (MOD)**, <GESTORA-PROC> usa o filtro da coluna **`Cod Produto`** e seleciona os componentes/codigos `MOD` (familia de codigos que incluem `MOD393` na captura).

**Evidencia de tela:** planilha com abas `1-FI01` e `2-FI02`, colunas `PA`, `Seq Comp`, `Cod Produto`, `Desc Produto`, `Qtd Fat`, `Quantidade`, `Custo Unitario`, `Custo Total`, `Custo Produto` e `Horas`. Na captura, `Cod Produto=MOD393` aparece com descricao `MAQUINA DE CORTE WL603`; selecao de colunas numéricas do Excel aparece destacada. **O destaque numérico nao prova por si so que toda a selecao e exclusivamente MOD, nem a soma do subconjunto.** A coluna `Quantidade` apresenta valores mistos/textuais como `HR 14,22`; nao converter essa friccao de Excel em regra de negocio.

**Regra de conferencia a reproduzir, sujeita a owner:** competencia mensal + filial + componentes classificados como MOD pela autoridade do cadastro/estrutura + agregacao da medida de custo homologada. O filtro textual por prefixo `MOD` e `OWNER_REPORTED_VIA_PO` como procedimento humano; **nao homologar prefixo como criterio tecnico exclusivo** sem verificar classificacao canonica e historico de estrutura. Nao confundir `Custo Total`, `Custo Produto` e `Horas`.

**Verificacao ainda aberta:** confrontar intervalo exato filtrado e medida somada com a captura anterior de `172.001,37`. A captura deste complemento mostra outra selecao/contagem no Excel; seus totais nao substituem automaticamente o valor observado antes.

Estado: `MOD_MONTH_RANGE=OWNER_REPORTED_VIA_PO`; `MOD_PRODUCT_COLUMN=PROVEN_SCREENSHOT`; `MOD_PREFIX_FILTER=OWNER_REPORTED_VIA_PO`; `MOD_TOTAL_RECONCILIATION=INCONCLUSIVE`; `IMPLEMENTATION_AUTHORIZED=NO`.


## Registro 12 - Conciliacao cruzada MATR320 x P7 completo x Saldo em Processo (30:00-32:21)

**Fonte:** narracao guiada do PO e capturas da gravacao: Excel `matr989` (Saldo em Processo, aba `01-01 - Saldo em Processo (Ana...)`), preview `SIGA/MATR320` e preview do Registro de Inventario P7. Este registro **nao** certifica paridade de tres fontes no banco.

### Finalidade e sequencia AS-IS
- <GESTORA-PROC> usa **Saldo em Processo** para identificar valores de materiais/operacoes que ficaram pendentes de apontamento no fechamento.
- A conferencia de estoque envolve **tres relatorios distintos**: **Resumo das Entradas e Saidas (MATR320)**, **P7 completo (sem o recorte Bloco H)** e **Saldo em Processo Analitico (MATR989)**. Nao trocar o P7 completo pelo P7 de MP/PI/PA destinado a contabilidade.
- Ela compara o total de Entradas e Saidas com o P7, procura explicar parte do delta com o saldo em processo e, quando nao fecha, investiga parametrizacao, classificacoes, movimentos e apontamentos. Atribuir todo delta a falta de apontamento **nao esta comprovado**.
- Segundo PO, essa investigacao consome parte substancial do tempo e pode exigir nova execucao das rotinas e novas exportacoes. Materiais de consumo e parametros diferentes sao **hipoteses explicitamente relatadas**, nao causa-raiz confirmada.

### Numeros observados na tela (competencia 09/2026)
| Origem | Medida/valor visto | Estado |
|---|---:|---|
| MATR320 - Resumo Entradas e Saidas, filial MATRIZ, 01/09-30/09 | Saldo Atual / Total Geral **3.890.247,177** (exibicao do relatorio; ~3.890.247,18 com 2 casas) | `PROVEN_SCREENSHOT` |
| P7 Registro de Inventario, estoque existente em 30/09/2026 | Total Geral **3.776.994,69** | `PROVEN_SCREENSHOT` |
| Diferenca MATR320 - P7 | **113.252,49** arredondada a 2 casas | `DERIVED_FROM_SCREENSHOTS` |
| MATR989 Saldo em Processo, Excel selecionado na coluna de valor | Barra de status **Soma: 64.968,42** sobre selecao filtrada; screenshot indica `1577 de 57409 registros localizados` | `PROVEN_SCREENSHOT_PARTIAL` |
| Diferenca menos valor selecionado MATR989 | **48.284,07** (113.252,49 - 64.968,42), apenas subtracao exploratoria | `DERIVED_NOT_RECONCILED` |
| Outro valor na planilha de trabalho, proximo da linha 57420 | **48.284,06** aparece nitidamente no recorte ampliado fornecido pelo PO; a formula nao esta visivel | `PROVEN_SCREENSHOT_UNEXPLAINED` |

**ALERTA DE CONSISTENCIA:** o relato menciona diferenca residual de ~48 mil, compativel com a subtracao exploratoria acima, mas a mesma sequencia de imagens mostra **48.284,06** em outra celula, corrigindo erro anterior de leitura de imagem (nao era 40.204,06). A subtracao dos valores arredondados exibidos (113.252,49 - 64.968,42) da **48.284,07**, diferenca de **R$ 0,01** em relacao a celula observada. Pode ser precisao interna/criterio de arredondamento, mas a formula nao esta visivel e a causa nao esta comprovada. Nao presumir que a soma de **64.968,42** represente todo o universo do MATR989 nem declarar formula de conciliacao aprovada. Precisamos inspecionar formulas, filtros, filial, local/armazem, competencia, classes de itens, unidades, estados de apontamento e custos efetivamente comparaveis. Saldos de diferentes relatorios nao sao automaticamente somaveis apenas por estarem expressos em valor.

### Campos visiveis do MATR989
Planilha com colunas `CODIGO`, `DESCRICAO`, `LC` ou `LO` (cabecalho abreviado; confirmar), `ORDEM PRODUCAO`, `TI` ou `TIP` (confirmar), `QTDE EM` e `VALOR EM PROCESSO` (rotulos truncados). Nao transpor aliases diretamente para nome de coluna de Protheus.

### Proposta de desenho futuro, sem implementacao autorizada
Uma **Conferencia de Fechamento de Estoques** consolidada pode apresentar os tres valores por competencia/filial, parametros equivalentes, divergencia, parcela explicada, residual e detalhes rastreaveis de movimentos/apontamentos. **Nao** afirmar `MATR320 = P7 + MATR989` como invariante canonica sem evidencia e aceite do owner. O recurso deve diferenciar `divergencia detectada`, `causa em investigacao`, `conciliada` e `indisponibilidade da fonte` e preservar origem/extracao, timestamp e versao.

**Limites com o produto atual:** R03 hoje usa SB9/SB1 como snapshot operacional e nao prova equivalencia ao MATR460/P7 oficial. Portanto nao calcular essa conciliacao somando diretamente os KPIs atuais de R03. `api-delpi` e owner das regras SQL/TOTVS; TEO e owner da evidencia AS-IS; decisao de persistencia, escopo e contratos requer gate explicito.

### Pendencias de verificacao
1. Obter as exportacoes originais de MATR320, P7 completo e MATR989 da **mesma competencia e escopo** e preservar filtros e parametros de emissao.
2. Ler a formula exata da celula **48.284,06** e explicar a diferenca de **0,01** ante a subtracao dos valores arredondados, incluindo precisao, filtros ou ajustes.
3. Identificar o subconjunto de 1.577 registros no MATR989, o significado de `Saldo em Processo` e seus componentes que podem ou nao explicar saldo de estoque.
4. Comparar por filial, tipo de produto (incluindo ou excluindo material de consumo), armazem e data-base. Diferenciar saldos/fluxos/custos e tratamentos de terceiros.
5. Mapear chaves de origem e regras de apontamento; aprovar tolerancia, tratamento de diferencas e criterio de aceite com owner de Controladoria e owner de custeio.

**Classificacao:** `THREE_REPORTS_CONFERENCE=OWNER_REPORTED_VIA_PO`; `SCREEN_VALUES=PROVEN_SCREENSHOT`; `DIFFERENCE_113252_49=DERIVED`; `RESIDUAL_48284_07=DERIVED_NOT_RECONCILED`; `EXCEL_RESIDUAL_48284_06=PROVEN_SCREENSHOT_FORMULA_UNVERIFIED`; `SQL_PARITY=TEST_NOT_RUN`; `PORTAL_CONSOLIDATION=TARGET_DECISION_REQUIRED`.

**Proximo marcador da gravacao: apos ~32:21, a confirmar pelo PO.**


### Complemento ao Registro 12 - Triagem de divergencias e possivel reabertura de periodo

**Fonte:** explicacao do PO durante continuidade da gravacao, imediatamente apos a conciliacao com residual exibido de 48.284,06. Tempo exato desta fala ainda nao informado; nao atribuir timestamp inventado.

**Procedimento AS-IS relatado:** quando os tres relatorios nao conciliam, <GESTORA-PROC> revisa (1) **parametros de emissao dos relatorios**, inclusive filtros e recortes; (2) **movimentacoes e consumos** possivelmente incorretos; e (3) eventual presenca ou efeito de **dados de periodos anteriores** no fechamento atual. Esses sao ramos de investigacao, nao causas ja diagnosticadas do delta atual.

**Condicao operacional relatada:** se a apuracao encontrar problema originado em periodo anterior, pode ser necessario **reabrir o estoque e recalcular o fechamento**, investigando o evento historico responsavel. Nao inferir que qualquer diferenca exige reabertura, nem que <GESTORA-PROC> efetivamente reabriu o periodo nesta passagem. Reabertura e recálculo sao operacoes potencialmente impactantes no ERP, sujeitas a autorizacao, controles e owners proprios; **nao automatizar no Portal**.

**Candidato de fluxo TARGET, pendente de decisao:** trilha de diagnostico read-only com categorias `report_parameters_mismatch`, `movement_or_consumption_anomaly`, `prior_period_effect` e `undetermined`, cada uma vinculada a evidencia, competencia de origem, movimento/documento e impacto estimado. Se houver hipotese de periodo anterior, exibir dependencias e necessidade de analise/autorizacao humana; nao oferecer botao de reabrir/recalcular sem contrato e gate especificos.

**Pendencias:** criterios objetivos de identificacao de movimentos antigos, historico de recalculos, parametro que altera o escopo e responsabilidade por autorizar reabertura. `ROOT_CAUSE=INCONCLUSIVE`; `HISTORICAL_REOPEN=OWNER_REPORTED_VIA_PO`; `PORTAL_WRITE_ACTIONS=NOT_AUTHORIZED`.


## Registro 13 - Conferencia analitica por tipo de material (34:25 em diante)

**Fonte AS-IS:** explicacao guiada do PO sobre <GESTORA-PROC> e capturas da gravacao por volta de 34:25-35:35. O timestamp indica a etapa da investigacao, nao uma validacao de todos os valores em ERP.

**Metodo praticado:** diante da divergencia da conciliacao geral, <GESTORA-PROC> abre o **Resumo das Entradas e Saidas (MATR320)** e o **P7 completo, sem filtro Bloco H**, compara seus totais por **tipo de material** e aprofunda a analise na classificacao discrepante, ate chegar a grupos, produtos, movimentos ou parametros potencialmente responsaveis. Essa conferencia **nao se restringe ao P7 de MP/PI/PA enviado a contabilidade**.

**Achado relatado pelo PO:** a categoria **materia-prima (MP)** apresenta uma diferenca percebida ao comparar os dois relatorios. <GESTORA-PROC> relata que problemas recorrentes podem estar ligados a **material em processo** e materia-prima. Trata-se de heuristica da especialista, **nao** prova de que o material em processo causou a divergencia deste fechamento.

**Evidencia visual:** no MATR320 (matriz, 01/09-30/09/2026), a linha `MP` traz `Saldo Atual` **3.370.493,537** (unidade monetaria descrita no cabecalho como R$). O P7 em preview exibe totais por classes dentro de blocos `EM ESTOQUE` e `EM PROCESSO`; ha item `MATERIA PRIMA` em ambos. **Nao comparar diretamente MP do MATR320 com apenas uma linha de MP do P7 sem confirmar composicao, recorte e parametros**. Nos prints, a leitura precisa de cada sublinha do P7 nao esta homologada; registrar a existencia do detalhamento, mas nao fabricar um delta MP.

**Sequencia de diagnostico candidata (somente leitura):** (1) estabelecer competencia e escopo comum, (2) total geral MATR320 x P7 completo, (3) quebrar por tipo/classificacao e situacao em estoque/em processo, (4) localizar categorias com maiores deltas, (5) detalhar por filial/armazem/produto e rastrear transacoes/apontamentos, (6) considerar historico e parametros, (7) anexar evidencia e concluir `reconciled`, `discrepancy_unexplained` ou `needs_erp_review`. **Nao aprovar esta arvore como formula oficial sem owner e comprovacao de paridade.**

### Conhecimento para eventual assistente de IA (TARGET, sem autorizacao de implementacao)
- Preservar como **hipotese priorizada por especialista**, com atribuicao `<GESTORA-PROC> / via PO / timestamp ~34:25`: investigar primeiro materia-prima e saldo em processo quando esses segmentos apresentarem delta.
- Agente nao deve afirmar causa-raiz, necessidade de reabrir periodo, nem recomendar lancamento corretivo como fato apenas por correspondencia de categoria.
- Explicar cada sugestao com valores/filtros/linhagem demonstraveis e separar observacao, calculo, heuristica e conclusao homologada. Exigir revisao humana de achados e autorizacao separada para escrita no ERP.
- Evitar conceito de "treinar IA" diretamente com dados de tela sem governanca: o artefato atual e base de conhecimento rastreavel para recuperacao contextual e regras verificaveis, nao dataset de treinamento aprovado.

**Pendente:** extracoes originais comparaveis, valores de MP em ambos os relatorios, composicao de `EM PROCESSO` e mapeamento de aliases do relatorio para fontes TOTVS via `api-delpi`.

**Classificacao:** `DRILLDOWN_BY_MATERIAL_TYPE=OWNER_REPORTED_VIA_PO`; `MP_DIVERGENCE=OWNER_REPORTED_VIA_PO`; `MP_MATR320_VALUE=PROVEN_SCREENSHOT`; `MP_CAUSAL_LINK_TO_WIP=INCONCLUSIVE`; `AI_ASSISTED_DIAGNOSTICS=TARGET_DECISION_REQUIRED`; `RUNTIME_VALIDATION=TEST_NOT_RUN`.


## Registro 14 - Natureza da demonstracao e janela temporal do fechamento (35:48)

**Fonte:** esclarecimento do PO sobre fala da <GESTORA-PROC> por volta de 35:48. A gravacao retrata uma **demonstracao executada com o mes de referencia ainda em andamento**, nao o fechamento mensal definitivo. O processo mostrado usa dados reais do ERP na demonstracao, mas **nao deve ser tratado como resultado final homologado da competencia**.

**Implicacao AS-IS:** no ultimo dia do mes ainda podem existir baixas, movimentacoes, consumos ou apontamentos a registrar. <GESTORA-PROC> indica que a conferencia efetiva deve ocorrer **apos a virada para o dia seguinte ao encerramento da competencia**, quando o mes estiver concluido do ponto de vista operacional. A referencia a `00:01` ou `01:00` e exemplificativa na explicacao do PO: **nao ha horario minimo nem janela tecnica de corte oficialmente comprovados**.

**Correcao de interpretacao retroativa:** o delta global de 113.252,49 e o residual em planilha de 48.284,06 vistos nessa sessao **nao provam falha no fechamento de setembro/2026**. Sao diferencas observadas em uma demonstracao antes de a competencia estar definitivamente pronta para fechamento. As hipoteses de parametros, consumo, movimentos tardios e efeitos historicos seguem hipoteses; nao houve RCA conclusivo.

**Candidato TARGET, sujeito a contrato/owner:** distinguir `demonstration_or_preclosing`, `period_ended`, `source_updates_pending` e `ready_for_reconciliation` a partir de evidencias reais (data de referencia, ultimo processamento, completude das fontes e status de rotinas). Nao inferir `ready` apenas porque o calendario passou de meia-noite; nem executar fechamento, recalculo ou reabertura pelo Portal.

**Pendencias:** confirmar horario/criterio oficial de corte, eventual processamento noturno e atrasos de integracao, autoridade para validar completude e regra de negocios de liberacao da conciliacao.

**Classificacao:** `DEMONSTRATION_NOT_FINAL_CLOSE=OWNER_REPORTED_VIA_PO`; `NEXT_DAY_PREFERENCE=OWNER_REPORTED_VIA_PO`; `EXACT_CUTOFF_TIME=TO_INVENTORY`; `SEPTEMBER_VARIANCE_ROOT_CAUSE=INCONCLUSIVE`; `TARGET_READINESS_GATE=PLANNED_DECISION_REQUIRED`.


## Registro 15 - Gate de conclusao de custos, P7 contabilidade e reposicao (aprox. 36:10)

**Fonte:** narracao guiada do PO e print TOTVS `Acompanha Custo > Novo fechamento de custo > Analise e revisao`, com botao `Proximo passo` visivel. O print prova a existencia da etapa e do controle, nao que a <GESTORA-PROC> efetivamente executou o fechamento final nesta demonstracao.

**Sequencia AS-IS relatada:** depois de encerrar a competencia e validar a conciliacao de saldos, parametros, movimentos e custos, <GESTORA-PROC> retorna a `Acompanha Custos` e pode avancar de `Analise e revisao` para `Fechamento` por `Proximo passo`. **Condicional:** so avancaria no fechamento real se os valores e conferencias estivessem corretos. Como a gravacao representa demonstracao antes do fechamento definitivo, **nao registrar fechamento concluido**.

**P7 entregue a contabilidade:** <GESTORA-PROC> afirma que utiliza a **ultima pagina / resumo do P7 na configuracao Bloco H**, com escopo de **materia-prima (MP), produto intermediario (PI) e produto acabado (PA)**. Esse documento e diferente do P7 completo usado para verificacoes internas. A interpretacao exata da configuracao fiscal Bloco H, das classificacoes e da competencia depende do contrato e exemplar oficial; nao inferir que um P7 operacional SB9 e equivalente.

**Pecas de reposicao e DRE:** segundo o PO, <GESTORA-PROC> comenta que pecas de reposicao compradas e nao consumidas podem ser consideradas no resultado contabil da **competencia de compra**, diferentemente da apropriacao pelo consumo aplicada a materia-prima. **Esta e uma afirmacao de pratica/entendimento relatado, NAO regra contabil homologada**: e necessario validar com Contabilidade/Controladoria o conceito de reconhecimento (compra, despesa, estoque, consumo, apropriacao), natureza do item e eventual excecao. Nao implementar contabilizacao nem classificar todas as pecas como despesa automaticamente.

**Dependencia temporal adicional:** ela **aguarda a conclusao da rotina de Custo de Reposicao** para produtos acabados (PA) e intermediarios (PI). Relacao exata entre resultado do recalculo, validacoes e liberacao do gate final permanece por especificar. O fato de ter iniciado a rotina nao equivale a resultado disponivel.

**Candidato TARGET, sem implementacao autorizada:** checklist read-only de fechamento com evidencias de conciliacao, completude de competencia, revisao de variacoes do custo medio, processamento de custo de reposicao PA/PI e envio do P7 Bloco H. Acoes de fechar/reabrir/recalcular TOTVS requerem owner, contrato, permissao e decisao explicitos; nao disparar via Portal neste mapeamento.

**Classificacao:** `FINALIZATION_SEQUENCE=OWNER_REPORTED_VIA_PO`; `NEXT_STEP_CONTROL=PROVEN_SCREENSHOT`; `FINAL_CLOSE_EXECUTED=NOT_PROVEN`; `P7_ACCOUNTING_SCOPE=OWNER_REPORTED_VIA_PO`; `REPLACEMENT_PARTS_ACCOUNTING_TREATMENT=TO_VALIDATE_WITH_ACCOUNTING`; `PA_PI_REPLACEMENT_COST_WAIT=OWNER_REPORTED_VIA_PO`; `PORTAL_FINALIZATION=TARGET_DECISION_REQUIRED`.


## Registro 16 - Documentos externos ao TOTVS: extratos bancarios (38:28)

**Fonte:** relato guiado do PO da explicacao de <GESTORA-PROC> iniciada em 38:28. Nesta marca temporal, o processo passa a abordar documentos originados **fora do TOTVS**, especificamente **extratos bancarios**. A finalidade declarada no TARGET e integrar esses documentos ao fluxo de fechamento para **importacao e validacao** na aplicacao.

**AS-IS relatado:** a fonte documental bancaria e externa ao ERP. Ainda nao foram descritos bancos, contas, canais de obtencao, formatos, responsaveis, frequencia, conciliacoes ou criterios de aceite. Nao assumir que um arquivo importado equivale a extrato validado ou conciliado.

**TARGET proposto pelo PO:** uma area de documentos do fechamento capaz de receber extratos bancarios e registrar sua validacao. A modelagem detalhada (document_type, competencia, banco/conta, filial quando aplicavel, periodo coberto, origem, upload, integridade, versao, status, validacoes, evidencias e aprovacao) e **PLANNED**, nao contrato aprovado nem funcionalidade implementada.

**Gates de seguranca e compliance:** antes de desenvolver upload, retencao, leitura de dados bancarios ou armazenamento, decidir com owner a politica de confidencialidade, classificacao, armazenamento, escopo de acesso, auditoria, tipos de arquivo e regras de tratamento de dados. Reutilizar plataforma e contracts autorizados, sem novas permissoes alem de `controllership-finance.access`/`controllership-finance.manage`, com autorizacao backend por escopo do recurso.

**Pendencias para as proximas falas:** identificar a finalidade concreta dos extratos (ex. confronto com saldos, pagamentos/recebimentos ou evidencias), documentos adicionais fora do TOTVS, etapas de conferencia, quem valida, criterios de discrepancia e tratamento de excecoes. Essas possibilidades NAO estao comprovadas pela fala de 38:28.

**Classificacao:** `EXTERNAL_BANK_STATEMENTS_AS_IS=OWNER_REPORTED_VIA_PO`; `IMPORT_AND_VALIDATE_IN_PORTAL=TARGET`; `BANK_DOCUMENT_CONTRACT=TO_INVENTORY`; `VALIDATION_RULES=TO_INVENTORY`; `IMPLEMENTATION=NOT_AUTHORIZED`.


## Registro 17 - Custos por centro de custo: SD1 e filtros de exclusao (44:28 a 47:48)

**Fonte:** narracao guiada do PO e capturas TOTVS/Excel. No minuto 44:28, <GESTORA-PROC> recorda um relatorio adicional para entrega por filial a Controladoria/DRE: custos por centro de custo. O PO informa que os relatorios de estoque e custos sao entregues para todas as filiais pertinentes, nao apenas a matriz. A lista real de filiais e seus contratos de entrega ainda precisam ser inventariados.

**AS-IS:** no TOTVS, <GESTORA-PROC> entra em Genericos, abre a base `SD1 - Itens das NFs de Entrada`, aplica filtro de **data de digitacao no mes de referencia**, exporta para Excel e faz as analises. Os prints mostram base SD1, filtro e planilha com filial, produto, tipo de produto, tipo de entrada, centro de custo e outros campos. Os alias da interface/exportacao nao identificam por si so os campos fisicos.

**REGRA DE EXCLUSAO (nao inclusao):** retirar registros cujos codigos de **tipo de entrada** pertençam a: `01`, `02`, `03`, `04`, `030`, `040`, `083`, `080`, `085`, `120`, `204`, `318`. Estes codigos vieram do relato do PO e nao tiveram semantica individual validada no cadastro TOTVS. Tratar como strings e preservar zeros a esquerda. Nao converter esta lista em `IN`; a condicao relatada e de **exclusao**, `NOT IN`.

Depois, <GESTORA-PROC> **ordena por produto** e **exclui materia-prima (MP)** ainda presente na lista, pois MP nao compoe esta analise especifica de custo por centro de custo. Isto nao revoga o uso de MP em outros relatorios, como P7 e CPV. O objetivo declarado e conhecer **despesas diretas, indiretas e administrativas**.

**Sequencia evidenciada/relatada:** SD1 -> filiais e periodo por digitacao -> excluir os 12 tipos de entrada -> ordenar por produto -> excluir MP -> analisar despesa por centro de custo -> entregar por filial. Os prints fundamentam as telas e manipulacao; os significados dos codigos, formula final e resultado nao foram homologados.

**Pendencias de inventario:** campos fisicos e aliases SD1, data de digitacao, cancelados/excluidos, classificacao MP, tipos de entrada, centro de custo e contas; significado e vigencia dos 12 codigos; medidas e sinais para agregar, impostos, devolucoes e reconciliacao; criterios de despesas diretas/indiretas/administrativas; responsabilidade pelo DRE; filial e competencia. Consultar producers/consumers e contratos em `api-delpi` antes de qualquer TARGET. Search miss nao equivale a ausencia.

**Fronteira com o Portal:** R01/R02 baixas financeiras e R03 estoque historico nao comprovam esta regra SD1 implementada. Nao criar pagina, endpoint, permission, rotina ERP nem persistencia neste registro. Eventual dado TOTVS pertence ao owner canonico `api-delpi`; MFE acessa apenas sua BFF, apos decisao de produto e gate transversal. Nao afirmar que Excel exportado corresponde a conciliacao aprovada.

**Proximo marco:** aos 47:48 <GESTORA-PROC> inicia explicacao adicional das regras de negocio. Registrar a explicacao posterior em novo trecho, sem antecipa-la.

**Classificacao:** `SD1_SOURCE=PROVEN_SCREENSHOT`; `BY_FILIAL=OWNER_REPORTED_VIA_PO`; `DATE_DIGITATION=OWNER_REPORTED_VIA_PO`; `ENTRY_TYPE_EXCLUSION_SET=OWNER_REPORTED_VIA_PO`; `EXCLUDE_MP=OWNER_REPORTED_VIA_PO`; `EXPENSE_GOAL=OWNER_REPORTED_VIA_PO`; `FIELDS_FORMULAS_OWNER=TO_INVENTORY`; `RUNTIME_PARITY=TEST_NOT_RUN`; `TARGET_IMPLEMENTATION=NOT_AUTHORIZED`.


## Registro 18 - Classificacao assistida de custos e excecoes SD1 (47:48 ate o fim da gravacao)

**Fonte:** narracao guiada do PO das falas de <GESTORA-PROC>, com prints da planilha `SCAGPOU0.XML` derivada de SD1, principalmente 48:11, 48:25, 48:48, 50:10 e 50:35. Este registro continua o Registro 17. Prints evidenciam linhas, codigos e edicao manual da planilha; a semantica e as correcoes pretendidas sao relatos de especialista mediados pelo PO, ainda nao homologados nos cadastros do ERP.

### Metodo AS-IS e classificacoes relatadas

<GESTORA-PROC> percorre entradas remanescentes depois dos filtros de exclusao dos tipos de entrada e de materia-prima, consulta os produtos no TOTVS quando nao reconhece um item e tenta classificar cada gasto em **direto**, **indireto** ou **administrativo**. Ela pode escrever a classificacao manualmente na coluna da planilha e utilizar centro de custo como indicio. Essa conferencia por produto/centro de custo demanda tempo consideravel.

- **Exemplo de item material direto:** o PO cita codigo `<PRODUTO-EXEMPLO-A>`. A leitura de codigo diretamente no print e limitada, por isso confirmar codigo exato e natureza no cadastro antes de usa-lo como amostra de teste.
- **Coparticipacao do plano de saude:** segundo <GESTORA-PROC>, a parcela que constitui despesa do colaborador deve ser **excluida desta apuracao** e ela nao exige associacao a centro de custo para essa parcela. O PO tambem menciona participacao paga pela empresa. Portanto, **nao extrapolar que toda despesa de plano de saude ou toda coparticipacao e excluida**: discriminar parcela do colaborador versus empresa e tratamento contatabil com owner.
- **Administrativos:** <GESTORA-PROC> associa centros de custo com prefixo `02` a administrativos e menciona centros vinculados a vendas/compras que comecariam por `05`, tambem classificados como administrativos no exemplo. A relacao entre prefixos e natureza exige inventario: `05` nao pode ser tratado como administrativo universal sem confirmacao do cadastro e excecoes.
- **Indiretos:** centros com prefixo `03`, associados a processos; exemplos adicionais mencionados: `0405` (PCP) e `0504` (almoxarifado). Esses exemplos nao fecham uma tabela universal de classificacao, e podem exigir revalidacao, especialmente frente a regra narrativa do prefixo `05`.
- **Diretos:** materiais/custos diretamente associados a producao; classificacao deve ser fundamentada em cadastro de produto, centro de custo e finalidade, nao apenas em prefixos. Os exemplos em planilha mostram insercao manual de `Direto` e `Indireto`.

### Erros de cadastro, revisao e casos concretos

- **50:10:** <GESTORA-PROC> alerta que ha lancamentos atribuidos ao centro `0404` que nao correspondem de fato a ele. Um centro valido nao garante enquadramento correto do item.
- **50:35:** <GESTORA-PROC> relata uso de centro `0401` inexistente/invalido e indica um produto do tipo cabo singelo que deveria estar associado ao `CT`. Interpretar `CT` como abreviacao usada no relato, sem inventar seu codigo canonico.
- **Produto `<PRODUTO-EXEMPLO-B>`:** <GESTORA-PROC> diz nao reconhecer o item e precisar consultar cadastro TOTVS. A classificacao permanece **pendente**, nao deduzida pelo assistente.
- **Separacao de despesas:** <GESTORA-PROC> informa que a contabilidade recebe a relacao para separar totais administrativos, diretos e indiretos. Conforme pratica descrita, administrativos compoem custo fixo e diretos/indiretos entram na analise de custo de producao. **Tratamento gerencial/contabil relatado**, sujeito a homologacao pela Contabilidade; nao alterar DRE ou contabilizacao com base somente na narracao.

### Candidato TARGET: pre-classificacao explicavel com revisao humana

O PO propoe substituir a triagem exclusivamente manual por uma lista de **candidatos de classificacao**: categoria sugerida, centro de custo sugerido quando respaldado por cadastro, justificativa/rastreabilidade, pesquisa por produto e acesso ao contexto de cada registro (produto, tipo, nota, filial, centro, conta, documentos/estrutura quando disponivel). A pessoa revisora deve poder confirmar, alterar ou **retirar da listagem de apuracao** itens fora do escopo, indicando motivo. Retirar da apuracao do Portal **nao e excluir a linha SD1 nem alterar lancamento no ERP**.

Estados conceituais para estudo, NAO contrato aprovado: `unreviewed`, `suggested`, `confirmed`, `excluded_from_analysis`, `needs_erp_correction`. O sistema deve separar divergencia de classificacao gerencial de erro cadastral que so owner do TOTVS pode corrigir; nao marcar automaticamente `approved` nem escrever na SD1. A experiencia deve suportar pesquisa, filtros por categoria, centro, produto, filial e motivo de excecao, e preservar versao de regras, justificativa e responsavel pela revisao, sujeito a decisao de persistencia/auditoria.

### Gaps, verificacoes e gates

1. Inventariar tabela de centros de custo e seu owner no TOTVS/`api-delpi`: codigo, descricao, hierarquia, vigencia, filial, classificacao existente ou possivel atributo direto/indireto/administrativo, relacao com conta contabil e SD1. Conferir tambem consumidores em dashboards e regras de DRE. DAVI pode ajudar a localizar informacao autorizada, mas nao substituir a authority tecnica do codigo/contrato.
2. Validar com <GESTORA-PROC>/Controladoria **cada prefixo e excecao**, sobretudo `02`, `03`, `05`, `0405`, `0504`, `0404`, `0401`, o item `<PRODUTO-EXEMPLO-B>` e o exemplo de cabo singelo. Nao promover heuristica por prefixo a regra canonica sem catalogo homologado.
3. Resolver tratamento de coparticipacao: origem do valor, parcela colaborador versus empresa, tipo de entrada, centro e contabilizacao. Reconciliar o conjunto de exclusoes anteriores (Registro 17) com as exclusoes por natureza/colaborador deste registro.
4. Obter o Excel efetivamente entregue, com competencia/filial e colunas de classificacao, e confrontar **linha a linha** com extracao SD1 por chaves do documento/item. Reconciliar totais por direto/indireto/administrativo/excluido e diferencas, antes de prometer equivalencia.
5. Definir owner, RQ/AC, estrategia de auditoria e seguranca, modelo de dados, versao de regras, acoes de revisao e entrega a Contabilidade. Sem decisao explicita, nao implementar classificacao, nova pagina, persistencia ou endpoint.

**Gates de arquitetura:** `api-delpi` e fonte canonica de regra/dados TOTVS, MFE fala apenas com BFF `controllership-finance-api`, backend verifica `controllership-finance.access` ou `manage` combinada com escopo do recurso e regra de negocio; filial e dimensao de dados, nao permission code.

**Classificacao:** `MANUAL_EXPENSE_CLASSIFICATION=OWNER_REPORTED_VIA_PO`; `SPREADSHEET_EDITS=PROVEN_SCREENSHOT`; `CENTER_PREFIX_RULES=OWNER_REPORTED_VIA_PO_TO_VALIDATE`; `COPAYMENT_EMPLOYEE_SHARE_EXCLUSION=OWNER_REPORTED_VIA_PO_TO_VALIDATE`; `MISPOSTED_CENTERS=OWNER_REPORTED_VIA_PO`; `PROPOSED_SEARCH_AND_CANDIDATE_REVIEW=TARGET_DECISION_REQUIRED`; `ERP_CENTER_MASTER_DATA=TO_INVENTORY`; `OFFICIAL_COST_CENTER_ACCOUNTING=TO_INVENTORY`; `DELIVERED_EXCEL_PARITY=TEST_NOT_RUN`.

**Situacao da evidencia ao final do video:** houve mapeamento qualitativo das etapas, mas nao conciliacao tecnica dos totais SD1 por centro de custo nem homologacao de classificacoes/aliases. O proximo trabalho e INVENTORY + VALIDATE, nao EXECUTE.
