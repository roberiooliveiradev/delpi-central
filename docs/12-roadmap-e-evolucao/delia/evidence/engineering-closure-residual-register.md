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
| `CANONICAL_NEXT` | `T2_INDEPENDENT_REVIEW` → aprovação explícita `RETIRE_FULL_SET` (ou rejeição/KEEP) antes de qualquer remoção; T3 não autorizada |
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
| L-06 | Legacy | Snapshot experiment code (`snapshot_interop`, `catalog_store`, `mcp_catalog_sync`) | DÉLIA interop + coordenação | T2: consumidores só experiment/tests/composer branch; default código=`live`; **prod env ainda `snapshot_experiment`** (drift ops) | `KEEP_APPROVED` até ADR | T2 review → remoção só se RETIRE aprovado |
| A-01 | Architecture | Domain/Application sem import direto de Infra no snapshot | DÉLIA specialist_interop | `snapshot_interop` usa Protocol `_SnapshotCatalogStore`; ledger G5 | `CLOSED_PROVEN` | — |
| A-02 | Architecture | C3-T4 Structured Understanding preservado | DÉLIA structured_understanding | docs 21/20/25 + doc256 Conflict A; código presente; unwired root = approved KEEP | `KEEP_APPROVED` | — |
| A-03 | Architecture | C3-T5 OpenAPI foundation preservado | DÉLIA openapi/capability | ledger G5 KEEP (46 testes); `openapi_provider.py` presente; adapter direto já aposentado | `KEEP_APPROVED` | — |
| A-04 | Architecture | Segundo Agent/planner/tool-loop paralelo ao Pydantic AI | DÉLIA orchestration | Agent + MCPToolset em adapter/investigation; G8 “zero segundo runtime” | `CLOSED_PROVEN` | — |
| A-05 | Architecture | Destino do experimento snapshot (`live` vs `snapshot_experiment`) + R04 stale | Coordenação + DÉLIA interop | T2 HEAD `fd78269968`; doc216 PRODUCTION_SWITCH_NOT_APPROVED; LIVE equivalente PROVEN; RETIRE recomendado; **código não removido** | `ARCHITECTURE_DECISION_REQUIRED` | Aguardar ADR |
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
