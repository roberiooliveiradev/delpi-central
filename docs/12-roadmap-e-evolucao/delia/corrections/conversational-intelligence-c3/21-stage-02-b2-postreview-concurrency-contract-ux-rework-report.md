# 21 — Relatório de correção bounded B2 (RW-01 / RW-02 / UX-01)

**TASK:** `DELIA-C3-STAGE-02-B2-POST-REVIEW-BOUNDED-REWORK-01`  
**DATA:** 2026-10-16  
**EXECUTION MODE:** GitHub connector, direct updates to `main`; not a local git checkout.  
**REVIEW INPUT:** [20 — independent implementation review](./20-stage-02-b2-independent-implementation-review.md), ledger §6.186, reviewed SHA `397cb5c34415abaf72761c8d09d8654336def9a7`.  
**REMOTE HEAD CONSULTED FOR THIS REPORT:** `03ed68b3b478b44315c98c240110735a38836b13`.  
**STATUS:** `IMPLEMENTATION_EVIDENCE_RECORDED`, `INDEPENDENT_REVIEW=PENDING`, `STAGE_02_ACCEPTED=NO`, `STAGE_03_AUTHORIZED=NO`.

## 1. Autoridade, ownership e reuso

Reancoragem no HEAD remoto: Project Instructions/.cursor → docs 16→50→17→49→51→52→21→20→25→02→24→temáticas 60/69/70/personality→ledger §§6.126/130/133/140/141/145/183–186. Doc18/§6.184 encerra o contrato D1/D2/D3: MESSAGE nunca ACT material, somente APPLY_PREPARED tipado e operation-bound pode progredir; REJECT cancela. Este rework não altera essas decisões.

`EXISTING_EQUIVALENT=YES` para `PendingWriteStore`, `bind_confirmation`, `InteractiveTurnRequest`, `HandleInteractiveConversationTurn`, HTTP route mapper, `GovernedConfirmation` UI e harness existentes. `REUSE_DECISION=EXTEND` nos três seams; `NEW` planner/engine/registry/provider rule = NO. Keycloak/Core/Domain/Policy/Decision/owner confirmation intactos.

## 2. RW-01 — claim de PendingWrite exclusivo

**Original (§6.186):** dois APPLY podem realizar `get` sobre o mesmo digest antes de um deles removê-lo; retorno de `take` era descartado, e ambos podiam avançar para `_execute_prepared_act`.

**Alterações publicadas:** `PendingWriteStore` utiliza `RLock` em `put/get/take`; `take_if_current(digest, expected)` realiza comparação de **identidade do record validado**, checagem de expiração e remoção em uma região crítica única. `_confirm_proposal` só prossegue ao ACT quando recebeu exatamente o record que venceu o claim; `None` retorna `WRITE_REJECTED/confirmation_unknown`. O lock não cobre chamadas de owner/network. Um digest substituído por proposta distinta não é consumido por decisão stale.

**Limite:** garantia atômica dentro da instância Python que contém o store. O repositório declara PendingWriteStore como estado temporário *process-local*: isso **não prova exactly-once distribuído** ou resiliência entre processos/restarts. Outros workers sem o pending original devem falhar fechados; qualquer necessidade de persistência compartilhada/CAS multi-instância exige inventário de implantação e decisão arquitetural separada, sem novo store por conveniência. Domain/owner idempotency e authoritative Outcome permanecem obrigatórios.

**Testes adicionados (NÃO EXECUTADOS neste ambiente):** `test_stage02_b2_concurrent_decisions.py` força os dois callers a lerem a mesma proposta usando `Barrier(2)`, executa APPLY×APPLY e APPLY×REJECT nos dois ordenamentos, verifica máximo um owner ACT, único vencedor, retry fail-closed; caso separado de digest substituído.

## 3. RW-02 — contrato de comando atravessa HTTP e Application

**Original (§6.186):** `command.type` validado em HTTP mas descartado ao criar `InteractiveTurnRequest`; consumers internos podiam enviar `confirmation` sem comando tipado.

**Alterações:** vocabulário compartilhado em `interaction/contracts.py`: `MESSAGE`, `APPLY_PREPARED`, `REJECT_PREPARED`; campo `InteractiveTurnRequest.command_type` (default seguro `MESSAGE`). `interaction_routes.py` usa os mesmos valores e transporta `command_type` ao Application. `HandleInteractiveConversationTurn._validate_turn_command` bloqueia combinations indevidas em todos os callers (MESSAGE+decision, APPLY+texto, decision incompatível, teto prepare+APPLY, valor desconhecido), antes de invocar orquestração/modelo. Exceção legada: o HTTP converte a label PT **exata** publicada em um comando tipado; o Application aceita apenas essa label exata **junto do comando tipado normalizado**. Um caller direto com `command_type=MESSAGE` + confirmation é sempre rejeitado, mesmo com label legada; decisão tipada sem orquestrador também falha fechada.

**Testes adicionados (NÃO EXECUTADOS neste ambiente):** `test_interaction_runtime.py` inclui assertions da propagação HTTP→Application e parametriza requests inválidos construídos diretamente (não dependem do HTTP), teto e legado.

## 4. UX-01 — verdade visual dos pendings

**Original (§6.186):** qualquer `sendTurn` bem-sucedido definia `confirmationAnswered=true` para todos os cards, mesmo após MESSAGE não relacionado.

**Alterações:** `plugins/delia/src/App.tsx` marca como respondida **somente** a proposta cujos `proposal_digest`, `preview_fingerprint` e `session_id` correspondam à decisão APPLY/REJECT enviada. MESSAGE comum não fecha pending. Demo também fecha apenas a decisão alvo.

**Testes adicionados (NÃO EXECUTADOS neste ambiente):** `plugins/delia/src/interaction.test.tsx` valida PREPARE→MESSAGE não relacionado→cartão visível e dois pendings→APPLY alvo→outro cartão permanece.

## 5. Evidência e testes

| Item | Estado factual nesta sessão |
| --- | --- |
| GitHub write/commit na `main` | PROVEN (connector commits, remote HEAD verificável) |
| Correção estática de claim e checks em `orchestration.py` | PROVEN por inspeção do código remoto; eficácia concorrente runtime PENDING |
| Testes RED controlados | `TEST_NOT_RUN` na sessão (assertivas da antiga falha registradas no review §6.186; novos testes escritos, sem execução) |
| Backend pytest completo | `TEST_NOT_RUN` nesta sessão; 1121/1121 refere-se ao commit ANTERIOR do executor, não pode ser reciclado |
| Frontend vitest / tsc / build/federation | `TEST_NOT_RUN` nesta sessão; resíduo `tsc` anterior TO_INVENTORY |
| Browser QA / real-model / live business Outcome | `TEST_NOT_RUN` |
| GitHub Actions Architecture Enforcement | CI disponível e disparado por commits; registrar separadamente status por SHA; não é substituto das suítes B2 |
| Git local status | `TO_INVENTORY` — ferramenta GitHub remota não observa dirty local de Cursor/Devin |

**Comandos exigidos no checkout no SHA revisado antes do aceite:** executar testes direcionados `pytest -q tests/test_stage02_b2_concurrent_decisions.py tests/test_interaction_runtime.py tests/test_stage02r2_execution_bound_diagnosis.py` a partir de `delia-api`; depois suíte `pytest` completa; em `plugins/delia`, `vitest` conforme package scripts, `tsc -p tsconfig.app.json` e build; testar browser com duas propostas pendentes; verificar concorrência real de workers se topologia de produção exigir. Registrar exit codes/versões e evidência.

## 6. Commits funcionais e de teste (sem alterações concorrentes incluídas)

- `95b544e9e9` — lock + claim atômico no PendingWriteStore
- `10b1380f7b` — orchestrator exige claim vencedor
- `8d1989056a`, `cdd53a00eb`, `3094568b4c`, `6abbe3c077`, `62095e4d46` — typed command no Application, legacy-normalized allowlist, MESSAGE+confirmation always rejected
- `95562516fb` — UI marca somente proposta alvo, MESSAGE preserva cards
- `942c56cb36`, `3213dcb181`, `377d307840`, `df90c051e7`, `47b7758e05`, `d54ddc0549` — testes de concorrência, Application/legado e UI

O GitHub recebeu commits diretos na branch `main`; commits concorrentes de outras frentes apareceram entre mudanças B2, mas **não foram editados** por esta tarefa. No commit final de relatório deve ser revalidado remote HEAD; não declarar push local/working tree limpo.

## 7. Gates e handoff

**B2_REWORK_IMPLEMENTED=YES (static code/evidence)**; **B2_SECURITY_VERIFIED=NO (tests pending)**; `INDEPENDENT_REVIEW=PENDING`. Não marcar PASS ou avançar fase sem execução e revisão independente. Aceite deve demonstrar single winner real sob simultaneidade, ausência de bypass para consumers diretos e UX correta após mensagens não relacionadas; continuar sem ACT empresarial real.

`STAGE_02_ACCEPTED=NO`; `STAGE_03_AUTHORIZED=NO`; `C3_EXECUTED=NO`; `C4_AUTHORIZED=NO`; `C5_AUTHORIZED=NO`; `NEXT=RETURN_TO_ARCHITECTURE_COORDINATION`.
