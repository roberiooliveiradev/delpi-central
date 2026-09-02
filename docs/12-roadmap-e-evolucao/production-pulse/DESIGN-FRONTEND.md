# Design frontend — Production Pulse

> **Plugin:** `production-pulse` · **Root CSS:** `.dashboard-production-pulse` · **Prefixo BEM:** `pp-`  
> **Kit:** `@delpi/plugin-ui/index` via Module Federation · **Ícones:** `lucide-react`  
> **Wireframes (estrutura):** [WIREFRAMES.md](./WIREFRAMES.md) · **Visuais e cores:** [VISUAL-WIREFRAMES-AND-COLORS.md](./VISUAL-WIREFRAMES-AND-COLORS.md)

---

## 1. Identidade visual

Pulso de Produção é **monitoramento IoT industrial**: dispositivos na rede, leituras ao vivo (golpes, rpm, °C) e amarração a **postos, máquinas ou equipamentos**. Tom **industrial limpo** — vocabulário visual dos dashboards Delpi (Production, Maintenance).

### 1.1 Cores (tokens locais)

> **Mapa visual por tela/componente:** [VISUAL-WIREFRAMES-AND-COLORS.md](./VISUAL-WIREFRAMES-AND-COLORS.md)

Mapeamento em `.dashboard-production-pulse` → `--delpi-ui-*` (kit). **Não** hardcode `#fff` / `#000` em componentes.

| Token `--pp-*` | Fallback / origem | Uso |
|----------------|-------------------|-----|
| `--pp-accent` | `var(--primary, #089bdb)` | Ações primárias, links, foco |
| `--pp-accent-soft` | `color-mix(in srgb, var(--pp-accent) 12%, transparent)` | Fundo ícone KPI, hover suave |
| `--pp-title` | `var(--secundary, #003866)` | Títulos de seção |
| `--pp-text` | `var(--text, #111111)` | Texto principal |
| `--pp-text-muted` | `var(--text-muted, rgba(17,17,17,0.7))` | Meta, timestamps |
| `--pp-surface` | `var(--surface, #ffffff)` | Cards |
| `--pp-border` | `var(--border, #e6e6e6)` | Bordas |
| `--pp-canvas` | `var(--app-canvas, var(--bg))` | Fundo página |
| `--pp-success` | `var(--success, #15803d)` | **Online**, poll OK |
| `--pp-danger` | `var(--danger, #b42318)` | **Offline**, erro hardware |
| `--pp-warning` | `var(--warning, #b45309)` | Sem binding, stale |
| `--pp-info` | `var(--pp-accent)` | Informativo neutro |

**Dark mode:** bloco `:root[data-theme="dark"] .dashboard-production-pulse { … }` — sobrescrever `--pp-surface`, `--pp-text`, `--pp-border` mapeando vars do portal (padrão `maintenance` / `controle-retrabalhos`).

### 1.2 Semântica de status (badges)

| Estado | Cor | Condição (API) | Label UI |
|--------|-----|----------------|----------|
| `online` | `--pp-success` | `status === "online"` | Online |
| `offline` | `--pp-danger` | `status === "offline"` | Offline |
| `no_binding` | `--pp-warning` | sem binding vigente | Sem amarração |
| `disabled` | `--pp-text-muted` | `enabled === false` | Desativado |

Kit: `StatusBadge` via `createDashboardStatusBadge({ prefix: "pp" })`.

### 1.3 Tipografia e densidade

| Token | Valor | Uso |
|-------|-------|-----|
| `--pp-font-xs` | 12px | Meta, timestamp |
| `--pp-font-sm` | 13px | Tabela, labels |
| `--pp-font-md` | 14px | Corpo |
| `--pp-font-hero` | `clamp(24px, 2vw, 36px)` | Título PageHero |
| `--pp-font-kpi` | `clamp(22px, 2vw, 30px)` | Valor KPI contador |
| `--pp-page-padding` | 24px (16px mobile) | Padding página |
| `--pp-section-gap` | 20px | Entre seções |
| `--pp-grid-gap` | 16px | Grid KPI / cards |
| `--pp-card-radius` | 18px | Cards |
| `--pp-card-padding` | 20px | Interior card |

### 1.4 Badges `anchor_type` (`AnchorTypeBadge`)

Componente domínio `.pp-anchor-badge` — pill compacto ao lado de `placement_label`.

| `anchor_type` | Label PT | Cor fundo | Ícone |
|---------------|----------|-----------|-------|
| `work_center` | Posto | `color-mix(accent 15%)` | `Factory` |
| `machine` | Máquina | `color-mix(title 12%)` | `Cog` |
| `equipment` | Equipamento | `color-mix(success 12%)` | `Fan` |
| `area` | Área | `color-mix(warning 12%)` | `MapPin` |
| `standalone` | Avulso | muted | `Radio` |

### 1.5 Form — segmented `anchor_type`

`.pp-anchor-segmented` — radio group pill, min-height **44px** touch:

```text
[ Posto PCP ] [ Máquina ] [ Equipamento ] [ Área ] [ Avulso ]
     Factory      Cog         Fan          MapPin    Radio
```

Estado ativo: borda `--pp-accent`, fundo `--pp-accent-soft`. Campos condicionais abaixo animam height (reduced-motion safe).

Bloco **«Vincular ao TOTVS (opcional)»** — `<details>` fechado por default se tipo ≠ `work_center`.

### 1.6 Fundo da página

```css
.dashboard-production-pulse.dashboard-page {
  background-color: var(--pp-canvas);
  background-image: linear-gradient(
    180deg,
    color-mix(in srgb, var(--pp-accent) 5%, var(--pp-canvas)),
    var(--pp-canvas) 280px
  );
}
```

Gradiente **sutil** 5% accent — zero CSS de componente do kit no MFE.

---

## 2. Ícones (lucide-react)

| Contexto | Ícone | Tamanho |
|----------|-------|---------|
| App / menu manifest | `Activity` ou `Radio` | manifest |
| PageHero | `Activity` | 28, stroke 1.75 |
| KPI total devices | `Cpu` | 22 |
| KPI online | `Wifi` | 22 |
| KPI offline | `WifiOff` | 22 |
| KPI sem amarração | `Link2Off` | 22 |
| Novo dispositivo | `Plus` | 16 |
| Atualizar / poll | `RefreshCw` | 16 |
| Centro de trabalho | `Factory` | 16 |
| Máquina (anchor) | `Cog` | 16 |
| Equipamento (anchor) | `Fan` | 16 |
| Área (anchor) | `MapPin` | 16 |
| Sensor / gauge | `Gauge` | 16 |
| Temperatura | `Thermometer` | 16 |
| Detalhe / histórico | `LineChart` | 16 |
| Reset contador | `RotateCcw` | 16 |
| Testar conexão | `PlugZap` | 16 |
| Voltar | `ArrowLeft` | 16 |

---

## 3. Inventário `@delpi/plugin-ui` (MVP)

Import: `from "@delpi/plugin-ui/index"`. Factory com prefixo `pp` onde existir helper `createDashboard*`.

### 3.1 Layout e navegação

| Componente | Uso no Production Pulse |
|------------|-------------------------|
| `PageHero` | Cabeçalho de todas as páginas (`density="compact"`) |
| `BackLink` | Voltar do formulário/detalhe → painel |
| `UnderlineNav` | Abas no detalhe do device (Visão geral · Histórico · Comandos) |
| `ScopeChipBar` | **Fora MVP** — usar `FilialSwitcher` (padrão maintenance) |

### 3.2 Ações

| Componente | Uso |
|------------|-----|
| `ActionButton` | `primary` Salvar · `ghost` Atualizar · `link` Ver detalhe |
| `IconButton` | Poll row · menu contextual linha |

### 3.3 KPI e feedback

| Componente | Uso |
|------------|-----|
| `SimpleKpiCard` | Strip 4 KPIs no painel (`createDashboard` ou layout iconStart) |
| `StatusBadge` | Online / offline / sem CT |
| `EmptyState` | Nenhum device na filial |
| `EmptyGuidance` | Filial sem devices + CTA cadastrar |
| `ScreenLoading` | Carregamento inicial painel |
| `InlineLoadingProgress` | Poll row / refresh strip |
| `StateBox` | Erro API / permissão |

### 3.4 Filtros e formulário

| Componente | Uso |
|------------|-----|
| `FiltersRow` + `FilterInputField` + `FilterSelectField` | Barra filtros painel |
| `FieldLabel` | Todos os campos (help hover) |
| `TextField` | Nome, IP, rótulos máquina/equipamento |
| `SelectField` | Filial, driver, CT (search async) |
| `TextAreaField` | Observações binding |

### 3.5 Tabelas e dados

| Componente | Uso |
|------------|-----|
| `DataTable` / `DataTableSection` | Lista devices · histórico readings · log comandos |
| `CompactPagination` | Paginação server-side |
| `ConfigurableSeriesChart` ou `ChartCard` + Recharts | Gráfico deltas no detalhe |

### 3.6 Modais

| Componente | Uso |
|------------|-----|
| `ModalShell` | Confirmar reset · resultado teste conexão · desativar device |

**Modal host-contained** (`mfe-modal-host-contained.mdc`): `containInHost={true}` default.

### 3.7 Helps e explicações

**Catálogo:** [`docs/.../content/helpTooltips.ts`](./content/helpTooltips.ts) → `plugins/production-pulse/src/content/helpTooltips.ts`  
**Mapa completo:** [HELP-CONTENT.md](./HELP-CONTENT.md)

| Componente MFE | Kit | Chaves `PP_HELP` |
|----------------|-----|------------------|
| `ProductionPulsePageHero` | `PageHero` | `shell.heroTitle`, `shell.heroFilial`, `shell.pollAll`, `shell.modeOperator` |
| `DeviceKpiStrip` | `SimpleKpiCard` | `panel.kpiTotal`, `kpiOnline`, `kpiOffline`, `kpiWithoutBinding` |
| `DeviceFiltersBar` | `FiltersRow` + selects | `panel.filterAnchorType`, `filterRole`, `filterStatus`, `filterSearch`, `filterGroupBy`, `viewList`, `viewGrouped` |
| `DeviceTable` | `DataTableSection` | `panel.colName` … `colLastSeen`, `rowPoll`, `rowReset` |
| `DeviceGroupedByPlacement` | layout MFE | cabeçalho + `badges.anchor*` |
| `DeviceForm` | `SectionCard` + fields | `form.sectionDevice`, campos `form.name` … `form.enabled`, `form.testConnection` |
| `DeviceBindingSection` | segmented + fields | `form.sectionPlacement`, `form.anchorType`, `form.anchor*`, `form.sectionTotvs`, `workCenterOptional` … |
| `DeviceDetailPage` | `UnderlineNav` + tabs | `detail.tabOverview`, `tabHistory`, `tabCommands` |
| `DeviceOverviewTab` | KPI + cards | `detail.liveMetrics`, `bindingCard`, `pollNow`, `resetCounter`, `deactivate` |
| `DeviceHistoryTab` | `ChartCard` + table | `detail.chartDelta`, `chartSeries`, `readingsTable`, `delta` |
| `DeviceCommandsTab` | `DataTableSection` | `detail.commandsTable` |
| Modais reset/teste/desativar | `ModalShell` | `modals.reset*`, `clearOperator*`, `testOk`, `testFail`, `deactivate*` |
| `OperatorPlacementHub` | cards touch | `operator.hubTitle`, `hubFilter*`, `hubSearch`, `hubCardMeta` |
| `OperatorDevicePicker` | cards + badges | `operator.pickerTitle`, `pickerBadgeCounter`, `pickerBadgeSensor` |
| `OperatorCounterPad` | botões grandes | `operator.statusBar`, `counterValue`, `counterIncrement/Decrement/Clear` |
| `OperatorGaugeReadout` | readout | `operator.gaugeValue`, `gaugeRefresh`, `offlineBanner` |
| `AnchorTypeBadge` | badge domínio | `badges.anchorWorkCenter` … `anchorStandalone` |
| `DeviceStatusBadge` / role pills | badge domínio | `badges.status*`, `badges.role*` |

**Padrão de uso:**

```tsx
import { PP_HELP, getPpHelp } from "../content/helpTooltips";

<FieldLabel label="Endereço IP" hint={PP_HELP.form.ip} />
<SectionHintLabel hint={PP_HELP.form.sectionDevice}>Dispositivo IoT</SectionHintLabel>
```

**Copy visível** (prosa abaixo do título de seção, além do `?`): ver [HELP-CONTENT § textos de seção](./HELP-CONTENT.md#textos-de-seção-copy-visível-não-só-tooltip). Opcional P1: `sectionIntros.ts` ao lado do catálogo.

**Proibido:** textos PT hardcoded no componente; `HelpTooltip.tsx` local; paths API ou IPs fixos nos helps.

Referência de padrão: `plugins/maintenance/src/content/helpTooltips.ts` (`DM_HELP`).

### 3.8 O que **não** criar no MFE

- Cópia de KPI card, tabela, filter bar, modal, badge — zero CSS `.delpi-ui-*` local
- `HelpTooltip.tsx` local
- Motor de chart paralelo — Recharts dentro do shell do kit

### 3.9 Lacunas / extensões futuras no kit (P2)

| Necessidade | MVP | P2 |
|-------------|-----|-----|
| Tabela agrupada por CT (accordion) | Layout MFE: seções colapsáveis por CT | `GroupedDataTable` no kit se 2º consumidor |
| Sparkline inline na linha | Opcional P1 — `CompareSparkline` se couber | — |
| Indicador pulse animado online | CSS domínio `.pp-pulse-dot` (não kit) | — |

---

## 4. Estrutura de arquivos MFE (planejada)

```text
plugins/production-pulse/
├── production-pulse.manifest.json
├── src/
│   ├── bootstrap.tsx
│   ├── App.tsx
│   ├── index.css                    # só tokens + layout página
│   ├── constants/routes.ts
│   ├── content/helpTooltips.ts
│   ├── content/sectionIntros.ts
│   ├── api/productionPulseApi.ts
│   ├── app/
│   │   ├── productionPulseUi.ts     # factories kit (pp prefix)
│   │   └── routeParser.ts
│   ├── hooks/
│   │   ├── useDevices.ts
│   │   ├── useDeviceDetail.ts
│   │   ├── useSummary.ts
│   │   └── useUrlFilters.ts
│   ├── components/
│   │   ├── ProductionPulseShell.tsx
│   │   ├── ProductionPulsePageHero.tsx
│   │   ├── FilialSwitcher.tsx       # ou reexport padrão maintenance-like
│   │   ├── DeviceStatusBadge.tsx    # thin wrapper StatusBadge
│   │   ├── DeviceKpiStrip.tsx
│   │   ├── DeviceFiltersBar.tsx
│   │   ├── DeviceTable.tsx
│   │   ├── DeviceGroupedByPlacement.tsx
│   │   ├── AnchorTypeBadge.tsx
│   │   ├── AnchorTypeSegmented.tsx
│   │   ├── DeviceForm.tsx
│   │   ├── DeviceBindingSection.tsx
│   │   ├── DeviceReadingsChart.tsx
│   │   ├── DeviceReadingsTable.tsx
│   │   ├── DeviceCommandsTable.tsx
│   │   ├── operator/
│   │   │   ├── OperatorPlacementHub.tsx
│   │   │   ├── OperatorDevicePicker.tsx
│   │   │   ├── OperatorDeviceSurface.tsx
│   │   │   ├── OperatorBrandBar.tsx
│   │   │   ├── OperatorCounterStage.tsx
│   │   │   ├── OperatorGaugeStage.tsx
│   │   │   ├── OperatorActionPad.tsx
│   │   │   └── OperatorStatusBar.tsx
│   │   └── modals/
│   │       ├── ResetCounterModal.tsx
│   │       ├── OperatorClearConfirmModal.tsx
│   │       └── TestConnectionModal.tsx
│   └── pages/
│       ├── PanelPage.tsx            # WF-PP-01
│       ├── DeviceFormPage.tsx       # WF-PP-02 create/edit
│       ├── DeviceDetailPage.tsx     # WF-PP-03 tabs
│       └── OperatorPage.tsx         # WF-PP-OP — tela operador
```

---

## 5. Navegação e URL (P0)

Sync query ↔ estado (`replaceState`). Parser em `routeParser.ts`.

| Rota | Query params |
|------|----------------|
| `/apps/production-pulse` | `branch`, `anchorType`, `workCenter`, `role`, `status`, `search`, `view`, `groupBy`, `page` |
| `/apps/production-pulse/devices/new` | `branch` |
| `/apps/production-pulse/devices/:id` | `tab` (`overview`\|`history`\|`commands`) |
| `/apps/production-pulse/devices/:id/edit` | — |
| `/apps/production-pulse/operator` | `branch`, `anchorType`, `search` |
| `/apps/production-pulse/operator/placements/:placementKey` | — |
| `/apps/production-pulse/operator/devices/:deviceId` | — |

**Deep link:** copiar URL do painel com filtros; link de detalhe com aba Histórico.

---

## 6. Permissões na UI

Matriz API: [ADR-003-rbac-mvp.md](./ADR-003-rbac-mvp.md).

| Elemento | Permissão |
|----------|-----------|
| Ver painel / detalhe | `production-pulse.devices.view` + filial |
| **Tela operador** (hub, picker, superfície) | `production-pulse.operator` + filial |
| Botões − / + / Limpar **na rota operador** | `production-pulse.operator` |
| Botões comando **no painel admin** | `devices.command` ou `devices.manage` |
| `[Novo dispositivo]` | `production-pulse.devices.manage` |
| Editar / form salvar | `devices.manage` |
| `[Testar conexão]` | `devices.manage` → `POST /devices/test-probe` (novo) ou `POST .../test` (edit) |
| `[Reset contador]` admin | `devices.command` ou `devices.manage` |
| `[Poll all]` strip | `devices.manage` |
| Filial no hero | **`FilialSwitcher`** · permissão `view.filial-01` / `02` ou `admin` |

Elementos sem permissão: **ocultos** (não disabled confuso).

---

## 7. Responsividade

Referência visual: [WIREFRAMES.md](./WIREFRAMES.md) — cada tela tem subseções **`tablet (769–1100px)`** e **`mobile (≤768px)`** com ASCII.

### Breakpoints globais

| Breakpoint | Comportamento |
|------------|---------------|
| `> 1100px` | KPI 4 colunas; tabela completa; gráfico ao lado do resumo no detalhe |
| **`769px – 1100px`** | **Tablet** — ver tabela por tela abaixo |
| **`≤ 768px`** | **Mobile admin** — cards, sticky footer, hero coluna |
| **`≤ 600px`** | **Operador narrow** — hub/picker 1 col; pad contador empilhado |

### Por tela (admin tablet `769–1100px`)

| Tela / rota | Layout tablet | Componentes / classes |
|-------------|---------------|------------------------|
| **Shell** WF-PP-00 | Hero wrap; filial 2ª linha se `<900px` | `ProductionPulsePageHero` flex-wrap |
| **Painel** WF-PP-01 | KPI **2×2**; filtros 2 linhas; **DataTable** compacta | `.pp-kpi-strip--tablet`, `.pp-device-table--compact` |
| **Painel 769–900** | Ocultar colunas «Papel»/«Última»; scroll-x fallback | `hiddenBelowTablet` columns |
| **Form** WF-PP-02 | 1 col `max-width: 720px`; segmented wrap | `.pp-form--tablet` |
| **Detalhe** WF-PP-03 | Overview 2 col ≥901px; 1 col 769–900; tabela histórico scroll-x | `.pp-detail-grid--tablet` |
| **Modais** WF-PP-04 | `min(520px, 100% - 48px)`; botões row | `ModalShell` |

### Por tela (operador tablet `769–1100px`)

| Tela | Portrait 769–900 | Landscape 901–1100 |
|------|------------------|---------------------|
| **Hub** | Grid **2 col** | Grid **3 col** |
| **Picker** | 2 col | 2–3 col |
| **Contador** | OP-01 se ≥600px wide; senão OP-02 | OP-01 pad 3 col, botões 112px |
| **Gauge** | 1 col métricas | 2 col métricas |

### Por tela (admin mobile `≤768px`)

| Tela / rota | Layout mobile | Componentes / classes |
|-------------|---------------|------------------------|
| **Shell** WF-PP-00 | Hero coluna; filial abaixo do título | `ProductionPulsePageHero` stack |
| **Painel** WF-PP-01 | KPI 1 col; filtros → sheet «Filtros»; tabela → **DeviceCard** | `.pp-device-card`, `.pp-device-card-list` |
| **Painel agrupado** | Acordeões full width; mini-cards dentro do grupo | `.pp-placement-group` |
| **Form** WF-PP-02 | Sections stack; segmented **vertical**; sticky footer | `.pp-form-footer`, `.pp-anchor-segmented--stack` |
| **Detalhe** WF-PP-03 | Hero stack; abas scroll horizontal; overview 1 col | `.pp-detail-hero`, `.pp-reading-card` |
| **Histórico** | Filtros stack; gráfico altura ~180px mobile; leituras → cards | `.pp-reading-card` |
| **Comandos** | Audit cards empilhados | `.pp-command-card` |
| **Modais** WF-PP-04 | Largura `calc(100% - 32px)`; botões column `<360px` | `ModalShell` host-contained |

### Por tela (operador)

| Tela | `≤768px` | `≤600px` |
|------|----------|----------|
| **Hub** | Chips filtro scroll horizontal; cards 2 col possível landscape | Cards **1 col** full width; min-h 96px |
| **Picker** | Device cards stack | Idem |
| **Contador** | Pad 3 col se ≥600px landscape | **+** full width; − e Limpar 50/50 (WF-PP-OP-02) |
| **Gauge** | Métricas stack; valor `clamp(2.5rem, 18vw, 4rem)` | Idem |

### CSS responsivo (planejado — `index.css`)

```css
/* Tablet admin */
@media (min-width: 769px) and (max-width: 1100px) {
  .dashboard-production-pulse {
    --pp-page-padding: 20px;
  }
  .pp-kpi-strip {
    grid-template-columns: repeat(2, 1fr);
  }
  .pp-form-page__inner {
    max-width: 720px;
    margin-inline: auto;
  }
  .pp-detail-overview {
    display: grid;
    grid-template-columns: 1fr;
    gap: 16px;
  }
}
@media (min-width: 901px) and (max-width: 1100px) {
  .pp-detail-overview {
    grid-template-columns: 1fr 1fr;
  }
  .pp-detail-overview__chart {
    grid-column: 1 / -1;
  }
  .pp-device-table--compact .pp-col-role,
  .pp-device-table--compact .pp-col-last-seen {
    display: none;
  }
}
@media (min-width: 769px) and (max-width: 900px) {
  .pp-device-table-wrap {
    overflow-x: auto;
  }
  .pp-operator-hub__grid {
    grid-template-columns: repeat(2, minmax(200px, 1fr));
  }
  .pp-operator-gauge__grid {
    grid-template-columns: 1fr;
  }
}
@media (min-width: 901px) and (max-width: 1100px) {
  .pp-operator-hub__grid {
    grid-template-columns: repeat(3, minmax(220px, 1fr));
  }
  .pp-operator-pick__grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .pp-operator-gauge__grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* Mobile admin */
  .dashboard-production-pulse {
    --pp-page-padding: 16px;
  }
  .pp-kpi-strip {
    grid-template-columns: 1fr;
  }
  .pp-device-table {
    display: none; /* substituído por cards */
  }
  .pp-device-card-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  .pp-form-footer {
    position: sticky;
    bottom: 0;
    padding: 12px 16px;
    padding-bottom: max(12px, env(safe-area-inset-bottom));
    background: var(--delpi-ui-surface);
    border-top: 1px solid var(--pp-border);
  }
  .pp-anchor-segmented--stack label {
    display: block;
    width: 100%;
  }
}
@media (max-width: 600px) {
  .pp-operator-hub__grid {
    grid-template-columns: 1fr;
  }
  .pp-operator-pad {
    grid-template-columns: 1fr;
  }
  .pp-operator-pad__btn--plus {
    order: -1; /* + primeiro em portrait */
  }
}
```

**Operador:** hub `OperatorPlacementHub` — cards por placement; chips filtro anchor; inspira PCP mas **não** só CT.

---

## 9. Modo operador — design caprichado (WF-PP-OP)

Tela **dedicada ao chão de fábrica**: tablet na máquina. Prioridade: **legibilidade à distância**, toque com luva, feedback imediato.

**Escalabilidade:** nem todo device é contador. O MFE usa **`OperatorDeviceSurface`** — roteador que escolhe a UI pelo `operatorSurface` do driver (registry via `GET /catalog/drivers`).

| `operatorSurface` | Componente | Fase |
|-------------------|------------|------|
| `counter_pad` | `OperatorCounterStage` + `OperatorActionPad` | MVP |
| `gauge_readout` | `OperatorGaugeStage` — valores grandes read-only | P1 |
| `temperature_focus` | `OperatorTemperatureStage` — °C + margem/alerta | P2 |
| `rotation_ring` | `OperatorRotationStage` — rpm + anel % | P2 |
| `telemetry_stack` | lista de tiles multi-métrica | P2 |
| `placement_combo` | board do posto (rota `/board`) | P2 |

Overlays P2 (não são surface): alerta sticky, faixa de meta %, chips no hub — ver [OPERATOR-SURFACES-P2.md](./OPERATOR-SURFACES-P2.md).

Dispositivos sem `operatorEligible` não entram no hub/picker operador.

### 9.0 Fluxo operador (3 telas + board P2)

```text
① Hub placements     ② Device picker (se N)     ③ Superfície por driver
/operator            /operator/placements/:key  /operator/devices/:id
(posto|máq|equip.)   (badges métrica)           counter | gauge | temp | rotation
                     └─ [Ver posto] → /board    (combo P2)
```

Hub unificado por **`placement_label`** — CT é um tipo de card entre outros.

| Tela | Rota | Quando |
|------|------|--------|
| **Hub** | `/operator` + filtros `anchorType` | Entrada operador |
| **Picker** | `/operator/placements/:placementKey` | N devices no mesmo placement |
| **Superfície** | `/operator/devices/:deviceId` | 1 device ou após escolha |

Atalho: menu «Operador · Pulso» → `/operator`.

### 9.1 Layout e chrome

- Classe página: `.dashboard-production-pulse.dashboard-page--operator`
- **Sem PageHero** administrativo — só `OperatorStatusBar` compacto no topo
- Conteúdo **centralizado** vertical e horizontal (`min-height: calc(100vh - header)`)
- Opcional: link discreto «Painel administrativo» (`BackLink`) canto superior — só se usuário tem `devices.view` admin
- Fundo: gradiente radial suave no palco do contador (`color-mix` accent 8% → canvas)

### 9.2 Palco contador (`OperatorCounterStage`) — `counter_pad`

| Elemento | Especificação |
|----------|----------------|
| Valor | `metrics.counter` — `clamp(5rem, 22vw, 10rem)` · tabular-nums |
| Label | «golpes» — muted, uppercase |
| Container | Card circular ou squircle `border-radius: 32px`, min-width 280px, padding 48px 64px, sombra suave, borda 2px `--pp-border` |
| Online | Anel externo `box-shadow` pulse verde quando online (`.pp-operator-stage--online`) |
| Offline | Valor opacity 0.45 + faixa «Sem conexão» `--pp-danger` |
| Animação +/− | Flash scale 1.04 no valor por 180ms após comando OK (CSS `@keyframes pp-counter-bump`) |

### 9.2b Palco gauge (`OperatorGaugeStage`) — `gauge_readout` (P1)

Layout vertical: **1 card por métrica** (rotação, temperatura, …).

| Elemento | Especificação |
|----------|----------------|
| Valor | `clamp(3rem, 12vw, 5rem)` por métrica |
| Unidade | Do registry (`rpm`, `°C`) — `--pp-font-md` ao lado |
| Label | `labelPt` da métrica |
| Ações | **Sem** pad −/+; opcional `[ghost Atualizar]` |
| Offline | Mesma faixa danger do contador |

Exemplo CT com contador + 2 sensores: picker mostra 3 cards com badges distintos; tap abre superfície correta.

### 9.3 Barra de status (`OperatorStatusBar`)

```text
CT-53 · Usinagem CNC          ● Online · sync há 8 s
Prensa hidráulica #1 · Sensor principal
```

- `Factory` + código CT · nome truncado
- `DeviceStatusBadge` + relativo última sync
- Segunda linha: `machine_label` · `equipment_label` (se houver)

### 9.4 Pad de ações (`OperatorActionPad`)

Três botões **grandes** em linha (`grid-template-columns: 1fr 1fr 1fr`, gap 16–24px, max-width 720px centrado).

| Botão | Ícone lucide | Símbolo | Label acessível | Cor / variant | API |
|-------|--------------|---------|-----------------|---------------|-----|
| **Diminuir** | `Minus` | **−** | «Diminuir um golpe» | Superfície neutra, borda `--pp-border`; ícone 48px | `POST .../commands/decrement` |
| **Limpar** | `Eraser` ou `RotateCcw` | **0** ou ícone borracha | «Zerar contador» | Outline `--pp-warning`; confirmação modal | `POST .../commands/reset` |
| **Aumentar** | `Plus` | **+** | «Aumentar um golpe» | Fill `--pp-accent`, texto branco; ícone 48px | `POST .../commands/increment` |

**Dimensões touch (obrigatório):**

- Altura mínima botão: **96px** (tablet); **112px** em viewport ≥768px
- Largura: flex 1:1:1; ícone **48px** + label curta opcional («−1», «+1», «Limpar») `--pp-font-sm`
- `border-radius: 20px`
- `:active` → `transform: scale(0.97)` · `:disabled` quando offline ou comando em flight

**Não usar** `ActionButton` kit para estes três — são **controles de domínio** (`.pp-operator-pad__btn`); chrome único desta tela, sem espelhar `.delpi-ui-*`.

### 9.5 Feedback operacional

| Evento | Feedback |
|--------|----------|
| Tap +/− | Spinner inline no botão · bump no contador · toast curto opcional |
| Tap Limpar | `OperatorClearConfirmModal` — «Zerar contador para 0?» · botões grandes |
| Offline | Pad desabilitado + banner «Dispositivo offline — tentando reconectar…» + `[ghost Reconectar]` |
| Erro 503 | Shake leve no palco + mensagem vermelha 3s |

### 9.6 Picker multi-device

Rota `/operator/placements/:placementKey` — ver WF-PP-OP-PICK.

### 9.7 Hub placements (`OperatorPlacementHub`)

Inspirado em PCP `WorkCenterPicker`, generalizado para **qualquer âncora**.

| Elemento | Especificação |
|----------|---------------|
| Filtros | Chips: Todos · Postos · Máquinas · Equipamentos |
| Card | `placement_label` grande + `AnchorTypeBadge` + meta `by_role` |
| Persistência | `localStorage` `delpi.production-pulse.operator.placement.{branch}` |

**Dados:** `GET /operator/placements?branch=&anchorType=&search=`

### 9.8 Entrada na jornada operador

| Origem | Ação |
|--------|------|
| **Menu Portal** | «Operador · Pulso» → `/operator` |
| Painel admin | «Modo operador» → `/operator` |
| Superfície | «Trocar posto» → hub |

### 9.9 Tokens CSS adicionais (modo operador)

```css
.dashboard-production-pulse.dashboard-page--operator {
  --pp-operator-pad-height: 96px;
  --pp-operator-counter-size: clamp(5rem, 22vw, 10rem);
  --pp-operator-stage-radius: 32px;
  --pp-operator-pad-gap: 20px;
  --pp-operator-hub-card-min-h: 128px;
  --pp-operator-hub-grid-min: 260px;
  --pp-operator-accent-plus: var(--pp-accent);
  --pp-operator-accent-minus: var(--pp-text);
  --pp-operator-accent-clear: var(--pp-warning);
}
@media (min-width: 768px) {
  .dashboard-production-pulse.dashboard-page--operator {
    --pp-operator-pad-height: 112px;
    --pp-operator-hub-card-min-h: 140px;
  }
}
```

### 9.10 Barra de marca operador (estilo PCP)

Faixa superior sticky (gradiente `--pp-title` → accent), como `BrandBar` do PCP:

- Logo Minha DELPI compacto + eyebrow «Pulso de produção · Filial 01»
- Título hub: «Escolha onde vai trabalhar» · superfície: `placement_label`
- Quiosque P1: `.dashboard-page--operator-kiosk` — ver [ADR-001](./ADR-001-operator-layout.md)

CSS domínio `.pp-operator-brandbar` — **não** copiar `.pcp-pub__*`; espelhar proporções e contraste.

### 9.11 Componentes kit reutilizados no operador

| Componente | Uso |
|------------|-----|
| `ModalShell` | Confirmar limpar/zerar |
| `StatusBadge` | Online/offline na status bar |
| `ScreenLoading` | Carregamento inicial |
| `InlineLoadingProgress` | Durante comando |
| `BackLink` | Voltar ao painel (admin) |

---

## 10. Referências visuais no monorepo

| Referência | Copiar |
|------------|--------|
| `plugins/maintenance` | PageHero, FilialSwitcher, tokens `--dm-*` → `--pp-*` |
| `plugins/controle-retrabalhos` | KPI strip + filtros período (adaptar para status/CT) |
| `plugins/commercial` | URL sync, EmptyGuidance, densidade PageHero compact |
| `plugins/public-hub` (PCP cockpit) | Grid cards touch — **não** copiar sem generalizar âncoras |
