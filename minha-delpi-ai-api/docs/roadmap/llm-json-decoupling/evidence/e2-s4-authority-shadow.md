# E2.S4 — Product-family cutover canary ON

**Status:** `CUTOVER_PRODUCT_CANARY` (2026-09-10) — família **product** com dial `cutoverEnabled=true`  
**Onda:** C (plano 02)

## O que entrou

| Peça | Path |
|------|------|
| Dial | `productFamilyAuthorityShadow.cutoverEnabled=true` (só `families.product`) |
| Mapper | grounding obrigatório (código/`produto`) + bloqueio doc/RAG (`política…`) |
| Authority | `detect` / `refine_*` usam mapper; fallback legado se `None` |
| Shadow | `candidateProductIntent` + `cutover=true` |

## Paridade offline (corpus E2.S2)

```text
agree_legacy_effective = 10/10
rag_policy → mapped=None → fallback full (PASS negativo)
stock/synonym/compound → mapped=stock|multi_scope (PASS)
```

## Aceite

```text
SHADOW_COMPARE_WIRED = PASS
PRODUCT_CUTOVER_ON = PASS
PRODUCT_MAPPER_GROUNDING = PASS
PRODUCT_MAPPER_NEGATIVE_RAG = PASS
CUTOVER_PRODUCTION_KPI = NOT_STARTED
DELETE_HEURISTICS = BLOCKED
```

## Rollback

`productFamilyAuthorityShadow.cutoverEnabled=false` → pipeline legado imediato.

## Não feito

- Production / KPI families
- E2.S5–S7 DELETE heurísticas
