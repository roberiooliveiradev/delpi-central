# Changelog — `@delpi/plugin-ui`

Formato baseado em [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added

- Manifesto `plugins/shared-libraries.manifest.json` e gate CI `check_plugin_docker_shared_libraries.py`.
- Documentação Docker em `plugins/docker/README.md` e fragmento de Dockerfile.
- Script `scripts/ci/build-tv-dashboard.sh` (gate + build).
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
