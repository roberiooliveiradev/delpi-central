# Arquitetura — `@delpi/plugin-ui`

## Papel no monorepo

Biblioteca **TypeScript + React** consumida por plugins MFE via **alias Vite** (mesmo padrão de `@delpi/tv-dashboard-presentation`). Não é um plugin federado — não tem `remoteEntry.js` nem manifesto na Core API.

```text
plugins/plugin-ui/          ← fonte única de componentes transversais
        ↓ alias Vite
plugins/tv-dashboard/       ← consumidor
plugins/dashboard-*/        ← migrar cópias locais
plugins/cadastro-kaizen/
…
```

## O que entra aqui

| Entra | Não entra |
|-------|-----------|
| Componentes usados por **2+ plugins** | Lógica de domínio (KPI, PAC, chat) |
| Primitivos de UI (tooltip, label, aba) | Páginas ou fluxos completos |
| Estilos com prefixo `delpi-ui-*` | Textos PT-BR ao usuário (ficam em `content/` de cada plugin) |
| Tipos e contratos estáveis | Dependência de API HTTP específica |

## Estrutura de pastas

```text
plugins/plugin-ui/
├── README.md                 # entrada + quick start
├── package.json
├── tsconfig.json
├── vitest.config.ts
├── docs/                     # documentação detalhada
│   ├── README.md
│   ├── architecture.md       # (este arquivo)
│   ├── component-catalog.md
│   ├── contributing.md
│   └── migration-catalog.md
└── src/
    ├── index.ts              # barrel público — único ponto de import TS
    ├── styles.css            # estilos globais delpi-ui-*
    └── components/
        └── help/             # família: balões explicativos
            ├── index.ts
            ├── HelpTooltip.tsx
            ├── FieldLabel.tsx
            ├── SectionHintLabel.tsx
            ├── TabHintCell.tsx
            └── HintAction.tsx
```

Novas famílias futuras (ex.: `components/form/`, `components/feedback/`) seguem o mesmo padrão: subpasta + `index.ts` + reexport em `src/index.ts`.

## CSS e tema

- **Prefixo de classe:** `delpi-ui-*` (evita colisão com portal e outros MFEs).
- **Tokens opcionais** no root do dashboard consumidor:

```css
.dashboard-meu-plugin {
  --delpi-ui-accent: var(--meu-accent, var(--primary, #089bdb));
  --delpi-ui-surface: var(--meu-surface, var(--surface, #fff));
  --delpi-ui-text: var(--meu-text, var(--text, #111));
  --delpi-ui-border: var(--meu-border, var(--border, #e5e7eb));
  --delpi-ui-muted: var(--meu-muted);
}
```

- Importar **uma vez** no entry do plugin: `import "../../plugin-ui/src/styles.css"`.
- Seguir [plugins-visual-design-system.mdc](../../.cursor/rules/plugins-visual-design-system.mdc): escopo `.dashboard-{nome}`, sem `body`/` :root` global no MFE.

## Integração Vite

```ts
// vite.config.ts do consumidor
resolve: {
  alias: {
    "@delpi/plugin-ui": path.resolve(__dirname, "../plugin-ui/src/index.ts"),
  },
  dedupe: ["react", "react-dom"], // recomendado quando o pacote é bundlado do source
},
```

`npm install` em `plugins/plugin-ui` é necessário para o TypeScript resolver `react` ao buildar consumidores que importam do source.

### Docker (consumidores MFE)

Contexto de build típico: `plugins/` (ver `tv-dashboard/Dockerfile`). Copiar **três** pastas no estágio builder:

- `tv-dashboard-presentation/`
- `plugin-ui/`
- `{plugin}/` (ex.: `tv-dashboard/`)

```dockerfile
COPY plugin-ui/package*.json ./plugin-ui/
RUN cd plugin-ui && npm install
COPY plugin-ui ./plugin-ui
```

Sem `plugin-ui` no contexto, o build falha em `@delpi/plugin-ui` e em `import "../../plugin-ui/src/styles.css"`.

## HelpTooltip — decisão técnica

O balão usa **`position: fixed` + `createPortal(document.body)`** porque ancestrais com `transform`, `overflow: hidden` ou filmstrip quebram tooltips só com CSS `:hover` relativo. Reposicionamento em scroll/resize via `visualViewport`.

## Versionamento

Pacote `private: true` no monorepo — versão semântica no `package.json` para changelog interno; breaking changes exigem atualizar [migration-catalog.md](./migration-catalog.md) e todos os consumidores listados.
