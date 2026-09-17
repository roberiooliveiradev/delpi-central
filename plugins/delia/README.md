# DÉLIA MFE — bootstrap C1

Standalone federated frontend da DÉLIA (`plugins/delia/`).

## Escopo atual (C1-T3)

- pasta MFE independente
- Module Federation (`./App` → `bootstrap.tsx`)
- consumo runtime de `@delpi/plugin-ui`
- mount / unmount / updateRoute compatíveis com Portal AppHost
- shell mínimo + baseline responsivo/a11y
- sem Chat runtime, sem captura de mídia automática, sem manifest/Gateway/Compose

## Scripts

```bash
cd plugins/delia
npm install
npm test
npm run build
npm run verify:federation
```

Dev standalone: `npm run dev` (requer plugin-ui remoto conforme convenção da plataforma).
