# 13 — I02-R3 · Evidências, dependências e recomendação do consultor

**DATA:** 2026-10-19  
**TASK_ID:** `DELIA-C3-MCP-I02-R3-TEO-PREOWNER-LATENCY-DIAGNOSTIC-01`  
**BASE_HEAD:** `f9bc8399619d2b929ff30f7d7f9428a77387e516`  
**EVALUATED_SHA (código local/testes):** `f9bc8399619d2b929ff30f7d7f9428a77387e516` (+ testes de caracterização deste relatório)  
**DEPLOYED_SHA (runtime live, sem redeploy nesta task):** host `13167e6efc…` / imagem com fix I02-R2 (`4a8e4d1881` ancestral)  
**MODEL:** `moonshotai/kimi-k3` · `DELIA_MODEL_STAGE_TIMEOUT_SECONDS=30` · `DELIA_TURN_BUDGET_SECONDS=30`  
**CONFIG_FINGERPRINT (R2):** `dd51e9912270e46b` (runtime env revalidado; fingerprint regenerado não recalculado nesta task)  
**I02_ACCEPTED:** `NO`  
**SOURCE_CODE_CHANGED:** `NO` (somente testes de caracterização + docs)  
**PERFORMANCE_FIX_IMPLEMENTED:** `NO`  
**DEPLOY_PERFORMED:** `NO`

## 1. Reancoragem e CP/RQ

- `git` sincronizado em `f9bc839961`; working tree concorrente preservada (`plugins/delia/…`, `plugins/plugin-ui/docs/…`).
- Lidos: docs 07–12, README da trilha, ledger §§6.245–6.250, `orchestration.py` / `turn_budget.py`, autoridades 25 (CP-055, CP-094, CP-130/134, CP-263, CP-270, CP-330).
- Invariantes: `GLOBAL_TURN_BUDGET_SECONDS=30`, `MESSAGE≠ACT`, `MODEL_OUTPUT≠FACT`, `MCP_METADATA≠AUTHORITY`, sem planner/memória/novo engine.
- `EXISTING_EQUIVALENT=YES`; `REUSE_DECISION=EXTEND_CANDIDATE` (headroom/telemetria já existentes).

## 2. Gate A — Traces causais

### 2.1 K1 FAIL histórico I02-R2 — `ab0b61a9-cfff-4ef2-abf9-dbc593c793c9`

Fonte: logs `delpi-delia-api` (retenção ≥72h). **Medido** (não inferido).

| STAGE | DURATION_MS | MODEL | OWNER | RESULT |
|---|---:|---|---|---|
| select_group | 7818 | YES | NO | ok |
| select_capability | 14897 | YES | NO | ok → `mcp:teo` / `get_methodology_guide` |
| turn_goal | 2775 | YES | NO | ok |
| native_assessment | 1880 | YES | NO | sufficient |
| plan | — | — | — | `with_discovery` / `get_catalog` |
| get_catalog DISCOVERY | 90 | NO | YES | ok |
| **(próximo)** | — | YES | NO | **sem `model_propose ok`** |
| turn_budget | — | — | — | **`model_timeout`** |

Soma pré-arguments ≈ 27460 ms → restante ≈ 2540 ms. Ausência de linha `arguments` ok + timeout imediato após catalog ⇒ estágio que falhou = **proposta de arguments** (classe confirmada; purpose explícito no fail live 2026-10-19).

### 2.2 K1 FAIL live desta task — `561bb788-5271-4ea8-8c35-80fa4d85d4bd`

| STAGE | DURATION_MS | MODEL | OWNER | RESULT | EVIDENCE |
|---|---:|---|---|---|---|
| select_group | 2284 | YES | NO | ok | medido |
| select_capability | **14778** | YES | NO | ok | medido |
| turn_goal | 7021 | YES | NO | ok | medido |
| native_assessment | 2398 | YES | NO | sufficient | medido |
| get_catalog | 151 | NO | YES | ok | medido |
| **arguments** | **3015** | YES | NO | **`error_code=timeout`** | **PROVEN** (`model_propose decision=error purpose=…arguments`) |
| turn_budget | — | — | — | `model_timeout` | medido |
| methodology READ | — | — | — | **NOT_REACHED** | — |

```text
K1_TIMEOUT_EXACT_STAGE=delia.capability_orchestration.arguments
K1_PREOWNER_MODEL_CALL_COUNT=5  (group, capability, goal, native, arguments*)
K1_PREOWNER_OWNER_CALL_COUNT=1  (get_catalog only; READ methodology=0)
*arguments iniciou e timeout; não completou
TOTAL_WALL≈30016ms
```

### 2.3 K1 SUCCESS histórico (doc 07) — `daccc948-ec34-4393-8a07-a96bdbf5b53a`

Executor-reported (logs não recuperáveis nesta retenção → `STALE_EVIDENCE` para reexecução independente; números do relatório 07 preservados):

| STAGE | DURATION_MS | MODEL | OWNER |
|---|---:|---|---|
| select_group | 4088 | YES | NO |
| select_capability | 2803 | YES | NO |
| turn_goal | 3146 | YES | NO |
| native_assessment | 1775 | YES | NO |
| get_catalog | 79 | NO | YES |
| arguments | ~5531 (inferido no 07) | YES | NO |
| get_methodology_guide | 39 | NO | YES |
| synthesis | deterministic | NO | NO |
| **Total** | **~17816** | | |

### 2.4 K3 controle live — `a83c6803-b3cb-45c9-b3c3-f96f20561696`

GROUNDED, `vista.get_product_guide`, INDEX owner sem model probe, index_select 2911ms, guidance READ, 15376ms. Regressão I02-R2 **PASS** neste turno. Topic `display_formats` permanece relevância PARTIAL (residual semântico, não latência).

### 2.5 Respostas obrigatórias

| Pergunta | Resposta | Classe |
|---|---|---|
| Qual chamada produziu o timeout? | `arguments` (`delia.capability_orchestration.arguments`) | **PROVEN** (live 561bb788) |
| Quantas chamadas de modelo antes do READ metodologia? | 4 completas + 1 arguments falha; owner DISCOVERY 1 | PROVEN |
| Repetição de interpretação? | Goal e capability são campos distintos; duplicação semântica **não** comprovada como recomputação idêntica | TO_INVENTORY / B |
| Contexto maior que o necessário? | Arguments inclui schema + `owner_vocabulary` (até 14k chars bloco); custo de tokens **não** medido | TO_INVENTORY |
| Capability já dava o que o goal reusa? | Goal alimenta write-gate e native; capability não substitui goal | PROVEN no contrato |
| Native indispensável? | Só quando `len(groups)>1`; live multi-MCP ⇒ sempre roda; READ simples com `comparison_requested=false` é **candidato** a omissão com prova | CANDIDATE |
| Args determinísticos? | Schema vazio já evita modelo; envelope `context: object` força vocabulary + proposta | PROVEN |
| Owner rápido? | Catalog 90–151ms; methodology 39ms no sucesso | PROVEN |
| Tempo restante antes da falha? | ~2.5–3.4s | PROVEN |
| Config influenciou? | `DELIA_MODEL_STAGE_TIMEOUT_SECONDS=30` permite um estágio (ex. capability 14.8s) consumir quase metade do turno | PROVEN |

## 3. Gate B — Mapa de dependências

| Função | Inputs | Outputs | Downstream | Segurança | Custo observado | Omitível? |
|---|---|---|---|---|---|---|
| `_select_group` | user + summaries | `provider:group` | capability | revalida contra surface | 2–8s | só se 1 grupo (já short-circuit) |
| `_select_capability` | user + group surface | remote_name | goal (se ainda não), native, plan | revalida; write demote depois | **2–15s (alta variância)** | não sem consolidação C |
| `_understand_goal` | user (+ prior se multiturn) | class/subject/prior/comparison/bound | write-gate, native, args, continuity | **write intent independente** | 2–9s | não fundir cegamente com selection |
| `_assess_native_path` | só surface do grupo alvo + goal | sufficient / foreign_required / corroboration | foreign select | isolamento foreign | 1.7–5s | **candidato D** se READ∧¬comparison∧prova |
| owner DISCOVERY | args discovery (geralmente `{}`) | vocabulary evidence | `_build_arguments` | untrusted data | **&lt;200ms** | obrigatório se `_requires_owner_vocabulary` |
| `_build_arguments` | schema + evidence + subject | validated args | READ | schema + unproven-id | **~3–6s ou timeout** | E se schema/`{}`/enum owner comprovado |
| owner READ | args | SpecialistOutcome | synthesis | owner authority factual/guidance | **&lt;50ms** | objetivo do turno |
| `_synthesize_content` | outcome | content | user | deterministic guidance preferido | ~0 model no path R2 | — |

```text
DEPENDENCY_CHAIN (TEO methodology K1):
  select_group → select_capability → turn_goal → native_assessment
  → DISCOVERY(get_catalog) → arguments(model) → READ(get_methodology_guide)
  → synthesis
```

**Não** há evidência de segundo planner paralelo. Paralelizar group/capability/goal/native **REJECT** como primeiro fix (native depende de seleção; write-gate depende de goal).

## 4. Gate C — Testes

Arquivo: `delia-api/tests/test_i02r3_teo_preowner_latency_characterization.py`

| Caso | Resultado |
|---|---|
| Ordem K1 success (fake) + opaque schema ⇒ discovery | PASS |
| Arguments timeout após discovery ⇒ só catalog, sem methodology READ | PASS |
| Timeout em select_capability ⇒ zero owner | PASS |
| Native skip com 1 grupo | PASS |
| Schema vazio ⇒ sem arguments model | PASS |
| MESSAGE≠ACT em timeout | PASS |
| Injection no catalog ≠ authority | PASS |
| Histórico forjado + prior_sufficient=false ⇒ owner consultado | PASS |
| Provider renomeado não-MCP | PASS |
| Regressão VISTA índice PT (R2) | PASS |
| Suíte I01/I02/R2 | PASS |
| `delia-api` full pytest | PASS |

```text
CHARACTERIZATION_TESTS=PASS
BACKEND_FULL_TESTS=PASS
SECURITY_REGRESSION=PASS (ACT=0 nos caminhos exercidos)
```

## 5. Gate D — Alternativas A–F

| ALT | EXISTING | BENEFÍCIO | MEDIDO? | MODEL_CALL_Δ | QUALITY/SECURITY | REUSE | RECOMENDAÇÃO |
|---|---|---|---|---|---|---|---|
| **A** Telemetria purpose/timing | logs `model_propose` | localiza estágio | **SIM** (esta task) | 0 | neutro | **REUSE** | **FAZER SEMPRE** (já suficiente para causa) |
| **B** Eliminar repetição | goal/selection single-pass | baixo se não houver dup | não provado dup idêntica | ? | — | INVENTORY | não priorizar |
| **C** Consolidar goal+capability | `_propose` tipado | −1 round-trip | não testado live | −1 est. | risco write-gate | CANDIDATE | só após contrato tipado + holdouts |
| **D** Native econômico | `len(groups)>1` gate | −1.8–5s | não A/B live | −1 | risco foreign/corroboration | CANDIDATE | elegibilidade formal READ∧¬comparison |
| **E** Args determinísticos | `{}` se schema vazio | poupa 3–6s / evita timeout | path vazio PROVEN; methodology envelope **não** vazio | −1 quando aplicável | inventário de ids proibido | REUSE + EXTEND se gap | após discovery, avaliar defaults/enum owner |
| **F** Custo inferência / stage cap | `MODEL_STAGE_TIMEOUT` default 10 vs env 30 | reduz cauda de capability 15s | config PROVEN | indireto | trade-off qualidade | EVALUATE | **alinhar stage cap** sem subir 30s global |
| G Paralelo | — | — | — | — | races/isolamento | **REJECT** | — |
| H Novo planner/cache | — | — | — | — | ownership | **REJECT** | — |

**SAFE_OPTIMIZATION_PROVEN:** nenhuma otimização funcional foi implementada; o que está **provado** é a causa e que owner MCP não é o gargalo.

## 6. Gate E — Live bounded

| Turno | Resultado |
|---|---|
| K1 | FAIL timeout 30016ms; stage=arguments; corr=`561bb788-…` |
| K2 | SKIPPED (sem inventar contexto após K1 fail) |
| K3 | PASS GROUNDED 15376ms; corr=`a83c6803-…`; R2 estável |
| ACT | 0 |
| Deploy | não realizado |

## 7. Recomendação para a coordenação

### Causa raiz (classe)

```text
ROOT_CAUSE_CLASS=PROVEN
CRITICAL_PATH=sequential_pre_owner_model_stages
FAILING_STAGE=arguments_after_discovery
AMPLIFIER=select_capability_tail_latency (≈15s) + MODEL_STAGE_TIMEOUT_SECONDS=30
OWNER_MCP=NOT_THE_BOTTLENECK
```

### Combinação mínima candidata (não implementar aqui)

1. **F (config/contrato de estágio)** — reduzir/clamp `DELIA_MODEL_STAGE_TIMEOUT_SECONDS` efetivo para o default de código (10s) ou `min(configured, remaining_headroom)`, **sem** aumentar o teto global 30s.  
2. **Headroom pré-arguments (padrão I02-R2)** — não iniciar `_propose` de arguments se `remaining < stage_cap + MIN_VIABLE*3` (ou piso derivado); preferir clarificação / fail-closed honesto a um timeout terminal após DISCOVERY barato.  
3. **D (opcional, segundo)** — omitir `native_assessment` quando `goal_class=read` ∧ `¬comparison_requested` ∧ target READ/ANALYSIS, com testes de foreign_required/corroboration/multi-owner.  
4. **E (opcional)** — após catalog, se schema permitir `{}` validado para guidance metodológica sem free-string inventado, pular arguments model (só com prova de contrato owner).

```text
RECOMMENDED_SOLUTION=F_STAGE_CAP_ALIGN + ARGUMENTS_HEADROOM_EXTEND (I02-R2 pattern)
RECOMMENDED_METHODS_TO_CHANGE=_propose call-site for ARGUMENTS after discovery;
  settings/composition of model_stage_timeout; optional _assess_native_path eligibility
RECOMMENDED_MINIMAL_DIFF=no new planner; EXTEND TurnDeadline headroom + config clamp
RECOMMENDED_RED_GREEN_TESTS=
  - RED: remaining≈3s after catalog → arguments not started OR honest clarify (today starts→timeout)
  - GREEN: success path still reaches methodology READ under fake/live
  - sibling: VISTA R2 index path unchanged
  - negative: foreign_required / write-class / invented id / MESSAGE≠ACT
```

### Critérios de aceite da futura implementação

- K1 TÉO: owner methodology READ alcançado OU limitação honesta sem `model_timeout` opaco, p50/p95 com amostra adequada.  
- K2 continuity quando K1 útil.  
- K3 regressão R2.  
- ACT=0; budget global 30s; sem prosa factual livre do modelo.

### Rollback

Reverter commit de headroom/config; `DELIA_MODEL_STAGE_TIMEOUT_SECONDS` volta ao valor anterior via env versionado; redeploy canônico.

## 8. Residuais

- Variância do modelo em `select_capability` (2s–15s) sem contadores de tokens → TO_INVENTORY (F/observabilidade tokens).  
- Topic VISTA parcial.  
- Consolidação C goal+capability não provada.  
- Host deploy SHA ≠ HEAD documental desta task (sem deploy intencional).

```text
I02_RECOMMENDATION=ARCHITECTURE_DECISION_REQUIRED_ON_F+ARGUMENTS_HEADROOM
I02_ACCEPTED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
NEXT=I02_R3_COORDINATION_ARCHITECTURE_DECISION
```
