# Catálogo de migração — cópias locais → `@delpi/plugin-ui`

Objetivo: **uma implementação** de balões explicativos e primitivos de label/aba no monorepo.

## Status

| Plugin | Arquivo local | Status | Notas |
|--------|---------------|--------|-------|
| `tv-dashboard` | — | ✅ Migrado | Referência de integração |
| `dashboard-production` | — | ✅ Migrado | Piloto Fase 1 |
| `dashboard-commercial` | — | ✅ Migrado | Fase 1 |
| `dashboard-engineering` | — | ✅ Migrado | Fase 1 |
| `dashboard-financial` | — | ✅ Migrado | Fase 1 |
| `dashboard-hr` | — | ✅ Migrado | Fase 1 |
| `dashboard-lmps` | — | ✅ Migrado | Fase 1 |
| `dashboard-quality` | — | ✅ Migrado | Fase 1 |
| `dashboard-supplies` | — | ✅ Migrado | Fase 1 |
| `cadastro-kaizen` | `src/components/ui/HelpTooltip.tsx` | ⏳ Pendente | + `FieldLabel` |
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

1. ~~**Dashboards departamentais**~~ ✅ Concluído (8 plugins)
2. **cadastro-kaizen** / **transformometro** / **quality-action-plans**
3. **eficiencia-fabril** / **maintenance** (variante CSS hover simples)
4. **portal** (só se unificarmos API controlada `open` no pacote)

## Após cada migração

- [ ] Remover arquivo `HelpTooltip.tsx` local
- [ ] Remover bloco CSS `*-help-tooltip` do `index.css` do plugin
- [ ] Atualizar esta tabela para ✅
- [ ] `npm run build` do plugin

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
