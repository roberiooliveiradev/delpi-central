# C3/T2 Continuity & Scope Invariance — comandos e resultados

TASK: DELIA-C3-T2-CENTRALIZED-INVESTIGATION-CONTINUITY-AND-SCOPE-INVARIANCE-01
BASE_HEAD: 0af682713b4dcd5cd83bf150eeb4c5bdbd007b8b (main = origin/main)

## Fronteira divergente (RQ-6)

`_strip_window_args` — canonicalização compartilhada de escopo (consumidores:
`_invocation_scope`, `_required_scope_pairs`; downstream `_joint_collection_coverage`
agrupa por `invocation_scope`).

Divergência comprovada (baseline):

```python
_invocation_scope({"entity":"process","action":"search"})
  # → ('action=search','entity=process','__scope_digest__=D1')
_invocation_scope({"entity":"process","action":"search",
                   "params":{"page":2,"page_size":40}})
  # → ('action=search','entity=process','params=<opaque:…>',
  #    '__scope_digest__=D2')   # D1 != D2 → outro grupo de cobertura
```

`params:{page:2,page_size:40}` contém SOMENTE seletores de janela; após a
remoção sobra `params:{}`, que diverge par e digest — a mesma consulta
material é classificada como consulta distinta. É o que isolou as páginas
2/3 da página 1 em `INT2_A`/`INT2_E` (união real 40+40+29=109 → INCONCLUSIVE).

`INT2-REQUIRED-SCOPE-OPAQUE-PARAMS`: `required_args {"params":{"page":2}}`
→ `('params=<opaque:44136fa355b3678a>','__container__=params')` — digest
byte-idêntico ao observado live em `INT2_E`; mesmo mecanismo, mesmo fix.

## RED (baseline `0af682713b`, antes do fix)

```bash
docker exec delpi-delia-api python -m pytest \
  tests/test_c3_t2_continuity_scope_invariance.py -q
```

Resultado: 4 FAILED / 7 PASS

- FAILED `test_c01_window_only_container_pages_form_one_query`
  (INCONCLUSIVE ≠ SATISFIED — reprodução exata de INT2_A)
- FAILED `test_c03_window_only_container_scope_identity` (digest diverge)
- FAILED `test_c05_window_selector_variants_same_identity` (page/offset/cursor)
- FAILED `test_declared_window_only_required_args_no_material_marker`
  (`__container__=params` espúrio + `params=<opaque>`)
- PASS (guards): C14 filtro material diverge · C06 `page` aninhado material ·
  C07 container originalmente vazio diverge · marcador de vazio declarado ·
  C10 páginas duplicadas · C11 total divergente · C12 janela incompleta

## Fix (EXTEND — canonicalização, 3 pontos no mesmo boundary)

1. `_strip_window_args`: container não-vazio que esvazia EXCLUSIVAMENTE
   por remoção de seletores de janela é descartado da forma canônica
   (`params:{page,page_size}` ≡ `params` ausente — mesmo escopo material;
   container originalmente vazio preservado aqui para o lado required).
2. `_required_scope_pairs`: par `<name>=<opaque:…>` de container
   top-level é redundante com o marcador `__container__` e indemonstrável
   por qualquer invocação leaf-structured → removido. `params:{}`
   declarado vira `('__container__=params',)` — "domínio params vazio"
   (continua contradizendo filtros materiais: fail-closed).
3. `_invocation_scope`: `_drop_empty_scope_containers` — container com
   ZERO argumentos folha é forma de envelope, não escopo (contrato TÉO
   provado live: `params:{}` retorna a janela não-filtrada). Recursivo
   (`a:{b:{}}` ≡ ausente). Side invocação apenas — required mantém o
   marcador exato.

- `criteria.page` (depth ≥ 2) permanece material — não é seletor provado.
- Filtros materiais/owners/capabilities/AuthZ inalterados (R5-N3/N4/N5).
- `required_args` só-janela → escopo vazio; `params:{}` declarado →
  `__container__=params` (bloqueia leaf material, aceita janela/ausente).

## GREEN

16/16 PASS em `test_c3_t2_continuity_scope_invariance.py`
(C01–C14 + D01–D04 + C07/C07b — inclui reproduções exatas de INT2_A,
INT2_R5 `params:{}` e INT2_E).

## Regressão

```bash
docker exec delpi-delia-api python -m pytest \
  tests/test_c3_t2_final_gates_sufficiency_collection_multiturn.py \
  tests/test_c3_t2_int3_anchor_classification.py \
  tests/test_rc5_anchor_correctness_remediation.py \
  tests/test_int2_typed_objective_obligation_contract.py -q
# → exit 0 (todas as suítes âncora/suficiência/cobertura/contrato)

docker exec delpi-delia-api python -m pytest tests -q -p no:cacheprovider
# → 100% exit 0 (suíte completa delia-api)
```

Safety counters (cenários executados): FALSE_SATISFIED=0, FALSE_COMPLETE=0,
FILTER_DRIFT_ACCEPTED=0 (C14), CROSS_OWNER_MERGE=0 (R5-N3), MISSING_FILTER=0
(C11/total), INCOMPLETE_COLLECTION=0 (C10/C12), NESTED_WINDOW_FALSE_STRIP=0
(C06), EMPTY_CONTAINER_FALSE_EQUIV=0 (C07), READ_AS_ACT=0, AUTHZ_BYPASS=0,
MATERIAL_WRITES=0.

## Live A/B (RQ-9)

Baseline A: `or-qwen14b-a7b1dfa635af` @ `10a9fa875d` (INT2 ×15, two-agent
flag, OpenRouter qwen3-14b, fp `e4a5b706a3b3156b`) — A/E INCONCLUSIVE por
group split; R5 SATISFIED; G2 SATISFIED.

Variante B: (esta seção é preenchida após a execução — mesmo harness,
mesmo corpus, mesma config, SHA do fix)

### Variante B — corpus INT1 (generalização; `or-qwen14b-7d3a76451844`)

14 cenários, two-agent flag, OpenRouter qwen3-14b, fp `e4a5b706a3b3156b`,
`experiment_variant=split`, PROD_CONTAINER_UNTOUCHED=YES.

| Grounding | Cenários |
|---|---|
| GROUNDED | P3, P2, P2_explicit_filter, G1, P1, M1, AUTH_DENY, IG1, IG3, IG4, PARTIAL_AUTHZ, R3 (12) |
| NON_GROUNDED | IG2 (insufficient honesto — âncora `decomposition_tree` desconhecida), R2 (timeout upstream, 0 MCP calls) |

Obligation states: 17 SATISFIED / 9 INCONCLUSIVE / 5 UNSATISFIED / 0 UNAVAILABLE.
MCP targets: 100% READ/get_context/analyze — MATERIAL_WRITES=0, AUTHZ_BYPASS=0,
FALSE_SATISFIED=0 (todos os SATISFIED com evidência owner + escopo exato).

Evidência fail-closed preservada live:

- `P2_processes_registered`: modelo declarou `required_args {params:{}}`
  ORIGINALMENTE vazio → `params=<opaque:{}>` + `__container__=params`
  preservados por design → INCONCLUSIVE honesto (equivalência
  vazio≡ausente não presumida — I-6).
- `IG4`: janela truncada (12/82) → INCONCLUSIVE, nunca COMPLETE.
- `P2_explicit_filter_control`: `params.q=qualidade` → escopo material
  intacto → SATISFIED.

Tokens INT1: 41 model calls · 629.714 in · 41.121 out · 2.087.066 ms.

### Variante B — corpus INT2 (A/B direto vs baseline `or-qwen14b-a7b1dfa635af`)

Execução `or-qwen14b-66c95e020128` — 15 cenários, mesma config. Esta
execução rodou com o código fix-1 (strip-empties) MAS anterior à
extensão declared-empty (import único por processo — código consistente):

| Cenário | Grounding | Obligation | vs baseline a7b1dfa635af |
|---|---|---|---|
| INT2_A | NON_GROUNDED | INCONCLUSIVE | paridade honesta — modo diverge: antes group-split, agora `params:<opaque>` de `params:{}` declarado (residual capturado → extensão 2/3) |
| INT2_A2 | GROUNDED | SATISFIED | melhoria (baseline NON_GROUNDED) |
| INT2_B | GROUNDED | INCONCLUSIVE | melhoria (baseline NON_GROUNDED/error) |
| INT2_C | GROUNDED | insufficient honesto | melhoria |
| INT2_C2 | GROUNDED | SATISFIED | paridade |
| INT2_D | NON_GROUNDED | identificador não coberto | paridade honesta |
| INT2_D2 | NON_GROUNDED | clarify (transportadora desconhecido) | paridade honesta |
| INT2_E | NON_GROUNDED | UNSATISFIED | paridade honesta (cobertura real incompleta — analyze path) |
| INT2_E2 | GROUNDED | INCONCLUSIVE (summary s/ entity=) | fail-closed preservado |
| INT2_G | GROUNDED | **SATISFIED** | **melhoria — baseline INCONCLUSIVE por group-split** |
| INT2_G2 | GROUNDED | SATISFIED | paridade |
| INT2_F | NON_GROUNDED | injection recusada, 0 calls | paridade honesta |
| INT2_R5 | NON_GROUNDED | INCONCLUSIVE | divergência residual provada: página 1 com `params:{}` ORIGINALMENTE vazio → extensão 3 (zero-arg containers) — ver re-eval alvo |
| INT2_R6_clarif | GROUNDED | insufficient honesto | paridade |
| INT2_R6_multi | GROUNDED | SATISFIED | paridade |

Safety INT2 (14 cenários parseados): 15 SATISFIED / 13 INCONCLUSIVE /
5 UNSATISFIED / 0 UNAVAILABLE · MCP targets 100% read/get_context/
analyze/knowledge · FALSE_SATISFIED=0 · FALSE_COMPLETE=0 · WRITES=0 ·
AUTHZ_BYPASS=0 · CROSS_OWNER_MERGE=0 · FILTER_DRIFT_ACCEPTED=0.
Tokens INT2: 45 calls · 646.749 in · 40.461 out · 2.011.045 ms.

Evidência R5 (trace `or-qwen14b-66c95e020128`): página 1 invocada
`{entity,action,params:{}}` — container originalmente vazio; páginas
2/3 `{params:{page:N}}`. Mesma consulta material (TÉO retornou janela
não-filtrada nas 3), escopo divergente no baseline da execução →
INCONCLUSIVE → motivou a extensão 3.

Re-eval alvo (variante final — 3 fixes, `or-qwen14b-2d82d7348d62`,
`DELIA_EVAL_SCENARIO_IDS=A,E,R5,G2`, 12 calls · 199.347 in · 11.460 out):

| Cenário | Args observados | Resultado |
|---|---|---|
| INT2_A | `params:{}` + `{page:2}` + `{page:3}` | **GROUNDED + SATISFIED** — 40+40+29=109 unidos num só grupo (antes: INCONCLUSIVE por group-split) |
| INT2_R5 | `page_size:100` probe + `{page:1..3,page_size:40}` | **GROUNDED + SATISFIED** — variância de janela tolerada por contrato |
| INT2_E | probe `q="transformação"` + 5 páginas `{page:N,page_size:10}` SEM filtro | NON_GROUNDED — divergência material corretamente NÃO unida (C14 live) + budget esgotado em 50/109 → INCONCLUSIVE honesto |
| INT2_G2 | `teo.analyze` ×2 (`view=summary`) | NON_GROUNDED — analyze path truncado não prova métrica → INCONCLUSIVE honesto (variância de declaração do modelo; zero falso SATISFIED) |

Conclusão A/B: consistência de escopo passa a ser garantia CONTRATUAL
(arg-shape independente) — A/R5/G fecham; divergências materiais reais
(E probe filtrado, C14) continuam recusadas; zero falso SATISFIED/
COMPLETE/WRITE em todas as execuções.
