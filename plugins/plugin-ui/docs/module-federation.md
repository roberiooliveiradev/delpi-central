# Module Federation — `@delpi/plugin-ui` como remote runtime

> **Status:** Rollout concluído (jul/2026) — todos os MFEs + `public-hub` consomem `@delpi/plugin-ui` via remote MF. Shared-builder mantém só `tv-dashboard-presentation` (bundled).

## Objetivo

Servir `@delpi/plugin-ui` como **remote Module Federation** em container nginx (`delpi-plugin-ui`), permitindo:

- **Deploy único** da biblioteca → consumidores federados carregam a versão nova no próximo refresh (sem rebuild de cada MFE).
- **Build mais leve** dos MFEs migrados — o bundle do MFE não inclui mermaid/xyflow/jspdf duplicados.
- **~15–30 MB RAM** a mais (1 container nginx).

O **portal** não consome este remote — só os MFEs com `remotes` no Vite.

---

## Arquitetura

```text
Browser
  Portal (AppHost)
    └─ remote MFE (ex. controle-retrabalhos/assets/remoteEntry.js)
         └─ remote @delpi/plugin-ui (/apps/plugin-ui/assets/remoteEntry.js)

Gateway nginx
  /apps/controle-retrabalhos/assets/*  → delpi-controle-retrabalhos
  /apps/plugin-ui/assets/*            → delpi-plugin-ui
```

| Recurso | URL | Cache (gateway) |
|---------|-----|-----------------|
| `remoteEntry.js` | `/apps/plugin-ui/assets/remoteEntry.js` | `no-store` |
| Chunks | `/apps/plugin-ui/assets/*` | longo / immutable |

---

## Remote — exposes

`plugins/plugin-ui/vite.config.ts`:

| Expose | Arquivo | Import no consumidor |
|--------|---------|----------------------|
| `./index` | `src/index.ts` | `import { KpiCard } from "@delpi/plugin-ui/index"` |
| `./styles` | `src/styles-entry.ts` | `await import("@delpi/plugin-ui/styles")` |

**Shared singletons:** `react`, `react-dom`, `lucide-react`.

Dependências pesadas (`mermaid`, `@xyflow/react`, `jspdf`, …) ficam **no bundle do remote**.

---

## Regras do `@originjs/vite-plugin-federation`

1. **Subpath obrigatório** — o plugin só intercepta imports com `/` após o nome do remote.  
   - ✅ `@delpi/plugin-ui/index` · `@delpi/plugin-ui/styles`  
   - ❌ `@delpi/plugin-ui` (bare) · ❌ alias Vite para source no build de produção

2. **CSS** — preferir `await import("@delpi/plugin-ui/styles")` no `bootstrap.tsx` (top-level await).

3. **Ordem dos plugins** — `federation()` **antes** de `react()`.

4. **Tipos** — `tsconfig.app.json` paths apontam para o source; Vitest usa `pluginUiTestAliases()`.

5. **Reexport + import no mesmo arquivo** — evite `export { x } from "@delpi/plugin-ui/index"` junto com `import { x }` no mesmo ficheiro (rollup MF duplica identificadores). Use um único bloco `import` e reexporte símbolos locais. Scripts: `fix-plugin-ui-federation-reexports.py`, `merge-plugin-ui-imports.py` (mesclar vários `import` do mesmo remote no ficheiro).

---

## Consumidor federado (referência: `controle-retrabalhos`)

### Vite

Helper: `plugins/vite/federation.shared.ts`

```ts
import federation from "@originjs/vite-plugin-federation";
import {
  FEDERATION_SHARED_REACT,
  pluginUiRemote,
  pluginUiTestAliases,
  reactResolveAliases,
} from "../vite/federation.shared";

export default defineConfig({
  plugins: [
    federation({
      name: "controle-retrabalhos",
      filename: "remoteEntry.js",
      remotes: pluginUiRemote(),
      exposes: { "./App": "./src/bootstrap.tsx" },
      shared: [...FEDERATION_SHARED_REACT],
    }),
    react(),
  ],
  resolve: {
    alias: { ...reactResolveAliases(__dirname) },
    dedupe: ["react", "react-dom"],
  },
  test: { alias: pluginUiTestAliases(__dirname) },
});
```

### Bootstrap

```ts
import "./index.css";

await import("@delpi/plugin-ui/styles");
```

### tsconfig.app.json

```json
"paths": {
  "@delpi/plugin-ui": ["../plugin-ui/src/index.ts"],
  "@delpi/plugin-ui/index": ["../plugin-ui/src/index.ts"],
  "@delpi/plugin-ui/styles": ["../plugin-ui/src/styles.css"]
}
```

### Dockerfile

Sem `COPY plugin-ui`. Incluir helper:

```dockerfile
COPY controle-retrabalhos ./controle-retrabalhos
COPY vite ./vite
```

### Compose

```bash
docker compose -f infra/docker-compose.dev.yml --profile plugins up -d plugin-ui controle-retrabalhos
```

Serviço `controle-retrabalhos` tem `depends_on: plugin-ui`.

---

## Dev local (sem Docker)

```bash
# Terminal 1 — remote
cd plugins/plugin-ui && npm install && npm run dev
# http://localhost:5010/apps/plugin-ui/assets/remoteEntry.js

# Terminal 2 — consumidor
cd plugins/controle-retrabalhos
VITE_PLUGIN_UI_DEV=1 npm run dev
```

---

## Modo legado (bundled)

Plugins não migrados: alias `@delpi/plugin-ui` → source + `COPY plugin-ui` ou shared builder.

Manifesto: `consumptionMode` em `plugins/shared-libraries.manifest.json`.

Gate CI:

```bash
python3 scripts/ci/check_plugin_docker_shared_libraries.py --check
```

Aceita por plugin-ui: **COPY** · **shared builder** · **`pluginUiRemote()`** no vite.

---

## Rollout

| Fase | Escopo |
|------|--------|
| ✅ 0 | Remote + compose + `federation.shared.ts` + docs |
| ✅ 1 | Piloto `controle-retrabalhos` |
| ✅ 2a | 8 dashboards departamentais (`dashboard-*`) |
| ✅ 2b | 17 MFEs operacionais (ver lista abaixo) |
| ✅ 3 | Trim shared-builder (só `tv-dashboard-presentation`); `public-hub` consumidor MF; `depends_on: plugin-ui` no Compose |

### Consumidores federados

**Piloto:** `controle-retrabalhos`

**Dashboards (2a):** `dashboard-production`, `dashboard-commercial`, `dashboard-engineering`, `dashboard-financial`, `dashboard-hr`, `dashboard-lmps`, `dashboard-quality`, `dashboard-supplies`

**Operacionais (2b):** `transformometro`, `quality-action-plans`, `cadastro-kaizen`, `maintenance`, `eficiencia-fabril`, `minha-delpi-chat`, `auditoria-5s`, `inspecoes-entrada`, `pedidos-venda-abertos`, `propostas-comerciais`, `financeiro-centro-custo`, `strategic-indicators`, `customer-experience`, `cultura-delpi`, `central-agendamento`, `quality-labels`, `tv-dashboard` (também consome `@delpi/tv-dashboard-presentation` bundled)

**Shell público:** `public-hub` — consumidor MF (sem `exposes`); `tv-dashboard-presentation` permanece bundled.

**Legado (bundled):** nenhum consumidor de `@delpi/plugin-ui` restante.

---

## Referências

- [`plugins/vite/federation.shared.ts`](../vite/federation.shared.ts)
- [`plugins/plugin-ui/vite.config.ts`](../vite.config.ts)
- [`plugins/controle-retrabalhos/vite.config.ts`](../../controle-retrabalhos/vite.config.ts)
- [`plugins/docker/README.md`](../../docker/README.md)
