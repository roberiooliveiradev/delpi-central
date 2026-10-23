# DÉLIA — Incidentes observados no Portal produtivo: CRI, prosa operacional e roteamento contextual (2026-10-22)

**Status:** INCIDENT_OPEN / PROD_RUNTIME_UNVERIFIED / RCA_PENDING.  
**Evidência primária:** três capturas de tela fornecidas pelo usuário nesta conversa, do endereço `minhadelpi.com.br/apps/delia`, em 22/10/2026, aproximadamente 12:56–13:12 (horário local). **As imagens não estão anexadas ao repositório nesta task; referências textuais abaixo não substituem logs, IDs de request ou evidência do runtime.**  
**Natureza do registro:** triagem factual, não diagnóstico concluído e não autorização de mudança de runtime.  
**Referências:** docs 81, 82, 84–91 da trilha CRI/MCP; doc 87 (incidente singular/plural e gate CRI); doc 88 (decisão de continuidade); doc 91 (CP4 e pendências CP5).

## Contexto e decisão de produto

O usuário reafirma: **CRI deve estar habilitado e funcional em produção**, e respostas operacionais precisam ser conversacionais, fundamentadas e úteis — não mera enumeração de campos de banco/API. Esta é uma exigência de produto reiterada, **não evidência de que a implantação já ocorreu**. Verificar SHA/config/instruction-resource efetivos antes de afirmar ativação. Não ativar produção silenciosamente nesta task; seguir gates legítimos de rollout, segurança e rollback.

O usuário decidiu **aguardar o resultado do CP5 já em execução** antes de autorizar nova implementação. Consolidar estes cenários como evidências e insumos para a revisão integrada posterior, evitando intervenção paralela que conflite com CP5.

## INC-01 — Último processo cadastrado: resposta correta em campos, mas prosa mecânica

**Pergunta literal:** `qual o ultimo processo cadastrado?`

**Observação na captura:** atividade marcada como concluída; fonte `transformometro-api` com horário de consulta exibido; corpo lista literalmente `codigo_processo`, `nome_processo`, `gestor_responsavel`, `status_processo`, `created_at`, inclusive UUID e timestamp ISO bruto. Registro exibido: `PROC-0080`, nome **Monitoramento e Análise dos Indicadores de Estoque**, status ativo, `created_at=2026-10-15T15:43:45.344799-03:00`. O usuário afirma que o conteúdo factual está correto, mas observa ausência de tratamento da prosa pelo LLM/CRI.

**PROVEN (captura):** houve apresentação de um registro operacional e identificação visual da fonte; texto final expôs nomes técnicos de campos, UUID e ISO datetime; experiência conversacional inadequada.

**NOT_PROVEN:** que `PROC-0080` é globalmente o mais recente por data de criação; coverage/ordering/pagination do owner; que o CRI estava ON/OFF; que a saída passou por composer CRI ou baseline; qual SHA de backend/frontend e versões de instrução estavam realmente em produção.

**Falha de experiência:** em vez de apresentar identificador, nome e dados relevantes em prosa natural, a DÉLIA despejou valores tipados. Não corrigir com template lexical específico de processo; investigar qual camada compôs a resposta e qual contrato e path deveriam receber o tratamento conversacional.

## INC-02 — “2 exemplos de terminal bala”: resposta genérica apesar do contexto empresarial

**Pergunta literal:** `2 exemplos de terminal bala`

**Observação na captura:** DÉLIA respondeu com exemplos ilustrativos de terminais bala macho/fêmea 4 mm azuis, aplicações e bitolas; marcou a resposta como `HYPOTHESIS`, exibiu `Sem fonte vinculada` e explicitou que exemplos são genéricos de mercado, não registros do cadastro DELPI, e que códigos/fichas/disponibilidade exigiriam consulta operacional governada.

**PROVEN (captura):** conversa gerou prosa legível e limites epistemológicos explícitos; sem fonte empresarial vinculada ao resultado.

**NOT_PROVEN:** que DAVI tenha sido descoberto, disponibilizado ou descartado pela seleção; que alguma capability de busca por nome/descrição exista no DAVI; que o usuário pediu apenas exemplos genéricos; que a resposta factual sobre bitolas/modelos esteja validada. Não confundir `HYPOTHESIS` com facto de catálogo.

**Comportamento desejado:** dado o contexto DELPI, priorizar descoberta semântica de capability legítima de consulta ao catálogo (DAVI ou outro owner real) **se disponível e autorizada**, pesquisar pelo significado/descrição do item e responder com até dois registros verificáveis, códigos e descrições. Se não houver capability, resultados ou acesso, informar a limitação e, se pertinente, separar exemplos genéricos dos registros empresariais. Não assumir capability específica sem contrato de owner. `discovery != approval`; `model selection != authority`.

## INC-03 — “use o davi”: falha de reconhecimento do especialista e continuidade do turno anterior

**Pergunta literal do follow-up:** `use o davi`, após `2 exemplos de terminal bala` na mesma conversa visual.

**Observação na captura:** resposta concluída: `Não consegui identificar a que "davi" se refere — não tenho conhecimento de uma ferramenta, módulo ou pessoa com esse nome neste contexto.` Em seguida solicita esclarecimento; exibe `Sem fonte vinculada`.

**PROVEN (captura):** texto da resposta não reconhece o DAVI e não executa visivelmente a continuação contextual pretendida.

**NOT_PROVEN:** se `prior_turns` foi transmitido/rejeitado; se o catalogue de capabilities incluía DAVI naquele request; se a seleção semanticamente o excluiu; se houve AuthZ ou provider error; se a rota caiu em `conversational` antes de discovery; se o estado/versão de produção possui correções relevantes.

**Comportamento desejado:** interpretar `use o davi` como instrução contextual para **investigar os terminais bala usando DAVI**, mediante discovery de capabilities, seleção semanticamente guiada e AuthZ live, em vez de tratar `davi` como nome desconhecido em pergunta isolada. Caso DAVI ou a capability não esteja acessível, responder com a limitação observada, não afirmar desconhecimento global do especialista.

**Proibição:** não implementar regra regex/string `use o davi → provider` ou `terminal bala → DAVI`, não adicionar branches por especialista no planner, não utilizar alias de provedor como autorização. Owner/contrato determinam capacidade e permissão.

## Problemas transversais — separar causa-raiz e evidências

| Dimensão | O que precisa ser comprovado | Estado |
| --- | --- | --- |
| CRI produtivo | `DELIA_RESPONSE_INTELLIGENCE_ENABLED` efetiva, `requested/effective`, instruction versions, SHA backend/MFE e evidência da **interação específica** | TO_INVENTORY |
| Compositor da resposta INC-01 | se texto veio de CRI E3, baseline deterministic fallback, grounded_synthesis ou outro ramo e por quê | TO_INVENTORY |
| Ordering INC-01 | `created_at` como campo semântico de criação, ordenação comprovada, cobertura global/paginação | INCONCLUSIVE |
| Discovery INC-02 | grupos/capabilities publicados por DAVI em prod, permissões e contrato de pesquisa por descrição | TO_INVENTORY |
| Interpretação semântica INC-02 | decisão admission/group/capability e justificativa observável para fallback HYPOTHESIS | TO_INVENTORY |
| Contexto INC-03 | `prior_turns` no payload, seleção do owner, continuidade de referência a terminal bala | TO_INVENTORY |
| Health DAVI INC-03 | se DAVI foi descoberto, AuthZ, erro real vs selection not_applicable | TO_INVENTORY |
| CP5 governado | recuperação timeout/continuity, gates R1–R4, MCP real, sem confundir com falha de CRI | PENDING |
| Produção | runtime SHA, flags, config e deploy auditado; `git push != deploy` | NOT_VERIFIED |

## Plano bounded de investigação **após** relatório CP5

1. Preservar e revisar o report CP5 sem abrir outra implementação concorrente. Correlacionar os novos incidentes com SHA efetivo, timestamps, correlation IDs/activity details, versão de composer e flags; obter apenas logs autorizados/sanitizados, nunca tokens.
2. Reproduzir literalmente os três prompts em ambiente autorizado no mesmo contexto conversacional, incluindo follow-up `use o davi`; registrar intent/admission, discovered groups, owner selection, capabilities, AuthZ, invoke, evidence, composer selecionado, `requested/effective CRI`, resposta final e limitações.
3. Separar **config/deploy** (CRI não ativado), **pipeline de composição** (CRI ativo mas não engajado, prosa de campos), **seleção/contexto** (DAVI ignorado), **contrato do owner** (ausência de search por descrição) e **fato empresarial** (último por criação não provado). Cada hipótese só vira causa quando correlacionada ao trace da interação.
4. Corrigir somente owner/boundary comprovado com RED→GREEN, teste de generalização para outros especialistas/produtos (sem lexical exceptions), prova de saída CRI natural com grounded sources e resiliência CRI OFF/on conforme contratos. Não presumir sucesso por HTTP 200 ou texto fluente.
5. Autorizar alterações de produção em task de release separada com SHA+config+rollback+evidência de runtime e outcomes; não inferir ativação da flag no `.env.prod.example`.

## Critérios de aceite futuro

- CRI efetivamente ON em produção **verificado** na interação operacional, com composer selecionado/versão e evidência, não apenas flag no código.
- INC-01 natural, sem dump de campos técnicos, fiel aos dados e honesto sobre prova de `último`.
- INC-02 busca empresarial adequada quando capability publicada/autorizada; sem alucinação de catálogo ou suppress indevido de contexto.
- INC-03 reconhece intenção de usar DAVI e vincula ao pedido anterior, se catálogo/permite; ausência real informada corretamente.
- Real tests de generalização, autorização negativa, source-unavailable e task outcome no SHA/config testado.
- CP5 permanece separado: correção de timeout não se confunde com pipeline CRI, discovery ou continuidade conversacional.

**Status final deste registro:** `OBSERVATIONS_REGISTERED=YES`; `PROD_CRI_EFFECTIVE=NOT_VERIFIED`; `INC01=OPEN`; `INC02=OPEN`; `INC03=OPEN`; `ROOT_CAUSES=TO_INVENTORY`; `IMPLEMENTATION=NOT_STARTED`; `CP5=IN_PROGRESS_USER_REPORTED`; `PRODUCTION_CHANGE=NONE`; `I04_ACCEPTED=NO`.


## Evidência adicional — sequência “use o davi” → “o mcp davi” (22/10/2026, ~13:29)

Duas novas capturas fornecidas pelo usuário mostram o follow-up **na mesma conversa**, após os exemplos genéricos de terminal bala. Primeiro, `use o davi` levou à resposta de desconhecimento do nome (INC-03). Em seguida, com a reformulação literal `o mcp davi`, a atividade registrou **Solicitação recebida** (completa), **Entendendo a solicitação** (completa), **Capacidade selecionada: DAVI** (completa), **Consulta finalizada: consulta falhou / api-delpi** (erro), **Atividade bloqueada** e mensagem **Fonte indisponível; não consegui consultar a fonte autoritativa**. Nenhum dado operacional foi verificado nessa tentativa.

**PROVEN_VISUAL:** a expressão explícita `mcp davi` levou à seleção visível do especialista DAVI, diferentemente de `use o davi`; a atividade tentou um caminho de consulta e falhou; a projeção de falha cita `api-delpi`. A mudança de comportamento com o follow-up constitui cenário de generalização/continuidade de contexto a testar, sem prescrever heurística lexical.

**NÃO PROVADO:** se `api-delpi` é um downstream do DAVI, um owner/provider diferente ou apenas uma projeção incorreta de provenance; a origem da falha (AuthZ, MCP transport, schema, domain, timeout, seleção incompatível); o request/response do owner; CRI efetivamente ON; eventual desvio de seleção; se o catálogo DAVI tem busca de material por descrição; se os `prior_turns` foram consumidos. `SOURCE_UNAVAILABLE` visível não comprova causa até inspeção de correlation IDs e logs.

**Critério adicional de reprodução:** iniciar uma única conversa: `2 exemplos de terminal bala` → `use o davi` → `o mcp davi`. Capturar as três requisições correlacionadas (turn/session IDs), `prior_turns`, admission/selection, live catalog, selected owner/capability, invocations efetivas, Core/Domain authorization, downstream owner ref, provenance `api-delpi`, real error_code, request outcome, CRI composer e versão produtiva. Comparar com outras referências anafóricas/contextuais e especialistas; não resolver com regra especial `davi`/ `mcp davi`.

**Coordenação:** observar o CP5 já em execução antes de implementar correção paralela; adicionar esta evidência à revisão posterior. `INC03_REPRO_EVIDENCE=EXPANDED`; `MCP_DAVI_SELECTION=PROVEN_VISUAL`; `OWNER_INVOKE_SUCCESS=NO_EVIDENCE`; `API_DELPI_FAILURE_CAUSE=TO_INVENTORY`; `INCIDENT_OPEN=YES`.


## INC-04 — Painel lateral Contexto sem evidência/atividade útil visível (~13:31)

**Nova captura fornecida pelo usuário:** na mesma conversa com `2 exemplos de terminal bala`, o painel lateral **Contexto** está aberto e mostra as seções `Detalhes`, `Evidências` e `Atividades`, mas exibe a instrução `Selecione uma mensagem para ver mais informações.` A resposta central continua com `Sem fonte vinculada` e `HYPOTHESIS`. O usuário relata ausência de informação suficientemente útil de contexto, seleção, fontes, logs de atividade e integração backend/frontend para investigar por que DAVI não foi utilizado.

**PROVEN_VISUAL:** a estrutura de navegação do painel existe; nenhuma mensagem aparece selecionada na captura; o painel não exibe detalhes da mensagem ou rastreabilidade nesse estado. **NÃO PROVADO:** que selecionar explicitamente a mensagem também deixe o painel vazio, que a API não forneça os envelopes necessários ou que toda a integração frontend/backend esteja ausente. O screenshot isolado não permite diferenciar UX discoverability/selection-state de lacuna contratual, producer, parser ou deployment drift.

**Requisito de produto:** a DÉLIA deve permitir ao usuário compreender em linguagem simples e segura **o que foi feito e o que foi ou não verificado**. Ao selecionar uma mensagem, quando houver dados, exibir estado factual da execução, owner e capability efetivamente selecionados, fonte autoritativa consultada, resultado/erro classificado, horário, evidência e limitações. Em respostas sem consulta, comunicar claramente `sem fonte consultada` e `exemplos gerais`, e por que não houve grounding **somente quando a razão for observada e autorizada para exibição**. Não expor chain-of-thought, prompts internos, tokens, RBAC sensível, payloads MCP brutos ou logs de infraestrutura ao usuário. Logs técnicos permanecem backend/audit e se relacionam por correlation ID redigido.

**Inventário fechado para próximo frontend/backend follow-up:** identificar componentes de Contexto/Detalhes/Evidências/Atividades em `plugins/delia` e compartilhados em `plugins/plugin-ui`; contrato `InteractiveTurnResult`, `presentation.v1`, `ActivityEvent.v1`, NDJSON activity channel, `provenance`/limitations; mapear produtor→transporte→parser→state/store→seleção de mensagem→render. Reproduzir com (a) resposta HYPOTHESIS sem fonte, (b) grounded DAVI/TÉO, (c) falha SOURCE_UNAVAILABLE, (d) PROCESSING_TIMEOUT/retry. Capturar estado com e sem mensagem selecionada. Distinguir `producer_missing`, `transport_missing`, `parser_drop`, `selection_state`, `render_not_integrated`, `runtime_stale`; testar um caso por camada, corrigir no owner correto sem duplicar contracts nem inventar eventos.

**Integração de experiência:** o painel deve fornecer caminho evidente para selecionar mensagem e inspecionar detalhes reais, com empty state honesto e acessível; evitar click que pareça não funcionar. Exibir ao usuário a trilha explicável, **não** logs internos completos. Este é um requisito de UX+contrato independente da ativação do CRI: resposta conversacional boa e observabilidade da execução são duas dimensões distintas.

**Status:** `INC04=OPEN`; `CONTEXT_PANEL_PRESENT=PROVEN_VISUAL`; `MESSAGE_SELECTED=NO_VISUAL_EVIDENCE`; `FRONTEND_API_INTEGRATION_COMPLETENESS=TO_INVENTORY`; `USER_FACING_TRACEABILITY=INADEQUATE_IN_CAPTURE`; `CODE_CHANGE=NONE`; `CP5=IN_PROGRESS_USER_REPORTED`.

## Fechamento INC-01 — ativação produtiva do CRI (22/10/2026, ~18:40)

- Causa-raiz da prosa mecanizada confirmada no host real: `DELIA_RESPONSE_INTELLIGENCE_ENABLED` ausente do `infra/.env` produtivo → compose injetava `""` → `delia_response_intelligence requested=baseline effective=baseline`, `decision=fail_closed reason=invalid_env_value`; todos os turns logavam `stage=response_mode decision=baseline`.
- A enumeração de campos era o **render determinístico baseline** (`_render_synthesis`), não o CRI: rótulos snake_case brutos, UUID e ISO `created_at` verbatim.
- Fix mínimo no owner canônico (`orchestration.py`): âncora em código de negócio sobre UUID, humanização de rótulos não mapeados, supressão de folhas UUID, formatação pt-BR de datas — sem novo planner/composer (RED→GREEN, suite completa verde).
- Deploy governado: pull ff para `d3de1b9c8`, backup `.env.bak-cri-activation-20261022-184008`, `DELIA_RESPONSE_INTELLIGENCE_ENABLED=true`, `up-prod-sequential.sh --build delia-api`, imagem `d543c6a7b358`.
- Startup verificado: `requested=cri effective=cri`; instruction resource v2 (`d5d0f75d…`); presentation vocabulary v3 (`24d6c126…`); container healthy.
- Resposta CRI para a pergunta do incidente (composição determinística verificada): `O registro mais recente entre os retornados foi PROC-0080 — Monitoramento e Análise dos Indicadores de Estoque.` + `A data mais recente encontrada foi 15/10/2026 às 15h43; a fonte não comprova que ela represente uma alteração.`
- Smoke real do usuário (pergunta literal na UI): pendente de sessão real — não se cunhou credencial de teste em produção. Relatório completo: `95-cri-production-activation-and-natural-response-verification.md`.
- INC-02/INC-03 (seleção DAVI e continuidade) e INC-04 (painel Contexto) seguem fora de escopo, como frentes próprias.


## Smoke real pós-deploy e requisito de transparência do compositor — 22/10/2026 (~15:46)

O usuário realizou em produção a pergunta `qual u ultimo proceso caastrado no transformometro?` (grafia conforme screenshot). Capturas mostram: especialidade **TÉO** selecionada, consulta finalizada, `transformometro-api` com **1 registro localizado** e informação de 76 registros no total, resposta sobre `PROC-0080`, rodapé com fonte e timestamp 22/10/2026 15:46, evidência `OBSERVATION` e especialista `teo`. A resposta contém lista com rótulos de campos humanizados e o fragmento isolado `Ori` após a descrição. O usuário relata que a prosa ainda parece mecanizada/incompleta.

**PROVEN_VISUAL:** a consulta autoritativa foi representada como concluída e a UI mostra proveniência e resposta parcialmente organizada após a ativação. **NÃO PROVADO POR CAPTURA:** evento de runtime `stage=response_mode decision=cri`, compositor efetivo nesta mensagem, se `Ori` foi truncado pelo owner, transformação E3, streaming ou render, se `PROC-0080` é último globalmente cadastrado, e se a UI já transporta metadados de tratamento da resposta. `CRI_REAL_USER_SMOKE=PARTIAL/PENDING_TRACE_CORRELATION` (não declarar PASS antes de correlacionar evento com request real).

**Novo requisito de observabilidade user-facing — decisão proposta para validação de contratos existentes:** separar claramente (a) fonte autoritativa de fatos (`transformometro-api`), (b) especialista/capability e etapas realmente executadas, (c) **modo efetivo de composição por mensagem** (`CRI`, `baseline`, `grounded synthesis` ou fallback conforme contrato), incluindo se houve transformação de apresentação e limitações. Preferir etapa honesta no fluxo `Resposta organizada com CRI` quando e somente quando o produtor emitir evidência de sua execução; resumo adicional em Detalhes/Contexto. Não apresentar flag global como prova de uso de CRI naquela resposta; não inventar novos campos antes de inventariar ActivityEvent/Evidence/Presentation e frontend state. Não confundir CRI determinístico com geração de prosa por LLM, não expor chain-of-thought, prompts internos, payloads MCP ou tokens. Caso baseline: informar que os dados foram apresentados sem composição CRI quando comprovado.

**Residual deliberadamente adiado pelo Product Master:** investigar fragmento `Ori` e qualidade/naturalidade da prosa mais tarde, com rastreamento owner payload → typed projection → E3/baseline → transporte NDJSON → markdown/frontend render. Não atribuir antecipadamente ao LLM, nem corrigir agora com heurística lexical. `INC05_PARTIAL_RENDERED_TEXT=OPEN_DEFERRED`; `CRI_COMPOSER_VISIBILITY=PLANNED_CONTRACT_INVENTORY`; `PRESENTATION_TRACE_REQUIRED=YES`; `NO_CODE_CHANGE_THIS_RECORD`.


## INC-06 — Repetições pós-ativação CRI: timeout intermitente, fragmento "Ori" e variação semântica (22/10/2026, ~15:52–15:54)

Novas capturas de testes **em conversas limpas** fornecidas pelo Product Master. A pergunta `Qual o último processo cadastrado?` foi repetida três vezes: uma interação terminou `Atividade bloqueada` / `Processamento interrompido` (timeout; nenhuma fonte verificada), duas interações concluíram com registro `PROC-0080` da fonte `transformometro-api`, mas ambas continuam apresentando o fragmento isolado `Ori` após a descrição. A resposta é uma listagem de campos humanizados, não prosa plenamente natural. Um outro teste `qual a descrição 10080043?` retornou registro de produto/código com fonte DELPI e campos descrição, group code e tipo. A pergunta `qual o primeiro processo cadastrado no transforma+?` terminou em timeout/processamento interrompido (duas capturas de diferentes estados dessa falha). Segundo a observação do usuário, o entendimento/seleção do TÉO em uma interação lenta consumiu aproximadamente 20 segundos; **latência por estágio não é comprovável apenas pela imagem**, requer traces.

**PROVEN_VISUAL:** variação entre timeout e resposta para pergunta repetida; `Ori` reproduzido em pelo menos duas respostas independentes; resposta de produto com dados da fonte; timeout na pergunta sobre primeiro processo; um caminho sem fonte verificada é classificado honestamente como processamento interrompido, não como falha de Domain API. `PROD_MAX_GOVERNED_ATTEMPTS=1` no último deploy documentado; não presumir que recuperação de duas tentativas esteja habilitada. **TO_INVENTORY:** timings de admission/select_group/select_capability/args/CRI, orçamento restante ao iniciar cada estágio, causa exata de timeout (provider vs budget), modelo/provedor efetivo em cada turn, CRI realmente usado por turno (`stage=response_mode decision=...`), origem do `Ori` (owner leaf / sanitization / composer / streaming / frontend), por que a pergunta do primeiro processo tem latência diferente, contextual payload/`prior_turns` e semantic event order/coverage. **Não assumir que a causa é exclusivamente o LLM nem que a recuperação governada já está ativa em produção.**

**DECISÃO DO PRODUTO:** continuar sequencialmente a execução planejada dos itens **4 Inteligência contextual**, **5 Painel Contexto**, **6 Homologação e ativação**, após tarefas 1–3 implementadas. Adiar investigação/correção individual dos novos resíduos até depois dessa sequência, mantendo-os como casos de regressão e observabilidade na etapa 6. Proibir correção por regex/keywords/provedor, afrouxamento oportunista de deadline, aumento de budgets sem decisão e direcionamento fixo para TÉO. Preferir modelo compreender intenção/contexto com capabilities publicadas e fallback honesto; avaliar continuidade multi-turn de fato, mas não confundir sessões limpas (sem `prior_turns`) com regressão de continuidade.

**Cenários para homologação futura (correlation ID/trace necessário):**
1. `Qual o último processo cadastrado?` repetido em sessões limpas, variância de latency e `Ori`;
2. `qual o primeiro processo cadastrado no transforma+?` e pergunta sem erro ortográfico: semântica de ordenação e coverage sem inventar último/primeiro global;
3. `qual a descrição 10080043?`: grounding de catálogo, apresentação e provenance;
4. `2 exemplos de terminal bala` → `use o davi` → `o mcp davi` na MESMA conversa, para comprovar `prior_turns` e capabilities;
5. CRI ON/OFF efetivo por resposta, resultado apresentado, status UI, ActivityEvent e painéis Detalhes/Evidências/Atividades;
6. timeout de seleção do owner antes da consulta, limitadores reais, eventual retry 2/60/30 somente após gate de revogação e autorização produtiva.

**Status:** `INC06=OPEN_DEFERRED`; `REPEATED_ORI=PROVEN_VISUAL`; `INTERMITTENT_PROCESSING_TIMEOUT=PROVEN_VISUAL`; `PROD_RETRY_ACTIVATION=NO_LAST_VERIFIED_CONFIG`; `SEMANTIC_ROOT_CAUSE=TO_INVENTORY`; `ITEMS_4_5_6=NEXT_BOUNDED_SEQUENCE`. Nenhum código ou deploy alterado neste registro.


## Fechamento INC-02/INC-03 — continuidade contextual e seleção semântica (doc 96)

A cadeia foi inventariada de ponta a ponta no HEAD vigente e as duas lacunas reais foram corrigidas no owner canônico (`orchestration.py`, instruções versão 12→13):

- **INC-02 (`terminal bala` sem consulta DELPI):** `openapi:delpi` expõe `delpi.search_products`/`get_product_summary` e `mcp:davi` expõe `discover_delpi_information` + READ candidate-bound. A instrução de admission não distinguia "exemplos de item de catálogo" de exemplo conceitual — agora prefere `ambiguous` (owner-bound) quando o item pode ser entidade registrada; verificação live resolveu o caso para `openapi:delpi`.
- **INC-03 (`use o davi` / `o mcp davi`):** a seleção de grupo era o único estágio semântico sem canal de contexto — `prior_observation` (projeção bounded, untrusted, já existente um nível abaixo) passa a alimentar `_group_summaries` e a seleção estrangeira; a instrução passa a declarar que resolver referência/nome de fonte contra `display_name`/`owner`/`source_system` é trabalho do estágio. Live: `use o davi`→`mcp:davi`, `o mcp davi`→`mcp:davi`, `agora use outro especialista`→`mcp:davi` (anáfora resolvida para owner distinto do anterior).
- **`api-delpi` na UI:** é o `owner_ref` canônico do DAVI (`_SPECIALIST_IDENTITY`) — proveniência honesta, não defeito. A classe da falha de invoke do T3 não pôde ser reproduzida (logs do turno anterior ao recreate); a cadeia contract→schema→owner está verificada e recusa argumentos inventados fail-closed.
- Latência do modelo ≤3B CPU-only segue limite documentado (doc 93): estágios esgotam o cap de 30s → `PROCESSING_TIMEOUT` honesto; nenhum deadline ou compensação lexical foi alterado.
- Status: `INC02=ROOT_CAUSE_FIXED`, `INC03=ROOT_CAUSE_FIXED`, `API_DELPI_LABEL=HONEST_PROVENANCE`, `EXTERNAL_LLM_CALLS=0`. Relatório: `96-contextual-intelligence-davi-multiturn-remediation.md`.


## INC-07 — Browser smoke após deploy do Prompt 5: observabilidade real e inconsistências de UX (22/10/2026 ~18:03–18:07)

Capturas de usuário no Portal produtivo, após deploy informado pelo Product Master enquanto a subetapa 5.1 de GPU Ollama continua executando:

- Turno `ola`: resposta social sem fonte. Painel Contexto visivelmente preenchido, com composição `Apresentação determinística`, modelo configurado `moonshotai/kimi-k3`, owner `DELPI`, `27,5 s`, `4` chamadas, uso **parcial** 3749 tokens entrada/540 saída, custo indisponível. Linhas técnicas incluem `interaction_admission` timeout 6 s, `turn_goal` 3,2 s, `select_group` 5,9 s e `turn` timeout 12 s. A ausência de fonte para saudação não é um defeito em si.
- Turno `qual o ultimo processo cadastrado?`: painel do turno correspondente mostra especialista `teo`, capability `record_read`, modo efetivo `Resposta organizada com CRI`, 23,4 s, 5 chamadas, 10071 tokens entrada + 1253 saída (total 11324 reportado), fonte `transformometro-api`, limitação `insufficient_evidence`. Resposta corretamente não afirma último global porque ordenação/cobertura não comprovadas. A atividade mostra consulta ao owner concluída e registros localizados.
- Follow-up `tente novamente`: turno terminou com mensagem de orçamento/tempo esgotado, sem fonte vinculada, mas cabeçalho/área de atividade mostra `Atividade concluída` com iconografia de advertência em algumas telas. Não há prova visual de que a interação manteve/consumiu o contexto anterior. Painel do turno anterior permanece aberto em algumas capturas; testar se o estado de seleção é explícito e todos os campos isolados por `turn_id`.
- UX do painel expõe nomes de estágios internos `delia.capability_orchestration.*`, abreviações `E`/`S` e limitações como `turn_budget_limited`/`insufficient_evidence` sem tradução user-facing; possibilitar nomenclatura amigável ancorada em códigos tipados e preservar diagnóstico técnico em área autorizada, sem string-rewrite de conteúdo livre.

**Evidência:** `CONTEXT_PANEL_BROWSER_SMOKE=PASS_PARTIAL` para abertura/seleção e dados reais em produção; `PER_TURN_OBSERVABILITY=PROVEN_VISUAL`; `ACTIVITY_RESULT_STATUS_CONSISTENCY=TO_INVESTIGATE`; `CONTEXT_SELECTION_ISOLATION=TO_TEST`; `FRIENDLY_LABELS=OPEN_UX_RESIDUAL`; `FOLLOWUP_PRIOR_TURNS_CONSUMPTION=TO_INVENTORY`. Não atribuir origem dos timeouts ao deploy do painel. Correlacionar turn IDs, activity phases, outcome status, response mode, model-call timings e schema do frontend/backend para qualquer decisão de correção.

**Sequenciamento:** manter 5.1 executando sem interferência; etapa 6 inclui QA de status, seleção de turnos, labels amigáveis, semântica de contexto e teste de follow-up. Não liberar retry produtivo enquanto revogação intra-turno permanecer sem decisão. Nenhuma alteração de código/deploy neste registro.


## INC-08 — Contexto parece seguir último turno e barra azul de seleção sem affordance clara (22/10/2026 ~18:07)

Product Master observa nas capturas após deploy da Etapa 5 que o painel Contexto **parece sempre mostrar dados da última resposta** e que a última resposta apresenta uma **barra vertical azul-clara à esquerda**, sem significado explicado ao usuário. Barra visual presente nas screenshots; origem exata em CSS/state não verificada. Hipóteses: estado `selectedTurnId` acompanha automaticamente a resposta mais recente, falha na troca de seleção, ou borda/indicador de foco/seleção intencional porém pouco compreensível. Imagem sozinha não prova cross-turn leakage.

**Obrigatório no QA pós-etapa 5:** conversa com ≥3 respostas de características distintas (saudação sem fonte; TÉO com fonte/CRI; timeout), selecionar deliberadamente 1ª, 2ª e 3ª pelo affordance real `moreActions`/Ver contexto; para cada seleção conferir ID/correlation, modelo, usage, custo, fonte, specialist, capability, events, composer, limitations e timestamps. Selecionar última e depois anterior, enviar quarto turno com painel aberto e verificar se seleção permanece intencional ou muda conforme contrato; testar fechar/reabrir, estado vazio, foco/teclado. Distinguir `AUTO_SELECT_LAST`, `SELECTION_NOT_UPDATED`, `DATA_CROSS_TURN_MIX`, `SELECTION_VISUAL_CUE_UNCLEAR` e justificar qualquer comportamento automático.

**UX esperada:** estado selecionado identificável e acessível, sem barra ornamental não explicada; pode manter indicador se seu significado for consistente (e.g. `Mensagem em foco no painel Contexto`) e visualmente discreto. Alternativa usar destaque do cartão/ação com semântica acessível, preferindo componente compartilhado. Não corrigir visual apenas removendo CSS antes de provar owner/seleção; não criar novo store ou duplicar ContextPanel.

**Status:** `INC08=OPEN`; `BLUE_SELECTION_BAR=PROVEN_VISUAL`; `PANEL_ALWAYS_LATEST=USER_REPORTED_TO_VERIFY`; `CROSS_TURN_DATA_LEAK=NOT_PROVEN`; `GPU_5_1_IN_PROGRESS`; registrar como residual da Etapa 5 / QA da Etapa 6. Nenhum código nem deploy alterado.
