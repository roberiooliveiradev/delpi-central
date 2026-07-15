# Checklist — novo plugin MFE

> **Status:** documentação oficial (jul/2026)  
> **Referência de código:** `plugins/controle-retrabalhos/`  
> **Complementa:** [manifesto-plugin.md](./manifesto-plugin.md) · [microfrontends.md](./microfrontends.md) · [plugins-documentation.mdc](../../.cursor/rules/plugins-documentation.mdc)

Todo **microfrontend novo** no monorepo deve seguir este padrão. O rollout de `@delpi/plugin-ui` via Module Federation está **concluído** — não criar plugins com `COPY plugin-ui` no Dockerfile.

---

## 1. Visão geral

```text
Portal (AppHost)
  └─ MFE /apps/{id}/assets/remoteEntry.js
       ├─ preparePluginUiRemote()  → share scope React + CSS remote
       └─ remote @delpi/plugin-ui  → /apps/plugin-ui/assets/remoteEntry.js

Gateway
  /apps/{id}/assets/*     → delpi-{id}
  /apps/plugin-ui/assets/* → delpi-plugin-ui
```

| Camada | Responsabilidade |
|--------|------------------|
| **Manifesto** | `type: microfrontend`, `ui.renderMode: federated`, `entry` → `remoteEntry.js` |
| **Vite MF** | `remotes: pluginUiRemote()`, `shared: FEDERATION_SHARED_REACT`, `federation()` antes de `react()` |
| **Bootstrap** | `await preparePluginUiRemote()` **antes** de renderizar React |
| **Docker** | `context: ../plugins`, `COPY vite ./vite`, **sem** `COPY plugin-ui` |
| **Compose** | `<<: *plugin-ui-federated` + `depends_on: plugin-ui` |
| **Deploy** | Scripts sequenciais — nunca `up --build gateway` isolado |

---

## 2. Estrutura mínima

Copiar de **`controle-retrabalhos`** ou **`dashboard-commercial`** (ambos federados).

```text
plugins/meu-plugin/
├── Dockerfile
├── package.json
├── vite.config.ts
├── tsconfig.app.json
├── delpi.manifest.json          # ou {id}.manifest.json
├── README.md
└── src/
    ├── bootstrap.tsx            # preparePluginUiRemote + mount/unmount
    ├── App.tsx
    ├── index.css
    └── api/httpClient.ts        # X-Delpi-Caller-App = id do manifesto
```

Helpers compartilhados (não copiar — importar):

| Arquivo | Uso |
|---------|-----|
| `plugins/vite/federation.shared.ts` | `pluginUiRemote()`, `FEDERATION_SHARED_REACT`, aliases |
| `plugins/vite/federationShareScope.ts` | `preparePluginUiRemote()` |

---

## 3. `vite.config.ts`

```ts
import federation from "@originjs/vite-plugin-federation";
import react from "@vitejs/plugin-react";
import {
  FEDERATION_SHARED_REACT,
  pluginUiRemote,
  pluginUiTestAliases,
  reactResolveAliases,
} from "../vite/federation.shared";

export default defineConfig({
  plugins: [
    federation({
      name: "meu-plugin",                    // = id estável do manifesto
      filename: "remoteEntry.js",
      remotes: pluginUiRemote(),
      exposes: { "./App": "./src/bootstrap.tsx" },
      shared: { ...FEDERATION_SHARED_REACT },
    }),
    react(),                               // federation ANTES de react
  ],
  resolve: {
    alias: { ...reactResolveAliases(__dirname) },
    dedupe: ["react", "react-dom"],
  },
  base: "/apps/meu-plugin/",
  build: {
    target: "esnext",
    modulePreload: false,
    cssCodeSplit: false,
  },
  test: {
    alias: pluginUiTestAliases(__dirname), // Vitest usa source local
  },
});
```

**Se o plugin usa React Flow** (ex.: `transformometro`): trocar shared por `FEDERATION_SHARED_WITH_DIAGRAM`.

---

## 4. `bootstrap.tsx`

Obrigatório — registra React/lucide no share scope antes do remote aninhado.

```ts
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

import { preparePluginUiRemote } from "../../vite/federationShareScope";

await preparePluginUiRemote();

// export mount / updateRoute / unmount para o Portal
```

**Não** semear React no portal (`portal/src/main.tsx`). **Não** importar `@delpi/plugin-ui/styles` manualmente — `preparePluginUiRemote()` já faz o dynamic import.

---

## 5. Imports de `@delpi/plugin-ui`

O `@originjs/vite-plugin-federation` exige **subpath** após o nome do remote:

| ✅ Correto | ❌ Errado |
|-----------|----------|
| `import { HelpTooltip } from "@delpi/plugin-ui/index"` | `import … from "@delpi/plugin-ui"` (bare) |
| `await import("@delpi/plugin-ui/styles")` (só no helper) | `import "../../plugin-ui/src/…"` |
| Reexport nomeado: `export { X } from "@delpi/plugin-ui/index"` | `export * from "@delpi/plugin-ui/index"` |

**Reexport local** (barrel do plugin): use exports **nomeados** — `export *` quebra o build MF.

Evite no mesmo arquivo: `export { x } from "@delpi/plugin-ui/index"` **e** `import { x } from "@delpi/plugin-ui/index"` (rollup duplica identificadores). Prefira um único bloco `import` + reexport local.

---

## 6. `tsconfig.app.json`

Paths apontam para o **source** (tipos/tsc local; produção usa remote):

```json
"paths": {
  "@delpi/plugin-ui": ["../plugin-ui/src/index.ts"],
  "@delpi/plugin-ui/index": ["../plugin-ui/src/index.ts"],
  "@delpi/plugin-ui/styles": ["../plugin-ui/src/styles.css"]
}
```

**Produção:** não adicionar alias Vite `@delpi/plugin-ui` → source — o MF resolve em runtime.

---

## 7. `Dockerfile`

Template federado (referência: `controle-retrabalhos/Dockerfile`):

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app

COPY meu-plugin/package*.json ./meu-plugin/
RUN cd meu-plugin && npm install

COPY meu-plugin ./meu-plugin
COPY vite ./vite

WORKDIR /app/meu-plugin
RUN npx vite build          # tsc no CI/local (npm run build)

FROM nginx:alpine AS production
COPY --from=builder /app/meu-plugin/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

| Regra | Detalhe |
|-------|---------|
| Contexto Compose | `context: ../plugins` (raiz `plugins/`) |
| **Proibido** | `COPY plugin-ui` no consumidor |
| Build Docker | `npx vite build` (sem `tsc -b` — MF externaliza plugin-ui) |

---

## 8. Docker Compose

Usar o anchor **`plugin-ui-federated`** (já definido em `infra/docker-compose*.yml`):

```yaml
meu-plugin:
  <<: *plugin-ui-federated
  build:
    context: ../plugins
    dockerfile: meu-plugin/Dockerfile
    target: production
  container_name: delpi-meu-plugin
```

O anchor inclui `depends_on: plugin-ui`. O container **`delpi-plugin-ui`** deve estar up antes do MFE.

**Subir dev:**

```bash
docker compose -f infra/docker-compose.dev.yml --profile plugins up -d plugin-ui meu-plugin
```

**Deploy produção** — scripts sequenciais (evita rebuild em cascata do gateway):

```bash
./infra/scripts/up-prod-sequential.sh --fase remote --build plugin-ui
./infra/scripts/up-prod-sequential.sh --fase mfe --build meu-plugin
./infra/scripts/up-prod-sequential.sh --fase core --build portal gateway
```

Ver [infra/README-ambiente.md](../../infra/README-ambiente.md) § Inicialização segura e [infra-sequential-container-startup.mdc](../../.cursor/rules/infra-sequential-container-startup.mdc).

---

## 9. Dev local (sem Docker)

```bash
# Terminal 1 — remote plugin-ui
cd plugins/plugin-ui && npm install && npm run dev
# http://localhost:5010/apps/plugin-ui/assets/remoteEntry.js

# Terminal 2 — consumidor
cd plugins/meu-plugin
VITE_PLUGIN_UI_DEV=1 npm run dev
```

---

## 10. UI compartilhada e tokens CSS

- Tooltips, labels, abas, KPI, cards, filtros, tabela, loading → `@delpi/plugin-ui/index` ([component-catalog.md](../../plugins/plugin-ui/docs/component-catalog.md))
- Textos PT-BR → `src/content/helpTooltips.ts` **do plugin** (nunca no pacote compartilhado)
- Tokens no root do dashboard (**sem** CSS espelho do chrome `.delpi-ui-*`):

```css
.dashboard-meu-plugin {
  --delpi-ui-accent: var(--prefix-accent, var(--primary, #089bdb));
  --delpi-ui-surface: var(--prefix-surface, var(--surface, #fff));
  --delpi-ui-text: var(--prefix-text, var(--text, #111));
  --delpi-ui-border: var(--prefix-border, var(--border, #e5e7eb));
  --delpi-ui-muted: var(--prefix-muted);
  --delpi-ui-card-padding: var(--prefix-card-padding, 20px);
  --delpi-ui-section-gap: var(--prefix-section-gap, 20px);
  --delpi-ui-grid-gap: var(--prefix-grid-gap, 16px);
}
```

- Layout de página (`*-page-stack`, gap) pode ficar no MFE; **CSS de componente do kit = zero no MFE** (sem exceção).
- Regra Cursor: [plugins-reusable-components.mdc](../../.cursor/rules/plugins-reusable-components.mdc) § CSS do kit.---

## 11. Manifesto e registro

Checklist manifesto (§31 em [visao-geral-plugin-system.md](./visao-geral-plugin-system.md)) **mais**:

- [ ] `type: "microfrontend"`
- [ ] `ui.renderMode: "federated"`
- [ ] `entry`: `/apps/{id}/assets/remoteEntry.js`
- [ ] `basePath`: `/apps/{id}` (ou path documentado)
- [ ] `id` = sufixo do container `delpi-{id}`

Registro: [registrar-plugin.md](../10-guias-operacionais/registrar-plugin.md).

---

## 12. Documentação obrigatória

Além deste checklist técnico, seguir [plugins-documentation.mdc](../../.cursor/rules/plugins-documentation.mdc):

| # | Entrega |
|---|---------|
| 1 | `plugins/{id}/README.md` |
| 2 | Doc API em `api-delpi/docs/api/` (se consumir api-delpi) |
| 3 | Entrada em `docs/08-plugins/README.md` |
| 4 | `X-Delpi-Caller-App` no `httpClient.ts` |

---

## 13. Gates CI antes do merge

```bash
cd plugins/meu-plugin && npm run build

python3 scripts/ci/check_plugin_docker_shared_libraries.py --check
python3 scripts/ci/audit_plugin_ui_duplication.py --check   # se alterou UI
```

O gate Docker aceita consumidor federado quando encontra `pluginUiRemote()` no `vite.config.ts` — **não** exige `COPY plugin-ui`.

Smoke HTTP:

```bash
curl -sI http://localhost/apps/meu-plugin/assets/remoteEntry.js | head -3
curl -sI http://localhost/apps/plugin-ui/assets/remoteEntry.js | head -3
```

---

## 14. Anti-padrões (proibidos)

| Anti-padrão | Por quê |
|-------------|---------|
| `COPY plugin-ui` no Dockerfile do MFE | Duplica build; ignora deploy único do remote |
| Alias Vite `@delpi/plugin-ui` → source em prod | Quebra MF; bundle local ≠ remote |
| Import bare `@delpi/plugin-ui` | vite-plugin-federation não intercepta |
| Paths `../plugin-ui/src/...` | Quebra Docker (contexto parcial) |
| Sem `preparePluginUiRemote()` | React #321 / `importShared` falha |
| Semear React no portal | Instâncias divergentes entre portal e MFE |
| `export * from "@delpi/plugin-ui/index"` | Build MF instável |
| `docker compose up --build gateway` manual | Rebuild em cascata de 30+ MFEs |
| `HelpTooltip.tsx` local | Duplicação — usar `@delpi/plugin-ui` |
| CSS de componente `@delpi/plugin-ui` no MFE (BEM local ou `.delpi-ui-*`) | Zero — em hipótese alguma; fonte única é o remote |

---

## 15. Bibliotecas adicionais

| Pacote | Modo | Doc |
|--------|------|-----|
| `@delpi/plugin-ui` | **federation-remote** (obrigatório) | [module-federation.md](../../plugins/plugin-ui/docs/module-federation.md) |
| `@delpi/tv-dashboard-presentation` | bundled (só `tv-dashboard`, `public-hub`) | [plugins/docker/README.md](../../plugins/docker/README.md) |

Manifesto: `plugins/shared-libraries.manifest.json`.

---

## 16. Referências

- [plugins/controle-retrabalhos/](../../plugins/controle-retrabalhos/) — piloto MF
- [plugins/vite/federation.shared.ts](../../plugins/vite/federation.shared.ts)
- [plugins/vite/federationShareScope.ts](../../plugins/vite/federationShareScope.ts)
- [plugins/plugin-ui/docs/module-federation.md](../../plugins/plugin-ui/docs/module-federation.md)
- [plugins/docker/README.md](../../plugins/docker/README.md)
- [docs/08-plugins/README.md](../08-plugins/README.md)
- [consumo-de-plugins.md](../06-portal-frontend/consumo-de-plugins.md)
