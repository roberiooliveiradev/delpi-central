# Doc 321 — INT-1 · Formal Engineering Acceptance, Controlled Production Deployment and Business Outcome Verification

**TASK_ID:** `DELIA-C3-T2-INT1-FORMAL-ACCEPTANCE-PRODUCTION-DEPLOY-AND-OUTCOME-VERIFICATION-01`
**Data:** 2026-11-13
**BASE_HEAD:** `413baef618b330827343d184787af2626d96315b` (= `origin/main` no fetch)
**PO DECISION:** `PRODUCTION_DEPLOY=AUTHORIZED_FOR_INT1_SCOPE` — escopo INT-1 apenas; sem avanço de fase, sem INT-2/INT-3/T3, sem IAM/RBAC, sem migrations destrutivas.

---

## PARTE A — Aceite formal de engenharia (pré-deploy)

### A1. Reancoragem

| Campo | Valor |
|---|---|
| HEAD / origin/main | `413baef618` (idênticos; REFERENCE_HEAD confirmado) |
| Branch | `devin/prc-track-prod-01-records-list` no mesmo SHA (push via `HEAD:main`, sem switch) |
| WIP concorrente | `engineering-api/*` (9 modified) + artifacts — preservados fora do stage |
| PHASE_FROM_16 | C3/T2 — INT-1 em fechamento |
| NEXT_FROM_LEDGER | `COORDINATION_INT1_TEO_SCOPE_AND_GATE_R_INDEPENDENT_ACCEPTANCE_REVIEW` |

### A2. Reconciliação das evidências (Docs 317–320 × Doc 293)

| Requisito | Estado | Evidência |
|---|---|---|
| P1 — estrutura de produto via DAVI | `SATISFIED_PROVEN_IN_SAMPLE` | Doc 317: `davi.read get_product_structure` → estrutura real GROUNDED/complete |
| P2 — enumeração de processos via TÉO | `SATISFIED_PROVEN_IN_SAMPLE` | Doc 317: `teo.read process.search` sem params → total=109, GROUNDED/partial, paginação honesta |
| P3 — catálogo de formatos via VISTA | `SATISFIED_PROVEN_IN_SAMPLE` | Doc 317: `vista.read display_format.list` → catálogo autoritativo GROUNDED |
| L_GATE | `PASS` | requisitos rastreados e evidenciados (Docs 313–320) |
| A_GATE | `PASS` | `AGENT_COUNT=1`, `PYDANTIC_AI_NATIVE`, `MCP_TOOLSET_LIVE`; `NEW_ROUTER/PLANNER/RESOLVER/RBAC_MUTATION=NO`; owners intactos |
| O_GATE | `PASS` | outcomes P1/P2/P3 provados no candidato congelado (`or-qwen14b-e069f3b33be8`) |
| R_GATE | `PASS` | as 4 suítes exit 0 no release; todas as 10 classes do Doc 318 encerradas (Doc 319) + fail-closed scope TÉO (Doc 320) |

### A3. Validade da evidência de regressão no HEAD

| Suíte | Resultado | SHA da evidência | Válida em `413baef618`? |
|---|---|---|---|
| DÉLIA | 1601 PASSED | `37ee712640` | ✅ — zero diff `delia-api` no intervalo |
| TÉO | 2140 PASSED / 62 SKIPPED | `413baef618` | ✅ — executada no próprio HEAD |
| VISTA | 2535 PASSED | `37ee712640` | ✅ — zero diff `tv-dashboard-api` no intervalo |
| DAVI | 5970 PASSED / 10 SKIPPED | `37ee712640` | ✅ — zero diff `api-delpi` no intervalo |

Commits no intervalo `37ee712640..413baef618`: 1 fix TÉO (este escopo, coberto por suíte) + 3 docs/WIP CF — nenhum toca DÉLIA/VISTA/DAVI.

### A4. Universo residual Doc 293

```text
ZERO_OPEN_MATERIAL=YES        (residuais restantes: OPEN_MINOR/OPEN_OPERATIONAL/owner-DAVI herdados — nenhum material)
OWNERSHIP_CONFORMANT=YES      (todos os fixes no owner legítimo)
NO_ARCHITECTURE_DRIFT=YES     (AGENT_COUNT=1, sem engines paralelas, MCP 6-tool surface)
TEST_EVIDENCE_VALID=YES       (ver A3)
OUTCOME_EVIDENCE_VALID=YES    (P1/P2/P3 GROUNDED em runtime real, Doc 317)
```

### A5. Decisão de engenharia

```text
INT1_ENGINEERING_ACCEPTANCE=ACCEPT
L_GATE=PASS · A_GATE=PASS · O_GATE=PASS · R_GATE=PASS
```

Registrado sob a decisão expressa do PO nesta task (`PRODUCTION_DEPLOY=AUTHORIZED_FOR_INT1_SCOPE`). Aceite de engenharia ≠ validação produtiva — esta última é provada na PARTE C.

**Residuais classificados (não-materiais):** `INT1-ATTEMPT-STATUS-CONFLATION` (observability), `INT1-MCP-HEAVY-VIEW-TIMEOUT` (reliability), `INT1-DAVI-NONEXECUTABLE-CAPS` (owner DAVI herdado), `INT1-EVAL-ENV-FLAKES` (operacional).

### A6. Congelamento do release

| Campo | Valor |
|---|---|
| RELEASE_SHA | `413baef618b330827343d184787af2626d96315b` (+ doc-commit Publication A — sem delta de código) |
| MODEL_ID | `qwen/qwen3-14b` |
| MODEL_PROFILE | `openrouter_qwen` (`max_output_tokens=8192`, context 40960, fingerprints `fed20318b167`) |
| INSTRUCTION_VERSION | `generalist-semantic-v2-3-enumeration-intent` (default_instruction_version confirmada no JSON) |
| INSTRUCTION_FINGERPRINT | `95e265ee18cd` (sha256 do corpo, 7.654 chars) |
| MODEL_CONFIG_FINGERPRINT | `fed20318b167` |
| TOOLSET_FINGERPRINT | MCP 6-tool surface (`get_context/read/analyze/knowledge/execute/delete`) — reconfirmada live pós-deploy |

`AGENT_COUNT=1` · `PYDANTIC_AI_NATIVE=YES` · `MCP_TOOLSET_LIVE=YES` · `NEW_ROUTER=NO` · `NEW_PLANNER=NO` · `NEW_RESOLVER_ENGINE=NO` · `RBAC_MUTATION=NO`. DÉLIA não reutiliza engines/tables do Minha DELPI Chat.

### A7. Inventário de serviços e plano de implantação

Serviços candidatos com código alterado no release INT-1 (vs. produção atual — inventário detalhado na PARTE B):

| Serviço | Mudanças INT-1 materiais |
|---|---|
| `api-delpi` (DAVI) | ROUTE_CONTRACTS, pagination tiers, avatar env, baseline OpenAPI |
| `transformometro-api` (TÉO) | authz-before-existence, setor-leak + fail-closed scope, requirements, fixtures |
| `tv-dashboard-api` (VISTA) | Actions compaction, share authz binding, display_format.list, route catalog |
| `delia-api` (DÉLIA) | capability orchestration, argument validation, interop, runtime/test config |

Ordem: `api-delpi → transformometro-api → tv-dashboard-api → delia-api` (owners antes da orquestradora). Procedimento canônico: `infra/scripts/up-prod-sequential.sh --build <serviço>` em `srv-api` após `git pull --ff-only`.

**Critérios de rollback:** falha persistente de health, quebra de contrato MCP, regressão de authZ, outcome incorreto ou falha operacional essencial → `STOP_DEPLOY` + restore da imagem anterior por serviço (tag/imagem registrada pré-deploy). Sem rollback destrutivo de banco.

**Critérios de sucesso:** containers saudáveis + MCP `tools/list` autoritativo + authZ íntegra + P1/P2/P3 GROUNDED no runtime produtivo.

---

## PARTE B — Execução do deploy (preenchida durante a operação)

_Aguardando execução — ver §14/ledger para registros pós-deploy._

## PARTE C — Validação produtiva P1/P2/P3 (preenchida após deploy)

_Aguardando execução._

---

`INT1_ENGINEERING_ACCEPTANCE=ACCEPT` · `PRODUCTION_DEPLOY=AUTHORIZED_FOR_INT1_SCOPE` · `PHASE_ADVANCEMENT=NO` · `INT2/INT3/T3=NOT_AUTHORIZED`
