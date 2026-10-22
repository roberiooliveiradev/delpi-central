# 88 — DÉLIA: Governed LLM Timeout Classification, Checkpoint & Resume

**Data:** 2026-10-22  
**Estado:** PRODUCT_DIRECTION_APPROVED; ARCHITECTURE_DECISION_REQUIRED for execution/continuation contract; IMPLEMENTATION_NOT_YET_EXECUTED  
**Escopo:** incidente singular/plural e continuidade de interação DÉLIA; sem mudança de runtime neste documento.  
**Base da inspeção:** HEAD GitHub `2d15472d5c23ff3789110254a886dbc7b89bccf9` no início da inspeção; revalidar HEAD, origin/main e authorities antes de executar.  
**Referências:** 73–87 da trilha CRI/MCP, especialmente 83, 84, 85, 86, 87 e sua revisão de coordenação; ADR 58; `delia-api/app/application/interaction/turn_budget.py`; `delia-api/app/application/capability_provision/orchestration.py`; `delia-api/app/application/interaction/contracts.py`.

## 1. Decisão de produto — explicitamente aprovada pelo usuário

Uma única pergunta do usuário deve originar uma **interação lógica contínua**. Falha intermitente, lentidão ou timeout do modelo externo **não** devem obrigar o usuário a repetir a pergunta, perder seleções já verificadas ou reiniciar manualmente o atendimento. A DÉLIA deve distinguir falha de modelo/transport, orçamento de tentativa síncrona, falha do MCP/domain, rejeição de autorização e insuficiência factual. Se houver um caminho de recuperação tecnicamente válido, prossegue automaticamente do último checkpoint válido e entrega o resultado na mesma interação.

A interface só pode indicar **"continuando"** se houver uma execução realmente continuada com estado acessível, observabilidade e mecanismo de entrega. Não afirmar continuidade se o backend cancelou o trabalho. Não inventar fontes, fatos, permissões nem um estado de sucesso enquanto o owner não respondeu.

**Regra congelada neste nível:** `30s` é limite da tentativa síncrona atual, não autorização para descartarmos trabalho útil. Não reiniciar o deadline dentro da mesma requisição e não aumentar silenciosamente o teto global: o transporte/gateway pode fechar a conexão independentemente. Continuação além do deadline requer boundary persistente, lifecycle governado e contrato com frontend.

## 2. Evidência factual e delimitação do problema

**PROVEN no código inspecionado:** `TurnDeadline.start(total_seconds)` define uma única janela monotônica; `stage_timeout` usa `min(configured_max, remaining_seconds)`; `TurnBudgetExhausted` impede iniciar estágios novos depois do prazo. O `OperationalCapabilityOrchestrator.attempt` captura `_StageDeadlineExceeded` (`model_timeout` / `turn_budget_exhausted`) e `TurnBudgetExhausted` e devolve `GovernedCapabilityStatus.SOURCE_UNAVAILABLE` com `error_code`. Esse mapeamento mistura falha de tempo do modelo/tentativa com indisponibilidade de fonte **antes de qualquer MCP invoke**, embora preserve parte da causa em `error_code`.

**Evidência de executor (não reexecutada nesta decisão):** doc 87 reproduziu P1 singular com duas falhas pré-invoke de deadline, uma execução GROUNDED correta via TÉO e novo timeout; P2 plural concluiu. O skip do `grounded_synthesis` descartado quando CRI compõe foi implementado e revisado em GitHub; **não** resolve starvation pré-invoke. A causa do incidente original em produção permanece `INCONCLUSIVE` sem logs/versão produtiva e replay autenticado. Não afirmar que não existe qualquer regex no repositório; não há evidência de regex causando a variação observada.

**TO_INVENTORY:** persistência real de interaction/work, checkpoints, streaming/reconnect, activity status/outcome, job lifecycle, idempotência, cancelamento, classificação de `ModelInvocationError`, budgets da UI/gateway e correspondência entre resultados do mesmo turno. Documentação não é prova de runtime. O código `InteractionTurnResult` já carrega `limitations`, `grounding_status`, `provenance`, `message_kind`/ `owner_hint`: não criar outro response envelope antes do inventário.

## 3. Modelo de falha que o consumidor precisa distinguir

O mapeamento exato deve reutilizar os enums/códigos canônicos após inventário, sem inventar taxonomia paralela. As seguintes classes são **requisitos semânticos**, não enums aprovados:

| Causa classificada | Momento da falha | Contrato de UX |
| --- | --- | --- |
| LLM stage timeout | Antes/depois de seleção; nenhuma prova de falha do owner | processamento atrasado; retry/resume governado se suportado |
| LLM provider/transport unavailable | Erro externo comprovado de modelo/rede | indisponibilidade temporária de processamento, não "fonte DELPI indisponível" |
| Sync turn budget exhausted | Janela síncrona expirada, estágio conhecido | continuidade quando suportada; senão interrupção honesta, sem promessa falsa |
| MCP/domain source unavailable | Invocação owner falhou realmente | fonte indisponível com proveniência da falha |
| Domain/Core AuthZ denied | Decisão backend de autoridade | negar sem tentar contornar via outro provider |
| Evidence insufficient | Consulta válida com dados insuficientes | limitação epistemológica, não falha técnica |
| Owner contract rejection | Argumento rejeitado pela API | recovery bounded já existente quando autorizado; nunca inventar permissão |

HTTP 200, resposta sintética, decisão do modelo ou metadados MCP não provam business outcome.

## 4. Continuidade: decisão de comportamento (não novo serviço)

Fluxo desejado:

`INTERACTION_ID → typed stage proposal/evidence → checkpoint → error classification → bounded retry (if safe) → resume same interaction → authoritative outcome → notify original UI`

**Checkpoint mínimo proposto (contrato a validar, não esquema novo autorizado):** interaction/turn ID, correlation ID, etapa concluída e etapa pendente, proposals tipadas válidas, owner/capability/catálogo com referência e versão, argumentos previamente validados, evidências/snapshots com proveniência e expiração, budgets de tentativas, status de retry, estado de entrega e auditoria. Não armazenar chain-of-thought, prompt bruto sensível, token, segredo, autoridade serializada/cached, biometric match como AuthZ ou payload de provider não sanitizado. Personal Memory não é checkpoint nem fonte autorizadora.

**Reuso/revalidação:** conservar decisões determinísticas/tipadas e evidências ainda válidas; revalidar autorização live do Core e regras da Domain API antes da nova invocação; revalidar schema/capability ao retomar e não usar resultado expirado como fato atual. O modelo pode reinterpretar quando contexto mudou. Não persistir propostas do LLM como fatos.

**Retry versus resume:** retry = uma chamada idempotente/read-only ao mesmo estágio dentro da janela disponível, bounded e observável. Resume = nova tentativa governada vinculada à mesma interação depois do fechamento da janela síncrona, dependente de persistência e entrega reais. Uma chamada ao modelo pode continuar no provider depois de timeout: não assumir cancelamento físico, evitar duplicação ilimitada, contabilizar tentativas, custo e race de conclusão.

**Gates de ação:** somente READ/propostas puras podem ser repetidos conforme validade. PREPARE requer idempotência/revalidação, ACT nunca pode ser reexecutado automaticamente por uma falha ou timeout sem verificar authoritative outcome, estado de commit e os gates identity → Core AuthZ → Domain authority → Policy/Decision → confirmation → idempotency → audit → execution → postcondition. A DÉLIA não vira scheduler paralelo; procurar mecanismo previsto em Interaction/Work e Automation Hub antes de definir lifecycle.

## 5. Experiência frontend proposta

Uma interação original mantém `user_turn_id`/`activity_id`; o avatar/atividade apresenta estados reais: PROCESSING, RETRYING_MODEL, CONTINUING, VERIFYING, COMPLETED, BLOCKED (nomes ilustrativos — verificar enum vigente). Exemplo de mensagem durante retomada legítima: "Estou continuando sua consulta. O processamento demorou mais que o esperado; vou retomar a etapa pendente." Quando não existe continuidade: "O processamento demorou além do limite e foi interrompido. Não identifiquei falha na fonte de dados." Nunca renderizar "Fonte indisponível" por timeout de modelo pré-MCP.

Retorno pela mesma atividade, entrega única, tolerância a refresh/reconnect, sem duplicação de resultados, cancelamento visível e terminal honesto. Suportar usuário navegando no Portal **apenas** se o transporte/event store já possuir esse contrato. Preferir componentes plugin-ui existentes; não inventar timer pulsante como prova de execução.

## 6. Decisão de ownership e arquitetura

- DÉLIA Interaction/Application: execução lógica, evidence, classificação, policy/decision e outcome; a continuidade do *trabalho lógico* pertence à DÉLIA.
- Domain APIs: facts, business semantics, final authorization/rules/postcondition.
- Core/Keycloak: identidade/contexto e live AuthZ; JWT não é permissão final.
- MCP/A2A: transport/discovery; outputs são untrusted data.
- Automation Hub: execução técnica apenas quando existente/legítima e autorizada, não segundo planner.
- Frontend/plugin-ui: renderiza estado recebido; não inventa execução nem armazena credenciais.
- Gateway/proxy: timeout síncrono independente do lifecycle de jobs.

Aplicar Clean Architecture + Ports/Adapters e boundary real se alguma nova extensão for autorizada. Respeitar ADR58 selection-only.

## 7. Reuse gate — ainda não autoriza novas abstrações

| Responsabilidade | EXISTING_EQUIVALENT | REUSE_DECISION |
| --- | --- | --- |
| Turn deadline monotônico | YES (`TurnDeadline`) | REUSE, preservar janela síncrona |
| Modelo de exceção de estágio | YES (`_StageDeadlineExceeded`, `ModelInvocationError`) | EXTEND mapeamento canônico após inspeção de consumers |
| Envelope de interaction/limitations | YES (`InteractionTurnResult` e contratos relacionados) | REUSE/EXTEND, condicionado a compatibilidade |
| Checkpoint persistente de Interaction/Work | TO_INVENTORY | TO_DECIDE |
| Background continuation, result delivery, reconnect | TO_INVENTORY | TO_DECIDE |
| Retry bounded por estágio e invocation cancellation | TO_INVENTORY | TO_DECIDE |
| UI activity-state transport/plugin-ui | TO_INVENTORY | TO_DECIDE |

`0 search results != inexistência`. Antes de criar capability/service/registry/queue/job/port/adapter, provar ausência do equivalente legítimo em DÉLIA Interaction/Work, Domain APIs, Automation Hub, Portal e contratos de atividades existentes. Não propor engine de retries nova por conveniência.

## 8. Plano de execução finito

**CP1 — Reanchor + inventário de consumers (read-only).** HEAD/origin/status, .cursor, authorities 16→50→17→49→51→52→21→20→25, arquitetura/product, specs temáticas, ledger. Rastrear call graph de timeout do modelo até activity/http/NDJSON/frontend, classificação error_code→status→message_kind; event/result store, reconnect e owner read-back. Produzir matriz responsabilidade/owner/fonte/consumers/contrato/código/teste/outcome. Gate reuse.

**CP2 — Corrigir classificação comprovada (small diff).** Teste RED: pre-MCP `model_timeout` ou `turn_budget_exhausted` NÃO resulta em texto "fonte indisponível"; falha real MCP continua SOURCE_UNAVAILABLE; authz continua falha fechada; insuficiência não vira timeout. Implementar no dono canônico dos erros, mantendo compatibilidade wire/observability. Testes unit/integration + frontend presentation quando aplicável. Não alterar timeout global.

**CP3 — Inventariar/checkpoint prototype via contratos existentes.** Verificar se um checkpoint tipado pode sobreviver a novo request/worker usando mecanismo existente. Teste: seleção concluída → timeout em arguments → retomar arguments (sem refazer seleção), revalidando authority e contrato; resultado entregue uma vez à interação original. Se não houver mecanismo legítimo de persistência/lifecycle, STOP→ARCHITECTURE_DECISION_REQUIRED; não persistir estado em arquivo/local memory do frontend como falso substituto.

**CP4 — Bounded retry/resume governado (apenas após gate).** Recovery somente de causas permitidas, max attempts/backoff/jitter e caps definidos em contrato real, sem unbounded restart; reconexão da UI e status real, idempotência/cancelamento. Respeitar fronteiras PREPARE/ACT e orçamento por tentativa. Se stage fica lento, preservar respostas/fatos já recebidos, não reiniciar interação lógica. Não adicionar outro stage LLM obrigatório.

**CP5 — Real eval e aceitação.** Injeção de demora/timeout determinístico em cada stage; model-provider unavailable, MCP error, auth denial, budget, disconnect/reconnect, restart, duplicate completion, expired schema/evidence, no ACT retry. Real model/MCP avaliação separada e repetida; percentis de latência, custo, completion rate, correctness of error class, retries/turn, outcome, logs por correlation. Reproduzir as duas perguntas originais do Portal no prod SHA verificado somente após autorização e infraestrutura; sem acesso, TEST_NOT_RUN e incidente de produção permanece OPEN.

**Sequenciamento:** CP1→CP2 podem ser executados como bounded correction após contrato; CP3 é prova de infraestrutura e gate; CP4 não inicia se CP3 não demonstrar owner/capability de continuidade; CP5 mede SHA/config executados. Evitar loops e refatoração geral de orchestration.py.

## 9. Invariantes e critérios de aceite

1. A pergunta original é enviada só uma vez pelo usuário.
2. Timeout de modelo antes do MCP jamais é rotulado como falha de fonte.
3. Classificação técnica e mensagem UX correspondem à evidência.
4. Nenhum trabalho válido é descartado sem motivo de invalidação; revalidar antes de reutilizar.
5. Expiração de uma janela síncrona não vira mais 30s na mesma request.
6. Continuation só é afirmada quando efetivamente persistida/executando.
7. Cada tentativa tem limites, audit, correlação e deduplicação de entrega.
8. Retomada inicia no último estágio válido, não refaz tool calls válidas arbitrariamente.
9. Sem reexecução automática material de PREPARE/ACT.
10. Sem aumento de authority por MCP, cache, JWT ou proposta de modelo.
11. Sem provider-specific heuristics, regex, catálogos clonados ou novo planner.
12. Contagem, proveniência, feedback e resultado final verificáveis.
13. Teste de generalização e segurança no SHA/config real; green tests não são business success.
14. CRI dev ON não prova CRI prod ON; gates de ativação/deploy continuam separados.

## 10. Evidência e status

`PRODUCT_DIRECTION=APPROVED` (uma pergunta, continuidade automática quando tecnicamente suportada); `CAUSE_MAPPING_DEFECT=PROVEN_STATIC`; `EXECUTOR_DEV_BUDGET_STARVATION=REPORTED`; `PROD_ROOT_CAUSE=INCONCLUSIVE`; `CHECKPOINT_RUNTIME=TO_INVENTORY`; `ASYNC_DELIVERY_RUNTIME=TO_INVENTORY`; `RETRY_STAGE_CONTRACT=TO_INVENTORY`; `CONTINUATION_IMPLEMENTED=NO`; `END_TO_END_TEST=TEST_NOT_RUN`; `PRODUCTION_CRI_ON=NOT_VERIFIED`; `I04_ACCEPTED=NO`; `C3_EXECUTED=YES_EXECUTOR_REPORTED`.

### 10.1 CP1+CP2 executados (2026-10-22, relatório 89)

`CP1_INVENTORY=DONE` — mapeamento completo model→attempt→interaction→
HTTP/NDJSON→MFE registrado no relatório 89; o defeito localizado em 4
sites (catch de `_StageDeadlineExceeded`/`TurnBudgetExhausted` em
`attempt()`, budget-skip de identificador, prior-continuation).

`CP2_CLASSIFICATION=FIXED` — novo membro `PROCESSING_TIMEOUT` em
`GovernedCapabilityStatus`; deadlines/budget nunca mais saem como
`SOURCE_UNAVAILABLE`; `error_code` preserva `model_timeout`/
`turn_budget_exhausted`; falha real de MCP permanece
`SOURCE_UNAVAILABLE`; AUTHZ fail-closed inalterado; insuficiência de
evidência inalterada. Mensagem terminal honesta ("processamento
interrompido… não identifiquei falha na fonte"), `message_kind`
`PROCESSING_TIMEOUT` aditivo ao contrato v1, badge MFE
"Processamento interrompido" (warning/TimerOff), atividade
`BLOCKED`/`FAILED`.

`CONTINUITY_INVENTORY=NONE_EXISTING` — sem persistência de
sessão/turno/atividade (request-scoped by design), sem reconnect, sem
engine de checkpoint/retry. Reusáveis para CP3: `correlation_id`,
`prior_turns` (contexto client-supplied), vocabulário ActivityEvent,
`TurnDeadline`/`stage_timeout`, `InteractiveTurnResult`. CP3 continua
`ARCHITECTURE_DECISION_REQUIRED` — não existe substrate legítimo de
persistência hoje.

`END_TO_END_TEST=PARTIAL` — boundary forçado em container real
(`turn_budget_seconds=0`, wiring real davi/teo/vista) comprova
`PROCESSING_TIMEOUT` end-to-end; caso natural depende de amostragem de
latência do modelo. `CHECKPOINT_IMPLEMENTED=NO`,
`RESUME_IMPLEMENTED=NO`, `PRODUCTION_ACTIVATION=NO`.

### 10.2 CP3 executado (2026-10-22, relatório 90)

`CP3_INVENTORY=DONE` — fluxo completo, matriz de estágios, estado em
memória, orçamento/transporte, recuperação existente, frontend e reuse
gate inventariados com evidências do código vigente; caracterização
executável em `tests/test_c3_ephemeral_continuity_characterization.py`
(7 testes PASS, sem alterar comportamento).

Fatores determinantes: resultados de estágio vivem como locais de
`_attempt` e morrem no raise — nunca exportados; o worker NDJSON é a
vida técnica da interação e o terminal único já é garantido pela fila;
nginx prod permite 86400s mas Cloudflare ~100s é o teto real (dev
default 60s); `_repair_once`/`_recover_owner_contract` são precedentes
de recovery bounded READ-only; `MAX_TIMEOUT_SECONDS=30` é teto duro por
invocação; sem idempotência no fio MCP; admission/synthesis/
index_select já degradam honestamente.

`EPHEMERAL_RECOVERY=TARGET` — decisão de produto: perda em refresh/
restart/disconnect aceita; persistência fora de escopo.

`ARCHITECTURE_DECISION=OPTION_B` — continuação efêmera vinculada ao
streaming: re-tentativa governada dentro do worker, checkpoint tipado
interno `_TurnExecutionState` (frontier + ids/refs/argumentos — nunca
CoT/credenciais), terminal único, cancelamento natural por disconnect,
zero contrato de fio/frontend novo. Opção A insuficiente (sem janela
restante quando o estágio esgota 30s); Opção C rejeitada (mesmo
resultado com store+contrato+dedupe adicionais — registrada como
fallback). Gate pendente para CP4: constantes explícitas de orçamento
total por interação (`DELIA_MAX_GOVERNED_ATTEMPTS`,
`DELIA_INTERACTION_TOTAL_BUDGET_SECONDS`) — o teto de 30s por tentativa
permanece; PREPARE/ACT nunca resumidos através do invoke.

`CHECKPOINT_RUNTIME=DESIGNED_EPHEMERAL`; `RETRY_STAGE_CONTRACT=DESIGNED`;
`CONTINUATION_IMPLEMENTED=NO`; `NEXT=CP4_GOVERNED_STAGE_RESUME` —
ver relatório [90](./90-cp3-ephemeral-continuity-and-llm-recovery-inventory.md).

## 11. Execution / review contract

Future execution report must carry: BASE_HEAD/FINAL_HEAD/origin; authorities+CP/RQ; EXISTING_EQUIVALENT/REUSE_DECISION per responsibility; error-code mapping before/after; checkpoint owner/schema/lifetime/storage; state transitions; transport/reconnect; effective authorization and TTL; resume stage; dedup/idempotency; cancellation and budget policy; RED/GREEN; negative safety; independent real-model+real-MCP eval; prod verification; files/commit/ledger; `ACCEPT|ACCEPT_WITH_RESIDUAL|REWORK|EXECUTION_DRIFT|INCONCLUSIVE`. A failed gate stops only the dependent continuation step; do not silently redesign.
