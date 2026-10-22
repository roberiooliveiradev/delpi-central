# DÉLIA — Conversation Queue v1: contrato implementável e gates de arquitetura

**Data:** 2026-10-22  
**Status:** CONTRACT_DRAFT / IMPLEMENTATION_NOT_AUTHORIZED / ADR_PENDING  
**Owner proposto:** `delia-api/app/application/interaction` (mesmo bounded context de `HandleInteractiveConversationTurn`).  
**Consumers:** MFE `plugins/delia`, componente compartilhado `ConversationQueue` via props; futuros Work consumers somente sob contrato próprio.  
**Base factual:** [121 — Runtime Inventory & Contract v1](./121-conversation-queue-runtime-inventory-and-contract-v1.md); [71 — UX Queue](./71-conversation-queue-and-my-work-ux-specification.md); ownership [17](./17-component-and-contract-map.md); fase [16](./16-execution-master-plan.md); modelo [21](./21-data-and-state-model.md).  
**Nota:** este documento refina o contrato para execução, mas não converte automaticamente propostas do doc 121 em decisões aceitas. Novas capacidades, armazenamento e fase dependem de ADR e do gate de execução.

## 1. Reuse Gate e responsabilidades

| Capability | Evidência no 121 | EXISTING_EQUIVALENT | REUSE_DECISION |
|---|---|---|---|
| Turn HTTP/AuthZ/model orchestration | `interaction_routes.py`, `HandleInteractiveConversationTurn` | YES | EXTEND |
| Cliente HTTP/UI | `interactionClient.ts`, `App.tsx` | YES | EXTEND |
| Visual | `ConversationQueue` em `plugin-ui` | YES | REUSE |
| Activity stream | `ActivityEvent.v1`, request-scoped NDJSON | YES | REUSE para turno, **não** para alterações offline na fila |
| TTL/lock/idempotency precedent | `PendingWriteStore` (somente write proposals) | YES_PARTIAL | REUSE PATTERN, **não compartilhar store nem autoridade** |
| Conversation identity | Não identificada no backend auditado | NO no escopo examinado | NEW sujeito a ADR-1 |
| Queue state/admission | Não identificados no backend auditado | NO no escopo examinado | NEW dentro do contexto `interaction`, sujeito a ADR-2 |
| Scheduler/technical execution | Sem equivalente legítimo para esta fila | TO_INVENTORY / fora do v1 | NOT_CREATE |

`0 results` não equivale a ausência global. Revalidar HEAD/código/autoridades antes de implementar.

## 2. Decisões impeditivas (não reconciliar silenciosamente)

**ADR-1 — `conversation_id`:** recomendação: criar uma identidade server-issued, escopada ao usuário e tenant, distinta de `InteractionSession.session_id` request-scoped e de `confirmation.session_id`. A emissão precisa de contrato de criação/recuperação, ciclo de vida, política de retenção e revogação; **não usar um ID local como autoridade**. A criação implícita na primeira admissão exige regra para primeira pergunta e reload; preferir contrato explícito caso o owner confirme necessidade.

**ADR-2 — armazenamento/consistência:** um process-local `RLock`/TTL não implementa autoridade de fila em multi-worker, restart, múltiplos pods ou balanceamento. O precedente `PendingWriteStore` autoriza **reutilização de padrões**, não a decisão de persistir a fila em memória. **Recomendação de segurança:** contrato v1 de produção somente com store compartilhado, isolamento tenant/actor, transações de claim e revisão monotônica, após inventário e aprovação do owner de dados/infra. Sem esse mecanismo comprovado, o recurso permanece OFF em produção; store local é permitido apenas para teste com marcação explícita `NON_PRODUCTION`. Não introduzir Redis, DB/schema ou dependência por suposição.

**ADR-3 — drenagem:** cliente pode **solicitar** execução explícita do item elegível, mas não ser fonte autoritativa de ordenação, lease, conclusão ou reprocessamento. A variante client-driven não entrega execução autônoma após fechamento da aba. Se o requisito é continuar automaticamente mesmo sem cliente, STOP: precisa de capability/owner e fase de Work/scheduler, não uma fila escondida em React. Antes de habilitar múltiplos itens, aprovar semântica exata de disparo pelo usuário e continuidade.

**ADR-4 — interação versus material action:** enfileirar uma mensagem não concede PREPARE/ACT, não confirma propostas anteriores nem autoriza repetir writes; comandos de `APPLY_PREPARED` e `REJECT_PREPARED` não podem entrar como texto livre e exigem gates originais, live AuthZ, confirmation e idempotência. Definir admissão ou exclusão explícita de comandos governados no v1; default recomendado: fila só de `MESSAGE`.

**Resultado:** sem ADR-1, ADR-2 e ADR-3 aceitas em authorities/ledger, `IMPLEMENTATION_GATE=BLOCKED`; preparar OpenAPI e testes é permitido, mas writes operacionais não.

## 3. State machine, domínio e invariantes candidatos

- `ConversationRef`: `conversation_id`, owner actor/tenant binding, `status`, `created_at`, `expires_at`, `revision`.
- `QueueItem`: ID opaco emitido pelo backend, `conversation_id`, `position`, `kind=MESSAGE`, payload armazenado segundo data policy, `display_title`, `status`, `depends_on_item_id?`, `created_at`, `expires_at`, `revision`, `started_turn_ref?`.
- **Estados de domínio:** `QUEUED | BLOCKED | RUNNING | COMPLETED | FAILED | REMOVED | EXPIRED`. `SUBMISSION_REQUESTED` e `ADMISSION_ACCEPTED` são eventos/etapas da API; `HEAD_ELIGIBLE` é elegibilidade derivada, **não status persistido**.
- Fila FIFO por `position`, com revisão; somente `QUEUED` elegível para move/removal. `BLOCKED` não executa enquanto condição verdadeira; dependência não é inferida por LLM.
- Invariante concorrente: **no máximo um RUNNING por conversa** se sequência serial for a direção aprovada; admissão + claim + revision são atômicos no owner e em todas as instâncias.
- Terminalidade de turno é distinta de **authoritative business outcome**. Item COMPLETED significa conclusão do processamento de turno, não conclusão de ação de domínio.
- Cancelamento de transporte `AbortController` não significa cancelamento backend: sem contrato de cancelamento autoritativo, item RUNNING continua até resultado/timeout e precisa reconciliar estado após desconexão.
- Um retry de `claim` nunca cria um segundo processamento do mesmo item; idempotência de admissão, claim e conclusão devem ser testadas.

## 4. Contrato HTTP proposto — sujeito a ADR e OpenAPI

Prefixo de API, convenção de erros e operationIds devem ser reconciliados com `interaction_routes.py` e OpenAPI existente; paths abaixo são **candidatos**, não rotas em produção.

| OperationId candidato | Método/rota candidata | Semântica | Sucesso |
|---|---|---|---|
| `createConversation` | `POST /conversations` | Emite referência autoritativa de conversa, vinculada a actor/tenant | 201 com id e revision |
| `enqueueConversationItem` | `POST /conversations/{conversation_id}/queue/items` | Admite MESSAGE sem executá-la | 201 com item + revision; retry idempotente |
| `getConversationQueue` | `GET /conversations/{conversation_id}/queue` | Snapshot autoritativo filtrado por AuthZ | 200 com revision + itens |
| `moveConversationQueueItem` | `POST /conversations/{conversation_id}/queue/items/{item_id}/move` | Move pendente elegível sob revision | 200 com snapshot reconciliado |
| `removeConversationQueueItem` | `DELETE /conversations/{conversation_id}/queue/items/{item_id}` | Remove pendente ainda não iniciado | 200 com snapshot reconciliado |
| `claimConversationQueueItem` | Extensão do `POST /interaction/turns` já existente | Claim de HEAD elegível e execução de MESSAGE | Resultado de turno existente + refs |

**CreateConversation request:** sem `actor_id` controlado pelo browser; subject/tenant resolvidos no backend e Core live. Retorno inclui `conversation_id`, `revision`, `expires_at`, `durability` verificada, sem promessa de persistência se indisponível.

**Enqueue request:** `{input: string, display_title?: string, idempotency_key: string, expected_revision?: number, depends_on_item_id?: string|null}`. Limites máximos condicionados aos contratos existentes; referência inicial: input 16384 chars, título <=120, count <=32, sujeitos a confirmação da segurança/domínio. Nunca logar texto livre em logs comuns. Campos extras rejeitados quando essa for a política vigente.

**Enqueue response:** `{conversation_id, item:{queue_item_id, status:"QUEUED"|"BLOCKED", position, display_title, eligibility, created_at, expires_at}, revision, request_id}`. Retentativa com mesma chave e mesmo payload retorna **a mesma admissão**; mesma chave/payload divergente retorna `409 idempotency_conflict`. HTTP 201 demonstra admissão, não processamento nem sucesso de negócio.

**GET response:** `{conversation_id, revision, items:[{queue_item_id, position, status, display_title, reason?, eligibility:{move_up,move_down,remove}, created_at}], next_eligible_item_id?, durability}`. Apenas pendências `QUEUED|BLOCKED` são projetadas para a mini fila; estados `RUNNING` e terminal devem ir à timeline/visão adequada, com referências separadas. Não projetar input integral em mini-fila por default.

**Move request:** `{direction:"up"|"down",expected_revision:number}`; resposta = snapshot atualizado, 409 `revision_conflict` com revision/snapshot atual autorizado, se política permitir. Restrições de dependência e `RUNNING` validadas no backend, não no booleano de UI.

**Remove:** exigir revisão condicional com `If-Match` ou campo aceito conforme convenção HTTP existente; remoção idempotente apenas quando o mesmo resultado terminal é demonstrável. Preferir resposta 200 com snapshot e revision; se opção 204 for adotada, revisão deve estar disponível por header e fetch subsequente. Não misturar as duas sem decisão.

**Turn binding:** estender `POST /interaction/turns` com `queue_item_ref:{conversation_id,queue_item_id,expected_revision?}` opcional, sujeito ao `ALLOWED_BODY_KEYS` real; resolver actor/tenant, validar HEAD/eligibilidade, claim atômico e vincular `session_id`/turn ID ao item. O texto autoritativo do item deve vir do owner, **não** aceitar novo `input` que substitua silenciosamente o texto originalmente admitido. Não retransmitir comando governado como `MESSAGE`. O processamento continua no `HandleInteractiveConversationTurn`; reconciliar sucesso/falha e atividade sem duplicar invocation.

## 5. Segurança, AuthZ e observabilidade

- Keycloak identifica subject. **Live Core AuthZ** `delia.access` e possession/tenant do recurso verificados em todas as operações; Domain rules adicionais aplicam-se a side effects materiais. `JWT != final authorization`.
- Não confiar em IDs, capability flags ou `eligibility` enviados pelo MFE; são somente intenções e hints.
- Proteção contra acesso cruzado entre conversa/tenant/usuário; status 404/403 sem vazamento de existência, de acordo com padrão existente.
- Audit trail de admissão, reorder, remoção, claim e terminalidade, com request IDs/correlation, não texto sensível. Segredos e bearer fora de prompt, memória, embeddings e logs comuns.
- Correlacionar `conversation_id → queue_item_id → interaction session/turn → ActivityEvent.v1 → outcome`. NDJSON continua apenas streaming de **turno em curso**, não feed global de fila.

## 6. Frontend contract / UX binding

- `plugins/plugin-ui` permanece render-only, sem API/permission logic.
- Criar/adaptar cliente HTTP **somente quando OpenAPI aceito**; de preferência extensão no padrão de `interactionClient.ts`, sem gestor paralelo de turnos.
- `plugins/delia/App.tsx` ou composição legítima resolve conversa ativa, snapshot revision e estados de leitura; callbacks invocam intents + aguardam retorno autoritativo; erro revalida snapshot; não faz scheduler loop.
- Mapear `queue_item_id→items[].id`, `display_title→label`, `position→ordinal`, `status QUEUED/BLOCKED→queued/blocked`, `eligibility→canMove*/canRemove`, `reason→reason`. Outras fases fora da mini fila.
- Enquanto backend/ADR estiver indisponível, `items=[]`, controles não operacionais, fixture QA gated; sem contagem ou sucesso fictícios.
- O ato de enviar enquanto ocupado não deve trocar de `draft→send` ou `draft→enqueue` implicitamente. UI precisa comunicar quando a ação é admitida, e **não limpar o draft após erro**.

## 7. Tabela de erros (proposta)

`unauthenticated(401)`, `forbidden(403)`, `conversation_not_found(404)`, `queue_item_not_found(404)`, `invalid_request(400)`, `not_eligible(409)`, `revision_conflict(409)`, `idempotency_conflict(409)`, `capacity_exceeded(429)`, `dependency_failed(409)`, `expired(410)`, `unavailable(503)`, `timeout(504)`, `internal_error(500)`.

Todos com `{code,request_id,message?}`; mensagens não vazam estado de terceiros. Error taxonomy deve ser confrontada com a convenção existente antes de congelar OpenAPI.

## 8. Contract tests obrigatórios antes de ativar

1. Admissão de MESSAGE, FIFO e limite de tamanho/count.
2. Retry idempotente igual; chave igual com conteúdo diferente → conflito.
3. Move/removal condicional com revision desatualizada.
4. Conflitos entre duas abas e entre dois workers/instâncias; somente um claim RUNNING.
5. Tentativa de claim não-HEAD, item expirado/removido ou conversa de outro actor/tenant.
6. Reconexão/reload e restart conforme durabilidade realmente aprovada.
7. Falha de turno, timeout e perda do cliente durante RUNNING; estado reconciliável.
8. Dependência: bloqueio, sucesso, falha; sem violar FIFO/eligibilidade.
9. PREPARE/ACT/confirmations e `STOP_RESPONSE` permanecem com suas regras sem que enqueue autorize side effect.
10. ActivityEvent/NDJSON, JSON fallback, UI full-page/Dock e regressões F03-A.
11. Kill-switch/feature admission OFF ⇒ nenhuma rota de escrita admitida; DÉLIA continua com fluxo de envio atual.
12. Outcome: turno COMPLETED não afirma business success; logs sem dados sensíveis.

Critérios: **PASS** somente em SHA/config real, evidência de transação cross-worker e postcondition; sem execução, `TEST_NOT_RUN`.

## 9. Ordem finita de implementação posterior

**Gate Q0 — decisão (NO CODE):** fechar ADR-1 identidade, ADR-2 store/consistência, ADR-3 semântica client-driven e ADR-4 escopo MESSAGE; registrar owner, fase/CP-RQ e acceptance.

**Gate Q1 — contrato primeiro (NO RUNTIME):** publicar OpenAPI `conversation.queue.v1` e schemas de request/response/erros com operationIds estáveis; compatibilidade aditiva com `interaction/turns`; validar testes de contrato red/fixtures.

**Gate Q2 — backend bounded:** implementar store e admission/GET/move/remove/claim no bounded context `interaction`, conforme decisão aprovada; reusar Core/turn processing; idempotência/atomicidade/observabilidade; default OFF até acceptance.

**Gate Q3 — MFE adapter:** conectar o `ConversationQueue` existente, trocar fixture por dados reais só quando habilitado e autorizado; evitar loops autônomos.

**Gate Q4 — validação:** testes unitários, contrato, concorrência cross-worker, E2E com usuário real, fallback, segurança, rollback e evidência de outcome; aceite independente antes de ON.

Cada gate termina com artefato verificável e no máximo um bounded rework; nova evidência que invalide owner/ADR ⇒ `EXECUTION_DRIFT`, não nova arquitetura silenciosa.

## 10. Estado factual desta entrega

`DOCUMENT=CONTRACT_DRAFT`; `RUNTIME_CHANGED=NO`; `OPENAPI_IMPLEMENTED=NO`; `ADR_1_2_3_4=PENDING`; `IMPLEMENTATION_AUTHORIZED=NO`; `TESTS=TEST_NOT_RUN`; `PHASE_PROGRESSION=NONE`.

**Critério de saída:** contrato suficientemente explícito para revisar, mas **não implementar produção** sem os gates de identidade e armazenamento. O documento 121 continua sendo a fonte do inventário factual, não substituída por esta proposta.

## 11. CORRECAO DE DIRECAO DO PRODUCT MASTER — fila efemera por conversa ativa (2026-10-22)

**Status:** PRODUCT_DIRECTION_CONFIRMED / ARCHITECTURE_PROPOSAL_REQUIRES_REWORK. Esta decisao **supera** as propostas de persistencia compartilhada, `conversation_id` autoritativo server-issued, criacao de tabela/Redis, store duravel e quatro rotas de fila descritas anteriormente neste documento e no documento 121, **apenas como direcao para esta fila de UX**. Os textos anteriores permanecem como historico de alternativas descartadas, nao como backlog aprovado. Nao altera Durable Work de C5/C6.

**Decisao expressa:** a mini fila e **temporaria, em memoria, isolada por conversa do usuario enquanto a experiencia conversacional esta ativa**. Nao persistir em tabela, Redis, DB, durable workflow, storage local ou servidor por conveniencia. A apresentacao `ConversationQueue` continua no `plugin-ui`; a propriedade do estado transitorio pertence ao consumer DÉLIA (boundary de experiencia da conversa). Nenhum item da fila passa a ser Task/Work persistente.

**Reuso/abstracao:** inventariar o lifecycle real do `App.tsx`, `sendTurn`, `handleSubmit`, `requestEpochRef`, `requestMode`, host Portal e Dock antes de decidir sobre hook/controller local. `EXISTING_EQUIVALENT=YES_PARTIAL` (envio/estado/componente), `REUSE_DECISION=EXTEND_EXISTING` proposta; nao criar um `interactionManager` generico, segundo planner, engine ou orquestrador. Backend `POST /interaction/turns` permanece owner de cada turno e gates, sem contratos de fila backend neste slice.

**Invariantes de produto:** fila so dentro do contexto de uma conversa ativa, nunca entre conversas; nao herdar pendencias ao iniciar outra conversa; conservar a fila ao trocar a apresentacao full-page/Dock **somente quando a mesma instancia/contexto efetivamente permanece montado**; unmount/reload/perda de memoria podem descartar a fila e isso deve ser comunicado honestamente, sem prometer recuperacao. Remover e reordenar somente pendentes; nao reordenar turno em andamento. `AbortController` e stop local nao equivalem a cancelamento backend.

**Dispatch:** UX de proxima pergunta pode ser sequencial via fluxo `sendTurn` existente, sem loop/scheduler backend. Antes de implementar, estabelecer gates claros para quando iniciar proximo item, evitar duplo envio, preservar contexto transitorio correto, respeitar confirmation/PREPARE/ACT, falhas e stop, e nunca limpar draft da nova pergunta indevidamente. Dispatch automatico exige teste/decisao explicita de UX; nenhuma mensagem enfileirada autoriza side effect ou altera Core/Domain AuthZ.

**Nao implementar:** ADR-1 identity issuer backend; ADR-2 store compartilhado; nova tabela/Redis/migration; endpoints `/conversations/*/queue`; binding `queue_item_ref`; worker/cron/scheduler; persistencia no browser. Se surgir necessidade futura de recuperacao entre reload/abas/dispositivos, tratar como produto/contrato separado, nao expandir esta fila silenciosamente.

**Gates e testes da futura task:** full-page ↔ Dock preservacao quando mesmo contexto; nova conversa/isolation; envio em andamento e varias pendentes FIFO; reordenar/remover; submit unico sem duplicacao; epoch/stale completion; stop; erro/timeouts; confirmacoes governadas; draft recovery e STT; unmount/reload sem promessa de recuperacao; browser a11y mobile/zoom; nenhum POST exceto turnos explicitamente submetidos pela intencao previamente admitida. Registrar evidencias SHA/config reais e manter fase inalterada.

`QUEUE_BACKEND_CONTRACT=NOT_REQUIRED_FOR_EPHEMERAL_UX`; `PERSISTENCE=OUT_OF_SCOPE`; `ARCHITECTURE_DRIFT_IDENTIFIED=YES (superseded persisted-contract proposal)`; `IMPLEMENTATION=NOT_STARTED`; `TESTS=TEST_NOT_RUN`; `PHASE_PROGRESSION=NONE`.
