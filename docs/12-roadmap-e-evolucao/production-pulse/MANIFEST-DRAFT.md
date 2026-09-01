# Manifesto — rascunho (`production-pulse.manifest.json`)

> Referência para E5.S1 — não commitado até scaffold MFE.

```json
{
  "id": "production-pulse",
  "name": "Pulso de Produção",
  "basePath": "/apps/production-pulse",
  "icon": "Activity",
  "routes": [
    {
      "path": "/apps/production-pulse",
      "label": "Pulso de Produção",
      "permission": "production-pulse.access"
    },
    {
      "path": "/apps/production-pulse/operator",
      "label": "Operador · Pulso",
      "permission": "production-pulse.operator"
    }
  ],
  "permissions": [
    "production-pulse.access",
    "production-pulse.devices.view",
    "production-pulse.devices.manage",
    "production-pulse.devices.command",
    "production-pulse.operator",
    "production-pulse.view.filial-01",
    "production-pulse.view.filial-02",
    "production-pulse.admin"
  ]
}
```

Menu admin e operador **separados** — operador não precisa ver painel CRUD.
