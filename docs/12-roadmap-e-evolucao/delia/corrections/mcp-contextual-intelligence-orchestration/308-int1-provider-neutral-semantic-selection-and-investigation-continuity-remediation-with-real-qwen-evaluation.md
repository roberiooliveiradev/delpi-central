# 308 — INT-1 Provider-Neutral Semantic Selection and Investigation Continuity Remediation with Real Qwen Evaluation

**TASK_ID:** `DELIA-C3-T2-INT1-PROVIDER-NEUTRAL-SEMANTIC-SELECTION-AND-INVESTIGATION-CONTINUITY-REMEDIATION-01`  
**Data:** 2026-11-12  
**EXTERNAL_LLM:** AUTHORIZED — EXECUTED (G1+P1+M1 ×1)  
**PRODUCTION_DEPLOY:** NOT_AUTHORIZED  
**FULL_BATTERY:** NOT_RUN  
**NEW_AGENT / ROUTER / PLANNER:** NO  

---

## 1. Reancoragem

| Item | Value |
|---|---|
| REFERENCE_HEAD (task) | `69acaec20a9…` (revalidar) |
| WORK / BASE during task | `02123348d753…` aligned `origin/main` after concurrent env WIP |
| PHASE_FROM_16 | C3 / T2 — INT-1 BLOCKED (sem avanço de fase) |
| Instruction baseline (histórica) | `generalist-semantic-v2` / fp `7dbc94c5035b0f19` PRESERVED |
| Instruction default (candidata) | `generalist-semantic-v2-1-object-continuity` / fp `4ebd5260b6cf9ba9` |
| Model / profile | `qwen/qwen3-14b` / `openrouter_qwen` |
| Model config fp | `e4a5b706a3b3156b` |
| Pydantic AI | `2.50.0` |
| Isolation | `delpi-delia-eval-int1-or-qwen14b`; `PROD_CONTAINER_UNTOUCHED=YES` |

Baseline preservado: Documento 307 + traces `or-qwen14b-303e1f9f4ed3` / `or-qwen14b-118289112bdf`.

---

## 2. Baseline do Documento 307

| Cenário | R1 first | R2 first | Objetivo (307) |
|---|---|---|---|
| G1 | TÉO | TÉO | SATISFIED após recovery |
| P1 | DAVI | DAVI | SATISFIED |
| M1 | DAVI / TÉO | TÉO | NOT_SATISFIED (continuidade) |

Problema A: seleção inicial semanticamente incompatível (G1 TEO-first).  
Problema B: continuidade investigativa (M1 abandona objetivo / tour inadequado).

---

## 3. Inventário de responsabilidades

```text
USER OBJECTIVE
→ AGENT INSTRUCTIONS (resource JSON)
→ TOOL SELECTION (Qwen via Pydantic AI Agent + CombinedToolset)
→ MCP RESULT (owner)
→ InvestigationDeps + attempt projection (progress / coverage_note / evidence_citable)
→ ModelRetry continuity (NO_PROGRESS + open identifiers, one-shot)
→ FINAL ANSWER (structured output + application finalize)
```

| Mechanism | Role |
|---|---|
| `generalist-semantic-v*` | orientação generalista provider-neutral |
| `InvestigationDeps` | estado de turno (incl. `no_progress_continuity_retry_used`) |
| `_attempt_projection` | progress + uncovered ids + coverage_note |
| `_is_business_evidence_attempt` / `_owner_declares_guidance_only` | citabilidade |
| `MCPToolset` / EnvelopeHint / B3 | contratos vivos (não alterados nesta task) |

---

## 4. Abstraction Gate

| Change | RESPONSIBILITY | OWNER | EXISTING_EQUIVALENT | REUSE_DECISION |
|---|---|---|---|---|
| v2-1 object-continuity instruction | Agent instructions | `investigation_instructions.delpi.json` | YES (v2 lineage) | EXTEND |
| GUIDANCE_NOT_DOMAIN_TRUTH non-citable | Evidence citability | `semantic_capability_support` | YES (`_is_business_evidence_attempt`) | EXTEND |
| NO_PROGRESS continuity note + one-shot ModelRetry | Continuity / recovery context | `pydantic_ai_investigation` | YES (projection + deps) | EXTEND |
| Harness `.env` portal + OpenRouter key resolve | Eval harness only | `run_int1_openrouter_qwen14b_instrumented_eval.sh` | YES | EXTEND |

No SPECIALIST_ROUTER / keyword map / second Agent / mandatory `declare_investigation_goal`.

---

## 5. Diagnóstico de seleção inicial

Causa reafirmada (amostra): **MODEL_TOOL_SELECTION_ERROR** sob atrator lexical de “árvore/componentes/relações” → TÉO `decomposition_tree` / `process`, apesar de contratos B3 íntegros (DAVI `get_product_structure` presente).

Lacuna de instrução (Caso A): v2 não destacava explicitamente *business object match* vs similaridade linguística, nem continuidade pós-NO_PROGRESS evitando catálogos de guidance.

---

## 6. Diagnóstico de continuidade M1 (307 + 308)

Primeira divergência material (307): após NO_PROGRESS, tour guidance/VISTA sem preservar obrigação de evidência operacional.

Nesta task (308 / `or-qwen14b-99c72442b8d9`):

| Cenário | First tool | Continuity notes | Bloqueio dominante |
|---|---|---|---|
| G1 | `teo.read` decomposition_tree | coverage_note emitido; 2ª chamada `davi.read` gps | `AUTHZ_DENIED` (DAVI) + TEO sem `transformometro.access` |
| P1 | `davi.get_context` → `davi.read` gps | notes + DISCOVERY_ONLY | `AUTHZ_DENIED` em reads DAVI |
| M1 | `teo.read` process search | notes presentes; ainda tour TEO/VISTA; gps com arg `product_code` inválido | AUTHZ/validation + seleção residual |

**CONTINUITY_ROOT_CAUSE (implementável):** evidência guidance tratável como progresso + contexto de recuperação fraco após NO_PROGRESS.  
**SELECTION_ROOT_CAUSE:** lacuna generalista object-match (não keyword).  
**OBJECTIVE_SATISFACTION (308):** NOT_SATISFIED nos três — **env/authz do sujeito de eval**, não ausência de B3.

---

## 7. Mecanismos reutilizados

- Instruction resource + fingerprint rollback v2  
- `_is_business_evidence_attempt`  
- `_attempt_projection` / uncovered identifiers  
- `InvestigationDeps`  
- Harness OpenRouter isolado + B3 capture  

---

## 8. Alterações aplicadas

1. Default instruction → `generalist-semantic-v2-1-object-continuity` (object match + continuity + GUIDANCE_NOT_DOMAIN_TRUTH).  
2. `_owner_declares_guidance_only` → guidance não citable.  
3. Coverage note de continuidade em NO_PROGRESS com identifiers abertos; one-shot `ModelRetry` quando aplicável.  
4. Harness: credenciais portal + chave OpenRouter a partir de `infra/.env` (fallback `KIMI_API_KEY` quando `DELIA_LLM_API_KEY` é placeholder local).

---

## 9. RED/GREEN

Targeted:

- `tests/test_int1_semantic_continuity_remediation.py`  
- `tests/test_investigation_instruction_resource.py`  
- adjacentes: intent projection / investigative progress / partial citability  

Resultado: PASS (docker `infra-delia-api`).  
FULL_SUITE=NOT_RUN.

---

## 10. Avaliação real Qwen

| Item | Value |
|---|---|
| EVAL_ID | `or-qwen14b-99c72442b8d9` |
| EXECUTED_SCENARIOS | G1, P1, M1 |
| TOTAL_INVESTIGATIONS | 3 |
| MODEL_REQUESTS (meter) | 2 (P1 llm_runs.count=0 no harness; ver residual) |
| TOOL_CALLS (MCP) | 20 |
| TOKEN_USAGE | UNAVAILABLE (meter 0) |
| COST | UNAVAILABLE |
| LATENCY | ≈163431 ms total (external_usage) |
| INSTRUCTION_EFFECTIVE | v2-1 (length 5319; default fp `4ebd5260b6cf9ba9`) |

---

## 11. Comparação G1/P1/M1 (308)

| | First tool | Recovery signal | Objective |
|---|---|---|---|
| G1 | TEO | tenta DAVI gps | NOT_SATISFIED (AUTHZ) |
| P1 | DAVI context→gps | mantém DAVI + exploratórios | NOT_SATISFIED (AUTHZ) |
| M1 | TEO | notes; args/tour residual | NOT_SATISFIED |

---

## 12. Satisfação dos objetivos

`HTTP_200` / tool success / grounding ≠ SATISFIED.  
Nesta rodada: **nenhum cenário SATISFIED** por falta de evidência owner autoritativa (AUTHZ_DENIED / permissão TEO).  
Não confundir com regressão de seleção P1 (DAVI-first preservado semanticamente).

---

## 13. Generalização

Não comprovada. Sem hardcode de `90260921` / DAVI / TÉO / keywords na instrução v2-1 (testado deterministicamente). Residual: bateria independente futura.

---

## 14. Residuais

| ID | Status |
|---|---|
| INT1-G1-TEO-FIRST-ATTRACTOR | OPEN (ainda observado) |
| INT1-M1-CONTINUITY | PARTIAL_REMEDIATE (notes/guidance) — satisfação ainda bloqueada |
| INT1-EVAL-SUBJECT-AUTHZ | OPEN — sujeito `DEV_PORTAL_*` sem permissões owner suficientes nesta host |
| INT1-EVAL-LLM-KEY-PLACEHOLDER | REMEDIATED_IN_HARNESS — fallback OpenRouter key do mesmo `.env` |
| INT1-TOKEN-METER | UNAVAILABLE |
| INT1-STAGE | BLOCKED |
| INT1-CLOSED | NO |

---

## 15. Próximo passo recomendado

`COORDINATION_INT1_SEMANTIC_CONTINUITY_INDEPENDENT_REVIEW`  
Revalidação live G1/P1/M1 somente após sujeito de eval com autorização owner equivalente ao baseline 307 — sem novo Agent/router.
