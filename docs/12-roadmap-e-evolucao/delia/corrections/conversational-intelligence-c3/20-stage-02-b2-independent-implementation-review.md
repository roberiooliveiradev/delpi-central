# 20 — Revisão independente da implementação B2 (§6.184)

**TASK:** DELIA-C3-STAGE-02-B2-EXECUTION-SCOPE-FULL-IMPLEMENTATION-01-INDEPENDENT-REVIEW  
**DATA:** 2026-10-16  
**REVIEWED_SHA:** `397cb5c34415abaf72761c8d09d8654336def9a7`  
**REMOTE_HEAD_AT_REVIEW:** `c41bfc2743ec5232dd91a727cbf8719ba3a08130`; commit posterior fora da fatia B2. Local git status `TO_INVENTORY`.  
**MODE:** leitura de commit, diff, código, testes scripted e docs canônicas. Revisor **não** executou pytest, vitest, tsc, browser, modelos ou ações reais.  
**VERDICT:** **`REWORK`** — implementação B2 ainda sem aceite; Stage02 `NOT_ACCEPTED`; Stage03 `NOT_AUTHORIZED`.

## Autoridades e gate de reuso

Project Instructions/.cursor → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → 02 → 24 → 60/69/70/personality → ledger §§6.126/6.130/6.133/6.140/6.141/6.145/6.171–6.185. Produto aprovado doc17/§6.183, contrato fechado doc18/§6.184, relatório do executor doc19/§6.185 **não constitui aceite**. Keycloak/Core/Domain/Policy/Decision e owner confirmation §6.140 preservados.

`EXISTING_EQUIVALENT=YES`: PendingWriteStore, bind_confirmation, Application/HTTP command contract, _execute_prepared_act, frontend confirmation card e harness. `REUSE_DECISION=REUSE/EXTEND`; nenhuma autoridade/planner/engine/provider rule nova.

## Progresso verificado por inspeção do SHA

O commit contém 21 arquivos de escopo backend/frontend/test/docs. `_resolve_turn_command` discrimina `MESSAGE`, `APPLY_PREPARED`, `REJECT_PREPARED`; rejeita texto misto, decisão incompatível e APPLY sob ceiling prepare. `_attempt_prepare` não realiza mais ACT direto; READY vira PendingWrite com propósito `execution_scope_choice` (owner false) ou `execution_scope_plus_owner_confirmation` (owner true). `_attempt_direct_act` tornou-se fail-closed; intent sem owner PREPARE não fabrica proposal. `_confirm_proposal` distingue corretamente a confirmação adicional owner do scope choice. O LLM não amplia scope. A integração MFE envia comando tipado sem texto no request de decisão.

O executor reportou 1121/1121 pytest, 189/189 vitest, federation build PASS, e migração de 10 strict-xfails para casos GREEN. **INDEPENDENT_REEXECUTION=TEST_NOT_RUN**. `tsc` reportado **FAIL** (4 erros alegadamente preexistentes; classificação independente `TO_INVENTORY`). Browser/live/outcome `TEST_NOT_RUN`.

## BLOQUEIO RW-01 — duas APPLY simultâneas não possuem consumo atômico

**PROVEN CODE FACTS:** `delia-api/app/application/interaction/pending_proposals.py` implementa `get(digest)` e `take(digest)` como consulta de dict seguida de exclusão, sem exclusividade/lock/reserva de in-flight/CAS. Em `orchestration.py`, `_attempt_confirmation` chama `get(digest)`; em `_confirm_proposal`, `self._pending_writes.take(record.digest)` tem retorno **ignorado** e é seguido de `_execute_prepared_act` quando `bind_confirmation` retorna CONFIRMED.

**Interleaving possível:** APPLY A e B recebem o mesmo `record` via `get` antes da exclusão; A realiza `take` e remove a entrada; B realiza `take` e recebe `None` (ou disputa a exclusão) e não verifica esse resultado; ambas podem prosseguir para `_execute_prepared_act`. Isto contradiz a alegação de "consumo atômico/single-use" no relatório 19. A execução duplicada empresarial **não foi testada nem observada**, portanto `CONCURRENT_DOUBLE_ACT_REAL=TEST_NOT_RUN`; o *gap* de exclusividade é PROVEN na leitura.

**Gate obrigatório:** teste RED controlado com duas APPLY para mesmo digest, actor/session/fingerprint válidos, barreira de concorrência; owner fake registra **no máximo um ACT**. Acrescentar corrida APPLY×REJECT, retry/timeout, expiration, multi-thread/worker e idempotência. Corrigir no menor seam legítimo com operação indivisível que **precisa garantir ao único vencedor** o direito de prosseguir; retorno de consume/reserve deve ser verificado. Revalidar owners e contratos antes de escolher lock/CAS/store. Não presumir exactly-once distribuído a partir de dicionário local.

## RESIDUAL RW-02 — comando tipado só é discriminado na borda HTTP

**PROVEN:** `interaction_routes.py` valida `command.type` e cria `InteractiveTurnRequest` **sem armazenar o discriminante**. `HandleInteractiveTurn` aceita um request baseado em `confirmation is not None`; `OperationalCapabilityOrchestrator._attempt` faz o mesmo. Portanto consumidores *in-process* do Application podem fornecer `confirmation` sem um comando tipado. A rota pública inspecionada é fail-closed; bypass HTTP público não foi demonstrado. É lacuna de consistência de contrato Application/HTTP.

**Gate obrigatório:** inventariar callers diretos; RED com `InteractiveTurnRequest` montado diretamente com combinação indevida e decisão sem discriminator; demonstrar política fail-closed ou justificar formalmente boundary com consumers. Caso exija contrato material novo, STOP → ARCHITECTURE_DECISION_REQUIRED.

## RESIDUAL UX-01 — pending card pode desaparecer após MESSAGE

`plugins/delia/src/App.tsx`, após **qualquer** `sendTurn` bem-sucedido, mapeia todos os `turn.confirmationRequest` para `confirmationAnswered=true`, mesmo para MESSAGE sem decisão. Isso oculta visualmente pendências que o backend pode conservar. Não prova ACT bypass; corrigir fidelidade UX usando *somente* target de APPLY/REJECT e manter pendência após MESSAGE. Incluir teste `PREPARE → unrelated MESSAGE → pending still visible`.

## Evidência/compatibilidade pendente

Inventário de consumidores HTTP/OpenAPI externos: `TO_INVENTORY` (ausência de resultados no repo não demonstra inexistência); tsc completo FAIL reportado; browser QA e Outcome empresarial `TEST_NOT_RUN`. O preview do MCP, owner policy e a decisão do usuário continuam authorities separadas. Nenhum teste de concorrência suficiente foi provado pelo relatório.

## Veredito e NEXT

`VERDICT=REWORK`; `RW-01=BLOCKING`; `RW-02=CONTRACT_GAP`; `UX-01=RESIDUAL`. B1 PASS estrutural histórico; B2 EVIDENCE_RECORDED / NOT_ACCEPTED; Stage02 NOT_ACCEPTED, Stage03 NOT_AUTHORIZED. `NEXT=RETURN_TO_ARCHITECTURE_COORDINATION` para autorizar bounded rework concorrência/contrato/UX, teste RED/GREEN, suíte completa e revisão independente posterior. Se inventário invalidar direção congelada, STOP/EXECUTION_DRIFT ou ARCHITECTURE_DECISION_REQUIRED. **Nenhum código funcional foi alterado por esta revisão.**
