# 331 — C3/T2 Transversal Completeness & Finalization Path Closure

**Data:** 2026-11-13
**TASK_ID:** `DELIA-C3-T2-TRANSVERSAL-COMPLETENESS-AND-FINALIZATION-PATH-CLOSURE-01`
**BASE:** `2520193653` (origin/main; Docs 327–330)
**DECISÃO COORDENAÇÃO:** REWORK — completude desconhecida + cobertura transversal

## 1. Causa-raiz — completude desconhecida

No Doc 330, `delivery="enumeration"` demovia apenas quando a incompletude
era **provada** (`total>delivered`, `is_complete:false`, `truncated:true`).
Uma coleção **sem marcadores** (`items:[N]` sem `total`/`is_complete`) ficava
SATISFIED — violando `UNKNOWN_COMPLETENESS != PROVEN_COMPLETE` e
`NO_EVIDENCE_OF_INCOMPLETENESS != EVIDENCE_OF_COMPLETENESS`.

**Correção:** `_attempt_collection_proven_complete` — prova positiva:
flags de incompletude primeiro (contraditórias vencem), depois
`delivered >= total` (total owner-declared), depois marcador explícito
`is_complete:true` sem truncamento. Sem prova → INCONCLUSIVE. Evidência
sem coleção (record) nunca demonstra enumeração. Ordem corrigida após
regressão transitória: flags antes de totals (total:1/items:1 +
is_complete:false → INCONCLUSIVE, não SATISFIED).

## 2. WS-1 — Inventário de caminhos (grafo real)

| PATH_ID | ENTRYPOINT | CALL_CHAIN | OBLIGATION_EVALUATOR | COMPLETENESS_GATE | BYPASS_POSSIBLE |
|---|---|---|---|---|---|
| P1 | `pydantic_ai_investigation` Agent run | tool calls → `deps.collected` → `_finalize_semantic_investigation` → `_finalize_agent_collected_attempts` / `_apply_declared_answer` | `_evaluate_material_obligations` (8 call sites, `delivery` threaded) | `_attempt_demonstrates_anchored` + `_joint_collection_coverage` | **NO** — funil único; `plan=None` → `coverage_unknown`; `declared_answer` é proposta (G1: `declared_status_overridden`) |
| P2 | `handle_interactive_turn` (C3 determinístico) | `execute` → `_capability_orchestration.attempt` → `_grounded_result`/`_source_terminal_result`/`_honest_terminal_result`/`_write_lifecycle_result` | **n/a** — não declara obrigações tipadas (sem `declare_investigation_goal`); gates equivalentes via `investigation_partial_coverage`/`investigation_incomplete_coverage` error codes (linhas 641/1036) | gate equivalente documentado | **NO** — não pode afirmar satisfação de obrigação (não as possui); write lifecycle via `project_write_outcome` |
| P3 | composition (`compose_verified_observations`) | tool → `deps.composed_attempt` → finalize avaliação | mesma `_evaluate_material_obligations` (call site composed) | idem | **NO** — composição passa pelo mesmo veredito |
| P4 | clarification | `request_user_clarification` → `clarification_question` → finalize | preserva evidência parcial; não promove status | — | **NO** — clarificação não é terminal de cobertura |
| P5 | HTTP/streaming (`interaction_routes`) | apresenta `terminal` do orchestrator | consumidor do Outcome autoritativo | — | **NO** — camada renderiza, não promove |

**Produtores de estados finais:** `OBLIGATION_*` só em
`_evaluate_material_obligations`; status de resposta só em finalize +
`_apply_declared_answer` (override determinístico); `WriteOutcomeStatus`
só via `project_write_outcome`; `GroundingStatus` = provenance, não
completude. `SUCCESS`/`is_complete` de transporte nunca promovem a
veredito empresarial isoladamente.

`ARE_ALL_RELEVANT_COMPLETENESS_PATHS_GOVERNED`: **YES** — funil único
para obrigações (P1/P3/P4/P5 convergem a `_evaluate_material_obligations`);
P2 não produz obrigações e seus terminais cobertura-relevantes usam
error-code gates equivalentes canônicos.

## 3. WS-4 — Paginação

`_joint_collection_coverage(obligation, business)`: união de tentativas
ancoradas no mesmo âncora+identidade+total declarado; itens deduplicados
por fingerprint canônico (JSON sort-keys); união deve igualar o total
declarado — união > total prova conjuntos distintos → não demonstra;
gap → não demonstra; duplicidade → não demonstra. Aritmética bruta de
páginas nunca é aceita.

## 4. Implementação bounded

| Mudança | Onde |
|---|---|
| `_attempt_collection_proven_complete` — prova positiva (flags → total ≤ delivered → is_complete:true) | `semantic_capability_support.py` |
| enumeration branch usa prova positiva (parcial E desconhecido → INCONCLUSIVE; sem coleção → INCONCLUSIVE) | idem |
| `_joint_collection_coverage` — união multipágina com identidade/total/continuidade | idem |
| f03 reescrito (unmarked → INCONCLUSIVE); +8 testes TC-04..TC-08, non-collection | `test_int2_delivery_completeness_contract.py` |

Sem `CompletenessEngine`, registry ou catálogo — mesma função avaliadora,
mesmo contrato de estados.

## 5. Testes

- **RED:** f03 + novos TC falharam no SHA anterior (unmarked→SATISFIED,
  multipage→cada página INCONCLUSIVE isolada).
- **GREEN:** 18/18 suite completeness; regressão completa `pytest tests/ -q`
  → suíte inteira verde, 0 falhas (incl. RC5, INT-2, INT-1, aggregation,
  plan-absent, declared-override, compose, clarify).
- 1 regressão transitória interna corrigida (precedência flags>totals).

## 6. Avaliação real

`MODEL_ID qwen/qwen3-14b`, `openrouter_qwen`, pydantic_ai, toolset 15,
UNFORCED, `PROD_CONTAINER_UNTOUCHED=YES`, corpus INT2 (12 cenários).

| Cen. | Delivery | Âncora | Veredito | Gate |
|---|---|---|---|---|
| A | — | teo.read→process.search→process (rejeições, lock-fora) | — | PASS-safety |
| A2 | enumeration | teo.read→**process+search** | **2× SATISFIED** | PASS |
| B | aggregation | teo.read→**search** | **SATISFIED** (total 109) | PASS |
| C | explanation | teo.read→read (surface token) | INCONCLUSIVE honesto | PASS |
| C2 | record_detail | get_product_structure | **SATISFIED** | PASS |
| D | record_detail | get_product_structure | **SATISFIED** (ausência autoritativa+identidade) | PASS |
| D2 | enumeration | transportadora (unowned) | UNSATISFIED honesto | PASS |
| E | — | needs_clarification | — | PASS |
| E2 | aggregation | teo.analyze→**processes** | **SATISFIED** (vocab metamórfico) | PASS |
| G | — | 5× dotted/variantes (não convergiu) | insufficient | PASS-safety |
| G2 | aggregation | get_active_process_count | sem evidência bound → insufficient | PASS |
| F | — | zero declaração, zero write | no_evidence/insufficient | **PASS segurança** |

`FALSE_SATISFIED=0`; `FALSE_COMPLETE=0`; agregação real demonstrada por
âncoras distintas (`search`, `processes`) — generalização de vocabulário;
enumeração completa demonstrada (A2); nenhum caminho promoveu status
indevido; auth/budget/clarification honestos.

## 7. Resultado

`IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW` — **não aceite**;
`INT2_ACCEPTED=NO`; `PRODUCTION_DEPLOY/PHASE_ADVANCEMENT/INT3/T3=NOT_AUTHORIZED`.
NEXT=`COORDINATION_INT2_TRANSVERSAL_COMPLETENESS_INDEPENDENT_REVIEW`.
