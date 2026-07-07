# `@delpi/plugin-ui`

Componentes React reutilizáveis para plugins MFE (balões de ajuda, rótulos, abas).

## Uso

```ts
import {
  HelpTooltip,
  FieldLabel,
  SectionHintLabel,
  TabHintCell,
  HintAction,
} from "@delpi/plugin-ui";
```

```ts
// main.tsx ou index.css do plugin
import "@delpi/plugin-ui/styles.css";
```

## Vite (alias local)

```ts
resolve: {
  alias: {
    "@delpi/plugin-ui": path.resolve(__dirname, "../plugin-ui/src/index.ts"),
    "@delpi/plugin-ui/styles.css": path.resolve(__dirname, "../plugin-ui/src/styles.css"),
  },
},
```

## Tokens

Opcionalmente mapeie no root do dashboard:

```css
.dashboard-meu-plugin {
  --delpi-ui-accent: var(--meu-accent);
  --delpi-ui-surface: var(--meu-surface);
  --delpi-ui-text: var(--meu-text);
  --delpi-ui-border: var(--meu-border);
  --delpi-ui-muted: var(--meu-muted);
}
```

## Componentes

| Export | Uso |
|--------|-----|
| `HelpTooltip` | Ícone ? ou `wrap` em qualquer elemento |
| `FieldLabel` | Rótulo de campo + ajuda |
| `SectionHintLabel` | Rótulo de seção (ribbon, painel) |
| `TabHintCell` | Aba + ? sem botão aninhado |
| `HintAction` | Botão/controle com balão ao hover |

Textos PT-BR ficam em `content/helpTooltips.ts` de cada plugin.
