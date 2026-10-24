# 137 — Remediação bounded das falhas de testes do api-delpi

**TASK_ID:** `DELIA-C3-DAVI-BASELINE-TEST-FAILURES-BOUNDED-REMEDIATION-01`
**PLAN_ID:** `DELIA-ORCHESTRATION-RESPONSIBILITY-REFACTOR-FINITE-01`
**REFERENCE_REVIEW:** `84306b0eb3d0b2cdd4ac50c6688fa67f02ff7fee` (revisão independente do doc 136)
**Data:** 2026-10-24
**Natureza:** remediação bounded da dívida de regressão do `api-delpi` — matriz causal completa, correções mínimas nos owners canônicos, zero ocultação de teste. Sem deploy (gate governado). Sem R3.

---

## 1. Reancoragem e autoridade

| Item | Valor verificado |
|---|---|
| BASE_SHA | `86942f8540` (`origin/main` no início — inclui o push F01–F06 `1f3bc4a640`) |
| Worktree isolada | `/home/analistaptd/davia-testfix-wt` — checkout principal e trabalho concorrente preservados |
| Autorização | prompt PO desta task; deploy produtivo **não** autorizado por este prompt |
| Authorities lidas | `.cursor` always-on + `delia-execution-protocol`; reancoragem 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25; specs 03/60; ADR 58; roadmap 59; S4/117; docs 125/129/130/134/135/136; parecer independente do doc 136 (`84306b0e`); ledger vigente |

Decisões congeladas respeitadas: zero classificador lexical paralelo; `DISCOVERY != APPROVAL`; `READ != PREPARE != ACT`; nenhum teste apagado, nenhum `xfail`/`skip` novo, nenhuma assertion relaxada por conveniência — expectativas só foram atualizadas onde a evolução sancionada do produto foi comprovada por commit.

## 2. Inventário baseline × candidato

Suíte completa `api-delpi` (6.044 testes coletados) reproduzida em worktree sob configuração equivalente. Comparação exata por test ID e assinatura de falha:

| Conjunto | Resultado |
|---|---|
| `BASELINE_ONLY_FAILURES` | `∅` |
| `SHARED_FAILURES` | todo o inventário — conjunto de falhas **byte-idêntico** ao rodar os mesmos arquivos com os arquivos alterados pela F06 revertidos ao baseline |
| `CANDIDATE_ONLY_FAILURES` | `∅` — F06 não introduziu regressão nova (confirma a revisão `84306b0e`) |

**Correção de ambiente:** a contagem "74" foi observada sob ambiente sem as variáveis de plugins-DB. Sob o ambiente oficial (rede `infra_delpi-network` + `PLUGINS_DB_*` do compose dev), os testes dependentes de plugins-DB passam — `ENVIRONMENT_CONFIGURATION`, não defeito. Inventário real agrupado em **10 causas-raiz**, não 74 defeitos.

## 3. Matriz causal de fechamento

| GRP | FAILED_TESTS (n) | ROOT_CAUSE | OWNER / CONTRACT | FIX_TYPE | STATUS |
|---|---|---|---|---|---|
| G1 | 28 | Allowlist governada evoluiu v22→v23 (commit sancionado `89693fb049` — restauração SQL canônica: `execute_readonly_sql`, 95 ops, token `select` fora da quarentena); expectativas congeladas em v22/94 | `davi_external_read_allowlist.json` + testes | TEST (+1 fixture benchmark) | CLOSED_PROVEN |
| G2 | 16 | Bypass auditado do SQL validator virou default ON (`dacf4fa7ca`, sancionado); fixtures deletavam a env var e passavam a exercitar modo bypass | `sql_validator` + fixtures de teste | FIXTURE (setenv enforcement explícito) | CLOSED_PROVEN |
| G3 | 3 | Testes geradores chamam `git rev-parse HEAD`; imagem `infra-api-delpi` não contém git e o gitdir da worktree não era visível | ambiente de execução | ENVIRONMENT_CONFIGURATION | CLOSED_PROVEN (verde com git + gitdir montados) |
| G4 | 2 | `cadastro-produto.md` evoluiu 2026-10-23 sem re-pin do manifesto governado | `build_davi_governed_knowledge_bundle.py emit-manifest` (procedimento canônico, precedentes `4ad6347231`/`6aa37384b4`) | FIXTURE (re-pin canônico) | CLOSED_PROVEN |
| G5 | 3 | Diretivas projetadas 17.149B > soft budget 16KiB após restauração SQL sancionada (+778B); corpus já estava a 13B do teto | `DAVI_AGENT_DIRECTIVES_MAX_BYTES` (guard interno, não contrato publicado; referência de transporte é 64KiB) | PRODUCT (re-baseline documentado 16→20KiB) | CLOSED_PROVEN |
| G6/G7 | 9 | `BRANCH_QUERY_OPTIONAL` (`01c1bc93de`) tornou chamadas diretas sem `branch` inválidas (Depends não resolvido); `customer_centers` adicionado às assinaturas de use cases (sancionado) | rotas + use cases | TEST | CLOSED_PROVEN |
| G8 | 3 | 9 `operation_id` novos (suppliers Protheus REST, integration tracking, GPT schema, supplies requesters/cost_centers, audit_5s force-close) sem entrada no registry; 2 testes inspecionavam `router.routes` com `_IncludedRouter` lazy do FastAPI 0.156.8 | `route_contract_registry.py` + framework | PRODUCT (registry) + TEST (lazy include) | CLOSED_PROVEN |
| G9 | 2 | Inspeções: `COUNT(*)` apareceu legitimamente em `list_operation_inspections` (agregação two-step sancionada) — assertion era file-scoped; `historico_tela` literal virou constante `HISTORICO_TELA_VIEW` | repositório inspeções + testes | TEST (escopo/case da assertion) | CLOSED_PROVEN |
| S1..S6 | 6 | Singletons — ver §4 | por item | PRODUCT×2 / TEST×4 | CLOSED_PROVEN |
| ENV | 2 | plugins-DB ausente na invocação sem env oficial | ambiente | ENVIRONMENT_CONFIGURATION | CLOSED_PROVEN |

## 4. Singletons (S1–S6)

| ID | Teste | Causa | Fix |
|---|---|---|---|
| S1 | `test_lancamentos_sem_busca_usa_resumo_e_nao_chama_count` | **PRODUCT_DEFECT real** — `d85e9e09d8` migrou o DTO para `PaginationEnvelopeBuilder` sem o import → `NameError` em runtime | import adicionado no DTO (`despesas_centro_custo_lancamentos_response.py`) |
| S2 | `test_gpt_get_catalog_lists_v1_ops_without_raw_rbac` | **PRODUCT_DEFECT real** — nota de `system_metadata` projetava o identificador bruto `api-delpi.access` no catálogo externo | rewording no owner canônico (`davi_agent_intelligence.json`): "generic API access alone is not sufficient" — semântica preservada, identificador removido |
| S3 | `test_kpi_fields_merges_common_si_and_route_bundles` | `3f0b8e6f37` introduziu label sancionado "Meta (rótulo)" no bundle financeiro | expectativa atualizada |
| S4 | `test_fetch_consumption_analysis_rows_binds_period` | binds do universo 3019 reordenados pela feature sancionada (`f4e56918c5` cadeia) | assertion atualizada para a ordem vigente + tail period/product_code |
| S5 | `test_inventory_factories_match_defaults` | inventário de paginação cresceu 120→122 (tiers sancionados, `ef124cfa36`/`0d110ac59d`) | expectativa atualizada |
| S6 | `test_kaizen_savings_investment_series` (×2) | `a4c26762c3` mudou projeção para dias úteis (253/365) via `business_days_equivalent` | expectativas passam a usar o helper canônico |

## 5. Correções de produto (owner canônico)

1. **`despesas_centro_custo_lancamentos_response.py`** — import `PaginationEnvelopeBuilder` restaurado (defeito real de `d85e9e09d8`; `NameError` em `to_dict()`).
2. **`route_contract_registry.py`** — 9 `operation_id` registrados com entity/shape derivados dos envelopes reais das rotas (sem shape inventado): `gpt_get_openapi_schema`, `create/update_protheus_rest_supplier`, `get_integration_operation`, `list_integration_operation_events`, `list_supplies_purchase_request_cost_centers`, `list_supplies_purchase_request_requesters`, `get_supplies_protheus_user_by_email`, `force_close_audit_5s_nc_without_treatment`.
3. **`davi_agent_intelligence.json`** — remoção do identificador RBAC bruto da projeção externa (S2).
4. **`davi_agent_intelligence_service.py`** — `DAVI_AGENT_DIRECTIVES_MAX_BYTES` 16→20KiB com comentário documentando o driver (v23) e o teto de transporte 64KiB. **Decisão a registrar:** o conteúdo governado está denso e integralmente pinned; o re-baseline preserva a guarda contra bloat acidental sem deletar diretivas sancionadas. Flagado para revisão da coordenação.
5. **`davi-governed-knowledge-manifest-v1.json`** — re-pin via `emit-manifest` canônico (somente hash de `cadastro-produto.md` + metadados).

## 6. Correções de testes/fixtures (justificadas)

- **G1:** versão 22→23, contagens 94→95, `execute_readonly_sql` incluído nos conjuntos elegíveis/allowlist; `"select"` fora da quarentena global; query `sql` saiu da parametrização de quarentena e ganhou teste dedicado de roteamento canônico; benchmark fixture: 6 casos `GENERIC_SQL_NEGATIVE` convertidos para `POSITIVE_PRECISE` esperando `execute_readonly_sql` (redirect canônico governado provado live @0.88–0.9), família `canonical_sql`.
- **G2:** fixtures passam a declarar `DATA_SQL_SKIP_TABLE_WHITELIST=false` explicitamente — enforcement continua testado sob o novo default auditado.
- **G6/G7:** chamadas diretas recebem `branch=None` explícito (Depends não resolve fora do FastAPI); asserts de mock incluem `customer_centers=None`.
- **G8:** testes de path inspecionam rotas materializadas via `effective_route_paths()` — helper novo em `tests/support/route_contract_smoke.py` que resolve `original_router`+`include_context.prefix` dos `_IncludedRouter` lazy (FastAPI 0.156.8).
- **G9:** `COUNT(*)` restrito ao método `list_historico_by_branch`; `historico_tela` → `HISTORICO_TELA_VIEW`.
- **Singletons:** conforme §4.

`EXISTING_EQUIVALENT=YES` `REUSE_DECISION=REUSE|EXTEND` em todos os grupos — zero registry/engine/adapter paralelo.

## 7. Suites executadas

| Suíte | Resultado |
|---|---|
| **api-delpi completa** (env oficial) | **6.026 passed / 15 skipped / 3 failed** — os 3 são `ENVIRONMENT_CONFIGURATION` (git ausente na imagem de teste); provados verdes com git + gitdir montados (41 passed) |
| api-delpi DAVI/retrieval blast-radius | verde — `test_davi_*` incluídos na suíte completa |
| sql_validator (G2) | 116 passed |
| **delia-api completa** | **2.202 passed / 3 skipped / 0 failed** — idêntico ao baseline pós-F01–F06 |
| F01–F06 regression | preservado — bond estrito, required enforcement, guidance precedence, goal-free terminals, aliases material — todos dentro dos 2.202 |

## 8. Segurança e arquitetura

- SQL genérico segue `STATUS_GENERIC_SQL_FORBIDDEN`; somente a rota canônica `execute_readonly_sql` é descoberta (bounded, requestBody exigido; baseline sem contrato → `NEEDS_BOUNDED_EXECUTION`).
- Bypass auditado do validator mantém AST/safeguards; testes de enforcement agora explicitam o modo — nenhuma salvaguarda removida.
- `api-delpi.access` e demais identificadores RBAC brutos fora da projeção externa; AuthZ backend permanece autoridade.
- `DISCOVERY != APPROVAL`; `READ != PREPARE != ACT`; candidate_token nunca projetado; nenhuma mudança de fluxo de segurança.
- AP-01…AP-20 reconciliados: DAG acíclico, owner único de projeção, zero duplicação de contrato.

## 9. Riscos residuais e pendências

- **G5 flag para coordenação:** re-baseline do soft budget 16→20KiB — alternativa seria cortar conteúdo governado (degradação) ou bloquear o grupo como `ARCHITECTURE_DECISION_REQUIRED`. Decisão executada com justificativa inline + aqui; revisão independente pode reverter e reclassificar.
- 3 testes geradores dependem de git na imagem de execução — oficialmente verdes; a imagem `infra-api-delpi` sem git é limitação documentada do harness local, não do produto.
- Suite não executada: homologação produtiva `kimi-k3` (gate de release governado, fora desta task).

## 10. Estado de readiness

`RELEASE_READINESS=READY_FOR_INDEPENDENT_REVIEW` — sem regressão nova; falhas materiais do escopo resolvidas; segurança preservada; testes executados e rastreáveis; rollback = `git revert`. `DEPLOY_STATUS=NOT_EXECUTED` — próximo gate: release governado `delia-api` + `api-delpi` com autorização operacional e homologação `kimi-k3`.
