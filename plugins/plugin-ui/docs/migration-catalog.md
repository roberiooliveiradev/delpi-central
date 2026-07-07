# Catálogo de migração — cópias locais → `@delpi/plugin-ui`

Objetivo: **uma implementação** de balões explicativos e primitivos de label/aba no monorepo.

## Status

| Plugin | Arquivo local | Status | Notas |
|--------|---------------|--------|-------|
| `tv-dashboard` | — | ✅ Migrado | Referência de integração |
| `cadastro-kaizen` | `src/components/ui/HelpTooltip.tsx` | ⏳ Pendente | + `FieldLabel` |
| `dashboard-lmps` | `src/components/HelpTooltip.tsx` | ⏳ Pendente | |
| `dashboard-commercial` | `src/components/HelpTooltip.tsx` | ⏳ Pendente | |
| `dashboard-engineering` | `src/components/HelpTooltip.tsx` | ⏳ Pendente | |
| `dashboard-financial` | `src/components/HelpTooltip.tsx` | ⏳ Pendente | |
| `dashboard-hr` | `src/components/HelpTooltip.tsx` | ⏳ Pendente | |
| `dashboard-production` | `src/components/HelpTooltip.tsx` | ⏳ Pendente | |
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

## Componentes futuros no pacote

Candidatos quando houver 2+ consumidores:

| Componente | Onde existe hoje |
|------------|------------------|
| `EmptyState` | vários dashboards |
| `ChartCard` shell | `dashboard-production`, clones |
| `KpiCard` shell | dashboards departamentais |
| `DataTable` toolbar | `dashboard-lmps`, `dashboard-commercial` |

**Não** mover sem consolidar — ver [contributing.md](./contributing.md).
