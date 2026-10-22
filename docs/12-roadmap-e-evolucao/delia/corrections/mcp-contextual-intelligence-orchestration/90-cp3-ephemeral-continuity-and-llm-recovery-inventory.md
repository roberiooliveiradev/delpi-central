# 90 — CP3: Inventário de continuidade efêmera e decisão de recuperação de LLM

**Data:** 2026-10-22
**Task:** `DELIA-C3-EPHEMERAL-CONTINUITY-AND-LLM-RECOVERY-INVENTORY-01`
**Tipo:** inventário dirigido + reuse gate + decisão arquitetural (CP3 do documento 88)
**Escopo:** investigação e decisão — **nenhum comportamento de runtime alterado**. O único artefato executável novo é a suíte de caracterização `tests/test_c3_ephemeral_continuity_characterization.py` (ETAPA H), que observa o código vigente sem modificá-lo.

## 1. Decisão de produto assumida

O usuário pergunta uma única vez; a DÉLIA deve tentar concluir a interação reutilizando as etapas válidas. Nesta fase:

```text
PERSISTENT_CONVERSATIONS=OUT_OF_SCOPE
PERSISTENT_CHECKPOINTS=OUT_OF_SCOPE
EPHEMERAL_RECOVERY=TARGET
PAGE_REFRESH_SURVIVAL=NOT_REQUIRED
API_RESTART_SURVIVAL=NOT_REQUIRED
USER_MANUAL_REASK=NOT_DESIRED
```

Perda aceita: refresh, fechamento de aba, disconnect definitivo, restart da API. Isso não autoriza ignorar disconnect, cancelar incorretamente nem ultrapassar deadlines de infraestrutura.

## 2. Inventário do fluxo (ETAPA A)

### 2.1 Cadeia real

```text
USER → plugins/delia (DeliaConversationPage → submitInteractionTurn)
  → POST /apps/delia-api/interaction/turns
     Accept: application/x-ndjson, application/json
  → nginx gateway (prod: proxy_read_timeout 86400; dev: sem override → default 60s)
  → app/interfaces/http/interaction_routes.py
     _wants_ndjson() → _stream_interaction_turn()
       worker thread: handler.execute(command, activity_channel=publish)
       request thread: drains in-memory queue.Queue(maxsize=66) → NDJSON
  → HandleInteractiveConversationTurn.execute()
       TurnDeadline.start(settings.turn_budget_seconds=30)
       InteractionSession/InteractionTurn (request-scoped, value objects)
       sink = activity_sink_or_none(...)  → ActivityEvent.v1
  → OperationalCapabilityOrchestrator.attempt(turn_deadline, activity_sink)
       _ACTIVITY_SINK ContextVar bound per call
       _attempt() — linear stage chain, results kept as LOCALS
  → stage model calls: _model_stage_proposal → InvokeModel → adapter
       (single-shot; ModelInvocationError code=timeout → _StageDeadlineExceeded)
  → MCP: SpecialistInterop → port (list_remote_tools / call_remote_tool)
  → GovernedCapabilityAttempt → InteractiveTurnResult
  → terminal turn_result/turn_error → MFE parser → badges/presentation
```

### 2.2 Matriz de estágios do caminho operacional

| Estágio | Tipo | Resultado | Reaproveitável em resume? | Timeout próprio | Comportamento em deadline |
|---|---|---|---|---|---|
| `interaction_admission` | model `_propose` | proposal admission | sim (rerun barato) | cap 6s | **catch** → segue p/ seleção (`decision=budget_exhausted`) |
| `groups` (`_groups`) | MCP `list_remote_tools` | `groups`,`surface` | re-listar no resume (verdade viva) | deadline-clamped | `TurnBudgetExhausted` → terminal |
| `goal_understanding` | model `_propose` | `_TurnGoal` tipado | sim | stage cap | propaga → `PROCESSING_TIMEOUT` |
| `prior_continuation` | model síntese | attempt | sim | stage cap | catch → `PROCESSING_TIMEOUT` determinístico |
| `target_selection` (group+capability) | model `_propose` ×2 | `group_key`,`descriptor` | **sim — principal reuso** | stage cap | propaga → `PROCESSING_TIMEOUT` |
| `native_assessment` | model `_propose` | status | sim | stage cap | propaga → `PROCESSING_TIMEOUT` |
| `discovery`/`preflight` | MCP invoke | evidence | refetch se necessário | deadline-clamped | propaga |
| `index_probe`/`index_select` | model `_propose` | index ids | sim | stage cap | propaga (probe) / **catch** → no_match→clarify (select) |
| `arguments` | model `_propose` | `arguments`,`missing_inputs` | **sim — principal reuso** | stage cap | `model_timeout` propaga; `turn_budget_exhausted` → projeção/clarify |
| `resolver` (missing inputs) | model+MCP | resolved args | sim | budget-gated | budget-gated (`skipped_budget`) |
| `candidate_*` | model `_propose` | candidate args | sim | stage cap | propaga |
| `execute` (`_invoke_selected`) | MCP `call_remote_tool` | `outcome` | **nunca re-emitir PREPARE/ACT**; READ pode re-invocar | deadline-clamped | propaga |
| `grounded_synthesis` | model `_propose` | content | sim | stage cap | **catch** → render determinístico (SUCCESS preservado) |
| `clarification` wording | model `_propose` | question | sim | stage cap | **catch** → ask-back determinístico |
| CRI composition | determinístico | presentation | sim | — | n/a |

**Resposta à pergunta obrigatória:** se `arguments` sofre timeout após `group_selection` e `capability_selection` concluídos, **é possível repetir somente `arguments`**: no ponto do raise (`_build_arguments` → `_propose`), `descriptor`, `input_text`, `workspace_context`, `owner_evidence`, `foreign_evidence`, `goal` e `deadline` estão todos em escopo como locais de `_attempt`. O impedimento atual não é ausência de dados — é que a exceção desenrola o frame e os locais morrem sem exportação; nenhum resultado parcial chega a `GovernedCapabilityAttempt` (verificado: `PROCESSING_TIMEOUT` carrega apenas `status`/`correlation_id`/`error_code`).

## 3. Estado em memória (ETAPA B)

### 3.1 Onde os dados vivem hoje

| Dado | Local | Lifetime |
|---|---|---|
| correlation_id | local `attempt()`/logs/events | request |
| input_text, workspace_context, prior_turns | params de `_attempt` | request |
| groups/surface (surface live) | locais `_attempt` | até o raise |
| goal tipado (`_TurnGoal`) | local `_attempt` | até o raise |
| descriptor/capability selecionada | local `_attempt` | até o raise |
| owner/foreign evidence | locais `_attempt` | até o raise |
| arguments/missing_inputs | locais `_attempt` | até o raise |
| outcome MCP verificado | local `_attempt` → `attempt.outcome` só em SUCCESS | até o raise |
| session_id/turn_id | `InteractionSession`/`InteractionTurn` | request (não durável) |
| activity events | `_ACTIVITY_SINK` → queue in-memory → NDJSON | request/stream |
| bearer | `subject_bearer` ContextVar (worker) | worker |

### 3.2 Perguntas obrigatórias respondidas

- **O que se perde quando o timeout sobe até `attempt()`?** Tudo o que era local de `_attempt`: group/capability/arguments/outcome. O `GovernedCapabilityAttempt` terminal não exporta nada além de `status`/`correlation_id`/`error_code` (caracterizado em ETAPA H).
- **O que poderia ser preservado sem nova infraestrutura?** Um objeto tipado de estado (`TurnExecutionState`) preenchido incrementalmente em `_attempt` — ids/refs de fronteira, nunca CoT/prompts/credenciais. É estado interno novo (não infraestrutura, não persistência, não contrato de fio).
- **O que pode ser reutilizado com segurança?** Decisões tipadas já validadas deterministicamente: `group_key`, identidade da capability (`remote_name` + schema ref), `arguments`/`missing_inputs`, refs de evidence. Re-listar a surface no resume é barato e preserva verdade viva; re-validação de existência da capability e AuthZ acontecem naturalmente no re-enter (mesmo bearer via ContextVar do worker).
- **O que exige nova validação?** `arguments` só pode ser reusado se a capability ainda existir na surface re-listada e o schema não tiver mudado — revalidar contra o descriptor re-obtido, não contra o checkpoint.
- **Risco de duplicar invocações MCP?** READ re-invoke é seguro (efeito colateral nulo; pior caso = leitura repetida). PREPARE/ACT **nunca** pode ser re-executado — gate de fronteira obrigatório: resume permitido apenas enquanto a fronteira alcançada for anterior ao invoke, ou quando `operation_class` for READ e a política decidir re-invocar; se o invoke já retornou, o resume deve pular direto para síntese/render com o `outcome` preservado.
- **Como impedir entrega dupla?** O worker escreve exatamente um terminal (`turn_result`/`turn_error`) após a última tentativa — o contrato da fila já garante single-terminal; o risco só existe se a resposta fosse entregue por tentativa (não será).
- **Lifetime correto do estado efêmero?** Enquanto o worker da stream estiver vivo (início de `handler.execute` até o terminal). Morre com o request — exatamente o escopo aceito pela decisão de produto.
- **Não persistir:** chain-of-thought, credenciais, tokens, prompts sensíveis, autorizações presumidas, metadata externa como verdade — checkpoint carrega ids/refs/argumentos tipados apenas.

## 4. Orçamento e transporte (ETAPA C)

### 4.1 Fatos medidos

- `DEFAULT_TURN_BUDGET_SECONDS = 30.0` (`turn_budget.py`) — janela síncrona **por tentativa**, monotônica, compartilhada por todos os estágios; `stage_timeout = min(configurado, remaining)` — reduz, nunca amplia.
- `MIN_VIABLE_MODEL_STAGE_SECONDS = 2.0`; `MAX_TIMEOUT_SECONDS = 30.0` por invocação (`invoke_model.py` — teto duro).
- `DELIA_MODEL_STAGE_TIMEOUT_SECONDS=30` em dev/prod → um estágio pode consumir `min(30, remaining)` — caso P1 do relatório 87: um `select_capability` de 21.3s faminto matou o turno.
- Nginx prod `/apps/delia-api/`: `proxy_read_timeout 86400` — o gateway **não** impõe teto curto. Nginx dev: sem `proxy_read_timeout` no bloco → **default 60s** (assimetria dev/prod relevante para orçamento total >60s).
- Edge real: Cloudflare ~100s (524 observado — docstring de `turn_budget.py`). O teto prático total de uma interação é ~100s; 30s mantém margem grande.
- NDJSON: worker thread executa `handler.execute`; disconnect → `GeneratorExit` → "the worker finishes bounded by the turn deadline — never re-executed" (interaction_routes.py:386-389). A vida técnica da interação = vida do worker.
- Frontend: `AbortSignal` suportado por `submitInteractionTurn` mas **nenhum AbortController/cancel UI** existe na página; sem reconnect de stream; estado de conversa = memória transitória do componente (`buildInteractionContext` → `prior_turns`).

### 4.2 Resposta à pergunta central

**A DÉLIA consegue iniciar uma nova tentativa técnica após 30s sem encerrar a interação lógica na interface?** Sim — mecanicamente: o worker da stream continua vivo enquanto `handler.execute` rodar, a fila entrega eventos de qualquer tentativa ao mesmo stream e o terminal único só é escrito ao final. O transporte suporta (prod 86400s; Cloudflare ~100s é o teto real — margem suficiente para um total de interação ~60-75s). O que falta é uma decisão explícita de orçamento: uma segunda tentativa significa um segundo `TurnDeadline.start(30)` — a janela síncrona por tentativa não é esticada, mas o **trabalho total por interação** passa a exceder 30s. Isso é a decisão arquitetural desta fase — distinta do bypass proibido no CP2 (reiniciar o deadline silenciosamente para contornar o limite dentro da mesma tentativa): aqui é uma extensão delimitada, contada e observável.

## 5. Recuperação existente (ETAPA D)

| Mecanismo | Estado |
|---|---|
| Retry de Model Invocation | **não existe** — adapter é single-shot; `_model_stage_proposal` única chamada |
| Retry de HTTP (adapter/model) | não existe |
| Recovery de MCP (`_repair_once`) | existe — 1 round, READ-only por construção, re-lista surface + re-seleciona + re-invoca; `MAX_REPLAN_ROUNDS=1` |
| Recovery de argumentos (`_recover_owner_contract`) | existe — 1 round, READ-only, re-projeta via DISCOVERY do próprio owner |
| Retry de seleção | não existe (stage propaga) |
| Deadline propagation | existe — `TurnDeadline` compartilhado; `remaining_budget()` para fan-out |
| Cancellation | parcial — disconnect mata a entrega; worker termina bounded; sem cancel token explícito |
| Idempotência/dedupe | **não existe** — `call_remote_tool` não carrega chave (caracterizado) |
| Circuit breaker/backoff/rate limiting | não existe no caminho model/MCP |

**Precedente arquitetural chave:** `_repair_once`/`_recover_owner_contract` já implementam "recuperação limitada, deadline-gated, nunca PREPARE/ACT" — o retry de timeout deve seguir exatamente esse padrão.

## 6. Frontend (ETAPA E)

- Cliente: `submitInteractionTurn` — POST único, `Accept: application/x-ndjson, application/json`; `readNdjsonTurnStream` entrega `activity_event` via `onActivityEvent` e um terminal `turn_result`/`turn_error`.
- Vocabulários fechados: `ACTIVITY_PHASES` (12), `ACTIVITY_STATES` (9), `ACTIVITY_OUTCOME_STATUSES` (4) — extensão aditiva possível; kind desconhecido degrada neutro (nunca inventa).
- Estados conceituais pedidos mapeiam: PROCESSING→`CONTEXTUALIZING`/`REQUEST_RECEIVED`(running); uma continuação honesta pode reutilizar `CONTEXTUALIZING` (ou fase aditiva nova, decisão do contrato); COMPLETED/FAILED/CANCELLED→fases terminais existentes; `PROCESSING_TIMEOUT`→badge "Processamento interrompido" já renderizado.
- **Nenhuma mudança de frontend é necessária para a Opção B** — o mesmo stream entrega o resultado final quando a cadeia conclui; o frontend nunca inventa execução ativa (só renderiza eventos recebidos).

## 7. Reuse gate (ETAPA F)

| RESPONSIBILITY | OWNER | EXISTING_EQUIVALENT | REUSE_DECISION |
|---|---|---|---|
| tentativa governada + deadline | `OperationalCapabilityOrchestrator.attempt` | YES | EXTEND (loop bounded + resume-state) |
| orçamento por turno | `TurnDeadline`/`turn_budget.py` | YES | REUSE (por tentativa, inalterado) |
| orçamento total por interação | — | NO | NEW (constante governada — decisão §8) |
| checkpoint efêmero | — | NO | NEW (tipo interno `TurnExecutionState`, request-scoped) |
| sinal honesto de continuação | ActivityEvent.v1 | YES | REUSE/EXTEND (vocabulário aditivo) |
| entrega única de resultado | queue NDJSON + terminal único | YES | REUSE |
| cancelamento por disconnect | `GeneratorExit` → worker bounded | YES | REUSE |
| autorização | bearer ContextVar + AuthZ existente | YES | REUSE (re-validação natural no re-enter) |
| retry de estágio model | `_model_stage_proposal` | parcial | EXTEND (política bounded, ver §8.4) |
| dedupe/idempotência MCP | — | NO (gap real) | não requerido para READ; PREPARE/ACT protegido por fronteira |
| Automation Hub / worker | — | NO | fora de escopo por decisão de produto |

## 8. Opções (ETAPA G)

### 8.1 Comparação

| Critério | A — retry in-request | B — continuação efêmera no stream | C — nova request técnica |
|---|---|---|---|
| Reutilização existente | `_model_stage_proposal` | `attempt()` boundary + sink + queue | handler + novo contrato |
| Preserva etapas válidas | sim (locais em escopo) | sim (checkpoint tipado) | sim (store efêmero) |
| Ultrapassa 30s total | **não** (mesmo deadline) | sim, com teto explícito | sim |
| Corrige caso observado (estágio 21s esgota 30s) | **não** — sem janela restante | **sim** | sim |
| Persistência | nenhuma | nenhuma | store in-memory novo |
| Novo contrato de fio | não | não | sim (resume token/command) |
| Complexidade | baixa | média | alta |
| Risco de duplicação | nenhum (mesmo estágio) | baixo (fronteira READ-only) | médio (dedupe por token, double-delivery) |
| Cancelamento | herdado | herdado (disconnect → GeneratorExit) | precisa política própria |
| Frontend | zero | zero obrigatório | auto-resume + token handling |
| Observabilidade | stage timing existe | + tentativa/atividade | + lifecycle de store |

### 8.2 Veredito

- **A sozinha é insuficiente:** só atua quando resta `≥ MIN_VIABLE` após o estágio falhar — o caso dominante observado (um estágio consome os 30s) não deixa janela. Útil como micro-otimização opcional, não resolve o produto.
- **C é o mesmo resultado com mais superfície:** store efêmero com TTL+single-flight, token opaco, dedupe/double-delivery, segunda ida HTTP, lógica de auto-resume no MFE — para entregar o que B entrega com zero contrato novo. Rejeitada nesta fase; documentada como fallback se o vínculo por stream provar insuficiente (ex.: necessidade futura de sobreviver a queda da request HTTP — fora do escopo aceito).
- **B é a solução mínima completa:** re-tentativa governada dentro do worker da stream, estado efêmero tipado em memória, terminal único, cancelamento natural, AuthZ preservada, zero mudança de contrato de fio ou de frontend.

### 8.3 Recomendação — Opção B ("governed re-attempt with ephemeral checkpoint")

**Pré-condição de autoridade (decisão explícita exigida):** o limite de 30s por tentativa permanece; a **soma** das tentativas de uma interação passa a ser orçada por constantes novas e explícitas. Sem essa decisão de produto assinada, CP4 não inicia.

### 8.4 Contrato preliminar da próxima implementação (sem implementar)

```text
RESPONSIBILITY=recuperação efêmera de timeout de estágio LLM
OWNER=app/application/capability_provision/orchestration.py
      (OperationalCapabilityOrchestrator.attempt — boundary canônico)
TRIGGER=_StageDeadlineExceeded | TurnBudgetExhausted em tentativa
        READ-class, antes ou depois do invoke conforme fronteira
CHECKPOINT=_TurnExecutionState (interno, não-exportado no contrato):
  frontier: admission_done|surface|selected|arguments|invoked
  group_key, remote_name, descriptor_identity (schema fingerprint),
  arguments, missing_inputs, owner/foreign evidence refs, outcome
  — nunca CoT, prompts, credenciais, bearer
ATTEMPTS=DELIA_MAX_GOVERNED_ATTEMPTS (default 1 → 2 quando ligado;
        hard cap 2 nesta fase)
TOTAL_BUDGET=DELIA_INTERACTION_TOTAL_BUDGET_SECONDS (guard monotônico;
        proposta ~75s ≤ margem Cloudflare ~100s; dev nginx precisa de
        proxy_read_timeout ≥ total — config acompanhante)
PER_ATTEMPT=TurnDeadline.start(turn_budget_seconds=30) — inalterado
RESUME_RULES=
  - re-enter _attempt(resume=state): pula estágios concluídos válidos
  - re-lista surface se necessária; revalida descriptor contra surface viva
  - re-executa somente a fronteira falha + downstream
  - invoke já concluído → resume direto na síntese/render com outcome
  - PREPARE/ACT: nunca resume através do invoke — frontier gate fail-closed
  - confirmation/pending-write path fora do retry
COST=max 2× model stages + 1× invoke (READ); sem backoff nesta fase
     (mesmo worker, imediato — jitter desnecessário para 1 retry)
PROGRESS=evento honesto no mesmo sink (fase aditiva ex.: CONTINUING
        ou reuse CONTEXTUALIZING — decisão de contrato na implementação;
        nunca "continuo processando" como texto sem trabalho ativo)
TERMINAL=turn_result único ao final da última tentativa; falha final =
        PROCESSING_TIMEOUT existente (mensagem já honesta)
IDEMPOTENCY=READ re-invoke aceitável (bounded, ≤1 extra); nenhuma chave
        de dedupe no fio — gap registrado; PREPARE/ACT protegido por
        fronteira, não por idempotência
CANCELLATION=disconnect → GeneratorExit → worker termina bounded;
        resultado descartado honestamente (aceito pela fase)
OBSERVABILITY=stage timing por purpose (existente) + attempt_index +
        resumed_from em logs; fase/estado em ActivityEvent
ACCEPTANCE=
  - arguments timeout após seleção → retomada só no estágio falho,
    seleção não repetida, resposta na mesma interação
  - timeout após invoke (não-síntese) → não re-invocar READ
    desnecessariamente; PREPARE/ACT nunca re-executado
  - timeout final → PROCESSING_TIMEOUT honesto (já existe)
  - budget total guard respeitado; attempt cap respeitado
  - OFF/legado (MAX_ATTEMPTS=1) byte-idêntico ao comportamento atual
SECURITY=mesmo bearer/AuthZ; nenhuma autorização presumida do checkpoint;
        revalidação natural no re-enter; fail-closed preservado
```

## 9. Caracterização (ETAPA H)

`tests/test_c3_ephemeral_continuity_characterization.py` — 7 testes, PASS:

```text
arguments timeout pós-seleção   → PROCESSING_TIMEOUT; admission+group+
                                   capability+arguments executados;
                                   outcome/provenance/owner_hint = None
                                   (trabalho concluído morre no frame)
synthesis timeout pós-invoke    → SUCCESS (fallback determinístico
                                   existente — recovery JÁ existe)
admission timeout               → degrada p/ seleção (recovery existente)
provider error não-timeout      → NOT_APPLICABLE (degradação suave,
                                   nunca falso timeout)
janela de retry in-budget       → stage_timeout ≥ MIN_VIABLE após falha
                                   aos 21s/30s (seam existe)
budget esgotado                 → stage_timeout = 0 (stop honesto)
invoke sem idempotency key      → confirmado (gap documentado)
TEST_NOT_RUN=disconnect-during-retry, double-terminal delivery,
             cancellation-mid-resume (exigem transporte real/mecanismo
             que ainda não existe; contrato do worker documentado)
```

Regressão da suíte canônica de budget: mantida verde (sem alteração de comportamento).

## 10. Veredito

`ARCHITECTURE_DECISION=OPTION_B_APPROVED_FOR_IMPLEMENTATION_PENDING_BUDGET_SIGNOFF` — o mecanismo é viável com o código vigente; a única autoridade pendente é o par de constantes de orçamento total por interação (`DELIA_MAX_GOVERNED_ATTEMPTS`, `DELIA_INTERACTION_TOTAL_BUDGET_SECONDS`) e o acompanhante dev-nginx `proxy_read_timeout` se o total exceder 60s.

`NEXT_IMPLEMENTATION_TASK=DELIA-C3-GOVERNED-STAGE-RESUME-01 (CP4)` — implementar `_TurnExecutionState` + resume-aware `_attempt` + boundary loop bounded + frontier gate + sinal de atividade + config; RED→GREEN→real-eval conforme contrato §8.4.

`RUNTIME_CODE_CHANGED=NO` `CHECKPOINT_IMPLEMENTED=NO` `RESUME_IMPLEMENTED=NO` `PRODUCTION_ACTIVATION=NO` `I04_ACCEPTED=NO` `C3_EXECUTED=YES`


## 11. Revisão independente de coordenação — 2026-10-22

**Veredito: ACCEPT_WITH_RESIDUAL (CP3 inventário), Opção B = preferred candidate, NOT unconditional implementation approval.** Inspecionados o documento 90, o índice da trilha e o SHA de `main` no início da revisão (`b80956483aae95892670c1af2462411d7061faff`). Os 7 testes de caracterização e medições de infraestrutura permanecem **executor-reported**; `INDEPENDENT_RUNTIME_REEXECUTION=TEST_NOT_RUN`.

**Direção aprovada pelo produto:** continuidade efêmera por interação aberta, sem persistência de conversa/atividade, sem sobreviver a refresh, fechamento de aba, perda de conexão ou restart. Reaproveitar resultados tipados válidos dentro do mesmo fluxo; sem novo banco, worker persistente, engine, scheduler, token de resume ou nova request. O objetivo da próxima implementação é recuperar um timeout pontual sem solicitar novamente a pergunta.

**Evidência favorável:** variáveis locais de `_attempt` conservam as seleções e evidências enquanto o frame existe; o propagador de timeout perde esses resultados; stream/worker/queue/sink já fornecem envelope técnico efêmero e terminal único. Assim, usar um checkpoint interno tipado restrito à execução atual é extensão plausível. `EXISTING_EQUIVALENT=YES` para streaming e deadline; `NO` no caminho inspecionado para checkpoint de estágio; `REUSE_DECISION=EXTEND` do owner legítimo, condicionado aos gates abaixo. Ausência global/ecossistêmica não pode ser inferida de uma pesquisa residual.

**Gate G1 — orçamento e transporte:** uma ou duas tentativas de até 30s não autorizam reiniciar a mesma janela silenciosamente nem garantir 75s de trabalho útil. Definir separadamente `MAX_ATTEMPTS`, `INTERACTION_TOTAL_BUDGET`, reserva de transporte/entrega e os tempos efetivos em dev, prod e edge. O valor **75s é candidato, não autoridade aprovada**. Com Nginx dev sem configuração explícita, 75s podem ultrapassar seu default reportado de 60s; com Cloudflare, edge e ociosidade do stream têm limites independentes. Validar streaming real e margem de timeout antes de ativar recuperação que exceda 30s. A configuração deve preservar compatibilidade de MAX_ATTEMPTS=1 e rollout controlado.

**Gate G2 — cancelamento real:** `GeneratorExit` encerrar a entrega não prova que a thread worker seja cancelada. O próprio inventário relata worker concluindo bounded mesmo após desconexão. Não registrar `CANCELLATION=PASS` por herança. Como desconexão é perda aceita nesta fase, o mínimo é evitar retries adicionais após disconnect, garantir liberação bounded e não prometer continuidade ao usuário. Testar disconnect durante timeout/retry, terminal duplicado e atraso de emissão.

**Gate G3 — autorização/efeitos:** ContextVar com bearer preservado não é **live Core AuthZ revalidated**. É preciso localizar o enforcement real para retomada e garantir nova validação de permissão/regras para qualquer nova chamada ao owner. A fronteira READ não pode ser inferida só de nome/metadata MCP; usar capability operation class e contratos governados. PREPARE/ACT e intents de escrita, confirmação pendente, postcondition indeterminada nunca recebem re-invocação automática. Até uma leitura pode depender de efeitos externos não provados; somente repetir invocações comprovadamente READ e seguras.

**Gate G4 — integridade de checkpoint:** guardar apenas estado tipado, versão/fingerprint de schema e refs sanitizadas; revalidar surface, arguments e evidence TTL ao retomar; separar estágio que falhou de resultados anteriores. No fluxo de duas tentativas, provar que `arguments` falhando não chama novamente group/capability selection validamente concluídas. Se houver resposta atrasada da primeira tentativa, ignorar resultado tardio e garantir terminal único. Observar custo, correlation, attempt_index e resultado factual.

**Decisão para CP4:** Autorizar apenas a **elaboração de contrato e implementação gated** após G1–G4 comprovados no HEAD; priorizar primeiro uma feature OFF/default compatível, testes RED determinísticos e rollout dev controlado. Não declarar `OPTION_B_IMPLEMENTED` nem `PRODUCTION_RESUME_ON` antes da avaliação. Se qualquer gate não puder ser cumprido sem infraestrutura adicional ou violar autoridade canônica, STOP → ARCHITECTURE_DECISION_REQUIRED, sem redesenho silencioso.

`CP3=ACCEPT_WITH_RESIDUAL`; `OPTION_B=SELECTED_AS_DESIGN_DIRECTION`; `BUDGET_SIGNOFF=PENDING`; `CANCELLATION_PROOF=PENDING`; `LIVE_AUTHZ_REVALIDATION_PROOF=PENDING`; `CP4_IMPLEMENTED=NO`; `I04_ACCEPTED=NO`.
