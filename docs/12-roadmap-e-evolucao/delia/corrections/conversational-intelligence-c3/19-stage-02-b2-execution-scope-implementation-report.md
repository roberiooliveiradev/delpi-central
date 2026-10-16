# 19 — Stage 02 · B2 Execution-Scope Implementation Report

**TASK:** `DELIA-C3-STAGE-02-B2-EXECUTION-SCOPE-FULL-IMPLEMENTATION-01`
**MODE:** `REANCHOR → INVENTORY → REUSE GATE → CONTRACT → RED TESTS → BACKEND → FRONTEND → INTEGRATION → GREEN TESTS → SECURITY REVIEW → DOCUMENT → COMMIT → PUSH → VERIFY MAIN → REPORT`
**AUTHORITY:** documento [18](./18-execution-scope-architecture-contract-closure.md) (direção de contrato FECHADA pela coordenação), subordinado a §6.179 (princípio de produto) e §6.183 (regra D1 de produto). Documentos 14/15/16 permanecem históricos.
**ESCOPO:** somente a correção B2 da Etapa 02. Sem Etapa 03, sem redesign arquitetural, sem ACT real em dados empresariais, sem alteração de ownership.

---

## 1. Contrato implementado

Critério central (documento 18):

| Regra | Resultado |
|---|---|
| `MESSAGE → PREPARE, NEVER MATERIAL ACT` | **IMPLEMENTADO + TESTADO** |
| `VALID OPERATION-BOUND APPLY_PREPARED → GOVERNED ACT` | **IMPLEMENTADO + TESTADO** |
| `REJECT_PREPARED → NO ACT` | **IMPLEMENTADO + TESTADO** |
| `CONFLICT / INVALID / STALE / UNAUTHORIZED → NO ACT` | **IMPLEMENTADO + TESTADO** |

### Vocabulário de comandos tipados

| `command.type` | Requisito | Semântica |
|---|---|---|
| `MESSAGE` | `input` não vazio; sem `confirmation` | READ / ANALYSIS / PREPARE conforme gates; nunca ACT material no turno |
| `APPLY_PREPARED` | sem texto livre; `confirmation.decision=CONFIRM`; digest/fingerprint/session válidos | única porta para ACT, com revalidação viva de capability, Core/Domain AuthZ, owner invocation e outcome |
| `REJECT_PREPARED` | sem texto livre; `confirmation.decision=REJECT` | consome/cancela a proposta pendente; nunca ACT |

Sem `command` → compatibilidade por forma: texto puro = `MESSAGE`; `confirmation` + label legada **exata** (`LEGACY_CONFIRMATION_LABELS`, janela temporária de migração) → comando tipado equivalente; qualquer texto arbitrário sobre `confirmation` → rejeitado (`400`).

`max_execution_stage="prepare"` permanece reduction-only e bloqueia `APPLY_PREPARED` tanto na forma tipada quanto na legada — na fronteira HTTP **e** na orquestração (defesa em profundidade).

### Distinção de propósito (G3, §6.184)

`PendingWrite` agora carrega `pending_purpose`:

- `execution_scope_choice` — owner declarou `explicit_user_confirmation=false`; a proposta aguarda apenas a **escolha de escopo** do usuário. Não é apresentada nem auditada como confirmação exigida pelo owner.
- `execution_scope_plus_owner_confirmation` — owner declarou `explicit_user_confirmation=true`; um único `APPLY_PREPARED` vinculado satisfaz simultaneamente a escolha de escopo e a confirmação do owner (um clique, duas necessidades, sem duplicação artificial).

O propósito é derivado da política real declarada pelo owner no PREPARE — nunca fabricado.

## 2. Reuse Gate

| Capability | EXISTING_EQUIVALENT | REUSE_DECISION |
|---|---|---|
| `/interaction/turns` request/response | YES | EXTEND (campo `command` aditivo, allowlist estrita) |
| `_validate_execution_ceiling` / `max_execution_stage` | YES | REUSE (reduction-only preservado) |
| `PendingWriteStore` / confirmação estruturada | YES | EXTEND (`pending_purpose`; pending agora nasce de proposta PREPARE) |
| `_execute_prepared_act` (single ACT path) | YES | REUSE (revalidação viva + gates preservados) |
| `LEGACY_CONFIRMATION_LABELS` | YES | EXTEND (allowlist exata, janela de migração) |
| `GovernedConfirmation` (plugin-ui) | YES | REUSE (presentation-only, loading guards) |
| `interactionClient` / `App` | YES | EXTEND (comandos tipados) |
| Novo planner / execution engine / policy engine / catálogo MCP / agent / confirmação universal | — | **NÃO CRIADO** (proibido pelo contrato) |

## 3. Backend

### Orquestração (`capability_provision/orchestration.py`)

- **`_attempt_prepare`**: toda proposta `READY` vira `PendingWrite` com digest + fingerprint + `pending_purpose` derivado da política do owner, e retorna `CONFIRMATION_REQUIRED`. O mesmo-turno ACT direto foi removido — `MESSAGE` encerra em PREPARE mesmo quando o owner declara `explicit_user_confirmation=false`.
- **`_attempt_direct_act`**: fail-closed. Seleção fria de capability ACT via texto livre é recusada verdadeiramente (`precondition_required`); sob ceiling `prepare`, `execution_ceiling`. ACT-only sem PREPARE/preview verificável não fabrica proposta — bloqueio governado (documento 18 §4.6).
- **`_attempt_confirmation` / `_confirm_proposal`**: dispatch unificado por decisão; `REJECT` consome a pendência sem invocar o owner; `CONFIRM` segue pelo caminho único `_execute_prepared_act` com revalidação viva de `tools/list`, Core AuthZ, revalidação de domínio e outcome projection. O propósito `execution_scope_plus_owner_confirmation` registra `ConfirmationRecord` legítimo; `execution_scope_choice` não falsifica confirmação de owner.
- **`_confirm_intent`** (pending-intent por texto livre): removido — caminho morto que permitiria continuação de escrita sem proposta PREPARE verificável.
- **`execution_bound` do modelo**: reduction-only (`prepare_only` só restringe; `unrestricted`/ausente/inválido/timeout nunca concede ACT — e agora é irrelevante para elegibilidade, pois `MESSAGE` nunca alcança ACT).

### Fronteira HTTP (`interfaces/http/interaction_routes.py`)

- `command` na allowlist do body; `_resolve_turn_command` resolve deterministicamente as três variantes antes de qualquer orquestração.
- Rejeições fail-closed: `command` não-objeto, `command.type` desconhecido, campos extras em `command`, `MESSAGE` sem texto ou com `confirmation`, `APPLY`/`REJECT` com texto livre, `decision` incompatível com o comando, `APPLY` sob ceiling `prepare`, texto arbitrário sobre `confirmation` (fora das labels legadas exatas).
- Observabilidade: log do `command.type` resolvido por `request_id` — sem texto de usuário, digests ou handles.

### Aplicação (`interaction/handle_interactive_turn.py`, `contracts.py`, `pending_proposals.py`)

- Validação de input command-aware: `MESSAGE` exige texto; decisões tipadas aceitam turno sem texto.
- `InteractiveTurnRequest` inalterado em autoridade: `access_context` continua Core-resolved; `confirmation` permanece untrusted e só carrega decisão + digests.
- `PendingWrite` carrega `pending_purpose` e o preview digerido; `proposal_ref` permanece backend-only.

## 4. Frontend (`plugins/delia`)

- **`interactionClient.ts`**: tipos de comando (`MESSAGE`/`APPLY_PREPARED`/`REJECT_PREPARED`); turnos comuns enviam `command: { type: "MESSAGE" }` explicitamente; decisões enviam o comando tipado **sem** `input` (nenhum texto livre viaja como autorização); `confirmation` preserva `decision`, `proposal_digest`, `preview_fingerprint`, `session_id` verbatim; `pending_purpose` é parseado do `confirmation_request` para apresentação.
- **`App.tsx`**: `handleConfirmation` envia `APPLY_PREPARED`/`REJECT_PREPARED`; labels PT fixos deixam de ser mecanismo de autorização; demo mode permanece visual-only e network-free; card consumido após decisão (single-use); loading guards anti-duplo-submit.
- **`DeliaAssistantMessage.tsx`**: copy purpose-aware — `execution_scope_choice` → título «Operação pronta para execução», CTA «Executar»; `execution_scope_plus_owner_confirmation` → «Confirmação necessária», CTA «Confirmar e executar»; cancelamento sempre «Cancelar». Digests, fingerprints, session IDs e handles nunca renderizados.

## 5. Compatibilidade e consumidores

| Consumidor | Estado |
|---|---|
| `plugins/delia` (MFE) | Migrado — comandos tipados em todos os turnos |
| `delia-api/scripts/real_provider_neutral_eval.py` | Migrado — `MESSAGE` tipado; `_confirm` usa `APPLY_PREPARED`/`REJECT_PREPARED`; checks D1/D2 reescritos para o fluxo two-turn (`write_message_no_direct_act`, `write_apply_governed_act`, `write_apply_owner_verified`); slide-id extraído da resposta do APPLY |
| `delia-api/scripts/real_governed_read_eval.py` | Inalterado — read-only; `{"input"}` sem comando resolve como `MESSAGE` pela forma (compat intencional) |
| `delia-api/scripts/real_multistep_orchestration_eval.py` | Inalterado — read/análise; mesmo compat por forma |
| `real_model_eval.py` / `real_model_continuity_eval.py` | Inalterados — in-process, constroem `InteractiveTurnRequest` diretamente sem `confirmation` |
| Non-MFE externos identificáveis | `TO_INVENTORY` — nenhum além dos acima foi localizado no repo |

`delia-api` não publica OpenAPI próprio para `/interaction/turns` (rota interna de plugin); o contrato é os testes de fronteira + este documento.

## 6. Resultados RED → GREEN

**RED (antes da correção, HEAD de referência):** os 10 casos strict-xfail de `test_stage02r2_execution_bound_diagnosis.py` foram convertidos em assertions do contrato fechado — `test_b2diag01_textual_bound_vs_unrestricted_proposal` reproduziu `commit_record` invocado sobre «prepare, mas não aplique» com `execution_bound=unrestricted`. Falha real observada antes da implementação.

**GREEN (após a correção):**

| Suíte | Comando | Resultado |
|---|---|---|
| `delia-api` completa | `pytest` | **1121 coletados, 0 falhas — PASS** |
| Contrato B2 (diagnosis convertido + boundary) | pytest direcionado | **PASS** |
| `plugins/delia` | `vitest run` | **189 testes, 16 arquivos — PASS** |
| `plugins/delia` typecheck | `tsc -p tsconfig.app.json` | **FAIL residual pré-existente** — 4 erros em arquivos fora do escopo (`s2.shell.test.tsx:238`, `plugin-ui` ×3), idênticos em HEAD (verificado via `git show HEAD`); zero erros nos arquivos alterados |
| `plugins/delia` build/federation | `vite build` | **PASS** — `__federation_expose_App` gerado |
| Eval script | `py_compile` | **PASS** sintático; execução live = `TEST_NOT_RUN` (exige stack real) |

Testes legados que assertavam ACT direto no mesmo turno foram migrados para o contrato two-turn (`MESSAGE → PREPARE → APPLY → ACT`), preservando as assertions negativas (zero ACT em MESSAGE) — nenhum expected foi enfraquecido para esconder regressão.

## 7. Security review (§9 da task)

| Item | Veredito |
|---|---|
| MESSAGE nunca alcança ACT material | OK — toda proposta READY vira pending; direct-ACT fail-closed |
| Classificação do LLM libera ACT | OK — `execution_bound` reduction-only; `unrestricted` inerte |
| Owner metadata libera ACT | OK — `explicit_user_confirmation=false` ainda exige escolha de escopo |
| Confirmação falsa enviada ao owner | OK — `pending_purpose` distingue escopo de owner-confirmation |
| ACT exige escolha tipada vinculada à proposta | OK — digest + fingerprint + session + TTL + single-use |
| Core/Domain/Policy/Decision preservados | OK — `_execute_prepared_act` revalida a surface viva e todos os gates |
| Reaproveitamento de escopo entre turnos | OK — sem flag de sessão; decisão vinculada a uma pendência |
| Bypass em continuação direta | OK — `_confirm_intent` removido |
| Bypass na confirmação | OK — ceiling checado na fronteira e na orquestração |
| Bypass em ACT frio | OK — `precondition_required` / `execution_ceiling` |
| Dupla execução por replay | OK — pending single-use, consumo atômico |
| Planner/engine duplicado | OK — zero módulos novos |
| Branches por nome de provider/capability | OK — decisão por `operation_class`/schema, nunca por nome |
| Segredo/handle no frontend/log | OK — digests only; `proposal_ref` backend-only; log só de `command.type` |

## 8. Lacunas honestas

- **Typecheck delia**: 4 erros pré-existentes em arquivos não pertencentes à task (`s2.shell.test.tsx`, `plugin-ui`) — `STALE_EVIDENCE`/dívida documentada, não introduzida por este diff.
- **Browser QA**: `TEST_NOT_RUN` — sem harness de browser nesta sessão; cobertura via Vitest (189 testes incluindo render, payload, labels, consumo de card).
- **Live evals**: `TEST_NOT_RUN` — `real_provider_neutral_eval.py` atualizado para o contrato mas exige stack/token real; classificação `TARGET`.
- **Janela de compatibilidade**: labels legadas PT continuam aceitas por exact-match — remoção depende de evidência de que nenhum cliente material as envia (G5).
- **ACT-only sem PREPARE verificável**: bloqueado por desenho — qualquer flexibilização futura exige revisão separada (documento 18 §4.6).
- **Business outcome real**: não provado — `pytest` verde e HTTP 200 não são Outcome empresarial.

## 9. Estado

`B2_IMPLEMENTATION=COMPLETE_PENDING_INDEPENDENT_REVIEW`; `B2=REWORK→EVIDENCE_RECORDED`; `STAGE_02_ACCEPTED=NO`; `STAGE_03_AUTHORIZED=NO`; `PRODUCTION_READINESS=NOT_PROVEN`.

**NEXT:** `INDEPENDENT_REVIEW` do diff + veredito sobre B2; só então decisão de aceite da Etapa 02.
