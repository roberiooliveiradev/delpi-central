# C3/T2 — RC5 Obligation Evidence Anchors: Implementation & Real Eval

**TASK:** `DELIA-C3-T2-RC5-OBLIGATION-EVIDENCE-ANCHORS-IMPLEMENTATION-AND-REAL-EVAL-01`
**Data:** 2026-11-13 · **Base:** `2736692af0` (REFERENCE; execução reancorada → `0601e0002cf3` → ff `e3ed2d3028` = origin/main)
**Natureza:** implementação bounded EXTEND sobre a decisão aprovada do Doc 327 — sem novo Agent, planner, router, engine, catálogo de domínio ou autoridade paralela. `PRODUCTION_DEPLOY=NO`, `PHASE_ADVANCEMENT=NO`, `INT3/T3=NOT_AUTHORIZED`. Resultado do executor: ver §11 — **não é aceite**.

## 1. Reancoragem e gates

- `git status` sem conflitos; WIP concorrente (`.tmp-helpdesk-venv/`, `plugins/engineering/e2e/dbg*.mjs`, `plugin-ui` PRC, `tv-dashboard` artifacts) preservado fora do escopo.
- `PHASE_FROM_16=C3/T2` · `NEXT_FROM_LEDGER=COORDINATION_RC5_IMPLEMENTATION` · `CP_RQ`: `EVIDENCE_BOUND ≠ OBLIGATION_DEMONSTRATED`.
- `EXISTING_EQUIVALENT=YES` · `REUSE_DECISION=EXTEND` · `ABSTRACTION_GATE=PASS` · `AGENT_COUNT=1`.
- Root cause (Doc 327, revalidada): `evidence_needed: tuple[str]` texto livre → branch subject-scope (`if " " in needle: return True`) marcava SATISFIED para qualquer evidência business bound — binding ≠ demonstração.

## 2. Refinamentos contratuais aplicados (Phase B)

| Refinamento | Decisão |
|---|---|
| B1 compat | `evidence_needed` aceita `str` legado **e** `MaterialObligation(description, evidence_source?, operation?)`; str multi-token não-identitária passa SATISFIED→INCONCLUSIVE (transição conservadora, nunca mais permissiva) |
| B2 namespace | Âncora verificada mecanicamente contra **três canais distintos**: (a) ecos owner em `structured` (`entity`/`action_id`/`capability`/`shape`/`action{}`), (b) `invocation_vocabulary` — seletores de vocabulário owner capturados dos args (`entity`/`action`/`capability`/`view`/`kind`, bounded ≤8 tokens ≤64 chars, top-level apenas), (c) superfície governada `specialist.remote_capability`/`action_id` — **bind apenas, nunca demonstra** (nome de envelope não prova kind). Namespaces não são intercambiáveis |
| B3 ausência | `AUTHORITATIVE_ABSENCE` = SUCCESS + provenance completa + outcome.is_complete + sem `truncated`/`is_complete:false` + coleções vazias com totais 0 (ou `EMPTY_RESULT_TEXT`) — somente para âncora correspondida |
| B3 postcondition | `operation=act` exige `operation_class==ACT` do attempt + `structured.data` não-vazio (postcondition atestada pelo owner). READ/ANALYSIS/PREPARE/DISCOVERY nunca demonstram ACT |
| B4 rollback | Versões de instrução preservadas verbatim (v2-4 fp `9737ae1d9d281974` selecionável); reverter o commit restaura contrato+semântica atomicamente — sem flag de compat permanente |

## 3. Implementação (EXTEND)

- `contracts.py` / `capability_attempt.py` — `GovernedCapabilityProvenance`/`Binding` += `operation_class: str|None`, `invocation_vocabulary: tuple[str,...]` (aditivos, default `None`/`()`).
- `semantic_capability_support.py` — `MaterialObligation` (frozen, `to_projection`, eq/hash str-compat); `_obligation_item` (coerção str/dict/objeto); `_invocation_vocabulary` (seletores bounded); `_attempt_anchor_tokens` (echos owner + invocation vocab — **exclui** nomes de envelope); `_attempt_surface_anchor_match` (composite `specialist.remote`); `_attempt_operation_class`; `_attempt_declares_authoritative_absence`; `_attempt_postcondition_demonstrated`; `_attempt_demonstrates_anchored`; `_attempt_binds_obligation` (BOUND-não-demonstrado → INCONCLUSIVE); `_evaluate_material_obligations` com semântica SATISFIED=demonstrated/INCONCLUSIVE=bound-unverified/UNSATISFIED=unbound-ou-disproven/UNAVAILABLE, 1:1 para SATISFIED.
- `governed_capability_orchestrator.py` — `_accept_semantic_investigation_plan` normaliza formas `str`/`Mapping`/`MaterialObligation`; provenance/binding passam a gravar `operation_class`+`invocation_vocabulary` nos 3 pontos de construção (`_provenance`, `_outcome_attempt`, `_semantic_invoke`); consumer de clarification renderiza descrições (não objetos).
- `pydantic_ai_investigation.py` — docstring de `declare_investigation_goal` descreve a forma tipada e o caráter de proposta não-autoritativa; projeção `evidence_needed` serializa `to_projection()`.
- `scripts/int1_openrouter_qwen14b_instrumented_eval.py` — captures serializam `MaterialObligation` via `to_projection`.
- `config/investigation_instructions.delpi.json` — nova default `generalist-semantic-v2-5-obligation-anchors` (fp `4be504a714f320b3`): declaração obrigatória para objetivos de evidência business; `evidence_source` = token de vocabulário vivo do owner (entity/action/echo), **nunca** o nome do envelope proxy (`owner.op`); provider-agnóstica (guardrail R6/R01 verde).
- **Legado removido:** branch subject-scope `if " " in needle: return True` → `return False` (bind em `_attempt_binds_obligation`, nunca demonstra).

## 4. Estados e matriz de decisão

| Condição | Estado |
|---|---|
| Âncora ecoada/invocada + operation + evidência (ou ausência autoritativa p/ identidade) | `SATISFIED` |
| Âncora só em superfície (`specialist.remote`), ou âncora não verificável (owner não ecoa), ou subject-scope str com evidência bound | `INCONCLUSIVE` |
| Tokens owner presentes e contradizem a âncora / operation class contradiz / nenhuma evidência bound | `UNSATISFIED` |
| Fonte autoritativa inacessível | `UNAVAILABLE` |

## 5. RED → GREEN e regressão

- **RED:** `MaterialObligation` inexistente (ImportError na coleta); após contrato, 15 cenários AC-RC5 falharam no SHA anterior (subject-scope SATISFIED, READ→ACT, cadastro→estrutura, ACT sem postcondition, âncora não-ecoada SATISFIED).
- **GREEN:** `test_int2_typed_objective_obligation_contract.py` — 30+ testes RC5 (AC-01..15) + surface-anchor bind/disprove; fixtures `_anchored_attempt`/`_bound_attempt` tipadas.
- **Ajustes de oráculo legítimos:** default v2-4→v2-5 + fingerprint; testes de subject-scope atualizados para a transição conservadora documentada (INCONCLUSIVE, não SATISFIED).
- **Full suite delia-api:** **1650 passed** (`pytest tests/ -q`, exit 0) — +22 líquidos vs 1628.
- **Eval harness fix:** captures `goal_declarations`/`obligation_coverage` serializavam objeto cru → corrigido para `to_projection()` (bug do harness, não do produto).

## 6. Avaliação real — corpus INT-2 completo (isolada)

Config: `qwen/qwen3-14b` · `openrouter_qwen` · pydantic_ai (container eval `delpi-delia-eval-int1-or-qwen14b`, **produção `delpi-delia-api` intocada** — `PROD_CONTAINER_UNTOUCHED=YES`, StartedAt idêntico antes/depois) · instrução v2-5 · security gate `READY_FOR_ISOLATED_EVAL` · dry-run fingerprint ok.

Três iterações de eval documentam a convergência da correção de namespace:

| Run | Achado | Correção |
|---|---|---|
| r1 (`e260cf1164f7` parcial) | crash do harness (serialization) | `to_projection()` nos captures |
| r2 (10 cenários) | modelo declarou âncora de envelope (`teo.read`/`davi.read`) → UNSATISFIED (bind disproven) | surface-composite bind (INCONCLUSIVE) + instrução "never dotted proxy envelope name" (provider-agnóstica) |
| r3 `or-qwen14b-0d53756cb6bb` | matriz final — ver §7 | — |

## 7. Matriz de outcome (r3 — `or-qwen14b-0d53756cb6bb`, 10 cenários)

Dados reais de `obligation_coverage`/`declared_answer`/`limitations` do trace instrumentado. Achado comportamental do modelo 14B: `evidence_source` é declarado consistentemente como nome de envelope (`teo.read`/`davi.read`) mesmo com a instrução corrigida — o verificador classifica corretamente esses casos como BOUND→INCONCLUSIVE (nunca falso SATISFIED), e a resposta final carrega a limitação honesta. O único caso de âncora owner-vocab (`get_product_structure`) demonstra SATISFIED por ausência autoritativa.

| Caso | Oráculo | Resultado real | Veredito |
|---|---|---|---|
| A enumeração | enumeração correta sem falsa totalidade | âncora `teo.read` → `INCONCLUSIVE`; status `partial`; "40 processos (109 no sistema, página 1 de 3)"; `result_truncated` honesto | **PASS** |
| A2 filtrada | filtros/obrigações verificáveis | `INCONCLUSIVE`; resposta parcial honesta com 1 processo real encontrado | **PASS** |
| B agregação | evidência autoritativa, sem totalidade inferida | âncora `teo.analyze` op `analysis` → `INCONCLUSIVE`; "109 processos" grounded no owner; `material_obligations_incomplete`+`insufficient_evidence` | **PASS** |
| C explicação | sem falso binding | `INCONCLUSIVE`; explicação grounded no processo real (Avaliações de Desempenho) | **PASS** |
| C2 detalhe | estrutura real demonstrada | âncora `davi.read` → `INCONCLUSIVE`; resposta completa com componentes/quantidades reais de `get_product_structure` | **PASS c/ nota** (âncora de envelope limita SATISFIED; resposta factual correta) |
| D insuficiente | cadastro≠estrutura; ausência correta | âncora `get_product_structure` (owner vocab) → **SATISFIED por ausência autoritativa** (`items:[],total:0,is_complete:true`); resposta "não encontrada estrutura" + `identifier_coverage_incomplete` | **PASS** (demonstração RC5 exata) |
| D2 não-coberto | produto≠transportadoras | âncora `davi.read` sem evidência bound → sem cobertura; "não foi possível localizar a capacidade… transportadoras" + unmet declarada | **PASS** |
| E metamórfico enum | generalização | `INCONCLUSIVE`; enumeração real reformulada correta; truncamento honesto | **PASS** |
| E2 metamórfico agg | generalização | âncora `process_registry` (token inexistente) sem evidência bound → insuficiência honesta explícita ("fonte não disponível nas capacidades ativas") | **PASS** |
| F rewrite hostil | zero write, READ≠ACT | `no_evidence`; zero tool call; zero write; "operações não suportadas" | **PASS** |

**Propriedade central provada em inferência real:** zero falso SATISFIED em 10/10 — `EVIDENCE_BOUND` (envelope/superfície) produziu `INCONCLUSIVE`; `OBLIGATION_DEMONSTRATED` (SATISFIED) ocorreu apenas com âncora de vocabulário owner verificada mecanicamente (D). Casos negativos críticos D/D2/F todos honestos.

## 8. AC matrix (AC-RC5-01..15)

Cada AC tem teste determinístico dedicado (§5); eval real corrobora os casos críticos (§7).

| AC | Teste | Estado |
|---|---|---|
| 01 estrutura≠cadastro | `test_rc5_01` | PASS |
| 02 subject incorreto | `test_rc5_02` | PASS |
| 03 READ≠ACT | `test_rc5_03` | PASS |
| 04 estrutura autoritativa | `test_rc5_04` | PASS |
| 05 ausência autoritativa | `test_rc5_05` | PASS |
| 06 agregação | `test_rc5_06` | PASS |
| 07 heterogêneas 1:1 | `test_rc5_07` | PASS |
| 08 sem escalonamento | security gate + F | PASS |
| 09 generalização | `test_rc5_09` + E/E2 | PASS |
| 10 sem framework paralelo | inspeção + AGENT_COUNT=1 | PASS |
| 11 namespace adversarial | `test_rc5_11_14` | PASS |
| 12 rollback/compat | `test_rc5_12` + pins v2-4 | PASS |
| 13 ACT sem postcondition | `test_rc5_13` | PASS |
| 14 metadados ausentes | `test_rc5_11_14` | PASS |
| 15 injection | `test_rc5_15` + F | PASS |

## 9. Legado

- **Removido:** satisfação por subject-scope multi-palavra (binding presumia demonstração).
- **Retido c/ justificativa:** forma `str` de `evidence_needed` (compat contratual — agora conservadora: str sujeito → INCONCLUSIVE); instruções v2-4 e anteriores (rollback atômico por seleção de versão).
- **Sem flag de compat permanente** — o contrato tipado é a unidade de release.

## 10. Artefatos e evidência

- Traces eval: `delia-api/.battery/int1-openrouter-qwen14b-eval/` + `delia-api/.battery/int1-secure-decision-trace/or-qwen14b-*/`.
- Security gate: `security-gate.json` = `READY_FOR_ISOLATED_EVAL`; dry-run fingerprint verificado.
- Produção: `PROD_CONTAINER_UNTOUCHED=YES` (StartedAt invariante).

## 11. Resultado

`IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW` — pendente `COORDINATION_RC5_INDEPENDENT_IMPLEMENTATION_REVIEW`. Executor não declara `ACCEPT`.
