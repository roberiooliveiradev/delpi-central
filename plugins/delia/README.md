# DÉLIA MFE — bootstrap C1

Standalone federated frontend da DÉLIA (`plugins/delia/`).

## Escopo atual (C1-T3 / C1-T4)

- pasta MFE independente
- Module Federation (`./App` → `bootstrap.tsx`)
- consumo runtime de `@delpi/plugin-ui`
- mount / unmount / updateRoute compatíveis com Portal AppHost
- shell mínimo + baseline responsivo/a11y
- manifesto de publicação: `delpi.manifest.json` (owner DÉLIA; registry owner = Core)
- sem Chat runtime, sem captura de mídia automática
- Gateway/Compose/registro Core live **ainda não** feitos nesta fase

## Manifesto

Arquivo: [`delpi.manifest.json`](./delpi.manifest.json)

- `id=delia`, `basePath=/apps/delia`, `entry=/apps/delia/assets/remoteEntry.js`
- `ui.renderMode=federated`
- `delia.access` = metadata de visibilidade exigida pelo schema Core (`permissions`/`routes` minItems=1)
- `backend.serviceName=delia-api`, `baseUrl=/apps/delia-api`
- Portal default `exposedModule=./App` (campo não existe no schema)

Registro Core (ops, não C1-T4 automático):

```bash
TOKEN=... bash scripts/register-manifest.sh
```

## Scripts

```bash
cd plugins/delia
npm install
npm test
npm run build
npm run verify:federation
```

Dev standalone: `npm run dev` (requer plugin-ui remoto conforme convenção da plataforma).
