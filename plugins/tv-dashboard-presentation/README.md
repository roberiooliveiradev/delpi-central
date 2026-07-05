# Pacote compartilhado — PresentationEngine (Painéis TV)

Hook `usePresentationEngine` usado pelo plugin admin (`tv-dashboard`) e pelo `public-hub`.

```ts
import { usePresentationEngine } from "@delpi/tv-dashboard-presentation";
```

Resolvido via alias Vite em `plugins/tv-dashboard` e `plugins/public-hub` (`../tv-dashboard-presentation/src`).

**Docker:** o build usa contexto `plugins/` (ver `Dockerfile` de `tv-dashboard` e `public-hub`) para incluir este pacote no container.
