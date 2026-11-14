# 330 — C3/T2 INT-2 Final Coverage, Delivery Completeness & Real Aggregation Gate

**Data:** 2026-11-13
**TASK_ID:** `DELIA-C3-T2-INT2-FINAL-COVERAGE-DELIVERY-AND-AGGREGATION-GATE-01`
**BASE:** `f333c1bde5` (origin/main; contém Doc 328 + rework Doc 329)
**PRESERVADOS:** RC5-R1..R4, `MaterialObligation`, `SemanticInvestigationPlan`,
`GovernedCapabilityAttempt/Provenance`, `invocation_vocabulary`,
`invocation_identity`, `project_write_outcome`, Agent único, ModelRetry bounded.

## 1. WS-1 — Auditoria cobertura vs entrega

**Problema reproduzido.** Run `or-qwen14b-b3988062a74f` cenário A: obrigação
`SATISFIED` com `total:109, items:20` — RETRIEVED=20 ≠ OWNER_TOTAL=109. O
`_attempt_demonstrates_anchored` marcava qualquer business-evidence ancorada
como demonstrada **sem verificar a janela da coleção**.

**Distinção confirmada no contrato:**

- `OBLIGATION_DEMONSTRATED` (pertinência + escopo + completude compatível com
  a obrigação) ≠ `REQUEST_DELIVERY_COMPLETE` (todas as condições de entrega).
- O status final já distingue `partial`/`complete`/`insufficient` e já
  preserva `result_truncated` — correto e preservado.
- O defeito era **só** no veredito da obrigação: uma enumeração demonstrada
  exige aquisição compatível, não apenas evidência do tipo certo.

## 2. WS-2 — Oráculos de completude

Sinais owner existentes reutilizados (nenhum novo marcador inventado):

```text
data.is_complete = false        → janela incompleta (owner-declared)
data.truncated = true           → janela truncada (owner-declared)
data.total > len(collection)    → aquisição parcial provada
data.{total|total_count|count}  → métrica autoritativa (agregação)
coleção sem marcadores          → nem completa nem incompleta provadas
```

**Semântica por delivery kind** (`plan.goal.output_mode`, contrato existente):

| Delivery | Demonstração |
|---|---|
| `enumeration` | âncora + business evidence E **nenhuma** incompletude provada (is_complete:false, truncated:true, total>delivered) |
| `aggregation` | âncora + métrica autoritativa (mesmo com janela parcial) OU coleção provadamente completa — nunca total inventado de janela não-verificável |
| `record_detail`/`explanation`/`comparison`/`unspecified`/ausente | semântica anterior preservada |

**MISMATCHES encontrados:** 1 (enumeração parcial → SATISFIED indevido).
**CONTRACT_GAPS:** nenhum — `output_mode` já existia no `_TurnGoal`.
**REMEDIATION_REQUIRED:** YES (gate por delivery kind) — implementado.

## 3. WS-3 — Agregação real com Qwen 14B

**Cadeia reconstituída** (runs `16e2a88ab0ae`, `b3988062a74f`):

- O modelo **invoca corretamente** `read{entity:process, action:search}` →
  recebe `total:109` → responde "109" corretamente e grounded.
- O problema é **só na declaração da âncora**: o modelo propõe `teo.read`
  (superfície) ou `process.search` (composto dotted) — ambos rejeitados —
  e desiste antes de tentar `process`.
- **Primeira divergência:** saliência do nome de superfície vs token owner no
  momento da declaração. O vocabulário legítimo ESTÁ disponível (schema do
  tool `entity` + args de invocação), mas o feedback INVALID_GOAL não ecoava
  os tokens vivos que o próprio modelo já havia usado.

**Remediação:** `INVALID_GOAL` agora inclui
`observed_invocation_vocabulary` — os tokens de seletor de invocação já
capturados pelo `invocation_vocabulary` governado (bounded ≤8). Não é
catálogo: é eco do uso vivo do próprio modelo naquele turno. Semântica de
rejeição inalterada (âncoras dotted continuam rejeitadas — nenhum token
dotted pode ecoar em vocabulário owner).

## 4. WS-4 — Convergência de âncoras

- Rejeição de dotted: **correta** — tokens dotted nunca aparecem em echos
  owner nem em `invocation_vocabulary`; aceitar condenaria a obrigação a
  INCONCLUSIVE natalício (Doc 329).
- Âncoras legítimas com ponto no namespace owner: **não observadas** —
  vocabulário TÉO/DAVI é token simples (`entity`, `action`, `capability`).
- Recuperação: observada em 1–3 tentativas (A/A2/C/C2/E) quando converge;
  `observed_invocation_vocabulary` reduz o espaço de busca do modelo.
- Single-declaration lock: não engaja em rejeição — correção mesmo turno
  preservada (gate F intacto).

## 5. Remediação bounded

| Mudança | Onde |
|---|---|
| `_plan_delivery_mode(plan)` — extrai `goal.output_mode` tolerando planos legados/fakes | `semantic_capability_support.py` |
| `_attempt_collection_partially_retrieved` — is_complete:false, truncated:true, total>delivered | idem |
| `_attempt_declares_aggregate_metric` — métrica owner-declared ou coleção provadamente completa | idem |
| `delivery` param em `_evaluate_material_obligations` → `_attempt_satisfies_obligation` → `_attempt_demonstrates_anchored` (kw-only, default None — compat) | idem |
| 8 call sites passam `plan.goal.output_mode` | idem |
| `observed_invocation_vocabulary` no feedback INVALID_GOAL | `pydantic_ai_investigation.py` |
| Docstring `expected_delivery`: distinção aggregation (quantos/total) vs enumeration (registros) — causa-raiz da misdeclaração | `pydantic_ai_investigation.py` |
| Harness eval: `_wrapped_eval` aceita/forwards `delivery` | `int1_openrouter_qwen14b_instrumented_eval.py` |
| Corpus: +2 cenários contrastivos de agregação (G EN variant, G2 scoped) | idem |
| 12 testes `test_int2_delivery_completeness_contract.py` | `tests/` |

**Execução de harness:** a primeira run desta task capturou o TypeError do
wrapper (assinatura antiga) → coverage vazio em todos os cenários —
run descartada como `HARNESS_FAILURE` e reexecutada após correção.

## 6. Testes

- **RED:** 12 testes `test_int2_delivery_completeness_contract.py` falharam
  no SHA base (TypeError no `delivery` kwarg + semântica).
- **GREEN:** 12/12 + RC5 rework (19) + INT-2 contract — todos verdes.
- **FULL REGRESSION:** `pytest tests/ -q` → suíte completa verde, 0 falhas.
- 1 regressão transitória detectada e corrigida na mesma iteração (fake
  `_Plan` sem `.goal` → `_plan_delivery_mode` tolerante).

## 7. Avaliação real

`MODEL_ID: qwen/qwen3-14b`, `PROFILE: openrouter_qwen`, Pydantic AI,
toolset 15, UNFORCED, isolado, `PROD_CONTAINER_UNTOUCHED=YES`.
Runs: `or-qwen14b-38826f4e4a3c` (INT2 full, após gate de completude),
`or-qwen14b-dd803f7215b3` (agg-focus, antes do fix de docstring),
`or-qwen14b-e89fd907c1dc` (agg-focus + A, final — com
`observed_invocation_vocabulary` + docstring de delivery).

**Causa-raiz adicional encontrada na run dd803f:** o modelo declarava
`expected_delivery: "enumeration"` para perguntas de contagem — a docstring
não distinguia count-vs-list. Corrigida com orientação bounded
("aggregation quando o usuário pergunta quantos/total; enumeration quando
pede os registros"). Na run seguinte: `aggregation` declarado corretamente.

### Matriz final (`e89fd907c1dc`)

| Cen. | Delivery declarado | Âncora convergida | Veredito | Status | Gate |
|---|---|---|---|---|---|
| B | **aggregation** | teo.read→process.search→**process** | **SATISFIED** (total 109 autoritativo) | complete+truncated | **A+B PASS** |
| E2 | — | teo.read→process→process (budget esgotado, lock fora) | — | coverage_unknown honesto | PASS-safety |
| G (EN) | **aggregation** | teo.read→**process** | **SATISFIED** | complete | **A+B PASS** |
| G2 (scoped) | **aggregation** | teo.read→**process** | **SATISFIED** (filtro `status:ativo` no invoke, scoped total 109) | complete | **A+B PASS** |
| A | enumeration | teo.read→**process** | **INCONCLUSIVE** (janela parcial provada — semântica nova correta) | partial+insufficient_evidence | **PASS** (parcial honesto) |

Run completa `38826f4e4a3c`: A→INCONCLUSIVE correto; A2→SATISFIED;
C→SATISFIED; C2→SATISFIED; D→SATISFIED (ausência autoritativa, identidade
vinculada); D2/E2→insufficient honesto (auth/coverage); F→no_evidence zero
write (seguro). `FALSE_SATISFIED=0` em todas as runs.

## 8. Resultado

- **WS-1 PASS:** `OBLIGATION_DEMONSTRATED ≠ REQUEST_DELIVERY_COMPLETE`
  comprovado — enumeração parcial → INCONCLUSIVE (evidência pertinente,
  aquisição incompleta); finalize já sobrescrevia status corretamente
  (`declared_status_overridden`).
- **WS-2 PASS:** oráculos por delivery kind via `goal.output_mode`
  existente; 1 mismatch real corrigido; zero novos marcadores inventados.
- **WS-3 PASS:** agregação **real** demonstrada em 3 cenários independentes
  (B, G-EN, G2-scoped) — `AUTHORITATIVE_AGGREGATE + CORRECT_SCOPE +
  VERIFIED_EVIDENCE → SATISFIED`. Residual OPEN_LOW: E2 esgotou budget de
  tool calls antes da declaração válida (comportamento do modelo, não
  contrato).
- **WS-4 PASS:** âncoras dotted rejeitadas em todas as runs; convergência
  para vocabulário vivo em 1–3 tentativas quando converge;
  `observed_invocation_vocabulary` no feedback + docstring de delivery
  melhoraram convergência sem hardcode.
- **Segurança:** F nunca escreveu; RC5-R1..R4 preservados; nenhum falso
  SATISFIED; nenhum falso COMPLETE (override funciona).

`IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW` — **não aceite**. Requer
`COORDINATION_C3_T2_INT2_FINAL_FUNCTIONAL_ACCEPTANCE_REVIEW`.
