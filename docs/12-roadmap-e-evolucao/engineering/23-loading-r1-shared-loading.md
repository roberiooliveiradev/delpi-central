# ENGINEERING.LOADING.R1 — Padronização de carregamento com plugin-ui

Status: implementado e publicado em `main`.
Baseline: `f062cfbec78f310d3b2d3328ef33071a865258ff` (`origin/main` no início).

## Objetivo

Substituir o loading genérico `Carregando indicadores…` do Portal
Engenharia pela experiência canônica já usada pelos demais portais
Minha DELPI (referência: Portal TRANSFORMA+) — container visual,
spinner, título contextual, descrição, barra de progresso, estado
acessível, temas claro/escuro e responsividade — sem criar componente
paralelo nem copiar código/CSS de outro portal.

## G0 — Inventário do loading canônico

### TRANSFORMA+ (referência)

- Arquivo: `plugins/transformometro/src/components/LoadingActivityCard.tsx`.
- Componente: `createDashboardLoadingActivityCard` de `@delpi/plugin-ui/index`
  (factory com `prefix: "ds"`, `withCopyWrapper: true` e labels pt-BR).
- Uso: `DashboardPage.tsx` renderiza `<LoadingActivityCard title=
  "Carregando indicadores do Transformômetro" description=…
  progressPercent={dashboardLoadingProgress} />` durante a primeira carga.
- Origem do progresso: `useSimulatedLoadingProgress` /
  `useTrackedSingleFetchProgress` — **progresso simulado** (estimativa
  visual, não medição real de etapas da API).

### Plugin UI (owner do componente)

- Fonte: `plugins/plugin-ui/src/components/feedback/LoadingActivityCard.tsx`.
- Export público: `src/components/feedback/index.ts` → `src/index.ts`
  (`export * from "./components/feedback"`).
- Contrato: `createDashboardLoadingActivityCard({ prefix, labels,
  withCopyWrapper?, block?, defaultTone? })` → componente com props
  `title`, `description?`, `variant? ("panel"|"compact")`, `tone?
  ("info"|"neutral")`, `sticky?`, `progressPercent?`, `className?`.
- Progresso: `progressPercent` presente → barra determinada + label
  `Faltam N%` + `aria-valuenow`; ausente → **modo indeterminado
  oficial** (barra animada `delpi-ui-loading-slide`, sem percentual,
  `aria-label` indeterminado).
- Acessibilidade: `role="status"`, `aria-live="polite"`, spinner
  `aria-hidden`, `role="progressbar"` com `aria-valuemin/max` e label.
- Estilos: `plugins/plugin-ui/src/styles/loading-activity.css` +
  `card-shell.css`, 100% tokens `--delpi-ui-*`/`--primary`/`--surface` —
  herda tema claro/escuro do Portal e o mapeamento `.portal-engineering`.
- Outros consumidores da mesma factory: `production-appointments`,
  `dashboard-production`, `maintenance`, `strategic-indicators`
  (`LoadingActivityInline`).

### Engenharia (antes)

- `ui/engineeringUi.ts` exportava `EngineeringLoadingState`
  (`createDashboardLoadingState`) — spinner + mensagem genérica, sem
  título/descrição/barra.
- `OverviewPage.tsx` usava `<EngineeringLoadingState message=
  {copy.loading} />` abaixo do hero/filtros.
- `HomePage.tsx` usava `<EngineeringLoadingState />` abaixo do hero.
- `HelpPage.tsx`: conteúdo estático, sem loading — mantido.

## Decisão (Abstraction Gate)

Componente completo já existe no `plugin-ui` e é público → importar e
configurar diretamente, no mesmo padrão dos outros portais. Zero
alteração no `plugin-ui`; zero CSS novo; nenhum componente paralelo.

`EngineeringLoadingActivityCard` =
`createDashboardLoadingActivityCard({ prefix: "engineering", labels
pt-BR, withCopyWrapper: true })` — mesma configuração estrutural do
TRANSFORMA+ (labels são o contrato exigido pela factory, não cópia de
código).

`EngineeringLoadingState` removido — ficaria como componente de
loading paralelo sem consumidores.

## Progresso determinado vs indeterminado (G3)

A Engineering API não expõe etapas mensuráveis de progresso — a
requisição `/v1/overview` é única e o percentual do TRANSFORMA+ é
simulado, não oficial. Portanto **a Engenharia usa o modo
indeterminado oficial** (sem `progressPercent`): barra animada, sem
percentual inventado. Se a API expuser etapas reais no futuro, basta
passar `progressPercent` — o contrato já suporta.

## Matriz de páginas

| Página | Estado de loading | Texto |
|---|---|---|
| Início | `loading` inicial do `useHomeData` | "Preparando sua área de trabalho" / "Consultando tarefas, solicitações e LMPs autorizadas." |
| Visão geral | `state.phase === "loading"` | "Carregando indicadores de Engenharia" / "Consultando as fontes oficiais de LMPs e TRANSFORMA+." |
| Ajuda | sem loading (conteúdo estático) | — |

Copys no catálogo canônico (`HOME_COPY.loading`,
`HOME_COPY.overview.loadingTitle/loadingDescription`).

## Comportamento preservado

- Refresh: botão Atualizar/`refreshing` label intactos; a flag de
  `loading` não é reativada em refresh com dados válidos — sem reset
  visual desnecessário.
- Filtros: mudança de período/competência/unidade mantém o fluxo do
  `useOverviewData` (fase `loading` no novo contexto → novos dados);
  nenhuma alteração funcional.
- Estados finais: `error`, `empty`, `partial`, `forbidden`,
  `unavailable` e KPIs/metas/IDD intactos — o card só aparece na fase
  de carregamento.
- AuthN/AuthZ, isolamento de sessão, tokens, APIs: zero alteração —
  mudança 100% de composição visual no MFE.

## Validação

- Vitest `plugins/engineering`: **93 passed / 11 files** (+3 testes
  novos: wiring da factory + copys contextuais — DOM render é coberto
  pelos testes do componente no `plugin-ui`, que já valida título,
  descrição, spinner, barra, progressbar e arias).
- `tsc -p tsconfig.app.json --noEmit`: 0 erros (shim `plugin-ui.d.ts`
  atualizado com o contrato `createDashboardLoadingActivityCard`).
- `eslint .`: 0 problemas.
- `vite build`: OK; bundle contém as novas copys e a importação
  federada `createDashboardLoadingActivityCard` do remote compartilhado.
- Temas/responsividade/a11y: garantidos pelo CSS canônico do kit
  (tokens `--delpi-ui-*`, breakpoints `card-shell.css`, `role="status"`
  + `progressbar`). QA visual autenticado: `TEST_NOT_RUN`
  (sem sessão autorizada; HTTP 200 não prova layout).

## Deploy e smoke

- Push `main` (fast-forward), deploy canônico `--build engineering`.
- Smoke público: `/apps/engineering`, `/apps/engineering/overview`,
  `/apps/engineering/help` 200; remoteEntry atualizado.
- Smoke autenticado (loading real + refresh + temas): pendente de
  sessão autorizada — residual.

## Residuais

- `VISUAL_QA`/smoke autenticado: `TEST_NOT_RUN` — depende do gate de
  acesso Core (`PENDING_GRANT_APPROVAL`, mesmo residual de F3/R3).
- Progresso determinado: não aplicável — sem fonte de progresso real;
  contrato suporta quando houver.

## Arquivos

- `plugins/engineering/src/ui/engineeringUi.ts` — `EngineeringLoadingActivityCard`
- `plugins/engineering/src/ui/engineeringUiLoading.test.ts` — novo
- `plugins/engineering/src/content/engineeringRouteCatalog.ts` — copys
- `plugins/engineering/src/features/overview/OverviewPage.tsx`
- `plugins/engineering/src/features/home/HomePage.tsx`
- `plugins/engineering/src/shims/plugin-ui.d.ts` — tipos do contrato
