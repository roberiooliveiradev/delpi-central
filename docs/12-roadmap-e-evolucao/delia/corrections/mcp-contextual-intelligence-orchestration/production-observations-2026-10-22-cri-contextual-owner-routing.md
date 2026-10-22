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
