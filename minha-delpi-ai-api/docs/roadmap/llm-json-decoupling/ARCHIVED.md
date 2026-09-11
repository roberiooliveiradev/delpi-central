# Histórico — Ondas A–J

**Estado atual do programa:** **REABERTO — Onda J**  
**Motivo:** auditoria pós-fechamento invalidou `VERIFY_FINAL=PASS` do candidate `782a49721319571f0fe4733d59b8a5cc65ac4c04`.  
**Plano ativo:** [`planos/11-corrective-cutover-generalization-cleanup.md`](./planos/11-corrective-cutover-generalization-cleanup.md)  
**Auditoria vigente:** [`evidence/e11-post-close-audit-2026-09-11.md`](./evidence/e11-post-close-audit-2026-09-11.md)

> Este arquivo registra histórico de fechamentos. Ele não deve ser usado como fonte de estado vigente enquanto o programa estiver reaberto.

## Ondas A–I

Históricas. Produziram avanços e evidências úteis, mas drifts pós-auditoria invalidaram o uso de seus PASS como release do estado posterior.

## Primeiro fechamento da Onda J — histórico invalidado

A Onda J chegou a ser registrada como concluída com:

```text
FINAL_CANDIDATE_GIT_SHA = 782a49721319571f0fe4733d59b8a5cc65ac4c04
VERIFY_FINAL = PASS
FINAL_RESULT = PASS
```

Esse fechamento permanece preservado para rastreabilidade em:

- [`evidence/e11-s9-final-candidate.md`](./evidence/e11-s9-final-candidate.md)
- [`evidence/e11-s10-residual-scan-verify-final.md`](./evidence/e11-s10-residual-scan-verify-final.md)

A auditoria posterior encontrou bloqueios materiais em R8, requiredDimensions, reprodutibilidade de evidence, unknown-provider full chain, metamorphic rename, Architecture Enforcement, path semantic affinity, registry técnico, semantic ownership, recommendations e Clean Architecture.

Consequentemente:

```text
HISTORICAL_FINAL_RESULT = PASS
CURRENT_FINAL_RESULT = VERIFY_FINAL_FAILED
```

## Estado vigente

O Programa 11 voltou a ser o plano ativo e só poderá ser arquivado novamente após novo candidate final cumprir integralmente:

```text
R8_THRESHOLD_CANONICAL
REQUIRED_DIMENSIONS_MATRIX
EVIDENCE_REPRODUCIBLE
UNKNOWN_EXTERNAL_FULL_CHAIN
METAMORPHIC_PROVIDER_PATH_OPERATION_ID_RENAME
ARCHITECTURE_GATE_INDEPENDENT
NO_PATH_SEMANTIC_AFFINITY
TECHNICAL_PARALLEL_REGISTRY cleanup/classification
ASSISTANT_CONTENT_TECHNICAL_DUPLICATION cleanup
SEMANTIC_AUTHORITY_SINGLE_OWNER
CONTEXTUAL_RECOMMENDATIONS
LEGACY_RECOMMENDATION_FALLBACK = 0
CLEAN_ARCHITECTURE
R1_R11_REQUIRED_DIMENSIONS
RESIDUAL_SCAN
COMPLETE_GATE
VERIFY_FINAL
```

Fontes vigentes:

- [`README.md`](./README.md)
- [`roadmap.md`](./roadmap.md)
- [`planos/11-corrective-cutover-generalization-cleanup.md`](./planos/11-corrective-cutover-generalization-cleanup.md)
- [`evidence/e11-post-close-audit-2026-09-11.md`](./evidence/e11-post-close-audit-2026-09-11.md)
- [`evidence/execution-ledger.md`](./evidence/execution-ledger.md)
