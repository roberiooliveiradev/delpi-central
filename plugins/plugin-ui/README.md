# `@delpi/plugin-ui`

Biblioteca de **componentes React reutilizáveis** para plugins MFE do monorepo Minha DELPI.

Centraliza primitivos de UI que hoje estão duplicados em dezenas de plugins (ex.: `HelpTooltip` em 14+ pastas). Textos em português permanecem em `content/helpTooltips.ts` de cada plugin — este pacote é **só interação, layout e acessibilidade**.

---

## Documentação

| Recurso | Descrição |
|---------|-----------|
| [docs/README.md](./docs/README.md) | Índice da documentação |
| [docs/architecture.md](./docs/architecture.md) | Estrutura, tokens CSS, integração Vite |
| [docs/component-catalog.md](./docs/component-catalog.md) | API de cada export + exemplos |
| [docs/contributing.md](./docs/contributing.md) | Como adicionar componentes |
| [docs/migration-catalog.md](./docs/migration-catalog.md) | Plugins a migrar das cópias locais |

---

## Quick start

### 1. Alias no consumidor (Vite)

```ts
// plugins/meu-plugin/vite.config.ts
import path from "node:path";

resolve: {
  alias: {
    "@delpi/plugin-ui": path.resolve(__dirname, "../plugin-ui/src/index.ts"),
  },
  dedupe: ["react", "react-dom"],
},
```

### 2. Estilos (uma vez)

```ts
// src/main.tsx — ajuste o caminho relativo
import "../../plugin-ui/src/styles.css";
import "./index.css";
```

### 3. Tokens no root do dashboard

```css
.dashboard-meu-plugin {
  --delpi-ui-accent: var(--meu-accent, var(--primary, #089bdb));
  --delpi-ui-surface: var(--meu-surface, var(--surface, #fff));
  --delpi-ui-text: var(--meu-text, var(--text, #111));
  --delpi-ui-border: var(--meu-border, var(--border, #e5e7eb));
  --delpi-ui-muted: var(--meu-muted);
}
```

### 4. Uso

```tsx
import { FieldLabel, HelpTooltip, HintAction, SectionHintLabel, TabHintCell } from "@delpi/plugin-ui";
import { MEU_HELP } from "./content/helpTooltips";

<FieldLabel htmlFor="periodo" label="Período" hint={MEU_HELP.fields.period} className="meu-field__label" />

<SectionHintLabel label="Filtros" hint={MEU_HELP.sections.filters} className="meu-ribbon__label" />
```

---

## Exports atuais

| Export | Função |
|--------|--------|
| `HelpTooltip` | Balão ? ou `wrap` em qualquer elemento |
| `FieldLabel` | Label de formulário + ajuda |
| `SectionHintLabel` | Rótulo de seção (ribbon) + ajuda |
| `TabHintCell` | Aba + ? sem botão aninhado |
| `HintAction` | Botão/controle com balão ao hover |
| `ChartCard` | Cartão de gráfico (layout headless + `classNames` BEM) |
| `chartCardBemClasses` | Helper para mapa BEM `{prefix}-chart-card__*` |
| `KpiCard` | Cartão KPI departamental (meta, badges IDD, ícone) |
| `kpiCardBemClasses` / `createDashboardKpiCard` | Helpers BEM + factory de wrapper |
| `LoadingActivityCard` | Spinner + barra de progresso de carregamento |
| `loadingActivityBemClasses` / `createDashboardLoadingActivityCard` | Helpers BEM + factory |

Detalhes: [component-catalog.md](./docs/component-catalog.md).

---

## Estrutura do pacote

```text
src/
├── index.ts              # barrel público
├── styles.css            # classes delpi-ui-*
└── components/
    └── help/             # família: balões explicativos
        ├── HelpTooltip.tsx
        ├── FieldLabel.tsx
        ├── SectionHintLabel.tsx
        ├── TabHintCell.tsx
        └── HintAction.tsx
```

---

## Consumidores

| Plugin | Status |
|--------|--------|
| `tv-dashboard` | ✅ Integrado (referência) |
| `dashboard-commercial` | ✅ Fase 1 |
| `dashboard-engineering` | ✅ Fase 1 |
| `dashboard-financial` | ✅ Fase 1 |
| `dashboard-hr` | ✅ Fase 1 |
| `dashboard-lmps` | ✅ Fase 1 |
| `dashboard-production` | ✅ Fase 1 |
| `dashboard-quality` | ✅ Fase 1 |
| `dashboard-supplies` | ✅ Fase 1 |
| `cadastro-kaizen` | ✅ Fase 1 |
| `transformometro` | ✅ Fase 1 |
| `quality-action-plans` | ✅ Fase 1 |
| `eficiencia-fabril` | ✅ Fase 1 |
| `maintenance` | ✅ Fase 1 |
| `portal` | ❌ Fora de escopo (shell) |

Demais plugins — ver [migration-catalog.md](./docs/migration-catalog.md).

---

## Desenvolvimento

```bash
cd plugins/plugin-ui
npm install
npm test
```

Build do consumidor (valida resolução do alias):

```bash
cd plugins/tv-dashboard
npm run build
```

---

## Relacionados

| Pacote / doc | Papel |
|--------------|-------|
| `@delpi/tv-dashboard-presentation` | Motor de apresentação TV (domínio) |
| [docs/08-plugins/README.md](../../docs/08-plugins/README.md) | Inventário de plugins |
| [plugins-visual-design-system.mdc](../../.cursor/rules/plugins-visual-design-system.mdc) | Tokens e escopo CSS dos MFEs |
| [plugins-reusable-components.mdc](../../.cursor/rules/plugins-reusable-components.mdc) | **Diretriz Cursor:** plugins devem usar este pacote |

---

## Changelog

Ver [CHANGELOG.md](./CHANGELOG.md).
