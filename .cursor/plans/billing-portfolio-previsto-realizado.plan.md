---
name: Billing portfolio previsto×realizado
overview: "Família simples /commercial/billing-portfolio/{summary,series,by-customer,by-branch} na api-delpi — forecast (C6_ENTREG) × realized (D2_EMISSAO), filtros comerciais e granularidade day|week|month|year. Uma família, não duas. Sem composta, sem FCT, sem MFE no MVP."
todos:
  - id: e0-s1-confirm-p1-p4
    content: E0.S1 Confirmar P1–P4 (nature, quantity_basis, MVP 4 rotas, by-customer both)
    status: pending
  - id: e0-s2-fix-doc-drift
    content: E0.S2 Corrigir drift playbook (path único → família simples) + D9 na doc
    status: pending
  - id: e1-s1-extend-port
    content: E1.S1 Estender port/repo forecast (agregado período, by-branch)
    status: pending
  - id: e1-s2-entities-contract
    content: E1.S2 Entities HTTP-friendly (não Snapshot composto de relatório)
    status: pending
  - id: e2-s1-uc-summary
    content: E2.S1 Use case summary + composer wiring
    status: pending
  - id: e2-s2-uc-series
    content: E2.S2 Use case series (build_period_buckets)
    status: pending
  - id: e2-s3-uc-by-customer
    content: E2.S3 Use case by-customer
    status: pending
  - id: e2-s4-uc-by-branch
    content: E2.S4 Use case by-branch
    status: pending
  - id: e3-s1-http-routes
    content: E3.S1 Rotas HTTP + enums nature/quantity_basis
    status: pending
  - id: e3-s2-registry-locale
    content: E3.S2 route_contract_registry + tv_route_audience + param locale
    status: pending
  - id: e3-s3-smoke-coverage
    content: E3.S3 Smoke Nível A + audit_route_test_coverage
    status: pending
  - id: e3-s4-api-docs
    content: E3.S4 Doc commercial-billing-portfolio.md + cross-links
    status: pending
  - id: e4-s1-verify-final
    content: E4.S1 Verify-final live SQL + paridade ROL + objetivo original
    status: pending
isProject: false
---

# Plano — billing portfolio (previsto × realizado)

**Status:** CONCLUÍDO — E0–E4 PASS (2026-09-24). Verify-final: Wanke forecast `66571.05` na semana 2026-08-10..16 via `by-customer`.  
**Owner:** api-delpi / commercial (TOTVS)  
**Regra canônica:** `api-delpi/docs/api/padroes-totvs/carteira-semanal-previsto-realizado.md`

---

## Overview

Expor na api-delpi uma **família de 4 rotas simples** que devolvem receita **prevista** (carteira SC6 por `C6_ENTREG`) e **realizada** (NF/ROL por `D2_EMISSAO`) no mesmo contrato, com granularidade e filtros comerciais — sem acoplar ao layout do Excel e sem segunda família “só previsão”.

---

## Leitura do pedido

| Item | Conteúdo |
|------|----------|
| Objetivo | Rota(s) generalizada(s) previsto × realizado |
| Subobjetivos | Granularidade; filtros filial/segmento/clientes; alinhar ao padrão comercial |
| Restrições | Sem composta; identifiers EN; owner api-delpi; não inventar FCT |
| Dependências | SQL/entity WeeklyPortfolio; ROL canônico; `CommercialAnalysisFilter*` |
| Entregáveis | 4 rotas + testes + doc API + correção drift padroes-totvs |
| Aceite | Summary/series/by-customer/by-branch respondem; live SQL bate caso conhecido; `/rol/*` intacto |

---

## Ledger de requisitos

| ID | Requisito | Estado |
|----|-----------|--------|
| RQ-01 | Expor previsto × realizado via HTTP na api-delpi | ATENDIDO_NO_PLANO |
| RQ-02 | Granularidade day\|week\|month\|year | ATENDIDO_NO_PLANO |
| RQ-03 | Filtros filial, segmento, clientes (+ excludes/centers) | ATENDIDO_NO_PLANO |
| RQ-04 | Organizar como famílias comerciais atuais (rotas simples) | ATENDIDO_NO_PLANO |
| RQ-05 | Reusar fórmula C6_ENTREG vs D2_EMISSAO | HERDADO_POR_SOLUCAO_TRANSVERSAL |
| RQ-06 | Identifiers EN | HERDADO_POR_SOLUCAO_TRANSVERSAL |
| RQ-07 | Não reativar composta ROL / `include=portfolio` | ATENDIDO_NO_PLANO |
| RQ-08 | `nature` + `quantity_basis` defaults | ATENDIDO_NO_PLANO — E0.S1 confirmado |
| RQ-09 | Snapshot `as_of` auditável | FORA_DO_ESCOPO_COM_JUSTIFICATIVA (MVP live; documentar limite) |
| RQ-10 | BFF / MFE / chat / Ajuda | FORA_DO_ESCOPO_COM_JUSTIFICATIVA (MVP API-only; satélite quando houver UI) |
| RQ-11 | Uma família cobre “comparativo” e “só previsão” | ATENDIDO_NO_PLANO (D9) |
| RQ-12 | Positive + sibling + negative + verify live | ATENDIDO_NO_PLANO |

### Rastreabilidade

| RQ | Evidência | Decisão | Subetapa | Teste | Aceite |
|----|-----------|---------|----------|-------|--------|
| RQ-01 | entity/SQL sem HTTP | D1–D2 | E2–E3 | smoke A | 4 rotas 200 |
| RQ-02 | `build_period_buckets` | D5 | E2.S2 | series day/week | points coerentes |
| RQ-03 | `CommercialAnalysisFilter*` | D6 | E2–E3 | sibling segment | filtros aplicados |
| RQ-04 | commercial-analysis-routes | D1 | E3.S1 | antipattern | sem composta |
| RQ-05 | padroes-totvs | D4 | E1–E2 | live Wanke | âncoras no data |
| RQ-06 | english-code-identifiers | D2 | E3 | OpenAPI | path EN |
| RQ-07 | compostas descontinuadas | D8 | E4 | grep | zero composta |
| RQ-08 | playbook decisões | P1–P2 | E0.S1 | — | defaults travados |
| RQ-11 | análise 1 família | D9 | E0–E3 | contrato | realized sempre no payload |
| RQ-12 | evidence-driven | — | E2/E4 | pos/sib/neg | verify-final |

---

## Evidências e hipóteses

**CONFIRMADO_NO_CODIGO:** famílias `/commercial/rol/*` e `/sales-order-otd/*`; `WeeklyPortfolio*` sem wiring HTTP; `build_period_buckets` seg→dom; filtros em `commercial_route_helpers` / `query_param_enums`.

**CONFIRMADO_EM_DOCUMENTACAO_CANONICA:** `carteira-semanal-previsto-realizado.md`; compostas descontinuadas em `commercial-analysis-routes.md`.

**DRIFT:** playbook ainda cita path único sugerido → corrigir em E0.S2 (família simples vence).

| # | Hipótese de organização | Veredito |
|---|-------------------------|----------|
| H1 | Rota composta = Snapshot Excel | **Rejeitada** |
| H2 | Família simples sob prefixo novo | **Escolhida** |
| H3 | Estender `/rol/*` com forecast | **Rejeitada** |
| H4 | Meter em billing-series | **Rejeitada** |
| H5 | Duas famílias (só forecast + forecast×realized) | **Rejeitada** — RQ-11/D9 |

---

## Arquitetura atual × alvo

```text
CURRENT
  Excel/SQL ad hoc
  → CommercialWeeklyPortfolioRepository (forecast, sem HTTP)
  → /commercial/rol/* (realized)

TARGET
  Query (period + filters + nature + quantity_basis [+ granularity])
  → UC billing-portfolio (summary | series | by-customer | by-branch)
  → Forecast: repo SC5/SC6 (C6_ENTREG)
  → Realized: get_rol OU gross NF (nature)
  → Envelope { forecast_value, realized_value, variance_value, … }
  → Consumidores futuros (fora MVP)
```

---

## Decisões travadas

| ID | Decisão | Evidência | Prontidão |
|----|---------|-----------|-----------|
| D1 | Família de rotas **simples** | commercial-analysis-routes | READY_CONFIRMED |
| D2 | Prefixo `/commercial/billing-portfolio/*` | EN + generalização | READY_CONFIRMED |
| D3 | Nome de domínio pode manter “weekly…”; path sem “weekly” | padroes-totvs + RQ-02 | READY_CONFIRMED |
| D4 | forecast=`C6_ENTREG`; realized=`D2_EMISSAO`; declarar no `data` | padroes-totvs + OTD | READY_CONFIRMED |
| D5 | Semana = `build_period_buckets` (seg→dom) | chart_period_buckets | READY_CONFIRMED |
| D6 | Filtros MVP = paridade ROL/OTD (segment, codes, names, centers, excludes, branch, dates) | commercial filters | READY_CONFIRMED |
| D7 | Owner api-delpi only | padroes-totvs | READY_CONFIRMED |
| D8 | Proibido: composta, `include=portfolio`, FCT, path PT | docs + histórico | READY_CONFIRMED |
| D9 | **Uma família** cobre comparativo e “só previsão”; UI ignora `realized_*` se quiser | análise generalista | READY_CONFIRMED |
| D10 | MVP = exatamente 4 rotas (sem series-by-customer/panel) | paridade ROL mínima | READY_CONFIRMED (P3) |
| D11 | Contrato sempre inclui forecast + realized + variance | D9 | READY_CONFIRMED (P4) |
| D12 | Defaults `nature=order_gross`, `quantity_basis=planned` + query override | Excel + playbook | READY_CONFIRMED (P1–P2) |

### E0.S1 — Confirmado (2026-09-24)

| ID | Decisão | Valor |
|----|---------|-------|
| P1 | `nature` default | `order_gross` (+ query `rol`) |
| P2 | `quantity_basis` default | `planned` (+ query `open`) |
| P3 | MVP 4 rotas | sim |
| P4 | by-customer com realized+variance | sim |

---

## Contrato alvo (MVP)

```text
GET /commercial/billing-portfolio/summary
GET /commercial/billing-portfolio/series
GET /commercial/billing-portfolio/by-customer
GET /commercial/billing-portfolio/by-branch
```

| operationId | Shape | `data` |
|-------------|-------|--------|
| `get_billing_portfolio_summary` | scalar | forecast/realized/variance (+ by_branch opcional), nature, quantity_basis, date_basis |
| `get_billing_portfolio_series` | scalar | granularity, truncated, points[] com forecast/realized/variance |
| `get_billing_portfolio_by_customer` | paged_list | items[] customer_* + forecast/realized/variance; summary; pagination |
| `get_billing_portfolio_by_branch` | paged_list | items[] branch + forecast/realized/variance |

Query comum: `start_date`, `end_date`, `branch?`, filtros carteira, `nature`, `quantity_basis`; `granularity` (series); `page`/`page_size` (by-customer).

Permissão: `KPI_COMMERCIAL_ACCESS` (paridade comercial).

---

## Estado antes × depois

| Caso | Antes | Depois | Muda? |
|------|-------|--------|-------|
| P0 novos negócios / semana | Excel/SQL | rotas + `customer_segment=new_business` | sim |
| Sibling WEG / mês | — | mesmos endpoints | sim |
| Sibling series day | — | `granularity=day` | sim |
| Negativo OTD | OTD = % | portfolio = R$ rotas distintas | não |
| Negativo composta | descontinuada | continua | não |
| Invariante `/rol/*` | vivo | intacto | não |

---

## Matriz de fluxos × superfícies

| Fluxo | Superfície | Caminho | Classificação |
|-------|------------|---------|---------------|
| KPI período forecast×realized | api-delpi HTTP | `/billing-portfolio/summary` | P0 |
| Série temporal | api-delpi HTTP | `/billing-portfolio/series` | P0 |
| Ranking/detalhe cliente | api-delpi HTTP | `/billing-portfolio/by-customer` | P0 |
| Totais filial | api-delpi HTTP | `/billing-portfolio/by-branch` | P0 |
| “Só previsão” UI | consumidor futuro | mesma família; ignora realized | HERANÇA (D9) |
| Realizado isolado | `/commercial/rol/*` | intacto | FORA (invariante) |
| OTD prazo | `/sales-order-otd/*` | intacto (irmã `C6_ENTREG`) | FORA |
| Homologação SQL | `/system` + `/data/sql` | verify E4 | P0 evidência |
| TV / commercial-api / chat | — | — | FORA MVP |
| Ajuda in-app | — | — | FORA até feature user-facing (`feature-help-sync`) |

---

## Matriz transversal (8)

| # | Responsabilidade | Aplicação |
|---|------------------|-----------|
| 1 | Arquitetura | Família commercial; ports; sem BFF no MVP |
| 2 | Segurança | `KPI_COMMERCIAL_ACCESS` + branch gate se padrão da rota exigir |
| 3 | Contratos | OpenAPI EN, registry, locale |
| 4 | Dados | SC5/SC6 + SD2; sem migration |
| 5 | Frontend | Fora MVP |
| 6 | Qualidade | smoke + UC/SQL + pos/sib/neg + verify-final |
| 7 | Delivery | só api-delpi |
| 8 | Reliability | timeouts existentes; `as_of=live` no data; cap buckets 366 |

---

## Riscos / compatibilidade

| Risco | Mitigação |
|-------|-----------|
| Comparar gross×ROL sem aviso | `nature` no `data` + enum validado |
| Drift SC6 histórico | `as_of=live` documentado; snapshot fora |
| Series N×2 queries | padrão ROL series; cap 366 |
| Reativar composta | D8 + E4 grep |
| Chat sem Action Catalog | RQ-10 fora; se habilitar agent depois → `new-api-route-checklist` |

Rollout: feature aditiva (rotas novas). Rollback: remover rotas; zero breaking em `/rol/*`.

---

## Etapas e receitas E*.S*

### E0 — Travamento e doc

#### E0.S1 — Confirmar P1–P4
- **Objetivo:** P1–P4 = READY_CONFIRMED neste plano  
- **RQ:** RQ-08, D10–D12  
- **Fazer:** obter confirmação do usuário (defaults ou ajuste); atualizar seção Decisões deste arquivo  
- **Não fazer:** iniciar E1 sem confirmação  
- **Evidência:** defaults alinhados ao Excel/playbook  
- **Dependências:** nenhuma  
- **Teste:** n/a  
- **Pronto quando:** P1–P4 marcados READY_CONFIRMED no plano  
- **Commit:** nenhum (só plano) ou “Trava defaults nature/quantity_basis do billing-portfolio” se editar docs

#### E0.S2 — Corrigir drift documental
- **Objetivo:** padroes-totvs/playbook apontam família `/billing-portfolio/*`, não path único  
- **RQ:** RQ-04, RQ-11, drift  
- **Fazer:** editar `carteira-semanal-previsto-realizado.md` + `playbook-carteira-semanal-previsto-realizado.md` (contrato HTTP = 4 rotas; D9)  
- **Não fazer:** tipar path PT; reintroduzir composta  
- **Evidência:** commercial-analysis-routes vence playbook antigo  
- **Dependências:** E0.S1 (defaults no texto)  
- **Teste:** leitura humana / links  
- **Pronto quando:** zero menção a path único como canônico  
- **Commit:** `Alinha padroes-totvs da carteira semanal à família billing-portfolio.`

---

### E1 — Domain / ports

#### E1.S1 — Estender port/repo forecast
- **Objetivo:** port agrega forecast por período e por branch (não só lista cliente)  
- **RQ:** RQ-01, RQ-05  
- **Fazer:** estender `CommercialWeeklyPortfolioRepositoryPort` + repo SC5/SC6; métodos alinhados a summary/by-branch; reutilizar `CommercialAnalysisFilterService`; `quantity_basis` planned/open  
- **Não fazer:** SQL de realized no mesmo repo se nature=rol (usar FinancialRepository); hardcode clientes Excel  
- **Evidência:** repo atual só `list_delivery_week_forecast_by_customer`  
- **Dependências:** E0.S1  
- **Teste:** `pytest api-delpi/tests/ -q -k weekly_portfolio or billing_portfolio` (SQL unit / predicates)  
- **Pronto quando:** port cobre agregações necessárias aos 4 UCs  
- **Commit:** `Estende port de forecast da carteira para agregados por período e filial.`

#### E1.S2 — Entities de contrato HTTP
- **Objetivo:** tipos de domínio para summary/series/by-* sem espelhar Snapshot de relatório  
- **RQ:** RQ-01, RQ-11, D9  
- **Fazer:** entities/DTOs com forecast/realized/variance + nature + date_basis; não usar `WeeklyPortfolioSnapshot` como body HTTP  
- **Não fazer:** composite_analysis shape; group_by legado  
- **Evidência:** D1/D9; anti-composta  
- **Dependências:** E1.S1  
- **Teste:** unit to_dict / invariantes variance  
- **Pronto quando:** shapes batem com tabela Contrato alvo  
- **Commit:** `Define entities do billing-portfolio sem shape de relatório composto.`

---

### E2 — Use cases

#### E2.S1 — Summary
- **Objetivo:** UC summary compõe forecast + realized no período  
- **RQ:** RQ-01, RQ-03, RQ-05  
- **Fazer:** `GetBillingPortfolioSummaryUseCase`; realized via `get_rol` ou gross conforme nature; wiring `commercial_composer`  
- **Não fazer:** meta SI; notas qualitativas do Excel  
- **Dependências:** E1  
- **Teste:** unit positive new_business; sibling weg; negative período vazio  
- **Pronto quando:** execute retorna tríade + nature  
- **Commit:** `Adiciona use case summary do billing-portfolio.`

#### E2.S2 — Series
- **Objetivo:** série por `build_period_buckets`  
- **RQ:** RQ-02  
- **Fazer:** `GetBillingPortfolioSeriesUseCase`; granularity required; truncated cap 366  
- **Não fazer:** DATEPART ad hoc divergente do bucket canônico  
- **Dependências:** E2.S1 (reuso composição métrica)  
- **Teste:** unit week + day; truncated se range absurdo  
- **Pronto quando:** points[] com sort_key/start/end + tríade  
- **Commit:** `Adiciona série temporal do billing-portfolio.`

#### E2.S3 — By-customer
- **Objetivo:** ranking/lista cliente com tríade  
- **RQ:** RQ-01, RQ-03, RQ-11, P4  
- **Fazer:** `GetBillingPortfolioByCustomerUseCase`; pagination; filtros carteira  
- **Não fazer:** misturar OTD qty  
- **Dependências:** E1  
- **Teste:** positive + exclude codes + empty  
- **Pronto quando:** items[] com forecast/realized/variance  
- **Commit:** `Adiciona ranking por cliente do billing-portfolio.`

#### E2.S4 — By-branch
- **Objetivo:** totais 01/02  
- **RQ:** RQ-01, RQ-03  
- **Fazer:** `GetBillingPortfolioByBranchUseCase`  
- **Não fazer:** inventar filial além 01/02 sem padrão filiais.md  
- **Dependências:** E1  
- **Teste:** consolidado omite branch → ambos; branch=01 só matriz  
- **Pronto quando:** items[] por filial  
- **Commit:** `Adiciona totais por filial do billing-portfolio.`

---

### E3 — HTTP + contrato

#### E3.S1 — Rotas
- **Objetivo:** 4 GETs no `commercial_router`  
- **RQ:** RQ-01–04, RQ-06  
- **Fazer:** paths/operationIds da tabela; `api_delpi_success`; enums nature/quantity_basis em `query_param_enums` (enum+pattern); parsers carteira existentes; `KPI_COMMERCIAL_ACCESS`  
- **Não fazer:** path PT; composta; agent_route chat obrigatório neste MVP  
- **Dependências:** E2  
- **Teste:** smoke handler kwargs Query()  
- **Pronto quando:** 4 operationIds no OpenAPI local  
- **Commit:** `Expõe família HTTP billing-portfolio no commercial_router.`

#### E3.S2 — Registry + locale
- **Objetivo:** contrato registry + labels EN/pt-BR  
- **RQ:** RQ-06; api-delpi-openapi standards  
- **Fazer:** `route_contract_registry`; `tv_route_audience.json`; `openapi_param_locale.json` para params novos  
- **Não fazer:** labels só no MFE  
- **Dependências:** E3.S1  
- **Teste:** sync/check scripts do pacote quando aplicável  
- **Pronto quando:** meta.entity/shape registrados  
- **Commit:** `Registra contrato e locale OpenAPI do billing-portfolio.`

#### E3.S3 — Smoke + coverage
- **Objetivo:** Nível A + inventário coverage  
- **RQ:** RQ-12  
- **Fazer:** testes smoke envelope/meta.operationId; `audit_route_test_coverage.py --write && --check`  
- **Não fazer:** alterar expected para mascarar bug  
- **Dependências:** E3.S1  
- **Teste:** `pytest api-delpi/tests/ -q -k billing_portfolio`  
- **Pronto quando:** coverage check verde para as 4 oids  
- **Commit:** `Cobre smoke e inventário das rotas billing-portfolio.`

#### E3.S4 — Docs API
- **Objetivo:** doc de rota + links comerciais  
- **RQ:** RQ-04  
- **Fazer:** `api-delpi/docs/api/commercial-billing-portfolio.md`; links em commercial-analysis-routes, 06-modulos, padroes-totvs (estado HTTP = vivo)  
- **Não fazer:** docs em planejamento-orcamentario  
- **Dependências:** E3.S1  
- **Teste:** links relativos  
- **Pronto quando:** commercial-analysis-routes não lista portfolio como “só conceito”  
- **Commit:** `Documenta a família commercial billing-portfolio.`

---

### E4 — Verify-final

#### E4.S1 — Prova objetiva
- **Objetivo:** objetivo original comprovado além de testes verdes  
- **RQ:** RQ-12, RQ-05  
- **Fazer:** live `/data/sql` vs summary (ex.: Filial previsto semana 2026-08-10 Wanke 66571.05); paridade realized com `/rol/by-branch` mesmo period quando nature=rol; grep zero composta; checklist RQ  
- **Não fazer:** hardcode Excel clients na asserção de produto  
- **Dependências:** E3  
- **Teste:** script/curl documentado no resultado da etapa  
- **Pronto quando:** tabela pass/fail do objetivo; P0 coberto  
- **Commit:** só se houver fix de regressão encontrado no verify

---

## Fora do escopo

- Snapshot/`as_of` persistido; FCT  
- series-by-customer; panel linhas SC6  
- Meta SI no summary  
- commercial-api BFF; MFE; Ajuda; Action Catalog chat  
- YoY  
- Planejamento orçamentário  

---

## Revisão adversarial

| # | Pergunta | Resposta / correção |
|---|----------|---------------------|
| 1 | RQ sem teste? | RQ-08 só E0; demais mapeados |
| 2 | Fato sem evidência? | Defaults P1–P2 = READY_BOUNDED até E0.S1 |
| 3 | Hipótese concorrente? | H5 (2 famílias) rejeitada via D9 |
| 4 | Owner correto? | api-delpi commercial — sim |
| 5 | Etapa redundante? | E2.S1–S4 são 4 contratos HTTP distintos (paridade ROL) |
| 6 | “Se necessário”? | Removido; cache series = risco documentado, não etapa |
| 7 | Sibling/negativo? | WEG/mês/day; OTD; composta; `/rol` invariante |
| 8 | Testes verdes, falha usuário? | nature misturada; mitiga nature no data + E4 live |
| 9 | Hardcode Excel? | Proibido; segmento/filtros genéricos |
| 10 | Regressão? | `/rol/*` e OTD fora do diff |
| 11 | Compat/rollback? | Rotas aditivas |
| 12 | Outro agente executa? | Receitas E*.S* + YAML todos — sim após E0.S1 |

---

## Critério de pronto do plano

- [x] Ledger + hipóteses + CURRENT/TARGET  
- [x] Família simples + D9 (uma família)  
- [x] Receita por subetapa + YAML todos  
- [x] Matriz fluxos × superfícies + 8 responsabilidades  
- [x] Revisão adversarial  
- [ ] E0.S1 P1–P4 confirmados pelo usuário  
- [ ] Autorização explícita para executar E0.S2+

**Próximo passo:** confirmar P1–P4 (ou aceitar defaults da tabela) e pedir execução.
