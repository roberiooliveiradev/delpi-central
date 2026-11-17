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
