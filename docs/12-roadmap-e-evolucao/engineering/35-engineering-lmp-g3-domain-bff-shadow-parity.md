# ENGINEERING.LMP.G3 — Domain Rules, BFF Integration, Unified Authorization & Shadow Parity Evidence

**Status:** domínio LMP implementado e validado em teste na Engineering API — paridade sintética tolerância 0 contra outputs reais do código legado; shadow real e benchmark permanecem pendentes de ambiente autorizado; S2S facts segue bloqueado até provisionamento oficial.
**Baseline:** `BASE_HEAD` = `df2df3c9c493a047b7c27dea470a62ef7c4e94b4` (HEAD real de `origin/main`; trabalho ancorado após commits concorrentes DÉLIA/controllership fora do escopo).
**Autoridades:** docs 32/33/34 (inventário, ownership, facts evidence), `lmp_semantics.v1.yaml` (spec canônica), regras transversais (`centralized-rules-first`, `clean-code-architecture-guardrails`, `platform-security-identity-authorization`, `platform-api-contracts-integration`, `platform-quality-testing`, `evidence-driven-execution`, `english-code-identifiers`).

---

## 1. Escopo implementado

Transferência das regras de negócio elegíveis de LMP da api-delpi para a
Engineering API como **domínio puro** (sem I/O), consumo do contrato facts
via `DownstreamClient` (BFF oficial), contratos funcionais mínimos
E-LMP-01/E-LMP-03 sob `engineering.access` exclusivo, e harness de shadow
parity com fixtures sintéticas geradas pelo código legado real.

Nenhum endpoint/consumidor legado alterado. Aditivo e reversível.

## 2. Fatos G2 revalidados

F-LMP-01..04 inspecionados no HEAD: schemas, paginação (default 50, cap
500), `listing_type`, `include_qtd_pi`, provenance/policy, guard
`require_s2s_or_any_permission(ENGINEERING_LMP_ACCESS)`, erros estáveis.
Compatíveis com as necessidades do domínio — **nenhum ajuste aditivo foi
necessário**.

| Necessidade do domínio | Campo facts | Cobertura |
|---|---|---|
| Nível/SLA (R01–R03) | `qtd_pi` (opt-in F-LMP-01/F-LMP-04) | ✅ |
| Status/dashboard (R04) | `engineering_status`, `residence_minutes`, `end_date` | ✅ |
| Lead time (R05) | `start_date`, `end_date` | ✅ |
| Classe efetiva (S05/S07) | `listing_kind_source`, `has_sample_anchor`, `has_lmp_finalized`, `sample_eng_minutes`, `residence_minutes` | ✅ reexecutada na eng-api e comparada ao `listing_kind` executado na fonte |
| Revisões/ciclos (S12) | `homolog_revision`, `measurement_revision`, `cycle_index` | ✅ |
| Histórico (R15/R16) | F-LMP-03 events/flow (port pronto; contrato funcional na G4) | portado, exercido por teste |

## 3. Estrutura de domínio (owner: engineering-api)

`engineering_app/domain/lmp/` — sem FastAPI/httpx/delpi_*/pydantic
(guarda de pureza em `test_architecture.py::test_domain_layer_is_pure`):

| Módulo | Regras |
|---|---|
| `dates.py` | parse TOTVS/ISO/serial Excel (paridade `parse_spreadsheet_date`), R05 dias úteis |
| `business_rules.py` | R01 SLA por nível, R02 nível por PI, R03 tolerância (+1 d.u. no limite de status, não no `data_limite`), R04 status (RETORNADA→Andamento→OR semântica), formatação |
| `listing_semantics.py` | S05/S07 classe efetiva por revisão, S03 filtro residência ≥30min, filtros `listing_type`/status |
| `dashboard_aggregates.py` | R09 `% no prazo` (numerador = `status != "Atrasado"` — Andamento/Retornada contam: quirk legada preservada e fixtureada), R10 avg lead, R11 charts |
| `history_enrichment.py` | R15 enriquecimento de eventos (labels, current por revisão, late, duration) |
| `flow_transition.py` | R16 detecção entrada/avanço/retorno de engenharia |
| `stage_labels.py` | labels de estágio (S04 apresentação) |
| `parity.py` | comparador tolerância 0 com divergências keyadas por rule-id |

**Pendentes (não elegíveis/sem decisão):** R13/R14 (metas/IDD — owner
Strategic Indicators), R18 (gravação NC — sem decisão de persistência),
regras `SOURCE_INTEGRATION` (permanecem na api-delpi).

## 4. Ports & adapters / BFF

```text
GET /v1/lmps, /v1/lmps/summary  (engineering.access — Core)
  → ListLmpsDashboardUseCase / GetLmpSummaryUseCase  (application)
    → LmpFactsSource (port)
      → ApiDelpiFactsSource (adapter)
        → DownstreamClient GET/POST  (Bearer humano único)
          → api-delpi F-LMP-01 / F-LMP-04
```

- `DownstreamClient.post` adicionado com **a mesma** delegação do GET:
  `Authorization: Bearer <JWT humano>`, `X-Delpi-Caller-App` (telemetria),
  `X-Request-Id` propagado. Nenhum service header, nenhum fallback.
- `fetch_pi_counts` capa o lote em 500 chaves e mapeia `(branch, ov,
  revision)→qtd_pi` via `LmpPiCountsResult.get`.
- Erros → estados honestos: `forbidden` (401/403) / `unavailable`
  (timeout, transporte, contrato) — nunca lista vazia falsa.
- S2S (`engineering-facts.read` + client `engineering-api`) **existe** na
  api-delpi mas depende de provisionamento (doc 34 §11): adapter usa
  apenas Bearer humano; sem credencial inventada, sem bypass.

## 5. Autorização unificada

| Rota | Permissão efetiva (Core) |
|---|---|
| `GET /v1/lmps` (E-LMP-01) | `engineering.access` |
| `GET /v1/lmps/summary` (E-LMP-03) | `engineering.access` |

- `require_any_permission` + `principal_type == "user"` no backend.
- `engineering.manage` **não** concede acesso operacional (teste
  dedicado: manage-only → 403). Nenhum endpoint admin artificial criado.
- Residual search: nenhuma permissão legada (`api-delpi.access`,
  `dashboard-*.view`) em guard/rota nova; referências restantes são
  docstrings e contratos legados pré-existentes de Home/Overview
  (preservados por G3.10 — migração é fase própria).
- Falha da Core → deny (403/503) provado em teste.

## 6. Contratos funcionais

| Contrato | Request | Response (envelope ok/fail) | Erros |
|---|---|---|---|
| E-LMP-01 `GET /v1/lmps` | `start_date`,`end_date` (ISO), `branch`, `listing_type`, `status`, `page`/`page_size≤500` | `items[]` (shape do dashboard legado + revisões/ciclo), `summary`, `charts`, `provenance`, `policy`, `status` | 400 validação, 401 sem JWT, 403 sem permissão/fonte negada |
| E-LMP-03 `GET /v1/lmps/summary` | período, `branch` | realizado: `summary` (R09/R10) sem `goal_*`/IDD | idem |

Endpoints registrados no OpenAPI; superfície autorizada atualizada nos
testes de inventário (`test_health`, `test_auth_middleware`). Rotas
protegidas e **sem roteamento de consumidores oficiais** — cutover na G4
após shadow real.

## 7. Shadow read e paridade

**Harness:** `tests/test_lmp_shadow_parity.py` + `domain/lmp/parity.py`
(tolerância 0, divergências keyadas `rule_id|field|key`).

**Fixtures:** `tests/fixtures/lmp_shadow_fixtures.json` — **geradas
executando `LMPBusinessRules.get_dashboard_status` real da api-delpi**
sobre os cenários obrigatórios; expectations são outputs do owner
anterior, não valores escritos à mão. 17 casos: residência 29/30/31, em
andamento, finalizada pontual (data **e** minutos — OR semântica),
atrasada real, retornada, múltiplas revisões/ciclos, virada de mês, datas
nulas, LMP/AMOSTRA/OUTRO, fim de semana, níveis 1–3.

**Resultado:** `PARITY PASS` — 17/17 itens + agregação R09/R10
consistentes, tolerância 0.

`REAL_SHADOW = TEST_NOT_RUN` — sem ambiente TOTVS autorizado; corpus
200 OVs × 12 janelas permanece protocolo para G4.

**Divergências encontradas e corrigidas durante a migração** (o harness
fez o papel dele):
- parse de `YYYYMMDD` como int/str caía como serial Excel → `None`
  (corrigido: overflow cai no strptime).
- tolerância +1 d.u. pertence ao **limite de status**, não ao
  `data_limite` exibido (corrigido no port).

## 8. Benchmark

`BENCHMARK = TEST_NOT_RUN` — sem ambiente autorizado. Protocolo herdado
doc 34 §8 (3 braços: legado / facts / domínio migrado; P50/95/99; memória;
atenção a N+1 mitigado via F-LMP-04 lote ≤500 e fan-out paginado com teto
`MAX_FACTS_PAGES=40`).

## 9. Testes de segurança executados

| Cenário | Resultado |
|---|---|
| `engineering.access` | 200 |
| sem permissão | 403 |
| somente `engineering.manage` | 403 (sem hierarquia implícita) |
| access + manage | 200 |
| `dashboard-lmps.view` legado | 403 (não substitui) |
| sem JWT | 401 |
| Core indisponível | deny 403/503 — fail-closed |
| fonte `forbidden` (401/403 facts) | 403 envelope |
| fonte `unavailable` | payload `status=unavailable`, items [] |
| período inválido / listing inválido | 400 |

## 10. Consumidores preservados / ciclos

- Dashboard legado, Strategic Indicators, TV, DÉLIA, MFE atual:
  **intocados** — facts continua servindo legado; `engineering-api`
  nunca é chamada pela api-delpi (audit `backend_boundaries` PASS).
- Fluxo proibido eng-api→api-delpi→eng-api: inexistente.
- EVA/MCP: não modificado.

## 11. Matriz de ferramentas EVA candidatas (habilitação futura)

| Tool | Contrato | Quando habilitável |
|---|---|---|
| `search_lmps` | E-LMP-01 | G4 após shadow real PASS |
| `get_lmp_dashboard` | E-LMP-02/03 | G4 (summary realizado pronto; metas via SI) |
| `get_lmp_detail` | E-LMP-04 | após contrato de detalhe (facts F-LMP-02) |
| `get_lmp_history` | E-LMP-05 | após expor R15/R16 via F-LMP-03 |
| `analyze_lmp_performance` | composição oficial | após indicadores oficiais publicados |

Nenhuma ferramenta exposta nesta G3.

## 12. Arquivos alterados (engineering-api)

| Arquivo | Mudança |
|---|---|
| `engineering_app/domain/lmp/*` | **novo** — domínio puro (8 módulos) |
| `application/models/lmp.py` | **novo** — `LmpFact`, `LmpDashboardItem`, `LmpQuery`, resultados |
| `application/ports/lmp_facts.py` | **novo** — `LmpFactsSource` |
| `application/use_cases/{list_lmps_dashboard,get_lmp_summary}.py` | **novo** |
| `infrastructure/gateways/downstream_client.py` | `post` com mesma delegação do GET |
| `infrastructure/gateways/api_delpi_facts.py` | **novo** — adapter F-LMP-01/04 |
| `composition/lmp_composer.py` | **novo** — wiring |
| `interface/http/routes/lmp_routes.py` | **novo** — E-LMP-01/03 |
| `main.py` | include_router(lmp_router) |
| `tests/test_architecture.py` | guarda de pureza do domínio (substitui a proibição de `domain/`) |
| `tests/test_health.py`, `test_auth_middleware.py` | inventário de rotas autorizado |
| `tests/test_lmp_{domain,routes,shadow_parity}.py`, `fixtures/` | **novo** — 44 testes + 17 fixtures geradas do legado |

## 13. Evidência de execução

| Comando | Resultado |
|---|---|
| `pytest engineering-api/tests` | **287 passed** (SHA final) |
| `audit_architecture_phase3 --check` | 0 findings |
| `audit_platform_guardrails --check` | 0 findings |
| `audit_openapi_contracts --check` | 0 findings |
| `audit_fastapi_authz --check` | 0 findings |
| `audit_backend_boundaries --check` | 0 findings — sem import cross-context |
| Scan de segredos nos arquivos alterados | limpo |

## 14. Residuais e riscos

| Item | Owner | Gate |
|---|---|---|
| Provisionamento S2S (client `engineering-api`, audience, `engineering-facts.read`) | Keycloak/Core | desbloqueia smoke autenticado da integração |
| `REAL_SHADOW` 200 OVs × 12 janelas | Dados/infra | G4 — tolerância 0 |
| `BENCHMARK` | infra | G4 |
| E-LMP-02/04/05, exposição R15/R16, consumidores oficiais | Coordenação | G4 após shadow real |
| `stage_path` explícito por revisão no facts | api-delpi | avaliar se G4 exigir |
| Tooling EVA sobre novos contratos | EVA | §11 |

## 15. Próximo gate (G4)

Shadow real autorizado → migração de contratos restantes → roteamento
oficial de consumidores → remoção governada do cálculo legado. Não
avançar automaticamente.
