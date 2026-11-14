# DÉLIA — Engineering Closure Residual Register (T0 Freeze)

**TASK_ID:** `DELIA-C3-ENG-CLOSURE-T0-BASELINE-RESIDUAL-FREEZE-01`
**DOC_AUTHORITY:** [293](../corrections/mcp-contextual-intelligence-orchestration/293-c3-four-gate-engineering-closure-finite-track.md) · plano mestre [256](../corrections/mcp-contextual-intelligence-orchestration/256-consolidated-native-pydantic-ai-legacy-cleanup-execution-master-plan.md)
**TYPE:** DOCUMENTATION / EVIDENCE / COORDINATION ONLY
**CODE_CHANGED:** NO · **TESTS_CHANGED:** NO · **PRODUCTION_DEPLOY:** NOT_AUTHORIZED
**FREEZE_UTC_DATE:** 2026-11-09

---

## 0. Reancoragem canônica

| Campo | Valor |
|---|---|
| `CURRENT_HEAD` | `54755b078aa8915fe28347850362d8a79f8721b7` |
| `ORIGIN_MAIN` | `54755b078aa8915fe28347850362d8a79f8721b7` (ff-only na T0) |
| `WORKTREE_STATUS` | limpo de diffs staged; untracked locais irrelevantes (`.battery/*/artifacts`, e2e artifacts de outros apps) — **não modificados** |
| `BRANCH` | `main` |
| `CANONICAL_REANCHOR` | HEAD → `.cursor`/instruções → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura → product spec → 256/293/ledger/backlog R01–R07 → matrix E2E |
| `CURRENT_PHASE` | Coordenação de fechamento engenharia **T0 Freeze** (doc 293). Marcadores históricos de `16` sob Product Master Option B permanecem supersedidos para sequência de feature; **esta trilha não avança C3/C4/C5**. |
| `CANONICAL_NEXT` | `T2_INDEPENDENT_REVIEW` — snapshot code retired; cadastro Core `BLOCKED_BY_OWNER_CONTRACT`; prod flag `PENDING_OPS`; T3 não autorizada |
| `APPLICABLE_CP_RQ` | Gates L/A/O/R do doc 293; CPs materiais de Evidence/Epistemic/MCP (ex. CP-093/094) permanecem PARTIAL históricos — **não reabertos** nesta T0 |
| `PYDANTIC_AI_VERSION` | `2.50.0` (`delia-api/requirements.txt`) |
| `RUNTIME_CONFIG_FINGERPRINT` | JSON runtime sha256 prefix `3836a5290ebf4372` (arquivo `pydantic_ai.runtime.delpi.json` no HEAD); profiles: `local_ollama` (default), `openrouter_kimi`, `openrouter_qwen` |
| `INSTRUCTION_VERSION` | `42` · fp prefix `8fed7885b7864b4b` (`orchestration_instructions.delpi.json`) |
| `LAST_ACCEPTED_CODE_SHA` (admission v42) | `d30a3acd21` (ancestral de HEAD) |
| `LAST_VERIFIED_E2E_SHA` | `dc491abd1e` (ancestral de HEAD; matrix `delia-api/.battery/r01-v42-e2e/matrix-summary.json`) |
| `DOC256_RECONCILED` | YES — G2 deleções `outcome_assessment`/`paginated_result_semantics` **CLOSED_PROVEN** no HEAD; G5 snapshot Protocol + C3-T5 KEEP; G8 histórico `ACCEPT_WITH_RESIDUAL` **não** equivale a L=A=O=R=PASS do doc 293 |
| `DOC293_RECONCILED` | YES — T0 produz este registro; gates permanecem **não aceitos** |
| `EXECUTION_LEDGER_RECONCILED` | YES — entradas R01 E2E + G0–G8 + remoções nativas consumidas; sem reabrir CLOSED sem evidência nova |

**Regra de evidência:** documentação histórica ≠ prova de HEAD. Itens `CLOSED_PROVEN` abaixo têm existência/ausência ou wiring verificados no `CURRENT_HEAD` ou SHA ancestral explícito. Itens sem prova diferencial = `TO_VERIFY` (não `CLOSED_PROVEN`).

---

## 1. Tabela consolidada (IDs estáveis)

| ID | Gate | Responsabilidade | Owner | Evidência | Status | Próxima etapa |
|---|---|---|---|---|---|---|
| L-01 | Legacy | `paginated_result_semantics.py` removido | DÉLIA capability_provision | HEAD ABSENT; delete `88a7c4e50c`; ledger G2 | `CLOSED_PROVEN` | — |
| L-02 | Legacy | `outcome_assessment.py` removido | DÉLIA capability_provision | HEAD ABSENT; delete `88a7c4e50c`; ledger G2 | `CLOSED_PROVEN` | — |
| L-03 | Legacy | Monólito `orchestration.py` removido / decomposto | DÉLIA capability_provision | ledger `LEGACY-ORCHESTRATION-REMOVAL…`; módulos `governed_capability_orchestrator` + `semantic_capability_support` | `CLOSED_PROVEN` | — |
| L-04 | Legacy | Adapter texto `openai_compatible_adapter` aposentado | DÉLIA model_invocation | ausente em `infrastructure/model_invocation/`; ledger runtime unificado | `CLOSED_PROVEN` | — |
| L-05 | Legacy | Busca residual: zero import vivo dos módulos deletados L-01/L-02 | DÉLIA QA | T1 SHA `d3a3d5ebfb`; `rg`+AST=0 imports; importlib ModuleNotFoundError×2; composer/`__init__` limpos; comentário histórico only; focused 37 PASS | `CLOSED_PROVEN` | — |
| L-06 | Legacy | Snapshot experiment code removido (RETIRE_FULL_SET PO) | DÉLIA interop | T2 ampliada: arquivos ausentes; env retired fail-closed; compose limpo; testes retired PASS | `CLOSED_PROVEN` (código) | ops: limpar flag prod |
| A-01 | Architecture | Domain/Application sem import direto de Infra no snapshot | DÉLIA specialist_interop | `snapshot_interop` usa Protocol `_SnapshotCatalogStore`; ledger G5 | `CLOSED_PROVEN` | — |
| A-02 | Architecture | C3-T4 Structured Understanding preservado | DÉLIA structured_understanding | docs 21/20/25 + doc256 Conflict A; código presente; unwired root = approved KEEP | `KEEP_APPROVED` | — |
| A-03 | Architecture | C3-T5 OpenAPI foundation preservado | DÉLIA openapi/capability | ledger G5 KEEP (46 testes); `openapi_provider.py` presente; adapter direto já aposentado | `KEEP_APPROVED` | — |
| A-04 | Architecture | Segundo Agent/planner/tool-loop paralelo ao Pydantic AI | DÉLIA orchestration | Agent + MCPToolset em adapter/investigation; G8 “zero segundo runtime” | `CLOSED_PROVEN` | — |
| A-05 | Architecture | Snapshot experiment RETIRE executado (código) | DÉLIA interop | PO §2A + remoção física; Settings fail-closed; live SpecialistInterop only | `CLOSED_PROVEN` (código) | R04 prod = PENDING_OPS |
| A-07 | Architecture | Cadastro centralizado MCP (Core provider registry) | Core governance | R1 + R1-REWORK: revoke-at-invoke, CA port, SSRF policy, provider-neutral admission, authorizationScope; ExternalConnection ainda TARGET; prod N/A | `IMPLEMENTED_BOUNDED_DEV` | T2_INDEPENDENT_REVIEW; ExternalConnection; R04 |
| A-06 | Architecture | Estratégia PromptedOutput vs ToolOutput (coexistência) | Coordenação DÉLIA | migração PromptedOutput rollback; ADR spike; **não reabrir em T3** | `KEEP_APPROVED` (+ ADR registrado) | — |
| O-01 | Flow | Admissão v42 → owner path (Kimi, Qwen14B) | DÉLIA admission | matrix E2E + admission 3/3; SHA `dc491abd1e` | `CLOSED_PROVEN` | — |
| O-02 | Flow | Admissão C1 Qwen4B local (`explanation`/owner_path=false) | DÉLIA admission + eval | matrix: admission FAIL 2/2; E2E 0 MCP; fronteira `ADMISSION` | `OPEN_MATERIAL` | T3 |
| O-03 | Flow | Outcome parcial Qwen14B B1 (MCP>0, NON_GROUNDED, `filial_id`) | DÉLIA Outcome / TÉO scope | matrix note `owner_path_proven_outcome_partial_filial_id`; fronteira `TO_VERIFY` | `OPEN_MATERIAL` | T3 |
| O-04 | Flow | Outcome parcial Qwen14B OPS_NON_TEO_1 (3 MCP, NON_GROUNDED) | DÉLIA Outcome | matrix E2E; fronteira `TO_VERIFY` | `OPEN_MATERIAL` | T3 |
| O-05 | Flow | Controles conceituais SIPOC/PDCA (0 tools) | DÉLIA admission | Kimi+Qwen14B NON_GROUNDED 0 invokes | `CLOSED_PROVEN` | — |
| O-06 | Flow | Multi-turn TEO GROUNDED (Kimi/Qwen14B) | DÉLIA continuity | matrix MULTITURN_TEO | `CLOSED_PROVEN` | — |
| O-07 | Flow | R03 — `tool_calls_limit` interrompe investigações densas | DÉLIA budgets | backlog R03 OPEN; E2E Kimi C1/B1 limitations `tool_calls_limit_reached` | `OPEN_MATERIAL` | T3 |
| O-08 | Flow | R05 — retry/churn de escopo residual | DÉLIA + modelo; TÉO se metadata | backlog R05 OPEN; causa exclusiva modelo `INCONCLUSIVE` | `TO_VERIFY` | T3 |
| O-09 | Flow | NDJSON / deadline / cancelamento | DÉLIA interaction | suítes históricas PASS; **não reexecutado nesta T0** | `TO_VERIFY` | T4 |
| O-10 | Flow | Multi-owner compare (cobertura formal matriz T3) | DÉLIA orchestration | evidência E2E focada TEO/admission; compare multi-owner **não** na matrix v42 | `TO_VERIFY` | T3 |
| R-01 | Regression | Suíte ampla delia-api no container bind-mount | DÉLIA QA | ~1376 PASS / 1 FAIL G4 path na sessão E2E (SHA ancestral `dc491abd1e`); **não** reexecutada no `CURRENT_HEAD` | `TO_VERIFY` | T4 |
| R-02 | Regression | `test_g4_integrated_homologation::test_fixture_matches_current_producer_output` | DÉLIA tests + packaging | Fixture **existe** em `plugins/delia/...`; sob `/app` no container `REPO_ROOT=parents[2]` resolve `/plugins/...` → FileNotFound; defeito de **path/ambiente**, não do producer | `OPEN_MATERIAL` | T4 |
| R-03 | Regression | Architecture/import/security focused suites | DÉLIA QA | arquivos `test_*architecture*` presentes; último PASS pleno = ledger G-series / post-removal — **STALE vs CURRENT_HEAD** sem rerun | `TO_VERIFY` | T4 |
| R-04 | Regression | E2E real Outcome (Kimi + Qwen14B) no SHA T1–T3 | DÉLIA QA | matrix `dc491abd1e` PROVEN DEV; revalidar no SHA pós-T1–T3 | `TO_VERIFY` | T4 |
| X-01 | External | R06 — tools/list autenticado MCP **produção** | TÉO + identidade/Keycloak | backlog `TEST_NOT_RUN` credencial; **não** mascara PASS DÉLIA DEV | `EXTERNAL_DEPENDENCY` | release/ops (não T1–T3 código) |
| X-02 | External | R07 — 10 FAILs suíte completa transformometro-api | TÉO / owners de domínio | backlog FAIL pré-existente | `EXTERNAL_DEPENDENCY` | trilha TÉO |
| X-03 | External | Auth password-grant **prod** (`invalid_grant` DEV_PORTAL) | Identidade/ops | E2E usou DEV local; prod auth não sincronizada | `EXTERNAL_DEPENDENCY` | ops (sem reset nesta trilha) |

---

## 2. Gate L — Legacy Cleanup (detalhe)

| ID | Arquivo/símbolo | Consumidor | Evidência | Estado | Ação T1 |
|---|---|---|---|---|---|
| L-01 | `…/paginated_result_semantics.py` | nenhum (removido) | HEAD ABSENT · `88a7c4e50c` | `CLOSED_PROVEN` | nenhuma |
| L-02 | `…/outcome_assessment.py` | nenhum (removido); lógica determinística em `generic_evidence_renderer.py` | HEAD ABSENT · G2 ledger | `CLOSED_PROVEN` | nenhuma |
| L-03 | `orchestration.py` monólito | substituído por orchestrator/support | ledger remoção nativa | `CLOSED_PROVEN` | nenhuma |
| L-04 | `openai_compatible_adapter` (texto) | aposentado; STT adapter distinto KEEP | dir model_invocation | `CLOSED_PROVEN` | nenhuma |
| L-05 | imports órfãos L-01/L-02 | nenhum ativo | T1 `d3a3d5ebfb`: AST 0; importlib ausente; 2 linhas comentário `HISTORICAL_REFERENCE` | `CLOSED_PROVEN` | nenhuma |
| L-06 | `snapshot_interop` / `catalog_store` / `mcp_catalog_sync` | `root_composer` se `DELIA_MCP_CATALOG_MODE=snapshot_experiment`; default `live` | HEAD EXISTS | `KEEP_APPROVED` | não DELETE sem A-05 |

**Saída L (T0):** candidatos DELETE do doc256/244/245 **já executados**. Não há `OPEN_MATERIAL` de remoção física restante. T1 = verificação residual + proibição de reintrodução — **não** nova auditoria dos 66 arquivos.

### T1 — L-05 verification (2026-11-09)

**TASK_ID:** `DELIA-C3-ENG-CLOSURE-T1-LEGACY-CONSUMER-PURGE-01`
**BASE_HEAD verificado:** `d3a3d5ebfb628aa81404d269ac2dfcd8b5272384` (= `origin/main` no início)
**CODE_CHANGED:** NO (Caso 1 — nenhum consumidor executável)

| Campo | Valor |
|---|---|
| `L01_FILE_ABSENT` | YES |
| `L02_FILE_ABSENT` | YES |
| `STATIC_IMPORT_REFERENCES` | 0 (AST Import/ImportFrom) |
| `DYNAMIC_IMPORT_REFERENCES` | 0 (`__import__`/`import_module` AST) |
| `ACTIVE_CONSUMERS` | 0 |
| `ORPHAN_ALIASES` | 0 |
| `REGISTRY_REFERENCES` | 0 |
| `COMPOSITION_REFERENCE_ERRORS` | 0 (`root_composer` load OK; source sem símbolos) |
| `HISTORICAL_REFERENCES` | 2 linhas comentário em `generic_evidence_renderer.py:366-367` |
| `NEGATIVE_TEST_REFERENCES` | `tests/test_g2_evidence_contract_regression.py` (pins assessors retired; importa equivalente `generic_evidence_renderer`) |
| `EXISTING_EQUIVALENT` | YES — projeção determinística em `generic_evidence_renderer` |
| `REUSE_DECISION` | REUSE |
| `FOCUSED_TEST_COMMAND` | `pytest -q tests/test_g2_evidence_contract_regression.py tests/test_composition_surface_regression.py tests/test_model_invocation_architecture.py tests/test_specialist_interop_architecture.py tests/test_interaction_architecture.py` |
| `FOCUSED_TEST_RESULT` | 37 PASS |
| `FULL_BACKEND_REGRESSION` | `TEST_NOT_RUN` (responsabilidade T4; sem diff de produção) |
| `L05_STATUS` | `CLOSED_PROVEN` |
| `L06_STATUS` | `KEEP_APPROVED` / A-05_PENDING |
| `LEGACY_CLEANUP_VERDICT` (L-05 slice) | `PASS` |
| `ZERO_LEGACY_GLOBAL_VERDICT` | **NOT PASS** — L-06/A-05 deliberadamente pendentes até T2 |

**Não reabrir:** L-01–L-04; não remover L-06; gates A/O/R inalterados.

---

## 3. Gate A — Architecture & Ownership (detalhe)

### A-01 — Snapshot boundary (CLOSED_PROVEN)

```text
ISSUE_ID: A-01
RESPONSIBILITY: dependency direction Application ↛ Infrastructure
LEGITIMATE_OWNER: delia-api/application/specialist_interop
CANONICAL_SOURCE: doc49 + ledger G5 + Protocol em snapshot_interop.py
CURRENT_CONSUMERS: root_composer (injeta McpCatalogStore só no composition root)
CURRENT_CONTRACT: SnapshotDiscoverInterop(store: _SnapshotCatalogStore Protocol)
IMPLEMENTATION_PATH: delia-api/app/application/specialist_interop/snapshot_interop.py
EVIDENCE_SHA: G5 ledger base cb9668c2 + HEAD verifica Protocol sem import infra
EXISTING_EQUIVALENT: YES (Protocol + DI)
REUSE_DECISION: REUSE
STATUS: CLOSED_PROVEN
REQUIRED_T2_ACTION: none
```

### A-05 — Snapshot experiment destiny (T2 decision package)

```text
ISSUE_ID: A-05
TASK_ID: DELIA-C3-ENG-CLOSURE-T2-BOUNDARY-OWNERSHIP-CONFORMANCE-01
BASE_HEAD: fd78269968b8f546e49ea8f859ca8cd2e6212d23
RESPONSIBILITY: retire vs keep snapshot_experiment + stale catalog (R04)
LEGITIMATE_OWNER: coordenação DÉLIA (adoção); interop/composition (código); TÉO (descrições live)
CANONICAL_SOURCE: doc216 (APPROVED_FOR_BOUNDED_EXPERIMENT; PRODUCTION_SWITCH_NOT_APPROVED;
  Task33 live baseline); ledger DOC216-FINAL ADOPTION_RECOMMENDATION=HYBRID_CANDIDATE
  com AB_VALIDITY=LIMITED + PRODUCTION_SWITCH=NO; doc217 KEEP_LIVE produção;
  doc256 Conflict C; backlog R04; residual register T0
A05_CANONICAL_AUTHORITY: doc216 + Task33 live — promoção produção exige ADR; NÃO há ADR
  posterior autorizando RETIRE_FULL_SET nem promoção permanente do snapshot
STATUS: ARCHITECTURE_DECISION_REQUIRED
RECOMMENDED_DECISION: RETIRE_FULL_SET
DECISION_APPROVAL_STATUS: PENDING_COORDINATION
CODE_CHANGED: NO
```

#### Gate A — caminhos atuais (PROVEN no HEAD)

| Campo | LIVE | SNAPSHOT_EXPERIMENT |
|---|---|---|
| Origem catálogo | `tools/list` MCP live (adapter / native `MCPToolset`) | SQLite `McpCatalogStore` (`DELIA_MCP_CATALOG_DB`) |
| Owner informação | Specialist MCP (TÉO/DAVI/VISTA…) | Snapshot capturado + hash; **não** authority |
| Discovery | `SpecialistInterop.discover_catalog` → adapter list; Agent: `MCPToolset` live | `SnapshotDiscoverInterop` lê ACTIVE; **invoke permanece live** |
| Ativação | default `DELIA_MCP_CATALOG_MODE` unset/`live` | flag composition-only; exige `DELIA_MCP_CATALOG_DB` |
| Consumidores código | runtime padrão; investigation Agent | `root_composer` branch; `mcp_catalog_sync.py`; `r4_authenticated_resume_eval` (condicional); `test_mcp_catalog_experiment.py` |
| Freshness | contínua no owner | prod DB `/data/delia/mcp_catalog.db` mtime/captura **2026-11-03**; teo `analyze` **sem** “Scope requirements” (stale vs contrato R02) |

`PRODUCTION_DEFAULT` (código): `live`.
`EXPERIMENT_ACTIVATION` (ops): **prod container `delpi-delia-api` tem `DELIA_MCP_CATALOG_MODE=snapshot_experiment` + DB set** — contradiz doc216 `PRODUCTION_SWITCH_NOT_APPROVED` → `OUT_OF_SCOPE_FINDING` / drift operacional (corrigir flag exige autorização ops; **sem** deploy/mutação nesta T2).

#### Gate B — reuse

| Responsabilidade | LIVE equivalente | Snapshot necessário? |
|---|---|---|
| Discovery capabilities | YES — MCPToolset + SpecialistInterop live | NO para runtime canônico |
| Descrições/schemas | YES — tools/list owner | NO (risco stale) |
| Seleção semântica | YES — Agent nativo | NO benefício estatístico (AB LIMITED) |
| Atualização contratos | YES — live | Snapshot exige sync manual; auto-sync **proibido** nesta trilha |
| Proveniência/AuthZ | YES — invoke + Core/Domain live | Snapshot explicitamente não-authority |

```text
EXISTING_EQUIVALENT: YES
REUSE_DECISION: REUSE (live MCP / Pydantic AI MCPToolset)
BENEFIT_NOT_PROVEN: melhoria latência discovery ~11s→0ms citada no ledger 216,
  mas AB_VALIDITY=LIMITED; sem ADR de promoção; BENEFIT ≠ autorização produção
```

#### Gate C — R04

```text
R04_PRODUCTION_IMPACT: PARTIAL_PROVEN — com flag prod=snapshot_experiment,
  mcp_provider.discover_catalog consome snapshot stale; Agent MCPToolset
  discovery permanece live (mitiga path investigation nativo)
R04_EXPERIMENT_IMPACT: PROVEN — teo analyze snapshot 2026-11-03 sem Scope requirements
R04_CONTRACT_DRIFT: PROVEN (descrição analyze desatualizada vs live pós-R02)
R04_OWNER: DÉLIA (modo/consumo); TÉO (contrato live autoritativo)
R04_ROOT_CAUSE: snapshot congelado + modo experiment ativo sem refresh autorizado
R04_REQUIRED_DISPOSITION: RETIRE_FULL_SET (fecha residual sem novo sync) OU
  KEEP_EXPERIMENT estrito EVAL_ONLY + flag prod→live + política refresh (não fecha
  R04 sozinho sem refresh/ADR)
R04_STATUS_AFTER_T2: OPEN_MATERIAL (aguarda execução pós-ADR)
```

#### Gate D — decisão

**RETIRE_FULL_SET (recomendado)** — critérios atendidos na evidência: LIVE cobre responsabilidades; consumidores exclusivos são experiment/test/composer branch; doc216 não autoriza produção; R04 stale PROVEN; sem continuidade obrigatória pós-native MCPToolset.

**KEEP_EXPERIMENT** — só se coordenação declarar obrigação experimental contínua; exigiria: owner, EVAL_ONLY, prod flag=`live`, critério de encerramento, e tratamento R04 (refresh manual governado ou aceite residual) — **não recomendado** para fechar gate A do doc293.

```text
DECISION_REQUIRED=RETIRE_FULL_SET_APPROVAL
```

Conjunto candidato **após aprovação** (não executado nesta T2):

- `delia-api/app/application/specialist_interop/snapshot_interop.py`
- `delia-api/app/infrastructure/interoperability/mcp/catalog_store.py`
- `delia-api/scripts/mcp_catalog_sync.py`
- branch `snapshot_experiment` em `root_composer.py` (+ mirror em `r4_authenticated_resume_eval.py`)
- settings `mcp_catalog_mode` / `mcp_catalog_db` (retirar ou fail-closed retired)
- `tests/test_mcp_catalog_experiment.py` (aposentar com o experimento)
- **Preservar** testes LIVE/MCP/AuthZ/architecture

Ops paralelo (fora remoção de código): restaurar `DELIA_MCP_CATALOG_MODE=live` em produção por processo autorizado (local-first / config governada) — **PRODUCTION_DEPLOY desta task = NOT_AUTHORIZED**.

#### Gate E — implementação

```text
AUTHORIZED_MINIMAL_ACTION: NONE
REASON: falta aprovação superior explícita RETIRE_FULL_SET
```

#### Testes T2 (decisão only)

```text
FOCUSED_TEST_COMMAND: pytest -q tests/test_mcp_catalog_experiment.py
  tests/test_specialist_interop_architecture.py
  tests/test_composition_surface_regression.py
FOCUSED_TEST_RESULT: 20 PASS
FULL_BACKEND_REGRESSION: TEST_NOT_RUN
LIVE_PATH_REGRESSION: TEST_NOT_RUN (sem mutação; default código live)
```

### A-02 / A-03 — KEEP_APPROVED (sem DELETE)

- **A-02 C3-T4:** capability aprovada; falta de wiring ≠ legado.
- **A-03 C3-T5:** foundation KEEP; adapter DELPI direto já aposentado (G5).

### A-04 / A-06

- **A-04:** um runtime Pydantic AI — `CLOSED_PROVEN` no sentido de ausência de segundo motor (G8 + inspeção Agent sites).
- **A-06:** ToolOutput vigente após rollback PromptedOutput; **proibido reabrir em T3**; mudança exige ADR novo fora desta trilha.

---

## 4. Gate O — Orchestration & Flow (detalhe)

Mapeamento backlog R01–R07 → IDs:

| Backlog | Status no backlog | ID freeze | Bloqueia aceite DÉLIA (gates 293)? |
|---|---|---|---|
| R01 admission/E2E | RESOLVED_WITH_RESIDUAL | O-01 CLOSED; O-02/O-03/O-04 residuais | Sim, se O-02/O-03/O-04 forem material no DoD da trilha — T3 deve vereditar |
| R02 READ contract | RESOLVED_WITH_RESIDUAL | — (TÉO); churn residual → O-08 | Não como contrato; sim se Outcome DÉLIA falhar por args evitáveis |
| R03 tool budget | OPEN | O-07 | Sim, se falhas densas forem do fluxo DÉLIA |
| R04 snapshot stale | OPEN_MATERIAL (T2) | A-05 / L-06 | Impacto experiment PROVEN; prod parcial com flag `snapshot_experiment` ainda ON |
| R05 scope retry | OPEN | O-08 | T3 classifica |
| R06 prod tools/list | OPEN TEST_NOT_RUN | X-01 | **Release/prod** — não substitui PASS DEV; se critério produto exigir prod metadata, permanece bloqueador de **release**, não de T1 código |
| R07 TÉO suite 10 FAIL | OPEN | X-02 | Trilha TÉO; não esconder sob PASS DÉLIA |

**Primeira fronteira divergente (quando evidenciada):**

| ID | Fronteira |
|---|---|
| O-01 | — (fechado) |
| O-02 | `ADMISSION` (PROVEN admission-only 2/2) |
| O-03 | `TO_VERIFY` (`OWNER` vs `OUTCOME` — filial_id / clarificação após MCP) |
| O-04 | `TO_VERIFY` |
| O-07 | `AGENT`/`OUTCOME` (limit hit) — confirmar em T3 |
| O-08 | `TO_VERIFY` |

**Não reabrir:** ToolOutput/PromptedOutput; keyword routing; branches por modelo.

---

## 5. Gate R — Full Regression (matriz única T4)

| TEST_GROUP | CANONICAL_COMMAND | TARGET_ENVIRONMENT | LAST_EVALUATED_SHA | LAST_RESULT | KNOWN_FAILURES | REQUIRED_EVIDENCE | T4_DISPOSITION |
|---|---|---|---|---|---|---|---|
| Admission routing unit | `pytest -q tests/test_interaction_admission_routing.py` | delia-api (host ou container com repo root) | `dc491abd1e` | 8 PASS | — | exit 0 | RUN |
| Full backend delia-api | `pytest -q` (sem `-k` substituto; excluir só se ADR) | **repo root montado** ou path fixture corrigido | parcial container ~`dc491abd1e` | ~1376 PASS / 1 FAIL | R-02 G4 path | exit 0 no SHA T1–T3 | RUN após R-02 |
| G4 fixture homologation | `pytest -q tests/test_g4_integrated_homologation.py` | ambiente onde `plugins/delia` é visível via `REPO_ROOT` | container FAIL; host fixture EXISTS | FAIL path | R-02 | PASS + fixture drift assert | FIX path/packaging **ou** run canônico documentado — sem skip silencioso |
| Architecture / imports | `pytest -q tests/test_*architecture*.py tests/test_composition_surface_regression.py` | delia-api | ledger G-series (STALE) | PASS histórico | — | exit 0 HEAD | RUN |
| Security / AuthZ negatives | suites security/specialist_interop_security + AuthZ 401/403 existentes | delia-api | STALE | PASS histórico | — | exit 0 + casos negativos | RUN |
| MCP / interop contract | testes MCP delia-api + focused TEO MCP se contrato exigir | DEV | R02 era 89 PASS TÉO MCP | PASS histórico | X-02 fora | exit 0 escopo DÉLIA | RUN |
| E2E Outcome real | `native_mcptoolset_direct_eval.py` + scenarios r01-v42-e2e | DEV auth legítima; profiles Kimi + Qwen14B | `dc491abd1e` | matrix-summary.json | O-02/O-03/O-04 | matrix atualizada no SHA T4 | RUN |
| Conceptual / multiturn controls | mesmos scripts | DEV | `dc491abd1e` | O-05/O-06 | — | 0-tool conceitual; multiturn GROUNDED | RUN |
| TÉO full suite | `scripts/ci-transformometro-api.sh` | TÉO CI | backlog R07 | 10 FAIL | X-02 | owner TÉO | EXTERNAL — reportar, não mascarar |
| Prod MCP tools/list auth | curl/MCP initialize+tools/list | produção | R06 | TEST_NOT_RUN | X-01 | hash descrição | EXTERNAL |

**Falha G4 (R-02) — classificação T0:**

1. Teste: `tests/test_g4_integrated_homologation.py::test_fixture_matches_current_producer_output`
2. SHA avaliado: sessão E2E sob ancestral `dc491abd1e` (container `b03ea2f1eb69_delpi-delia-api`)
3. Baseline: fixture **presente** no monorepo; falha **não** reproduz “fixture ausente no Git”
4. Causa: `REPO_ROOT = Path(__file__).parents[2]` assume monorepo; no container `/app` ⇒ `/plugins/...` inexistente → **ambiente/path**
5. Owner: DÉLIA test packaging / compose mount (não product Outcome)
6. Prova de correção: teste PASS no ambiente canônico T4 **sem** alterar expected para esconder drift; producer↔fixture parity preservada

`FUNCTIONAL_TESTS_EXECUTED` nesta T0: **TEST_NOT_RUN** (reconciliação only).

---

## 6. Pacotes congelados T1–T4

### T1 — Legacy Cleanup (`DELIA-C3-ENG-CLOSURE-T1-LEGACY-CONSUMER-PURGE-01`)

**Status:** EXECUTADO — `L-05=CLOSED_PROVEN`; sem diff funcional.
**Não incluir:** L-01…L-04 (já CLOSED); L-06 DELETE (bloqueado por A-05).
**Próxima revisão:** `T1_INDEPENDENT_REVIEW` antes de autorizar T2.

### T2 — Architecture & Ownership (`DELIA-C3-ENG-CLOSURE-T2-BOUNDARY-OWNERSHIP-CONFORMANCE-01`)

**Status:** EXECUTADO como **decision package** — `RECOMMENDED=RETIRE_FULL_SET`; `CODE_CHANGED=NO`; aguarda ADR.
**Preservar até ADR:** L-06 código; A-01/A-02/A-03/A-06.
**Proibido nesta etapa:** remoção, sync automático, novo registry, T3.

### T3 — Orchestration & Flow (`DELIA-C3-ENG-CLOSURE-T3-FLOW-OUTCOME-REMEDIATION-01`)

**Somente IDs abertos:** `O-02`, `O-03`, `O-04`, `O-07`, `O-08`, mais confirmações `O-10` se falhar matriz mínima doc293.
**Preservar:** O-01/O-05/O-06 CLOSED; instruction v42; sem PromptedOutput revisit.
**Por defeito:** 1ª fronteira → 1 diff bounded → RED/GREEN → caso DEV.
**Veredicto explícito** se O-02 (Qwen4B) entra no DoD ou fica limitação de modelo documentada **fora** de PASS universal.

### T4 — Full Regression (`DELIA-C3-ENG-CLOSURE-T4-FULL-REGRESSION-AND-REAL-EVAL-01`)

Executar **exatamente** a matriz da §5.
Corrigir/isolar R-02 no owner de teste se legítimo.
Revalidar E2E Kimi+Qwen14B no SHA pós-T1–T3.
X-01/X-02: reportar status; se critérios de produto os exigirem para CLOSE, **STOP** sem auto-executar outros serviços.

### T5 (fora desta task)

Comparar este registro vs HEAD pós-T1–T4; ACCEPT só se L=A=O=R=PASS e zero `OPEN_MATERIAL` no escopo.

---

## 7. Evidências necessárias para aceite final T5

1. Diffs T1–T3 com consumers/contratos e residual search dirigida aos IDs acima.
2. Suíte completa delia-api exit 0 no SHA final (ambiente canônico).
3. R-02 PASS ou isolamento canônico com owner.
4. Matrix E2E atualizada (Kimi+Qwen14B) com Outcome honesto; veredicto O-02.
5. A-05 decidido (KEEP documentado ou RETIRE completo).
6. X-01/X-02 explicitamente bloqueadores ou não-bloqueadores de **produto**.
7. Review independente T5; ledger atualizado; **sem** deploy implícito.

---

## 8. Contagens T0 (para relatório)

| Gate | CLOSED_PROVEN | OPEN_MATERIAL | KEEP_APPROVED | TO_VERIFY | EXTERNAL / ADR |
|---|---:|---:|---:|---:|---:|
| L | 5 | 0 | 1 | 0 | 0 |
| A | 2 | 0 | 3 | 0 | 1 ADR (A-05) |
| O | 3 | 4 | 0 | 3 | 0 |
| R | 0 | 1 | 0 | 3 | 0 |
| X | 0 | 0 | 0 | 0 | 3 |

**Gates L/A/O/R do doc 293:** todos **ainda NÃO PASS** — T0 apenas congela o universo.

**NEXT_BOUNDED_STEP:** `T2_INDEPENDENT_REVIEW` — coordenação aprova/rejeita `RETIRE_FULL_SET`; só então task bounded de remoção (se aprovada). T3 **não** autorizada.


---

## T2 ampliada — execução (2026-11-09)

**TASK_ID:** `DELIA-C3-ENG-CLOSURE-T2-BOUNDARY-OWNERSHIP-CONFORMANCE-01` (emenda PO §2A doc 293)
**PLAN_COMMIT:** `91ab7b8476a48b9b7afd815952ae4a67843098c9`
**BASE_HEAD (reanchor):** `1a895cb0f02bedb6bd2288855fe1d447fea8998e`
**PRODUCTION_DEPLOY:** NOT_AUTHORIZED · **T3:** NOT_AUTHORIZED

### T2.1 — RETIRE_FULL_SET (código)

**Removidos:**
- `delia-api/app/application/specialist_interop/snapshot_interop.py`
- `delia-api/app/infrastructure/interoperability/mcp/catalog_store.py`
- `delia-api/scripts/mcp_catalog_sync.py`
- `delia-api/tests/test_mcp_catalog_experiment.py`
- branch snapshot em `root_composer.py` e `r4_authenticated_resume_eval.py`
- env Compose `DELIA_MCP_CATALOG_MODE` / `DELIA_MCP_CATALOG_DB`

**Fail-closed:** `Settings` rejeita `DELIA_MCP_CATALOG_DB` não-vazio e qualquer `DELIA_MCP_CATALOG_MODE` ≠ unset/`live`.

**Testes:** `test_mcp_catalog_snapshot_retired` + arch/composition focused PASS; suíte ampla ~1374 PASS / 1 FAIL = G4 path (T4, pré-existente).

**Consumidores ativos snapshot:** 0 (somente testes negativos de ausência).

### Produção — drift e remediação (NÃO executada)

Estado observado anteriormente: `DELIA_MCP_CATALOG_MODE=snapshot_experiment`, DB `/data/delia/mcp_catalog.db` (~2026-11-03).

Procedimento autorizado futuro (ops; **não** mutar prod nesta task):

1. Backup `.env` / compose overlay e do volume `mcp_catalog.db` se retenção for necessária.
2. Remover ou comentar `DELIA_MCP_CATALOG_MODE` e `DELIA_MCP_CATALOG_DB` no env prod.
3. Deploy/restart **somente** após push deste código (Settings fail-closed) + autorização ops — ordem: código live-only → limpar env → restart.
4. Pós-condição: container sem as duas envs; health 200; um turno DEV/prod autorizado com MCPToolset live; ausência de erros `retired` no boot.
5. Volume SQLite experimental: reter ou apagar conforme política de dados; **não** é fonte de authority.
6. Rollback: restaurar env+imagem anteriores (não reintroduzir snapshot no código).

`R04_STATUS` após T2.1 código: **`PENDING_OPS`** até pós-condição prod verificada. Não declarar `CLOSED_PROVEN` para R04 sem prova runtime prod.

### T2.2 — Inventário (READ-ONLY)

| Responsabilidade | EXISTING_EQUIVALENT | REUSE_DECISION | Evidência |
|---|---|---|---|
| MCPToolset / CombinedToolset live | YES | REUSE | `pydantic_ai_investigation.py` |
| SpecialistInterop + adapter | YES | REUSE | application/infrastructure interop |
| Identidades 7 specialists | YES | REUSE | `_SPECIALIST_IDENTITY` (davi…eva) |
| Endpoints/enable flags | YES (env) | REUSE até Core | `settings.mcp_specialist_*` |
| Provider approval persistido Core | NO / TARGET_ONLY | **não NEW** | doc51 §18.3; sem tabela/API Core |
| ExternalConnection físico | NO / TARGET_ONLY | **não NEW** | doc21 candidato; doc51 TARGET_ONLY |
| Keycloak 7 resource clients (desejado) | YES (script) | REUSE IAM | `delia_mcp_keycloak_state.py` SPECIALISTS×7; **≠ prova prod provisionada** |
| Compose defaults | PARCIAL | — | DAVI/TÉO/VISTA enabled; CAIO/CLARA/SURI/EVA unset no DEV local |

**Matriz 7× (DEV local container):**

| ID | Endpoint env | Enabled | tools/list | AuthZ | Nota |
|---|---|---|---|---|---|
| DAVI | set | true | TEST_NOT_RUN (T2) | — | compose default |
| TÉO | set | true | TEST_NOT_RUN | — | compose default |
| VISTA | set | true | TEST_NOT_RUN | — | compose default |
| CAIO | unset | unset | TEST_NOT_RUN | — | identity exists; not wired DEV |
| CLARA | unset | unset | TEST_NOT_RUN | — | idem |
| SURI | unset | unset | TEST_NOT_RUN | — | idem |
| EVA | unset | unset | TEST_NOT_RUN | — | idem |

Keycloak prod state: **TO_VERIFY** (sem `--check` autorizado nesta execução).

### T2.3 — Contrato cadastro centralizado (design only)

```text
RESPONSIBILITY: aprovar/cadastrar/desabilitar provedores MCP
LEGITIMATE_OWNER: Core governance (doc60 §5.1)
CANONICAL_SOURCE: docs 21 §§4A.18/7/23; 60 §5.1; 51 TARGET_ONLY
CONSUMERS: DÉLIA composition (futuro read model); Control Tower UI
CURRENT_CONTRACT: candidato ExternalConnection + provider approval — NÃO físico
EXISTING_EQUIVALENT: NO (plataforma)
REUSE_DECISION: EXTEND Core quando contrato/fase autorizarem — NEW na DÉLIA PROIBIDO
OWNER_APPROVAL: REQUIRED (Core write)
PHASE_AUTHORIZATION: DEFERRED / BLOCKED_BY_OWNER_CONTRACT
```

Separação preservada: **Server registration ≠ ExternalConnection ≠ live tools/list**.

### T2.4 / T2.5 — implementação

```text
STATUS: BLOCKED_BY_OWNER_CONTRACT
REASON: ExternalConnection / provider approval Core não existem fisicamente;
        PO autorizou planejar, não improvisar tabela na DÉLIA
UI_ADMIN: não implementada (sem contrato backend)
EXTERNAL_MCP_E2E: TEST_NOT_RUN
```

### Estados finais T2 ampliada

| ID | Status |
|---|---|
| A-05 | `CLOSED_PROVEN` (código) |
| L-06 | `CLOSED_PROVEN` (código) |
| R04 | `PENDING_OPS` (prod flag) |
| A-07 cadastro Core | `BLOCKED_BY_OWNER_CONTRACT` |
| Architecture Ownership gate | **NOT PASS** global (A-07 + R04 ops) |
| Snapshot removal gate | **PASS** no código/repo |

**NEXT:** `T2_INDEPENDENT_REVIEW`


---

## T2 — Governed MCP Registry implementation attempt (2026-11-09)

**TASK_ID:** `DELIA-C3-T2-CORE-GOVERNED-MCP-REGISTRY-IMPLEMENTATION-01`
**ARCHITECTURE_DECISION_COMMIT:** `f5baf5b2a65dcbbf93d1f17efe6b2a9bdd5131b2` (§2A.7)
**BASE_HEAD:** `b3973d87a10c17da8593011cbe7c5f08e325a0c6`
**CODE_CHANGED:** NO · **MIGRATIONS_CHANGED:** NO · **PRODUCTION_DEPLOY:** NOT_AUTHORIZED · **T3:** NOT_AUTHORIZED

### Ownership gate (obrigatório)

```text
CORE_OWNER_APPROVAL: NOT_PROVEN
  evidência: §2A.7 declara direção arquitetural aprovada E
  "implementação ainda BLOCKED_BY_OWNER_CONTRACT";
  gate (1) exige "aceite formal de Core owner e fase/CP-RQ"
  — ausente neste prompt e no HEAD
CURRENT_PHASE: T2 / A-07 (não fase Core de persistence write)
CP_RQ: A-07; doc60 §5.1 TARGET/DEFERRED; CP-197 ExternalConnection PLANNED
LEGITIMATE_OWNER: Core governance (PostgreSQL delpi_core)
EXISTING_EQUIVALENT: NO (provider registry / ExternalConnection MCP)
REUSE_DECISION: EXTEND Core (preferido) — execução NÃO autorizada
CONTRACT_APPROVED: NO (somente especificação abaixo)
PERSISTENCE_AUTHORIZED: NO
```

**Veredicto de execução:** `BLOCKED_BY_OWNER_CONTRACT` — análise + especificação contratual apenas. Nenhum write Core/Keycloak/DÉLIA registry paralelo.

### Inventário dirigido Core (HEAD)

| RESPONSIBILITY | OWNER | SOURCE | CONSUMERS | CURRENT_CONTRACT | IMPLEMENTATION | TEST | EXISTING_EQUIVALENT | REUSE_DECISION |
|---|---|---|---|---|---|---|---|---|
| Cadastro apps/plugins | Core | `apps`, `app_manifests`, `app_versions`, `app_routes` | Portal/admin | HTTP `apps.*` + AuthZ `apps.view`/`apps.manage` | `apps_controller` + use cases | unit use cases | YES (portal apps) | REUSE padrões AuthZ/audit — **não** é MCP provider registry |
| Active/inactive lifecycle | Core | `apps.active` + set_plugin_active | admin | boolean active | presente | unit | YES (apps) | REUSE padrão lifecycle — schema apps **sem** protocol/endpoint/authStrategy MCP |
| RBAC / PermissionResolver | Core | `permissions`, roles/groups | toda plataforma | PermissionResolver canônico | `permission_resolver.py` | alignment tests | YES | REUSE para AuthZ admin/consumer futuro |
| Auditoria | Core | `audit_logs` | admin/export | AuditLog model + retention job | presente | retention | YES | REUSE trilha — não cobre provider MCP hoje |
| Consents | Core | `user_consents` | /me consents | purpose-scoped LGPD | presente | — | PARTIAL | REUSE só se ExternalConnection consent mapear purpose; **não** é connection OAuth |
| S2S effective-access | Core | `GET /integrations/effective-access/...` | TV MCP futuro | doc integrations-effective-access | presente | — | YES (AuthZ subject) | REUSE para Domain AuthZ; **não** lista providers MCP |
| MCP provider approval persistido | Core governance (alvo) | — | DÉLIA (futuro) | doc60 §5.1 DEFERRED; §2A.7 | **AUSENTE** (rg=0) | — | **NO** | EXTEND/NEW **após** CORE_OWNER_APPROVAL |
| ExternalConnection físico | TBD | doc21 §7 candidato | DÉLIA connectors | TARGET_ONLY | **AUSENTE** | — | **NO** | TO_CONFIRM owner antes de schema |
| tools/list catalog | MCP servers | live | MCPToolset | nativo | live | retired tests | YES | REUSE — nunca persistir como authority |
| IAM token exchange | Keycloak | `delia_mcp_keycloak_state.py` SPECIALISTS×7 | delia-api | doc60 | script + runtime | TO_VERIFY prod | YES | REUSE — sem writes prod nesta task |
| Snapshot catalog | — | retired | — | RETIRE_FULL_SET | ABSENT | retired PASS | N/A | NÃO reintroduzir |

**Prova de ausência (CONFIRMADO_NO_CODIGO):** `rg mcp_provider|external_connection|provider_registry|mcp_server` em `core-api` → 0; nenhuma migration `CREATE TABLE` MCP; models listados sem tabela provider/connection MCP.

**Apps ≠ MCP registry:** `apps` modela plugins do Portal (`id/name/base_path/type/active`), sem `protocol=MCP`, `endpoint_ref`, `auth_strategy_ref`, `approval_status`, `risk_tier` ou lifecycle `DISCOVERED→…→REVOKED`. Estender `apps` sem contrato aprovado seria overloading semântico — **não recomendado sem ADR Core**.

### Especificação contratual (draft — NÃO implementada)

**A. Provider registration (Core-owned, PostgreSQL `delpi_core`)**

Campos conceituais mínimos (adaptar a naming Core):

```text
provider_ref (stable id)
display_name
protocol (= MCP)
endpoint_ref (validated HTTPS / egress policy ref)
owner_ref
auth_strategy_ref (KEYCLOAK_DELEGATED | EXTERNAL_OAUTH | …)
approval_status (DISCOVERED|REVIEWED|APPROVED|REJECTED|DISABLED|REVOKED|DEPRECATED)
enabled (bool; só relevante se APPROVED)
risk_tier / policy_ref
version (optimistic concurrency)
approved_by_ref / created_at / updated_at / audit_ref
```

Transições tipadas + AuthZ administrativa Core (`require_permission` novo código, ex. `integrations.mcp_providers.manage` — nome TBD pelo Core owner).
`approved=true` **nunca** via PATCH genérico sem use case de aprovação.

**B. ExternalConnection (owner físico a confirmar)**

Separado do provider. Sem tokens na tabela. Campos candidatos doc21 §7.
`PERSISTENCE_AUTHORIZED=NO` ⇒ **não criar tabela nesta task**.

**C. HTTP Core (padrão apps_controller / integrations_*)**

Capacidades alvo (paths/operationIds TBD pelo Core owner; exemplos não congelam URL):

1. list providers
2. get by id
3. register candidate
4. approve / reject
5. enable / disable
6. revoke
7. list eligible for authorized consumer (DÉLIA S2S ou user-delegated)
8. audit trail query

Erros tipados, paginação, idempotência de registro, observabilidade, fail-closed.

**D. DÉLIA consumer (após Core live)**

```text
authenticated context → Core eligibility → connection resolution
→ credential (Keycloak exchange / external secret owner)
→ MCPToolset live tools/list → governed invoke → Domain → Outcome
```

Fail-closed se Core indisponível. Sem segundo registry. Sem remoção prematura de `_SPECIALIST_IDENTITY`/settings até paridade comprovada.

**E. Migração 7 especialistas (design)**

Idempotente por `provider_ref` canônico (`davi`…`eva`); preservar Keycloak client ids; `enabled` espelha compose efetivo (DAVI/TÉO/VISTA true; CAIO–EVA false até ops). **Não aplicar em prod.**

**F. Externo**

Provider-neutral; SSRF/redirect/DNS checks; OAuth externo fora do Keycloak DELPI; E2E real = `TEST_NOT_RUN` sem servidor autorizado.

### Estados

| ID | Status após esta task |
|---|---|
| A-07 | Architecture | Cadastro centralizado MCP (Core provider registry) | Core governance | R1 + R1-REWORK: revoke-at-invoke, CA port, SSRF policy, provider-neutral admission, authorizationScope; ExternalConnection ainda TARGET; prod N/A | `IMPLEMENTED_BOUNDED_DEV` | T2_INDEPENDENT_REVIEW; ExternalConnection; R04 |
| R04 | `PENDING_OPS` |
| Architecture Ownership gate | `NOT_PASS` |
| Snapshot | permanece ABSENT |

**Decisão necessária do Core owner (bloqueador):**

1. Aceite formal `CORE_OWNER_APPROVAL` + fase/CP-RQ.
2. Escolha: nova tabela vs extensão justificada (não `apps` sem ADR).
3. Permission codes + operationIds.
4. Owner físico de ExternalConnection.
5. Autorização de migrations em DEV (não prod).


### Decisão posterior ao relatório — autorização PO para execução bounded Core DEV (2026-11-09)

**A-07 / mudança prospectiva:** PO autorizou explicitamente a implementação de registro governado MCP **sob ownership Core**, com PostgreSQL Core, API contratada, RBAC, auditoria, migration **DEV**, integração DÉLIA via HTTP e migração idempotente dos sete registros em DEV. `A-07=AUTHORIZED_FOR_BOUNDED_DEV_IMPLEMENTATION` (não `CLOSED_PROVEN`); `CORE_OWNER_ACK=TO_VERIFY` se o contrato vigente exigir aceite independente da equipe Core; `PERSISTENCE_DEV_SCOPE_AUTHORIZED_BY_PO=YES`. A decisão encontra-se no Documento 293 §2A.9; o relatório histórico da tentativa anterior continua válido como *estado anterior à autorização*, não como bloqueio de PO ainda pendente.

**Condições de execução:** reancorar 16/ledger/ownership; contract-first com schema escolhido após inventário, permissão/operationIds/erros/audit/revoke/rollback; criar somente estrutura mínima Core no âmbito DEV se autorizada pela autoridade superior; nenhuma tabela MCP na DÉLIA/Keycloak, nenhum `tools/list` persistido. `ExternalConnection` físico e OAuth externo = owner/contrato separados, não automaticamente aprovados. Tests 401/403, isolation, SSRF, idempotence, migration 7× DEV, MCP live, Core+DÉLIA regression e Outcome; sem `PASS` por documentação. Produção/Keycloak writes/deploy **NÃO autorizados**; `R04=PENDING_OPS`; `T3=NOT_AUTHORIZED`.


**NEXT:** `T2_INDEPENDENT_REVIEW` — aguardar aceite Core antes de qualquer implementação.


---

## T2 R1 — Core governed MCP registry implementation (2026-11-09)

**TASK_ID:** `DELIA-C3-T2-CORE-GOVERNED-MCP-REGISTRY-IMPLEMENTATION-R1`
**AUTHORIZATION:** §2A.9 / commit `a2321e15` — `PO_IMPLEMENTATION_AUTHORIZATION=APPROVED`
**CORE_OWNER_ACK:** `TO_VERIFY` (sem assinatura separada exigida no contrato vigente; execução DEV sob PO)

### Entrega

- Migration `u7v8w9x0y1_mcp_providers` → tabela `mcp_providers` + permissions `mcp_providers.view|manage`
- Lifecycle tipado + use cases + audit via `audit_logs`
- Admin `/admin/mcp-providers/*` + S2S `GET /integrations/mcp-providers/eligible`
- Seed DEV idempotente 7 especialistas (enabled só davi/teo/vista)
- DÉLIA: `DELIA_MCP_PROVIDER_REGISTRY_MODE=core|settings` + client HTTP fail-closed
- Snapshot continua ABSENT; ExternalConnection **não** implementado

### Testes

- Core focused: lifecycle + use case + HTTP authz **PASS**
- DÉLIA focused: core registry client + snapshot retired **PASS**
- Full suites: executar se tempo; senão registrar resultado real

### Estados

| ID | Status |
|---|---|
| A-07 | `IMPLEMENTED_BOUNDED_DEV` (não `CLOSED_PROVEN` — ExternalConnection + review + mode=core prod) |
| R04 | `PENDING_OPS` |
| Architecture Ownership | PARTIAL — Core registry vivo em DEV; gate global ainda depende review |

**NEXT:** `T2_INDEPENDENT_REVIEW`

## T2 R1-REWORK — bounded architecture & security (2026-11-09)

**TASK_ID:** `DELIA-C3-T2-CORE-GOVERNED-MCP-REGISTRY-R1-REWORK-01`
**AUTHORIZATION:** Documento 293 §2A.9 / §2A.11
**BASE:** R1 SHA `3dacbdc0c23c13fefc23d9610f21cdbfd0632333`

### Correções

1. **RW01 Revocation:** invoke-time Core eligibility recheck (port + guard + orchestrator); bloqueia revoke/disable/unavailable/malformed sem restart DÉLIA.
2. **RW02 CA boundary:** Application → `McpProviderRepositoryPort` + domain entities; SQLAlchemy só em infrastructure/UoW.
3. **RW03 SSRF:** `domain/mcp_providers/endpoint_policy.py` + trusted-host allowlist; cadastro ≠ connection-time completa para proxies arbitrários (residual documentado).
4. **RW04 Provider-neutral:** Core-eligible desconhecidos admitidos com auth suportada; `EXTERNAL_OAUTH`/unsupported → `unavailable_reason` (não silent discard; não auto-ACT).
5. **RW05 AuthZ boundary:** `authorizationScope=provider_approval_only` no S2S; gates Policy/Decision/Domain preservados.

### Testes

- Core focused MCP (lifecycle/http/policy/use_case): **32 PASS**
- Core full `app/tests/`: **382 PASS / 29 FAIL** — falhas **sem** overlap MCP (RBAC/routes/favorites/presence/manifest); alinhado ao relatório R1 (29 FAIL preexistentes; PASS aumentou pelos novos testes)
- DÉLIA focused registry/eligibility/composition: **31 PASS**
- DÉLIA suite (sem presentation_v2 docs-mount + support): **1 FAIL** `test_g4_integrated_homologation` (fixture drift; fora do escopo MCP rework) + 2 ERROR de collection presentation_v2 por `/docs` não montado no container

### Estados

| ID | Status |
|---|---|
| A-07 | `IMPLEMENTED_BOUNDED_DEV` (não `CLOSED_PROVEN`) |
| R04 | `PENDING_OPS` |
| T2_ARCHITECTURE_GATE | PARTIAL — rework R1 entregue; review independente pendente |

**DEV_REAL_E2E revoke-without-restart:** coberto por testes de invoke revalidation (guard/orchestrator); E2E HTTP admin+live wire classificado `TEST_NOT_RUN`/`INCONCLUSIVE` se ambiente admin token/ops não exercitado nesta fatia.
**PRODUCTION_DEPLOY:** NOT_AUTHORIZED. **T3:** NOT_AUTHORIZED.
**NEXT:** `T2_INDEPENDENT_REVIEW`

## T2 FULL-REMEDIATION — suites + MCP security (2026-11-09)

**TASK_ID:** `DELIA-C3-T2-CORE-MCP-REGISTRY-FULL-REMEDIATION-AND-REGRESSION-01`
**REFERENCE:** `ebd0a3533d20d93c001a2151fd9e567e9f116f85`
**AUTHORIZATION:** PO full remediation; §2A.12

### Correções MCP

- Revogação no boundary `_invoke` (além do semantic tool path).
- Domain `endpoint_policy` sem I/O; infra `endpoint_network` (DNS/env).
- DÉLIA `endpoint_egress` no `_connect` (connection-time).
- Compose DEV monta `/docs` + `/plugins/delia` para testes de contrato.

### Suites

| Suite | Antes | Depois |
|---|---|---|
| Core `app/tests/` | 382 PASS / 29 FAIL | **413 PASS / 0 FAIL** |
| DÉLIA `tests/` | ~1387 PASS / 1 FAIL + collection errors | **1463 PASS / 0 FAIL** |

### DEV E2E

- Seed 7; eligible davi/teo/vista; disable davi → fora do eligible → restore: **PASS**
- DÉLIA S2S client + guard (teo ok / caio blocked); envelope `authorizationScope=provider_approval_only`: **PASS**
- Outcome user-facing live Domain/Keycloak ACT: **TEST_NOT_RUN**

| ID | Status |
|---|---|
| A-07 | `IMPLEMENTED_BOUNDED_DEV` |
| R04 | `PENDING_OPS` |

**NEXT:** `T2_INDEPENDENT_REVIEW`

## T2 RESUME-REVOCATION CLOSURE (2026-11-09)

**TASK_ID:** `DELIA-C3-T2-MCP-REGISTRY-REVOCATION-RESUME-FINAL-CLOSURE-01`
**REFERENCE:** `a2944df834…`
**DEFECT:** resume replay de READ MCP sem revalidar Core eligibility
**FIX_LOCATION:** `governed_capability_orchestrator.py::_invoke` — eligibility **antes** de `invoke_outcomes` replay
**EXISTING_EQUIVALENT:** `McpProviderEligibilityPort` / `CoreMcpProviderEligibilityGuard`
**REUSE_DECISION:** REUSE (mesmo gate; ordem corrigida)

### Evidência

- RED/GREEN A–H em `tests/test_mcp_resume_eligibility_gate.py`
- DEV S2S eligible davi/teo/vista + caio blocked: PASS
- Resume-revoke live multi-turn harness: COVERED_BY_CONTRACT_TESTS (não harness E2E dedicado)
- Outcome ACT live: TEST_NOT_RUN

| ID | Status |
|---|---|
| A-07 | `IMPLEMENTED_BOUNDED_DEV` (não CLOSED_PROVEN) |
| R04 | `PENDING_OPS` |

**OPEN_MATERIAL:** ExternalConnection; R04 ops; DNS-rebinding/proxy residual; Outcome ACT live
**NEXT:** `T2_INDEPENDENT_REVIEW`

## T2 FINAL QUALITY + ADVERSARIAL VALIDATION (2026-11-09)

**TASK_ID:** `DELIA-C3-T2-MCP-REGISTRY-FINAL-QUALITY-AND-ADVERSARIAL-VALIDATION-01`
**REFERENCE_IMPL:** `94f51e542b` (resume eligibility) sob HEAD reancorado `dbc2e526c68e…`
**SCOPE:** qualidade de testes + invariantes; sem feature nova; sem T3; sem prod.

### Defects

| ID | Achado | Correção |
|---|---|---|
| TQ-01 | Cancel assertion `… or True` (falso positivo) | `_TurnCancelled` tipado + mutação RED |
| TQ-02 | Deadline `raises(Exception)` permissivo | `TurnBudgetExhausted` + stage + no wire |
| TQ-03 | Missing-token só checava tipo genérico | assert `integrations_token_missing` |

### Path / invariants (resumo)

- I-01..I-08 cobertos por testes de eligibility/resume/cancel/deadline/multi-owner (contract).
- I-09 Outcome ACT live: `TEST_NOT_RUN`.
- I-10 single runtime: sem novo planner/registry (code audit).
- Race TOCTOU eligibility→wire: residual documentado (não atomicidade distribuída).
- G4 `assert line.strip() == line or True` em presentation homologation: residual na task de qualidade; **corrigido em T2 full acceptance** (ver seção seguinte).

### Regressão desta execução

| Suite | Resultado |
|---|---|
| Core `app/tests/` | **413 PASS / 0 FAIL** |
| Core MCP focused (policy/lifecycle/authz/use_case) | **34 PASS / 0 FAIL** |
| DÉLIA MCP focused (resume/eligibility/registry/egress/adapter/native) | **74 PASS / 0 FAIL** |
| DÉLIA `tests/` full | **1473 PASS / 0 FAIL** (baseline 1472 + 1 mutação cancel) |
| DEV S2S eligibility live (este container: mode≠core, token ausente) | **TEST_NOT_RUN** |
| Real multi-turn revocation harness | **TEST_NOT_RUN** (cobertura contratual A–H) |
| Outcome ACT live | **TEST_NOT_RUN** |

### Status gates

| ID | Status |
|---|---|
| A-07 | `IMPLEMENTED_BOUNDED_DEV` (não CLOSED_PROVEN) |
| R04 | `PENDING_OPS` |
| T2_ARCHITECTURE_GATE | quality slice ready for independent review; ownership/ExternalConnection/R04 ops still open |

**OPEN_MATERIAL:** ExternalConnection; R04 ops; DNS-rebinding/proxy; Outcome ACT; TOCTOU Core→wire
**NEXT:** `T2_INDEPENDENT_REVIEW`
**PRODUCTION_DEPLOY / T3:** `NOT_AUTHORIZED`

## T2 FULL IMPLEMENTATION + INTEGRATED ACCEPTANCE (2026-11-09)

**TASK_ID:** `DELIA-T2-FULL-IMPLEMENTATION-REMEDIATION-AND-INTEGRATED-ACCEPTANCE-01`
**BASE_HEAD:** `d8097eb033…` (ancestral `eda3121a6a`)
**SCOPE:** G4 + Core registry DEV + DÉLIA mode=core + revogação E2E + regressões; sem T3/prod.

### G4

- Defect: `test_pipeline_serializes_json_and_single_line_ndjson` usava `or True`.
- Fix: wire NDJSON single-line estrito + `test_ndjson_wire_assertion_rejects_raw_newline`.
- RED/GREEN: mutação multi-line rejeitada; suite G4 PASS.

### Core + DÉLIA DEV runtime

| Check | Resultado |
|---|---|
| Migration `u7v8w9x0y1` | PROVEN |
| Seed 7 providers | PROVEN (3 enabled / 4 disabled) |
| Compose wiring mode+token | PROVEN (`docker-compose.dev.yml`) |
| `DELIA_MCP_PROVIDER_REGISTRY_MODE=core` | PROVEN (infra/.env gitignored) |
| S2S eligible + scope | PASS (`davi,teo,vista` / `provider_approval_only`) |
| Disable davi → guard/composition | PASS (`mcp_provider_not_eligible`; teo ok) |
| Restore parity | PASS |
| Bad token | PASS fail-closed |
| Rollback settings↔core | PASS |
| Final DEV mode | `core` |
| User-delegated tools/list READ live | TEST_NOT_RUN |
| Outcome ACT live | TEST_NOT_RUN |

### Regressão

| Suite | Resultado |
|---|---|
| Core full | **413 PASS / 0 FAIL** |
| DÉLIA full | **1474 PASS / 0 FAIL** |
| G4 homologation | **PASS** |

### R04 OPS HANDOFF (permanece PENDING_OPS)

**OWNER:** Ops / delivery DÉLIA (flag de composição produtiva).
**PROBLEM:** produção ainda pode carregar `DELIA_MCP_CATALOG_MODE=snapshot_experiment` (contradiz RETIRE_FULL_SET no código).
**AUTHORIZED_DEV:** N/A para mutação prod.
**PROCEDURE (quando PRODUCTION_DEPLOY autorizado separadamente):**

1. Confirmar imagem/SHA com snapshot experiment removido do código.
2. Via processo local-first: config `DELIA_MCP_CATALOG_MODE=live` (ou unset) + remover `DELIA_MCP_CATALOG_DB` se residual.
3. Restart apenas serviços afetados; health/readiness.
4. Smoke: discovery live SpecialistInterop/MCPToolset; ausência de path snapshot.
5. Evidência: env efetiva + logs sem secret + turn READ amostral.
6. Rollback: restaurar env anterior apenas se autorizado e documentado.

**STATUS:** `PENDING_OPS` — handoff pronto; **não** `CLOSED_PROVEN`.

### Status gates

| ID | Status |
|---|---|
| A-07 | `IMPLEMENTED_BOUNDED_DEV` + DEV runtime evidence (não CLOSED_PROVEN) |
| R04 | `PENDING_OPS` |
| ExternalConnection | TARGET (fora T2 obrigatório) |
| T2_TECHNICAL_STATUS | READY_FOR_INDEPENDENT_REVIEW |

**OPEN_MATERIAL:** R04 ops prod; ExternalConnection; DNS/proxy; Outcome ACT; TOCTOU; delegated live READ
**NEXT:** `T2_INDEPENDENT_REVIEW`
**PRODUCTION_DEPLOY / T3:** `NOT_AUTHORIZED`

## T2 REAL DEV E2E + OUTCOME (2026-11-09)

**TASK_ID:** `DELIA-C3-T2-MCP-REAL-DEV-E2E-AND-OUTCOME-VALIDATION-01`

| ID | Status | Evidência |
|---|---|---|
| T01 tools/list | PASS (live drift) | DAVI: analyze/get_context/knowledge/read; auth delegada |
| T02 turn READ | INCONCLUSIVE/FAIL timeout | Domain FP a3dcef2068200898; turn 480s TimeoutError; davi.get_context ok mid-turn |
| T02b interop READ | PASS | SpecialistInterop davi.read get_product_structure → COMPLETED + 90260921 |
| T03 disable | PASS | admin disable/enable + expectedVersion; eligible restored |
| T04 resume multi-turn | TEST_NOT_RUN | contract A–H only |
| T05 user AuthZ neg | TEST_NOT_RUN | sem usuário negativo provisionado |
| T06 bad token | PASS | core_forbidden fail-closed |
| T07 isolation | PASS | teo eligible while davi blocked |
| T08 outcome | PARTIAL | Domain match PROVEN; full Delia answer not delivered |
| T09 cancel/deadline | PASS | pytest resume+G4 |
| T10 regression | PASS | Core 413/0; DÉLIA 1474/0 |

**LIVE_CONTRACT_DRIFT:** docs ainda citam `discover_delpi_information`/`execute_delpi_information`; owner api-delpi MCP vigente = surface `get_context/knowledge/read/analyze`.

**DEV_ROLLBACK:** DAVI enabled restaurado; eligible davi,teo,vista.

| ID | Status |
|---|---|
| A-07 | `IMPLEMENTED_BOUNDED_DEV` |
| R04 | `PENDING_OPS` |
| T2_TECHNICAL_STATUS | `ACCEPT_WITH_RESIDUAL` (proposta) |

**NEXT:** `T2_INDEPENDENT_REVIEW`
**PRODUCTION_DEPLOY / T3:** `NOT_AUTHORIZED`



## C3 SEMANTIC MCP + RESPONSE SYNTHESIS (2026-11-10)

**TASK_ID:** `DELIA-C3-SEMANTIC-MCP-PROGRESSION-RESPONSE-SYNTHESIS-AND-LEGACY-REMOVAL-01`

| Campo | Valor |
|---|---|
| ROOT_CAUSE_A | `_INVESTIGATION_INSTRUCTIONS` acopladas a `davi.execute_delpi_information` / `discover_*` / `candidate_token` universal + metadata DAVI `get_context` dizendo read/analyze não implementados |
| FIRST_DIVERGENCE_A | Agent recebia contrato/instruções obsoletas → falhava args de `davi.read` ou não progredia catalog→READ |
| ROOT_CAUSE_B | `_business_lines` substituía `data.root` por único item de `items`; síntese omitia `is_complete=false` do owner |
| FIRST_DIVERGENCE_B | Evidence citable com root 90260921, mas conteúdo renderizado/síntese perdia root e limitação parcial |
| REMEDIATION | Instruções generalistas v1; hints schema-derived; DAVI metadata live; render root+items; `owner_result_incomplete` |
| REAL_E2E | OpenRouter `qwen/qwen3-14b` (~49s): GROUNDED + OBSERVATION; read completed; 90260921 + 10020003 + is_complete=false |
| GENERALIZATION | Catalog live DAVI(4)/TEO(6)/VISTA(6) superfícies distintas; harness G04–G12 instructions-agnostic PASS |
| RESIDUAL | Comentário histórico `discover_delpi_information` em `generic_evidence_renderer.py` (HISTORICAL_REFERENCE); flake local_ollama sob budget 300s (BUDGET_REDESIGN=DEFERRED) |
| PHASE | NÃO avançada |
| NEXT | `T2_INDEPENDENT_REVIEW` |
| PRODUCTION_DEPLOY / T3 | NOT_AUTHORIZED |

## T2 INDEPENDENT REVIEW + QWEN14B PRODUCTION RELEASE (2026-11-10)

**TASK_ID:** `DELIA-C3-T2-INDEPENDENT-REVIEW-RESIDUAL-CLOSURE-QWEN14B-PRODUCTION-RELEASE-01`
**REVIEW_SHA / RELEASE_SHA / FINAL_HEAD:** `30ac7cbb4467f2d4703f266a701979747857a54c`
**FUNC_REMEDIATION_SHA:** `f4eff148ff40d5b4d83b3099b08f3a6af918623f` (ancestral)
**MODEL:** `openrouter_qwen` / `qwen/qwen3-14b` (fingerprint profile `bbe33dd125948f32`)
**REFERENCE:** `openrouter_kimi` / `moonshotai/kimi-k3`

### Independent architecture (AR01–AR12)

| ID | STATUS | EVIDENCE |
|---|---|---|
| AR01 planner paralelo | PASS | único Agent Pydantic AI + MCPToolset; A-04 CLOSED |
| AR02 instruções sem MCP names | PASS | `_INVESTIGATION_INSTRUCTIONS` generalistas; harness decoupling PASS |
| AR03 discovery dinâmica | PASS | MCPToolset tools/list live |
| AR04 sem shadow catalog | PASS | Settings fail-closed CATALOG_*; SpecialistInterop only |
| AR05 MCP owner contract | PASS | DAVI/TÉO/VISTA owners |
| AR06 sem import BC bypass | PASS | ports/adapters; Core HTTP |
| AR07 MCP≠FACT sem Evidence | PASS | Evidence + grounding path |
| AR08 modelo≠autorização | PASS | instructions + AuthZ gates |
| AR09 READ≠WRITE | PASS | PREPARE/ACT não expostos |
| AR10 PREPARE/ACT separado | PASS | investigation instructions |
| AR11 structured output | PASS | JSON/output-tool contract |
| AR12 presentation≠facts | PASS | root+items + owner_result_incomplete |

### Residual matrix R01–R14

| ID | FINAL_STATUS | BLOCKS_RELEASE | NOTES |
|---|---|---|---|
| R01 semantic MCP | CLOSED_PROVEN | NO | E01/E02/P05 GROUNDED |
| R02 synthesis/Evidence | CLOSED_PROVEN | NO | root+items+is_complete; focused pytest PASS |
| R03 multi-MCP | CLOSED_PROVEN (bounded) | NO | DAVI/TEO PASS; VISTA flaky phrasing ACCEPTED_CONTROLLED_RISK |
| R04 catalog legado prod | CLOSED_PROVEN | NO | CATALOG_* absent; Settings fail-closed; live mode=core |
| R05 resume pós-revogação | ACCEPTED_CONTROLLED_RISK | NO | unit resume/eligibility PASS; live E10 not re-run on prod window |
| R06 User AuthZ negativo | ACCEPTED_CONTROLLED_RISK | NO | sem user negativo provisionado; 401 invalid token PASS |
| R07 Core S2S fail-closed | CLOSED_PROVEN | NO | unit + prior DEV E2E; bad token 401 |
| R08 DNS/proxy/egress | ACCEPTED_CONTROLLED_RISK | NO | endpoint_policy + egress controls; DNS-rebinding residual |
| R09 TOCTOU | ACCEPTED_CONTROLLED_RISK | NO | revalidate-at-invoke; atomicidade distribuída impossível |
| R10 Outcome ACT | OUT_OF_SCOPE_FUTURE_PHASE | NO | ACT prod não autorizado nesta task |
| R11 ExternalConnection | OUT_OF_SCOPE_FUTURE_PHASE | NO | TARGET_ONLY |
| R12 model profile parity | CLOSED_PROVEN | NO | container profile+model invocation verified |
| R13 Rollback | CLOSED_PROVEN | NO | digests anteriores capturados; procedure documentada |
| R14 deploy identity | CLOSED_PROVEN | NO | RUNTIME_SHA=HEAD; image digests pós-build |

### Production deploy

| Campo | Valor |
|---|---|
| SERVICES | `delia-api`, `api-delpi` |
| PROD_DELIA_IMG | `sha256:28af603572d67fb62b00abfba02d0216e2df60fa85b45077938a1653b4b2aabe` |
| PROD_APIDELPI_IMG | `sha256:7ea9dfd5baeaf7eef3e1b4273612644e362cc13288e8f77b06123b5c9be272b8` |
| ROLLBACK_DELIA_IMG | `sha256:07de3027e959e4ef31764f85e957eab3245dabd5c57595c599b89cd3bf8e3726` |
| ROLLBACK_APIDELPI_IMG | `sha256:d7eab622bdfb6c6b057fab10505a096954cf01a8b2188b5319dc7c552fb89aca` |
| PROFILE | `openrouter_qwen` effective |
| MCP_REGISTRY_MODE | `core` |
| CATALOG_VARS | ABSENT |
| PROD_URL | `http://localhost/` (Portal) / `http://localhost/apps/delia` |
| HEALTH | delia-api + api-delpi healthy; gateway curl 200 (wget UA 403 false-positive) |
| P05 DAVI | PASS GROUNDED qwen/qwen3-14b |
| P06 TEO | PASS GROUNDED |
| P07 VISTA | INCONCLUSIVE/flaky (clarification) — E04 anterior GROUNDED |
| P08 SIPOC | PASS GROUNDED |
| NDJSON | PASS `turn_result` terminal em `/interaction/turns` |

### Gates

| Gate | Status |
|---|---|
| RELEASE_GATE | GO (PO-authorized + technical gates) |
| A-07 | `IMPLEMENTED_BOUNDED_DEV` (ExternalConnection ainda TARGET) |
| R04 | `CLOSED_PROVEN` (runtime prod deste host) |
| T2_TECHNICAL_STATUS | `ACCEPT_WITH_RESIDUAL` (riscos controlados R05/R06/R08/R09; VISTA phrasing) |
| T2_RELEASE_STATUS | `DEPLOYED_QWEN14B` |
| PROD_READY_FOR_PO_MANUAL_TEST | YES |
| T3 | NOT_AUTHORIZED |

**NEXT_FROM_CANONICAL_PLAN:** homologação manual do PO; sem avanço T3.


## 2026-11-10 — PO failed homologation and T2-INT cognitive responsibility track (docs-only)

**Canonical owner/order:** doc 16; bounded execution map doc 293; execution state ledger. This entry **supersedes only prior functional acceptance claims**, without rewriting release history or negating reported runtime/image identities.

| Item | State | Evidence / limit |
|---|---|---|
| T2 release to production | DEPLOY_REPORTED / historical | Qwen14B release SHA 30ac7cbb reported; not functional acceptance |
| PO manual objective outcome | **FAIL** | Three PO queries failed to satisfy requested product structure, process listing, visualization formats |
| F1/F2 generalization claim | **STALE_EVIDENCE for broad success** | Isolated DAVI positive controls do not cover multi-turn PO failure |
| P1 root cause | **INCONCLUSIVE** | Reproduction PASS; original screenshot path discovery/metadata not traced to exact correlation |
| P2/P3 shared flow | **PROVEN boundary gap, remediation NOT_STARTED** | Relevant grounded evidence accepted despite failure of user-objective coverage; invalid arguments/churn |
| Independent DEV vs PROD parity | TEST_NOT_RUN | Executor had one shared production container; not two runtime environments |
| Runtime model in original PO turn | INCONCLUSIVE | Later Qwen invocations proven by executor, original PO correlation missing |
| Objective satisfaction | **FAIL / OPEN_MATERIAL** | Evidence validity/grounding distinct from semantic obligation satisfaction |
| Proposed multi-agent separation | **TO_INVENTORY** | Four cognitive responsibilities, not four approved Agents; Pydantic AI reuse-first |
| Current authorized next | **T2-INT0 inventory/specification only** | Agent investigation path first; no code/deploy/release/T3 |

**Corrective direction:** The same Pydantic AI runtime remains the primary investigation intelligence; inspect reuse in Application coverage/finalize and native Pydantic AI before authorizing any cognitive delegation. `EXISTING_EQUIVALENT=YES` for core investigation/MCPToolset/Evidence/Outcome, and `TO_INVENTORY` for independent cognitive evaluator. `REUSE_DECISION=REUSE|EXTEND` candidate, **not implementation authorization**. No provider/tool-specific instructions, no parallel planner, no model comparison or full-stack testing by default. Measure by objective satisfaction and evidence fidelity, not HTTP 200, GROUNDED, call count or token consumption alone.

**Residual status:** R04 production config closure historical unchanged. R05/R06/R08/R09 controlled risk classifications unchanged pending proper owner review. Outstanding P2/P3 semantic coverage gap is a **new material functional rework**, cannot be silently recast as accepted residual. T2 functional closure blocked, T3 still unauthorized. For stages/gates, see doc 293 T2-INT and doc 16 2026-11-10 decision.

## T2-INT0 — Investigative Agent reuse / contract inventory (2026-11-10)

**TASK_ID:** `DELIA-C3-T2-INT01-INVESTIGATIVE-INTELLIGENCE-NATIVE-PYDANTIC-AI-IMPLEMENTATION-AND-LOCAL-EVALUATION-01` (INT-0 slice only)
**BASE_HEAD (execution):** `45d031f724b340a0e443eed69034810461ed31d9` (contains origin `06abbd3b98` + unrelated PRC commit)
**ORIGIN_MAIN at start:** `06abbd3b98490663f82bb6e90c07782646035fcb`
**PYDANTIC_AI_VERSION (runtime container):** `2.50.0`
**CODE_CHANGES:** NONE (doc 293 INT-0 = TO_INVENTORY; sem código)
**INT1_AUTHORITY_GATE:** `AUTHORIZED_BOUNDED_CONDITIONAL` (coordination 2026-11-10) → INT-1 executed; pending **independent review** of implementation
**LOCAL_ENVIRONMENT:** `HOST_PYTEST_ISOLATED` — deterministic tests via `delia-api/.venv` without touching prod container; `LOCAL_LIVE_EVAL=TEST_NOT_RUN` because compose.dev still shares `container_name: delpi-delia-api` with production

### Responsibility inventory

| RESPONSIBILITY | OWNER | CANONICAL_CONTRACT | CONSUMERS | CURRENT_IMPLEMENTATION | CURRENT_FAILURE | EXISTING_EQUIVALENT | REUSE_DECISION |
|---|---|---|---|---|---|---|---|
| I01 investigation understanding | `PydanticAiInvestigationOrchestrator` + optional `declare_investigation_goal` → `SemanticInvestigationPlan` | Agent instructions + plan tool; plan **optional** for simple READ | finalize / obligations | `_INVESTIGATION_INSTRUCTIONS` **generalist-semantic-v2**; plan tool exists | Without plan, finalize has no typed obligation of *kind* (list vs aggregate) — INT-3 Outcome | YES | EXTEND (done signals; Outcome remains INT-3) |
| I02 capability discovery | MCPToolset live + `_project_semantic_tool_catalog` | tools/list; SpecialistInterop | Agent tool surface | Native MCPToolset ×3 (davi/teo/vista) + catalog project | Discovery content can still reach user path if not tagged | YES | REUSE |
| I03 semantic selection | Agent (Pydantic AI) | live tool descriptions/schemas | governed invoke | Model selects among live tools; progress/coverage notes on projections | Live Qwen selection still unverified (`TEST_NOT_RUN`) | YES | EXTEND (progress signals shipped) |
| I04 argument generation | Agent + schema hints + `focus_arguments_on_next_identifier` + ModelRetry on serialized dicts | owner JSON Schema | `_governed_semantic_tool_invoke` | arg_type_gate + **owner_argument_rejected ModelRetry** with `owner_validation_hint` | Live recovery still unverified | YES | EXTEND (recovery shipped) |
| I05 governed invocation | `OperationalCapabilityOrchestrator._governed_semantic_tool_invoke` / gates | Policy/AuthZ/eligibility | investigation process_tool_call | Port + Core eligibility + Domain | Intact; not the PO objective failure | YES | REUSE |
| I06 evidence interpretation | `_is_business_evidence_attempt` + `classify_investigation_progress` | GovernedCapabilityAttempt / Evidence | finalize, CRI, Agent projection | Filters discovery; **progress classes** NEW/NO_PROGRESS/RELATED/DISCOVERY | Related SUCCESS still citable as business when plan absent (Outcome INT-3) | YES | EXTEND (shipped) |
| I07 investigation progress | `non_progress_calls` + content fingerprints + equivalent rejection fp | repeated_failure_no_progress / repeated_observation_no_progress | Agent instructions | Exact args + owner_argument_rejected class after one recovery | Live churn unverified | YES | EXTEND (shipped) |
| I08 recovery | ModelRetry + `owner_validation_hint` | SpecialistOutcome / CapabilityProviderError.owner_hint | Agent | One-shot ModelRetry on owner_argument_rejected | Second equivalent rejection blocked as non-progress | YES | EXTEND (shipped) |
| I09 continuation | Agent loop + tool_calls_limit / budgets + COMPLETE/uncovered ModelRetry | profile agent.tool_calls_limit | orchestrator | Continues; COMPLETE with uncovered ids retries once | May still finalize related-only when plan absent | YES | EXTEND (partial; INT-3) |
| I10 investigation output | `InvestigationAnswer` → `_apply_declared_answer` / `_finalize_agent_collected_attempts` | contracts.InvestigationAnswer | interaction / presentation | Structured output + acceptor; `related_observations_insufficient` when plan obligations/REF05 fail | plan-absent objective-kind gate still INT-3 | YES | EXTEND (signals; Outcome INT-3) |
| Coverage / Outcome final | Application finalize + Evidence | Outcome contracts | HTTP/NDJSON | `_evaluate_material_obligations` only when plan.evidence_needed set | **Gap:** no plan ⇒ no material obligation check ⇒ related aggregates accepted | YES | REUSE now; INT-3 owns independent sufficiency |
| AuthZ / Policy | Core + Domain + gates | existing | all invokes | intact | N/A | YES | REUSE |

### First divergence (falsifiable)

```text
H_PRIMARY:
  When SemanticInvestigationPlan is absent (optional for simple READ),
  _finalize_agent_collected_attempts treats any _is_business_evidence_attempt
  SUCCESS as terminal SUCCESS, without checking whether the observation's
  semantic kind satisfies the user objective (list vs aggregate vs docs).

H_SUPPORTING:
  Agent tool selection lacks a native signal distinguishing purpose classes
  across live MCP descriptions; owner_argument_rejected recovery is weak;
  discovery metadata leak is partially gated but presentation can still expose catalogs.
```

Proven by prior forensic correlations (teo.read reject → teo.analyze SUCCESS → GROUNDED aggregates) and code path `semantic_capability_support.py` finalize when `business` non-empty and `obligations` empty.

### Native Pydantic AI capabilities available (v2.50.0)

Agent, structured output, MCPToolset, process_tool_call, ModelRetry, usage/tool limits — **already in use**. No missing framework prerequisite for EXTEND. New Agent **not** justified by INT-0.

### INT-1 experiment status (2026-11-10)

**AUTHORIZED_BOUNDED_CONDITIONAL** executed. Shipped:

1. `classify_investigation_progress` + projection `investigation_progress` / coverage notes (NEW_INFORMATION / NO_PROGRESS / RELATED_INSUFFICIENT / DISCOVERY_ONLY).
2. One-shot `owner_argument_rejected` ModelRetry with `owner_validation_hint`; equivalent rejection non-progress after recovery.
3. Finalize limitation `related_observations_insufficient` when related business fails plan obligations/REF05; discovery remains non-citable.
4. Focused suite `test_int1_investigative_progress_rework.py` + metamorphic rename-invariant progress.

**Not shipped (by design):** INT-2/3/4; compulsory SemanticInvestigationPlan; live Qwen P1–P3 (`TEST_NOT_RUN`); new Outcome evaluator.

**NEXT:** `COORDINATION_INT1_INDEPENDENT_REVIEW`.
**PRODUCTION_DEPLOY / T3 / INT2:** NOT_AUTHORIZED.

### INT-1 final bounded rework F1–F4 (2026-11-10)

**TASK:** `DELIA-C3-T2-INT1-FINAL-BOUNDED-REWORK-AND-ACCEPTANCE-01`
**REVIEWED_SHA:** `7cd27e6d0cbc6f401fca9a5fc93282eac54073a0`
**INT1_REWORK_BUDGET_EXHAUSTED:** YES

| Fix | Change | Evidence |
|---|---|---|
| F1 | Identical fingerprint short-circuit only; material arg change still invokes; one-shot owner ModelRetry | `test_f1_identical_rejection_short_circuits_but_new_args_invoke` |
| F2 | Progress ignores READ/ANALYSIS class; obligations + structure decide | `test_f2_analysis_adequate_*` / `test_f2_read_inadequate_*` |
| F3 | Real Agent path + metamorphic rename | `test_f3_agent_path_*` / `test_f3_metamorphic_*` |
| F4 | plan absent → `coverage_unknown` on fast SUCCESS; related+plan stays NOT_APPLICABLE | `test_f4_*` |

**LOCAL_QWEN_EVAL (at F1–F4 close):** was `TEST_NOT_RUN` — superseded by isolated live eval stamp below.
**Proposal (code review only):** ACCEPT_WITH_RESIDUAL → then real-eval gate.

### INT-1 isolated real Qwen evaluation (2026-11-10)

**TASK:** `T2_INT1_ISOLATED_REAL_QWEN_EVAL_GATE`
**LIVE_EVAL:** EXECUTED (isolated container + OpenRouter proxy; prod untouched)
**MODEL:** `qwen/qwen3-14b` / `openrouter_qwen`

| Residual | Class | Notes |
|---|---|---|
| P3 selected `analyze` dashboards for “formatos de visualização” | INVESTIGATION_SELECTION | Related-insufficient vs operational viz catalog; no code rework (budget exhausted) |
| G1 semantic reword missed structure tree | INVESTIGATION_CONTINUITY | Identity found; structure not recovered on reword |
| Tool-rename MCP generalization | TEST_NOT_RUN | No isolated rename MCP without new architecture |
| MCP READ backends on prod docker network | ENVIRONMENT | Eval process isolated; owner READ services shared |
| INT-3 Outcome sufficiency / plan-absent | DEFERRED | `coverage_unknown` preserved; not INT-1 Outcome authority |
| MODEL_PING empty on short OpenAI client probe | NON_BLOCKING | Full Agent turns invoked model successfully |

**Proposal:** `ACCEPT_WITH_RESIDUAL` → `COORDINATION_INT1_REAL_EVAL_INDEPENDENT_REVIEW`
**INT1_REWORK_BUDGET_EXHAUSTED:** YES


## 2026-11-10 — INT-1 real Qwen independent review: material failures / eval harness security hold

| ID | Classification | Evidence / next |
|---|---|---|
| INT1-P3 semantic selection | **OPEN_MATERIAL / FAIL** | Real Qwen selected dashboard analyze rather than operational visualization-format catalog; objective not met |
| INT1-G1 semantic reword | **OPEN_MATERIAL / FAIL** | Real Qwen found identity but not requested BOM tree |
| INT1-MCP-RENAME | **TEST_NOT_RUN** | Real renamed-tool selection not exercised; prior FunctionModel tests do not prove this |
| INT1-P1-P2 | **PARTIAL_OUTCOME** | Owner evidence acquired with incomplete/truncated coverage, not global completion |
| INT1-EVAL-CREDENTIAL-ISOLATION | **TO_VERIFY / SECURITY_REVIEW_REQUIRED** | Eval script copies prod `printenv`, selectively filters and supplies to eval container; separation of processes != separation of credentials |
| INT1-EVAL-EGRESS | **TO_VERIFY / SECURITY_REVIEW_REQUIRED** | Host proxy bound 0.0.0.0; script describes use of localhost route to pass application egress guard; requires authorized egress-policy review |
| INT1-REWORK-BUDGET | **EXHAUSTED** | No automatic functional rework |

**Stage:** `INT1_STAGE_ACCEPTANCE=BLOCKED`, `INT1_CLOSED=NO`; `NEXT=T2_INT1_EVAL_ENV_SECURITY_AND_BLOCKER_DECISION`. No assertion of actual secret exposure or runtime write; production restart not observed in executor evidence. No promotion/INT2/T3/production deploy authorization.

## 2026-11-11 — INT-1 consolidated root-cause inventory (diagnosis; no code)

**TASK:** `DELIA-C3-T2-INT1-CONSOLIDATED-ROOT-CAUSE-AND-SECURITY-INVESTIGATION-01`

| ID | Classification | Evidence / next |
|---|---|---|
| INT1-P3 | **ROOT_CAUSE_PROVEN (selection)** | Live eval invoked TEO `analyze`→`dashboard_*`; VISTA live surface has no `get_catalog`/`get_product_guide` (forbidden); successors `knowledge`/`read`. Exact eligible catalog_caps line missing → eligibility residual INCONCLUSIVE |
| INT1-G1 | **ROOT_CAUSE_PROVEN (single-turn selection/args)** | Independent reword without prior; tools≠BOM path that P1 used successfully |
| INT1-P1 | **OWNER_LIMITATION_PRIMARY** | `owner_result_incomplete` + partial structure; investigation ended with honest partial |
| INT1-P2 | **OWNER_TRUNCATION + INVESTIGATION_CONTINUATION_GAP** | TEO `page`/`page_size` exist; Agent noted page=2 but did not continue |
| INT1-COVERAGE-OUTCOME | **CONTRACT_BOUNDARY (F4)** | `SUCCESS`+`coverage_unknown` when plan/obligations absent — INT-1 marks unknown; INT-3 owns objective satisfied |
| INT1-HARNESS-SECURITY | **EXECUTION_DRIFT PROVEN** | Prod printenv copy; 0.0.0.0 OpenRouter proxy; localhost-shaped base URL passes nonprod egress guard |
| INT1-REWORK-BUDGET | **EXHAUSTED** | No automatic functional rework from this diagnosis |

**Stage unchanged:** `INT1_STAGE_ACCEPTANCE=BLOCKED`, `INT1_CLOSED=NO`, `HARNESS_REUSE=BLOCKED`. **NEXT=`COORDINATION_T2_INT1_CONSOLIDATED_CAUSAL_REVIEW`**.

## 2026-11-11 — INT-1 P3/G1 exact decision forensics

**TASK:** `DELIA-C3-T2-INT1-P3-G1-EXACT-DECISION-FORENSICS-01`

| ID | Classification | Notes |
|---|---|---|
| INT1-P3-FIRST-TOOL | **OBSERVED** `analyze`×2; TEO dashboard content | Specialist label in stdout collapsed to `MCP:` |
| INT1-P3-TOOL-SURFACE | **MISSING** | Cannot prove VISTA knowledge/read were/weren't in Agent toolset that turn |
| INT1-P3-ARGS | **MISSING** | Container `/tmp/delia_eval_artifacts` destroyed; stdout filtered records |
| INT1-P3-NON-RECOVERY | **PROVEN_BY_CODE** | plan-absent → progress NEW not RELATED; finalize accepts partial+coverage_unknown |
| INT1-G1-SEQUENCE | **OBSERVED** diverges from P1 at step1 | P1 get_context→read; G1 read→…→knowledge×2 |
| INT1-G1-ARGS / structure op | **MISSING / INCONCLUSIVE** | No proof get_product_structure was or wasn't called |
| INT1-EVAL-ARTIFACT-CAPTURE | **DEFECT (observability)** | Rich records not host-persisted; blocks exact causal close |

**NEXT=`COORDINATION_INT1_EXACT_CAUSAL_DECISION`**. `INT1_STAGE_ACCEPTANCE=BLOCKED`.

## 2026-11-11 — Secure eval gate + decision-trace observability prep

**TASK:** `DELIA-C3-T2-INT1-SECURE-EVAL-AND-FULL-DECISION-TRACE-01`

| ID | Classification | Notes |
|---|---|---|
| INT1-SECURE-EVAL-GATE | **BLOCKED** | No security-owner-approved nonprod OpenRouter path; no separate eval credentials proven; target model 14B unavailable locally as required id |
| INT1-HARNESS-BYPASS | **STILL_FORBIDDEN** | Do not reuse `run_int1_isolated_qwen_eval.sh` / `openrouter_local_egress_proxy.py` |
| INT1-DECISION-TRACE-OBS | **PREPARED_PASS (dry-run)** | Host-persistent JSONL capture schema validated; real Agent wiring pending authorized eval |
| INT1-REAL-P3-G1 | **TEST_NOT_RUN** | Blocked by security gate |

**NEXT=`COORDINATION_INT1_DECISION_TRACE_REVIEW`**. Stage acceptance remains BLOCKED.

## 2026-11-11 — OpenRouter Qwen14B instrumented causal eval (PO correction)

**TASK:** `DELIA-C3-T2-INT1-LOCAL-QWEN14B-SETUP-AND-INSTRUMENTED-ROOT-CAUSE-EVAL-01`
**EVAL_ID:** `or-qwen14b-35aaf1a4174b`
**MODEL:** `qwen/qwen3-14b` / `openrouter_qwen` / pydantic-ai `2.50.0`
**SECURE_EVAL_GATE:** `READY_FOR_ISOLATED_EVAL` (allowlist + `DELIA_EVAL_EGRESS_AUTHORIZED=1`; no localhost proxy)

| ID | Classification | Evidence / next |
|---|---|---|
| INT1-EGRESS-ALLOWLIST | **PROVEN_FOR_EVAL** | Settings allowlist `openrouter.ai` under eval flag; real host used |
| INT1-P3-FIRST-DIVERGENCE | **PROVEN** | First MCP=`vista.read` (422); never `teo.analyze`; recovery `teo.knowledge` → GROUNDED+`coverage_unknown` |
| INT1-G1-FIRST-DIVERGENCE | **PROVEN** | First MCP=`teo.read` vs P1 `davi.get_context`; no `get_product_structure` on G1 |
| INT1-P1-CONTROL | **GROUNDED_PARTIAL** | `davi.get_context`→`davi.read` BOM; `owner_result_incomplete`+`coverage_unknown` |
| INT1-CREDENTIAL-ISOLATION | **RESIDUAL** | Selective infra/.env keys — not a separate eval secret scope |
| INT1-OLLAMA-14B | **CANCELLED** | Do not install/replace local 14B; keep `qwen3:8b` |
| INT1-FUNCTIONAL-REWORK | **NOT_AUTHORIZED** | Diagnosis only; budget exhausted |

**NEXT=`COORDINATION_INT1_OPENROUTER_INSTRUMENTED_CAUSAL_REVIEW`**. `INT1_STAGE_ACCEPTANCE=BLOCKED`; `INT2/T3/PRODUCTION_DEPLOY=NOT_AUTHORIZED`.

## 2026-11-11 — Causal report persistence (doc 294)

**TASK:** `DELIA-C3-T2-INT1-OPENROUTER-CAUSAL-REPORT-PERSISTENCE-01`

| ID | Classification | Notes |
|---|---|---|
| INT1-CAUSAL-REPORT-PUBLISHED | **DOC_ONLY** | Sanitized self-contained report in corrections/294; review pending |
| INT1-RAW-TRACES | **LOCAL_ONLY** | `.battery` JSONL not committed |
| INT1-STAGE | **BLOCKED** | Publication ≠ acceptance |

**NEXT=`COORDINATION_INT1_PUBLISHED_CAUSAL_REPORT_REVIEW`**.

## 2026-11-11 — INT-1 instruction candidate not promoted

**TASK:** `DELIA-C3-T2-INT1-SPECIALIZED-INSTRUCTIONS-AND-REAL-GENERALIZATION-EVOLUTION-01`

| ID | Classification | Notes |
|---|---|---|
| INT1-INSTR-ISOLATION | **DONE** | JSON resource + loader; baseline default |
| INT1-CANDIDATE-V3 | **NOT_PROMOTED** | P1 structure regression; P2 grounding regression |
| INT1-P3-G1-GAIN | **OBSERVED_NOT_SUFFICIENT** | Gains do not outweigh known-case regressions |
| INT1-STAGE | **BLOCKED** | Review required |

**NEXT=`COORDINATION_INT1_SPECIALIZED_INSTRUCTIONS_INDEPENDENT_REVIEW`**.

## 2026-11-11 — INT-1 instruction ablation (2º ciclo PO; no composite)

**TASK:** `DELIA-C3-T2-INT1-INSTRUCTION-ABLATION-AND-REGRESSION-FREE-EVOLUTION-01`

| ID | Classification | Notes |
|---|---|---|
| INT1-ABLATION-G-OBJ | **REGRESSION_ASSOCIATED** | P2 NON_GROUNDED; P3 NON_GROUNDED + tool limit |
| INT1-ABLATION-G-PROG | **REGRESSION_ASSOCIATED** | P3 GROUNDED with TEO dashboard metrics (wrong evidence) |
| INT1-ABLATION-G-DISC | **NO_DEMONSTRATED_BENEFIT** | P3 clarification; no unique gain vs v2 |
| INT1-ABLATION-G-EFF | **NOT_EVALUATED** | Outside 3-group budget |
| INT1-ABLATION-G1-FIRST-TOOL | **PROMISING_BUT_INCONCLUSIVE** | davi-first on OBJ/PROG (1 rep; stochastic baseline also BOM) |
| INT1-COMPOSITE-CANDIDATE | **NONE** | No sustained regression-free package |
| INT1-DEFAULT | **v2 preserved** | `7dbc94c5035b0f19` |
| INT1-CREDENTIAL-ISOLATION | **RESIDUAL** | Shared infra LLM key scope unchanged |
| INT1-STAGE | **BLOCKED** | Independent review of ablation |

**NEXT=`COORDINATION_INT1_INCREMENTAL_EVOLUTION_INDEPENDENT_REVIEW`**. `INT2/T3/PRODUCTION_DEPLOY=NOT_AUTHORIZED`.

## 2026-11-11 — INT-1 v2 stability diagnostic residuals

**TASK:** `DELIA-C3-T2-INT1-V2-STABILITY-AND-OBJECTIVE-SATISFACTION-DIAGNOSTIC-01`

| ID | Classification | Notes |
|---|---|---|
| INT1-EVAL-MCP-AUTH-LIFETIME | **OPEN / PROVEN** | 17/24 runs `catalog_failure:mcp_authentication_failed` or zero-tool `delpi_source_unverified` after early scenarios |
| INT1-V2-SELECTION-STABILITY | **INCONCLUSIVE** | Cannot claim 3-rep stability until harness auth fixed |
| INT1-P1-DAVI-TO-TEO-DRIFT | **OBSERVED (n=1 valid)** | Suitable first tool then TEO product reads; finalize unverified |
| INT1-P2-PAGINATION | **KNOWN_RESIDUAL** | Truncation without continuation (valid-env PARTIAL) |
| INT1-H4-VALID-SAMPLE | **MISSING** | All H4 reps env-invalid in this battery |
| INT1-CREDENTIAL-ISOLATION | **RESIDUAL** | Shared infra OpenRouter key scope |
| INT1-INT2-INT3-IMPL | **NOT_AUTHORIZED / NOT_JUSTIFIED_BY_THIS_BATTERY** | Fix eval validity first |
| INT1-STAGE | **BLOCKED** | Review ownership recommendations in doc 297 |

**NEXT=`COORDINATION_INT1_STABILITY_AND_OWNERSHIP_INDEPENDENT_REVIEW`**.

## 2026-11-11 — INT-1 MCP auth remediation + valid v2 stability rerun residuals

**TASK:** `DELIA-C3-T2-INT1-MCP-EVAL-AUTH-LIFETIME-REMEDIATION-AND-V2-STABILITY-RERUN-01`

| ID | Classification | Notes |
|---|---|---|
| INT1-EVAL-MCP-AUTH-LIFETIME | **REMEDIATED_IN_HARNESS** | Per-scenario `acquire_subject_access_session`; 24 unique token fingerprints; catalog preflight OK×24 |
| INT1-V2-SELECTION-STABILITY | **OBSERVABLE (n=3 valid/scenario)** | G1 TEO-first 3/3; P3 first-tool unstable (vista/teo/vista); H4 teo:analyze 3/3 PARTIAL |
| INT1-P2-PAGINATION | **CONFIRMED_VALID_ENV** | PARTIAL×3; continuity gap remains |
| INT1-G1-SELECTION | **OPEN_MATERIAL** | UNSUITABLE/PARTIALLY_SUITABLE TEO path vs DAVI structure obligation |
| INT1-P3-SELECTION | **OPEN_MATERIAL** | Includes one `teo:analyze` + Gwo dashboard-as-formats |
| INT1-H4-VALID-SAMPLE | **OBTAINED** | 3/3 env-valid; objective PARTIAL (not SAT) |
| INT1-CREDENTIAL-ISOLATION | **RESIDUAL** | `NONE_PROVEN_SEPARATE_FROM_PROD` unchanged |
| INT1-INT2-IMPL | **NOT_AUTHORIZED / NOT_PROVEN_REQUIRED** | Objective representation gap not proven mandatory |
| INT1-INT3-IMPL | **NOT_AUTHORIZED / NOT_AUTO_JUSTIFIED** | One coverage-gap signal; inventory before any INT-3 |
| INT1-STAGE | **BLOCKED** | Doc 298; independent review of valid stability + ownership |

**NEXT=`COORDINATION_INT1_VALID_STABILITY_INDEPENDENT_REVIEW`**. `INT2/T3/PRODUCTION_DEPLOY=NOT_AUTHORIZED`.

## 2026-11-11 — INT-1 context / tool-surface / recovery residuals

**TASK:** `DELIA-C3-T2-INT1-INVESTIGATION-CONTEXT-TOOL-SURFACE-AND-RECOVERY-REMEDIATION-01`

| ID | Classification | Notes |
|---|---|---|
| INT1-TOOL-DESC-TRUNCATION-500 | **REMEDIATED** | EnvelopeHint no longer shortens published MCP descriptions |
| INT1-PAGINATION-PROJECTION | **REMEDIATED** | `_attempt_projection` reuses `extract_pagination_envelope`; N2 live pages 1→7 |
| INT1-P3-TEO-ANALYZE-FIRST | **IMPROVED** | Corrected battery: VISTA-first only (0× teo.analyze first) |
| INT1-G1-TEO-DECOMPOSITION-ATTRACTOR | **OPEN** | Still TEO-first ×3 after description fix; owner semantic overlap |
| INT1-P2-CONTINUITY-RELIABILITY | **PARTIAL** | Some page continuation; not consistent across 3 reps |
| INT1-CATALOG-DTO-DESC-320 | **REMEDIATED** | Catalog DTO preserves full owner descriptions (doc 300) |
| INT1-CATALOG-HARD-CAP-80 | **REMEDIATED→CAP256** | Soft cap raised to safety 256 + overflow log; INT-1 surface ≪ cap |
| INT1-BOUNDED-JSON-SILENT-OVERVIEW | **REMEDIATED** | Essential-field overflow preserves pagination/limitations/continuation |
| INT1-CONTENT-SLICE-2000 | **REMEDIATED** | Projection/compose no longer hard-slice content before budget serializer |
| INT1-QWEN-CONTEXT-32768 | **REMEDIATED** | `openrouter_qwen` effective window = 40960 |
| INT1-G1-TEO-DECOMPOSITION-ATTRACTOR | **OPEN / OWNER_CHANGE_REQUIRED** | TEO `decomposition_tree` = process WBS ≠ product BOM; no local DÉLIA rewrite |
| INT1-LIVE-FULL-CONTEXT-RERUN | **BLOCKED** | Security/credential gate; live 8×3 not run in doc 300 |
| INT1-CREDENTIAL-ISOLATION | **RESIDUAL** | Unchanged |
| INT1-INT2-INT3-IMPL | **NOT_AUTHORIZED** | Not auto-justified |
| INT1-STAGE | **BLOCKED** | Doc 300 independent review |

**Independent inventory corroboration (post-299):** [Investigation context audit](21a43e92-fe4a-457c-94eb-8ea775194bce) reconfirmed F1/F2 (description `[:500]`, missing pagination fields), native Pydantic AI loop, deps non-visible, and owner-agnostic selection — consistent with remediations already landed in `5b0fbab313`.

**NEXT=`COORDINATION_INT1_CONTEXT_AND_RECOVERY_INDEPENDENT_REVIEW`**.

## 2026-11-11 — INT-1 full context + MCP semantic contract residuals

**TASK:** `DELIA-C3-T2-INT1-FULL-CONTEXT-AND-MCP-SEMANTIC-CONTRACT-REMEDIATION-01`

| ID | Classification | Notes |
|---|---|---|
| INT1-FULL-CONTEXT-CODE | **REMEDIATED** | Catalog/bounded_json/content/config path |
| INT1-MCP-G1-OWNER-AMBIGUITY | **OPEN** | Owner TEO must clarify decomposition_tree ≠ BOM |
| INT1-LIVE-EVAL-THIS-TASK | **TEST_NOT_RUN** | `SECURE_EVAL_GATE=BLOCKED` |
| INT1-CREDENTIAL-ISOLATION | **RESIDUAL** | Unchanged |
| INT1-STAGE | **BLOCKED** | Doc 300 review |
| INT1-CLOSED | **NO** | — |

**NEXT=`COORDINATION_INT1_FULL_CONTEXT_INDEPENDENT_REVIEW`**. `INT2/T3/PRODUCTION_DEPLOY=NOT_AUTHORIZED`.

## 2026-11-11 — INT-1 intent / tool-selection causal residuals

**TASK:** `DELIA-C3-T2-INT1-INTENT-UNDERSTANDING-AND-TOOL-SELECTION-CAUSAL-REVIEW-01`

| ID | Classification | Notes |
|---|---|---|
| INT1-G1-FIRST-TOOL-TEO-DECOMPOSITION | **PROVEN_IN_SAMPLE** | first MCP `teo.read` decomposition_tree/process; DAVI structure available |
| INT1-GOAL-DECLARATION-UNUSED | **PROVEN_IN_SAMPLE** | 0/55 traces called `declare_investigation_goal` |
| INT1-UNCOVERED-PROJECTION-CANONICAL | **REMEDIATED** | uncovered/coverage now inside `_attempt_projection` |
| INT1-BUSINESS-SUBJECT-ECHO | **REMEDIATED** | declare ACCEPTED echoes `business_subject` |
| INT1-TEO-OWNER-DESC-AMBIGUITY | **OPEN / OWNER_CHANGE_REQUIRED** | process WBS ≠ product BOM |
| INT1-LIVE-INTENT-RERUN | **PENDING_PO_AUTHORIZATION** | minimal live proposal in doc 301 |
| INT1-STAGE | **BLOCKED** | Doc 301 review |
| INT1-CLOSED | **NO** | — |

**NEXT=`COORDINATION_INT1_INTENT_SELECTION_INDEPENDENT_REVIEW`**. `INT2/T3/PRODUCTION_DEPLOY=NOT_AUTHORIZED`.

## 2026-11-11 — INT-1 minimal real G1+P1 eval residuals

**TASK:** `DELIA-C3-T2-INT1-INTENT-VS-TOOL-SELECTION-MINIMAL-REAL-QWEN-EVAL-01`

| ID | Classification | Notes |
|---|---|---|
| INT1-MINIMAL-LIVE-G1-P1 | **BLOCKED** | Security/egress/credential gates; MODEL_REQUESTS=0 |
| INT1-CREDENTIAL-ISOLATION | **RESIDUAL** | `NONE_PROVEN_SEPARATE_FROM_PROD` — PO two-scenario auth ≠ credential-owner approval |
| INT1-EGRESS-HOST-SESSION | **BLOCKED** | `DELIA_EVAL_EGRESS_AUTHORIZED` absent; Settings model mismatch |
| INT1-TEO-OWNER-DESC-AMBIGUITY | **OPEN** | unchanged (prior docs) |
| INT1-STAGE | **BLOCKED** | Doc 302 review |
| INT1-CLOSED | **NO** | — |

**NEXT=`COORDINATION_INT1_MINIMAL_REAL_INTENT_EVAL_REVIEW`**. `INT2/T3/PRODUCTION_DEPLOY=NOT_AUTHORIZED`.

## 2026-11-11 — INT-1 G1/P1 real Qwen eval-02 residuals

**TASK:** `DELIA-C3-T2-INT1-G1-P1-REAL-QWEN-INTENT-SELECTION-EVAL-02`  
**EVAL_ID:** `or-qwen14b-198e127edee9` · **SHA:** `3d1a445189…` · Doc **303**

| ID | Classification | Notes |
|---|---|---|
| INT1-MINIMAL-LIVE-G1-P1 | **EXECUTED** | Isolated OpenRouter runner; supersedes doc302 host-Settings false-negative |
| INT1-G1-FIRST-TOOL-TEO-DECOMPOSITION | **PROVEN_IN_SAMPLE (live)** | `teo.read` entity=`decomposition_tree` params.id=90260921 despite DAVI BOM visible |
| INT1-G1-RECOVERY-TO-DAVI-BOM | **PROVEN_IN_SAMPLE** | After TEO miss → `davi.get_context` → `davi.read` `get_product_structure` |
| INT1-P1-DAVI-FIRST | **PROVEN_IN_SAMPLE** | Control: DAVI catalog → product structure; TEO unused |
| INT1-GOAL-DECLARATION-UNUSED | **PROVEN_IN_SAMPLE (live)** | 0/2 scenarios called `declare_investigation_goal` |
| INT1-OBJECTIVE-PARTIAL-OWNER | **OPEN** | Both GROUNDED+PARTIAL with `owner_result_incomplete` / depth |
| INT1-TEO-OWNER-DESC-AMBIGUITY | **OPEN / OWNER_CHANGE_REQUIRED** | Process WBS vs product BOM attractor unchanged |
| INT1-STATISTICAL-STABILITY | **UNPROVEN** | n=1 each; no full battery |
| INT1-HARNESS-SCENARIO-FILTER | **REMEDIATED (EXTEND)** | `DELIA_EVAL_SCENARIO_IDS` on existing OpenRouter runner |
| INT1-CREDENTIAL-ISOLATION | **RESIDUAL** | Unchanged; prod untouched this run |
| INT1-STAGE | **BLOCKED** | Doc 303 coordination review |
| INT1-CLOSED | **NO** | — |
| INT1-INT2-INT3-IMPL | **NOT_AUTHORIZED** | — |

**NEXT=`COORDINATION_INT1_G1_P1_REAL_EVAL_REVIEW`**. `PRODUCTION_DEPLOY=NOT_AUTHORIZED`.

## 2026-11-11 — INT-1 TEO contract + DAVI BOM completeness residuals

**TASK:** `DELIA-C3-T2-INT1-TEO-SEMANTIC-CONTRACT-AND-DAVI-BOM-COMPLETENESS-REMEDIATION-01` · Doc **304**

| ID | Classification | Notes |
|---|---|---|
| INT1-TEO-DECOMPOSITION-DESC-AMBIGUITY | **REMEDIATED** | MCP `read` publishes Process WBS / processo_id / not materials BOM |
| INT1-TEO-LIVE-RESELECTION | **TEST_NOT_RUN** | External LLM not authorized this task |
| INT1-DAVI-FULLMODE-NULL-PAGINATION | **REMEDIATED** | UC omits null page keys; classifier treats null as absent |
| INT1-DAVI-FALSE-INCOMPLETE | **REMEDIATED (deterministic)** | flat BOM total==items → is_complete true |
| INT1-DAVI-SKU-MULTILEVEL-LIVE-SQL | **TO_INVENTORY** | 90260921 observed depth=1; no live SG1 probe here |
| INT1-G1-P1-LIVE-AFTER-FIX | **NOT_AUTHORIZED** | needs PO minimal live |
| INT1-STAGE | **BLOCKED** | Doc 304 coordination review |
| INT1-CLOSED | **NO** | — |
| INT1-INT2-INT3-IMPL | **NOT_AUTHORIZED** | — |

**NEXT=`COORDINATION_INT1_TEO_DAVI_INDEPENDENT_REVIEW`**. `PRODUCTION_DEPLOY=NOT_AUTHORIZED`.

## 2026-11-11 — INT-1 TEO/DAVI integrated validation + prod deploy residuals

**TASK:** `DELIA-C3-T2-INT1-TEO-DAVI-INTEGRATED-VALIDATION-AND-PRODUCTION-DEPLOY-01` · Doc **305** · SHA `e2b341d877…`

| ID | Classification | Notes |
|---|---|---|
| INT1-DAVI-FALSE-INCOMPLETE | **CLOSED_IN_PROD** | Runtime probe 90260921 is_complete=true; no null page keys |
| INT1-TEO-DECOMPOSITION-DESC-AMBIGUITY | **CLOSED_IN_PROD** | tools/list WBS prose active on transformometro-api |
| INT1-G1-P1-LIVE-AFTER-FIX | **EXECUTED** | eval `or-qwen14b-3863d58c5327`; declared complete; incomplete=false |
| INT1-G1-TEO-FIRST-ATTRACTOR | **OPEN / RESIDUAL** | G1 still TEO-first (process search → decomposition_tree) then DAVI recovery |
| INT1-COVERAGE-UNKNOWN-FINALIZE | **OPEN** | plan-absent coverage_unknown (INT-3) |
| INT1-PROD-DEPLOY-THREE-SERVICES | **EXECUTED** | api-delpi → TEO → delia-api; health OK; rollback not required |
| INT1-STAGE | **BLOCKED** | Doc 305 independent review |
| INT1-CLOSED | **NO** | — |
| INT1-INT2-INT3-IMPL | **NOT_AUTHORIZED** | — |

**NEXT=`COORDINATION_INT1_PRODUCTION_VALIDATION_INDEPENDENT_REVIEW`**.

## 2026-11-12 — INT-1 G1 first-tool semantic selection residuals

**TASK:** `DELIA-C3-T2-INT1-G1-FIRST-TOOL-SEMANTIC-SELECTION-ROOT-CAUSE-INVESTIGATION-01` · Doc **306**

| ID | Classification | Notes |
|---|---|---|
| INT1-G1-TEO-FIRST-ATTRACTOR | **PROVEN_IN_SAMPLE (model selection)** | Post-WBS surface intact; G1 still TEO-first then recovery |
| INT1-H1-INFO-LOSS-POST304 | **REJECTED** | WBS+BOM-neg present in capture; EnvelopeHint preserves |
| INT1-H4-DETERMINISTIC-ROUTING | **REJECTED** | No forced first-tool router |
| INT1-GOAL-DECLARE-UNUSED | **PROVEN_IN_SAMPLE** | 0/4 G1/P1 calls; optional by v2; does not gate MCP |
| INT1-TRACE-DESC-TRUNCATION | **REMEDIATED (observability)** | catalog snapshot + sanitize description limit EXTEND |
| INT1-PROVIDER-REQUEST-WIRE | **TO_INVENTORY** | raw OpenRouter tools[] not captured |
| INT1-STAGE | **BLOCKED** | Doc 306 coordination review |
| INT1-CLOSED | **NO** | — |
| INT1-INT2-INT3-IMPL | **NOT_AUTHORIZED** | — |

**NEXT=`COORDINATION_INT1_G1_SELECTION_CAUSAL_REVIEW`**. `PRODUCTION_DEPLOY=NOT_AUTHORIZED`.

## 2026-11-12 — INT-1 provider-request + real semantic selection residuals

**TASK:** `DELIA-C3-T2-INT1-PYDANTIC-AI-PROVIDER-WIRE-AND-REAL-SEMANTIC-SELECTION-REMEDIATION-01` · Doc **307**

| ID | Classification | Notes |
|---|---|---|
| INT1-PROVIDER-REQUEST-WIRE | **PROVEN (B3 pre-HTTP)** | `WrapperModel.request` MRP; HTTP bytes NOT_OBSERVED |
| INT1-ENVELOPEHINT-DROPPED-ON-FOR-RUN | **REMEDIATED** | subclass `WrapperToolset` |
| INT1-ENVELOPEHINT-ANYOF-OBJECT-MISS | **REMEDIATED** | `_schema_declares_object` |
| INT1-H1-OWNER-CONTRACT-LOSS | **REJECTED** | TEO WBS + DAVI gps at live B3 |
| INT1-G1-TEO-FIRST-ATTRACTOR | **PROVEN_IN_SAMPLE (live×2)** | rounds 303e + 1182; recovery to DAVI OK |
| INT1-P1-DAVI-CONTROL | **PASS** | both rounds |
| INT1-M1-WORDING-SENSITIVITY | **UNSTABLE_IN_SAMPLE** | DAVI-first then TEO-first across rounds |
| INT1-M1-RECOVERY-FAILURE | **PROVEN_IN_SAMPLE** | both rounds NOT_SATISFIED |
| INT1-GOAL-DECLARE-UNUSED | **PROVEN_IN_SAMPLE** | 0/6 |
| INT1-STAGE | **BLOCKED** | Doc 307 independent review |
| INT1-CLOSED | **NO** | — |
| INT1-INT2-INT3-IMPL | **NOT_AUTHORIZED** | — |

**NEXT=`COORDINATION_INT1_REAL_SEMANTIC_SELECTION_INDEPENDENT_REVIEW`**. `PRODUCTION_DEPLOY=NOT_AUTHORIZED`.

## 2026-11-12 — INT-1 semantic selection + continuity remediation residuals

**TASK:** `DELIA-C3-T2-INT1-PROVIDER-NEUTRAL-SEMANTIC-SELECTION-AND-INVESTIGATION-CONTINUITY-REMEDIATION-01` · Doc **308** · Eval `or-qwen14b-99c72442b8d9`

| ID | Classification | Notes |
|---|---|---|
| INT1-INSTRUCTION-OBJECT-CONTINUITY | **REMEDIATED (default v2-1)** | fp `4ebd5260b6cf9ba9`; v2 preserved |
| INT1-GUIDANCE-NON-CITABLE | **REMEDIATED** | `GUIDANCE_NOT_DOMAIN_TRUTH` |
| INT1-NO-PROGRESS-CONTINUITY-NOTE | **REMEDIATED** | coverage_note + optional one-shot ModelRetry |
| INT1-G1-TEO-FIRST-ATTRACTOR | **OPEN** | still observed live |
| INT1-P1-DAVI-CONTROL | **PASS (selection)** | DAVI-first; satisfaction blocked by AUTHZ |
| INT1-M1-CONTINUITY | **PARTIAL** | notes present; tour/args residual; NOT_SATISFIED |
| INT1-EVAL-SUBJECT-AUTHZ | **OPEN** | DAVI `AUTHORIZATION_DENIED`; TEO missing `transformometro.access` |
| INT1-EVAL-LLM-KEY-PLACEHOLDER | **REMEDIATED_IN_HARNESS** | OpenRouter key from same `.env` when LLM key is local placeholder |
| INT1-GENERALIZATION | **NOT_PROVEN** | G1/P1/M1 only; no scenario hardcode in instructions |
| INT1-STAGE | **BLOCKED** | Doc 308 coordination review |
| INT1-CLOSED | **NO** | — |
| INT1-INT2-INT3-IMPL | **NOT_AUTHORIZED** | — |

**NEXT=`COORDINATION_INT1_SEMANTIC_CONTINUITY_INDEPENDENT_REVIEW`**. `PRODUCTION_DEPLOY=NOT_AUTHORIZED`.

## 2026-11-12 — INT-1 eval env restoration + authorized revalidation residuals

**TASK:** `DELIA-C3-T2-INT1-EVAL-ENV-AUTHZ-RESTORATION-AND-REAL-QWEN-REVALIDATION-01` · Doc **309** · Eval `or-qwen14b-be922c439302`

| ID | Classification | Notes |
|---|---|---|
| INT1-EVAL-SUBJECT-AUTHZ | **REMEDIATED_LOCAL** | `ti_delpi` Core owner grants + RBAC cache clear; DAVI preflight PASS |
| INT1-ENV-LOCAL-OVERRIDE | **CLOSED** | exclusive `infra/.env` (`c5bd6bc708` + targeted test) |
| INT1-G1-TEO-FIRST-ATTRACTOR | **OPEN** | still TEO-first; recovery SATISFIED |
| INT1-P1-DAVI-CONTROL | **PASS** | DAVI-first + SATISFIED |
| INT1-M1-CONTINUITY | **PASS_IN_SAMPLE** | DAVI-first + SATISFIED under restored AUTHZ |
| INT1-OPENROUTER-KEY-HOST-DRIFT | **OPEN** | harness uses `KIMI_API_KEY` when `DELIA_LLM_API_KEY` is local |
| INT1-DEV-PORTAL-PERM-SEED | **OPEN** | grants locais não versionados; seed documental recomendado |
| INT1-STAGE | **BLOCKED** | Doc 309 independent review |
| INT1-CLOSED | **NO** | — |
| INT1-INT2-INT3-IMPL | **NOT_AUTHORIZED** | — |

**NEXT=`COORDINATION_INT1_AUTHORIZED_REAL_EVAL_INDEPENDENT_REVIEW`**. `PRODUCTION_DEPLOY=NOT_AUTHORIZED`.

## 2026-11-12 — INT-1 semantic root cause + governed authz denial residuals

**TASK:** `DELIA-C3-T2-INT1-SEMANTIC-ROOT-CAUSE-AND-AUTHORIZATION-DENIAL-COMMUNICATION-01` · Doc **310** · Evals `or-qwen14b-985d439b1653` + `or-qwen14b-525ed88ac205`

| ID | Classification | Notes |
|---|---|---|
| INT1-G1-TEO-FIRST-ATTRACTOR | **MITIGATED_IN_SAMPLE** | v2-2 + owner contract clarity; G1/P1/M1 all DAVI-first, GROUNDED/SATISFIED |
| INT1-P1-DAVI-CONTROL | **PASS** | DAVI-first + SATISFIED (re-validated) |
| INT1-M1-CONTINUITY | **PASS_IN_SAMPLE** | DAVI-first + SATISFIED (re-validated) |
| INT1-AUTHZ-DENIAL-PROPAGATION | **PASS** | real e2e: owner `AUTHORIZATION_DENIED` → projection → no retry → governed message |
| INT1-AUTHZ-RETRY-BYPASS | **CLOSED** | `ModelRetry` blocked for authorization denial; single invocation observed |
| INT1-PEDIDOS-TAREFAS-AMBIGUITY | **OPEN** | "pedidos em aberto" still attracts TÉO task entities; formulation-level residual |
| INT1-DAVI-NONEXECUTABLE-CAPS | **OPEN** | `NEEDS_*_PROJECTION` capabilities absent from eligible catalog; fine-grained domain deny unreachable via DAVI for `api-delpi.access` holders |
| INT1-E2E-DELIA-IDENTITY | **PROVISIONED_LOCAL** | Keycloak user bound to pre-existent restricted Core user; no grants changed; DEV-only |
| INT1-RUNTIME-PROFILE-TESTS | **OPEN_PREEXISTING** | 3 config-profile failures at HEAD unrelated to this scope |
| INT1-GENERALIZATION | **NOT_PROVEN** | G1/P1/M1 known scenarios only; no scenario hardcode added |
| INT1-STAGE | **BLOCKED** | Doc 310 independent coordination review |
| INT1-CLOSED | **NO** | — |
| INT1-INT2-INT3-IMPL | **NOT_AUTHORIZED** | — |

**NEXT=`COORDINATION_INT1_SEMANTIC_AND_AUTHZ_INDEPENDENT_REVIEW`**. `PRODUCTION_DEPLOY=NOT_AUTHORIZED`.

## 2026-11-12 — INT-1 independent generalization + partial authz residuals

**TASK:** `DELIA-C3-T2-INT1-SEMANTIC-GENERALIZATION-AND-PARTIAL-AUTHORIZATION-REAL-EVALUATION-01` · Doc **311** · Evals `or-qwen14b-99d36aa86540` + `or-qwen14b-195dc9cf3bb6`

| ID | Classification | Notes |
|---|---|---|
| INT1-GENERALIZATION-SELECTION | **MITIGATED_IN_SAMPLE** | IG1–IG4 first-tool suitability 4/4; independent corpus; no keyword router |
| INT1-GENERALIZATION-OBJECTIVE | **PARTIAL_IN_SAMPLE** | IG1/IG3/IG4 grounded; IG2 NOT_SATISFIED (process code↔UUID / continuity) |
| INT1-PROCESS-CODE-VS-UUID | **OPEN** | IG2 TEO object match then id/args recovery incomplete |
| INT1-PARTIAL-AUTHZ-DETERMINISTIC | **PASS** | A–E finalize preserve + denial/not_found/unavailable distinctions |
| INT1-PARTIAL-AUTHZ-E2E-COMPOSED | **INCONCLUSIVE** | e2e-delia: schema_reject loop before TEO SUCCESS / DAVI DENY |
| INT1-AUTHZ-DENIAL-PROPAGATION | **PASS (deterministic + Doc310 real deny)** | composed PARTIAL e2e not proven this sample |
| INT1-DAVI-NONEXECUTABLE-CAPS | **OPEN** | inherited Doc 310 |
| INT1-GENERALIZATION | **PROVEN_IN_SAMPLE** | first-tool/object; n=4; no statistical claim |
| INT1-STAGE | **PENDING_COORDINATION_REVIEW** | Doc 311 |
| INT1-CLOSED | **NO** | — |
| INT1-INT2-INT3-IMPL | **NOT_AUTHORIZED** | — |

**NEXT=`COORDINATION_INT1_GENERALIZATION_AND_PARTIAL_AUTHZ_INDEPENDENT_REVIEW`**. `PRODUCTION_DEPLOY=NOT_AUTHORIZED`.

## 2026-11-12 — INT-1 identifier resolution + partial authz residuals

**TASK:** `DELIA-C3-T2-INT1-IDENTIFIER-RESOLUTION-AND-PARTIAL-AUTHZ-SCHEMA-REMEDIATION-01` · Doc **312** · Evals `or-qwen14b-64d9e5b4d58b` + `or-qwen14b-a06d048c2597` + `or-qwen14b-84c04f1194d2`

| ID | Classification | Notes |
|---|---|---|
| INT1-PROCESS-CODE-VS-UUID | **CLOSED_IN_SAMPLE** | TÉO resolves UUID/business code via canonical `ProcessoRepository.get`; decomposition/diagram/BPMN echo `codigo_processo`; R1/R2 real evals |
| INT1-PARTIAL-AUTHZ-E2E-COMPOSED | **PROVEN_IN_SAMPLE** | e2e-delia: TÉO SUCCESS + DAVI AUTHZ_DENIED → partial answer; `authorization_denied_partial`; no bypass/leak |
| INT1-PARTIAL-AUTHZ-DETERMINISTIC | **PASS** | A–E preserved from Doc 311 |
| INT1-ARGS-SCHEMA-FEEDBACK | **MITIGATED** | `explain_arguments` + get_context hint + no self-injection; model budget on opaque nested schemas remains a capability residual |
| INT1-PROJECTION-BUDGET | **OPEN** | large TÉO trees exceed `max_projection_chars` (20k) → honest `result_truncated`; owner pagination/continuation residual |
| INT1-DAVI-NONEXECUTABLE-CAPS | **OPEN** | inherited Doc 310 |
| DELIA-PREEXISTING-TEST-DEBT | **OPEN** | `test_runtime_profiles_share_execution_policy` + `test_module_exposes_native_first_tools` fail on clean baseline — unrelated to this task |
| INT1-GENERALIZATION | **PROVEN_IN_SAMPLE** | code/title/multi-identifier; n=4; no statistical claim |
| INT1-STAGE | **PENDING_COORDINATION_REVIEW** | Doc 312 |
| INT1-CLOSED | **NO** | — |
| INT1-INT2-INT3-IMPL | **NOT_AUTHORIZED** | — |

**NEXT=`COORDINATION_INT1_IDENTIFIER_RESOLUTION_AND_PARTIAL_AUTHZ_INDEPENDENT_REVIEW`**. `PRODUCTION_DEPLOY=NOT_AUTHORIZED`.

## 2026-11-12 — INT-1 independent coordination requirements and causal-review freeze (Doc 313)

**TASK:** `DELIA-C3-T2-INT1-COORDINATION-REQUIREMENTS-AND-CAUSAL-CLOSURE-REVIEW-01` · **DOC_ONLY** · evidence reviewed at `a832b5318dfa388903a998ff8609d3dbf7931db1` · no functional changes or new eval.

| Residual / gate | State | Required evidence or disposition |
|---|---|---|
| INT1-PO-P1-P2-P3-CONSOLIDATED-ACCEPTANCE | **PENDING** | Reconcile original PO failure vs later SHA/config/live user-facing outcomes; no automatic PASS from isolated probes |
| INT1-PROJECTION-BUDGET | **OPEN** | Large TÉO trees truncate; investigate owner pagination/continuation before increasing context budget |
| INT1-IDENTIFIER-COVERAGE-PROVENANCE | **TO_VERIFY** | Exact scalar match across arbitrary owner structured fields may be incidental; test authoritative object/root/obligation match and global walk budget |
| INT1-PARTIAL-USER-GROUNDING | **TO_VERIFY** | Owner TÉO SUCCESS + DAVI DENY proven; confirm user-facing permitted evidence has provenance and truthful partial status on final path |
| INT1-RENAMED-SCHEMA-GENERALIZATION | **TO_VERIFY** | Locate specific real proof for original acceptance requirement; do not infer from 4 independent known sample runs |
| DELIA-PREEXISTING-TEST-DEBT | **OPEN** | Two baseline assertions reported failing; owner and impact on mandatory regression gate to be reconciled |
| INT1-STAGE | **PENDING_COORDINATION_REVIEW** | No auto advancement; final independent evidence matrix required |
| INT1-CLOSED | **NO** | — |

**CAUSAL REVIEW RULE:** model-selection hypothesis is never the default explanation. Check B1/B2/B3 contract delivery, local argument mutation/schema, owner/AuthZ, evidence coverage and user outcome before attributing to the LLM. First-divergence evidence is mandatory. **NEXT=`COORDINATION_INT1_REQUIREMENTS_EVIDENCE_MATRIX_AND_FINITE_ACCEPTANCE_DECISION`**. No new task loop without bounded evidence-based blocker.

## 2026-11-12 — INT-1 finite acceptance review residuals (Doc 314)

**TASK:** `DELIA-C3-T2-INT1-REQUIREMENTS-EVIDENCE-MATRIX-AND-FINITE-ACCEPTANCE-DECISION-01` · Doc **314** · Evals `or-qwen14b-123ff3f94c37`/`3eac383d5237`/`b51e9ecf9f5d`/`5ad8d570cfdc`/`7c97bac72237`

| ID | Classification | Notes |
|---|---|---|
| INT1-OWNER-TYPED-REJECTION-FEEDBACK | **CLOSED** | `error_kind="validation"`+`recoverable:true` (VISTA `INVALID_CHANGE`/`QUERY_REQUIRED`, etc.) now `OWNER_ARGUMENT_REJECTED`+hint→ModelRetry; was `mcp_protocol_error`→`SOURCE_UNAVAILABLE`; proven live `error=owner_argument_rejected` |
| INT1-OWNER-FORBIDDEN-CLASSIFICATION | **CLOSED** | Doc 315: owner envelope `code:"FORBIDDEN"` (`error_kind:"forbidden"`, httpStatus 403 — VISTA tool_bridge) mapped to `mcp_protocol_error`→`SOURCE_UNAVAILABLE`; now `MCP_AUTHORIZATION_DENIED` via `_OWNER_ERROR_CODE_MAP`; proven live `or-qwen14b-7c2d2bd54410` |
| INT1-PO-P1 | **SATISFIED_PROVEN** | Doc 310 DAVI-first GROUNDED |
| INT1-PO-P2 | **SATISFIED_PROVEN_IN_SAMPLE** | Doc 316: v2-3 enumeration-intent rule; live `or-qwen14b-2ff9e302c874` — unfiltered `process.search` → `total:109` GROUNDED with honest pagination; explicit-filter control run preserved filter |
| INT1-PO-P3 | **SATISFIED_PROVEN_IN_SAMPLE** | Doc 316: `display_format.list` under TV_READ implemented in VISTA; live `or-qwen14b-393ea7510418` — semantic selection → authoritative catalog GROUNDED; TV_WRITE paths preserved |
| INT1-PROJECTION-BUDGET | **OPEN** | large TÉO trees truncate honestly (Doc 312) |
| INT1-ATTEMPT-STATUS-CONFLATION | **OPEN_MINOR** | `attempt.status=SOURCE_UNAVAILABLE` also for `owner_argument_rejected`; `error_code`+`owner_hint` carry correct semantics — observability debt only |
| INT1-MCP-HEAVY-VIEW-TIMEOUT | **OPEN_MINOR** | one real `mcp_timeout` (15s) on heavy `teo.analyze` — reliability, not INT-1 |
| INT1-DAVI-NONEXECUTABLE-CAPS | **OPEN** | inherited Doc 310; owner DAVI |
| DELIA-PREEXISTING-TEST-DEBT | **OPEN** | `test_runtime_profiles_share_execution_policy` + `test_module_exposes_native_first_tools` baseline failures — unrelated to this task |
| INT1-GATE-R-FULL-REGRESSION | **TEST_NOT_RUN** | full battery not authorized in this task; pending gate if canonical DoD requires — owner + condition registered in Doc 314 §6 |
| INT1-GENERALIZATION | **PROVEN_IN_SAMPLE** | no statistical/universal claim |
| INT1-STAGE | **PENDING_COORDINATION_REVIEW** | recommendation `ACCEPT_WITH_RESIDUAL` submitted — NOT self-approved |
| INT1-CLOSED | **NO** | — |
| INT1-INT2-INT3-IMPL | **NOT_AUTHORIZED** | — |

**TASK:** `DELIA-C3-T2-INT1-P2-PROCESS-ENUMERATION-AND-P3-VISTA-FORMATS-CONTRACT-REMEDIATION-01` · Doc **315** · Evals `or-qwen14b-4be3b315381e`(invalid-env)/`or-qwen14b-7c2d2bd54410`

| ID | Classification | Notes |
|---|---|---|
| INT1-P2-MODEL-ENUMERATION-STRATEGY | **CLOSED** | Doc 316: v2-3 instruction (`95e265ee18cd5d66`) — eval `or-qwen14b-2ff9e302c874` model ran unfiltered `search` → total=109 GROUNDED; explicit-filter control preserved (`q:"quality"`→`q:"qualidade"`) |
| EXT-VISTA-READ-FORMAT-CATALOG | **CLOSED** | Doc 316: `display_format.list` shipped in VISTA `READ_ENTITY_ACTIONS` under TV_READ — bounded projection of canonical displayModes/blockTypeByMode/dataBlockTypes/block_type_vocabulary/format_catalog_entries; admin catalog stays TV_WRITE; proven live `or-qwen14b-393ea7510418` |
| INT1-EVAL-TEO-ROOTPATH | **CLOSED_OPERATIONAL** | isolated eval TÉO containers require canonical `--root-path /apps/transformometro-api` (missing → MCP POST 404); env defect of eval setup, not repo code |

**NEXT=`COORDINATION_INT1_P2_P3_INDEPENDENT_ACCEPTANCE_REVIEW`**. `PRODUCTION_DEPLOY=NOT_AUTHORIZED`.

### INT-1 P2/P3 governed implementation — 2026-11-13

**TASK:** `DELIA-C3-T2-INT1-P2-SEMANTIC-ENUMERATION-AND-P3-VISTA-READ-FORMAT-CATALOG-IMPLEMENTATION-01` · Doc **316** · Evals `or-qwen14b-2ff9e302c874` / `or-qwen14b-1ab21b3ca278` / `or-qwen14b-393ea7510418`

| Residual | Status | Evidence |
|---|---|---|
| INT1-VISTA-READ-WIRE-DISCOVERY | **CLOSED** | `vista.read` wire description (server.py `add_tool`) did not advertise new/existing READ entities — docstring is not the wire source; updated (sha `071279a8…`), P3 selection proven |
| INT1-EVAL-ENV-FLAKES | **OPEN_OPERATIONAL** | `model_unavailable` (provider) + `turn_budget_limited` (0 tool calls) occurred once each; environmental, not model evidence |

**NEXT=`COORDINATION_INT1_P2_P3_REAL_OUTCOME_INDEPENDENT_REVIEW`**. `PRODUCTION_DEPLOY=NOT_AUTHORIZED`.

### INT-1 finite full regression + consolidated acceptance gate — 2026-11-13

**TASK:** `DELIA-C3-T2-INT1-FINITE-FULL-REGRESSION-AND-CONSOLIDATED-ACCEPTANCE-GATE-01` · Doc **317** · Consolidated eval `or-qwen14b-e069f3b33be8` (candidate `ce9602744037`)

| Residual | Status | Evidence |
|---|---|---|
| INT1-DOC-INSTRUCTION-NAME-DRIFT | **CLOSED** | Docs said `v2-3-object-authz-continuity`; registry has single v2-3 `generalist-semantic-v2-3-enumeration-intent` (fp `95e265ee18cd5d66`) — documentation-only divergence, corrected (runtime unchanged) |
| INT1-DOC-VISTA-FIELD-DRIFT | **CLOSED** | Docs said `valueFormats`; real contract returns `displayFormats` — corrected in 316/16/ledger |
| DELIA-PREEXISTING-TEST-DEBT | **PARTIALLY_CLOSED** | `test_module_exposes_native_first_tools` FIXED (OPTIONAL marker in docstring → GREEN); `test_runtime_profiles_share_execution_policy` remains — context-proportional profile budgets (ollama 16k→6000/4 vs qwen 40k→20000/32) is a deliberate policy divergence requiring canonical decision (BLOCKED_BY_POLICY_DECISION, owner: DÉLIA runtime config) |
| INT1-EVAL-ENV-CATALOG-ARTIFACT | **OPEN_OPERATIONAL** | isolated VISTA eval container writes `tv-dashboard-api/data/tv-dashboard/catalog/tv_data_routes.json` into mounted working tree → catalog-sync suite failures; environment artifact, not code regression |

**Gates proposed:** L=PASS · A=PASS · O=PASS · R=FAIL (one classified preexisting policy blocker). **NEW_REGRESSIONS=0** across DELIA/TÉO/VISTA/DAVI suites. Consolidated P1/P2/P3 = SATISFIED_PROVEN on frozen candidate.

**NEXT=`COORDINATION_INT1_LAOR_AND_FINAL_ACCEPTANCE_INDEPENDENT_REVIEW`**. `PRODUCTION_DEPLOY=NOT_AUTHORIZED`.

### INT-1 Gate R residual remediation + publication — 2026-11-13

**TASK:** `DELIA-C3-T2-INT1-GATE-R-REMEDIATION-FINAL-COMMIT-AND-PUSH-01` · Doc **319** · Candidate commit published on `main`

| Residual | Status | Evidence |
|---|---|---|
| INT1-PROJECTION-BUDGET | **CLOSED** | Doc 300 divergence ratified — test reconciled to governance-parity invariants + technical-capacity tolerance (`prior_turns_limit`, `max_projection_chars`) + negative guard; DELIA suite 1601/0 |
| DELIA-PREEXISTING-TEST-DEBT | **CLOSED** | `runtime_profiles_share_execution_policy` GREEN post-reconciliation; `module_exposes_native_first_tools` já verde; `test_llm_tuning_comes_from_runtime_json` env-determinismo corrigido (`delenv DELIA_RUNTIME_PROFILE`) |
| R-T1-TEO-OAUTH | **CLOSED** | same root cause as R-T2 — async tests without declared `pytest-asyncio` (added to requirements); not an auth defect |
| R-T2-TEO-ASYNC-ENV | **CLOSED** | `pytest-asyncio` declared in `transformometro-api/requirements.txt` |
| R-T3-TEO-DOMAIN | **CLOSED** | 2 real owner defects fixed (sector-leak on empty `setores`; authz-before-existence order); rest = stale mocks/dates/contract reconciliation/synthetic fixture |
| R-V1-VISTA-BASELINE | **CLOSED** | 18→6 tool consolidation (`06103630cf`) — stale tests reconciled to proposal_handle/DEPENDENCY_UNSATISFIABLE contract; env-driven PUBLIC_BASE_URL |
| R-V2-VISTA-OPENAPI | **CLOSED** | baseline synced canonically 583→597 GETs; catalog regenerated; container drift = missing `openapi_param_locale.json` |
| R-V3-VISTA-ARTIFACT | **CLOSED** | runtime catalog at `TV_DATA_ROUTES_PATH` resynced (equivalent of startup `sync_safe()`) |
| VISTA-ACTIONS-BUDGET | **CLOSED** | envelope 105,294→102,182B dispatch / 96,715B standalone (headroom 5,685≥4,096); only redundant/transport fields dropped; `modes`/directives preserved per Actions pins |
| VISTA-B5-PATCH-TARGET | **CLOSED** | `ACCESS_SVC` now patches `playlist_share_service.PlaylistAccessService` (actual lookup binding) |
| R-A1-DAVI-FIXTURES | **CLOSED** | git in eval image; manifests re-pinned via canonical spec; ROUTE_CONTRACTS gaps; pagination tier factories; avatar env-driven |
| INT1-ATTEMPT-STATUS-CONFLATION | OPEN_MINOR | observability debt only |
| INT1-MCP-HEAVY-VIEW-TIMEOUT | OPEN_MINOR | reliability residual, not INT-1 |
| INT1-DAVI-NONEXECUTABLE-CAPS | OPEN | inherited Doc 310; owner DAVI |
| INT1-EVAL-ENV-FLAKES | OPEN_OPERATIONAL | occasional `model_unavailable`/`turn_budget_limited` |
| INT1-GATE-R-FULL-REGRESSION | **EXECUTED** | all four suites exit 0 (DELIA 1601 · TÉO 2127+62sk · VISTA 2535 · DAVI 5970+10sk) |
| INT1-STAGE | PENDING_COORDINATION_REVIEW | R=PASS_PROPOSED; NOT self-approved |

**NEXT=`COORDINATION_INT1_GATE_R_PUBLISHED_CODE_INDEPENDENT_REVIEW`**. `PRODUCTION_DEPLOY=NOT_AUTHORIZED`.

### INT-1 TÉO scope fail-closed remediation — 2026-11-13

**TASK:** `DELIA-C3-T2-INT1-TEO-SHARED-RESOURCE-SCOPE-FAIL-CLOSED-REMEDIATION-01` · Doc **320**

| Residual | Status | Evidence |
|---|---|---|
| R-T3-SCOPE-FAIL-CLOSED | **CLOSED** | H1 (`_share_setor` `""==""`), H2 (âncora ausente → pool completo) e `_same_filial` análogo — 3 CONFIRMED_DEFECT corrigidos no owner; 13 testes S1–S12; TÉO 2140/0 fail |
| INT1-STAGE | PENDING_COORDINATION_REVIEW | R=PASS_PROPOSED no novo SHA; NOT self-approved |

**NEXT=`COORDINATION_INT1_TEO_SCOPE_AND_GATE_R_INDEPENDENT_ACCEPTANCE_REVIEW`**. `PRODUCTION_DEPLOY=NOT_AUTHORIZED`.

### INT-1 formal acceptance + deploy authorization — 2026-11-13

**TASK:** `DELIA-C3-T2-INT1-FORMAL-ACCEPTANCE-PRODUCTION-DEPLOY-AND-OUTCOME-VERIFICATION-01` · Doc **321**

| Residual | Status | Evidence |
|---|---|---|
| INT1-STAGE | **ENGINEERING_ACCEPT** | L/A/O/R=PASS formalizado sob autorização PO; produção autorizada escopo INT-1 |
| INT1-ATTEMPT-STATUS-CONFLATION | OPEN_MINOR | não-material (observability) |
| INT1-MCP-HEAVY-VIEW-TIMEOUT | OPEN_MINOR | não-material (reliability) |
| INT1-DAVI-NONEXECUTABLE-CAPS | OPEN | herdado Doc 310 — owner DAVI |
| INT1-EVAL-ENV-FLAKES | OPEN_OPERATIONAL | ambiente de eval, não produção |

**NEXT=`COORDINATION_INT1_PRODUCTION_OUTCOME_INDEPENDENT_ACCEPTANCE_REVIEW`** (após evidências PARTE B/C).

### INT-1 deploy executado + validação produtiva — 2026-11-13 (Doc 321 PARTES B/C)

| Residual | Status | Evidence |
|---|---|---|
| INT1-PRODUCTION-DEPLOY | **EXECUTED** | 4 serviços seqüenciais, healthy/running; imagens anteriores registradas (rollback pronto, não requerido) |
| INT1-PRODUCTION-VALIDATION | **PASS_REPORTED** | eval `or-qwen14b-49cc26d53beb`: P1/P2/P3 GROUNDED em owners produtivos; aceite independente pendente |
| INT1-EVAL-HARNESS-PROD-DEFAULTS | **CLOSED** | host header + issuer parametrizáveis (`c774b45655`, `50d107b3ba`) — defaults dev preservados |
| INT1-PROD-RUNTIME-PROFILE | OPEN_EXTERNAL | prod `DELIA_RUNTIME_PROFILE=openrouter_kimi` ≠ perfil homologado `openrouter_qwen` — decisão ops/PO, fora do escopo |
| INT1-SEC01-API-DELPI | OPEN_EXTERNAL | `ef2ea358f2` pós-build, task SEC-01 — não deployado (sem autorização INT-1) |
| INT1-ATTEMPT-STATUS-CONFLATION | OPEN_MINOR | não-material |
| INT1-MCP-HEAVY-VIEW-TIMEOUT | OPEN_MINOR | não-material |
| INT1-DAVI-NONEXECUTABLE-CAPS | OPEN | herdado Doc 310 — owner DAVI |
| INT1-EVAL-ENV-FLAKES | OPEN_OPERATIONAL | ambiente de eval |

`PRODUCTION_VALIDATION=PASS` reportada com evidência; `INT1_CLOSED=NO` — NEXT=`COORDINATION_INT1_PRODUCTION_OUTCOME_INDEPENDENT_ACCEPTANCE_REVIEW`.

### INT-1 model-agnostic reconciliation — 2026-11-13 (Doc 322)

| Residual | Status | Evidence |
|---|---|---|
| INT1-ATTEMPT-STATUS-CONFLATION | OPEN_MINOR — **NOT MATERIAL** | P2 real: `declared_status_overridden`+`coverage_unknown`+`declared_limitation` apresentados; completude não promovida indevidamente (CASO B) |
| INT1-MCP-HEAVY-VIEW-TIMEOUT | OPEN_MINOR — NOT MATERIAL | não-bloqueante |
| INT1-DAVI-NONEXECUTABLE-CAPS | OPEN — NOT MATERIAL | owner DAVI, fora da superfície read |
| INT1-EVAL-ENV-FLAKES | OPEN_OPERATIONAL — NOT MATERIAL | ambiente de eval |
| INT1-PROD-RUNTIME-PROFILE | OPEN_EXTERNAL — NOT MATERIAL | model-agnostic por decisão PO; contratos verificados preservados |
| INT1-SEC01-API-DELPI | OPEN_EXTERNAL | task independente |
| INT1-FINAL-DECISION | **SUBMITTED** | pacote Docs 317–322 + traces prod/dev → `COORDINATION_INT1_FINAL_INDEPENDENT_ACCEPTANCE_DECISION`; `INT1_CLOSED=NO` |

### INT-1 independent final review — 2026-11-13 (Doc 323)

| Residual | Status | Evidence / disposition |
|---|---|---|
| INT1-FINAL-DECISION | **ACCEPT / CLOSED** | Coordenação aceita INT-1 delimitada, L/A/O/R=PASS, Doc323; sem avanço de C3/T2 |
| INT1-P2-PROD-ENUMERATION | **ACCEPTED_BOUNDED_PARTIAL / NOT_FULL_ENUMERATION_PROVEN** | Prod `q:"transformação"` `total=1` GROUNDED, cobertura parcial honesta; Doc314 §8 aceita residual, não declarar enumeração integral |
| INT1-PROD-RUNTIME-PROFILE | **OPEN_EXTERNAL / NON_BLOCKING** | Kimi ativo, eval Qwen isolado; contratos model-agnostic aceitos, sem troca de modelo |
| INT1-ATTEMPT-STATUS-CONFLATION | **OPEN_MINOR / NON_BLOCKING** | Observability, Outcome override/limitations presentes |
| INT1-MCP-HEAVY-VIEW-TIMEOUT | **OPEN_MINOR / NON_BLOCKING** | Confiabilidade governada, owner/DoD posterior |
| INT1-DAVI-NONEXECUTABLE-CAPS | **OPEN / NON_BLOCKING** | Owner DAVI, fora do escopo READ INT1 aceito |
| INT1-EVAL-ENV-FLAKES | **OPEN_OPERATIONAL / NON_BLOCKING** | Eval infrastructure |
| INT1-SEC01-API-DELPI | **OPEN_EXTERNAL / SEPARATE_TASK** | Deployment de outra task não autorizado por INT1 |

**NEXT=`COORDINATION_C3_T2_POST_INT1_NEXT_BOUNDED_STEP_DECISION`**. `INT1_CLOSED=YES`; `INT2/INT3/T3=NOT_AUTHORIZED`; `NEW_PRODUCTION_DEPLOY=NOT_AUTHORIZED`.

### C3/T2 post-INT-1 — requirements inventory (Doc 324; 2026-11-13)

| Residual | Status | Evidence / disposition |
|---|---|---|
| T2-INT2-TYPED-OBJECTIVE | **OPEN — MATERIAL TO T2** | plan=None em prod real (tool nunca invocada) → coverage provável impossível; único passo bounded proposto, pendente autorização |
| T2-INT3-SUFFICIENCY | OPEN — BLOCKED BY INT-2 | machinery existe, nunca exercitada |
| T2-INT4-SYNTHESIS | OPEN — PARTIAL_PROVEN_IN_SAMPLE | avanço pleno depende INT-2/3 |
| T2-INT5-INTEGRATED-ACCEPTANCE | GATED | gate final posterior |
| INT1-* (menores/externos) | OPEN_NON_BLOCKING | inalterados — owners registrados (Doc 323) |

### INT-2 typed objective implementation — 2026-11-13 (Doc 325)

| Residual | Status | Evidence / disposition |
|---|---|---|
| T2-INT2-TYPED-OBJECTIVE | **EVIDENCE_READY_FOR_REVIEW** | cadeia declaration→plan→obligations→verdict provada em `or-qwen14b-a7c42fd4167f` (9/10 com veredito tipado); aceite é da coordenação |
| INT2-DELIVERY-LABEL-VARIANCE | OPEN_MINOR — NOT MATERIAL | C/E2: modelo escolhe `record_detail`/`enumeration` onde oráculo esperava `explanation`/`aggregation` — vocabulário bounded correto, seleção fina = variância cognitiva; objetivo/obrigações corretos |
| INT2-DISTINCT-BINDING-FIELD-OBLIGATIONS | OPEN_MINOR — conservador | obrigações campo-a-campo sobre o mesmo registro exigem tentativa distinta → UNSATISFIED honesto; declaração subject-level evita falso-negativo |
| INT2-IDENTITY-BIND-VS-KIND | OPEN_MINOR — contrato | D: evidência bound à identidade satisfaz a obrigação mesmo quando o *tipo* pedido (estrutura) está ausente no owner — pertinência de tipo é model-declared; resposta permanece honesta |
| INT2-CLARIFICATION-FIRST-NO-PLAN | OPEN_MINOR | D2: path clarificação-first não declara objetivo → `coverage_unknown` por construção honesta (sem plano) |
| INT2-MODEL-TOTAL-COMPOSITION | OPEN_MINOR — guard ativo | "109" não-verificado rejeitado 3× por `declared_answer_unverified_values` + `result_truncated` preservado |
| INT1-* (menores/externos) | OPEN_NON_BLOCKING | inalterados — owners registrados (Docs 322–323) |

### INT-2 forensic review — 2026-11-13 (Doc 326)

| Residual | Status | Evidence / disposition |
|---|---|---|
| INT2-RC1-SCALAR-IDENTIFIER-BINDING | **RESOLVED** | `_attempt_satisfies_obligation` agora reusa `_attempt_identifier_roots` (root=None, wrong-root gate) — `codigo_processo` e campos não-canônicos vinculam; +2 testes |
| INT2-RC2-TOKEN-EXACT-CODE | OPEN_MINOR — contrato | correção "digit-free→subject-scope" regrediu em 3 protection tests → revertida; token único code-shaped permanece strict (B/C honestos) |
| INT2-RC3-STRUCTURED-NUMERIC-POOL | **RESOLVED** | guard agora inclui escalares `outcome.structured` bound — "109" owner-declared verificado no eval real (A); +2 testes |
| INT2-RC4-FIELD-BINDING | OPEN_MINOR — conservador | obrigações campo-a-campo no mesmo registro → falso-neg honesto (binding 1:1); relaxar cria falsos-pos heterogêneos |
| INT2-RC5-OBLIGATION-SEMANTICS | **OPEN — ARCHITECTURE_DECISION_REQUIRED** | `OBLIGATION_SATISFIED`=`EVIDENCE_BOUND`≠`OBLIGATION_DEMONSTRATED`: D (kind), D2 (sujeito não-pertinente), F (write-claim bound a read) — honestidade preservada por limitations; correção exige entity-kind echo ou refinamento de estado → contrato congelado |
| INT2-DELIVERY-LABEL-VARIANCE | OPEN_MINOR — documentado | C/E2 bounded-vocabulary variation, outcome servido (WS-2: 8 equiv / 2 partial / 0 incorrect) |
| INT2-CLARIFICATION-FIRST-NO-PLAN | OPEN_MINOR | inalterado — path honesto por construção |
| INT1-* (menores/externos) | OPEN_NON_BLOCKING | inalterados — owners registrados (Docs 322–323) |

**NEXT=`COORDINATION_INT2_REVIEW_AND_ARCHITECTURE_DECISION_ON_OBLIGATION_SEMANTICS`**

### RC5 architecture decision — 2026-11-13 (Doc 327)

| Residual | Status | Evidence / disposition |
|---|---|---|
| INT2-RC5-OBLIGATION-SEMANTICS | **IMPLEMENTED_PENDING_REVIEW** | Doc 328 — Obligation Evidence Anchors implementados (EXTEND): `MaterialObligation` tipado; âncora verificada vs echos owner + `invocation_vocabulary` (bind-only para superfície `specialist.remote`); ausência autoritativa ancorada; ACT exige postcondition; legado subject-scope removido; zero falso SATISFIED no eval real `or-qwen14b-0d53756cb6bb` (10/10); pendente revisão independente da coordenação |
| INT2-RC5-TEO-ENVELOPE-ECHO | **RESOLVED** | Doc 328 — TÉO structured **não** ecoa `entity`/`action_id`; resolvido via `invocation_vocabulary` (seletores de vocabulário owner capturados dos args de invocação na provenance/binding) |
| demais INT2-* | inalterados | Doc 326/register |

**NEXT=`COORDINATION_RC5_INDEPENDENT_IMPLEMENTATION_REVIEW`**

### RC5 implementation residual — 2026-11-13 (Doc 328)

| Residual | Status | Evidence / disposition |
|---|---|---|
| INT2-RC5-MODEL-ENVELOPE-ANCHORS | OPEN_LOW | modelo qwen3-14b declara `evidence_source` como nome de envelope (`teo.read`) mesmo com instrução v2-5 — outcome correto (INCONCLUSIVE, jamais falso SATISFIED) mas limita demonstração; mitigação possível em futura iteração de instrução sem hardcode de vocabulário |

**NEXT=`COORDINATION_RC5_INDEPENDENT_IMPLEMENTATION_REVIEW`**

### RC5 rework — 2026-11-13 (Doc 329)

| Residual | Status | Evidence / disposition |
|---|---|---|
| INT2-RC5-R1-ENVELOPE-ANCHORS | **REMEDIATED** | Âncoras dotted rejeitadas na declaração c/ `anchor_guidance`; correção no mesmo turno comprovada em modelo real (teo.read→process→SATISFIED) |
| INT2-RC5-R2-GENERIC-OPERATION | **REMEDIATED** | `operation` sem âncora = restrição apenas; operation-only jamais demonstra |
| INT2-RC5-R3-ABSENCE-IDENTITY | **REMEDIATED** | `invocation_identity` (top-level + 1 nível); ausência exige identidade vinculada; divergente = UNSATISFIED |
| INT2-RC5-R4-WRITE-POSTCONDITION | **REMEDIATED** | ACT demonstra só via `project_write_outcome` VERIFIED; data não-vazio removido como prova |
| INT2-RC5-MODEL-ENVELOPE-ANCHORS | OPEN_LOW (refinado) | Modelo ainda propõe dotted na 1ª tentativa; guidance resolve em 1–3 iterações quando converge; quando não converge, outcome honesto — nunca falso SATISFIED |
| INT2-RC5-AGGREGATION-REAL-COVERAGE | OPEN_LOW | SATISFIED de agregação PROVEN determinístico; modelo 14B não convergiu declaração em B nas 2 runs — aguarda run futura ou modelo distinto |

**NEXT=`COORDINATION_RC5_INDEPENDENT_REVIEW_AFTER_REWORK`**

### INT-2 final validation — 2026-11-13 (Doc 330)

| Residual | Status | Evidence / disposition |
|---|---|---|
| INT2-ENUM-PARTIAL-SATISFIED | **REMEDIATED** | Janela parcial owner-declared (total>delivered, is_complete:false, truncated) → INCONCLUSIVE; gate por `goal.output_mode` |
| INT2-AGG-REAL-CONVERGENCE | **REMEDIATED** | Agregação SATISFIED real em 3 formulações (B/G/G2) após fix de docstring delivery + observed_invocation_vocabulary |
| INT2-RC5-AGGREGATION-REAL-COVERAGE | **CLOSED** | Doc 330 — agregação real comprovada (B, G, G2) |
| INT2-MODEL-BUDGET-EXHAUSTION | OPEN_LOW | E2 esgotou tool_calls antes da declaração válida; outcome honesto (coverage_unknown), não defeito de contrato |
| INT2-MODEL-FABRICATED-ANCHOR | OPEN_LOW | Modelo pode declarar token não-vivo (`processo_competencia_snapshot`) → UNSATISFIED honesto; mitigado por observed_invocation_vocabulary |

**NEXT=`COORDINATION_C3_T2_INT2_FINAL_FUNCTIONAL_ACCEPTANCE_REVIEW`**
