# Arquitetura — `@delpi/plugin-ui`

## Papel no monorepo

Biblioteca **TypeScript + React** de componentes transversais para plugins MFE.

**Dois modos de consumo (jul/2026):**

| Modo | Quem | Integração |
|------|------|------------|
| **Module Federation (recomendado)** | MFEs migrados (piloto: `controle-retrabalhos`) | Remote runtime `delpi-plugin-ui` — doc [module-federation.md](./module-federation.md) |
| **Bundled (legado)** | `tv-dashboard-presentation`, `public-hub` (parcial) | Alias Vite + COPY ou shared builder |

`@delpi/tv-dashboard-presentation` permanece **bundled** (alias + COPY).

```text
plugins/plugin-ui/          ← fonte + remote federation (remoteEntry.js)
        ↓ remotes (MF) ou alias Vite (legado)
plugins/controle-retrabalhos/   ← piloto MF
plugins/dashboard-*/            ← legado (migrar Fase 2)
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
├── README.md
├── package.json
├── vite.config.ts            # remote federation
├── Dockerfile                # container runtime nginx
├── tsconfig.json
├── vitest.config.ts
├── docs/
│   ├── architecture.md       # (este arquivo)
│   ├── module-federation.md  # integração MF + Docker
│   ├── component-catalog.md
│   ├── contributing.md
│   └── migration-catalog.md
└── src/
    ├── index.ts              # barrel — expose federation "."
    ├── styles.css            # expose federation "./styles"
    └── components/
```

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

- **MF:** `import "@delpi/plugin-ui/styles"` no `bootstrap.tsx`.
- **Legado:** `import "../../plugin-ui/src/styles.css"`.
- Seguir [plugins-visual-design-system.mdc](../../.cursor/rules/plugins-visual-design-system.mdc): escopo `.dashboard-{nome}`, sem `body`/`:root` global no MFE.

## Integração — Module Federation (recomendado)

Ver guia completo: **[module-federation.md](./module-federation.md)**.

Resumo:

```ts
// consumidor — plugins/vite/federation.shared.ts
remotes: pluginUiRemote(),
shared: ["react", "react-dom", "lucide-react"],
```

```ts
// bootstrap.tsx
import "@delpi/plugin-ui/styles";
```

Container: `delpi-plugin-ui` · URL: `/apps/plugin-ui/assets/remoteEntry.js`

## Integração — bundled (legado)

```ts
resolve: {
  alias: {
    "@delpi/plugin-ui": path.resolve(__dirname, "../plugin-ui/src/index.ts"),
  },
  dedupe: ["react", "react-dom"],
},
```

### Docker (consumidores legados)

Contexto: `plugins/`. Copiar `plugin-ui/` (+ `tv-dashboard-presentation/` se aplicável) ou usar `delpi-plugins-shared-builder`.

**Gate CI:** `python3 scripts/ci/check_plugin_docker_shared_libraries.py --check` — manifesto em `plugins/shared-libraries.manifest.json`.

## HelpTooltip — decisão técnica

O balão usa **`position: fixed` + `createPortal(document.body)`** porque ancestrais com `transform`, `overflow: hidden` ou filmstrip quebram tooltips só com CSS `:hover` relativo. Reposicionamento em scroll/resize via `visualViewport`.

## Versionamento

Pacote `private: true` no monorepo — versão semântica no `package.json` para changelog interno.

Em modo **federation-remote**, breaking changes no barrel exigem atualizar [migration-catalog.md](./migration-catalog.md) e coordenar deploy do container `plugin-ui` (consumidores federados não precisam rebuild se a API exportada for compatível).
