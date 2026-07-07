# `@delpi/tv-dashboard-presentation`

Pacote compartilhado do **motor de apresentação** Painéis TV — usado pelo plugin admin e pelo `public-hub`.

Documentação: [`docs/12-roadmap-e-evolucao/tv-dashboard/README.md`](../../docs/12-roadmap-e-evolucao/tv-dashboard/README.md)

---

## Exports

```ts
import {
  usePresentationEngine,
  useFullscreenStage,
  NativeSlideView,
  formatPct,
  formatNumber,
  parseComunicadoConfig,
  serializeComunicadoConfig,
  ComunicadoBlockView,
  comunicadoImageCropCssProperties,
} from "@delpi/tv-dashboard-presentation";
```

| Export | Função |
|---|---|
| `usePresentationEngine` | Autoplay, transições, refresh periódico, pausa por visibilidade |
| `useFullscreenStage` | Duplo-clique → fullscreen (preview admin) |
| `NativeSlideView` | Render por `screenKey` (OEE, OTD, comunicado…) |
| `ComunicadoBlockView` | Render blocos comunicado (texto, mídia, crop, formas, dados) |
| `parseComunicadoConfig` / `serializeComunicadoConfig` | Schema v2–v4 (`imageCrop`, `groupId`, `dataBinding`, …) |
| `comunicadoImageCropCssProperties` | CSS viewport para recorte de imagem |
| `native-screens.css` | Layout viewport-fit (`tdp-*`) |

---

## Consumidores

| App | Import |
|---|---|
| `plugins/tv-dashboard` | Preview admin — Federation `shared: react` |
| `plugins/public-hub` | Link público `/p/tv-dashboard/present/{token}` |

Resolução Vite (ambos):

```ts
"@delpi/tv-dashboard-presentation": path.resolve(__dirname, "../tv-dashboard-presentation/src/index.ts")
```

### public-hub — React único (obrigatório)

O pacote é compilado **do source** no build do `public-hub`. Sem dedupe, o Vite pode embutir **duas cópias** do React → erro `Cannot read properties of null (reading 'useState')`.

`plugins/public-hub/vite.config.ts`:

```ts
resolve: {
  dedupe: ["react", "react-dom"],
  alias: {
    react: path.resolve(__dirname, "node_modules/react"),
    "react-dom": path.resolve(__dirname, "node_modules/react-dom"),
    // … alias do pacote
  },
},
```

Docker: `npm install` em **ambos** (`tv-dashboard-presentation` para tipos TS + `public-hub` para runtime).

---

## CSS

- Prefixo **`tdp-`** (tv-dashboard presentation)
- Modo kiosk público: `.tdp-stage--kiosk` dentro de `.pub-kiosk-root` (public-hub)
- Preview admin: `.tdp-stage--preview-shell`

---

## Testes

```bash
cd plugins/tv-dashboard-presentation
npm test
```

Cobertura: `usePresentationEngine` (autoplay, refresh nativo), render OEE com payload real.

---

## Docker

Build context **`plugins/`** nos Dockerfiles de `tv-dashboard` e `public-hub` — este diretório deve estar no contexto de cópia.
