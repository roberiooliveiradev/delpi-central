# I02-R1 — Validação live pós-nested-fix e diagnóstico de latência pré-síntese

**DATA:** 2026-10-17
**TASK_ID:** `DELIA-C3-MCP-I02-R1-POST-FIX-VALIDATION-AND-LATENCY-DIAGNOSIS-01`
**BASE_HEAD:** `abc6e28e322b47bb4bb06e99c5c7463c52a23862`
**DEPLOYED_SHA:** `abc6e28e322b47bb4bb06e99c5c7463c52a23862` (contém `cc7d2c8e3ba0d70edd56088df72ee795976c2e2e`)
**MODEL:** `moonshotai/kimi-k3` (`LLM_PROVIDER=openai_compatible`)
**RUNTIME_CONFIG_FINGERPRINT:** `5062d3b7f10fecaa`
**SOURCE_CODE_CHANGED:** testes de caracterização apenas; **PERFORMANCE_FIX_IMPLEMENTED=NO**
**I02_ACCEPTED:** `NO` (permanece REWORK)

## 1. Gate A — Nested fix live (VISTA K3)

```text
ORIGIN_MAIN_SHA=abc6e28e322b47bb4bb06e99c5c7463c52a23862
DEPLOYED_DELIA_SHA=abc6e28e322b47bb4bb06e99c5c7463c52a23862
NESTED_FIX_COMMIT_PRESENT=YES (_GUIDANCE_NESTED_KEYS + skip_budget_deterministic no container)
```

**Turno único (MESSAGE):**

> Quero melhorar a apresentação visual de um painel no TV Dashboard. Que critérios devo considerar para escolher a visualização e evitar problemas de legibilidade?

| Campo | Valor |
|---|---|
| CORRELATION | `2687ac53-c152-42bd-ad13-2303c0e40162` |
| SELECTED | `mcp:vista` / `get_product_guide` |
| SELECTED_TOPIC | N/A — READ owner nunca executado |
| LATENCY_MS | 30024 |
| RESULT | `delpi_source_unverified` / NON_GROUNDED |
| OWNER_READ | NO |
| SYNTHESIS | NOT_REACHED |

### Cadeia de estágios (telemetria existente)

| STAGE | DURATION_MS | MODEL | OWNER | REQUIRED_FOR_GOAL |
|---|---:|---|---|---|
| select_group | 1637 | YES | NO | YES |
| select_capability | 3497 | YES | NO | YES |
| turn_goal | 2315 | YES | NO | YES |
| native_assessment | 2913 | YES | NO | YES |
| plan | — | — | — | `self_index_candidate` |
| **index_probe** | **19289 timeout** | **YES** | NO | TO_INVENTORY (topic bind) |
| turn_budget | terminal `model_timeout` | — | — | — |
| owner READ / synthesis / nested projection | — | — | — | **NOT REACHED** |

```text
GUIDANCE_ENVELOPE_PROJECTION=TEST_NOT_RUN
TOPIC_SELECTION_RELEVANCE=TEST_NOT_RUN
RESPONSE_USEFULNESS=FAIL
NESTED_FIX_LIVE_VALIDATED=INCONCLUSIVE
```

**Interpretação:** o SHA com nested fix estava implantado, mas o turno esgotou o orçamento no **modelo de `index_probe`**, antes de qualquer `SpecialistOutcome`. Portanto a correção de envelope aninhado **não foi exercitada** no runtime — não é PASS nem FAIL da projeção; é INCONCLUSIVE.

## 2. Gate B — Latência pré-síntese (K1 TÉO + contraste K3)

### 2.1 K1 reexecução (mesmo SHA/config)

| Campo | Valor |
|---|---|
| CORRELATION | `daccc948-ec34-4393-8a07-a96bdbf5b53a` |
| SELECTED | `mcp:teo` / `get_methodology_guide` |
| PLAN | `with_discovery` → `teo.get_catalog` |
| LATENCY_MS | 17816 |
| SYNTHESIS | `deterministic_guidance` |
| RESULT | GROUNDED; methods/when_to_use/invariants projetados |
| VERDICT | PASS_WITH_LIMITATION (sucesso neste SHA; falha anterior I02 permanece evidência histórica) |

#### Estágios K1 (sucesso)

| STAGE | DURATION_MS | MODEL | OWNER |
|---|---:|---|---|
| select_group | 4088 | YES | NO |
| select_capability | 2803 | YES | NO |
| turn_goal | 3146 | YES | NO |
| native_assessment | 1775 | YES | NO |
| get_catalog DISCOVERY | 79 | NO | YES |
| arguments (gap ~5531ms até built) | ~5531 | YES (inferido; sem linha model_propose dedicada no grep) | NO |
| get_methodology_guide READ | 39 | NO | YES |
| synthesis deterministic_guidance | ~0 model | NO | NO |

```text
K1_MODEL_CALL_COUNT_PRE_OWNER≈4 (+ arguments)
K1_OWNER_CALL_COUNT=2 (catalog + methodology)
K1_PRE_SYNTHESIS_LATENCY_MS≈17777
K1_FAILURE_STAGE=N/A_THIS_RUN (histórico I02: model_timeout pós-plan with_discovery)
```

### 2.2 Causa raiz comprovada (classe de falha)

```text
LATENCY_ROOT_CAUSE=PROVEN
CRITICAL_PATH=sequential_model_stages_before_owner_READ
```

**Cadeia causal (não apenas o sintoma):**

1. Quatro propostas de modelo (group → capability → goal → native) consomem ~10–12s.
2. Para VISTA `get_product_guide` (schema com string opcional, sem envelope DISCOVERY): `self_index_eligible=True` → `_propose_index_probe` (5ª chamada de modelo).
3. `index_probe` pode consumir o **restante quase inteiro do TurnDeadline** (observado 19289ms / timeout) e termina o turno com `turn_budget decision=model_timeout`.
4. Owner READ e síntese/nested projection **nunca iniciam**.
5. Timeout é de **invocação do modelo** sob deadline global 30s — não do MCP owner (owner nem foi chamado no K3 falho).
6. Catálogo TEO (`get_catalog`, 79ms) é barato quando o plano é `with_discovery`; o risco assimétrico está no **self-index probe model** (VISTA) e na soma das etapas modelo pré-READ.

**Respostas objetivas:**

1. Modelo antes do owner (K3 fail): **5** (group, capability, goal, native, index_probe).
2. Consultas MCP necessárias no fail: **0** executadas; READ planejado não ocorreu.
3. Redundante? Índice via modelo **após** capability já selecionada — necessário apenas se topic bind for obrigatório; não é necessário para provar nested projection de um READ já possível.
4. Catálogo TEO: sim, após capability determinada — mas é DISCOVERY owner barato, não segunda seleção semântica.
5. Seleção semântica: uma vez (group+capability); não repetida.
6. Modelo recebe schema/descrição no index_probe — limitado, não o guia completo.
7. READ K3: **não começou** (budget esgotado no probe).
8. Timeout: **modelo + deadline global**, não MCP.
9. Proposta index_probe: **não retornou** (timeout).
10. Mecanismos existentes: `TurnDeadline` headroom, fail-closed de `_propose_index_probe` (False quando proposal ausente), caminho `with_discovery` / direct — ver alternativas.

## 3. Alternativas avaliadas (sem implementar)

| ID | Alternativa | EXISTING_MECHANISM | OWNER | DECISION |
|---|---|---|---|---|
| A | Evitar re-seleção / reconsulta no mesmo turno | selection já single-pass | Application | REUSE — já em grande parte |
| B | Em timeout/ausência de probe, degradar para READ direto (sem topic) em vez de terminal timeout | `_propose_index_probe` já fail-closed em proposal ausente; **timeout hoje sobe `_StageDeadlineExceeded` e mata o turno** | Application | **EXTEND_CANDIDATE** |
| C | Reduzir projeção ao modelo no probe | block já bounded | Application | REUSE / baixo ganho vs 19s hang |
| D | Não iniciar index_probe se `remaining < headroom` (MIN_VIABLE×N + READ + synth) | `TurnDeadline.remaining_seconds`, padrão skip_budget síntese | Application | **EXTEND_CANDIDATE** (preferido com B) |
| E | Gap só no especialista | MCP index_probe é decisão DÉLIA | — | REJECT como causa única |

```text
RECOMMENDED_EXISTING_MECHANISM=TurnDeadline headroom + index_probe fail-closed degrade-to-direct-READ
RECOMMENDED_METHODS_TO_CHANGE=_propose_index_probe call site (~4277); optional catch of _StageDeadlineExceeded around probe to fall through (not widen timeout)
RECOMMENDED_MINIMAL_DIFF=before probe: if remaining insufficient → skip probe (False); on probe model_timeout → treat as probe=False and continue direct arguments/READ when schema allows empty-optional path; never raise turn-terminal solely because probe timed out when a non-index READ remains viable
RECOMMENDED_RED_GREEN_TESTS=test_index_probe_timeout_falls_through_to_owner_read (today RED via characterization); sibling with_discovery unchanged; negative: required-field schema still fail-closed; security MESSAGE≠ACT
```

**Não autorizada nesta task:** aplicar o patch. `IMPLEMENTATION_AUTHORIZED=NO`.

## 4. Testes desta task

| Item | Resultado |
|---|---|
| `test_i02r1_presynthesis_latency_characterization.py` | PASS — documenta fail-closed atual (probe timeout → zero owner calls) |
| Performance fix | NOT_IMPLEMENTED |
| MATERIAL_ACT | 0 |

## 5. Decisão / próximos passos

```text
GATE_A_NESTED_FIX=INCONCLUSIVE
GATE_B_PRE_SYNTHESIS_LATENCY=PROVEN

I02_ACCEPTED=NO
NEXT=I02_R2_BOUNDED_INDEX_PROBE_HEADROOM_AND_DEGRADE_TO_DIRECT_READ
+ re-live K3 nested projection after R2 (or dedicated nested-only path if READ obtainable without probe)
```

Residuais: nested fix ainda sem prova live de projeção; topic selection VISTA não avaliada; soma das 4 etapas modelo pré-owner permanece pressão estrutural (onda Q / I02-R2 scope check).
