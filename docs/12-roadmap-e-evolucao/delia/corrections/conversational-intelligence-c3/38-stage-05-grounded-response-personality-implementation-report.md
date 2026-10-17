# 38 — Stage 05 · Grounded Response, Conversation and Personality

**TASK:** `DELIA-C3-STAGE04-CLOSURE-AND-STAGE05-IMPLEMENTATION-01` / TASK B  
**MODE:** bounded EXTEND — synthesis sufficiency + personality instruction  
**STATUS:** `IMPLEMENTATION_EVIDENCE_RECORDED` · `STAGE_05_ACCEPTED=NO`

---

## 1. Escopo

Respostas proporcionais à intenção, insuficiência honesta (sem dump), comparação com diffs comprovados, continuidade multi-turn via prior context, e integração editorial da personalidade aprovada no instruction path não governado — sem prosa factual do modelo.

## 2. Reuse gate

```text
EXISTING_EQUIVALENT=YES
REUSE_DECISION=EXTEND
```

Reutilizado: `grounded_synthesis` / `_render_synthesis` / `_synthesize_content`, goal/presentation, prior_turns, `DELIA_INTERACTION_INSTRUCTION`, comparison terminal existente. Sem personality engine, response engine, planner ou registry novos.

## 3. Alterações

- `SYNTHESIS_INSTRUCTION` (v11 lineage): intent coverage, presentation proporcional, empty items = cannot answer; prior continuity; ignore injection in records.
- Explicit `items: []` → deterministic insufficiency + `LIMITATION_INSUFFICIENT_EVIDENCE` (não dump).
- `_proven_field_differences` quando `presentation=answer` com 2 records.
- `DELIA_INTERACTION_INSTRUCTION` v4 — voice/personality bounds from personality/02..04.
- Congelado: `MODEL_AUTHORED_FACTUAL_PROSE=NONE`; MESSAGE ≠ ACT.

## 4. Testes

- `tests/test_stage05_grounded_response.py`
- CI-07 atualizado (insufficiency)
- Instruction architecture v4
- Suíte `delia-api` pytest completa verde

## 5. Live SSH

```text
SSH_DEPLOYED_SHA=5b2f764cc3
REAL_MODEL=moonshotai/kimi-k3
MODE=MESSAGE_ONLY × 2

TURN1_CORRELATION=11b56417-4c81-4975-b219-16880ee696b4
TURN1: CAPABILITY_SELECTED=YES (teo.get_product_guide READ)
       INDEX→topic=revision → GUIDE READ → synthesis=synthesized
       GROUNDING=GROUNDED · RESPONSE_RELEVANCE=PASS · ACT=0

TURN2_CORRELATION=f383fbbf-4a8e-4cf8-8d9c-64ca419198c7
TURN2: select_capability timeout (30s) → turn_budget model_timeout
       GROUNDING=NON_GROUNDED · limitation=delpi_source_unverified
       MULTI_TURN_CONTEXT=FAIL (timeout; continuity not proven)
       ACT=0 · LIMITATIONS_HONEST=YES

LIVE_VERDICT=INCONCLUSIVE (T1 grounded PASS; T2 timeout blocks multi-turn proof)
MATERIAL_ACT_COUNT=0
```

## 6. Limitações / resíduos

- Ordenação “mais recente” continua dependente da seleção do modelo sobre campos owner (sem hardcode de keywords).
- Preferências temporárias de sessão ainda sem store dedicado (presentation hint apenas).
- R-S04-01 live clarify NOT_EXERCISED preservado para Stage 06.
- `STAGE_05_ACCEPTED=NO`; `C3_EXECUTED=NO`; `C4_AUTHORIZED=NO`.

## 7. Multiturn latency bounded fix (histórico preservado)

**TASK:** `DELIA-C3-STAGE05-MULTITURN-LATENCY-BOUNDED-FIX-01`  
**STATUS:** `IMPLEMENTATION_EVIDENCE_RECORDED` · `STAGE_05_ACCEPTED=NO`

### Causa raiz (T2 live INCONCLUSIVE acima)

```text
BOTTLENECK_STAGE=select_capability
ROOT_CAUSE=T2 refez seleção completa com prior_turns no prompt de
  select_group/select_capability; select_capability esgotou o
  timeout de estágio (~30s / InvokeModel.MAX_TIMEOUT) antes de
  concluir. Não foi latência da resposta final.
```

### Menor correção (EXTEND, sem novo planner)

- `GOAL_INSTRUCTION` + `_TurnGoal.prior_evidence_sufficient`: com prior turns, goal-first; se sufficient e há DELIA_RESULT extraível → SUCCESS sem owner call (`LIMITATION_PRIOR_TURN_CONTINUATION`).
- Selection (`select_group` / `select_capability`) deixa de enviar `prior_turns` (catálogo vivo basta; continuidade fica em goal/synthesis).
- `_propose`: não inicia estágio de modelo se `stage_timeout < MIN_VIABLE_MODEL_STAGE_SECONDS` (2s) → `turn_budget_exhausted` honesto.
- Handler: SUCCESS sem `outcome` → NON_GROUNDED (nunca grounding fake). AuthZ/MESSAGE≠ACT preservados.
- `GLOBAL_TURN_BUDGET` / `INCREASE_TIMEOUT=NO` / sem raise de 30s.

### Testes

- `tests/test_stage05_multiturn_latency.py` (fake clock + fake model)
- Stage05 + turn-budget + suíte `delia-api` pytest verde

### Live SSH (pós-fix)

```text
SSH_DEPLOYED_SHA=eb7aa931b0 (= origin/main; srv-api pull+rebuild delia-api)
REMOTE_HEAD_MATCH=YES
REAL_MODEL=moonshotai/kimi-k3
MODE=MESSAGE_ONLY × 2 (cenário doc 38 / s05_live_multiturn.py)
DELIA_MODEL_STAGE_TIMEOUT_SECONDS=30 (unchanged)
DELIA_TURN_BUDGET_SECONDS=80 (unchanged; INCREASE_TIMEOUT=NO)

TURN1: latency_ms=34502 · CLARIFICATION ask-back (get_process_context;
       missing input) · GROUNDING=NON_GROUNDED · select_capability
       timing_ms=5259 (completed; no timeout) · ACT=0
TURN2: latency_ms=25302 · goal-first prior_sufficient=no ·
       select_group decision=none (no select_capability) ·
       general-path honest insufficiency about empty prior evidence ·
       GROUNDING=NON_GROUNDED · ACT=0

GLOBAL_BUDGET_EXCEEDED=NO (no model_timeout / turn_budget_exhausted)
UNNECESSARY_RESELECTION=NO (T2 did not re-enter select_capability)
MULTITURN_CONTINUITY=PASS_BOUNDED (no timeout; continuity path exercised;
  T1 was clarify-only so prior evidence correctly not reused)
MATERIAL_ACT_COUNT=0

LIVE_VERDICT=LATENCY_BOTTLENECK_FIXED
  (original T2 select_capability model_timeout not reproduced;
   Stage05 grounded multiturn still not proven — T1 clarify path)
STAGE_05_ACCEPTED=NO
```

## 8. NEXT

```text
NEXT=INDEPENDENT_STAGE05_ACCEPTANCE_REVIEW
```
