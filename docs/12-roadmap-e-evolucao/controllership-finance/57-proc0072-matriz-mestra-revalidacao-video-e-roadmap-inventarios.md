# 57 - PROC-0072 | Matriz-mestra de revalidacao do video, prints e roadmap de inventarios

**Data:** 2026-10-22. **Escopo:** toda a narracao guiada do PO sobre a gravacao de acompanhamento do fechamento de estoques e custos, prints enviados e documentos existentes, incluindo a extensao 44:28-50:35. **Natureza:** revisao documental comparativa, sem nova reproducao audiovisual integral, sem homologacao de dados TOTVS e sem alteracao de runtime. **Resultado global:** ACCEPT_WITH_RESIDUAL para consolidacao documental; INCONCLUSIVE para comprovacao integral da fala, paridade de relatorios e reconciliacoes.

## 1. Hierarquia, fontes e limites da revalidacao

1. AS-IS: TEO/Transformometro para processo, responsaveis, evidencias e proveniencia; relato guiado do PO e screenshots como fontes observacionais, NAO substitutos de homologacao de <GESTORA-PROC>.
2. TARGET: instrucoes oficiais GPT Arquiteto, regras .cursor aplicaveis, ADR/contratos no GitHub e respectivos owners. Este documento nao altera padroes congelados.
3. Documentos confrontados nesta rodada: [46 inventario de reports](./46-t01-report-source-inventory-v1.md), [55 matriz de conciliacoes](./55-proc0072-matriz-conferencias-estoques-custos-asis.md), [56 registros guiados 01-18](./56-proc0072-observacoes-guiadas-fechamento-custos.md) e [README da frente](./README.md).
4. Os screenshots fornecidos na conversa exibem interfaces TOTVS/Excel, parametros e alguns valores em setembro de 2026. **Nao existem neste commit como imagens anexadas**: portanto nao afirmar auditoria binaria do acervo no GitHub. Capturar os originais autorizados, identificar SHA-256 e armazenar em repositorio de evidencias apropriado sem dados pessoais, segredos, host/IP interno ou planilhas financeiras sensiveis indevidamente expostas. Criar referencia persistente imutavel para cada evidência no indice abaixo.
5. Marcacoes de tempo vem do acompanhamento manual do PO e podem ter deslocamento. Houve correcao expressa de 22:24 para ~21 minutos; tambem houve atribuicao indevida de conferencia aos ~30:45 anteriormente retirada. **Nao declarar audio/lip sync ou minuto exato PROVEN se nao conferido no MP4**. Existem referencias conflitantes de duracao (~54:44 versus outro indice derivado >60 min); reconciliar origem do arquivo, versao e timebase antes de auditar minutos.
6. `PROVEN` = visivel em fonte de tela/documento, dentro de seus limites; `OWNER_REPORTED_VIA_PO` = <GESTORA-PROC> descrita pelo PO, sujeita a revalidacao; `TO_INVENTORY` = dados/contrato a inventariar; `TARGET` = hipotese de produto. `PASS` exige reproducao verificavel; `TEST_NOT_RUN` nao e PASS.

## 2. Matriz de rastreabilidade - observacao -> regra -> fonte -> proximo passo

Legenda owners: **J** = <GESTORA-PROC>/Controladoria valida AS-IS; **T** = TEO prova decomposicao; **E** = owner ERP/api-delpi valida campo, consulta e algoritmo; **C** = Contabilidade/Financas valida destino e classificacao; **P** = PO decide produto; **D** = owner de dashboards/indicadores e consumers. `Evidence` indica doc 56 Registro e tempo relatado; nao prova temporal do MP4.

| ID | Trecho / referencias | Artefato, fato operacional ou regra candidata | Fonte fisica ou sistema a inventariar | Validadores | Evidencia / status | Gate verificavel |
|---|---|---|---|---|---|---|
| V01 | ~01:25-02:08; 56/R01 | Acompanha Custos inicia primeiro porque demora; trabalha outras tarefas em paralelo | job/logs ERP, politica de concorrencia | J,E,T | **r27: verificado — lista `Fechamentos` persiste execucoes com status (Concluido/Cancelado/Analise e revisao) + `Reabertura de estoque`; objeto com ciclo de vida** | identificar job, estados, locks e dependencias |
| V02 | ~02:08; R01 | Ultimo dia da competencia no sistema; operadora ajusta data, apropriacao diaria, filial corrente | parametros TOTVS, calendario/cutoff | J,E | **r27: verificado 02:40 — etapa 1 Predefinicao: ultimo fechamento 31/08, data 30/09, metodo Diaria, Filial corrente; regra visivel "somente posterior ao ultimo fechamento"** | homologar data de negocio versus data da maquina; nao automatizar alteracao |
| V03 | 03:09-03:59; R02 | Reposicao MC-MP pelo ultimo custo de compra e PA-PI pela estrutura; custo liquido relatado; indicador custo operacional | algoritmos reposicao/estrutura, impostos, indicadores | J,E,D | **r27: PROVEN — rotina = MATA320 (SX1 MTA320 1:1); TTAT prova escrita `B1_CUSTD` 13.201+1.532 writes 30/09 JOICI +15.972 em 01/10; errata `Tempo Setup?`=`Som Tempo Propo`** | duas variantes, chaves, amostra, consumidor |
| V04 | 04:36-06:46; R03-R04 | Refaz Saldos geral; conclusao visual OK sem export; refaz DIT terceiros eventual e bloqueio de faturamento | tarefas TOTVS, logs, seguranca operacional | J,E | **r27: rotina = MATA300 (SX1 MTA300 1:1 — `Zera saldo/CM MOD`=Recalcular); log threads `c300P* - Ok` verificado; efeito SB2 `PENDING_EVIDENCE` (sem TTAT); DIT terceiros apenas citada → E12** | catalogar precondicoes, riscos e status sem executar |
| V05 | 06:04-06:40; R04 | Faturamento x MOD no mes inteiro, filiais 01/02, previsto versus realizado | produtor ERP, estrutura, OP, rateio e medida | J,E,C,D | screenshot+relato | obter arquivo real, layout e regras |
| V06 | 07:25; R05 | Kardex01/99 e saldo estoque aguardam termino do calculo de custos | locks/consistencia, jobs, extracao | J,E | OWNER_REPORTED_VIA_PO | demonstrar quais leituras bloqueadas, nao generalizar |
| V07 | 07:56-09:18; R05 | Triagem/compensacao PA antecipado, devolucao, titulos iguais, casos marketplace | SE2/SE1, compensacao, rastreio, permissao | J,E,C | screenshot interface; sem algoritmo | definir somente candidatos; matching com revisao |
| V08 | 10:09-11:32; R06 | Posicao titulos em aberto pagar/receber inclui vencimentos anteriores/futuros, nao somente movimentos no mes | FINR150/FINR130 citados em screenshots; tabelas/parametros | J,E | OWNER_REPORTED_VIA_PO | diferenciar aberto de baixado R01/R02 |
| V09 | 12:48-13:52; R07 | Relacao de baixas DELPI customizada falhou; cinco saidas auxiliares; entrega Aliance; cliente/fornecedor/CNPJ | relatorios FINR190 e custom, DTOs R01/R02 | J,E,C | OWNER_REPORTED_VIA_PO; original ausente | mapear todas 5 entradas e parity antes de alegar substituicao |
| V10 | ~16:00-16:57; R07 | Calcula 100%, revisa custo medio inicial/final e nao finaliza ate conferir | estados Acompanha Custos, auditoria variacao | J,E | **r27: verificado — etapa 2 a 100% (14:47) com checkpoints + controles; etapa 3 "1991 produtos" (16:40/36:10) = fonte do `Analise.xlsx` (1.966/1.994 CM final ≡ SB9@30/09); etapa 4 nao exibida** | separar calculo 100% de fechamento homologado |
| V11 | 17:10-18:53; R08 | P7 completo para revisao e layout H somente MP/PI/PA para Contabilidade, exclusao terceiros relatada | MATR460, SB9/SB1 e fontes custo oficiais | J,E,C | 2 PDFs anteriores + print; parity TEST_NOT_RUN | provar parametros de ambos contra original |
| V12 | 18:53-20:00; R08 | Kardex diario 01 CPV e 99 inventarios, em algumas filiais | MATR910/SD3 candidata, aliases | J,E | screenshots+relato | inventariar codigo exato, filial, armazem e periodo |
| V13 | ~21:00-21:53; R08 | Saldo Em Processo/Em Processo separados e MATR320 entradas/saidas | MATR989/H02, MATR320 e fontes fisicas | J,E | screenshots+relato, timecode corrigido | catalogar 3 saidas distintas e parametros |
| V14 | 21:56-23:33; R09 | Filtra `INVENT` em Kardex 01/99, une movimentos e calcula entradas menos saidas (prejuizo relatado ~57 mil) | SD3 por filial, documento/movimento, sinal/custo | J,E,C | prints da soma; parity TEST_NOT_RUN | refazer por linhas e sinais, registrar competencia e denominador |
| V15 | 23:46-25:46; R10 | CPV Kardex 01: excluir terceiros e filtrar CFOPs narrados 5101/5124/6101/6124, somar `Saidas Custo` | SD3, natureza/CFOP, BOM, cadastro terceiro; dashboard suprimentos | J,E,D | prints e relato; codigos TO_INVENTORY | verificar cada CFOP e reconciliar CPV canonico |
| V16 | 26:25-29:54; R11 | MOD selecionada pelo `Cod Produto` prefixo MOD; mes inteiro, duas filiais, total visual aproximado 172 mil | produtor MOD, estrutura, OP, FI01/FI02, planilha | J,E,D,C | prints; total exemplo nao homologado | reproduzir medidas e consumer DRE/Sheets |
| V17 | 30:00-35:48; R12-R14 | Conciliacao MATR320 x P7 completo x Saldo Em Processo, inspecao por tipo, MP, consumos, historicos e parametros; demo nao e fechamento efetivo | 3 relatorios com mesmo corte e regras de saldo | J,E,C | prints/relato; INCONCLUSIVE | obter calculos, denominadores e diferencas por grupo |
| V18 | 35:48-38:28; R14-R16 | Competencia ainda em aberto na demonstracao; somente sacramenta custos depois dos checks; P7 ultima pagina Bloco H; pecas de reposicao relato DRE | cutoff/status ERP, aprovacao, Contabilidade | J,E,C | OWNER_REPORTED_VIA_PO | matriz de precondicoes e aprovacao; confirmar regime contabil |
| V19 | 38:28; R16 | Extratos bancarios e outros externos a TOTVS sao documentos a importar e validar | instituicoes/arquivos, TEO kp02 | J,T,C,P | relato; TARGET documento | especificar tipos, acesso e validacoes depois de decisao |
| V20 | 44:28-47:48; R17 | Custos por CC por filial via SD1/data digitacao; excluir 12 tipos entrada, depois MP, classificar custos | SD1 + SB1 + centro custo/conta | J,E,C | prints+relato; SQL TEST_NOT_RUN | provar aliases, NOT IN preservando zeros, flags e total |
| V21 | 47:48-50:35; R18 | <GESTORA-PROC> classifica direto/indireto/admin, consulta produto desconhecido, rejeita coparticipacao colaborador | centro custo, produtos, despesas, cadastro RH quando autorizado | J,E,C | screenshot manual + relato | validar casos e regras, sem classificacao por prefixo automatica |
| V22 | ~48:48-50:35; R18 | Prefixos 02/03/05 e exemplos 0405, 0504; erros 0404/0401; produto <PRODUTO-EXEMPLO-B> | tabela oficial CC e relacionamento produto/conta | J,E,C | OWNER_REPORTED_VIA_PO | tratar conflito 05/0504, codigo desconhecido e vigencia |
| V23 | proposta PO apos 50:35; R18 | Lista pre-classificada explicavel, pesquisa, excluir da apuracao, revisar humano, auditoria | BFF/ports/versionamento ainda nao decidido | P,E,C,J | TARGET / DECISION_REQUIRED | fechar UX, ownership, RQ/AC, dados e autorizacao |

**Nao confundir:** `R01/R02` implementados = baixas financeiras; `Posicao de Titulos` em aberto (V08) nao equivale a baixas. `R03` operacional = SB9/SB1, nao replica oficial do P7. `MATR320` nao e Kardex. `SD1` entrada NF nao e `SD3` movimentos de estoque. `CFOP` do Excel precisa mapeamento ao campo fisico, nao supor alias.

## 3. Matriz especifica de reconciliacoes, calculos e casos de referencia

| Chave | Candidato a calculo/conferencia | Exemplo/escopo informado | O que impede PASS |
|---|---|---|---|
| RC-01 | P7 completo versus MATR320 por filial/competencia/tipo | Setembro/2026, divergencia apontada na narracao | filtros, saldos inicial/final, fonte temporal, arredondamento e paridade oficiais |
| RC-02 | Diferenca P7 x MATR320 explicada por saldo em processo | prints exibem `3.890.247,18`, `3.776.994,69`, `113.252,49`, `64.968,42`, `48.284,06` em contas exploratorias | formulas, rotulos e inclusao de estoque em processo nao homologados; nao assumir identidade contábil |
| RC-03 | Inventario = soma entradas menos soma saidas filtradas por `INVENT` (01+99) | Excel mostra `-57.181,80` no exercicio e PO relata prejuizo | valor por movimento e sinal, arredondamento, inclusao dupla, documento chaves e competencia |
| RC-04 | CPV = soma coluna de custo de saida apos CFOP/terceiros | Relato indica recorte CFOP 5101/5124/6101/6124 | reconciliar api-delpi `get_supplies_cpv`/dashboard e fonte real, sem nova formula arbitraria |
| RC-05 | MOD = valor total dos produtos de mao de obra direta no periodo/filiais | Exemplo em Excel ~172 mil | BOM, unidade, rateio, custo total versus custo unitario, notas negativas, consumer |
| RC-06 | Despesa por CC = SD1 elegivel (NOT IN tipos + NOT MP + exclusoes justificadas), depois classificação | Sem total oficial recebido nesta rodada | semantica `C Custo`/`C Cont`, base valor bruto/liquido/credito, filial, impostos, dupla contagem |
| RC-07 | Terceiros nao entram em CPV/P7 quando fora do escopo especifico | <GESTORA-PROC> aponta residuos/itens do cliente | custodiante, propriedade, estrutura, estoque, tratamento fiscal e scope |
| RC-08 | Gate fim do mes e salvamento definitivo | Demo dia 30/09/2026 nao representa fechamento real | ausencia de movimentos tardios, datas de corte, locks e aprovacao owner |
| RC-09 | Compensacoes financeiras com pares provaveis | PA, NF, devolucoes e marketplaces | chaves, saldos e nao comprometer ERP; apenas triagem ate gate |

**Numeros do video nao sao criterios de aceite universais**. Conservar imagem/arquivo original e competencia, filtros, hora/versao, filial e formula antes de comparar.

## 4. Conflitos, correcoes e riscos explicitamente detectados

| ID | Risco / observacao | Tratamento |
|---|---|---|
| X01 | Divergencia de duracao/timebase: original ~54:44 e derivacoes maiores; timecode `22:24` corrigido para ~21m | indexar video por hash e versao; timecodes provisórios |
| X02 | Suposta conferencia em 30:45 foi contestada pelo PO | alegacao retirada no doc 55; NAO promover a requisito |
| X03 | O P7 PDF layout H e o P7 completo sao saidas distintas com totais distintos; R03 e proxy operacional | contratos/paridade independentes |
| X04 | Diferenca numerica de setembro/2026 pode refletir demonstracao com competencia ainda aberta | preservar condicao de demonstracao e recalculo, sem meta de fechamento zero nesse exemplo |
| X05 | `INVENT` no Excel, `CF`, `SD1`/`SD3`, `C Custo` sao aliases/contextos heterogeneos | dicionario de dados e linhagem campo-a-campo obrigatorios |
| X06 | `05` dito administrativo mas `0504` exemplificado em outro grupo; `0401` alegadamente inexistente | catalogo mestre e historia por vigencia, decisao contabilidade |
| X07 | Coparticipacao do colaborador excluida, mas parte da empresa existe | tratamento da fracao com documentos/centro correto |
| X08 | Material direto, MP excluida da analise SD1 e CPV, mas MP presente P7 | regra depende do relatorio; nao criar filtro global MP |
| X09 | `Acompanha Custos 100%` nao prova fechamento consumado | estado calculado/revisado/confirmado separado |
| X10 | Reports enviados a Aliance e ao financeiro por arquivos podem conter dados pessoais e financeiros | inventariar classificacao e direito de acesso antes de anexar a repo |
| X11 | V17 e V23 tem sugestoes de automacao; ainda sem aprovacao de comportamento e persistencia | DECISION_REQUIRED; nenhum runtime |
| X12 | Doc 55 ainda intitulado foco 19-33m enquanto doc 56 evoluiu a 50:35 | doc 57 passa a ser indice mestre; preservar doc 55 como estudo setorial, nao reescrever historico |

## 5. Roadmap de levantamento e validacao - ate 3 ciclos de handoff, NAO de implementacao

Cada ciclo encerra **somente apos** evidencias, revisao do GPT, testes de dados quando existirem, atualizacao documental, commit/SHA e proximo gate. Nao implantar software baseado em informacao incompleta.

### Ciclo I - Evidencias, inventario AS-IS, dicionario e ownership (prioridade P0)
**Objetivo:** resolver proveniencia e cobertura integral V01-V23.

Entregas: (a) manifesto de fontes (video original/recortes, hash, nome, timestamp, prints autorizados, arquivos reais e PDFs) com seguranca; (b) index timecode corrigido, link registro 56, screens e TEO; (c) owners por artefato; (d) lista de relatorios disponiveis, outputs reais e respectivos parametros por filial/mes; (e) quadro `PROVEN` vs `OWNER_REPORTED_VIA_PO` vs `TO_INVENTORY`. Verificar as divergencias X01-X04 e a falta do original das cinco saidas do R01/R02.

**AC-I:** 23/23 entradas da matriz com referencia, responsavel e status; 100% dos prints fornecidos classificados como arquivo verificavel ou `NOT_AVAILABLE_IN_REPO`; nenhum minuto em `PROVEN` sem prova de timebase; todos os conflitos com owner. Evidencia negativa documentada, nao ocultada. Validacao humana requerida de <GESTORA-PROC> para regras faladas.

### Ciclo II - Inventario fisico TOTVS e demonstracao de calculos (prioridade P0)
**Objetivo:** provar os datasets reais e transformar heuristicas em regras testaveis.

Ordenar: (1) centros de custo/SD1/SB1 e hierarquia classificatoria V20-V22; (2) SD3 Kardex/INVENT/CFOP V12/V14/V15; (3) P7 oficial e MATR320/MATR989/V17; (4) MOD estrutural V05/V16; (5) titulos e compensacoes V07-V09; (6) jobs custo/reposicao V01-V06/V10; (7) origens externas V19. Para cada: tabela e owner, dicionario fisico e alias, chaves e cardinalidade, politica de deletado, filial, historico, timezone/datas, custos/moedas e rounding, joins, exemplos anonimizados, consumers ja existentes (inclusive CPV e MOD dashboards).

**AC-II:** RC-01..RC-09 com query/protocolo `READ-only` reproduzivel OU `BLOCKED` motivado; casos CC `02/03/05/0404/0401/0504/0405`, `<PRODUTO-EXEMPLO-B>` e coparticipacao explicitamente testados ou pendentes nomeados; relatorio de divergencias por linha/chave e valor para RC-01/RC-02/RC-03/RC-06. Nenhum `PASS` inferido de HTTP 200. Se bloqueado, `INCONCLUSIVE`.

### Ciclo III - Homologacao de regras, matriz de requisitos e desenho de experimento (prioridade P1)
**Objetivo:** concluir backlog de melhoria consolidada sem multiplicar telas TOTVS.

Workshop <GESTORA-PROC> + Contabilidade + owners: homologar catalogo versionado de classificacao e exclusoes, tolerancia e origem de variacoes, workflow de investigacao; decidir escopo apenas diagnostico ou tambem conciliacao historica, guardrails de IA, persistencia de evidencias por fechamento e responsabilidades de correcoes ERP. Derivar RQ/AC e contratos apenas apos decisions.

**AC-III:** matriz `business_rule -> inputs -> formula -> fixture -> expected -> owner approval`, decisoes `DECISION_REQUIRED` resolvidas ou mantidas explicitamente bloqueadas; prioridades com impacto/esforco/risco; backlog page-by-page se gate transversal explicitamente aprovado; documentacao de ajuda a evoluir no mesmo gate. Nenhuma API, migration, nova permission nem deploy nesta fase.

### Modelo de entrega por ciclo

`HEAD` + `git status` + leitura instructions/.cursor aplicaveis -> pesquisa TEO AS-IS / GitHub TARGET -> inventario owners/producers/consumers -> resultados com linhas/consultas/artefatos -> teste controlado -> classificacao PASS/FAIL/... -> diff de docs -> commit/push e SHA -> review ACCEPT/REWORK/... -> proximo ciclo. Branch, deploy e smoke somente para implementacao autorizada posteriormente; **nao implantar runtime por causa de atualizacao de mapeamento**.

## 6. Quadro de decisoes ainda nao tomadas

- **D-01 (produto):** grau de automacao da conferencia: leitura/diagnostico, sugestoes ou aprovacao de classificacoes e emissao de dossie.
- **D-02 (persistencia):** fonte, retencao, imutabilidade, versoes, auditoria e visibilidade dos dados por ciclo e das evidencias financeiras.
- **D-03 (regra):** fonte de autoridade do catalogo centro de custo e de classificacoes diretas/indiretas/administrativas; override e vigencia.
- **D-04 (integração):** reutilizacao de produtos/consumers existentes (CPV, MOD/Sheets/DRE) versus endpoint canonico; manter boundaries.
- **D-05 (operacao):** eventual execucao/mutacao ERP/refaz/custo/sacramentacao no Portal; NAO presumir permitido.
- **D-06 (IA):** assistente consultivo com referencia e explicabilidade vs automacao; nenhuma inferencia que altere contabilizacao.

**Arquitetura inalterada:** duas permissions `controllership-finance.access` e `controllership-finance.manage`; autorizacao backend fail-closed com effective permissions Core, escopo do recurso e regra de negocio. `plugins/controllership-finance` somente via `controllership-finance-api`, que cruza contracts HTTP com `api-delpi` para semantica TOTVS; nunca acesso direto MFE ao ERP nem banco do contexto alheio.

## 7. Manutencao viva da matriz

Para cada nova observacao, acrescentar ID `Vxx` ou `RC-xx` sem substituir nota antiga silenciosamente; registrar arquivo/timecode/screenshot, origem, grau de evidencia, owner, alteracao de entendimento, resultado de teste e SHA. Se uma premissa anterior for refutada pelo runtime, marcar `EXECUTION_DRIFT` e abrir rework. **Nao ha autorizacao de implementacao nem PASS runtime neste documento.**


## 8. Ciclo I - reinterpretacao do checklist como catalogo operacional P2/P5 (22/10/2026)

**Correcao explicita do PO:** o checklist de envio apresentado no documento privado e a referencia que <GESTORA-PROC> consulta para saber **quais itens preparar e encaminhar no fechamento mensal**. Ele NAO e apenas um inventario externo nem evidencia de que os itens ja foram enviados. Enriquecer o fluxo de negocio do Portal ja decidido, sem criar paginas, permissions ou mecanismos de review paralelos.

**Crosswalk canônico, sem conteudo privado:**
- **P2 (doc 09):** template e snapshot do checklist por competencia, contextos/filiais, entregaveis aplicaveis, requisito, evidencias, pendencias, validacao/rejeicao/historico. Distinguir previsto, produzido, anexado, validado e N/A; marcacao visual da planilha nao comprova sucesso.
- **P6 (doc 13):** governanca do template mestre e catalogos, nao editar retroativamente snapshots do fechamento.
- **P5 (docs 12 e 37, authority de decisao):** compor recipient packages e PackageVersion, finalizar sem enviar automaticamente, submeter **dentro da Minha DELPI** para review humano. Notificacao in-app/e-mail aponta ao Portal; nao enviar attachment por e-mail no V1. Aceite real por areas obrigatorias da versao vigente conforme C2/D-FINAL-02; sem force completion.
- **P1 (doc 08):** projetar progresso e blockers por competencia, sem assumir conclusao a partir de check verde.
- **Owners:** <GESTORA-PROC>/Controladoria define entregavel e operacao AS-IS; Contabilidade/Financeiro/Fiscal confirmam destinatarios e criterios por area; Core e authority das pessoas/permissoes; P2/P5 e authority do estado do pacote. Nao atribuir uma area obrigatoria a um item apenas por observacao do arquivo.

**Matriz conceitual de familias, sem dados da empresa:** (a) extratos e comprovantes de fontes externas; (b) baixas financeiras; (c) operacoes de importacao/cambio; (d) estoque/P7; (e) CPV, Kardex e ajustes; (f) MOD, material em processo e faturamento; (g) despesas por centro de custo; (h) excecoes fiscais e custo zero; (i) documentos fiscais; (j) documentos contabeis; (k) taxonomia auxiliar de consumo. Cada familia e candidata a itens distintos no template, mas NAO autoriza automaticamente inclusao como required/conditional/optional.

**Ciclo I pendente:** inventariar para cada item `familia -> deliverable -> company/branch applicability -> competency -> source -> preparation owner -> recipient package -> required area -> evidence format -> validation rule -> exception/N-A -> version and status`; confrontar com P2/P5/P6 e o ledger RQ/AC, sem duplicar contratos. Revisar catalogo com <GESTORA-PROC> e owners das areas. Ciclo II definira fontes/DTOs/consultas read-only quando esse mapeamento estiver claro.

**Seguranca dos documentos:** originais e dados operacionais/fiscais/financeiros ficam restritos ao contexto privado; este GitHub armazena **somente conceito, dependencia e gaps**, sem prints, arquivos, nomes de instituicoes, contas, identificadores ou valores.

**Status:** `CHECKLIST_PURPOSE=PO_CONFIRMED`; `P2_P5_BOUNDARY=PROVEN_GITHUB_DOC`; `CATALOG_ITEM_MAPPING=TO_INVENTORY`; `ACTUAL_REVIEW_ASSIGNMENTS=TO_INVENTORY`; `RUNTIME=TEST_NOT_RUN`; `NEW_IMPLEMENTATION=NOT_AUTHORIZED`.


### Correcao de evidencia do checklist - legenda verde `Enviar` (PO, 22/10/2026)

**Correcao sobre a leitura anterior:** a planilha apresenta legenda verde **`Enviar`**. Portanto, nas matrizes de entrega, **celula verde = entregavel indicado para envio naquele recorte de unidade/filial**. Este significado nao deve permanecer genericamente como "cor sem semantica" ou apenas "aplicabilidade provavel". O PO confirmou expressamente esse criterio e as capturas mostram a legenda.

- **Verde (`Enviar`) = REQUIREMENT_TO_SEND** no escopo da coluna correspondente, conforme checklist operacional. Nao equivale a `SENT`, `SUBMITTED_FOR_REVIEW`, `VALIDATED` ou `ACCEPTED`.
- **`x`** e outras anotacoes aparecem em celulas na planilha, mas sua interacao com a cor, em todos os quadros/abas, ainda requer conferencia da owner para evitar precedencia presumida. Branco/sem verde nao significa automaticamente "dispensado", "N/A" ou "nao requerido" sem regra confirmada.
- **Destino** e **obrigatoriedade da revisao** permanecem campos separados da marcacao verde: o documento informa o que deve ser enviado, enquanto P2/P5 e os contratos canonicos definem estados, pacotes e aceite humano.
- No inventario do template P6/snapshot P2, mapear `deliverable + business_unit/branch -> requirement_to_send` com contexto/competencia e versao do template, **sem** criar permission por filial. Confirmar aplicacao em todas as abas, excecoes e variacoes por competencia com <GESTORA-PROC> antes de migrar para contrato fisico.
- Atualizar o status da interpretacao: `GREEN_LEGEND=PROVEN_SCREENSHOT_AND_PO_CONFIRMED`; `GREEN_MEANS_SEND_REQUIRED_IN_COLUMN_SCOPE=PO_CONFIRMED`; `ACTUAL_DELIVERY=TEST_NOT_RUN`; `REVIEW_ACCEPTANCE=TEST_NOT_RUN`.

Este adendo prevalece sobre textos anteriores desta matriz que descrevem genericamente as marcacoes verdes como nao interpretadas. Dados originais e operacionais continuam restritos fora do GitHub.


### Correcao organizacional vigente (confirmacao do PO, 22/10/2026)

A coluna do checklist que referencia antiga empresa/segmento industrial **nao representa uma entidade operacional vigente**. Para este levantamento e para o futuro catalogo de entregaveis ativos, considerar **somente matriz e filial da empresa de componentes**, conforme escopo confirmado pelo PO. A marcacao verde "Enviar" em coluna legada nao gera obrigacao ativa P2, pacote P5 ou configuracao P6. Preservar o documento privado como evidencia historica, sem publicar identificadores e sem apagar historico de competencias anteriores. Antes da implementacao, validar os identificadores organizacionais atuais em cadastros autorizados do Core/TOTVS.

`ACTIVE_ORG_SCOPE=PO_CONFIRMED`; `LEGACY_INDUSTRIAL_COLUMN=EXCLUDED_FROM_CURRENT_REQUIREMENTS`; `ORG_REGISTRY_PARITY=TO_INVENTORY`. Este esclarecimento prevalece sobre citacoes anteriores a unidades industriais no checklist.
