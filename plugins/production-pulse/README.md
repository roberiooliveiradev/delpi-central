# Plugin Pulso de Produção

Monitoramento IoT de dispositivos na fábrica: contadores, sensores e modo operador tablet.

## Fluxo

```text
Portal → plugins/production-pulse (MFE) → /apps/production-pulse-api → schema production_pulse (postgres-plugins)
```

O MFE **não** chama a api-delpi diretamente.

## Rotas UI (MVP)

| Path | Descrição |
|------|-----------|
| `/apps/production-pulse` | Painel administrativo (scaffold E5.S1) |
| `/apps/production-pulse/operator` | Modo operador tablet (scaffold E5.S1) |

## API

Base: `/apps/production-pulse-api` — ver [production-pulse-api/README.md](../../production-pulse-api/README.md).

## Permissões

Ver `production-pulse.manifest.json` e [docs/12-roadmap-e-evolucao/production-pulse/README.md](../../docs/12-roadmap-e-evolucao/production-pulse/README.md).

## Dev

```bash
# Terminal 1 — remote plugin-ui
cd plugins/plugin-ui && npm run dev

# Terminal 2 — MFE
cd plugins/production-pulse
VITE_PLUGIN_UI_DEV=1 npm run dev
```

## Build / smoke

```bash
cd plugins/production-pulse && npm run ci
curl -sI http://localhost/apps/production-pulse/assets/remoteEntry.js | head -3
```

Registro do manifesto: `scripts/register-manifest.sh` (requer `TOKEN`).
