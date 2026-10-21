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
