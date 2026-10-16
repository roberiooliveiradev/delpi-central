# 34 — MCP Post-Index Binding Fix

**TASK:** `DELIA-C3-MCP-POST-INDEX-BINDING-FIX-01`  
**MODE:** minimal EXTEND — structured index IDs → exact select → guide READ  
**STATUS:** `FIX_EVIDENCE_RECORDED` · `STAGE_03_ACCEPTED=NO`

---

## 1. Causa

Após o INDEX READ, a proveniência usava substring em texto (`text in owner_evidence`) e a projeção caía em `_build_arguments` genérico. O modelo real omitia o identificador ou inventava valores presentes só em descrições → clarificação desnecessária ou dump do índice.

## 2. Diff funcional

`orchestration.py` (REUSE `_resolver_entities` / `_entity_identifier`):

- `_RESOLVER_ENTITY_KEYS` + `topics` (coleção genérica de catálogo).
- `_index_declared_identifiers` / `_index_option_rows` — IDs exatos do structured.
- `INDEX_SELECT_INSTRUCTION` + `_bind_arguments_from_index` — seleção modelada + validação exata + projeção no campo do schema.
- `_post_self_index_argument_gaps` — membership em frozenset de IDs (não substring).
- Revalidação pós-resolver; sem hardcode de provider/campo/guia.

## 3. Testes

`test_mcp_iterative_index_probe.py` + Stage03: Atlas positivo; descrição ≠ ID; ID inexistente rejeitado; ACT ausente.

## 4. Live SSH

Uma execução MESSAGE-only em `srv-api` com `moonshotai/kimi-k3` — ver ledger §6.211.

## 5. Outcome

```text
REUSE_DECISION=EXTEND
NEW_PLANNER=NO PROVIDER_HARDCODE=NO
STAGE_03_ACCEPTED=NO
C3_EXECUTED=NO
NEXT=INDEPENDENT_REVIEW
```
