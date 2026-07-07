# Changelog — `@delpi/plugin-ui`

Formato baseado em [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added

- Documentação em `docs/` (arquitetura, catálogo, contribuição, migração).
- Estrutura `src/components/help/` para famílias de componentes.
- `.gitignore`, `vitest.config.ts`.

### Changed

- Reorganização: componentes movidos de `src/*.tsx` para `src/components/help/`.
- README expandido com quick start e links para documentação.

## [0.1.0] — 2026-07-07

### Added

- Pacote inicial com família `help`: `HelpTooltip`, `FieldLabel`, `SectionHintLabel`, `TabHintCell`, `HintAction`.
- `styles.css` com tokens `--delpi-ui-*`.
- Primeiro consumidor: `tv-dashboard`.
