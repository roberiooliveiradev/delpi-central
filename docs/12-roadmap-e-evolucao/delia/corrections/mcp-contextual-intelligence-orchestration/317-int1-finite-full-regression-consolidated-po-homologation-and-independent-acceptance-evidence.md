# 317 — INT-1 Finite Full Regression, Consolidated PO Homologation and Independent Acceptance Evidence

**TASK_ID:** `DELIA-C3-T2-INT1-FINITE-FULL-REGRESSION-AND-CONSOLIDATED-ACCEPTANCE-GATE-01`
**BASE_HEAD / CANDIDATE_SHA:** `ce96027440378ec788f376136192e968a68f1724` (`HEAD == origin/main == REFERENCE_HEAD`; WIP concorrente preservado)
**PHASE:** C3/T2 — INT-1 pendente de revisão de coordenação · `INT1_STAGE_ACCEPTANCE=PENDING_COORDINATION_REVIEW`
**MODEL:** `qwen/qwen3-14b` via `openrouter_qwen` · pydantic_ai `2.50.0` · config fp `e4a5b706a3b3156b`
**ESCOPO:** reconciliação instrução/contratos, Gate R completo, homologação consolidada P1/P2/P3 no candidato congelado, matriz L/A/O/R e matriz dos 14 requisitos. Não é nova rodada de desenvolvimento.

---

## 1. Reancoragem e candidato congelado

```text
HEAD:                    ce96027440378ec788f376136192e968a68f1724
origin/main:             ce96027440378ec788f376136192e968a68f1724
GIT_STATUS:              WIP concorrente preservado (.tmp-helpdesk-venv,
                         plugins/*, tv-dashboard-api/data) — não commitado
PHASE_FROM_16:           C3/T2 · INT-1 pendente de revisão de coordenação
NEXT_FROM_LEDGER:        COORDINATION_INT1_P2_P3_REAL_OUTCOME_INDEPENDENT_REVIEW
FROZEN_DECISIONS:        AGENT_COUNT=1 · PYDANTIC_AI_NATIVE=YES ·
                         MCP_TOOLSET_LIVE=YES · NEW_ROUTER/PLANNER/RESOLVER=NO ·
                         RBAC_MUTATION=NO
EVAL_ENVIRONMENT:        containers isolados delpi-{teo,vista,davi}-eval-int1
                         (root-paths canônicos, mounts de código, rede
                         infra_delpi-network); prod intocada
                         (PROD_CONTAINER_UNTOUCHED=YES)
```

---

## 2. FRENTE 1 — Reconciliação de instrução e contratos

### 2.1 Divergência nome documentado × registry

```text
REGISTRY:                config/investigation_instructions.delpi.json
DEFAULT_INSTRUCTION:     generalist-semantic-v2-3-enumeration-intent
REGISTRY_KEYS:           v2-2-object-authz-continuity (preservada)
                         + v2-3-enumeration-intent (default)
INSTRUCTION_FINGERPRINT: 95e265ee18cd5d66 = sha256(texto v2-3)[:16] — VERIFICADO
RESOLVED_INSTRUCTION:    v2-3 (sem override de versão no loader/provider)
```

**Fato:** docs 316/16/ledger registraram o nome `…-v2-3-object-authz-continuity`;
o registry contém **uma única** v2-3, nomeada `…-v2-3-enumeration-intent` —
mesmo conteúdo avaliado (fingerprint confere). Divergência **exclusivamente
documental** → corrigidos Doc 316, Doc 16 e ledger; runtime inalterado.

### 2.2 Identidade do que chega ao provider

O sha entregue ao provider (`agent_instructions_sha256` nos B3) difere do
fingerprint base porque o runtime **anexa cláusulas condicionais**:

```text
base v2-3:   7654 chars → sha 95e265ee18cd5d66…
P2/P3 wire:  7827 chars → sha 2fff53116c8304a8822409a455e46842e2db6f34949ddb6d9c9302f4e07b64aa
             = base + identifier-gate (perguntas sem literal de identificador)
P1 wire:     base + catalog_failures condicional conforme o turno
MODEL_VISIBLE_INSTRUCTION_SHA: PROVEN via B3 em todos os cenários
```

### 2.3 Contrato VISTA

Campo real retornado por `vista.read{display_format,list}` é **`displayFormats`**
(lista `{formatId,category,label,pattern,compatibleTypes}`), não `valueFormats`.
Docs corrigidos. Resposta live completa:

```json
{entity, displayModes{modes, blockTypeByMode}, dataBlockTypes,
 dataViewBlockTypes, blockTypeVocabulary, displayFormats[]}
```

```text
INSTRUCTION_REGISTRY_CONSISTENT=YES · VERSION_IDENTIFIED=YES ·
FINGERPRINT_VERIFIED=YES · PROVIDER_DELIVERY_PROVEN=YES ·
DOCUMENTATION_MATCHES_RUNTIME=YES (após correção)
```

---

## 3. FRENTE 2 — Gate R: regressão completa

Execução em containers isolados (imagem canônica + mounts de código do candidato). Classificação por baseline comparável (`git archive e670c61f1b`, zero-diff ou identidade de falhas).

| Suite | Comando/ambiente | Total | Pass | Fail | Skip | Classificação das falhas |
|---|---|---|---|---|---|---|
| DELIA_BACKEND | `pytest tests` em `infra-delia-api` + mounts docs/plugins | 1599 | 1597→1598 | 2→1 | 0 | **runtime_profiles_share_execution_policy**: divergência deliberada de budgets proporcionais ao contexto (ollama 16k→6000/4; qwen 40k→20000/32) — residual `INT1-PROJECTION-BUDGET`, PREEXISTING_PROVEN, exige decisão de política (uniformidade vs proporcionalidade). **module_exposes_native_first_tools**: marcador `OPTIONAL` ausente no docstring — **CORRIGIDO** (bounded, mesmo owner) → GREEN |
| TÉO_OWNER | `pytest tests` em `infra-transformometro-api` + mount | 2189 | 2099 | 28 | 62 | 5 `test_teo_mcp_contract` OAuth = baseline documentado; ~12 `test_transformometro_realtime_*` = `pytest.mark.asyncio` não registrado na imagem (ENVIRONMENT_FAILURE); ~11 suites de domínio — **zero diff da task em `transformometro-api/`** → não-introduzidas por construção |
| VISTA_OWNER | `pytest tests` em `infra-tv-dashboard-api` + mounts shared/fixtures/monorepo-layout | 2534 | 2517 | 17 | 0 | 13 idênticas no baseline `e670c61f1b` (PREEXISTING_PROVEN: catalog budget >102400, execute_delete contract drift, freshness, display_format fixture, m_query phase0 lark); 4 `test_tv_openapi_catalog_sync` = generator/monorepo exec env; 1 `test_m_query_phase0_baseline` = ENVIRONMENT_FAILURE — startup do container eval **escreveu** `data/tv-dashboard/catalog/tv_data_routes.json` (rotas financeiro novas) no working tree, preferido pelo catalog service sobre o packaged |
| DAVI_OWNER | `pytest tests` em `infra-api-delpi` + mount | 5979 | 5889 | 61 | 30 | Massa em `knowledge_subject_addressability`/`live_governed_knowledge` (documentos pinned em data-dirs de prod ausentes) + contratos de domínio alheios — **zero diff da task em `api-delpi/`** → PREEXISTING/ENVIRONMENT |
| MCP_INTEROP / SECURITY / ARCHITECTURE | incluídas na suíte DÉLIA (specialist_interop, argument_validation, authorization, composition, g4) | — | — | — | — | dentro dos 1599 acima |
| E2E_DEV (live outcome) | homologação consolidada §4 | — | — | — | — | evidência live DEV autorizada = avaliação real consolidada |

**Correção bounded aplicada (§5.4):** `declare_investigation_goal` docstring
ganhou o marcador `OPTIONAL` (owner DÉLIA, REUSE, teste já existente) —
RED→GREEN, sem alteração funcional. Nenhum outro defeito elegível a fix
in-scope: restantes são baseline-proven, ambiente ou decisão de política/owner.

```text
BASELINE_FAILURES_PROVEN: 13 VISTA + 5 TÉO OAuth + 1 DÉLIA (profile policy)
NEW_REGRESSIONS:          0 (zero — nenhuma falha introduzida pelo diff)
ENVIRONMENT_FAILURES:     realtime asyncio TÉO (~12), VISTA m_query/env (5),
                          DAVI data-dir fixtures (~61), delia G4 mounts (resolvido por mount)
UNRESOLVED_FAILURES:      1 — runtime_profiles_share_execution_policy
                          (BLOCKED_BY_POLICY_DECISION, owner=DÉLIA config)
```

**R_GATE = FAIL** (critério estrito Doc 293 exige exit 0 na suíte completa;
1 falha classificada PREEXISTING/BLOCKED_BY_POLICY_DECISION impede o PASS
literal — decisão de uniformidade de budgets cabe à coordenação).

---

## 4. FRENTE 3 — Homologação consolidada P1/P2/P3 (mesmo SHA/config)

`or-qwen14b-e069f3b33be8` · sujeito `ti_delpi` · instrução v2-3 (fp
`95e265ee18cd5d66` base; wire `2fff53116c…` P2/P3) · toolset B3 = 15 tools ·
`vista.read` desc sha `071279a8…`

| Cenário | Pergunta | 1ª tool / args | Owner | Resposta | Grounding | Satisfação |
|---|---|---|---|---|---|---|
| P1 | "Qual é a estrutura do produto 90260921?" | `davi.read{capability:get_product_structure, code:90260921}` | DAVI | Estrutura real: Chicote de Ligação PA + componente 10020003 MP 175,0 MT | GROUNDED · status complete | **SATISFIED** |
| P2 | "Quais processos de transformação estão cadastrados?" | `teo.read{entity:process, action:search, params:{}}` — **sem filtro** | TÉO | total=109, janela 1..40, truncamento e continuação honestos | GROUNDED · status partial | **SATISFIED** |
| P3 | "Quais formatos de visualização de dados estão disponíveis?" | `vista.read{entity:display_format, action:list}` | VISTA (TV_READ) | Catálogo autoritativo: modos auto/bar_chart/chart/kpi/line_chart/table + dataBlockTypes + displayFormats | GROUNDED · status partial | **SATISFIED** |

```text
UNREQUESTED_FILTER=NO · FILTERS_APPLIED={} (P2) · PAGINATION_HONEST=YES ·
TV_WRITE_NOT_REQUIRED=YES · AUTHORITATIVE_CATALOG=YES ·
CONSOLIDATED_HOMOLOGATION=SATISFIED (3/3 no mesmo candidato congelado)
MODEL_REQUESTS=3 · TOOL_CALLS=3 · LATENCY: P1 70.6s · P2 38.1s · P3 26.1s ·
TOKENS/COST=UNAVAILABLE (provider não reporta via harness)
```

Sem re-runs de orçamento: 3 investigações válidas, 0 ambientais, 0 repetições.

---

## 5. FRENTE 4 — Matriz L/A/O/R

| Gate | Fonte | Evidência | SHA/config | Veredito proposto | Blocker |
|---|---|---|---|---|---|
| Instrução/fingerprint | Registry+provider | v2-3 fp `95e265ee18cd5d66`, wire `2fff53116c…`, v2-2 preservada | ce96027440 | PASS | — |
| P1 | Doc 16 | DAVI-first, estrutura real, complete GROUNDED | e069f3b33be8 | SATISFIED_PROVEN | — |
| P2 | Doc 16 | search sem params → 109, paginação honesta | e069f3b33be8 | SATISFIED_PROVEN | — |
| P3 | Doc 16 | display_format.list → catálogo autoritativo | e069f3b33be8 | SATISFIED_PROVEN | — |
| **L** | Doc 293 | zero OBSOLETE_PROVEN com consumer ativo no escopo; v2-2 preservada no registry; sem parser/retry/loop paralelo ao Pydantic AI introduzido | ce96027440 | **PASS** | — |
| **A** | Doc 293 | AGENT_COUNT=1; MCPToolset nativo; owners TÉO/VISTA/DAVI intactos; TV_READ≠TV_WRITE; sem autoridade paralela nem RBAC mutation | ce96027440 | **PASS** | — |
| **O** | Doc 293 | admission→seleção semântica→args válidos→owner→AuthZ→evidência→parcial/negação honesta→continuidade→finalização provados docs 310–316 + consolidada | e069f3b33be8 | **PASS** | — |
| **R** | Doc 293 | suítes completas executadas; 0 regressões; 1 falha PREEXISTING classificada (uniformidade de budgets = decisão de política) | ce96027440 | **FAIL** | `INT1-PROJECTION-BUDGET` (runtime profile policy divergence — owner: config DÉLIA; requer decisão canônica) |

## 6. Matriz dos 14 requisitos (reconciliação Doc 314)

```text
REQUIREMENTS_TOTAL: 14
SATISFIED_PROVEN(_IN_SAMPLE): 13 (inclui P1/P2/P3 agora SATISFIED_PROVEN
                              na mesma configuração congelada)
PARTIALLY_SATISFIED:           0 (P2/P3 promovidos de PARTIALLY/BLOCKED em 315)
FAILED_MATERIAL:               0
INCONCLUSIVE:                  0
TEST_NOT_RUN:                  1 — Gate R (executado agora; 1 falha pré-existente
                                 classificada mantém critério estrito não atendido)
BLOCKER_ID:                    INT1-PROJECTION-BUDGET
  OWNER: DÉLIA runtime config · FIRST_DIVERGENCE: profile policy fields
  CANONICAL_REQUIREMENT: profiles divergem apenas em campos técnicos
  CURRENT_EVIDENCE: qwen 40k→{20000,32} vs ollama 16k→{6000,4} — proporcional
  MINIMAL_REMEDIATION: decisão canônica (uniformizar ou formalizar
                       proporcionalidade no contrato do teste)
  TEST_REQUIRED: mesmo teste · EXPECTED_OUTCOME: exit 0 após decisão
```

---

## 7. Residuais, dependências e próxima ação

```text
OPEN_MATERIAL_BLOCKERS:   INT1-PROJECTION-BUDGET (único, classificado, owner
                          identificado — decisão de política, não de código)
NON_BLOCKING_RESIDUALS:   attempt.status conflation · mcp_timeout teo.analyze ·
                          eval-env flakes · falhas baseline TÉO/VISTA/DAVI
                          documentadas · artifact de catálogo gerado em
                          working tree (env-side-effect do eval isolado)
EXTERNAL_DEPENDENCIES:    nenhuma remanescente (EXT-VISTA-READ-FORMAT-CATALOG CLOSED)
RECOMMENDED_VERDICT:      L=PASS A=PASS O=PASS R=FAIL — P1/P2/P3
                          SATISFIED_PROVEN consolidados; fechamento global
                          depende da decisão de política do blocker único
FULL_BATTERY=RUN_AS_AUTHORIZED (Gate R) · PRODUCTION_DEPLOY=NOT_AUTHORIZED ·
PHASE_ADVANCEMENT=NO · INT1_CLOSED=NO
```

**NEXT:** `COORDINATION_INT1_LAOR_AND_FINAL_ACCEPTANCE_INDEPENDENT_REVIEW`
