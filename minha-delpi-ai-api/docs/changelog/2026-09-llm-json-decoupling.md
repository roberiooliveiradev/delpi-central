# Set/2026 — Desacoplamento JSON + generalização LLM/OpenAPI

**Roadmap:** [llm-json-decoupling](../roadmap/llm-json-decoupling/README.md)  
**Ledger:** [execution-ledger.md](../roadmap/llm-json-decoupling/evidence/execution-ledger.md)  
**Estado vigente:** **REABERTO — Onda J**  
**Plano:** [plano 11](../roadmap/llm-json-decoupling/planos/11-corrective-cutover-generalization-cleanup.md)  
**Candidate anteriormente declarado final:** `782a49721319571f0fe4733d59b8a5cc65ac4c04` — histórico invalidado como release evidence  
**VERIFY_FINAL / FINAL_RESULT vigente:** `FAIL / VERIFY_FINAL_FAILED`

---

## Resumo

As Ondas A–I entregaram avanços OpenAPI-first, Turn Understanding, schema-driven presentation e cleanup parcial. Uma primeira auditoria reabriu o programa como Onda J; a Onda J corrigiu vários drifts reais e chegou a ser registrada como concluída.

Uma nova auditoria pós-fechamento mostrou, porém, que o `COMPLETE_GATE` e o `VERIFY_FINAL` foram aplicados de forma permissiva em pontos materiais. O fechamento anterior é preservado como histórico, mas não representa mais o estado vigente.

```text
HISTORICAL_FINAL_RESULT = PASS
CURRENT_FINAL_RESULT = VERIFY_FINAL_FAILED
```

Auditoria: [`e11-post-close-audit-2026-09-11.md`](../roadmap/llm-json-decoupling/evidence/e11-post-close-audit-2026-09-11.md).

## Correções válidas preservadas da Onda J

- `_DOMAIN_RULES` path-based antiga deixou de ser authority principal;
- argument binding passou a ser schema-first no caminho principal;
- continuidade path-tail foi reduzida em favor de estado/facets;
- OpenAPI-first permaneceu com cutover ativo em caminhos relevantes;
- capability metadata passou a derivar de method+sensitivity;
- defaults versionados de credenciais de smoke foram removidos.

A reabertura não implica rollback dessas melhorias.

## Drifts pós-fechamento confirmados

| ID | Drift | Estado |
|---|---|---|
| A11-01 | evaluator R8 não compara Normal com `<= 5 s`; candidate teve P50≈41,5 s e P95≈50,7 s | **FAIL** |
| A11-02 | `requiredDimensions` do corpus divergem da matriz canônica | **FAIL** |
| A11-03 | manifest offline contradiz o runner que o gera | **FAIL** |
| A11-04 | unknown external API não prova executor HTTP + presentation + R9 | **INCONCLUSIVE** |
| A11-05 | gate live “metamorphic” mede sinônimo, não provider/path/operationId rename | **INCONCLUSIVE** |
| A11-06 | Architecture Enforcement aceita `cleanupMeta` como self-attestation para pular scan | **FAIL** |
| A11-07 | resolver ainda usa path/operationId em semantic affinity | **FAIL** |
| A11-08 | `operational_route_registry` ainda contém catálogo técnico material | **FAIL** |
| A11-09 | `api_route_domains.json` ainda duplica dados técnicos/strategy/path-prefix | **FAIL** |
| A11-10 | semantic single owner não está provado | **PARTIAL/FAIL** |
| A11-11 | `recommendationQueries` permanece `LEGACY_FALLBACK` | **FAIL** |
| A11-12 | filesystem/generation permanece em domain | **PARTIAL/FAIL** |

## Onda J — estado revisado

| Subetapa | Estado vigente |
|---|---|
| E11.S0 | PASS histórico |
| E11.S1 | REABERTO — gate precisa ser independente |
| E11.S2 | PASS com verify final pendente |
| E11.S3 | PASS/PARTIAL |
| E11.S4 | PASS/PARTIAL |
| E11.S5 | REABERTO — registry/path affinity |
| E11.S6 | REABERTO — semantic ownership |
| E11.S7 capability | PASS |
| E11.S7 recommendations | REABERTO — LEGACY_FALLBACK |
| E11.S8 credentials | PASS |
| E11.S8 Clean Architecture | REABERTO — residual |
| E11.S9 | INVALIDADO como candidate final |
| E11.S10 | INVALIDADO como verify-final |

## Próxima sequência obrigatória

```text
J-R1  R8 threshold canônico
J-R2  requiredDimensions canônicas
J-R3  evidence reproduzível
J-R4  unknown external full chain
J-R5  metamorphic rename verdadeiro
J-R6  Architecture Enforcement independente
J-R7  zero path semantic affinity
J-R8  cleanup registry/content técnico              ✅
J-R9  semantic single owner                         ✅
J-R10 recommendations sem LEGACY_FALLBACK material  ✅
J-R11 Clean Architecture                            ← próxima
J-R12 novo final candidate R1–R11 + residual + COMPLETE_GATE
```

## Regra de novo fechamento

Não registrar novo `FINAL_RESULT=PASS` se existir qualquer item material em `FAIL`, `PARTIAL`, `INCONCLUSIVE`, `LEGACY_FALLBACK`, evidence stale/não reproduzível ou gate cujo resultado dependa de autodeclaração do próprio artefato auditado.

## Evidências

- Auditoria vigente: [`e11-post-close-audit-2026-09-11.md`](../roadmap/llm-json-decoupling/evidence/e11-post-close-audit-2026-09-11.md)
- Candidate histórico: [`e11-s9-final-candidate.md`](../roadmap/llm-json-decoupling/evidence/e11-s9-final-candidate.md)
- Fechamento histórico: [`e11-s10-residual-scan-verify-final.md`](../roadmap/llm-json-decoupling/evidence/e11-s10-residual-scan-verify-final.md)
