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

### B1. Linha do tempo e árvore implantada

- Baseline produtivo (código ativo): `7f332cb39b4bc480ef973bfee2e2cdd9e29a9589` (ancestral do release).
- `origin/main` avançou durante a operação com commits **docs-only** (`b8a31f8c12` + `b3610405ca`/`b8a31f8c` family) — delta de código **zero** nos 4 serviços vs. release congelado; árvore de deploy efetiva em srv-api: `b8a31f8c12` (código ≡ release `b2a26867aa`/`413baef618` para os 4 serviços).
- **Fora de escopo:** `ef2ea358f2` (`fix(api-delpi) SEC-01 B` — task SEC-01) chegou a `main` **após** o build do `api-delpi`; imagem deployada **não** o contém. Deploy dele exige autorização da task SEC-01 — registrado como dependência externa, não bloqueador INT-1.
- Deploy executado em srv-api via `git pull --ff-only` + `infra/scripts/up-prod-sequential.sh --build <serviço>`, sequencial.

### B2. Registro por serviço

| Serviço | Imagem anterior | Imagem deployada | Estado pós-deploy |
|---|---|---|---|
| `api-delpi` (DAVI) | `sha256:a674524ce866` | `sha256:ee93e690be03` | running + **healthy** (17:18:52Z) |
| `transformometro-api` (TÉO) | `sha256:8ac6b818d3bf` | `sha256:0efc4789be3c` | **running** (sem healthcheck definido) |
| `tv-dashboard-api` (VISTA) | `sha256:a3117baf67dd` | `sha256:93023650be35` | **running** (sem healthcheck definido) |
| `delia-api` (DÉLIA) | `sha256:7e2516414dff` | `sha256:10e37b62cca0` | running + **healthy** (17:22:58Z) |

- `SERVICES_DEPLOYED=api-delpi,transformometro-api,tv-dashboard-api,delia-api`
- `SERVICES_NOT_DEPLOYED=core-api,keycloak,gateway,portal,MFEs,plugins` (sem dependência material)
- `DEPLOY_START≈17:05Z` · `DEPLOY_END≈17:23Z` (UTC, 2026-11-13)
- `PREVIOUS_IMAGE_IDS`/`DEPLOYED_IMAGE_IDS` conforme tabela — rollback por serviço = re-tag/start da imagem anterior (imagens anteriores preservadas no host).
- `PREDEPLOY_HEALTH=PASS` · `POSTDEPLOY_HEALTH=PASS` · `ROLLBACK_READY=YES` · `ROLLBACK_REQUIRED=NO` · `ROLLBACK_EXECUTED=NO`
- Source revision deployada: árvore `b8a31f8c12` (≡ código do release congelado para os 4 serviços). Labels OCI `image.revision` ausentes nas imagens — revisão registrada por evidência de checkout+build.

### B3. Contratos e autorização pós-deploy

- MCP `tools/list` **200** nos três owners via cadeia real: subject token (`delpi-central` password grant, usuário prod real) → RFC 8693 exchange (`delia-api`, `audience=<owner client>`, `scope=openid profile email mcp:tools`) → POST `/mcp` com `Host: minhadelpi.com.br`.
- Token delegado carrega aud resource-bound correto (`https://minhadelpi.com.br/apps/<owner>/mcp`) + `mcp:tools`; token bruto do subject é rejeitado (401) — binding de recurso intacto.
- `MCP_CONTRACT_VALIDATION=PASS` · `AUTHORIZATION_VALIDATION=PASS` · `CORE_AUTHZ=LIVE` · `DOMAIN_AUTHORITY=LIVE`.
- `DELIA_RUNTIME_PROFILE` produtivo = `openrouter_kimi` (env ops) — **divergência documentada** vs. perfil homologado `openrouter_qwen` usado na validação (eval isolado); decisão de troca do serviço produtivo é externa a esta task.

### B4. Incidentes de validação resolvidos (evidência de root cause)

1. Eval `or-qwen14b-8452861edcf1`: `catalog_failure:mcp_authentication_failed` ×3 — `DELIA_MCP_*_HOST_HEADER=localhost:8000` (layout dev) vs. owners prod exigindo `minhadelpi.com.br` (HTTP 421). Fix: `DELIA_EVAL_*_HOST_HEADER` parametrizável (`c774b45655`).
2. Eval `or-qwen14b-437190d79b8a`: mesma falha — root cause 2: `KEYCLOAK_ISSUER=http://localhost/...` vs. `iss=https://minhadelpi.com.br/auth/realms/delpi` produtivo → `token_validator` rejeitava o token delegado (fail-closed correto). Fix: `DELIA_EVAL_KEYCLOAK_ISSUER`/`DELIA_EVAL_KC_GATEWAY_TOKEN_BASE` parametrizáveis (`50d107b3ba`).
3. Respostas "insufficient/non-grounded" dos evals 1–2 foram **honestas** (sem fabricação) — comportamento fail-safe validado.

## PARTE C — Validação produtiva P1/P2/P3 (preenchida após deploy)

Eval produtivo real: **`or-qwen14b-49cc26d53beb`** — container isolado na rede prod, perfil homologado `openrouter_qwen`/`qwen3-14b`, owners produtivos, `PROD_CONTAINER_UNTOUCHED=YES`, 14 cenários / 13 model calls.

### C1. Superfície elegível

`eligible_specialists=['mcp']` · `function_tool_count=15` (12 MCP caps `davi|teo|vista.{get_context,read,analyze,knowledge}` + 3 ferramentas internas) — discovery real via Core eligibility + owner `tools/list`.

### C2. Outcomes por cenário

| Cenário | Status | Grounding | Invokes MCP | Outcome |
|---|---|---|---|---|
| **P1** product 90260921 | complete | GROUNDED | get_context+read×2 | Estrutura real: Chicote de Ligação (PA), componente 10020003 CABO PVC 175m — `REAL_STRUCTURE_RETURNED=YES` |
| **P2** processos cadastrados | complete | GROUNDED | read | PROC-0001 retornado + limitação honesta declarada (termo 'transformação') — `AUTHORIZED_RECORDS_RETURNED=YES` |
| **P3** formatos de visualização | complete | GROUNDED | read | Catálogo autoritativo: auto/bar_chart/chart/kpi/line_chart/table + tipos de bloco — `AUTHORITATIVE_CATALOG=YES` |
| AUTH_DENY | complete | GROUNDED | get_context×2+read×2 | Subject é superadmin — autorizado; outcome correto (não-denial é a verdade) |
| PARTIAL_AUTHZ | partial | GROUNDED | read×2 | PROC-0034 parcial — semântica partial honesta |
| P2_explicit_filter | partial | GROUNDED | read | Filtro explícito honrado (1 processo 'qualidade') — `UNREQUESTED_FILTER=NO` |
| G1/M1/IG1 | complete | GROUNDED | read | Re-wording/metamórficos — mesma estrutura 90260921 |
| R2 by-title | complete | GROUNDED | read×3 | Árvore real 'Avaliações de Desempenho' |
| R3 ambiguous-name | clarification | NON_GROUNDED | read | Pedido de clarificação honesto — sem fabricação |
| IG3 stock | complete | GROUNDED | read | Estoque real 90260148=0 (Branch 01/Arm 01) |
| IG4 item-tree | partial | GROUNDED | read | 90264135 parcial declarado — honesto |

### C3. Veredito produtivo

```text
PRODUCTION_TECHNICAL_HEALTH=PASS
PRODUCTION_INTEGRATION_HEALTH=PASS   (exchange+mcp:tools+tools/list 200 ×3 owners)
PRODUCTION_BUSINESS_OUTCOME=PASS     (P1/P2/P3 GROUNDED com evidência real)
PRODUCTION_VALIDATION=PASS           (três níveis comprovados; requer aceite independente da coordenação)
```

Limitações honestas observadas: `coverage_unknown`, `result_truncated` (P3), `tool_calls_limit_reached` (R3) — semântica preservada e declarada, não mascarada.

---

`INT1_ENGINEERING_ACCEPTANCE=ACCEPT` · `PRODUCTION_DEPLOY=AUTHORIZED_FOR_INT1_SCOPE` · `PHASE_ADVANCEMENT=NO` · `INT2/INT3/T3=NOT_AUTHORIZED`
