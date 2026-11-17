# C3/T2 — Two-Agent A/B functional comparison — evidence

TASK: COORDINATION_C3_T2_TWO_AGENT_LAYERED_HANDOFF_AND_FUNCTIONAL_RECOVERY
SHA: d60fed08b2 · corpus INT2×15 · qwen/qwen3-14b fp e4a5b706a3b3156b
· profile openrouter_qwen · PROD_CONTAINER_UNTOUCHED=YES (ambos)

VARIANT A (single-agent, DELIA_TWO_AGENT_EXPERIMENT=0):
run or-qwen14b-1d86e34f0958
GROUNDED 8/15: A A2 B C E G G2 R5
NON_GROUNDED 7/15: C2 D D2 E2 F R6c R6mt
tokens 640.984in / 36.378out · writes 0

VARIANT B (two-agent seq, flag=1):
run or-qwen14b-1557f58b9c15
GROUNDED 8/15: A A2 C C2 E G2 R5 R6mt
NON_GROUNDED 7/15: B D D2 E2 G F R6c
tokens 569.892in / 34.542out · writes 0

DIVERGENCES:
  A>W: INT2_B agg count (A grounded, B INCONCLUSIVE),
        INT2_G agg variant (A grounded, B NG)
  B>W: INT2_C2 product detail (B grounded, A NG),
        INT2_R6mt multiturn recovery (B grounded, A NG)
  parity: A/A2/C/E/G2/R5 grounded both; D/D2/E2/F/R6c NG both

HANDOFF INVARIANTS (code): run_investigation = flag AND
  handoff_error is None AND plan accepted (H1/H8);
  comprehension_agent_error classified fail-closed
  (UnexpectedModelBehavior → output_retries_exhausted class);
  T2-B residual NOT_REPRODUCED (single-occurrence flake, absent
  in two consecutive B runs).

BUSINESS_OUTCOME_SUPERIORITY: NOT_PROVEN — 8/15 vs 8/15 grounded,
  divergences bidirecionais consistentes com variância de modelo
  (n=1/cenário); B marginalmente mais barato (~11% menos tokens
  de input) mas sem outcome superior provado. Safety parity:
  writes=0, injection refused, filter drift=0 em ambos.

## B/G divergence — causal analysis (trace-level, runs 1557f58b vs 1d86e34f)

FIRST_DIVERGENT_BOUNDARY: COMPREHENSION — capability/strategy selection,
não defect de contrato.

INT2_G (B/two-agent): teo.analyze {view:"summary",params:{}} +
{view:"processes"} — declared `view=summary` ECHOED correctly (view é
top-level arg do analyze, sem mismatch de carrier). Owner retornou
aggregated views sem métrica de count (meta.row_count=null). Modelo
declarou "complete" → Application override → INCONCLUSIVE correto (S9).

INT2_B (B/two-agent): mesmo padrão — analyze view=summary, obrigação
operation=analysis; métrica não demonstrada → INCONCLUSIVE honesto.

INT2_B/G (A/single): modelo escolheu teo.read search → total
autoritativo do owner → SATISFIED legítimo.

VERDICT: MODEL_STRATEGY_VARIANCE — ambos os caminhos são legítimos;
a trajetória analyze coletou evidência que não continha a métrica
pedida → INCONCLUSIVE é o outcome correto, não regressão. Nenhum
defeito reproduzido → nenhuma alteração de código (RQ-7).

RESIDUAL candidate: analyze summary view não expõe count de processos
(limitação de capacidade do owner; alternativa read+total existe).

## INVESTIGATION↔SUFFICIENCY gap — remediated (bounded native correction)

DEFECT_PROVEN: output validator had NO bounded correction for
"COMPLETE/PARTIAL declared with collected evidence while material
obligations remain undemonstrated" — the model was never told which
obligation stayed open; the deterministic acceptor silently
overrode to INCONCLUSIVE (the B/G outcome).

RED: test_unmet_obligation_complete_declaration_buys_one_pass fails on
baseline (no RetryPromptPart) — proven by reverting the fix.

FIX (REUSE, ~55 LOC, zero new abstraction): 5th one-shot branch in
_investigation_answer_shape — when COMPLETE/PARTIAL + plan +
collected evidence + budget remain, evaluate obligations via the SAME
deterministic _evaluate_material_obligations/_plan_delivery_mode the
acceptor uses; if any != SATISFIED → one ModelRetry naming the unmet
obligations. Model may call a complementary governed capability or
re-declare honestly. Verdict authority unchanged — a second unproven
declaration finalizes INCONCLUSIVE. Shares the existing
insufficiency_retry_used flag → strictly one extra pass, bounded by
tool_calls_limit.

GREEN: 3 new tests (gap feedback fires + complementary call; budget-
exhausted guard; one-shot bound). Full delia-api suite exit 0.

Q-ANSWERS: Q1 YES (NEW_INFORMATION); Q2 YES (acceptor); Q3 was NO →
now YES via governed ModelRetry; Q4 now YES; Q5 yes-premature now
corrected; Q6 was NO → now bounded correction exists; Q7 gated by
tool_calls_limit; Q8 model chooses from live catalog (no hardcode);
Q9 one-shot + existing no-progress detectors; Q10 decided by model.

SAFETY invariants preserved: no false SATISFIED path added; obligation
evaluation read-only reuse; plan/filters/scope untouched; no
owner/capability hardcode; no ACT.

REAL_EVAL: ENV_BLOCKED — only delia-delia-api container up; eval stack
(gateway/keycloak/teo) down. Unit-level real-path proof via
FunctionModel through the real Agent/toolset/governed invoke chain.
Paired OpenRouter eval remains a residual pending stack recovery.

## REAL-MODEL EVAL @917e5c764c (fix 522a1fefe7 in HEAD) — paired B/G

MODEL qwen/qwen3-14b · openrouter_qwen · stack DEV 11 containers up
· eval container bind-mounted worktree · PROD_CONTAINER_UNTOUCHED=YES

ARM B (two-agent, flag=1) run or-qwen14b-3c4b119d2537:
- INT2_B NON_GROUNDED — trajectory analyze(view:summary)→analyze(view:meta)
  →read(process,search,status:active)→get_context→read(process,search).
  interrupted:1 = exactly ONE output-validator retry fired; only the NEW
  branch matches the state (plan present + evidence collected +
  COMPLETE w/ unmet obligations) → bounded correction FIRED in real
  eval; model sought complementary capabilities (no hardcode).
  Final declared "complete" claiming 109 → acceptor correctly
  overrode: obligation required_scope=[view=summary,__container__=params]
  + operation=analysis is unechoable by read scope → UNSATISFIED →
  honest NON_GROUNDED. ZERO false SATISFIED.
- INT2_G GROUNDED — direct read→authoritative total, SATISFIED 1st try.

ARM A (single-agent, flag=0):
- INT2_B GROUNDED (read→total); INT2_G GROUNDED (read→total).

VERDICT: REAL_MODEL_GAP_RECOVERY = MECHANISM_PROVEN_OUTCOME_PARTIAL
- Recovery path exercised: feedback→continuation→complementary calls ✓
- Final grounding still honest NON_GROUNDED on B: NEW RESIDUAL —
  comprehension-accepted obligation over-anchored to presentation
  envelope (view=summary/operation=analysis) for a count objective;
  read-derived authoritative totals cannot bind that scope. Fail-closed
  behavior is CORRECT (no scope-drift acceptance); the anchor choice is
  a comprehension-quality residual for a dedicated task — relaxing
  scope matching is FORBIDDEN by contract.

SAFETY (this eval): FALSE_SATISFIED 0 · FALSE_COMPLETE 0 · FILTER_DRIFT 0
· CROSS_OWNER 0 · WRITES 0 · AUTHZ_BYPASS 0 · UNBOUNDED_RETRY 0
