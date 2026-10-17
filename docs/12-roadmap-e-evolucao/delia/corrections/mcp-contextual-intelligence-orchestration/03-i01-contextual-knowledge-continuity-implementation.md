# I01 — Implementação da continuidade contextual de conhecimento especializado

**DATA:** 2026-10-17
**TASK_ID:** `DELIA-C3-MCP-CONTEXTUAL-KNOWLEDGE-CONTINUITY-I01-IMPLEMENTATION-01`
**TRACK:** `DELIA-C3-MCP-CONTEXTUAL-INTELLIGENCE-AND-ORCHESTRATOR-QUALITY-01`
**BASE_HEAD:** `1ced87f1db2aea809215be3ecbe5b07cfac31767`
**CODE_COMMIT:** `118a1814e57a57cec2fb2c57848476268efc4af8`
**LIVE_EVALUATED_SHA:** `118a1814e57a57cec2fb2c57848476268efc4af8`
**MODEL:** `moonshotai/kimi-k3`
**I01_ACCEPTED:** `NO` (recomendação para revisão arquitetural independente)

## 1. CP/RQ e autoridades

Reancorados no HEAD: plano 16, standalone 50, padrões 49, estado 21, testes 20, rastreabilidade 25, I00/I01 proposal, relatório 44, ledger §§6.235–6.238.

**CP/RQ materiais (não inventados):**

| ID | Papel nesta I01 |
|---|---|
| CP-094 | Classes epistêmicas — prior ≠ FACT novo |
| CP-055 | Injection safety — histórico não muta AuthZ/Policy |
| CP-263 / CP-264 | MCP trust / read-only delegation |
| CP-270 | Personalização/contexto não substitui fato live |
| CP-130 / CP-134 | Clean Architecture + Abstraction Gate (EXTEND, sem novo engine) |

Contrato `ConversationContextTurn` **não** foi alterado — suficiente para a correção.

## 2. Reuse

```text
EXISTING_EQUIVALENT=YES
REUSE_DECISION=EXTEND
```

Estendidos: `GOAL_INSTRUCTION` / `_understand_goal`, `_prior_excerpt_records`, gate em `_attempt` + `_prior_transform_probe_eligible`, `_prior_continuation_attempt` (inalterado no núcleo de síntese).
**Não criados:** planner, memory engine, registry MCP, persistência, contrato público novo, branch por especialista.

## 3. Causa raiz (K2)

```text
ROOT_CAUSE=EVIDENCED
```

Cadeia: follow-up transformável → modelo marcava `prior_evidence_sufficient=false` → orquestrador ignorava continuidade → reconsulta owner + replay/truncamento → latência ~30s.
Correção: instrução de goal mais clara para extração de evidência anterior + probe provider-neutral quando cues de continuidade existem e conteúdo OBSERVATION é transformável; insuficiência cai no fluxo live.

## 4. Testes

| Suite | Resultado |
|---|---|
| RED class (fixture `specialist_alpha`, `prior_sufficient=false`) | reproduzido como GREEN pós-fix (`test_k2_continuity_probe_…`) |
| GREEN + regressões I01 (14 testes) | PASS |
| Stage05 / provider-neutral relacionados | PASS |
| `delia-api` full suite | PASS |

Segurança coberta: histórico malicioso ≠ ACT; write ≠ prior-only ACT; fato “agora” não usa só prior; rename provider/capability; HTTP não-MCP; budget 30s.

## 5. Live K1/K2 (uma conversa, MESSAGE-only)

```text
K1_SELECTED_SPECIALIST=mcp:teo
K1_GUIDANCE_RECEIVED=YES (get_methodology_guide; result_truncated; 20725ms)
K1_VERDICT=PASS_WITH_LIMITATION

K2_PRIOR_EVIDENCE_SUFFICIENT=yes (log goal_understanding)
K2_PRIOR_CONTINUATION_USED=YES (decision=transformed; prior_turn_evidence_only)
K2_OWNER_REINVOKED=NO
K2_LITERAL_REPLAY=NO
K2_GROUNDING=NON_GROUNDED
K2_LIMITATIONS=prior_turn_evidence_only
K2_LATENCY_MS=13849
K2_ANSWER_RELEVANT=PARTIAL
K2_USER_GOAL_ACHIEVED=PARTIAL
K2_VERDICT=PASS_WITH_LIMITATION
```

**Nota factual:** a continuidade estrutural passou (sem reconsulta, sem replay literal, abaixo de 30s, epistemics corretos). A relevância do texto K2 é parcial porque o conteúdo K1 chegou truncado (metadados/invariantes do guia) e a seleção de excerpts refletiu o que estava disponível — residual de síntese/truncamento alinhado à I02, não regressão do path de continuidade.

```text
UNAUTHORIZED_MATERIAL_ACT_COUNT=0
GLOBAL_TURN_BUDGET_SECONDS=30
MAX_OBSERVED_TURN_LATENCY_MS=20725
MODEL_AUTHORED_FACTUAL_PROSE=NONE
```

## 6. Arquivos

- `delia-api/app/application/capability_provision/orchestration.py`
- `delia-api/tests/test_i01_contextual_knowledge_continuity.py`

## 7. Residuais / próxima etapa

- I02: síntese fundamentada + headroom sob truncamento (`result_truncated` / skip_budget).
- Aceite independente desta I01 (não auto-aceitar).
- Não avançar C3/C4/C5.

```text
I01_RECOMMENDATION=ACCEPT_WITH_RESIDUAL
I01_ACCEPTED=NO
SOURCE_CODE_SCOPE=I01_ONLY
I02_IMPLEMENTED=NO
ORCHESTRATOR_STRUCTURAL_REFACTOR=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
NEXT=INDEPENDENT_I01_ARCHITECTURE_ACCEPTANCE_REVIEW
```
