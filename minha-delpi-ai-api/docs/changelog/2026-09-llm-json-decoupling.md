# Set/2026 — Desacoplamento JSON + generalização LLM/OpenAPI

**Roadmap:** [llm-json-decoupling](../roadmap/llm-json-decoupling/README.md)  
**Ledger:** [execution-ledger.md](../roadmap/llm-json-decoupling/evidence/execution-ledger.md)  
**Estado vigente:** **CONCLUÍDO / ARCHIVED — Onda J**  
**Plano:** [plano 11](../roadmap/llm-json-decoupling/planos/11-corrective-cutover-generalization-cleanup.md)  
**FINAL_CANDIDATE_GIT_SHA:** `782a49721319571f0fe4733d59b8a5cc65ac4c04`  
**VERIFY_FINAL / FINAL_RESULT:** PASS

---

## Resumo

As Ondas A–I entregaram avanços OpenAPI-first, Turn Understanding, schema-driven presentation e cleanup parcial. Auditoria pós-onda encontrou substitutos semânticos (JSON→Python) e candidate stale — o que reabriu o programa como **Onda J**.

A Onda J executou cutover → generalização → cleanup → residual scan → candidate fresco R1–R11 e fechou com:

```text
VERIFY_FINAL = PASS
FINAL_RESULT = PASS
SEMANTIC_* full-tree = 0
```

## Correção de política — 2026-09-11

```text
NENHUM MAPA LATERAL OU SUBSTITUTO SEMÂNTICO DEVE SER AUTHORITY.
```

Action Catalog `path`/`method`/`operationId` = metadata técnica legítima. Proibido: usá-los como heurística de semântica no core genérico.

## Drifts corrigidos na Onda J

| Drift | Etapa |
|---|---|
| path→domain Python | E11.S2 |
| endpoint→parameterStrategy | E11.S3 |
| continuity path-tail | E11.S4 |
| registry operationIds authority | E11.S5 |
| NLU pathTokens/pathMarkers laterais | E11.S6 |
| recs estático + capability fake | E11.S7 |
| smoke credential defaults | E11.S8 |
| candidate fresco R1–R11 | E11.S9 |
| residual scan + docs | E11.S10 |

## Ondas

| Onda | Entrega | Estado vigente |
|------|---------|----------------|
| A–H | Inventário → evals/cutover | histórico |
| I | Zero mapa lateral (JSON) | histórico; aceite invalidado por substitutos |
| J | Correção + candidate final | **CONCLUÍDO / PASS** |

## Residuais pós-programa (não bloqueiam)

- observer `operationIds` arrays (DELETE quando CI facets 100%);
- `recommendationQueries` LEGACY_FALLBACK até exit criteria;
- vocabulary `_TOKEN_RULES` facet/kind;
- backlog CA: FS lint/generator em domain.

## Evidências

- Candidate: [`e11-s9-final-candidate.md`](../roadmap/llm-json-decoupling/evidence/e11-s9-final-candidate.md)
- Fechamento: [`e11-s10-residual-scan-verify-final.md`](../roadmap/llm-json-decoupling/evidence/e11-s10-residual-scan-verify-final.md)
- Histórico E1–E10 preservado em `evidence/` (baseline/rastreabilidade).
