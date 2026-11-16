# WS-1 — Suficiência material (diagnóstico e fechamento)

## Causa raiz

Primeira fronteira divergente: `_attempt_demonstrates_anchored` /
`_attempt_satisfies_obligation` exigiam eco literal de
`evidence_source`/`operation` do plano (ex.: `summary`/`analysis`)
contra o vocabulário do owner (ex.: `process`/`READ` via `teo.read`).
Uma métrica autoritativa (`total_count`) sob filtro material
(`params.status=ativo`) permanecia `INCONCLUSIVE` apesar de GROUNDED.

## Classificação da divergência

| Tipo | Tratamento |
|---|---|
| Apresentação (`summary`/`analysis`/`view=*`) vs entidade | equivalência sob `delivery=aggregation` + métrica + filtros materiais |
| `params.*` ↔ `arguments.*` (mesmo leaf) | alias de container no `_required_scope_state` |
| Filtro ausente / owner errado / identidade errada | permanece UNSATISFIED / INCONCLUSIVE |

## Reuse decision

```yaml
RESPONSIBILITY: material obligation demonstration
OWNER: semantic_capability_support
CANONICAL_SOURCE: RC5 MaterialObligation + delivery mode
EXISTING_EQUIVALENT: YES
REUSE_DECISION: EXTEND
```

## Live eval

`or-qwen14b-00bb3f24aebb` / INT2_G2 → GROUNDED + obrigação SATISFIED
(`Contagem de processos ativos` / `teo.read` ×3 / total 109).
