# C3/T2 — Qwen 14B multiturn continuity evidence index

TASK_ID: `DELIA-C3-T2-POST-E2-QWEN14B-MULTITURN-CONTINUITY-AND-CONTEXT-EFFICIENCY-01`

## Provenance

```yaml
model: qwen/qwen3-14b
provider: OpenRouter (openrouter.ai) — isolated eval egress, DELIA_EVAL_EGRESS_AUTHORIZED=1
runtime_profile: openrouter_qwen
config_fingerprint: recorded per-run inside each artifact summary JSON
reanchored_head_at_task_start: f254a0961c63fb64caf0258705c70fe9775fc5d0
worktree_head_range_during_runs: f254a0961c..d0e6a511f8
  # concurrent foreign commits only; none touched delia-api/ or api-delpi/
  # files in this task's scope — runtime code for the evaluated paths is
  # therefore identical across the range
code_baselines:
  e2_native_pydantic_ai: d9f9abec4b (ancestor)
  davi_argument_feedback_echo: 688cfb3832c754bab9651885676e5ea306aefed6
identity: delegated subject token (Keycloak realm delpi), READ-only
environment: DEV containers, live-mounted worktree
```

## Run index (single scenario, executed 5× for boundary diagnosis)

| Artifact | evaluation_id (trace dir `or-qwen14b-*`) | Turn 1 (C2 structure) | Turn 2 (C3 stock continuity) | model_calls | input tokens | output tokens |
|---|---|---|---|---|---|---|
| `run1_initial.txt` | `14b22babe20d` | GROUNDED 75.8s | NON_GROUNDED — investigation leg interrupted | 4 | 52.139 | 2.983 |
| `run2_typed_failure.txt` | `a805424591f4` | GROUNDED 91.1s | NON_GROUNDED — honest clarification + `tool_calls_limit_reached` | 4 | 64.781 | 3.271 |
| `run3_degraded.txt` | `5b7384b853fb` | NON_GROUNDED — `UnexpectedModelBehavior` | NON_GROUNDED — chained from honest-limitation prior | 4 | 11.152 | 1.164 |
| `run4_typed_failure.txt` | `266fafa4e001` | GROUNDED 57.1s | NON_GROUNDED — `UnexpectedModelBehavior` (ModelRetry cause, output_retries_exhausted, tool_calls=7) | 4 | 60.937 | 2.509 |
| `run5_stock_continuity_engaged.txt` | `8d1b3feb03ec` | GROUNDED 61.4s | NON_GROUNDED — engaged loop; referent 10020003 resolved; invented capability `get_material_stock` → `CAPABILITY_NOT_ALLOWED` | 4 | 128.885 | 5.610 |

Total: 20 model calls, 317.894 input + 15.537 output tokens. Cost USD not
reported by the provider in artifacts.

## Key findings

- Continuity mechanically proven (run 5): live prior carried the published
  turn-1 answer; model resolved `10020003` and declared an accepted typed
  goal `estoque da matéria-prima 10020003`.
- First divergent boundary: model capability-name selection — invoked
  `get_material_stock` (nonexistent) instead of eligible `get_product_stock`
  (allowlist, executable=True). Governed path failed closed correctly;
  no stock value was ever invented.
- Context composition per provider request (B3 boundary, measured):
  15 tools — descriptions 12.787 chars + schemas 11.292 chars —
  plus agent instructions 10.851 chars (~35k chars static, resent every call);
  remainder is accumulated message history / tool results (estimate class).
