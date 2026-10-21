# 56 - PROC-0072 | Observacoes guiadas pelo PO: fechamento de custos

Data de registro: 2026-10-21. Fonte: relato direto do PO enquanto acompanha a gravacao, associado ao screenshot TOTVS `Acompanha Custo > Novo fechamento de custo`. Registro incremental: acrescentar proximos trechos em ordem sem recontar o audiovisual por inferencia.

**Regra de evidencia:** `OWNER_REPORTED_VIA_PO` para falas da Joici relatadas pelo PO; `PROVEN_SCREENSHOT` para controles e valores visiveis na imagem; `TO_INVENTORY` para comportamento interno de TOTVS, algoritmos e contratos; `TARGET` apenas para ideias futuras. Nao afirmar audio literalmente transcrito ou validar formula TOTVS com screenshot.

## Registro 01 - inicio do fluxo, referencia temporal informada pelo PO ~01:25 a 02:08

### AS-IS: escolha da primeira atividade e paralelismo
1. A Joici **prefere iniciar pelos processamentos de fechamento de estoque**, por serem os que mais demoram (segundo relato do PO).
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
2. O que faz a Joici em `Analise e revisao` antes de confirmar `Fechamento`?
3. Quando ha erro de calculo ou data invalida, qual procedimento de correcao e reexecucao?
4. A data ajustada e realmente a data global/sessao de usuario, ou apenas a data de referencia da rotina? Confirmar com TOTVS e responsavel.
5. Como o recalculo de custo medio afeta P7, MATR320, Kardex e consultas de saldos, e quando cada extracao ocorre em relacao ao termino do job?

## Conclusao do registro 01
`AS_IS_STEP=OWNER_REPORTED_VIA_PO`; `TOTVS_WIZARD_FIELDS=PROVEN_SCREENSHOT`; `COST_AVERAGE_ALGORITHM=TO_INVENTORY`; `COST_CLOSING_JOB_RUNTIME=TO_INVENTORY`; `AUTOMATION_DESIGN=TARGET_NOT_APPROVED`; `ERP_PARITY=TEST_NOT_RUN`.

**Proximo registro:** continuar cronologicamente com as observacoes verbalizadas pelo PO. Evitar usar o trecho de video antigo como autoridade sobre timestamps quando o PO esta narrando outro ponto.


## Registro 02 - Custo de Reposicao, aproximadamente 03:09-03:59

**Fonte:** narracao direta do PO nesta conversa e capturas da rotina TOTVS `Custo de Reposicao [02.9.0004]`. Classificacao: `OWNER_REPORTED_VIA_PO` para finalidade e criterio de custo liquido; `PROVEN_SCREENSHOT` para campos visiveis. Nao confundir com P7.

### Primeira execucao: materiais MC ate MP (cerca de 03:11)
- Joici abre `Custo de Reposicao` > `Recalculo do Custo de Reposicao` > `Perguntas`.
- Finalidade relatada: alimentar o indicador **custo de operacao / custo operacional**. Owner, formula e integracao efetiva com indicador estrategico ainda `TO_INVENTORY`.
- Parametros vistos: `Utilizar Qual Moeda? = Nenhuma`; `Utilizar Taxa? = Diaria`; `Calcular os Custos Por? = Ult Custo Compra`; `Considerar Ult. Preco Compra? = Sim`; `Dt. Final Ref. Taxa? = 30/09/2026`; `Do Tipo do Produto? = MC`; `Ate o Tipo do Produto? = MP`.
- Outros campos visiveis: grupo inicial em branco e final alto (`zzzz`); `Considerar Qtdes. Negativa? = Nao`; `Avisar Divergencia? = Atualizar`; `Seleciona filiais? = Nao`; `Considera Mao de Obra? = Ambos`; `Considera Tipo Dec. OP? = Nao`; `Tempo Setup? = Sem Tempo Proprio`; roteiro de operacoes em branco.
- PO relata que considera **custo liquido, sem tributacoes**; a captura nao prova a regra fiscal/algoritmo, a natureza liquida ou se isso resulta especificamente do parametro de ultimo custo de compra. Status `OWNER_REPORTED_VIA_PO / TECHNICAL_FORMULA_TO_INVENTORY`.

### Segunda execucao: PA ate PI (cerca de 03:54)
- Joici reabre a rotina para outro conjunto de tipos: `Do Tipo do Produto? = PA`, `Ate o Tipo do Produto? = PI`.
- Mantem referencia ao ultimo dia do mes `30/09/2026`.
- Altera `Calcular os Custos Por? = Estrutura` (diferente da primeira execucao, que usava ultimo custo de compra). Na captura tambem permanecem `Considerar Ult. Preco Compra? = Sim`, `Utilizar Taxa? = Diaria` e demais opcoes visiveis; nao inferir que parametros nao mostrados sao iguais.
- PO relata que manda executar. Nao ha evidência do log de sucesso nem valores de saida nesta captura.
- Relacao com os dois P7 PDFs: o PO associou este recorte PA/PI ao trabalho que envia um relatorio para Financeiro, mas **Custo de Reposicao nao e MATR460/P7**. A afirmacao de identidade, derivacao do P7 ou equivalencia entre relatorios nao esta comprovada e nao deve ser implementada.

**Cuidado:** intervalo `MC..MP` ou `PA..PI` e parametro TOTVS representado por dois limites; nao assumir inclusividade alfabetica, conjunto fechado ou equivalencia a `B1_TIPO IN (...)` sem validar processamento.

## Registro 03 - Refaz Saldos e rotina de terceiros (04:36 e ~05:34)

### Refaz Saldos, aproximadamente 04:36
- Joici abre a rotina `Refaz Saldos [02.9.0004]` (identificacao visual da aba) e preenche parametros para **todos os materiais/produtos** conforme o PO.
- Campos visiveis no screenshot: `Do Armazem?` em branco / limite inicial nao legivel; `Ate o Armazem? = zz`; `Do Produto?` em branco; `Ate o Produto?` com codigo de limite superior; `Zera o saldo de produtos MOD? = Recalcular`; `Zera o CM de produtos MOD? = Recalcular`. Outros parametros podem existir fora do viewport.
- Relato do PO: executa **recalculo dos saldos**, utilizado quando ha falhas no processamento, para corrigir inconsistencias. Isso e contexto operacional relatado, **nao e prova** de garantia de correcao, idempotencia ou ausencia de impacto transacional.
- `PROVEN_SCREENSHOT` para visibilidade dos campos; `OWNER_REPORTED_VIA_PO` para finalidade; `RESULT_TEST_NOT_RUN` para comportamento efetivo.

### Refaz por DIT terceiros, citado por volta de 05:34
- PO relata que Joici **apenas cita** outra rotina, chamada por ele de `Refaz por DIT terceiros` (nome tecnico exato `TO_VERIFY`); **nao a executa nem exporta relatorio** neste trecho.
- Segundo PO/Joici, e usada esporadicamente e requer comunicacao ou alinhamento com o Financeiro, porque sua execucao **pode impedir temporariamente outras rotinas de faturamento** relacionadas a materiais em poder de terceiros.
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
1. Joici navega no modulo `Estoque/Custos > Relatorios > Analises > Faturamento x MOD`; a aba `Faturamento X Mod [02.9.0004]` aparece aberta na captura.
2. **Finalidade explicada pelo PO:** comparar custo esperado de mao de obra direta com o efetivamente realizado; verificar se a mao de obra cobrada corresponde ao que efetivamente foi pago/incorrido. Esta formulacao e `OWNER_REPORTED_VIA_PO`, **nao formula operacional validada**, pois a imagem nao demonstra os campos de custo calculado/pago, nem a metodologia do confronto.
3. Na janela `Parametros`, intervalo visivel `Data de? = 01/09/2026`, `Data ate? = 30/09/2026`. Filtros adicionais: `Produto Acabado de?` e `Produto Acabado Ate?` (limite superior preenchido), `Grupo De?` em branco e `Grupo Ate?` com valor `0040` aparente na captura. Nao inferir semantica dos grupos.
4. Na etapa seguinte `Selecao de Filiais` aparecem duas linhas, `01 - MATRIZ` e `02 - DELPI - UES`; contador inferior `Elem. Selecionado(s) = 2`. PO relata selecao de ambas e continuacao do processamento.
5. **Nao ha planilha gerada ou comparacao de valores provada nestas capturas**. O processo descrito aqui e parametrizacao e solicitacao do relatorio, nao calculo homologado nem exportacao.
6. O modulo `Faturamento x MOD` tambem foi mencionado no trecho posterior da gravacao (docs 54/55), em que se relatou tratamento de planilha no Excel. Correlacionar os dois pontos do processo sem inventar igualdade de bases, criterios de agrupamento ou valores.

### Refaz Saldos - retorno do processamento (aprox. 06:46)
1. Joici retorna a rotina aberta `Refaz Saldos`, janela `Recalculo dos Saldos`, e abre/visualiza o `Log de processamento das STORED PROCEDURES`.
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
