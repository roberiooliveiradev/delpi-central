# 34 — MCP Post-Index Binding Fix

**TASK:** `DELIA-C3-MCP-POST-INDEX-BINDING-FIX-01`  
**MODE:** minimal EXTEND — structured index IDs → exact select → guide READ  
**STATUS:** `FIX_EVIDENCE_RECORDED` · `STAGE_03_ACCEPTED=NO`

---

## 1. Causa

Após o INDEX READ, a proveniência usava substring em texto (`text in owner_evidence`) e a projeção caía em `_build_arguments` genérico. O modelo real omitia o identificador ou inventava valores presentes só em descrições → clarificação desnecessária ou dump do índice.

## 2. Diff funcional

`orchestration.py` (REUSE unwrap/entity-key conventions / `_entity_identifier`):

- `_RESOLVER_ENTITY_KEYS` + `topics` (coleção genérica de catálogo).
- `_index_catalog_entities` / `_index_declared_identifiers` / `_index_option_rows` — IDs exatos do structured; budget `MAX_INDEX_OPTION_ENTRIES=48` (não o shortlist de ambiguidade do resolver).
- `INDEX_SELECT_INSTRUCTION` + `_bind_arguments_from_index` — seleção modelada + validação exata + projeção no campo do schema.
- `_post_self_index_argument_gaps` — membership em frozenset de IDs (não substring).
- Revalidação pós-resolver; sem hardcode de provider/campo/guia.

## 3. Testes

`test_mcp_iterative_index_probe.py` + Stage03: Atlas positivo; descrição ≠ ID; ID inexistente rejeitado; catálogo >10 IDs preservado; ACT ausente.

## 4. Live SSH

**Primeira evidência (binding, truncado):** MESSAGE-only em `srv-api` / `moonshotai/kimi-k3` no SHA `cd88e3f49c`: INDEX→select→GUIDE (`identifiers=10`, GROUNDED) mas shortlist omitiu `process` → selecionou `decomposition`. `END_TO_END=FAIL`.

**Validação final do budget (`DELIA-C3-MCP-INDEX-GUIDANCE-FINAL-LIVE-VALIDATION-01`):** deploy runtime com `MAX_INDEX_OPTION_ENTRIES=48` (repo HEAD contendo `42991c5ae3`; checkout `06896575bd`). Uma MESSAGE: «Como faço para cadastrar um processo no Transformômetro?»

```text
index_probe identifiers=25
index_select bound field=topic
provider_invoke arg_keys=topic
guide id=process GROUNDED
MATERIAL_ACT=0
LIVE_VERDICT=PASS
```

Sem alteração de código nesta validação. `STAGE_03_ACCEPTED=NO` (aceite independente pendente).

## 5. Outcome

```text
REUSE_DECISION=EXTEND
NEW_PLANNER=NO PROVIDER_HARDCODE=NO
FINAL_LIVE_VALIDATION=PASS
STAGE_03_ACCEPTED=NO
C3_EXECUTED=NO
NEXT=INDEPENDENT_STAGE03_ACCEPTANCE_REVIEW
```
