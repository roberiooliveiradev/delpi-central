# Catálogo de migração — cópias locais → `@delpi/plugin-ui`

Objetivo: **uma implementação** de balões explicativos e primitivos de label/aba nos **plugins MFE**. O **portal** (shell) permanece fora de escopo — não consome `@delpi/plugin-ui`.

## Status — Fase 1 (help)

| Plugin | Arquivo local | Status | Notas |
|--------|---------------|--------|-------|
| `tv-dashboard` | — | ✅ Migrado | Referência de integração |
| `dashboard-production` | — | ✅ Migrado | Piloto Fase 1 |
| `dashboard-commercial` | — | ✅ Migrado | |
| `dashboard-engineering` | — | ✅ Migrado | |
| `dashboard-financial` | — | ✅ Migrado | |
| `dashboard-hr` | — | ✅ Migrado | |
| `dashboard-lmps` | — | ✅ Migrado | |
| `dashboard-quality` | — | ✅ Migrado | |
| `dashboard-supplies` | — | ✅ Migrado | |
| `cadastro-kaizen` | — | ✅ Migrado | `FieldLabel` + tokens `--delpi-ui-*` |
| `eficiencia-fabril` | — | ✅ Migrado | |
| `transformometro` | — | ✅ Migrado | `TableHeader` local (tabelas HTML) |
| `quality-action-plans` | — | ✅ Migrado | `TitleWithHelp` / `TableHeaderCell` locais (UX com ícone `?`) |
| `maintenance` | — | ✅ Migrado | re-export em `components/data/index.ts` |
| `portal` | `src/components/HelpTooltip.tsx` | ❌ Fora de escopo | Shell do host; API controlada (`open`, placement) diferente |

## Mapeamento de classes CSS legadas

| Prefixo antigo | Ação na migração |
|----------------|------------------|
| `*-help-tooltip*` | Remover do plugin; estilos em `plugin-ui/src/styles.css` (`delpi-ui-*`) |
| `*-field__label` | Manter no plugin como `className` em `FieldLabel` |

## Ordem sugerida de migração (concluída Fase 1)

1. Dashboards departamentais — ✅
2. `cadastro-kaizen`, `transformometro`, `quality-action-plans`, `eficiencia-fabril`, `maintenance` — ✅

## Após cada migração

- [x] Remover arquivo `HelpTooltip.tsx` local
- [x] Remover bloco CSS `*-help-tooltip` do `index.css` do plugin
- [x] Atualizar esta tabela para ✅
- [x] `npm run build` do plugin
- [x] Compose: `context: ../plugins`, `dockerfile: {plugin}/Dockerfile`

## Roadmap completo

Fases 0–5, matriz por plugin, riscos e métricas: **[refactoring-roadmap.md](./refactoring-roadmap.md)**.

## Componentes futuros no pacote

Ver inventário detalhado em [refactoring-roadmap.md § 1.3](./refactoring-roadmap.md#13-componentes-duplicados--candidatos-a-extrair-2-consumidores).

Resumo (2+ consumidores):

| Componente | Ocorrências | Fase sugerida |
|------------|-------------|---------------|
| `KpiCard` | 15 | F2 |
| `ChartCard` | 14 | F2 |
| `LoadingActivityCard` | 12 | F2 |
| `Pagination` (+ jump, page size) | 14–20 | F2 |
| `MultiSelectField` | 13 | F2 |
| `FilterBar` | 12 | F2 |
| `DataTable` / `DataTableSection` | ~25 | F2 (último) |
| `EditableSectionCard` | 3 | F3 |
| `EmptyState` | 2+ | F3/F5 |

**Não** mover sem consolidar — ver [contributing.md](./contributing.md).
