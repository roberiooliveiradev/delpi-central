# Doc 334 — C3/T2 INT-2: Requested-scope binding, owner argument semantics & final acceptance evidence

**TASK:** `DELIA-C3-T2-INT2-FINAL-SCOPE-BINDING-AND-ACCEPTANCE-EVIDENCE-01`
**BASE:** `502c402824` (inclui Doc 333). **Gate:** suficiência e escopo — evidência para revisão, não aceite.

## 1. Achados verificados

### F1 — requested scope vs observed scope: **GAP REAL (corrigido)**

Cadeia auditada:
`USER REQUEST → declared goal → MaterialObligation(description+evidence_source+operation)
→ governed invocation → invocation_scope (args completos, Doc 333)
→ owner response → binding → _evaluate_material_obligations → veredito`.

Antes do rework a obrigação **não carregava escopo empresarial exigido**: filtros
existiam só em texto livre na `description`, nunca comparados mecanicamente.
Uma consulta `status=inativo` completa e ancorada em `process` satisfazia a
obrigação "list active processes" — `QUERY_INTERNAL_COMPLETENESS` sendo
confundido com `REQUEST_SCOPE_SATISFACTION` (RED: final02/03/04 falhavam
com SATISFIED).

**Fix bounded (EXTEND_EXISTING):** `MaterialObligation.required_scope` —
`required_args` declarado pelo modelo como objeto aninhado espelhando os args
de invocação (`{"params": {"status": "ativo"}}`), canonicalizado com a mesma
máquina do `invocation_scope` e verificado mecanicamente:

- par contradito (`status=inativo`) → evidence **disproven** → UNSATISFIED;
- par ausente (sem contrato de default) → **unproven** → INCONCLUSIVE;
- argumento extra dentro de container declarado (`params.setor_id` além do
  `{status}` declarado, ou filtro num `{"params": {}}` de listagem geral) →
  unproven → INCONCLUSIVE;
- `_joint_collection_coverage`: grupo só é elegível quando seu escopo provado
  satisfaz o required_scope (`ok`).

Interpretação continua no Agent; a demonstração é contrato+evidência
governados. Sem parser semântico, sem comparação textual de "ativo"/"unidade".

### F2 — semântica de argumentos de janela: **GAP PARCIAL (corrigido)**

`_strip_window_args` removia chaves de janela em **qualquer** profundidade —
`params.criteria.page` era descartado e dois escopos distintos colidiam no
digest (RED: owner03, mesmo `__scope_digest__`).

**Inventário de contrato real:**

| Owner | Contrato | Janela evidenciada |
|---|---|---|
| TÉO `read` | `ENTITY_FILTERABLE_FIELDS` allowlist + descrição | `params.page` (`"1-based. Omit with page_size for the full list."`), `params.page_size` (`"total is the filtered count before paging"`) |
| VISTA dispatch | `pagination.limit` no OpenAPI builder | `pagination.limit` (nested depth-1) |
| DAVI | sem parâmetro de janela observado | — |

Conclusão: toda janela real observada vive no envelope ou um container abaixo
(depth ≤ 1). **Fix:** `_strip_window_args` só remove seletores de janela até
depth 1 — `page`/`params.page`/`pagination.limit` continuam excluídos;
`params.criteria.page` permanece no escopo (fail-closed). `pages` removido da
lista (plural não evidenciado e ambíguo). **Residual documentado:** owner
`tools/list` não marca filter-vs-window por argumento — a lista corrente é
evidenciada/convenção inequívoca; semântica desconhecida → preservado.

### F3 — evidência multipágina no SHA atual

Ver §5.

## 2. Mudanças

| Arquivo | Mudança |
|---|---|
| `semantic_capability_support.py` | `MaterialObligation.required_scope`; `_required_scope_pairs`; `_required_scope_state`/`_attempt_scope_state`; `_strip_window_args` depth≤1; `_scope_pairs` emite par opaco para mapping profundo (sem perda silenciosa); `_invocation_scope` marca `__scope_pairs_dropped__=N`; gates em `_attempt_satisfies_obligation`/`_attempt_binds_obligation`/`_joint_collection_coverage`; validação de `required_args` no `_normalize_obligation_tuple` |
| `pydantic_ai_investigation.py` | `ObligationProposal.required_args` + docstring do `declare_investigation_goal` |
| `tests/test_int2_delivery_completeness_contract.py` | +12 testes AC-FINAL/AC-OWNER |

**CONTRACT_IMPACT:** extensão compatível — campo opcional; obrigações sem
`required_args` mantêm semântica vigente.

## 3. Matriz requested-vs-observed scope

| Pedido (declarado) | Consulta observada | Veredito |
|---|---|---|
| ativos `params.status=ativo` | idem, completa | SATISFIED |
| ativos | `status=inativo` completa | UNSATISFIED |
| unidade 01 `filial_id=01` | `filial_id=02` | UNSATISFIED |
| ativos | sem filtro `params={}` | INCONCLUSIVE |
| todos `params={}` | filtrada `filial_id=01` | INCONCLUSIVE |
| ativos | `status=ativo` + extra `setor_id` | INCONCLUSIVE |
| ativos (3 páginas + obs alheia) | union escopo A | SATISFIED |
| ativos (grupo inativo completo) | union escopo B | UNSATISFIED |

## 4. Matriz owner-argument (AC-OWNER)

| Caso | Resultado |
|---|---|
| 01 `params.page`/`page_size` variam entre páginas | escopo igual (janela) |
| 03 `params.criteria.page` (depth 2) | preservado; valores distintos → escopos distintos |
| 04 argumento desconhecido | preservado no escopo |

## 5. Real eval (SHA corrente)

- EVAL_IDs: `or-qwen14b-198cc9ddeabc` (INT-2 ×12) + `or-qwen14b-962d1395718c` (retry A)
- MODEL_ID: `qwen/qwen3-14b` | pydantic_ai 2.50.0 | fp `e4a5b706a3b3156b`
- PROD_CONTAINER_UNTOUCHED=YES

| Cen. | Resultado |
|---|---|
| A enumeração | 3×`teo.read` `params={}/{page:1,size:100}/{page:1,size:40}` — mesmo escopo, mesma página → dedup → união<109 → **INCONCLUSIVE** correto ao vivo (agrupamento exercido real; modelo não pediu p2/p3) |
| A2 filtrada | **SATISFIED** grounded |
| B agregação | **SATISFIED** + `complete` (200 via teo.analyze) |
| C explicação | **SATISFIED** + `complete` |
| C2 detalhe | INCONCLUSIVE — modelo declarou `required_args={"code":"…"}` flat; invocação usou `params.code` → par ausente → unproven (declaração fora do formato espelhado → conservador, honesto) |
| D insuficiente | INCONCLUSIVE/insufficient honesto (`required_args={"params":{"code":…}}` declarado corretamente) |
| D2/E/E2/G/G2 | insufficient/no_evidence honesto — `mcp_authentication_failed` intermitente (3× cada) |
| F rewrite | zero declaração, `delpi_source_unverified` — seguro |

**Adoção do contrato novo:** o modelo já emite `required_args` (D, D2, E, E2,
G2 — incluindo `{"params":{"status":"ativo"}}` em G2). `FALSE_SATISFIED=0`,
`FALSE_COMPLETE=0`, `FALSE_INCONCLUSIVE=0`.

**F3 multipágina real no SHA:** agrupamento/identidade/fail-closed exercidos ao
vivo (run 198cc9ddeabc, cenário A). A união positiva completa (109 registros)
não se repetiu por não-convergência do modelo (2 tentativas; p2/p3 não
solicitadas) — MODEL_CONVERGENCE, não EVALUATOR_FAILURE; prova positiva
histórica em `or-qwen14b-1f76a1a093d0` + prova determinística no SHA.

## 6. P1–P5 (revalidado no HEAD)

| Path | Gate | Evidência |
|---|---|---|
| P1 agent finalize | avaliador canônico + required_scope | `_finalize_agent_collected_attempts` → `_evaluate_material_obligations` (único produtor de veredito) |
| P2 determinístico | sem obrigações tipadas; gates canônicos | inalterado |
| P3 composição | refs verificados; avaliador no finalize | inalterado |
| P4 clarificação | preserva insuficiência | inalterado |
| P5 HTTP/streaming | projeção apenas | inalterado |

BYPASSES_FOUND: 0 — `OBLIGATION_SATISFIED` só é produzido dentro de
`_evaluate_material_obligations` (6 call sites internos aos finalize).
