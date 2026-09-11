# Desacoplamento de JSONs + inteligência LLM/OpenAPI — Minha DELPI AI

**Status atual:** **CONCLUÍDO / ARCHIVED** — Onda J `VERIFY_FINAL=PASS`  
**Plano:** [`planos/11-corrective-cutover-generalization-cleanup.md`](./planos/11-corrective-cutover-generalization-cleanup.md)  
**Candidate final:** `782a49721319571f0fe4733d59b8a5cc65ac4c04`  
**Evidência:** [`evidence/e11-s9-final-candidate.md`](./evidence/e11-s9-final-candidate.md) · [`evidence/e11-s10-residual-scan-verify-final.md`](./evidence/e11-s10-residual-scan-verify-final.md)

```text
FINAL_RESULT = PASS
VERIFY_FINAL = PASS
SEMANTIC_* full-tree = 0
```

> Ondas A–I permanecem históricas. O aceite vigente é o candidate da Onda J acima.

## Princípio da iniciativa

```text
catálogo técnico duplicado
→ OpenAPI + Action Catalog

NLU/semântica endpoint-specific
→ semantic understanding + retrieval + structured planner

argument binding
→ semantic delta + OpenAPI schema + validator

multi-turn
→ structured conversation state

policy / business rule / safety
→ determinístico

copy / UX / prompt
→ conteúdo configurável

presentation
→ responseSchema + payload + semantic metadata

contextual prose/recommendations
→ grounded synthesis (static = LEGACY_FALLBACK com exit criteria)
```

## Invariante

```text
NENHUM MAPA LATERAL OU SUBSTITUTO SEMÂNTICO DEVE SER AUTHORITY.
```

`path` / `method` / `operationId` no Action Catalog = metadata técnica legítima.  
Proibido: usá-los como heurística hardcoded de semântica no core genérico.

## Documentos

| Documento | Finalidade |
|---|---|
| [`roadmap.md`](./roadmap.md) | Estado macro + DoD |
| [`planos/11-corrective-cutover-generalization-cleanup.md`](./planos/11-corrective-cutover-generalization-cleanup.md) | Plano Onda J (fechado) |
| [`evidence/execution-ledger.md`](./evidence/execution-ledger.md) | Ledger de execução |
| [`ARCHIVED.md`](./ARCHIVED.md) | Histórico A–I + ponte para J |
| [`prompt-cursor-execucao-corretiva.md`](./prompt-cursor-execucao-corretiva.md) | Prompt de execução (histórico desta onda) |

## Onda J — etapas

| Etapa | Resultado |
|---|---|
| E11.S0–S1 | Rebaseline + gate SEMANTIC_* |
| E11.S2–S4 | domain / schema bind / continuity facets |
| E11.S5–S6 | operationIds observer; pathTokens DELETE |
| E11.S7–S8 | capability contract; smoke creds |
| E11.S9 | candidate R1–R11 fresco PASS |
| E11.S10 | residual scan + VERIFY_FINAL |

## Pós-programa (não bloqueia)

- DELETE `operationIds` observer arrays quando coverage CI migrar;
- DELETE `recommendationQueries` após exit criteria;
- Migrar FS de lint/generator domain → infrastructure (backlog CA).
