# Roadmap de refatoração — componentes compartilhados (`@delpi/plugin-ui`)

> **Objetivo:** eliminar duplicação de UI transversal entre plugins MFE, centralizando em `plugins/plugin-ui/` (TSX **e** CSS `.delpi-ui-*`) sem quebrar builds, Docker nem tema claro/escuro no portal federado.  
> **Regra absoluta (jul/2026):** **zero CSS de componente do kit no MFE** — ver Cursor `plugins-reusable-components.mdc`. MFE só: tokens `--delpi-ui-*` + layout de página + UI fora do kit.  
> **Baseline:** jul/2026 · **Consumidores:** 27 MFEs via Module Federation (`pluginUiRemote()` + `preparePluginUiRemote()`) — rollout MF **concluído**; ver [module-federation.md](./module-federation.md).
> **Próxima frente:** § 8 — **Fase 7** (compliance CSS + cópias/markup residual). **Não implementar** lotes da Fase 7 sem atualizar o tracking neste doc + [migration-catalog.md](./migration-catalog.md).

---

## 1. Diagnóstico (varredura do monorepo)

### 1.1 O que já existe em `@delpi/plugin-ui`

| Família | Exports | Testes |
|---------|---------|--------|
| `help` | `HelpTooltip`, `KeyTip`, `FieldLabel`, `SectionHintLabel`, `TabHintCell`, `HintAction` | `FieldLabel.test.tsx`, `KeyTip.test.tsx` |

Referência de integração: `plugins/controle-retrabalhos/` (MF + `preparePluginUiRemote()`).

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
| `MultiSelectField` | 13 | `dashboard-production` | ✅ F2.5 — 8 dashboards + lmps + ef + transformometro |
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
| `strategic-indicators` | Design system interno (`ui/components/*`) | ✅ F3.12 — filtros + admin SelectControl; StatusBadge/SectionBlock no pacote; domínio (PanZoom, presentation) permanece local |
| `tv-dashboard-presentation` | Já é biblioteca irmã declarada em `shared-libraries.manifest.json` |
| Presenters de domínio | Cards OEE, fishbone, árvore TOTVS, etc. |

---

## 2. Princípios de migração (sem quebrar o front)

### 2.1 Padrão estrangulador (componentes — histórico Fase 1)

Para **novos plugins**, usar Module Federation desde o início — [novo-plugin-mfe-checklist.md](../../docs/05-plugin-system/novo-plugin-mfe-checklist.md).

```text
1. Scaffold MF (vite + bootstrap + Docker federado)
2. Importar de @delpi/plugin-ui/index
3. Tokens --delpi-ui-* no dashboard
4. Validar portal federado (claro + escuro + mobile)
```

### 2.2 Contrato de estilos (obrigatório)

Componentes em `plugin-ui` usam:

- Classes canônicas `.delpi-ui-*` (+ dual-class `{prefix}-*` via `delpiUiClass` / `*BemClasses`)
- Tokens `--delpi-ui-*` (mapeados no `.dashboard-{nome}` do MFE)
- CSS **somente** em `plugins/plugin-ui/src/styles/**`

O pacote **não** importa CSS do plugin consumidor.  
O MFE **não escreve CSS** de componente do kit **em hipótese alguma** (nem BEM local espelho, nem override `.delpi-ui-*`) — Cursor `plugins-reusable-components.mdc`.

### 2.3 Textos PT-BR

Permanecem em `src/content/helpTooltips.ts` de cada plugin. O pacote recebe só `content` / `hint` / `label` via props.

### 2.4 Docker / CI (jul/2026 — Module Federation)

Todo plugin MFE que consome `@delpi/plugin-ui`:

1. `remotes: pluginUiRemote()` + `shared: FEDERATION_SHARED_REACT` em `vite.config.ts`
2. `await preparePluginUiRemote()` no `bootstrap.tsx`
3. `Dockerfile`: `COPY vite ./vite` — **sem** `COPY plugin-ui`; `context: ../plugins` no Compose
4. Compose: `<<: *plugin-ui-federated` (`depends_on: plugin-ui`)
5. Gate: `python3 scripts/ci/check_plugin_docker_shared_libraries.py --check`

Checklist: [novo-plugin-mfe-checklist.md](../../docs/05-plugin-system/novo-plugin-mfe-checklist.md). Modelo: `plugins/controle-retrabalhos/Dockerfile`.

**Bundled** permanece só para `@delpi/tv-dashboard-presentation` (`tv-dashboard`, `public-hub`).

### 2.5 Definition of Done (por plugin)

- [ ] Zero `HelpTooltip.tsx` local (Fase 1)
- [ ] Dual-class presente no DOM (`prefix` + `delpi-ui-*`) nos exports do kit
- [ ] Tokens `--delpi-ui-*` mapeados (+ dark scoped)
- [ ] **Zero** seletor CSS de componente do kit no MFE (Fase 7) — só tokens + layout de página
- [ ] Sem cópia local / markup inline de KPI, Pagination, DataTable, EmptyState quando o kit cobre
- [ ] `npm run build` verde
- [ ] Smoke visual claro + escuro no portal federado
- [ ] Docker/MF ok (se aplicável)
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
| 0.5 | Script opcional: detectar `HelpTooltip.tsx` local (`scripts/ci/audit_plugin_ui_duplication.py`) | CI ✅ |

### Fase 1 — Família `help` (quick win, ~2–3 sprints)

**Meta:** 13 plugins migrados; ~3.800 LOC removidas.

| Lote | Plugins | Ordem |
|------|---------|-------|
| 1a Piloto | `dashboard-production` | Referência departamental + mais maduro |
| 1b Dashboards clone | `commercial`, `engineering`, `financial`, `hr`, `lmps`, `quality`, `supplies` | Copiar checklist do piloto; PRs em paralelo (1 plugin = 1 PR) |
| 1c Domínio | `transformometro`, `cadastro-kaizen`, `quality-action-plans` | Atenção a `FieldLabel`/`TitleWithHelp` |
| 1d Simplificados | `eficiencia-fabril`, `maintenance` | Ganho a11y (portal/viewport vs CSS puro) |
| 1e Portal | `portal` | Só após 0.3 — API controlada |

**Checklist por plugin (Fase 1 — histórico; integração atual = MF):**

Ver [novo-plugin-mfe-checklist.md](../../docs/05-plugin-system/novo-plugin-mfe-checklist.md). Resumo da migração de componentes:

```ts
import { HelpTooltip, FieldLabel } from "@delpi/plugin-ui/index";
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
| `SectionCard` | PAC + kaizen | ✅ F3.2 |
| `EmptyState` / `LoadingState` | controle-retrabalhos, financeiro-centro-custo | ✅ F3.7 |
| `EditableTableCell` / `NativeSelectControl` | maintenance, PAC, kaizen | ✅ F3.8 |
| Forms residual (a5s / QL / CA Native*) | auditoria-5s, quality-labels, central-agendamento | ✅ F3.8 |
| `BookingModal` Native* + `datetime-local` | central-agendamento | ✅ F3.9 |
| Maintenance Native* (`dmFormFields` + `afterControl`) | Configuração, MiniAplicadores, revisão programada | ✅ F3.10 |
| Native* `onBlur`/`readOnly`/`max` + TV + Transformômetro | tv-dashboard deck/BranchField; ProcessoFormFields | ✅ F3.11 |

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
| `ConfirmModalPanel` | ✅ F5.4 | Headless; `ModalShell` + wrapper fino |
| `ModalShell` | ✅ F5.5 | PAC + transformometro |
| `Modal` base | ⏳ | Variantes SI/drawer fora de escopo |

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
| `transformometro` | ✅ | ChartCard ✅ Pagination ✅ MultiSelect ✅ KpiCard ✅ DataTable ✅ | EditableSectionCard ✅ PageHeader ✅ ProcessoForm Native* ✅ | sim |
| `cadastro-kaizen` | ✅ | FiltersRow ✅ MultiSelect ✅ DataTable ✅ KpiCard ✅ | Forms ✅ SectionCard ✅ EditableSectionCard ✅ PageHeader ✅ StateBanner ✅ | sim |
| `quality-action-plans` | ✅ | FiltersRow ✅ MultiSelect ✅ ChartCard ✅ KpiCard ✅ | PageHeader ✅ SectionCard ✅ | sim |
| `eficiencia-fabril` | ✅ | ChartCard ✅ KpiCard ✅ LoadingActivity ✅ MultiSelect ✅ FilterBarShell ✅ | DetailFieldGrid ✅ | sim |
| `maintenance` | ✅ | Pagination ✅ MultiSelect ✅ FilterBarShell ✅ DataTable ✅ | PageHeader ✅ · EditableCell ✅ · Native* forms ✅ | sim |
| `controle-retrabalhos` | — | Kpi/Chart ✅ LoadingActivity ✅ FilterBarShell ✅ CompactPagination ✅ | PageHeader ✅ Empty/Loading ✅ | sim |
| `inspecoes-entrada` | — | Pagination ✅ KpiCard ✅ FilterBarShell ✅ | PageHeader ✅ | sim |
| `inspecoes-entrada` | — | Kpi/Pagination ✅ | PageHeader | sim |
| `financeiro-centro-custo` | — | ChartCard ✅ KpiCard ✅ FilterBarShell ✅ CompactPagination ✅ | PageHeader ✅ Empty/Loading ✅ | sim |
| `pedidos-venda-abertos` | — | Pagination ✅ KpiCard ✅ MultiSelect ✅ FilterBarShell ✅ | PageHeader | sim |
| `auditoria-5s` | — | ChartCard ✅ KpiCard ✅ FilterBarShell ✅ | AuditHeaderForm Native* ✅ | sim |
| `quality-labels` | — | — | CertificateFormFields + Admin form Native* ✅ | sim |
| `central-agendamento` | — | — | ResourceFormModal + BookingModal Native* ✅ | sim |
| `tv-dashboard` | ✅ | — | BranchField / Deck / AddSlide / NewPlaylist Native* ✅ | sim |
| `portal` | ❌ fora de escopo | — | — | N/A (shell) |

---

## 5. Riscos e mitigação

| Risco | Mitigação |
|-------|-----------|
| Regressão visual (tema escuro) | Validar no portal federado; tokens `--delpi-ui-*` |
| Build Docker quebra | Gate CI `check_plugin_docker_shared_libraries.py`; `pluginUiRemote()` no vite |
| `KpiCard`/tabela muito acoplados ao prefixo CSS | Props `className` granulares; não mover CSS de marca para o pacote |
| `eficiencia-fabril`/`maintenance` perdem tooltip CSS-only | Migração = melhoria a11y (portal + teclado) |
| PRs grandes | **1 plugin = 1 PR** na Fase 1; Fase 2 componente a componente |
| Portal API `open` controlado | Estender pacote (Fase 0.3) antes de migrar portal |

---

## 6. Métricas de sucesso

| Métrica | Hoje (pós F1–F6) | Meta pós-F7 |
|---------|------------------|-------------|
| Arquivos `HelpTooltip.tsx` locais | 1 (portal) | 0 nos plugins |
| Plugins consumindo `@delpi/plugin-ui` | 27 (MF) | 27+ |
| MFEs com CSS `.delpi-ui-*` / espelho BEM de kit | ~28 (auditoria) | 0 |
| Cópias Pagination/DataTable/EmptyState fora do kit | várias (IP, SI, chat admin) | 0 |
| Gate CI anti-reintrodução CSS kit no MFE | — | ⏳ 7.7 |

---

## 7. Status (jul/2026) — concluído × residual

### Concluído (núcleo)

| Frente | Escopo |
|--------|--------|
| **F1** Help | Plugins MFE; portal permanece local |
| **F2** Shell dashboard | Kpi/Chart/Loading/Pagination/Filter/MultiSelect/DataTable nos dept. |
| **F3** Forms/detalhe | F3.1–F3.13 (Native* + `beforeControl`, a5s NC, TV ribbon, TM revisão, CE FormsPanel, chat admin) |
| **F4** Utils | paginationPages, chartColors, operationalUnitLabels, goalDisplay |
| **F5** (parcial) | FileDropzone (+ policy workspace), ModalShell, **DrawerShell**, confirm controller; CE/SI/chat forms migrados |
| **MF runtime** | 27 MFEs + `public-hub`; `delpi-plugin-ui`; sem `COPY plugin-ui` nos consumidores |
| **Export E1–E3** | Motor tabular, PDF DELPI, botões, jsPDF, PNG chart, matrix, PVA — [export-catalog.md](./export-catalog.md) |

### Residual — avaliar demanda (não bloqueia produção)

| Prioridade ROI | Item | Notas |
|----------------|------|--------|
| **Ativa — Fase 7** | Zero CSS de componente do kit nos MFEs | § 8 · [migration-catalog.md](./migration-catalog.md) § Fase 7 |
| Baixa | Varredura CI `<select>`/`textarea` | ✅ concluída — 0 nativos nos MFE; gate `audit_plugin_ui_native_form_controls.py --check` |
| Backlog E4 | CSV Excel-aware (drawing) | Só se 2+ consumidores |
| Fora | **portal** HelpTooltip / shell | Explícito fora de escopo |

### Concluído nesta onda (jul/2026)

| Plugin | Entrega |
|--------|---------|
| **auditoria-5s** | `AuditNcItemCard` + observação critério → `AuditNative*` + `beforeControl` |
| **tv-dashboard** | `ComunicadoFormatRibbon` + `DataBindingInspector` → `TdRibbonSelect` / `NativeSelectControl` |
| **transformometro** | Textareas revisão/instância → `TmNativeTextAreaField` |
| **customer-experience** | `cxFormFields`, FormsPanel builder, `PhotoDropzone` empty → `FileDropzone` |
| **strategic-indicators** | `Modal` + `DrawerPanel` → `ModalShell` / `DrawerShell` |
| **minha-delpi-chat** | Composer, edição, canvas, shortcut → `ChatNativeTextAreaControl`; admin/workspace → `chatAdminFormFields` |
| **cultura-delpi** | Admin cultura → `CulturaNativeTextAreaControl` + Docker context `../plugins` |
| **propostas-comerciais** | Tabela/modal PDF → `PcNativeTextAreaControl` |
| **tv-dashboard** | Comunicado inline → `TdNativeTextAreaControl` |
| **plugin-ui** | `ToolbarSelectField` — select compacto de toolbar (CSS em `styles.css`) |

### Próximo lote sugerido (quando retomar)

1. ~~Consolidar estilos `SelectControl` compacto no `plugin-ui`~~ ✅ `ToolbarSelectField` / `ToolbarSelectControl`
2. **Fase 7 — zero CSS de componente do kit no MFE** → § 8 (auditoria jul/2026). **Implementar só após** tracking neste doc + [migration-catalog.md](./migration-catalog.md).
3. **api-delpi-console** — ainda não consome `@delpi/plugin-ui` (avaliar). **public-hub** — MF para plugin-ui; bundled só `tv-dashboard-presentation`.

---

## 8. Fase 7 — Zero CSS de componente do kit no MFE (jul/2026)

> **Status:** em execução · ondas 7.1+ · **Não iniciar implementação** sem marcar ondas abaixo e atualizar [migration-catalog.md](./migration-catalog.md) § Fase 7.  
> **Regra:** Cursor `plugins-reusable-components.mdc` — se a UI vem do kit, **zero CSS** no MFE (hipótese alguma).  
> **Auditoria:** varredura monorepo jul/2026 (~28 plugins com violação CSS e/ou TSX).

### 8.1 Tipos de violação

| Tipo | Exemplos | Ação canônica |
|------|----------|---------------|
| **A — Override `.delpi-ui-*`** | `tv-dashboard` format-pane/ribbon; PAC help-tooltip no modal; CR `margin` em filter-bar/loading | Mover utilitário ao kit **ou** apagar; layout via tokens/página |
| **B — Espelho BEM dual-class** | `.pac-ghost-btn`, `.kz-section-card*`, `.dm-state-box`, `.fi-kpi-*`, tabela th/td | Remover CSS do MFE; garantir CSS no kit + dual-class |
| **C — Cópia TSX / markup inline** | `inspecoes-processo` Pagination/EmptyState; SI DataTable; chat AdminKpi/DataTable; KPI/paginação inline (a5s, EF, maintenance) | Thin wrapper / factory do kit; apagar cópia |
| **D — Dual-class incompleto** | `filtersUi` IE/PVA/a5s sem `filtersRowBemClasses`; kaizen `dataTableUi` override remove `delpi-ui-*` | Restaurar `*BemClasses` sem override que apague o par |

### 8.2 Inventário P0 / P1 / P2

#### P0 — críticos (muitos `.delpi-ui-*` ou chrome massivo)

| Plugin | Violações típicas | Onda sugerida |
|--------|-------------------|---------------|
| `tv-dashboard` | ~96 seletores `.delpi-ui-*` (format-pane, ribbon, catalog, help-tooltip) → ✅ onda 7.1 | **7.1** |
| `quality-action-plans` | ghost, state-box, section-card header, table modal, help-tooltip | **7.2** |
| `minha-delpi-chat` | Admin KPI/filter/table/pagination local + CSS; overrides toolbar/checkbox | **7.3** (avaliar: migrar ao kit **ou** renomear DS admin como domínio fora do dual-class) |
| `tv-dashboard-presentation` | config-table, series-chart-shell, kpi-card TV → ✅ onda 7.1 | **7.1** (junto TV) |

#### P1 — espelho BEM / cópia nomeada

| Plugin | Violações típicas | Onda sugerida |
|--------|-------------------|---------------|
| `cadastro-kaizen` | `.kz-section-card*`; `dataTableUi` dual incompleto | **7.4** |
| `auditoria-5s` | table/filters CSS; KPI/paginação **inline** | **7.4** |
| `maintenance` | StateBox local + DataTable.css + KPI inline | **7.4** |
| `transformometro` | ghost, table-section, tree-guides/help print | **7.4** |
| `financeiro-inadimplencia` | CSS/markup `fi-kpi-*` | **7.4** |
| `inspecoes-processo` | Pagination + EmptyState **cópia local** | **7.5** |
| `strategic-indicators` | DataTable **cópia local** | **7.5** |

#### P2 — família dashboard + parciais

| Plugin / grupo | Violações típicas | Onda sugerida |
|----------------|-------------------|---------------|
| `dashboard-{production,commercial,quality,financial,hr,engineering,supplies,lmps}` | state-box, table mobile, print, ghost | **7.6** |
| `scrap-monitoring`, `production-appointments`, `inspecoes-entrada`, `pedidos-venda-abertos`, `eficiencia-fabril`, `propostas-comerciais`, financeiros | filters/state-box/pagination CSS; filtersUi MEDIUM | **7.6** |
| `controle-retrabalhos` | residual `.delpi-ui-filter-bar` / loading margin; `.cr-card:not(.delpi-ui-card)` | **7.2** (junto PAC — quick win) |

#### Limpos (referência — sem chrome das patterns)

`canal-denuncia`, `codigo-etica`, `cultura-delpi`, `quality-labels` (+ `public-hub` sem CSS relevante).

### 8.3 Ondas de execução (plano — ⏳)

| Onda | Escopo | DoD mínimo | Status |
|------|--------|------------|--------|
| **7.0** | Doc + regra Cursor (este § + migration-catalog + `plugins-reusable-components.mdc`) | Regra absoluta publicada | ✅ |
| **7.1** | `tv-dashboard` + `tv-dashboard-presentation` — zerar/mover overrides `.delpi-ui-*` | 0 seletores `.delpi-ui-*` em CSS do MFE (exceto justificativa doc) | ✅ `data-delpi-ui-density="compact"` + `host-density-compact.css` / `format-pane--compact` / `--fill` |
| **7.2** | `quality-action-plans` + `controle-retrabalhos` | 0 chrome espelho; tokens+layout only | ⏳ |
| **7.3** | `minha-delpi-chat` admin UI — decisão kit vs domínio renomeado | Sem classes que fingem dual-class do shell dashboard **ou** migrado ao kit | ⏳ |
| **7.4** | kaizen, a5s, maintenance, transformometro, financeiro-inadimplencia | Sem espelho BEM; inline → factory | ⏳ |
| **7.5** | `inspecoes-processo` Pagination/EmptyState; SI DataTable | Thin wrappers / kit | ⏳ |
| **7.6** | Família `dashboard-*` + MFEs P2 (filters/state-box/table mobile) | Padrão dept. alinhado a CR/tokens | ⏳ |
| **7.7** | Gate CI opcional (`audit` seletores `.delpi-ui-` / BEM espelho em `plugins/*/src/**/*.css`) | Falha CI se reintroduzir | ⏳ backlog |

### 8.4 Ordem operacional por PR

1. **1 onda = 1+ PRs** (preferir 1 plugin crítico por PR em 7.1–7.5).
2. Se o gap visual for no kit → alterar `plugins/plugin-ui/src/styles/` **primeiro**, rebuild remote (`up-*-sequential.sh --fase remote --build plugin-ui`), depois MFE.
3. Não “voltar” CSS podado no MFE.
4. Atualizar checkbox da onda em [migration-catalog.md](./migration-catalog.md) § Fase 7 ao concluir.

### 8.5 Fora de Fase 7 (não confundir)

| Item | Nota |
|------|------|
| UI 100% domínio (fishbone PAC, presentation SI PanZoom, …) | CSS no MFE **ok** se **não** for export/dual-class do kit |
| `@media print` hide de help-tooltip | Preferir utilitário no kit (onda 7.1/7.6); não deixar seletor `.delpi-ui-*` permanente no MFE |
| Admin chat se permanecer domínio | Renomear classes para **não** parecer shell KPI/filter do kit |

---

## Referências

- [component-catalog.md](./component-catalog.md) — API atual
- [migration-catalog.md](./migration-catalog.md) — tracking por plugin + **Fase 7**
- [architecture.md](./architecture.md) — tokens, CSS canônico vs MFE, Vite, Docker
- [contributing.md](./contributing.md) — critérios para novo componente
- [plugins-reusable-components.mdc](../../../.cursor/rules/plugins-reusable-components.mdc) — **zero CSS do kit no MFE**
- [plugins-visual-design-system.mdc](../../../.cursor/rules/plugins-visual-design-system.mdc)
