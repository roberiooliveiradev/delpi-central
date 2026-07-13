# Changelog — `@delpi/plugin-ui`

Formato baseado em [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Fixed

- Select portado (`SelectControl` / `FilterSelectField`): painel no `body` passa a herdar escopo `.dashboard-*` (inferido do âncora ou `portalScopeClassName`), evitando lista sem CSS (bullets / caixas soltas).

### Added

- `FilterSelectField` em `createDashboardFiltersKit` (filtros com `<select>`).
- `createKaizenKpiCard`, `simpleKpiKaizenBemClasses` e `simpleKpiKaizenToneClass` (`SimpleKpiCard` estilo kaizen).
- `createAnalyticsKpiCard` / `simpleKpiAnalyticsBemClasses` (KPI `analytics-kpi` — consumidor `auditoria-5s`).
- `createFilterBarShell`: opção `block` BEM + `embeddedByDefault` (ex.: `a5s-analytics-filters`).
- Documentação da migração completa de `cadastro-kaizen`: [UI-PLUGIN-UI.md](../cadastro-kaizen/docs/UI-PLUGIN-UI.md).
- Manifesto `plugins/shared-libraries.manifest.json` e gate CI `check_plugin_docker_shared_libraries.py`.
- Documentação Docker em `plugins/docker/README.md` e fragmento de Dockerfile.
- Script `scripts/ci/build-tv-dashboard.sh` (gate + build).
- Documentação em `docs/` (arquitetura, catálogo, contribuição, migração).
- Estrutura `src/components/help/` para famílias de componentes.
- `.gitignore`, `vitest.config.ts`.

### Changed

- `cadastro-kaizen`: páginas dashboard, detalhe, filtros e evidências passam a consumir wrappers `components/ui/` (F2/F3 concluído).
- [migration-catalog.md](./docs/migration-catalog.md), [component-catalog.md](./docs/component-catalog.md) e [refactoring-roadmap.md](./docs/refactoring-roadmap.md) atualizados.
- Reorganização: componentes movidos de `src/*.tsx` para `src/components/help/`.
- README expandido com quick start e links para documentação.

## [0.1.0] — 2026-07-07

### Added

- Pacote inicial com família `help`: `HelpTooltip`, `FieldLabel`, `SectionHintLabel`, `TabHintCell`, `HintAction`.
- `styles.css` com tokens `--delpi-ui-*`.
- Primeiro consumidor: `tv-dashboard`.
