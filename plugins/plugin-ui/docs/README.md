# Documentação — `@delpi/plugin-ui`

Índice da biblioteca de UI compartilhada entre plugins MFE.

| Documento | Conteúdo |
|-----------|----------|
| [**novo-plugin-mfe-checklist.md**](../../docs/05-plugin-system/novo-plugin-mfe-checklist.md) | Checklist oficial para criar MFE (vite, bootstrap, Docker) |
| [architecture.md](./architecture.md) | Princípios, escopo, tokens CSS, **CSS canônico vs MFE**, Vite bundled vs MF |
| [module-federation.md](./module-federation.md) | Remote runtime, Docker, consumidor federado, rollout |
| [component-catalog.md](./component-catalog.md) | Inventário de exports, props e exemplos + mapa do app catálogo |
| [contributing.md](./contributing.md) | Como adicionar componente, testes, checklist (+ cobertura visual) |
| [../plugin-ui.manifest.json](../plugin-ui.manifest.json) | App portal «Catálogo UI» (`./App`, permissão `plugin-ui.view`) |
| [`src/catalog/visualComponents.ts`](../src/catalog/visualComponents.ts) | Lista canônica + metadados `addedAt`/`updatedAt` (gate de cobertura) |
| [migration-catalog.md](./migration-catalog.md) | Tracking por plugin + **Fase 7** (zero CSS kit no MFE) |
| [refactoring-roadmap.md](./refactoring-roadmap.md) | Roadmap F1–F6 + **§ 8 Fase 7** (ondas 7.1–7.7) |
| [export-catalog.md](./export-catalog.md) | Catálogo de exportação (CSV / Excel / PDF / PNG; E4 backlog) |
| [../cadastro-kaizen/docs/UI-PLUGIN-UI.md](../cadastro-kaizen/docs/UI-PLUGIN-UI.md) | Migração UI concluída do cadastro-kaizen |

**Início rápido:** [README.md](../README.md) na raiz do pacote.
