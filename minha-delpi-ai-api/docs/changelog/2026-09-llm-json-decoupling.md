# Set/2026 — Desacoplamento JSON + generalização LLM/OpenAPI

**Roadmap:** [llm-json-decoupling](../roadmap/llm-json-decoupling/README.md)  
**Ledger:** [execution-ledger.md](../roadmap/llm-json-decoupling/evidence/execution-ledger.md)  
**Release histórico (Ondas A–H):** `globalReleasePass=true` no candidate avaliado em E9.S8/E9.S15  
**Onda I:** executada, aceite arquitetural posteriormente invalidado por drift  
**Estado vigente:** **REABERTO — Onda J**  
**Plano ativo:** [plano 11 — corrective cutover/generalization/cleanup](../roadmap/llm-json-decoupling/planos/11-corrective-cutover-generalization-cleanup.md)

---

## Resumo

As Ondas A–I entregaram avanços importantes no OpenAPI-first, Turn Understanding, schema-driven presentation e cleanup de catálogos. Uma auditoria posterior do código mostrou, porém, que parte do conhecimento removido dos JSONs reapareceu em outra representação no runtime e que algumas provas finais foram reutilizadas após mudanças materiais.

Por isso:

```text
PASS histórico ≠ PASS do candidate final atual
```

O programa só volta a ser considerado concluído após a Onda J provar cutover, generalização, cleanup, segurança, arquitetura e R1–R11 no mesmo candidate final.

## Correção de política — 2026-09-11

A regra passa a ser interpretada de forma conceitual:

```text
NENHUM MAPA LATERAL OU SUBSTITUTO SEMÂNTICO DEVE SER AUTHORITY.
```

Não basta remover `pathMarkers/pathToken/pathContains/pathRules` do JSON. Também são drift:

- path→domain map em Python/TS;
- endpoint→parameter strategy por path/operationId;
- continuity/route segment por path-tail/operationId-tail;
- registry route→operationIds como catálogo técnico de routing;
- selector/intent/presenter por endpoint;
- taxonomia proprietária obrigatória para unknown provider funcionar.

## Drifts que reabriram a iniciativa

1. `ApiRouteDomainInferenceService._DOMAIN_RULES` portando fragments de path do catálogo anterior;
2. `ParameterStrategyInferenceService` recriando endpoint→strategy;
3. follow-up/route segment dependente de path/operationId inventory;
4. `route.operationIds` residual como catálogo técnico;
5. semantic authority duplicada entre heurísticas/mappers e LLM Turn Analysis;
6. `recommendationQueries` ainda em fallback/oracle;
7. capability metadata genérica `read/low/parallelSafe` para actions de efeitos diferentes;
8. Clean Architecture/DI residual;
9. credential defaults em smoke;
10. unknown/metamorphic histórico não reexecutado depois do último diff material.

## Ondas

| Onda | Entrega | Estado vigente |
|------|---------|----------------|
| A | Inventário + baseline freeze | histórico/baseline |
| B | Registry OpenAPI-first | implementação existente; revalidar residual na J |
| C | Turn Understanding | implementação existente; cleanup semântico reaberto |
| D | Multi-turn/args | implementação existente; path coupling reaberto |
| E | Capabilities/composition | implementação existente; metadata reaberta |
| F | Recommendations | implementação existente; cutover contextual reaberto |
| G | Presentation/skills | implementação existente; revalidar candidate final |
| H | Evals/cutover | PASS histórico, não release atual |
| I | Zero mapa lateral | **aceite invalidado por substitutos semânticos** |
| J | Correção cutover + generalização + cleanup | **ABERTA / P0** |

## Regra de execução da Onda J

```text
CUTOVER
→ GENERALIZATION
→ CLEANUP
→ VERIFY
→ COMPLETE_GATE
```

Cada E11.S* precisa provar wiring, positive/sibling/negative, generalização quando aplicável, residual scan e pós-condições antes de liberar a próxima etapa.

Estados `PARTIAL`, `LEGACY_FALLBACK`, `INCONCLUSIVE`, TODO/FIXME/HACK, flag/fallback sem exit criteria ou evidência de candidate antigo impedem `FINAL_RESULT=PASS` quando são materiais ao objetivo.

## Evidências históricas

As evidências E1–E10 permanecem preservadas em `docs/roadmap/llm-json-decoupling/evidence/`. Elas servem para baseline, comparação e rastreabilidade; não devem ser apagadas nem renomeadas para parecer evidência da Onda J.

## Critério para novo fechamento

Somente registrar novo release quando o Plano 11 produzir no `FINAL_CANDIDATE_GIT_SHA`:

```text
CUTOVER_RESULT = PASS
GENERALIZATION_RESULT = PASS
CLEANUP_RESULT = PASS
UNKNOWN_EXTERNAL_API = PASS
METAMORPHIC_RENAME = PASS
R1_R11_REQUIRED_DIMENSIONS = PASS
CLEAN_ARCHITECTURE = PASS
SECURITY_HYGIENE = PASS
RESIDUAL_SCAN = PASS
COMPLETE_GATE = PASS
VERIFY_FINAL = PASS
FINAL_RESULT = PASS
```
