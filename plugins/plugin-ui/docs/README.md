# Documentação — `@delpi/plugin-ui`

> **UX V3 follow-up cross-MFE (16/11/2026, PO APPROVED / PLANNED):** [Ícone `FilterX` âmbar compartilhado + header sort](../../../docs/12-roadmap-e-evolucao/my-requests/UX-V3-FOLLOWUP-HEADER-SORT-AMBER-CLEAR-CROSS-MFE-PLAN.md). Owner do controle visual deve inventariar o `HelpdeskIconButton` existente e os exports públicos do kit, estender/reusar primitivo existente (Abstraction Gate); fornecer API compartilhada para My Requests Mine/Fila e Helpdesk. Posição: `[FilterX âmbar] [Filtros] [Ordenar] [Colunas] [Tabela|Cards]` na última linha à direita do Hero. Contraste/hover/foco/tooltip/a11y, tokens light/dark, sem CSS MFE duplicado. Nenhum novo componente deve ser declarado implementado antes de testes e deploy.


> **Contrato visual cross-MFE UX V3 (TARGET, 15/11/2026):** [Hero/list toolbar e DataTable — My Requests × Helpdesk](../../../docs/12-roadmap-e-evolucao/my-requests/UX-V3-CROSS-MFE-HERO-LOWER-RIGHT-TOOLBAR-WIREFRAME-AND-ROLLOUT.md). Componentes reutilizáveis, responsive, acessibilidade e posicionamento pertencem ao Plugin UI; aplicar Abstraction Gate. Ainda não implementado.


Índice da biblioteca de UI compartilhada entre plugins MFE.

| Documento | Conteúdo |
|-----------|----------|
| [**novo-plugin-mfe-checklist.md**](../../docs/05-plugin-system/novo-plugin-mfe-checklist.md) | Checklist oficial para criar MFE (vite, bootstrap, Docker) |
| [architecture.md](./architecture.md) | Princípios, escopo, tokens CSS, **CSS canônico vs MFE**, Vite bundled vs MF |
| [module-federation.md](./module-federation.md) | Remote runtime, Docker, consumidor federado, rollout |
| [component-catalog.md](./component-catalog.md) | Inventário de exports, props e exemplos + mapa do app catálogo |
| [bpmn-editor.md](./bpmn-editor.md) | Editor BPMN (`FlowchartEditor`) — checklist MF, wrapper, pastas |
| [contributing.md](./contributing.md) | Como adicionar componente, testes, checklist (+ cobertura visual) |
| [../plugin-ui.manifest.json](../plugin-ui.manifest.json) | App portal «Catálogo UI» (`./App`, permissão `plugin-ui.view`) |
| [`src/catalog/visualComponents.ts`](../src/catalog/visualComponents.ts) | Lista canônica + metadados `addedAt`/`updatedAt` (gate de cobertura) |
| [migration-catalog.md](./migration-catalog.md) | Tracking por plugin + **Fase 7** (zero CSS kit no MFE) |
| [refactoring-roadmap.md](./refactoring-roadmap.md) | Roadmap F1–F6 + **§ 8 Fase 7** (ondas 7.1–7.7) |
| [export-catalog.md](./export-catalog.md) | Catálogo de exportação (CSV / Excel / PDF / PNG; E4 backlog) |
| [chart-view-shell.md](./chart-view-shell.md) | Chart View Shell — famílias, inventário Portal, gaps Excel |
| [rich-text-selection-format-study.md](./rich-text-selection-format-study.md) | Diagnóstico + soluções prescritas: formatação por seleção e mídia inline (`RichTextEditor` × `MentionComposer`) |
| [../kaizometro/docs/UI-PLUGIN-UI.md](../kaizometro/docs/UI-PLUGIN-UI.md) | Migração UI concluída do kaizometro |

**Início rápido:** [README.md](../README.md) na raiz do pacote.
