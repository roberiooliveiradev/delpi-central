# F3.OVERVIEW — Implementação da Visão geral

Status: `IMPLEMENTADO`
Data: 2026-10-28
Baseline: `origin/main` `8389500d71` (reancorado; design ref `0ab67cfb03`)
Autoridade de design: `18-f3-overview-design-contract.md` (DESIGN_CANDIDATE → implementado)

## 1. Escopo executado

`GET /v1/overview` na `engineering-api` (composição autorizada dos seis
indicadores oficiais) + refatoração integral de
`plugins/engineering/src/features/overview/OverviewPage.tsx` conforme
WF-OV-01/WF-OV-02: Hero com filtros, grade de seis KPIs, estados
honestos e área de aprofundamento governada.

Fora de escopo (não iniciado): F2b, EVA/MCP, Sala de Interação,
migração do módulo LMPs, refatoração de outros portais.

## 2. Inventário G0 — fontes e owners

| Indicador | Owner | Endpoint oficial | AuthZ downstream |
|---|---|---|---|
| % LMP dentro do prazo | api-delpi / Strategic Indicators | `GET /engineering/lmps/dashboard/summary` | `ENGINEERING_LMP_ACCESS` |
| Lead time médio (dias úteis) | api-delpi | idem | idem |
| Total de propostas | api-delpi | idem (`total_items` preferido; `total_lmps` fallback do próprio owner) | idem |
| Ganhos brutos TRANSFORMA+ | api-delpi / SI | `GET /engineering/transforma-mais/processes/summary` | `ENGINEERING_LMP_ACCESS` |
| Soluções implementadas | api-delpi | idem | idem |
| ROI médio TRANSFORMA+ | api-delpi | idem (`average_roi`, multiplicador ×) | idem |
| Metas (`goal_*`) | Strategic Indicators (via `enrich_dashboard_metric` na api-delpi) | embutido nos resumos | idem |
| Nota IDD | Strategic Indicators | `GET /dashboard/department-indicators?department_id=engineering` | `DASHBOARD_IDD_ACCESS` / supplies-BFF |

IDs canônicos SI preservados: `engineering-projects-on-time` →
`lmp_on_time`; `engineering-transforma-plus` → `transforma_gross_savings`.

Referência funcional: `plugins/dashboard-engineering` (mesma semântica
de mapeamento, formatação pt-BR, metas/IDD via
`buildKpiGoalPresentation` do kit). Nenhum código importado entre MFEs.

## 3. Contrato `GET /v1/overview`

`GET /apps/engineering-api/v1/overview` — operationId
`get_engineering_overview`, envelope canônico `{success,data,meta}`.

Request (query, todos opcionais):
- `start_date`, `end_date` — YYYY-MM-DD; intervalo invertido ou formato
  inválido → 400;
- `competence` — YYYY-MM (validado 01–12);
- `branch` — unidade operacional repassada aos owners que suportam o
  recorte.

Response (`schema_version: "1.0"`): `generated_at`, `filters` (eco
efetivo), `status` (`available|partial|unavailable`) e `indicators[]`
com `id`, `label`, `family` (`lmp|transforma`), `availability`
(`available|empty|unavailable|forbidden`), `value`, `unit`, `scope`,
`start_date`/`end_date`, `source`/`source_endpoint`, conjunto completo
`goal_*`/`value_*` (espelho `DashboardGoalFields`), `idd`/`idd_label`,
`reason`/`message` sanitizados.

Serialização por owner preservada: LMP recebe datas `YYYYMMDD` +
`branch`; TRANSFORMA+ recebe ISO + `filial_id`; SI recebe
`competence`/datas/`branch`.

## 4. AuthN/AuthZ e delegação

- `require_any_permission(["engineering.access"])` — permissão efetiva
  resolvida pela Core (fail-closed).
- `principal_type == "user"` — service principal → 403.
- Bearer humano delegado aos owners; `X-Delpi-Caller-App` +
  `X-Request-Id` propagados; **nenhum** `X-Delpi-Service-Token` nas
  leituras personalizadas (F2a.R1 preservado — testado com token interno
  configurado).
- 401/403 downstream → família `forbidden`; demais falhas →
  `unavailable` com `reason` (`timeout|transport_error|upstream_error|
  contract_error`). Falha SI degrada só o IDD (`idd: null`).

## 5. Frontend

- `api/engineeringOverviewApi.ts` — client do envelope canônico +
  validação de contrato; `useOverviewData` com AbortController +
  sequence guard (requests obsoletos cancelados).
- `overviewFilters.ts` — presets do kit (`resolvePeriodPreset`,
  `detectPeriodPreset`, timezone America/Sao_Paulo), vínculo
  competência↔datas com a mesma política do dashboard, URL sync com os
  parâmetros do contrato (`start_date|end_date|competence|branch` —
  nenhum dado sensível).
- `overviewViewModel.ts` — `buildOverviewCards` usa
  `formatDashboardMetricValue` + `buildKpiGoalPresentation` +
  `resolveIndicatorIddScoreLabelFromSi` do kit (mesma apresentação de
  meta/escopo/IDD do dashboard — paridade de renderização); ROI em `×`;
  `value: null` → `—`, nunca zero.
- `OverviewPage.tsx` — PageHero (eyebrow `PORTAL ENGENHARIA`, título
  `Visão geral`, subtítulo, Atualizar com `RefreshCw` + disabled +
  aria-label) com faixa de filtros (`QuickPeriodSelector`, `DateField`
  date/month, `MultiSelectField` unidade `maxSelected=1`) + grade de 6
  `EngineeringKpiCard` (mesmo `createDashboardKpiCard` do dashboard) +
  aprofundamento.
- Aprofundamento: LMP = módulo interno futuro (informativo, sem CTA,
  sem redirect legado); TRANSFORMA+ = CTA `/apps/transformometro`
  somente quando `permissions` do host contém `transformometro.access`
  — sem botão desabilitado insinuando acesso.
- Responsividade: 3 colunas desktop / 2 tablet / 1 mobile; temas via
  tokens `--delpi-ui-*` (claro/escuro herdados do kit).
- Ajuda (`feature-help-sync`): nova seção "Visão geral" no manual.

## 6. Testes

- Backend: `tests/test_overview.py` (21) + `test_overview_gateways.py`
  (12) — AuthN/AuthZ, principal humano, seis indicadores, metas/IDD,
  filtros e validações, partial/forbidden/empty/unavailable, timeout,
  delegação humana sem service token, serialização por owner,
  OpenAPI. Suíte completa engineering-api: **193 passed**. Allowlist de
  rotas (`test_health`, `test_auth_middleware`) atualizada com a rota
  autorizada.
- Frontend: `engineeringOverviewApi.test.ts` (7), `overviewFilters.test.ts`
  (20), `overviewViewModel.test.ts` (12) — contrato, serialização,
  presets, vínculo competência/datas, unidade, formatação pt-BR,
  meta/IDD, estados. Suíte completa: **89 passed**.
- Typecheck `tsc --noEmit` 0 erros; `eslint` 0; `vite build` OK.
- Paridade (contrato): mesmo payload do owner produz os mesmos seis
  valores mapeados no dashboard (`percent_dentro_prazo`,
  `avg_lead_time`, `total_items ?? total_lmps`,
  `total_gross_savings_in_period`, `implemented_solutions_count`,
  `average_roi`) — coberto pelos testes de gateway/viewmodel. Paridade
  visual autenticada: pendente de sessão autorizada (gate G8).

## 7. Gates e limitações

- Manifest `0.2.0` na Core: `PENDING_OPERATOR_TOKEN` (herdado).
- Grant `engineering.access`: `PENDING_GRANT_APPROVAL` (herdado) —
  rota permanece fail-closed até o grant.
- Smoke autenticado e QA visual: `TEST_NOT_RUN`/`PENDING` — sem sessão
  autorizada; critérios D01–D05 baseados em código/tokens, não em
  screenshot.
- `department-indicators` exige `DASHBOARD_IDD_ACCESS` ou caminho
  supplies-BFF; sem a permissão, IDD fica `null` por contrato (honesto)
  — não há grant ad-hoc criado.
- Audits CI repo-wide (`mfe_plugin_ui_css`, `plugin_ui_duplication`)
  têm achados pré-existentes em outros MFEs; zero introduzidos pelo
  escopo (audits `backend_boundaries`, `platform_guardrails`,
  `architecture_phase3`, `fastapi_authz`: 0 findings).

## 8. Deploy e smoke (2026-10-28)

- SHA: `3108d81910` (commit `19ccc3147f` rebased sobre `origin/main`).
- Deploy canônico: `git pull --ff-only` em `srv-api` +
  `up-prod-sequential.sh --build engineering-api engineering` —
  `delpi-engineering-api` e `delpi-engineering` recriados e `Up`.
- Smoke público: `200` em `/apps/engineering`, `/overview`, `/help`,
  `remoteEntry.js` e `/apps/engineering-api/health`; `401` em
  `/v1/overview` sem JWT (fail-closed).
- Evidência de bundle: `remoteEntry` → `App-Dvlq6Wf3.js` contém
  `v1/overview`, `lmp_on_time`, `transformometro`, `Período rápido`.
- Smoke autenticado: pendente de grant `engineering.access`.
- Rollback: `git revert 3108d81910` + redeploy dos dois serviços.
