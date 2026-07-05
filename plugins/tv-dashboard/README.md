# Painéis TV (`tv-dashboard`)

Plugin MFE para gerenciar programações rotativas exibidas em TVs corporativas.

## Funcionalidades (Onda 0)

- CRUD de programações (playlists)
- Telas nativas (OEE, comunicado) e externas (iframe — Power BI, sites)
- Pré-visualização fullscreen
- Link público sem login: `/p/tv-dashboard/present/{token}`
- Ativar/desativar/excluir link

## API

Backend dedicado: `tv-dashboard-api` em `/apps/tv-dashboard-api/`

## Registro no portal

```bash
TOKEN="<jwt com apps.manage>" bash scripts/register-manifest.sh
```

Atribua `tv-dashboard.read`, `tv-dashboard.write` e `tv-dashboard.manage` no RBAC.

## Build

```bash
npm run build
```

## Deploy

Containers: `delpi-tv-dashboard`, `delpi-tv-dashboard-api`. Rebuild do `delpi-public-hub` após alterações na view pública.
