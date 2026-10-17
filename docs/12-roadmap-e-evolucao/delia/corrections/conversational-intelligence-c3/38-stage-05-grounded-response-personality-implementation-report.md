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

Registrado no ledger §6.219 (MESSAGE-only multi-turn; zero ACT).

## 6. Limitações / resíduos

- Ordenação “mais recente” continua dependente da seleção do modelo sobre campos owner (sem hardcode de keywords).
- Preferências temporárias de sessão ainda sem store dedicado (presentation hint apenas).
- R-S04-01 live clarify NOT_EXERCISED preservado para Stage 06.
- `STAGE_05_ACCEPTED=NO`; `C3_EXECUTED=NO`; `C4_AUTHORIZED=NO`.

## 7. NEXT

```text
NEXT=INDEPENDENT_STAGE05_ARCHITECTURE_REVIEW
```
