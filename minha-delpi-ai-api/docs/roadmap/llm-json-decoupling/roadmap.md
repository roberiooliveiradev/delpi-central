# Roadmap — desacoplamento de JSONs e generalização LLM/OpenAPI

**Status:** **CONCLUÍDO / ARCHIVED** — Onda J  
**Plano:** [`planos/11-corrective-cutover-generalization-cleanup.md`](./planos/11-corrective-cutover-generalization-cleanup.md)  
**FINAL_CANDIDATE_GIT_SHA:** `782a49721319571f0fe4733d59b8a5cc65ac4c04`  
**VERIFY_FINAL:** PASS · **FINAL_RESULT:** PASS

## 1. Resultado esperado (atingido)

```text
TARGET
mensagem + contexto estruturado
→ semantic understanding
→ goals/subtasks/entities/references
→ allowed Action Catalog
→ semantic retrieval
→ structured planner restricted to candidates
→ OpenAPI schema binder + validator
→ RBAC/policy/confirmation
→ generic execution
→ responseSchema + semantic metadata
→ schema-driven presentation
→ grounded synthesis + contextual recommendations
```

## 2. Histórico × vigente

Ondas A–I = histórico. Aceite vigente = candidate Onda J (`e11-s9` + `e11-s10`).

Drifts que motivaram a reabertura foram corrigidos:

| Drift | Correção |
|---|---|
| path→domain Python | E11.S2 |
| path→parameterStrategy | E11.S3 |
| path-tail continuity | E11.S4 |
| registry operationIds authority | E11.S5 |
| NLU path-teaching / pathTokens | E11.S6 |
| recs estático + capability fake | E11.S7 |
| smoke cred defaults | E11.S8 |
| candidate fresco R1–R11 | E11.S9 |
| residual scan | E11.S10 |

## 3. Definition of Done

```text
CUTOVER_RESULT = PASS
GENERALIZATION_RESULT = PASS
CLEANUP_RESULT = PASS
UNKNOWN_EXTERNAL_API = PASS_ON_FINAL_CANDIDATE
METAMORPHIC_RENAME = PASS_ON_FINAL_CANDIDATE
ARGUMENT_SCHEMA_AUTHORITY = PASS
MULTI_TURN_STRUCTURED_STATE = PASS
SEMANTIC_AUTHORITY_SINGLE_OWNER = PASS
CONTEXTUAL_RECOMMENDATIONS = PASS
CAPABILITY_SECURITY_METADATA = PASS
CLEAN_ARCHITECTURE = PASS
SECURITY_HYGIENE = PASS
SEND_STREAM_SIMULATE_UI = PASS
PERSIST_RELOAD_F5 = PASS
R1_R11_REQUIRED_DIMENSIONS = PASS
RESIDUAL_SCAN = PASS
DOCS_MATCH_FINAL_HEAD = PASS
COMPLETE_GATE = PASS
VERIFY_FINAL = PASS
FINAL_RESULT = PASS
```

Evidências: [`evidence/e11-s9-final-candidate.md`](./evidence/e11-s9-final-candidate.md), [`evidence/e11-s10-residual-scan-verify-final.md`](./evidence/e11-s10-residual-scan-verify-final.md).

## 4. Ordem executada (Onda J)

```text
E11.S0 → S1 → S2 → S3 → S4 → S5 → S6 → S7 → S8 → S9 → S10
```

## 5. Residuais pós-programa (não bloqueiam)

- observer `operationIds` arrays;
- `recommendationQueries` LEGACY_FALLBACK;
- vocabulary `_TOKEN_RULES` facet/kind;
- backlog CA: FS lint/generator em domain.
