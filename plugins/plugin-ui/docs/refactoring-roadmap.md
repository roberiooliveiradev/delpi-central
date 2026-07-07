# Roadmap de refatoração — componentes compartilhados (`@delpi/plugin-ui`)

> **Objetivo:** eliminar duplicação de UI transversal entre plugins MFE, centralizando em `plugins/plugin-ui/` sem quebrar builds, Docker nem tema claro/escuro no portal federado.  
> **Baseline:** jul/2026 · **Único consumidor hoje:** `tv-dashboard`.

---

## 1. Diagnóstico (varredura do monorepo)

### 1.1 O que já existe em `@delpi/plugin-ui`

| Família | Exports | Testes |
|---------|---------|--------|
| `help` | `HelpTooltip`, `FieldLabel`, `SectionHintLabel`, `TabHintCell`, `HintAction` | `FieldLabel.test.tsx` |

Referência de integração: `plugins/tv-dashboard/` (alias Vite + `styles.css` + tokens `--delpi-ui-*`).

### 1.2 Cópias locais de `HelpTooltip` (prioridade máxima)

| Plugin | Arquivo | Linhas | Variante |
|--------|---------|--------|----------|
| `dashboard-production` | `src/components/HelpTooltip.tsx` | ~324 | Portal + viewport + `FieldLabel` |
| `dashboard-commercial` | idem | ~324 | idem |
| `dashboard-engineering` | idem | ~324 | idem |
| `dashboard-financial` | idem | ~324 | idem |
| `dashboard-hr` | idem | ~324 | idem |
| `dashboard-lmps` | idem | ~324 | idem |
| `dashboard-quality` | idem | ~324 | idem |
| `dashboard-supplies` | idem | ~324 | idem |
| `transformometro` | idem | ~332 | idem |
| `quality-action-plans` | `src/components/ui/HelpTooltip.tsx` | ~363 | + `TitleWithHelp` |
| `cadastro-kaizen` | `src/components/ui/HelpTooltip.tsx` | ~294 | `FieldLabel` com `htmlFor` |
| `eficiencia-fabril` | `src/components/HelpTooltip.tsx` | ~59 | CSS hover simples (sem portal) |
| `maintenance` | `src/components/data/HelpTooltip.tsx` | ~59 | CSS hover simples |
| `portal` | `src/components/HelpTooltip.tsx` | — | ⚠️ API controlada (`open`) + `placement: right` |

**Impacto estimado:** ~3.800 linhas duplicadas só na família help (8 dashboards × ~324 LOC).

### 1.3 Componentes duplicados — candidatos a extrair (2+ consumidores)

Legenda: **A** = extrair para `plugin-ui` · **B** = pacote irmão futuro (`@delpi/dashboard-shell`?) · **L** = manter local (domínio ou uso único).

#### Tier A — shell de dashboard (mesmo DNA, só muda prefixo CSS)

| Componente | Ocorrências | Referência canônica | Notas |
|------------|-------------|---------------------|-------|
| `KpiCard` | 15 | `dashboard-production` | Completo (metas IDD) + `SimpleKpiCard` compacto (fcc, cr) |
| `ChartCard` | 14 | `dashboard-production` | Variantes com/sem `titleHint`, `actions` |
| `LoadingActivityCard` | 12 | `dashboard-production` | Lógica idêntica; classes `dp-*` vs `dc-*` etc. |
| `Pagination` | 14 | `dashboard-production` | ✅ F2.4 — 7 dashboards dept.; `createDashboardPaginationKit` |
| `PaginationPageJump` | 8 | `dashboard-production` | ✅ incorporado em `Pagination` |
| `TablePageSizeSelect` | (em `Pagination.tsx`) | `dashboard-production` | ✅ incorporado em `Pagination` |
| `MultiSelectField` | 13 | `dashboard-production` | ✅ F2.5 — 8 dashboards + lmps |
| `FilterBar` | 12 | `dashboard-production` | ✅ F2.6 — `FiltersRow` + `FilterInputField` (alias `FilterBar`) |
| `ChartToolbar` | 6 | `dashboard-production` | ✅ F2.7 + `ChartGranularityToggle` |
| `DataTable` | ~12 dashboards | `dashboard-production` | Maior risco — colunas via props |
| `DataTableSection` | ~12 | `dashboard-production` | Toolbar busca + paginação |

#### Tier B — formulários / detalhe (menos consumidores, alta similaridade)

| Componente | Ocorrências | Ação sugerida |
|------------|-------------|---------------|
| `EditableSectionCard` | 3 (`cadastro-kaizen`, `transformometro`, `quality-action-plans`) | **A** após Fase 2 |
| `ReadOnlyField` | 2 | **A** |
| `SelectField` | 2 (`quality-action-plans`, `transformometro`) | **A** |
| `PageHeader` | 7 | Avaliar diff; provável **A** com slots |
| `DetailFieldGrid` | 5 | **A** ✅ F3.1 |
| `DetailCard` | 3 | **A** |
| `StructureLegend` | 2 | **L** ou **A** se unificar com LMP/commercial |
| `EmptyState` | 2 (+ chat próprio) | **A** variante mínima |
| `LoadingState` | 2 | **A** |

#### Tier C — evidências / modais (domínio parcial)

| Componente | Ocorrências | Ação |
|------------|-------------|------|
| `*Dropzone*` / `*FileDropzone*` | 6 | **B** futuro — API de upload varia por domínio |
| `ConfirmDialog` / `useConfirmDialog` | 4 | **B** — chat tem UX própria |
| `ChartExpandModal` | 1 (`maintenance`) | **L** |

#### Utilitários duplicados (não são componentes, mas DRY)

| Arquivo | Ocorrências | Destino sugerido |
|---------|-------------|------------------|
| `utils/paginationPages.ts` | 7 dashboards | ✅ `plugin-ui/src/utils/paginationPages.ts` |
| `utils/goalDisplay.ts` | 8 dashboards | `@delpi/dashboard-utils` (semântica IDD) |
| `constants/chartColors.ts` | 10 | `plugin-ui` tokens ou import do portal |

### 1.4 Plugins sem cópia de HelpTooltip (nada a migrar na Fase 1)

`tv-dashboard` (✅), `controle-retrabalhos`, `inspecoes-entrada`, `financeiro-centro-custo`, `pedidos-venda-abertos`, `auditoria-5s`, `strategic-indicators`, `minha-delpi-chat`, `api-delpi-console`, `customer-experience`, `cultura-delpi`, `public-hub`, `central-agendamento`, `quality-labels`, `propostas-comerciais`.

### 1.5 Fora de escopo imediato

| Pacote | Motivo |
|--------|--------|
| `minha-delpi-chat` | UI de chat/apresentação rica — contrato próprio; não misturar com shell de dashboard |
| `strategic-indicators` | Design system interno (`ui/components/*`) — migrar só primitivos isolados se duplicarem dashboards |
| `tv-dashboard-presentation` | Já é biblioteca irmã declarada em `shared-libraries.manifest.json` |
| Presenters de domínio | Cards OEE, fishbone, árvore TOTVS, etc. |

---

## 2. Princípios de migração (sem quebrar o front)

### 2.1 Padrão estrangulador (recomendado)

```text
1. Adicionar alias Vite + import styles.css (sem remover código local)
2. Trocar imports em 1–2 arquivos piloto → build verde
3. Migrar restante dos imports; remover arquivo local
4. Remover CSS legado (*-help-tooltip*, etc.)
5. Validar portal federado (claro + escuro + mobile)
```

**Nunca** big-bang em todos os plugins num único PR.

### 2.2 Contrato de estilos (obrigatório)

Componentes em `plugin-ui` usam:

- Classes base `delpi-ui-*` no pacote
- Props `className`, `*ClassName` para o plugin continuar com prefixo local (`dp-`, `dc-`, `kz-`, …)
- Tokens `--delpi-ui-accent|surface|text|border|muted` mapeados no `.dashboard-{nome}` do plugin

O pacote **não** importa CSS do plugin consumidor.

### 2.3 Textos PT-BR

Permanecem em `src/content/helpTooltips.ts` de cada plugin. O pacote recebe só `content` / `hint` / `label` via props.

### 2.4 Docker / CI

Todo plugin que passar a importar `@delpi/plugin-ui` precisa:

1. `resolve.alias` em `vite.config.ts`
2. `import "../../plugin-ui/src/styles.css"` no entry (`main.tsx`)
3. `Dockerfile`: `COPY plugin-ui` + `context: ../plugins` no Compose
4. Gate: `python3 scripts/ci/check_plugin_docker_shared_libraries.py --check`

Modelo: `plugins/tv-dashboard/Dockerfile`.

### 2.5 Definition of Done (por plugin)

- [ ] Zero `HelpTooltip.tsx` local (Fase 1)
- [ ] `npm run build` verde
- [ ] Smoke visual: tooltip, aba com ?, campo com label
- [ ] Tema escuro no portal (não só Vite dev)
- [ ] Docker build verde (se aplicável)
- [ ] Linha atualizada em [migration-catalog.md](./migration-catalog.md)

---

## 3. Fases do roadmap

### Fase 0 — Infraestrutura transversal (1 sprint, paralelo)

| # | Entrega | Responsável |
|---|---------|-------------|
| 0.1 | Template `vite.config` + snippet `main.tsx` na doc | plugin-ui |
| 0.2 | Fragmento Docker reutilizável (`plugins/docker/shared-libraries.Dockerfile.fragment`) — validar em 2 plugins piloto | infra |
| 0.3 | Estender `HelpTooltip` com `placement: "right"` e `open?: boolean` (portal) **ou** documentar exceção permanente do portal | plugin-ui |
| 0.4 | Export `TitleWithHelp` → alias de `SectionHintLabel` ou helper fino | plugin-ui |
| 0.5 | Script opcional: detectar `HelpTooltip.tsx` local (`scripts/ci/audit_plugin_ui_duplication.py`) | CI |

### Fase 1 — Família `help` (quick win, ~2–3 sprints)

**Meta:** 13 plugins migrados; ~3.800 LOC removidas.

| Lote | Plugins | Ordem |
|------|---------|-------|
| 1a Piloto | `dashboard-production` | Referência departamental + mais maduro |
| 1b Dashboards clone | `commercial`, `engineering`, `financial`, `hr`, `lmps`, `quality`, `supplies` | Copiar checklist do piloto; PRs em paralelo (1 plugin = 1 PR) |
| 1c Domínio | `transformometro`, `cadastro-kaizen`, `quality-action-plans` | Atenção a `FieldLabel`/`TitleWithHelp` |
| 1d Simplificados | `eficiencia-fabril`, `maintenance` | Ganho a11y (portal/viewport vs CSS puro) |
| 1e Portal | `portal` | Só após 0.3 — API controlada |

**Checklist por plugin (Fase 1):**

```ts
// vite.config.ts
"@delpi/plugin-ui": path.resolve(__dirname, "../plugin-ui/src/index.ts"),

// main.tsx
import "../../plugin-ui/src/styles.css";

// index.css — dentro de .dashboard-{nome}
--delpi-ui-accent: var(--{prefix}-accent, var(--primary, #089bdb));
// … demais tokens (ver architecture.md)
```

Substituir:

```ts
import { HelpTooltip, FieldLabel } from "./HelpTooltip";
// →
import { HelpTooltip, FieldLabel } from "@delpi/plugin-ui";
```

Remover blocos CSS `*-help-tooltip*` do `index.css`.

### Fase 2 — Shell de dashboard (4–6 sprints)

Extrair componentes **headless + className**, usando `dashboard-production` como implementação de referência.

| Ordem | Componente | Família em plugin-ui | Dependência |
|-------|------------|----------------------|-------------|
| 2.1 | `LoadingActivityCard` | `feedback/` | Fase 1 |
| 2.2 | `ChartCard` | `layout/` | Fase 1 |
| 2.3 | `KpiCard` | `layout/` | Fase 1; props para badges IDD opcionais |
| 2.4 | `Pagination` + `PaginationPageJump` + `TablePageSizeSelect` | `data/` | ✅ Fase 1 + utils `paginationPages` |
| 2.5 | `MultiSelectField` | `forms/` | ✅ Fase 1 (`FieldLabel`) |
| 2.6 | `FilterBar` | `layout/` | ✅ `FiltersRow` + `FilterInputField` |
| 2.7 | `ChartToolbar` + `ChartGranularityToggle` | `layout/` | ✅ Fase 1 |
| 2.8 | `DataTable` + `DataTableSection` | `data/` | ✅ variante padrão (7 dept.) |

**Estratégia KpiCard:** um componente com props opcionais (`goalScopeBadge`, `goalPerformanceBadges`, …). Plugins simples (`controle-retrabalhos`) usam subset mínimo.

**Estratégia CSS:** mover regras **estruturais** para `delpi-ui-kpi-card` etc.; cores/densidade continuam no plugin via BEM prefixado ou `className`.

**Piloto Fase 2:** migrar `dashboard-production` inteiro → replicar para os 7 dashboards irmãos.

### Fase 3 — Formulários e detalhe (2–3 sprints)

| Componente | Consumidores-alvo | Status |
|------------|-------------------|--------|
| `DetailFieldGrid` | production, commercial, quality, lmps, eficiencia-fabril | ✅ F3.1 |
| `EditableSectionCard` | kaizen, transformometro, PAC | ✅ F3.2 |
| `ReadOnlyField` | kaizen, PAC | ✅ F3.3 |
| `SelectField` | PAC, transformometro | ✅ F3.4 |
| `DetailCard` | production, commercial, lmps | ✅ F3.5 |
| `PageHeader` | 7 plugins operacionais | ✅ F3.6 |
| `SectionCard` | PAC | ✅ F3.2 |
| `EmptyState` / `LoadingState` | controle-retrabalhos, financeiro-centro-custo | ✅ F3.7 |

### Fase 4 — Utilitários compartilhados (1 sprint)

| Utilitário | Status | Destino |
|------------|--------|---------|
| `paginationPages.ts` | ✅ | `plugin-ui/src/utils/paginationPages.ts` |
| `chartColors.ts` | ✅ | `plugin-ui/src/utils/chartColors.ts` |
| `operationalUnitLabels.ts` | ✅ | `plugin-ui/src/utils/operationalUnitLabels.ts` |
| `goalDisplay.ts` | ✅ | `plugin-ui/src/utils/goalDisplay.ts` |

Dashboards 8× reexportam via `src/utils/*.ts` e `src/constants/chartColors.ts` (~1 linha).

### Fase 5 — Backlog / avaliar demanda

| Item | Status | Notas |
|------|--------|-------|
| `FileDropzone` | ✅ F5.1 | kaizen, PAC, transformometro |
| `useConfirmDialogController` | ✅ F5.2 | PAC hook + transformometro provider |
| `strategic-indicators` utils | ✅ F5.3 | `operationalUnitLabels` reexport |
| Dropzones restantes (chat, customer-experience) | ⏳ | Domínio/API distinta — fora de escopo imediato |
| `ConfirmModalPanel` | ✅ F5.4 | Headless; `Modal` shell permanece local (PAC, transformometro) |
| `Modal` base | ⏳ | Shell por plugin — não extrair sem contrato unificado |

---

## 4. Matriz plugin × fase

| Plugin | F1 help | F2 shell | F3 forms | Docker hoje |
|--------|---------|----------|----------|-------------|
| `dashboard-production` | ✅ | ChartCard ✅ KpiCard ✅ LoadingActivity ✅ Pagination ✅ MultiSelect ✅ | — | sim |
| `dashboard-commercial` | ✅ | ChartCard ✅ KpiCard ✅ LoadingActivity ✅ Pagination ✅ MultiSelect ✅ | — | sim |
| `dashboard-engineering` | ✅ | ChartCard ✅ KpiCard ✅ LoadingActivity ✅ Pagination ✅ MultiSelect ✅ | — | sim |
| `dashboard-financial` | ✅ | ChartCard ✅ KpiCard ✅ LoadingActivity ✅ Pagination ✅ MultiSelect ✅ | — | sim |
| `dashboard-hr` | ✅ | ChartCard ✅ KpiCard ✅ LoadingActivity ✅ Pagination ✅ MultiSelect ✅ | — | sim |
| `dashboard-lmps` | ✅ | ChartCard ✅ KpiCard ✅ LoadingActivity ✅ MultiSelect ✅ | Detail* | sim |
| `dashboard-quality` | ✅ | ChartCard ✅ KpiCard ✅ LoadingActivity ✅ Pagination ✅ MultiSelect ✅ | — | sim |
| `dashboard-supplies` | ✅ | ChartCard ✅ KpiCard ✅ LoadingActivity ✅ Pagination ✅ MultiSelect ✅ | — | sim |
| `transformometro` | ✅ | LoadingActivity ✅ | EditableSectionCard ✅ PageHeader ✅ | sim |
| `cadastro-kaizen` | ✅ | — | EditableSectionCard ✅ | sim |
| `quality-action-plans` | ✅ | parcial | PageHeader ✅ SectionCard ✅ | sim |
| `eficiencia-fabril` | ✅ | LoadingActivity ✅ | — | sim |
| `maintenance` | ✅ | parcial | — | sim |
| `controle-retrabalhos` | — | Kpi/Chart ✅ LoadingActivity ✅ | Empty/Loading ✅ | sim |
| `inspecoes-entrada` | — | Pagination ✅ KpiCard ✅ | PageHeader ✅ | sim |
| `inspecoes-entrada` | — | Kpi/Pagination ✅ | PageHeader | sim |
| `financeiro-centro-custo` | — | Kpi/Chart/Empty | ChartCard ✅ Empty/Loading | sim |
| `pedidos-venda-abertos` | — | Kpi/Filter | PageHeader | sim |
| `auditoria-5s` | — | ChartCard | — | sim |
| `tv-dashboard` | ✅ | — | — | sim |
| `portal` | ❌ fora de escopo | — | — | N/A (shell) |

---

## 5. Riscos e mitigação

| Risco | Mitigação |
|-------|-----------|
| Regressão visual (tema escuro) | Validar no portal federado; tokens `--delpi-ui-*` |
| Build Docker quebra | Gate CI `check_plugin_docker_shared_libraries.py`; piloto tv-dashboard |
| `KpiCard`/tabela muito acoplados ao prefixo CSS | Props `className` granulares; não mover CSS de marca para o pacote |
| `eficiencia-fabril`/`maintenance` perdem tooltip CSS-only | Migração = melhoria a11y (portal + teclado) |
| PRs grandes | **1 plugin = 1 PR** na Fase 1; Fase 2 componente a componente |
| Portal API `open` controlado | Estender pacote (Fase 0.3) antes de migrar portal |

---

## 6. Métricas de sucesso

| Métrica | Hoje | Meta pós-F1 | Meta pós-F2 |
|---------|------|-------------|-------------|
| Arquivos `HelpTooltip.tsx` locais | 1 (portal) | 0 nos plugins | 0 |
| Plugins consumindo `@delpi/plugin-ui` | 15 | 15 ✅ | 20+ |
| LOC duplicada (help only) | ~3.800 | ~0 | ~0 |
| Componentes shell duplicados | ~80 arquivos | ~80 | ≤15 |

---

## 7. Próximo passo recomendado

1. **Fase 1 concluída** nos plugins MFE — portal permanece com implementação própria.
2. **Fase 2 concluída** nos dashboards departamentais.
3. **Fase 3.1 concluída** — `DetailFieldGrid` em 5 consumidores.
5. **Fase 3 concluída** — formulários/detalhe/shell operacional migrados.
6. **Fase 4 concluída** — utilitários centralizados.
7. **Fase 5 parcial** — `FileDropzone`, confirm controller, `ConfirmModalPanel`, SI `operationalUnitLabels`; backlog: `Modal` base, dropzones chat/CE.

---

## Referências

- [component-catalog.md](./component-catalog.md) — API atual
- [migration-catalog.md](./migration-catalog.md) — tracking por plugin (Fase 1)
- [architecture.md](./architecture.md) — tokens, Vite, Docker
- [contributing.md](./contributing.md) — critérios para novo componente
- [plugins-reusable-components.mdc](../../../.cursor/rules/plugins-reusable-components.mdc)
- [plugins-visual-design-system.mdc](../../../.cursor/rules/plugins-visual-design-system.mdc)
