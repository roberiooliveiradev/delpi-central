# 18 — Fechamento arquitetural B2: contrato de execução material vinculada à proposta

**TASK:** `DELIA-C3-STAGE-02-B2-EXECUTION-SCOPE-ARCHITECTURE-CLOSURE-01`
**DATA:** 2026-10-16
**REFERENCE_REMOTE_HEAD:** `9252a04f013c89680a3364b3de6300e80c3ba983` (GitHub remoto; status local TO_INVENTORY)
**MODE:** ARCHITECTURE / CONTRACT DECISION; DOCUMENTATION_ONLY; NO IMPLEMENTATION.
**DECISION:** `CONTRACT_DIRECTION_CLOSED_BY_ARCHITECTURE_COORDINATION` com base na regra de produto explicitamente aprovada em doc [17](./17-product-decision-text-only-prepare-until-scoped-execution-choice.md), ledger §6.183. `WIRE_IMPLEMENTATION=NOT_AUTHORIZED`; `STAGE_02_ACCEPTED=NO`; `STAGE_03_AUTHORIZED=NO`.

## 1. Reancoragem e precedência

Fontes e hierarquia revisadas no HEAD remoto: Project Instructions/.cursor → `16` → `50` → `17` → `49` → `51` → `52` → `21` → `20` → `25` → `02` arquitetura técnica → `24` produto → specs `60`/`69`/`70`/personality → ledger §§6.126/6.130/6.133/6.140/6.141/6.145/6.171–6.183 → docs 11–17 desta pasta. **Projeto/ledger continuam controlando a fase**. Contrato direction aqui congela a solução delimitada de B2 para preparação de implementação; não reabre ownership, não reivindica fase mais avançada nem reescreve §6.140.

**Product Master, aprovação específica (doc 17/§6.183):** texto livre pode até PREPARE; uma operação material precisa de escolha explícita de execução vinculada à operação, com mínimo de perguntas fora dessa decisão. O pedido de **'fechamento'** dirige a coordenação a resolver D1/D2/D3 e G1–G5 documentalmente. Não equivale a autorizar code diff, deploy ou aceite de runtime. O design deste documento é decisão da coordenação dentro desse princípio, não atribuir ao usuário aprovação prévia de sintaxe wire ou inferir consentimento humano infalível.

## 2. Decisão arquitetural delimitada — UMA escolha, SEM mistura de texto/ACT

**D1 FECHADO — `POST_PREPARE_OPERATION_BOUND_CHOICE` para a fatia conversacional material:**

- `MESSAGE` contendo texto livre é sempre **não elegível para ACT material**, mesmo se escrever 'crie', mesmo com LLM `execution_bound=unrestricted`, mesmo com owner `explicit_user_confirmation=false`. A DÉLIA pode READ/ANALYZE/DISCOVER/PREPARE pelos gates existentes; sem PREPARE legítimo, responder limitação verdadeira, não forjar preview.
- A elegibilidade para aplicar só aparece por **comando tipado de decisão em turno separado**, vinculado ao digest/fingerprint da proposta ou intenção exata mantida no backend. Não existe `ACT_ELIGIBLE` boolean no envelope `MESSAGE` nesta fatia, ao contrário da ALT-A original do doc 15. Isto fecha G1 por **separação sintática do canal ACT e texto livre**; não se tenta reconhecer toda negativa textual com LLM, parser ou regex.
- O usuário pode deliberadamente modificar um pedido anterior limitado a PREPARE ao escolher em novo turno executar a proposta exata ainda válida. Um ceiling `'prepare'` no turno de execução continua a bloquear ACT. A escolha não é session-sticky, não pode ser reutilizada com outra proposta e não se transfere entre usuários/sessões.
- `ACT_ELIGIBLE` é efeito da **decisão tipada vinculada**, nunca um grant Core/Domain. Toda execução segue Keycloak identity → live Core AuthZ → Domain final authority → capability/phase → DÉLIA Policy/Decision → owner confirmation → idempotence/audit → ACT → authoritative postcondition/Outcome. Output LLM / metadata / frontend state não autorizam.

**D2 FECHADO — comandos tipados mutuamente exclusivos:**

- `MESSAGE` precisa de texto não vazio, não permite `confirmation` e nunca ACT material.
- `APPLY_PREPARED` e `REJECT_PREPARED` **não aceitam texto livre concorrente**, e exigem uma referência backend-bound à proposta/intent. Uma mensagem 'Não aplique' é sempre `MESSAGE` e não coexiste com `APPLY_PREPARED`; body contraditório = `INVALID_REQUEST`/`turn_command_conflict`, zero ACT.
- Um cliente autenticado enviando APPLY com digests exatos é uma **declaração de escolha daquele solicitante autenticado**, não prova física de clique humano. Proteger contra binding errado, replay, TTL, revoke, CSRF conforme auth boundary real, e client bug; `source=user_click` nunca é prova suficiente.
- O comando `REJECT_PREPARED` invalida o pending correspondente e não executa. DÉLIA não converte simples mensagem 'sim' em APPLY sem comando tipado e binding. Não há segundo LLM nem prompt específico de provider.

**D3 FECHADO — bound do LLM somente redutor:**

- `_TurnGoal.execution_bound='prepare_only'` pode reduzir caminho da mensagem, nunca elevar scope ou operar como consentimento.
- Ausência, valor inválido ou `unrestricted` (inclusive erroneamente positivo) são **sem valor permissivo**; fail-closed como `NOT_ASSERTED` para ACT. Quando o objetivo estiver ausente/inválido, manter clarificação B1 existente; quando houver objetivo de escrita válido, permitir PREPARE se legítimo, sem perguntar desnecessariamente.
- O teto estruturado `max_execution_stage='prepare'` prevalece tanto em MESSAGE quanto em comando tipado APPLY; `None` nunca significa consentimento para ACT em MESSAGE.

## 3. Contrato de interação versionado — baseline de implementação (wire candidate normativo)

**API owner:** DÉLIA Application; borda HTTP é mapper/validator; Portal/MFE só transporte e affordance; Core/Domain permanecem authorities. O contrato conserva `POST /interaction/turns` e reutiliza payload `confirmation` com `decision`, `proposal_digest`, `preview_fingerprint`, `session_id` (todos validados no backend). A única extensão discriminante preferida é `command: {type: ...}` opcional. **Não introduzir simultaneamente** `command.execution_scope=ACT_ELIGIBLE` como campo positivo geral.

| Comando | Requisitos do body | Semântica de backend |
| --- | --- | --- |
| `MESSAGE` (ou `command` omitido sem confirmation) | `input` string não vazia; `confirmation` ausente; `max_execution_stage` opcional `prepare` | Sem ACT; intenção modelada pode gerar PREPARE e pending bound |
| `APPLY_PREPARED` | `command.type` exato + `confirmation.decision=CONFIRM` + digests/session; `input` ausente/vazio; teto não pode ser `prepare` | Verificar pending+binding+phase/live gates; satisfazer escolha de execução; ACT se autorizado |
| `REJECT_PREPARED` | `command.type` exato + `confirmation.decision=REJECT` + digests/session; `input` ausente/vazio | Invalidar pending correspondente; zero ACT |
| `command` inválido, `MESSAGE` com confirmation, APPLY/REJECT com texto livre, decision incompatível | 400 `INVALID_REQUEST`/`turn_command_conflict` (código específico candidato; reutilizar catálogo de erros se equivalente) | Nenhum ACT, nenhum fallback interpretativo |
| Legacy sem command, com `confirmation` + label gerada e conhecida | Apenas **período de migração**, labels PT **exatas** dos clientes publicados e digests/session válidos | Interpretar como comando tipado correspondente, auditar legacy; rejeitar texto arbitrário |

**G4 fechado por contrato discriminado:** atualmente `InteractiveTurnRequest.input_text` e `_validate_input` exigem texto não vazio. Na evolução, validar **a variante de comando antes** da regra de texto: `MESSAGE` mantém restrição; APPLY/REJECT permitem input ausente/vazio, não aceitam mensagem humana misturada. Registrar turn de decisão como evento/descrição determinística do backend sem falsificar fala livre, preservar session/actor/audit/provenance. Isto é uma alteração semântica deliberada de request, **não** alegar que a extensão é totalmente backward-compatible.

**Response:** continuar com surface bounded do `confirmation_request` e `PendingWrite` quando um PREPARE READY for elegível; acrescentar apenas distinção semântica explícita no payload/presentation entre `scope_choice_required` e `owner_confirmation_required`, derivada de política owner-sealed, não de heurística. Texto UI para owner `false`: 'Operação preparada. Escolha executar esta proposta.' Para owner `true`: 'Operação preparada. Confirme a execução desta proposta.' A **mesma ação explícita, exata e vinculada** pode cumprir escolha de escopo e confirmação adicional owner quando a policy requer, sem pedir dois cliques. Não expor raw owner proposal handle. Se a policy owner faltar/for inválida, fail-closed `owner_policy_invalid`.

## 4. Mecanismo de decisão e binding (G2/G3 fechados por contrato)

- Reutilizar `PendingWrite` backend, `proposal_digest`, `preview_fingerprint`, `session_id`, actor, TTL, live tools/list/revalidation e Decision Gate. O owner PREPARE `READY` e capability ACT legitima permitem pending com **tipo de necessidade** auditável: `execution_scope_choice` (owner false) ou `execution_scope_plus_owner_confirmation` (owner true). É semântica do request/presentation, não um novo owner policy nem um engine. Primeiro inventariar contrato de persistence e consumers antes de adicionar qualquer campo; preferir derivação determinística do preview.
- Ao processar APPLY, validar que digests correspondem à operação preparada exata, mesma identidade/sessão, não expirado, não consumido, categoria/operação estável e `max_execution_stage != prepare`. O backend deve consumir a decisão no store com semântica anti-replay/idempotente antes do side effect governado, revalidar Core/Domain/owner/phase e a pós-condição; nenhuma resposta `200` do MCP prova negócio concluído.
- Para owner `false`, APPLY é `execution_scope_choice` **sem declarar uma falsa `owner confirmation`**; o `confirmed` passado ao owner deve preservar a semântica owner-sealed (não fabricar `true` se não requerido). Para owner `true`, a escolha explícita de APPLY sobre preview exata **também** satisfaz a confirmação adicional exigida, usando binding existente e `ConfirmationRecord` real.
- REQUEST-SCOPED ceiling aplica-se ao turno que o contém; decisão APPLY posterior é nova decisão de usuário, não reutilização tácita do bound do turno anterior. Não persistir `ACT_ELIGIBLE` por usuário/conversa; não transformar Personal Memory em autorização.
- Se usuário depois enviar mensagem livre 'não aplique' enquanto há pending, é MESSAGE: zero ACT. A UI pode manter, rejeitar ou expirar pending sob política aprovada, mas não auto-executar. Uma escolha APPLY **posterior e explícita** pode modificar a intenção, desde que a proposta exata permaneça válida.
- Owner unavailable, proposal malformed, actor/session mismatch, tampering, expired, replay, permission revocation e phase-disabled → fail-closed e mensagem honesta. Auditar `decision_source=authenticated_typed_command`, `decision_purpose`, owner_confirmation_requirement, correlation e outcome sem guardar secrets/raw handles.

## 5. Tratamento de ACT-only / sem PREPARE (G3/G5)

Em `MESSAGE` sem owner PREPARE/preview legítimo, uma capability ACT-only **não executa** e não fabrica preview. O runtime atualmente admite `_attempt_direct_act` que gera pending *intent* com argumentos/fingerprint (sem owner proposal); esse equivalente é `PROVEN`, mas **não satisfaz automaticamente** a exigência da fatia principal de proposta preparada/preview verificável. `ACT_ONLY_FUTURE_SUPPORT=TO_INVENTORY`: somente permitir APPLY num intent se houver representação determinística suficiente e binding completo validado sob contrato separado; até essa prova, responder `WRITE_REJECTED / PRECONDITION_REQUIRED` com explicação, e não chamar ACT. Não exigir que MCP Owner altere sua autoridade por conveniência.

## 6. G5 — migração, versionamento e rollout (design fechado; inventário de consumers ainda factual)

- Corpo atual tem allowlist estrita e confirmation top-level. Evoluir contrato versionado `interaction/turns` preservando campos atuais; `command` opcional discriminante, não escopo positivo solto em MESSAGE. Manter errors/status canônicos quando possível; registrar OpenAPI/`operationId` estável na implementação após inventário. Não declarar backward-compatible em comportamento: texto livre que antes podia executar passa a PREPARE.
- Backend **fail-closed primeiro**: nenhum legacy MESSAGE sem escolha bound faz ACT; mesmo clientes não migrados recebem PREPARE/pending. Depois atualizar `plugins/delia` + `interactionClient` com comando sem texto, preview e CTA inequívoca; ao final remover tolerância temporária a labels fixas conforme métricas/consumers. Consumidores não-MFE ainda `TO_INVENTORY`; bloqueiam rollout sem inventário, não invalidam esta direção arquitetural.
- Compatibilidade de confirmation legacy: aceitar exclusivamente labels fixas documentadas do MFE atual com `confirmation` autenticado/bound e digest válido enquanto houver client legado publicado, com telemetria e sunset; input arbitrário + confirmation sempre rejeitado. Precedência v2: comando tipado e invariantes dominam; **não** analisar modelo como arbitro de conflito.
- Rollback: preservar READ/PREPARE e desligar ACT da nova via por gate de fase/policy existente, se comprovado; **nunca** restaurar ACT direto fail-open em MESSAGE. Não criar flag ad hoc nem obrigar downgrade inseguro. Aplicar tráfego/versão monitorados antes de remover compat.

## 7. Reuse/Abstraction Gate

`EXISTING_EQUIVALENT=YES`: `InteractiveTurnRequest.max_execution_stage`, `HandleInteractiveTurn`, `_TurnGoal`, `OperationalCapabilityOrchestrator`, `PendingWriteStore`, `StructuredConfirmation` + `bind_confirmation`, `evaluate_write_continuation`, `confirmation_request`, MFE e shared components. `REUSE_DECISION=REUSE/EXTEND` de seams já legítimas: request discriminator/validators, governed write lifecycle e presentation metadata. `NEW=NOT_AUTHORIZED` (nenhum planner/service/registry/engine/Provider-specific guard). Mudança de contrato deve incluir owner/consumers/security/observability/idempotency/compat, não apenas alterar um enum.

## 8. Matriz de aceitação (IMPLEMENTATION/PASS pendentes)

| Case | Evidência exigida |
| --- | --- |
| B2-DIAG-01/02/03/07/09, 10 strict-xfail | MESSAGE com qualquer proposta LLM `unrestricted`, ausente, inválido e owner direct → zero ACT; testes devem virar PASS real de segurança |
| Texto livre 'Crie X' | PREPARE com output/preview legítimo; gera decisão vinculada, nunca executa materialmente no mesmo turno |
| PREPARE_ONLY e teto `prepare` | Bloqueiam ACT, inclusive APPLY com teto `prepare` no request |
| APPLY bound, owner false | Um comando autenticado vinculado à proposta exata permite governed ACT após todos os gates, sem alegar owner confirmation adicional |
| APPLY bound, owner true | Mesma escolha vinculada também cumpre confirmação do owner; não exigência dupla artificial |
| Contradição | APPLY com 'não aplique'/qualquer free text, MESSAGE+confirmation, scope conflitante → fail-closed, zero ACT |
| REJECT | Consome/cancela pending corretamente; zero ACT |
| G2 trust | Cliente com sinal arbitrário/sem pending; token revogado; actor/session/owner mismatch; tampering/replay/expiry → zero ACT |
| G4 compat | Legacy label fixa + digests válidos funciona temporariamente; label arbitrária rejeita; MESSAGE vazio rejeita; typed APPLY sem texto funciona |
| G5 | Consumers HTTP/OpenAPI/MFE/tests/other clients inventariados e contrato versionado; ACT-only sem preview rejeita sem side effects |
| Provider metamorphic | Renomear owner/tool, variar class, no hardcode, Policy/Decision e Outcome permanecem |

Ensaios contra Core/Domain reais ou LLM real devem ser autorizados separadamente. Nenhum ACT real de negócio; registrar `TEST_NOT_RUN` até execução. Regressão, eval generalization, safety e Outcome são necessários no SHA/config homologados; suites green sem Task Outcome não aceitam a etapa.

## 9. Rastreabilidade e gates

CP-055 injection, CP-057 idempotency, CP-071 única DÉLIA, CP-094 epistemic, CP-107 approval, CP-110/111 policy/approval, CP-205 semantic capability, CP-263/264/265 MCP governance — IDs existentes em `25`; nenhum CP local inventado. Consultar matriz `20` e contracts/consumers efetivos antes da task. Owner TÉO/VISTA/DAVI não muda. `C5` e fases superiores não recebem nova autorização desta ADR.

**RESOLUTION:** D1/C3 interactive post-PREPARE exact-choice `CLOSED_BY_COORDINATION`; D2 command segregation + legacy fallback `CLOSED_BY_COORDINATION`; D3 LLM-only reduction `CLOSED_BY_COORDINATION`. G1 structural conflict separation `CLOSED_BY_DESIGN`; G2 authenticated scoped assertion + binding `CLOSED_BY_DESIGN` (physical click proof not claimed); G3 pending-purpose distinction `CLOSED_BY_DESIGN`; G4 discriminated input validation `CLOSED_BY_DESIGN`; G5 migration rules `CLOSED_BY_DESIGN` with **CONSUMER_INVENTORY=TO_INVENTORY** for implementation gate.

**Limite explícito:** fechamento é de **arquitetura/semântica de contrato**, não alegação de código implementado, consumidores testados, OpenAPI publicada ou produção segura. Se inventário factual contradisser as premissas, STOP → `EXECUTION_DRIFT`/`ARCHITECTURE_DECISION_REQUIRED`, nunca redesenhar silenciosamente. A coordenação pode autorizar separadamente próxima task bounded após reanchor; documentação não avança a fase.

CONTRACT_DIRECTION_CLOSED_BY_ARCHITECTURE_COORDINATION=YES
PRODUCT_RULE=APPROVED (doc 17 / §6.183)
B2_IMPLEMENTATION=NOT_STARTED; B2_SECURITY_ACCEPTANCE=NO; STAGE_02_ACCEPTED=NO; STAGE_03_AUTHORIZED=NO
C3_EXECUTED=NO; C4_AUTHORIZED=NO; C5_AUTHORIZED=NO; NEXT=RETURN_TO_ARCHITECTURE_COORDINATION
