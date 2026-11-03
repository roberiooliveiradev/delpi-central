# DÉLIA M1 — Contract Freeze & Baseline (Pydantic AI Unified Runtime)

M0 verdict: ACCEPT_WITH_RESIDUAL. Direção aprovada: runtime único de IA em
Pydantic AI; plano CRI-semantic `33bed6a3` subsumido como unidade da migração.

## Contratos congelados por stage (framework-independent)

| Stage | Contrato atual | Invariantes | Destino M2 |
|---|---|---|---|
| admission | `model_propose` com `INTERACTION_ADMISSION_INSTRUCTION_ID` → `(interaction_class\|None, owner_required:bool)`; deadline/budget guard | model output ≠ FACT; incerteza → clarificação | Pydantic AI agent |
| capability selection | `select_group`/`select_group_attempt`: model propose `capability_selection` → `(group\|None)` sobre `allowed_groups` | model propõe, catálogo valida; sem candidato → fallback | Pydantic AI agent |
| target selection | `select_target`: `capability_target_selection` → `(capability\|None)` | mesmo gate | Pydantic AI agent |
| arg generation | `pydantic_arggen` (JÁ Pydantic AI) → typed args validados contra JSON Schema do MCP | códigos como strings; validação final; nunca autoriza | KEEP/EXTEND (runtime canônico) |
| discovery→execute | owner contract `candidate_token` chain (orchestration:288-298) | provider-owned; 1 retry max | KEEP (contrato externo) |
| continuation/recovery | subobjective tracker + fanout + resume (gates S4–S6) | bounded; dedup; deadline | EXTEND no runtime |
| evidence/outcome | `EvidenceFacts` → `OutcomeVerdict` (determinístico) | **nunca** Pydantic AI | KEEP |
| CRI compose | `compose_cri_response` + vocab v7 + renderer | semantic lead × shape × verdict; metadata isolation | EXTEND (semantic stage via runtime) |
| sequenciamento | Engine A (gates) + Engine B (`langgraph_engine`) | **planners concorrentes hoje** | REPLACE — gates únicos + Pydantic AI internals |

## Invariantes de segurança (freeze)
identity → Core AuthZ → Domain authority → capability → Policy/Decision →
confirmação → idempotência → auditoria → execução → postcondition.
`model proposal != authorization`; `technical success != business outcome`.

## Baseline de comportamento (suítes existentes como caracterização)
- `test_unified_evidence_presentation.py` (42) — renderer fidelity
- `test_cri_unified_presentation.py` (21) — leads/estrutura/metadata isolation
- `test_cri_e3_conversational_presentation.py` (67) — pipeline completo
- `test_c3_*` — admission/selection/contracts
Bugs conhecidos NÃO-contrato: api-delpi timeout→empty (owner externo).
Métricas reais de baseline: model=qwen3:4b-instruct-2507-q4_K_M; ~7 calls/turn
operacional; tokens ~11k in/200 out (turn estrutura). LATENCY ~15-30s/turn (Ollama).

## Mapa de remoção (M5, nada removido em M1)
`langgraph_engine.py` → REPLACE (consumidor: `DELIA_ORCHESTRATION_ENGINE=langgraph`);
`_propose` hand-rolled model calls → REPLACE por Pydantic AI agents;
subobjective machinery → MOVE p/ runtime; demais: KEEP/EXTEND acima.

## Gaps abertos
- Baseline eval dataset formal (holdout) — a definir em M2.
- Telemetria por-stage (tokens/stage) — instrumentação existente parcial.
