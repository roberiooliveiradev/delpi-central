# Doc 128 — Aba Roteiro: rework visual Plugin UI — evidência

**TASK_ID:** `EVA-PORTAL-ROUTING-UX-PLUGIN-UI-VISUAL-REWORK-01` +
`EVA-PORTAL-ROUTING-UX-VISUAL-GATE-F-RECOVERY-01`
**Estado anterior:** `VISUAL_ACCEPTANCE=FAIL / REWORK_REQUIRED` (PO)
**Base:** `0af682713b` | **Data:** 2026-11-16

## 1. Escopo

Refatoração integral de apresentação da aba Roteiro (ficha do produto,
`?tab=routing`) para o design system canônico `@delpi/plugin-ui`,
conforme Doc 126. Zero mudança de backend, domínio, contratos ou
deduplicação.

## 2. Migração para componentes canônicos

| Elemento | Antes (reprovado) | Depois |
|---|---|---|
| Indicadores | `MetricStrip` (token `--delpi-surface` não mapeado → cartão branco no dark) | `EngineeringKpiCard` (`--delpi-ui-*` mapeado) |
| Tabela operações | `<table>` + expander manual | `DataTable` canônica (wrapper `components/dataTableUi.tsx`, mesmo padrão lmps) com `expandedRowKey`/`renderExpandedRow`/`rowClickRole="button"` |
| Componentes vinculados | lista manual | `DataTable` aninhada no expansor |
| Filtros | selects isolados à esquerda | `EngineeringFiltersRow` + `EngineeringFilterSelect` em `actions` do `EngineeringSectionCard` |
| Formulário | 5 inputs em linha | `EngineeringSectionCard`s "Condições de produção" + "Configuração opcional" + prévia (`EngineeringDetailFieldGrid`) + `EngineeringFormActions` |
| Gráficos | superfície branca no dark, ticks zerados | `ConfigurableSeriesChart` com `theme` (host `data-theme`) + `backgroundColor` resolvido de `--en-surface` via `usePortalTheme`; unidade de apresentação min→s quando máx < 0,5 min (`chartUnits.ts`, display-only) + `decimalPlaces` + `polarity: "high_is_bad"` |
| Comparação | blocos técnicos repetidos | `DataTable` de cenários com parâmetros PROVIDED preservados |

CSS local reduzido a composição de layout (`engineering-routing__*`:
grids de KPIs/formulário/charts, op-detail, badges, muted) — zero
primitivos recriados.

## 3. Gate F — validação visual real

**Ambiente:** recuperado via imagem local
`mcr.microsoft.com/playwright:v1.62.1-noble` (versão idêntica ao
`@playwright/test` do harness) + `--network host` contra stack dev.

**Causas-raiz resolvidas no caminho:**
1. `libnspr4.so` ausente no host → execução dentro do container oficial.
2. `delpi-gateway` com IP stale de `delpi-core-api` (recriado 14:57) →
   `/core-api/me` 502 → portal devolvia `/login` após SSO; `docker
   restart delpi-gateway`.
3. `loginAsDev` resolvia `waitForURL` antes da troca do código
   `response_mode=fragment` (a navegação seguinte abortava a sessão) →
   exclusão `/realms/` + `networkidle` + erro explícito em bounce
   (`e2e/helpers.ts`).
4. Docker COPY cacheado servia bundle pré-rework → rebuild `--no-cache`.

**Execução:** `e2e/specs/routing-visual.spec.ts` — 16 testes (4 specs ×
desktop/mobile/tablet/mobile-320), SSO real, zero pageerrors, zero
chamadas diretas a `/apps/api-delpi`.

**Evidências:** `plugins/engineering/artifacts/routing-visual/*-<projeto>.png`
(44 capturas: operações dark/light, expansão, detalhes técnicos,
balanceamento vazio/preenchido/prévia/resultado/validação/comparação,
gráficos dark/light, vazio honesto — em 4 viewports).

**Defeitos encontrados e corrigidos durante a validação:**
- superfície do gráfico branca no dark (`backgroundColor` padrão do kit
  é light) → resolvido por token;
- colisão título×badge `CALCULATED` em 320px → badges no corpo do card;
- labels da prévia comprimidas em ~500px → "Tempo produtivo";
- "1 operações" → pluralização.

## 4. Gates

| Gate | Resultado |
|---|---|
| A Arquitetura/inventário | PASS |
| B Migração Plugin UI | PASS (subagente confirma: nenhum `<table>/<select>/<button>` na feature) |
| C Funcionalidade/regressão | PASS — 477 vitest, tsc, build, gates transversais 0 findings |
| D Tema claro/escuro | PASS — screenshots reais |
| E Gráficos/escalas | PASS — segundos com ticks legíveis, dark surface |
| F Visual desktop/mobile | PASS — 16 e2e + revisão das capturas |
| G Verificação independente | oficial `INCONCLUSIVE` (infra: devin engine sem auth, r1–r3); fallback clean-context r1 `ACCEPT_WITH_RESIDUAL` → r3 `ACCEPT` |
| H Readiness/rollback | rebuild canônico do MFE; rollback = revert do commit + rebuild |

## 5. Resíduos

- Verificador oficial indisponível por infra (3 rodadas registradas).
- Ticks do eixo Y levemente comprimidos a 320px (kit; não bloqueante).
- Aviso preexistente `react-hooks/set-state-in-effect` (baseline).
- Spec de visual depende do container Playwright (host sem libs de
  browser) — documentado no cabeçalho do spec.
