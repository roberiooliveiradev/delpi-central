# Catálogo de migração — cópias locais → `@delpi/plugin-ui`

Objetivo: **uma implementação** de balões explicativos e primitivos de label/aba no monorepo.

## Status

| Plugin | Arquivo local | Status | Notas |
|--------|---------------|--------|-------|
| `tv-dashboard` | — | ✅ Migrado | Referência de integração |
| `dashboard-production` | — | ✅ Migrado | Piloto Fase 1 — `@delpi/plugin-ui` |
| `cadastro-kaizen` | `src/components/ui/HelpTooltip.tsx` | ⏳ Pendente | + `FieldLabel` |
| `dashboard-lmps` | `src/components/HelpTooltip.tsx` | ⏳ Pendente | |
| `dashboard-commercial` | — | ✅ Migrado | Fase 1 — `@delpi/plugin-ui` |
| `dashboard-engineering` | `src/components/HelpTooltip.tsx` | ⏳ Pendente | |
| `dashboard-financial` | `src/components/HelpTooltip.tsx` | ⏳ Pendente | |
| `dashboard-hr` | `src/components/HelpTooltip.tsx` | ⏳ Pendente | |
| `dashboard-quality` | `src/components/HelpTooltip.tsx` | ⏳ Pendente | |
| `dashboard-supplies` | `src/components/HelpTooltip.tsx` | ⏳ Pendente | |
| `eficiencia-fabril` | `src/components/HelpTooltip.tsx` | ⏳ Pendente | |
| `transformometro` | `src/components/HelpTooltip.tsx` | ⏳ Pendente | + `FieldLabel` |
| `quality-action-plans` | `src/components/ui/HelpTooltip.tsx` | ⏳ Pendente | |
| `maintenance` | `src/components/data/HelpTooltip.tsx` | ⏳ Pendente | |
| `portal` | `src/components/HelpTooltip.tsx` | ⚠️ Avaliar | API diferente (`open` controlado, placement `right`); estender pacote ou manter portal |

## Mapeamento de classes CSS legadas

| Prefixo antigo | Ação na migração |
|----------------|------------------|
| `kz-help-tooltip*` | Remover do plugin; usar `delpi-ui-*` + tokens |
| `lmps-help-tooltip*` | Idem |
| `*-field__label` | Manter no plugin como `className` em `FieldLabel` |

## Ordem sugerida de migração

1. **Dashboards departamentais** (mesmo padrão `HelpTooltip` + `FieldLabel`)
2. **cadastro-kaizen** / **transformometro** (já usam `FieldLabel` local)
3. **portal** (só se unificarmos API controlada `open` no pacote)

## Após cada migração

- [ ] Remover arquivo `HelpTooltip.tsx` local
- [ ] Remover bloco CSS `*-help-tooltip` do `index.css` do plugin
- [ ] Atualizar esta tabela para ✅
- [ ] `npm run build` do plugin

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
