# ENGINEERING.LMP.G2 — Facts Implementation & Parity Evidence

**Status:** implementado e validado em teste — S2S runtime permanece bloqueado até provisionamento oficial (Keycloak/Core).
**Baseline:** `BASE_HEAD` = `3e6bbf291cfed189a003cea5957b0fbb0655e105` (HEAD real de `origin/main`; início do trabalho ancorado em `181b238da8`, fast-forward sem conflito — commits concorrentes fora do escopo LMP).
**Autoridades:** doc 32 (G0 — inventário/consumidores), doc 33 (G1 — ownership/contratos), regras transversais (`centralized-rules-first`, `clean-code-architecture-guardrails`, `platform-security-identity-authorization`, `platform-api-contracts-integration`, `platform-data-persistence`, `platform-quality-testing`, `evidence-driven-execution`, `english-code-identifiers`).

---

## 1. Escopo implementado

Camada **facts** (extração oficial) na api-delpi, aditiva e reversível, sobre o
mesmo dataset físico do dashboard LMP (temp tables `#Delpi_CandidateLMPs`,
`#Delpi_EngResumo`, `#Delpi_PICount`, `#Delpi_PiScope`). Nenhuma regra de
negócio migrada, nenhum endpoint legado alterado, nenhum consumidor
modificado.

| Contrato | Endpoint | Operação |
|---|---|---|
| F-LMP-01 | `GET /engineering/lmps/facts` | `list_lmp_facts` |
| F-LMP-04 | `POST /engineering/lmps/facts/pi-counts` | `get_lmp_pi_counts` |
| F-LMP-03 | `GET /engineering/lmps/facts/{sale_number}/history/events` | `get_lmp_facts_history_events` |
| F-LMP-03 | `GET /engineering/lmps/facts/{sale_number}/history/flow` | `get_lmp_facts_history_flow` |
| F-LMP-02 | `GET /engineering/lmps/facts/{sale_number}` | `get_lmp_fact` |

Rotas literais registradas **antes** de `/lmps/{sale_number}` no
`engineering_router.py` (incluído via `router.include_router(lmp_facts_router)`
no topo do módulo) — não há captura do literal `facts` pelo parâmetro.

## 2. Arquivos alterados

| Arquivo | Mudança |
|---|---|
| `api-delpi/app/infrastructure/persistence/totvs/lmp_repositories/lmp_query_repository.py` | `_staged_facts_select` (projeção facts sobre o staged dataset), `get_lmp_facts`, `_map_lmp_fact_row`; `eng_resumo_lite=False` (lite omite contadores) |
| `api-delpi/app/domain/ports/lmp/lmp_query_repository_port.py` | `get_lmp_facts` com default p/ stubs |
| `api-delpi/app/application/use_cases/lmp/lmp_facts_use_cases.py` | **novo** — `ListLmpFactsUseCase`, `GetLmpFactUseCase`, `GetLmpFactsHistoryUseCase`, `GetLmpPiCountsUseCase` |
| `api-delpi/app/interface/http/routes/engineering/lmp_facts_router.py` | **novo** — rotas, body `LmpPiCountsBody` (lote ≤500), guard `require_s2s_or_any_permission` |
| `api-delpi/app/interface/http/routes/engineering/engineering_router.py` | include do facts router antes das rotas `{sale_number}` |
| `api-delpi/app/interface/http/openapi_agent_metadata.py` | metadados `LMP_FACT_*` / `LMP_PI_COUNTS` |
| `api-delpi/app/interface/http/route_contract_registry.py` | contratos entity/shape dos 5 operationIds |
| `api-delpi/app/composition/engineering_composer.py` | 4 builders facts |
| `api-delpi/contracts/lmp/lmp_semantics.v1.yaml` | **novo** — spec semântica única versionada |
| `api-delpi/tests/test_lmp_facts_contracts.py` | **novo** — 25 testes |
| `docs/12-roadmap-e-evolucao/engineering/34-*.md` | **novo** — este documento |

## 3. Campos e fontes (SOURCE_FIELD_MAPPING)

Projeção de `_staged_facts_select` — mesma base física do summary; campos
comuns compartilham o mesmo alias (paridade verificada por teste).

| Contrato | Origem | Tipo | Significado |
|---|---|---|---|
| `branch` | `C.AD1_FILIAL` (AD1010) | str | filial TOTVS |
| `sale_number` | `C.AD1_NROPOR` | str | número da OV |
| `sale_description` | `C.AD1_DESCRI` | str | descrição da OV |
| `listing_kind_source` | `C.LISTING_KIND` | str | classe bruta da candidata (S04) |
| `listing_kind` | `_effective_listing_kind_expr` | str | classe efetiva (S05/S07) — derivação executada na fonte; consumer deve revalidar |
| `has_sample_anchor` | `C.HAS_SAMPLE_ANCHOR` | bool | âncora de amostra (S04) |
| `has_lmp_finalized` | `C.HAS_LMP_FINALIZED` | bool | passou por 000012 (S04) |
| `sample_eng_minutes` | `H.TEMPO_MINUTOS_AMOSTRA_ENG` | int | minutos em estágios de amostra (S08) |
| `residence_minutes` | `H.TEMPO_TOTAL_MINUTOS_ENG` | int\|null | minutos em estágios de engenharia (S08) |
| `start_date`/`end_date` | `C.LMP_START_DATE`/`LMP_END_DATE` | date | âncora efetiva do período (S06 — `period_anchor` declarado) |
| `homolog_revision` | `C.AD1_REVISA` | str | revisão da candidata |
| `measurement_revision` | `H.MEASUREMENT_REVISION` | str | última revisão de medição eng. |
| `homolog_date` | `C.LMP_START_DATE` | date | mesma convenção do summary legado |
| `cycle_index` | `_staged_cycle_index_expr` | int | ciclo de revisão (S12) |
| `engineering_status` | `H.ENGINEERING_STATUS` | str | status bruto fonte (não classificado) |
| `qtd_engineering_*` (entries/closed/advanced/returned) | `H.QTD_PASSAGENS_*` / `QTD_AVANCOU_ENG` / `QTD_RETORNOU_ENG` | int | contadores de passagem (AIJ010) |
| `qtd_pi` | `PI.QTD_PI` (SB1010/SG1010 BOM, opt-in) | int | contagem PI — fato numérico (S09) |

**Não expostos (proibidos — spec `forbidden_outputs`):** `dashboard_status`,
`nivel`, `sla`, `data_limite`, `lead_time`, `% no prazo`, `goal_*`, `idd`.
Coberto por `test_fact_items_do_not_carry_business_rule_outputs`.

`stage_path` (S04): exposto via `listing_kind_source` + `has_*` +
`engineering_status` + eventos de histórico (F-LMP-03). Stage-path explícito
por revisão adiado para G3 se a revalidação da eng-api exigir — registrado
como residual (doc 33 §3.1).

## 4. Fatos derivados declarados (ADR-LMP-02)

`has_sample_anchor`, `has_lmp_finalized`, `residence_minutes`,
`sample_eng_minutes`, `period_anchor` (= `start_date`/`end_date` +
`policy.period_policy`), `stage_path` (composto — ver §3). Todos definidos em
`contracts/lmp/lmp_semantics.v1.yaml` → `derived_facts` com origem, regra
associada e justificativa de execução na fonte.

## 5. Especificação semântica única

`api-delpi/contracts/lmp/lmp_semantics.v1.yaml` — versão `1.0.0`, owner
semântico `engineering-api`, owner de execução `api-delpi`. Cobre S03–S08,
S12 (semânticas) e R01–R05 (`reference_only` — constantes canônicas para a
migração G3, **não executadas** pelos facts). Registra `known_divergences`
DIV-01 (SQL × domain service), DIV-02 (Andamento/Retornada no numerador R09 —
fixture dedicada `status_in_progress_numerator`), DIV-03 (feriados
TO_INVENTORY). Nenhum KPI final é calculado no caminho facts.

## 6. Autenticação e autorização

Guard: `require_s2s_or_any_permission(ENGINEERING_LMP_ACCESS,
required_scopes=("engineering-facts.read",), allowed_clients=("engineering-api",))`.

- **Caminho humano:** Bearer JWT + permissão funcional LMP existente
  (`api-delpi.access` | `dashboard-engineering.view` | `dashboard-lmps.view`)
  — mesma política do dashboard legado; `caller_app` nunca é autoridade.
- **Caminho S2S:** `X-Delpi-Service-Authorization` (client-credentials
  Keycloak) validado por `ServiceTokenValidator` com escopo e allowlist.
  **Runtime S2S bloqueado** até provisionamento oficial: config ausente →
  503 `S2S_CONFIG_MISSING`; client/escopo inválido → 403; token inválido →
  401. Sem fallback permissivo — header S2S presente nunca degrada para o
  caminho humano.
- **Token compartilhado legado** (`principal_type == "service"` sem header
  S2S): negado com `LEGACY_SERVICE_TOKEN` 403.
- Fail-closed em todos os caminhos — coberto por 4 testes negativos de auth +
  negação de usuário sem permissão + não autenticado.

## 7. Testes e evidência

**Comandos** (`api-delpi/.venv`):

```bash
python -m pytest tests/test_lmp_facts_contracts.py -x -q        # 25 passed
python -m pytest tests/test_lmp_* tests/test_get_lmp_* \
  tests/test_list_lmp_dashboard_use_case.py \
  tests/test_route_contract_registry_completeness.py -x -q      # 115 passed
python -m pytest tests -x -q                                    # suíte completa
python scripts/ci/audit_architecture_phase3.py   --check --base $BASE  # OK 0 findings
python scripts/ci/audit_platform_guardrails.py   --check --base $BASE  # OK
python scripts/ci/audit_openapi_contracts.py     --check --base $BASE  # OK
python scripts/ci/audit_fastapi_authz.py         --check --base $BASE  # OK
python scripts/ci/audit_backend_boundaries.py    --check --base $BASE  # OK
```

**Resultado suíte completa:** 1783 passed, **1 failed** —
`test_davi_similarity_flow_acceptance::test_v3_flow_b_web_research_starts_from_register`.
Falha **não relacionada** ao diff G2: o teste consome
`app/content/openapi_baseline.json` (baseline estático, não alterado) e mede
qualidade de retrieval semântico DAVI; nenhum arquivo do escopo facts é
referenciado. Registrado como `FAIL (pré-existente / fora de escopo)` —
evidência: baseline estático + diff restrito a LMP.

**Cobertura entregue:**

- Unit: paginação/limites, provenance/policy, parâmetros inválidos, lote PI
  >500 rejeitado, ordenação determinística de eventos, strip/opt-in de
  history no detail.
- Envelope/meta: `assert_envelope_meta` para os 5 operationIds
  (entity/shape registrados em `route_contract_registry`).
- AuthN/AuthZ negativos: sem token → Unauthorized; sem permissão → Forbidden;
  legacy service token → 403 `LEGACY_SERVICE_TOKEN`; S2S não provisionado →
  503; escopo ausente → 403.
- Paridade: `test_facts_mapper_parity_with_dashboard_summary_mapper`
  (campos compartilhados idênticos sobre a mesma linha staged),
  `test_facts_select_uses_same_staged_tables_as_dashboard`
  (reuso das temp tables), `test_facts_select_omits_pi_join_when_disabled`.
- `SYNTHETIC_TEST_FIXTURE` — todas as fixtures são sintéticas; paridade é
  estrutural (mapper/select compartilhado), não contra produção.

## 8. Benchmark

`BENCHMARK = TEST_NOT_RUN` — sem ambiente autorizado com dados
representativos. Protocolo executável (doc 33 §12):

```text
Ambiente: homologação com TOTVS volumétrico.
Braços: (a) GET /engineering/lmps/dashboard/summary (legado);
        (b) GET /engineering/lmps/facts (facts);
        (c) facts?include_qtd_pi=true (push-down PI).
Janelas: 3 competências × filiais 01/02 × listing_type {Todos,LMP,Amostra}.
Métricas: P50/P95/P99, tempo SQL, linhas, bytes, queries por request.
Critério: facts P95 <= 1.2× legado (mesmo staged dataset; facts usa
          eng_resumo_lite=False → overhead conhecido: contadores por revisão).
Limites: sem carga em produção; dados sensíveis não coletados.
```

## 9. Observabilidade

Herda o pipeline api-delpi: `request_id`/correlation pelo middleware, log
estruturado `log_error` em falhas com mensagem de validação (sem SQL/valores
sensíveis), `caller_request_stats`/`app_usage_tracker` para métrica de
consumidor (telemetria, não identidade). `s2s_denied`/`s2s_config_missing`
com `code` estável — códigos S2S chegam ao envelope via `error_code`.
Indisponibilidade de fonte propaga como 500 (nunca lista vazia).

## 10. Compatibilidade e consumidores

Zero alteração de comportamento em: `/engineering/lmps`, `/dashboard*`,
`/{sale_number}`, `/history/*`, nonconformities, Transforma+,
Transformômetro, SI, DÉLIA, TV, Portal. Novos paths sob `/lmps/facts*`
não colidem com `{sale_number}` (ordem de registro). Gateways de
consumidores **não** foram migrados (G2 não autoriza). O baseline
`openapi_baseline.json` e o catálogo TV/DÉLIA só são regerados na próxima
homologação autorizada — facts permanecem fora do Action Catalog até lá
(são contratos S2S/técnicos, não tools de chat).

## 11. Riscos e residuais

- **S2S runtime:** escopo `engineering-facts.read` e client `engineering-api`
  precisam ser provisionados no Keycloak/Core — `PENDING` externo; bloqueio
  fail-closed já verificado por teste.
- **`stage_path` explícito:** adiado — flags + histórico suprem a
  revalidação; reavaliar em G3.
- **`homolog_cycles_in_period`/`anchor_*` policies:** facts usa a política do
  `request.listing_type`/settings vigente; política explícita por parâmetro
  de contrato fica para a iteração do consumer (eng-api).
- **DAVI similarity failure:** pré-existente, fora do escopo — acompanhar na
  trilha DAVI.
- **`engineering.manage`:** ainda não registrada no Core — facts não a exige
  (somente leitura).

## 12. Próximo gate (G3)

Portar R01–R18 + S03–S08/S12 para módulo de domínio da engineering-api
consumindo F-LMP-01..04; shadow read instrumentado (N=200 OVs × 12 janelas,
tolerância 0) contra o dashboard legado usando as fixtures de
`test_lmp_facts_contracts.py` como corpus inicial; benchmark §12 quando
houver ambiente autorizado.
