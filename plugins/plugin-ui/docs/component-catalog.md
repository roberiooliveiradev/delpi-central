# Catálogo de componentes

Exports públicos de `@delpi/plugin-ui`. Import único:

```ts
import { HelpTooltip, FieldLabel, TabHintCell } from "@delpi/plugin-ui";
```

---

## Família `help` — balões explicativos

Textos em português vêm do **plugin consumidor** (`content/helpTooltips.ts`). Este pacote só fornece interação e acessibilidade.

### `HelpTooltip`

Balão ao passar o mouse ou focar. Ícone **?** por padrão; modo `wrap` envolve filho arbitrário.

| Prop | Tipo | Default | Descrição |
|------|------|---------|-----------|
| `content` | `string` | — | Texto do balão (obrigatório) |
| `ariaLabel` | `string` | `"Saiba mais"` | Rótulo acessível do gatilho |
| `wrap` | `boolean` | `false` | Se `true`, filhos são o gatilho (sem botão ?) |
| `placement` | `"top" \| "bottom"` | `"top"` | Preferência; inverte se não couber na viewport |
| `className` | `string` | — | Classe no root |

```tsx
<HelpTooltip content="Explicação curta." ariaLabel="Ajuda: campo X" />

<HelpTooltip content="Abre ao passar no botão." wrap placement="bottom" ariaLabel="Ajuda: salvar">
  <button type="button" className="meu-btn">Salvar</button>
</HelpTooltip>
```

**Não** aninhe `<button>` dentro de `<button>`. Para abas, use `TabHintCell`.

---

### `FieldLabel`

Rótulo de formulário com **?** opcional. Usa `<label htmlFor>` quando `htmlFor` é passado.

| Prop | Tipo | Descrição |
|------|------|-----------|
| `label` | `string` | Texto visível |
| `hint` | `string?` | Conteúdo do balão |
| `htmlFor` | `string?` | Associa ao input |
| `className` | `string` | Default: `delpi-ui-field-label` |

```tsx
<FieldLabel htmlFor="periodo" label="Período (dias)" hint={H.fields.period} className="td-field__label" />
```

---

### `SectionHintLabel`

Rótulo de seção (ribbon, painel) com balão no hover. Equivalente a `HelpTooltip` + `wrap` em um `<span>`.

| Prop | Tipo | Descrição |
|------|------|-----------|
| `label` | `string` | Texto da seção |
| `hint` | `string` | Explicação |
| `className` | `string?` | Classe do span (ex.: `td-deck-ribbon__label`) |

```tsx
<SectionHintLabel label="Inserir" hint={H.ribbon.insert} className="td-deck-ribbon__label" />
```

---

### `TabHintCell`

Aba acessível (`role="tab"`) + ícone **?** como **irmão** (evita HTML inválido).

| Prop | Tipo | Default | Descrição |
|------|------|---------|-----------|
| `label` | `string` | — | Texto da aba |
| `hint` | `string` | — | Balão da aba |
| `icon` | `LucideIcon?` | — | Ícone à esquerda do label |
| `active` | `boolean` | `false` | Estado selecionado |
| `disabled` | `boolean` | `false` | Desabilita a aba |
| `onSelect` | `() => void` | — | Clique na aba |
| `cellClassName` | `string` | `delpi-ui-tab-cell` | Wrapper |
| `tabClassName` | `string` | `delpi-ui-tab` | Botão da aba |
| `tabActiveClassName` | `string` | `delpi-ui-tab--active` | Classe quando ativa |
| `hintPlacement` | `"top" \| "bottom"` | `"bottom"` | Posição do balão |
| `children` | `ReactNode?` | — | Substitui ícone+label padrão |

```tsx
<TabHintCell
  label="Programação"
  hint={H.tabs.playlist}
  icon={Settings2}
  active={tab === "playlist"}
  onSelect={() => setTab("playlist")}
  tabClassName="td-deck-tabs__tab"
  tabActiveClassName="td-deck-tabs__tab--active"
  cellClassName="td-deck-tabs__tab-cell"
/>
```

---

### `HintAction`

Atalho para `HelpTooltip` com `wrap` em um único filho (botão, input color, etc.).

| Prop | Tipo | Default |
|------|------|---------|
| `hint` | `string` | — |
| `ariaLabel` | `string` | — |
| `placement` | `"top" \| "bottom"` | `"bottom"` |
| `children` | `ReactElement` | — |

```tsx
<HintAction hint={H.ribbon.duplicate} ariaLabel="Ajuda: Duplicar">
  <button type="button" className="td-btn td-btn--sm" onClick={onDuplicate}>
    <Copy size={15} /> Duplicar
  </button>
</HintAction>
```

---

## Família `layout` — cartões de painel

### `ChartCard`

Cartão de gráfico com título, hint opcional, ações no header e corpo para o chart. **Estilos visuais ficam no plugin** via `classNames` BEM; o pacote só monta a estrutura e a11y.

| Prop | Tipo | Descrição |
|------|------|-----------|
| `title` | `string` | Título da região |
| `titleHint` | `string?` | Balão no título |
| `hint` | `string?` | Subtítulo abaixo do título |
| `children` | `ReactNode` | Conteúdo (chart) |
| `headerActions` | `ReactNode?` | Toolbar à direita (ex.: export) |
| `classNames` | `ChartCardClassNames` | Classes BEM do plugin |
| `className` | `string?` | Extra no `<section>` |
| `titleLevel` | `2 \| 3` | Nível do heading (default `2`) |

Helper `chartCardBemClasses(prefix, options?)` gera o mapa BEM padrão `{prefix}-chart-card__*`.

```tsx
import { ChartCard, chartCardBemClasses } from "@delpi/plugin-ui";

const classNames = chartCardBemClasses("dp", { withHeading: false, withActions: false });

<ChartCard title="OEE" titleHint={H.charts.oee} classNames={classNames}>
  <ResponsiveContainer>...</ResponsiveContainer>
</ChartCard>
```

**Padrão nos dashboards:** wrapper fino local reexporta `ChartCard` com `classNames` fixo do prefixo do plugin.

### `KpiCard`

Cartão KPI departamental com valor, meta, badges IDD e ícone. Textos fixos (`Meta`, `Nota IDD`, aria de badges) vêm do plugin via `labels`.

| Prop | Tipo | Descrição |
|------|------|-----------|
| `title` / `titleHint` | `string` | Rótulo e balão |
| `value` | `string` | Valor principal |
| `valueVariant` | `"default" \| "per-unit"` | Modificador CSS do valor |
| `goalLabel` / badges | ver tipos `KpiScopeBadge`, `KpiPerformanceBadge` | Metas e IDD |
| `icon` | `ReactNode` | Ícone à direita |
| `footer` | `ReactNode?` | Slot inferior |
| `loading` | `boolean?` | Placeholder `…` |
| `classNames` | `KpiCardClassNames` | BEM do plugin |
| `labels` | `KpiCardLabels` | Textos PT do plugin |

Helpers: `kpiCardBemClasses(prefix)` e `createDashboardKpiCard({ prefix, labels })` para wrapper de uma linha nos dashboards.

### `LoadingActivityCard`

Feedback de carregamento com spinner, barra de progresso (determinada ou indeterminada) e variantes `compact` / `panel`.

| Prop | Tipo | Descrição |
|------|------|-----------|
| `title` / `description` | `string` | Textos do plugin |
| `variant` | `"compact" \| "panel"` | Densidade |
| `tone` | `"neutral" \| "info"` | Estilo |
| `sticky` | `boolean?` | Default: `true` quando `compact` |
| `progressPercent` | `number?` | 0–100 para barra determinada |
| `classNames` | `LoadingActivityCardClassNames` | BEM do plugin |
| `labels` | `LoadingActivityCardLabels` | Textos PT (progresso restante, aria) |

Helpers: `loadingActivityBemClasses(prefix, { withCopyWrapper? })` e `createDashboardLoadingActivityCard`.

---

## Estilos base (`styles.css`)

| Classe | Uso |
|--------|-----|
| `delpi-ui-help-tooltip` | Root do tooltip |
| `delpi-ui-help-tooltip__trigger` | Botão ? |
| `delpi-ui-help-tooltip__bubble` | Balão (portal) |
| `delpi-ui-field-label` | Layout label + ? |
| `delpi-ui-tab-cell` | Wrapper aba + ? |
| `delpi-ui-tab` / `delpi-ui-tab--active` | Aba default (override via props) |

Consumidores podem **só** passar `className` nas props sem usar as classes default de aba.

---

## Consumidores atuais

| Plugin | Componentes usados |
|--------|-------------------|
| `tv-dashboard` | Todos os exports `help` |
| `dashboard-production` | `HelpTooltip`, `FieldLabel` |
| `dashboard-commercial` | `HelpTooltip`, `FieldLabel` |
| `dashboard-engineering` | `HelpTooltip`, `FieldLabel` |

Ver [migration-catalog.md](./migration-catalog.md) para plugins pendentes.
