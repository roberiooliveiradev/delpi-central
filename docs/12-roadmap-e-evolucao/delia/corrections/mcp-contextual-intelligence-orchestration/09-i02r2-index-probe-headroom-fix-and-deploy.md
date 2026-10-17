# 09 — I02-R2 Index Probe Headroom Fix and Governed Deploy

**DATA:** 2026-10-17  
**TASK_ID:** `DELIA-C3-MCP-I02-R2-INDEX-PROBE-HEADROOM-FIX-AND-DEPLOY-01`  
**BASE_HEAD:** `0ed816702adf3ce4aecd572a7aef29b0479c5511`  
**CODE_COMMIT:** `4a8e4d1881957833ecce36d10344d4900f7087ed`  
**DEPLOYED_SHA:** `4a8e4d1881957833ecce36d10344d4900f7087ed`  
**MODEL:** `moonshotai/kimi-k3` (`LLM_PROVIDER=openai_compatible`)  
**CONFIG_FINGERPRINT:** `dd51e9912270e46b`  
**I02_ACCEPTED:** `NO` (candidato para revisão independente)

## 1. Baseline / CP-RQ

Reancoragem: authorities 16→50→17→49→51→52→21→20→25 + docs 05–08 + ledger §§6.243–6.246.  
CP/RQ materiais (doc 25 / trilha I02): orçamento global 30s, grounding owner-first, MESSAGE≠ACT, provider-neutral, sem prosa factual livre do modelo.

```text
EXISTING_EQUIVALENT=YES
REUSE_DECISION=EXTEND
GLOBAL_TURN_BUDGET_SECONDS=30
NEW_PLANNER=NO
NEW_MEMORY_ENGINE=NO
PUBLIC_CONTRACT_CHANGED=NO
```

## 2. Causa raiz confirmada

Classe K3 (doc 07/08, SHA `abc6e28e…`): após group/capability/goal/native (~10s), `self_index_eligible` disparava `_propose_index_probe` (modelo). Em VISTA, a descrição MCP em português («Sem topic: índice…») **não** batia no detector EN-only de omit→index, forçando a 5ª chamada de modelo (~19s) e `model_timeout` antes de qualquer owner READ.

```text
ROOT_CAUSE_CONFIRMED=YES
CRITICAL_PATH=optional_model_index_probe_before_owner_READ
OWNER_CONTRACT_PT_MISS=PROVEN
```

## 3. Teste RED

`delia-api/tests/test_i02r2_index_probe_headroom.py` (antes do fix):

| Cenário | Resultado RED |
|---|---|
| Descrição PT VISTA → contrato omit→index | FAIL (`False`) |
| Remaining &lt; headroom derivado → probe não inicia | FAIL (probe iniciado) |
| Contrato + budget apertado → INDEX sem modelo | FAIL |
| Identificador inventado pós-skip | FAIL (READ com inventado) |

## 4. Solução (diff mínimo)

Arquivo: `delia-api/app/application/capability_provision/orchestration.py`

1. **`_contract_declares_omit_returns_index`** — sinais PT (`omitir`/`sem ` + `índice`/`lista de`) sem hardcode de field/provider.
2. **`_budget_allows_optional_index_probe`** — headroom derivado:  
   `2 × model_stage_timeout + MIN_VIABLE_MODEL_STAGE_SECONDS × 3`  
   (probe + index_select + piso de apresentação já usado em síntese/resolver). Não amplia o teto global de 30s.
3. **Call site self-index** — contrato owner ⇒ INDEX READ sem modelo; senão probe só se headroom; senão `skip_budget` e clarificação (não apresentar `{}`/índice como orientação).
4. Timeout global esgotado permanece terminal (sem catch para continuar READ).

## 5. Testes GREEN / regressão

| Suite | Resultado |
|---|---|
| `test_i02r2_index_probe_headroom.py` | PASS |
| I02-R1 characterization (timeout path com remaining ≥ floor) | PASS |
| I01 + I02 + `test_mcp_iterative_index_probe` | PASS |
| `delia-api` full pytest | PASS |

## 6. Deploy governado

```text
TARGET=operador@192.168.1.237 (srv-api)
PROCEDURE=git pull --ff-only origin main
         + ./infra/scripts/up-prod-sequential.sh --pull --build delia-api
DEPLOY_AUTHORIZATION=task user request + local-first-deploy
DEPLOY_RESULT=PASS
HOST_HEAD=4a8e4d1881957833ecce36d10344d4900f7087ed
HEALTH=/apps/delia-api/health → 200 available
CONTAINER_MARKERS=_budget_allows_optional_index_probe=True; PT_CONTRACT=True
```

## 7. Live (máx. 3 turnos, sem retry de PASS)

### K3 — VISTA (corr. `7710a711-1803-4a41-a8cf-28af4843d25e`)

| Campo | Valor |
|---|---|
| SELECTED | `mcp:vista` / `get_product_guide` |
| INDEX_PROBE_MODEL | **NO** (contrato PT → INDEX READ direto) |
| INDEX_READ | YES (`provider_invoke` arg_keys vazio, 11 identifiers, 29ms) |
| INDEX_SELECT | YES (bound `topic`, 8213ms) |
| OWNER_GUIDANCE_READ | YES (`arg_keys=topic`) |
| SYNTHESIS | `deterministic_guidance` |
| NESTED_GUIDANCE | YES (`purpose` / `use_when` / `how_to_use` / `do_not_use_when` no content) |
| SELECTED_TOPIC | `display_formats` (Formatos de exibição) |
| TOPIC_RELEVANCE | PARTIAL (formatação ≠ legibilidade de painel completa) |
| LATENCY_MS | 28532 (&lt; 30s) |
| GROUNDING | GROUNDED |
| RESULT | PASS_WITH_LIMITATION (orçamento+READ+nested OK; relevância de tópico residual) |

### K1 — TÉO (corr. `ab0b61a9-cfff-4ef2-abf9-dbc593c793c9`)

Selecionou `with_discovery` → `teo.get_catalog` OK → plano `get_methodology_guide` → `model_timeout` 30014ms; `delpi_source_unverified`. **FAIL** (classe pré-síntese TEO, fora do gate de index_probe VISTA).

### K2 — follow-up (corr. `8ce1c81e-63ea-4f12-b408-c97b6b44b637`)

Sem evidência útil de K1; timeout 30013ms; literal replay da mensagem de fonte não verificada. **FAIL** / continuidade **NOT_PROVEN**. Sem inventar contexto K1.

```text
UNAUTHORIZED_MATERIAL_ACT_COUNT=0
MAX_OBSERVED_LATENCY_MS=30014
GLOBAL_TURN_BUDGET_SECONDS=30
MODEL_AUTHORED_FACTUAL_PROSE=NONE
```

## 8. Critérios candidatos

| Critério | Veredito |
|---|---|
| INDEX_PROBE_HEADROOM | PASS |
| OWNER_INDEX_CONTRACT_PRESERVED | PASS |
| SCHEMA_VALIDATION | PASS |
| GLOBAL_DEADLINE_PRESERVED | PASS |
| NO_SYNTHETIC_IDENTIFIER | PASS (testes) |
| BACKEND_FULL_TESTS | PASS |
| DEPLOYED_SHA_VERIFIED | YES |
| K3_OWNER_READ_REACHED | YES |
| K3_NESTED_GUIDANCE_PROJECTED | YES |
| K3_RESPONSE_USEFUL | PASS_WITH_LIMITATION |
| K1_RESPONSE_USEFUL | FAIL |
| K2_CONTINUITY | FAIL |

## 9. Residuais / próximo passo

- Latência pré-owner TEO (K1/K2) ainda esgota 30s intermitentemente — fora do escopo mínimo do headroom de index_probe.
- Seleção de tópico VISTA (`display_formats` vs legibilidade) — I03/qualidade de index_select.
- `DELIA_MODEL_STAGE_TIMEOUT_SECONDS=30` no runtime amplia o floor do probe opcional; em produção o caminho contrato-first é o que desbloqueou K3.

```text
I02_RECOMMENDATION=ACCEPT_WITH_RESIDUAL_CANDIDATE
I02_ACCEPTED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
NEXT=INDEPENDENT_I02_R2_ARCHITECTURE_AND_DEPLOY_REVIEW
```
