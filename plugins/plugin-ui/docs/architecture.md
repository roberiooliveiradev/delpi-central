# Arquitetura — `@delpi/plugin-ui`

## Papel no monorepo

Biblioteca **TypeScript + React** de componentes transversais para plugins MFE, servida como **remote Module Federation** (`delpi-plugin-ui`).

**Dois modos de consumo (jul/2026):**

| Modo | Pacote | Integração |
|------|--------|------------|
| **Module Federation** (obrigatório) | `@delpi/plugin-ui` | Remote runtime `delpi-plugin-ui` — [module-federation.md](./module-federation.md) · [novo-plugin-mfe-checklist.md](../../docs/05-plugin-system/novo-plugin-mfe-checklist.md) |
| **Bundled** | `@delpi/tv-dashboard-presentation` | Alias Vite + `COPY` no Dockerfile (`tv-dashboard`, `public-hub`) |

**Nenhum MFE consumidor** bundla mais `@delpi/plugin-ui` no build Docker.

```text
plugins/plugin-ui/              ← fonte + remote (remoteEntry.js)
        ↓ remotes + preparePluginUiRemote()
plugins/controle-retrabalhos/   ← referência canônica
plugins/dashboard-*/            ← 27 consumidores federados
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
    ├── index.ts              # barrel — expose "./index"
    ├── styles.css            # expose "./styles"
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

- **MF:** `preparePluginUiRemote()` no `bootstrap.tsx` carrega `@delpi/plugin-ui/styles` (dynamic import).
- Seguir [plugins-visual-design-system.mdc](../../.cursor/rules/plugins-visual-design-system.mdc): escopo `.dashboard-{nome}`, sem `body`/`:root` global no MFE.

## Integração — Module Federation (padrão)

Guia completo: **[module-federation.md](./module-federation.md)** · checklist novo MFE: **[novo-plugin-mfe-checklist.md](../../docs/05-plugin-system/novo-plugin-mfe-checklist.md)**.

```ts
// vite.config.ts — plugins/vite/federation.shared.ts
remotes: pluginUiRemote(),
shared: { ...FEDERATION_SHARED_REACT },
```

```ts
// bootstrap.tsx — plugins/vite/federationShareScope.ts
import { preparePluginUiRemote } from "../../vite/federationShareScope";
await preparePluginUiRemote();
```

```ts
// componentes
import { HelpTooltip } from "@delpi/plugin-ui/index";
```

Container: `delpi-plugin-ui` · URL: `/apps/plugin-ui/assets/remoteEntry.js`

### Docker (consumidores)

- `context: ../plugins`
- `COPY vite ./vite` no Dockerfile do MFE
- **Sem** `COPY plugin-ui`
- Compose: `<<: *plugin-ui-federated`

**Gate CI:** `python3 scripts/ci/check_plugin_docker_shared_libraries.py --check`

## Integração — `@delpi/tv-dashboard-presentation` (bundled)

Somente `tv-dashboard` e `public-hub`. Alias Vite + `COPY tv-dashboard-presentation/` no Dockerfile. Ver [plugins/docker/README.md](../../docker/README.md).

## HelpTooltip — decisão técnica

O balão usa **`position: fixed` + `createPortal(document.body)`** porque ancestrais com `transform`, `overflow: hidden` ou filmstrip quebram tooltips só com CSS `:hover` relativo. Reposicionamento em scroll/resize via `visualViewport`.

## Versionamento

Pacote `private: true` no monorepo — versão semântica no `package.json` para changelog interno.

Em modo **federation-remote**, breaking changes no barrel exigem atualizar [migration-catalog.md](./migration-catalog.md) e coordenar deploy do container `plugin-ui`. Consumidores federados **não** precisam rebuild se a API exportada for compatível — basta redeploy de `delpi-plugin-ui` + refresh do browser.
